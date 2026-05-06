"""
KPI resolver — turns a KPI id + scenario into a numeric result.

Public entry point: :func:`compute_kpi`. Reads the source CSV via
:class:`InputLocator`, walks the formula tree from
``calculators.evaluate``, returns a :class:`KPIResult` carrying the
value, unit, the list of source files actually read (used by the
cache layer to compute ``upstream_outputs_hash``), and a UTC
timestamp.

Failures:

* Unknown KPI id → :class:`KPIDefinitionError` (programmer error).
* Source file missing → :class:`KPINotAvailable` with
  ``upstream_tool`` derived from the schemas.yml ``created_by``.
* Source file present but missing a referenced column or zero
  denominator → :class:`KPINotAvailable`.

The resolver is stateless and synchronous; the cache wrapper added
in Phase 1c calls into it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd

from cea.inputlocator import InputLocator
from cea.kpi.calculators import evaluate
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable
from cea.kpi.registry import load_registry, _load_schemas

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


@dataclass(frozen=True)
class KPIResult:
    kpi_id: str
    value: float
    unit: str
    sources_read: List[str] = field(default_factory=list)
    computed_at: str = ""


def compute_kpi(
    kpi_id: str,
    scenario: str,
    *,
    whatif: Optional[str] = None,
) -> KPIResult:
    """Compute one KPI for one scenario.

    ``whatif`` is accepted for API symmetry with the cache layer
    but currently unused — the locator already resolves what-if
    paths via the project-store side. Wiring will be completed in
    the cache layer once the what-if scenario-resolution helper is
    in place.
    """
    registry = load_registry()
    if kpi_id not in registry:
        raise KPIDefinitionError(f"unknown KPI id '{kpi_id}'")
    kpi = registry[kpi_id]

    locator = InputLocator(scenario)
    file_path = _resolve_source_path(kpi, locator)
    if not os.path.isfile(file_path):
        upstream_tool = _upstream_tool_for(kpi.source.locator)
        raise KPINotAvailable(
            kpi_id,
            reason=f"source file is missing: {file_path}",
            upstream_tool=upstream_tool,
            missing_file=file_path,
        )

    df = pd.read_csv(file_path)
    value = evaluate(kpi.source.formula, df, kpi_id=kpi_id)
    if isinstance(value, pd.Series):
        # Schema's resolver enforces scalar output; if a Series
        # leaks out the formula author skipped an aggregate node
        # — caught by ``calculators._as_scalar`` on the way up,
        # but assert here as a belt-and-braces fallback.
        raise KPIDefinitionError(
            f"{kpi_id}: formula did not reduce to a scalar"
        )

    return KPIResult(
        kpi_id=kpi_id,
        value=float(value),
        unit=kpi.unit,
        sources_read=[file_path],
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


def _resolve_source_path(kpi, locator: InputLocator) -> str:
    method = getattr(locator, kpi.source.locator, None)
    if method is None or not callable(method):
        raise KPIDefinitionError(
            f"{kpi.id}: InputLocator has no method '{kpi.source.locator}'"
        )
    # Forward any `locator_args` from the yml as keyword args. Most
    # locators are nullary (`get_total_demand()`) — those entries
    # omit `locator_args` and the dict is empty. PV / network /
    # optimisation locators need `panel_type` / `network_name` /
    # `run_name`; the yml hardcodes the canonical default and the
    # resolver passes it through.
    locator_args = dict(kpi.source.locator_args or {})
    try:
        return method(**locator_args)
    except TypeError as exc:
        raise KPIDefinitionError(
            f"{kpi.id}: locator '{kpi.source.locator}' signature "
            f"mismatch ({exc}). Adjust `locator_args:` in the yml "
            f"to match the locator method's parameters."
        ) from exc


def _upstream_tool_for(locator_key: str) -> Optional[str]:
    """Best-effort: pull the first ``created_by`` entry from the
    schemas.yml record so :class:`KPINotAvailable` can tell the
    frontend which CEA tool to run."""
    schemas = _load_schemas()
    entry = schemas.get(locator_key) or {}
    created_by = entry.get("created_by") or []
    return created_by[0] if created_by else None
