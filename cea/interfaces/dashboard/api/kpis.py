"""
KPIs API — registry-driven Key Performance Indicators surfaced in
the Canvas Builder and OverviewCard ribbon.

Endpoint:
  GET /api/kpis/?project=&scenario=&feature=&whatif=
    Returns every KPI in the requested ``feature`` for the given
    scenario. Each KPI either reports its ``value`` + ``unit`` (cache
    hit or just-recomputed) or carries ``available: false`` with
    ``reason`` + ``upstream_tool`` so the frontend can prompt the
    user to run that tool first.

The endpoint is a thin wrapper around :func:`cea.kpi.cache.compute_kpi_cached`:
the cache layer owns the three-hash freshness gate, status-file
read/write, and on-miss recompute. The endpoint just iterates,
catches :class:`KPINotAvailable` per KPI, and shapes the JSON.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, status

import cea.inputlocator
from cea.interfaces.dashboard.dependencies import CEAProjectRoot
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.utils import resolve_scenario_path
from cea.kpi.cache import compute_kpi_cached
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable
from cea.kpi.registry import kpis_for_feature, load_registry

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

logger = getCEAServerLogger("cea-server-kpis")

router = APIRouter()


@router.get("/")
async def get_kpis(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    feature: str,
    whatif: Optional[str] = None,
):
    """Return every KPI registered under ``feature`` for the
    scenario, computed (or cache-hit) via the three-hash gate.

    KPIs whose source CSV doesn't exist yet are returned with
    ``available: false`` and an ``upstream_tool`` hint instead of
    failing the whole request — the frontend can render a "run X"
    prompt next to the empty tile.

    Truly broken KPIs (registry / formula errors) raise 500; those
    are bugs to fix in the yml, not user-facing states.
    """
    scenario_path = resolve_scenario_path(project_root, project, scenario)

    # Surface a tight error if the feature doesn't exist in the
    # registry — easier to debug than an empty array.
    registry = load_registry()
    known_features = {kpi.category for kpi in registry.values()}
    if feature not in known_features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown KPI feature '{feature}'. Known: {sorted(known_features)}",
        )

    kpi_payloads = []
    all_fresh = True
    for kpi in kpis_for_feature(feature):
        try:
            result = compute_kpi_cached(
                kpi.id, scenario_path, whatif=whatif
            )
            kpi_payloads.append(
                {
                    "id": kpi.id,
                    "label": kpi.label,
                    "category": kpi.category,
                    "value": result.value,
                    "unit": result.unit,
                    "available": True,
                    "headline": kpi.headline,
                    "better_direction": kpi.better_direction,
                    "info_note": kpi.info_note,
                    "description": kpi.description,
                    "computed_at": result.computed_at,
                }
            )
        except KPINotAvailable as exc:
            all_fresh = False
            kpi_payloads.append(
                {
                    "id": kpi.id,
                    "label": kpi.label,
                    "category": kpi.category,
                    "unit": kpi.unit,
                    "available": False,
                    "headline": kpi.headline,
                    "better_direction": kpi.better_direction,
                    "info_note": kpi.info_note,
                    "description": kpi.description,
                    "reason": exc.reason,
                    "upstream_tool": exc.upstream_tool,
                    "missing_file": exc.missing_file,
                }
            )
        except KPIDefinitionError as exc:
            # Registry-level bug — the yml is broken. Log loudly
            # and surface as 500: this is not a user-recoverable
            # state.
            logger.exception("KPI definition error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"KPI definition error for '{kpi.id}': {exc}",
            )

    return {
        "kpis": kpi_payloads,
        "metadata": {
            "feature": feature,
            "scenario": scenario,
            "whatif": whatif,
            "all_fresh": all_fresh,
        },
    }
