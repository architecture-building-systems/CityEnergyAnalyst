"""
KPI cache gate — wraps :func:`cea.kpi.resolver.compute_kpi` with a
three-hash freshness check so identical state never recomputes.

Hashes:

* ``scenario_inputs_hash`` — folder hash of the scenario's
  ``inputs/`` (``hash_folder``). Catches user input edits.
* ``upstream_outputs_hash`` — file hash of the source CSV(s) the
  KPI's formula reads (``hash_files``). Catches "did the upstream
  CEA tool re-run since I last computed this KPI?".
* ``kpi_definition_hash`` — attached to the
  :class:`KPIDefinition` at registry load (canonical-JSON SHA256 of
  the yml entry). Catches "did the formula or unit change?".

A cache hit returns the stored value when *all three* hashes match
the live ones; any mismatch triggers a recompute and the new record
is written under the same id (per-id write; other KPIs in the file
are preserved). Writes are atomic via :mod:`cea.kpi.status`'s
temp-file + ``os.replace`` shuffle.

The lazy fallback is always live: even if the dashboard's eager
post-processing chain (Phase 1e) is bypassed (CLI / batch / tests),
the next call still self-heals because the hashes catch any drift.

``force=True`` bypasses the cache entirely — handy for tests and
debug. The recomputed value is still written back, so subsequent
calls hit the cache.
"""

from __future__ import annotations

from typing import List, Optional

from cea.inputlocator import InputLocator
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable
from cea.kpi.registry import load_registry
from cea.kpi.resolver import KPIResult, _resolve_source_path, compute_kpi
from cea.kpi.status import read_kpi, write_kpi, clear_kpi as _clear_kpi
from cea.utilities.fingerprint import hash_files, hash_folder

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def compute_kpi_cached(
    kpi_id: str,
    scenario: str,
    *,
    whatif: Optional[str] = None,
    force: bool = False,
) -> KPIResult:
    """Cache-aware wrapper around :func:`compute_kpi`.

    Returns the stored value if all three hashes match what's on
    disk; otherwise recomputes via the resolver, writes the new
    record to ``kpi_status.json``, and returns the fresh result.
    """
    registry = load_registry()
    if kpi_id not in registry:
        raise KPIDefinitionError(f"unknown KPI id '{kpi_id}'")
    kpi = registry[kpi_id]

    locator = InputLocator(scenario)
    source_path = _resolve_source_path(kpi, locator)
    sources = [source_path]

    inputs_hash = _safe_hash_folder(locator.get_input_folder())
    upstream_hash = hash_files(sources)
    definition_hash = getattr(kpi, "definition_hash", "")

    if not force:
        cached = read_kpi(scenario, kpi_id)
        if _hashes_match(cached, inputs_hash, upstream_hash, definition_hash):
            return KPIResult(
                kpi_id=kpi_id,
                value=float(cached["value"]),
                unit=str(cached.get("unit", kpi.unit)),
                sources_read=list(cached.get("sources_read", sources)),
                computed_at=str(cached.get("computed_at", "")),
            )

    result = compute_kpi(kpi_id, scenario, whatif=whatif)
    # Re-hash sources from the resolver's reported list — usually
    # identical to what we computed up front, but the resolver is
    # the source of truth for "what files did this KPI actually
    # read?".
    final_upstream_hash = (
        hash_files(result.sources_read) if result.sources_read else upstream_hash
    )
    write_kpi(
        scenario,
        kpi_id,
        {
            "value": result.value,
            "unit": result.unit,
            "computed_at": result.computed_at,
            "sources_read": list(result.sources_read),
            "scenario_inputs_hash": inputs_hash,
            "upstream_outputs_hash": final_upstream_hash,
            "kpi_definition_hash": definition_hash,
        },
    )
    return result


def invalidate(
    scenario: str,
    *,
    kpi_id: Optional[str] = None,
    feature: Optional[str] = None,
) -> None:
    """Drop cache entries — see :func:`cea.kpi.status.clear_kpi`.

    Wired by the Phase-1e post-processing hook: when a CEA tool
    finishes, the matching feature's KPIs are cleared so the next
    fetch recomputes against the fresh upstream CSVs without
    paying the file-hash cost on every read."""
    _clear_kpi(scenario, kpi_id=kpi_id, feature=feature)


# ── Helpers ─────────────────────────────────────────────────────────


def _hashes_match(
    cached: Optional[dict],
    inputs_hash: str,
    upstream_hash: str,
    definition_hash: str,
) -> bool:
    if not cached:
        return False
    return (
        cached.get("scenario_inputs_hash") == inputs_hash
        and cached.get("upstream_outputs_hash") == upstream_hash
        and cached.get("kpi_definition_hash") == definition_hash
    )


def _safe_hash_folder(path: str) -> str:
    """Hash the folder if it exists, else return a stable
    "missing" marker. A scenario without an ``inputs/`` folder is
    pathological but shouldn't crash the cache layer — the
    resolver will raise :class:`KPINotAvailable` shortly after."""
    import os

    if not os.path.isdir(path):
        return "missing"
    return hash_folder(path)
