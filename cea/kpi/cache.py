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

from typing import Any, Mapping, Optional

from cea.inputlocator import InputLocator
from cea.kpi.exceptions import KPIDefinitionError
from cea.kpi.registry import load_registry
from cea.kpi.resolver import (
    KPIResult,
    _resolve_source_path,
    compute_kpi,
    merge_locator_args,
)
from cea.kpi.status import read_kpi, write_kpi, clear_kpi as _clear_kpi
from cea.utilities.fingerprint import hash_files, hash_folder, hash_payload

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
    locator_args_override: Optional[Mapping[str, Any]] = None,
    force: bool = False,
) -> KPIResult:
    """Cache-aware wrapper around :func:`compute_kpi`.

    Returns the stored value if all four hashes match what's on
    disk; otherwise recomputes via the resolver, writes the new
    record to ``kpi_status.json``, and returns the fresh result.

    ``locator_args_override`` carries per-card user choices (e.g.
    ``panel_type=amorphous``). Two cards with different overrides
    cache under distinct compound keys so they never collide on a
    shared single-record-per-id slot — see ``_cache_key`` below for
    the encoding.
    """
    registry = load_registry()
    if kpi_id not in registry:
        raise KPIDefinitionError(f"unknown KPI id '{kpi_id}'")
    kpi = registry[kpi_id]

    # Merge yml defaults with the per-call override once, up-front;
    # both the cache key (`args_hash`) and the resolver call see
    # the same effective args, so a hit/miss decision is consistent
    # with the value that would actually be computed.
    merged_args = merge_locator_args(kpi.source.locator_args, locator_args_override)
    args_hash = _args_hash_for(merged_args)
    cache_key = _cache_key(kpi_id, merged_args)

    locator = InputLocator(scenario)
    source_path = _resolve_source_path(kpi, locator, locator_args_override)
    sources = [source_path]

    inputs_hash = _safe_hash_folder(locator.get_input_folder())
    upstream_hash = hash_files(sources)
    definition_hash = getattr(kpi, "definition_hash", "")

    if not force:
        cached = read_kpi(scenario, cache_key)
        if _hashes_match(
            cached, inputs_hash, upstream_hash, definition_hash, args_hash
        ):
            return KPIResult(
                kpi_id=kpi_id,
                value=float(cached["value"]),
                unit=str(cached.get("unit", kpi.unit)),
                sources_read=list(cached.get("sources_read", sources)),
                computed_at=str(cached.get("computed_at", "")),
            )

    result = compute_kpi(
        kpi_id,
        scenario,
        whatif=whatif,
        locator_args_override=locator_args_override,
    )
    # Re-hash sources from the resolver's reported list — usually
    # identical to what we computed up front, but the resolver is
    # the source of truth for "what files did this KPI actually
    # read?".
    final_upstream_hash = (
        hash_files(result.sources_read) if result.sources_read else upstream_hash
    )
    write_kpi(
        scenario,
        cache_key,
        {
            "value": result.value,
            "unit": result.unit,
            "computed_at": result.computed_at,
            "sources_read": list(result.sources_read),
            "scenario_inputs_hash": inputs_hash,
            "upstream_outputs_hash": final_upstream_hash,
            "kpi_definition_hash": definition_hash,
            "args_hash": args_hash,
            # Mirror the merged args verbatim so a future debug /
            # invalidation pass can read the cache file and tell at
            # a glance which configuration this record represents.
            "locator_args": dict(merged_args),
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
    args_hash: str,
) -> bool:
    if not cached:
        return False
    # ``args_hash`` was added when the cache key gained per-call
    # overrides — older records on disk don't carry it. Treat a
    # missing field as "matches" so legacy records aren't blown
    # away on the first read after upgrade; the compound cache key
    # already separates variants, so this fallback only fires on
    # the no-args path.
    cached_args = cached.get("args_hash", args_hash)
    return (
        cached.get("scenario_inputs_hash") == inputs_hash
        and cached.get("upstream_outputs_hash") == upstream_hash
        and cached.get("kpi_definition_hash") == definition_hash
        and cached_args == args_hash
    )


def _args_hash_for(merged_args: Mapping[str, Any]) -> str:
    """SHA256 of the merged locator-args dict (canonical JSON).

    Empty dict (KPIs that take no args at all, e.g. demand /
    architecture) hashes to a fixed marker; the cache key for those
    omits the suffix so the on-disk record stays at the simple
    `<kpi_id>` slot.
    """
    if not merged_args:
        return ""
    return hash_payload(dict(merged_args))


def _cache_key(kpi_id: str, merged_args: Mapping[str, Any]) -> str:
    """Build the on-disk cache key.

    No args → ``<kpi_id>`` (preserves the storage shape used before
    per-card overrides existed). Otherwise → ``<kpi_id>::<hash>``
    so distinct configurations never collide on the same slot.
    """
    if not merged_args:
        return kpi_id
    return f"{kpi_id}::{hash_payload(dict(merged_args))}"


def _safe_hash_folder(path: str) -> str:
    """Hash the folder if it exists, else return a stable
    "missing" marker. A scenario without an ``inputs/`` folder is
    pathological but shouldn't crash the cache layer — the
    resolver will raise :class:`KPINotAvailable` shortly after."""
    import os

    if not os.path.isdir(path):
        return "missing"
    return hash_folder(path)
