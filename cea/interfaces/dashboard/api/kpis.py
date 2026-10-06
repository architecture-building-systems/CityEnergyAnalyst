"""
KPIs API — registry-driven Key Performance Indicators surfaced in
the Canvas Builder and OverviewCard ribbon.

Endpoint:
  GET /kpis/?feature=&whatif=
    Scenario is resolved from X-CEA-* headers. Returns every KPI in
    the requested ``feature`` for the given scenario. Each KPI
    either reports its ``value`` + ``unit`` (cache hit or
    just-recomputed) or carries ``available: false`` with ``reason``
    + ``upstream_tool`` so the frontend can prompt the user to run
    that tool first.

The endpoint is a thin wrapper around :func:`cea.kpi.cache.compute_kpi_cached`:
the cache layer owns the three-hash freshness gate, status-file
read/write, and on-miss recompute. The endpoint just iterates,
catches :class:`KPINotAvailable` per KPI, and shapes the JSON.

Every scenario-reading route hashes and parses files on disk, so each
runs its (synchronous) body in the threadpool rather than on the event
loop -- a slow scenario must not stall the rest of the server.
"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool

import cea.inputlocator
from cea.interfaces.dashboard.api.utils import CEAScenario
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.kpi.annotations import annotate
from cea.kpi.cache import compute_kpi_cached
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable
from cea.kpi.option_generators import run_generator
from cea.kpi.registry import kpis_for_feature, load_registry
from cea.kpi.resolver import effective_locator_args
from cea.kpi.units import UNIT_PARAMETER, convert, unit_choices

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
            # parameters (panel_type, whatif_name, etc.) or offers a
            # choice of display unit — drives the canvas picker's
            # step-1 button label ("Next" vs "Add KPI") without a
            # per-KPI step-2 fetch.
            "has_parameters": bool(kpi.source.parameters or unit_choices(kpi.unit)),
        }
        for kpi in registry.values()
    ]
    kpis.sort(key=lambda k: k["id"])
    return {"kpis": kpis}


@router.get("/")
async def get_kpis(
    scenario_path: CEAScenario,
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
    return await run_in_threadpool(_get_kpis, scenario_path, feature, whatif)


def _get_kpis(scenario_path: str, feature: str, whatif: Optional[str]):
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
            "scenario": scenario_path,
            "whatif": whatif,
            "all_fresh": all_fresh,
        },
    }


def _default_for(param, choices):
    """The value the picker pre-selects: the yml default, else the generator's first
    choice -- the same fallback `effective_locator_args` applies at fetch time."""
    if param.default is not None or not choices:
        return param.default
    return choices[0]["value"]


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
    kpi_id: str,
    scenario_path: CEAScenario,
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
              "default": "PV1",
              "choices": [
                {"value": "PV1", "label": "PV1 · typical csi 2024 (BIPV)"},
                {"value": "PV3", "label": "PV3 · typical cdte 2024 (BIPV)"}
              ]
            }
          }
        }

    Empty ``parameters`` map → KPI is fully configured by the yml
    (defaults work as-is, no step-2 form needed).
    """
    return await run_in_threadpool(_get_kpi_parameters, kpi_id, scenario_path, args)


def _get_kpi_parameters(kpi_id: str, scenario_path: str, args: Optional[str]):
    registry = load_registry()
    if kpi_id not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown KPI id '{kpi_id}'",
        )
    kpi = registry[kpi_id]

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
            "default": _default_for(param, choices),
            "description": param.description,
            "choices": choices,
            # Frontend uses this to decide which other parameter
            # changes should trigger a re-fetch. Empty when the
            # generator doesn't depend on anything.
            "depends_on": list(param.depends_on or []),
        }

    units = unit_choices(kpi.unit)
    if units:
        out[UNIT_PARAMETER] = {
            "label": "Unit",
            "type": "string",
            "default": kpi.unit,
            "description": "Unit to show the value in.",
            "choices": [{"value": u, "label": u} for u in units],
            "depends_on": [],
        }

    return {"parameters": out, "kpi_id": kpi_id}


@router.get("/{kpi_id}/value")
async def get_kpi_value(
    kpi_id: str,
    scenario_path: CEAScenario,
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
    return await run_in_threadpool(_get_kpi_value, kpi_id, scenario_path, locator_args, whatif)


def _get_kpi_value(kpi_id: str, scenario_path: str, locator_args: Optional[str], whatif: Optional[str]):
    args_override = _parse_locator_args(locator_args) or {}
    # The display unit is applied to the cached base value below; it is
    # not a locator argument and must not split the cache.
    display_unit = args_override.pop(UNIT_PARAMETER, None)

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
        # Resolved once and shared with the annotation, so defaults filled from
        # an options generator (e.g. panel_type) are looked up a single time.
        locator = cea.inputlocator.InputLocator(scenario_path)
        effective_args = effective_locator_args(kpi, locator, args_override)
        result = compute_kpi_cached(
            kpi_id,
            scenario_path,
            whatif=whatif,
            locator_args_override=effective_args,
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

    value, unit, unit_scale = result.value, result.unit, 1.0
    if display_unit and display_unit in unit_choices(unit):
        unit_scale = convert(1.0, unit, display_unit)
        value, unit = value * unit_scale, display_unit

    return {
        **base_payload,
        "available": True,
        "value": value,
        "unit": unit,
        # Base-unit -> display-unit factor, for values fetched elsewhere in the
        # base unit (the pathway sparkline reads the bulk endpoint).
        "unit_scale": unit_scale,
        "annotations": _annotations(kpi, locator, effective_args),
        "computed_at": result.computed_at,
    }


def _annotations(kpi, locator, effective_args):
    """Rows describing what the value was measured for (see `cea/kpi/annotations.py`).

    Annotations read user-editable files (the what-if configuration, the component
    database), so anything can go wrong in them -- including a YAML parse error.
    They only describe a value that computed fine, so any failure drops them (logged)
    rather than failing the request."""
    if kpi.annotation is None:
        return []
    try:
        return annotate(kpi.annotation, locator, effective_args)
    except Exception:
        logger.exception("Annotation '%s' for %s failed", kpi.annotation, kpi.id)
        return []
