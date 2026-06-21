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

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, status

import cea.inputlocator
from cea.interfaces.dashboard.dependencies import CEAProjectRoot
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.utils import resolve_scenario_path
from cea.kpi.cache import compute_kpi_cached
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable
from cea.kpi.option_generators import run_generator
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


@router.get("/registry")
async def get_kpi_registry():
    """Return the entire KPI catalogue as a flat list.

    The frontend's `KpiPicker` regroups these into the same
    hierarchy `FeatureCardPlot` uses (`PLOT_GROUPS` in
    `features/plots/constants.js`) by matching `category`
    against the plot-key strings in each group. No need for the
    backend to pre-bucket — frontend owns the visual taxonomy.

    Sorted by id so picker ordering is stable across reloads.
    """
    registry = load_registry()
    kpis = [
        {
            "id": kpi.id,
            "label": kpi.label,
            "category": kpi.category,
            "unit": kpi.unit,
            "headline": kpi.headline,
            "better_direction": kpi.better_direction,
            "info_note": kpi.info_note,
            "description": kpi.description,
            # Whether this KPI declares any user-configurable
            # parameters (panel_type, whatif_name, etc.) — drives
            # the canvas picker's step-1 button label ("Next" vs
            # "Add KPI") without a per-KPI step-2 fetch.
            "has_parameters": bool(kpi.source.parameters),
        }
        for kpi in registry.values()
    ]
    kpis.sort(key=lambda k: k["id"])
    return {"kpis": kpis}


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
    # registry — easier to debug than an empty array. Feature is
    # the id-prefix (yml file stem); `category` is now reserved
    # for plot-group picker grouping and may differ.
    registry = load_registry()
    known_features = {kpi.id.split('.', 1)[0] for kpi in registry.values()}
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


def _parse_locator_args(raw: Optional[str]) -> Optional[dict]:
    """Decode the ``locator_args`` query param.

    Frontend serialises the per-card override as a single JSON
    string (URL-encoded); decoding here keeps the wire format
    compact and round-trippable. ``None`` / empty string → no
    override (resolver falls through to yml defaults).
    """
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid locator_args JSON: {exc}",
        )
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="locator_args must decode to an object (dict)",
        )
    return parsed


@router.get("/{kpi_id}/parameters")
async def get_kpi_parameters(
    project_root: CEAProjectRoot,
    kpi_id: str,
    project: str,
    scenario: str,
    args: Optional[str] = None,
):
    """Return resolved choice lists for every parameter the KPI
    accepts. Drives the canvas KPI picker's step-2 form so the
    user sees a populated dropdown of (e.g.) the actual panel
    codes that exist on disk for this scenario.

    ``args`` is an optional JSON-encoded draft of currently-picked
    parameter values, forwarded to dependent generators (e.g.
    ``phases_for_plan`` filters by the picked ``plan_name``). The
    frontend re-fetches with the updated draft whenever any
    parameter changes so dependent dropdowns stay in sync.

    Shape::

        {
          "parameters": {
            "panel_type": {
              "label": "Panel type",
              "default": "monocrystalline",
              "choices": [
                {"value": "monocrystalline", "label": "monocrystalline"},
                {"value": "amorphous", "label": "amorphous"}
              ]
            }
          }
        }

    Empty ``parameters`` map → KPI is fully configured by the yml
    (defaults work as-is, no step-2 form needed).
    """
    registry = load_registry()
    if kpi_id not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown KPI id '{kpi_id}'",
        )
    kpi = registry[kpi_id]

    scenario_path = resolve_scenario_path(project_root, project, scenario)
    locator = cea.inputlocator.InputLocator(scenario_path)
    draft = _parse_locator_args(args) or {}

    out = {}
    for name, param in (kpi.source.parameters or {}).items():
        choices = []
        if param.options_generator:
            try:
                choices = run_generator(param.options_generator, locator, draft)
            except KPIDefinitionError as exc:
                logger.exception("Options generator failed: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Options generator '{param.options_generator}' "
                    f"for KPI '{kpi_id}' parameter '{name}' failed: {exc}",
                )
        out[name] = {
            "label": param.label,
            "type": param.type,
            "default": param.default,
            "description": param.description,
            "choices": choices,
            # Frontend uses this to decide which other parameter
            # changes should trigger a re-fetch. Empty when the
            # generator doesn't depend on anything.
            "depends_on": list(param.depends_on or []),
        }

    return {"parameters": out, "kpi_id": kpi_id}


@router.get("/{kpi_id}/value")
async def get_kpi_value(
    project_root: CEAProjectRoot,
    kpi_id: str,
    project: str,
    scenario: str,
    locator_args: Optional[str] = None,
    whatif: Optional[str] = None,
):
    """Return a single KPI's value with optional per-call
    ``locator_args`` override. Shape mirrors one entry of the
    bulk endpoint's ``kpis`` list.

    The canvas's per-card KPI fetch hits this endpoint so two
    cards bound to the same KPI but with different overrides
    (e.g. mono vs amorphous solar) get distinct values without
    the bulk endpoint's "share fetch across feature" assumption.
    """
    scenario_path = resolve_scenario_path(project_root, project, scenario)
    args_override = _parse_locator_args(locator_args)

    registry = load_registry()
    if kpi_id not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown KPI id '{kpi_id}'",
        )
    kpi = registry[kpi_id]

    base_payload = {
        "id": kpi.id,
        "label": kpi.label,
        "category": kpi.category,
        "unit": kpi.unit,
        "headline": kpi.headline,
        "better_direction": kpi.better_direction,
        "info_note": kpi.info_note,
        "description": kpi.description,
    }

    try:
        result = compute_kpi_cached(
            kpi_id,
            scenario_path,
            whatif=whatif,
            locator_args_override=args_override,
        )
    except KPINotAvailable as exc:
        return {
            **base_payload,
            "available": False,
            "reason": exc.reason,
            "upstream_tool": exc.upstream_tool,
            "missing_file": exc.missing_file,
        }
    except KPIDefinitionError as exc:
        logger.exception("KPI definition error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KPI definition error for '{kpi_id}': {exc}",
        )

    return {
        **base_payload,
        "available": True,
        "value": result.value,
        "computed_at": result.computed_at,
    }
