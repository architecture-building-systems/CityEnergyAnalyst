from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

import cea.inputlocator
from cea.datamanagement.district_pathways.intervention_templates import (
    delete_intervention_template,
    get_intervention_template_names,
)
from cea.datamanagement.district_pathways.pathway_timeline import (
    StockOnlyStateError,
    StockYearRequiresEditError,
    YearRequiresEditError,
    apply_templates_to_year,
    create_pathway_year,
    create_pathway,
    delete_or_clear_state,
    get_pathway_overview,
    get_pathway_timeline,
    get_year_editor_options,
    list_pathway_names,
    update_year_building_events,
    update_year_yaml,
    validate_baked_state,
    validate_pathway_log,
)
from cea.interfaces.dashboard.dependencies import CEAConfig, CEASeverDemoAuthCheck


async def _use_parent_scenario(config: CEAConfig):
    """Router-level dependency: temporarily resolves config.scenario to
    the parent scenario (stripping any ``/outputs/pathways/.../state_YYYY``
    suffix) so pathway endpoints always see the correct folder. Restores
    the original path after the response is sent, so map-layer and tool
    endpoints that run later still see the child-scenario path."""
    original = config.scenario
    parent = cea.inputlocator.InputLocator.parent_scenario_for_pathway_child(original)
    if parent != original:
        config.scenario = parent
    try:
        yield
    finally:
        config.scenario = original


router = APIRouter(dependencies=[Depends(_use_parent_scenario)])


class CreatePathwayPayload(BaseModel):
    pathway_name: str


class DuplicatePathwayPayload(BaseModel):
    name: str


class BuildingEventsPayload(BaseModel):
    new_buildings: list[str] = []
    demolished_buildings: list[str] = []


class ApplyTemplatesPayload(BaseModel):
    template_names: list[str]


class RawYearYamlPayload(BaseModel):
    raw_yaml: str


@router.get("/")
async def get_pathways(config: CEAConfig) -> dict[str, list[str]]:
    pathways = await run_in_threadpool(list_pathway_names, config)
    return {"pathways": pathways}


@router.get("/overview")
async def get_overview(config: CEAConfig) -> dict[str, Any]:
    return await run_in_threadpool(get_pathway_overview, config)


@router.post("/", dependencies=[CEASeverDemoAuthCheck])
async def post_pathway(config: CEAConfig, payload: CreatePathwayPayload) -> dict[str, Any]:
    try:
        return await run_in_threadpool(create_pathway, config, payload.pathway_name)
    except FileExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{pathway_name}/duplicate", dependencies=[CEASeverDemoAuthCheck])
async def duplicate_pathway(
    config: CEAConfig, pathway_name: str, payload: DuplicatePathwayPayload
) -> dict[str, Any]:
    import shutil
    from cea.datamanagement.district_pathways.pathway_state import validate_pathway_name

    src_name = validate_pathway_name(pathway_name)
    dst_name = validate_pathway_name(payload.name)
    locator = cea.inputlocator.InputLocator(config.scenario)

    src_folder = locator.get_district_pathway_folder(src_name)
    if not os.path.isdir(src_folder):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source pathway '{src_name}' does not exist.",
        )

    dst_folder = locator.get_district_pathway_folder(dst_name)
    if os.path.exists(dst_folder):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A pathway named '{dst_name}' already exists.",
        )

    await run_in_threadpool(shutil.copytree, src_folder, dst_folder)

    pathways = await run_in_threadpool(list_pathway_names, config)
    return {"pathway_name": dst_name, "pathways": pathways}


@router.get("/templates")
async def get_templates(config: CEAConfig) -> dict[str, list[str]]:
    locator = cea.inputlocator.InputLocator(config.scenario)
    names = await run_in_threadpool(get_intervention_template_names, locator)
    return {"templates": names}


@router.delete("/templates/{template_name}", dependencies=[CEASeverDemoAuthCheck])
async def delete_template(
    config: CEAConfig,
    template_name: str,
) -> dict[str, str]:
    try:
        await run_in_threadpool(
            delete_intervention_template, config, template_name,
        )
        return {"status": "deleted"}
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/building-lifecycle/{building_name}")
async def get_building_lifecycle_multi(
    config: CEAConfig,
    building_name: str,
    pathways: str = "",
) -> dict[str, Any]:
    """Get lifecycle intervals for a building across multiple pathways.

    Query param `pathways` is a comma-separated list of pathway names.
    """
    from cea.datamanagement.district_pathways.pathway_state import DistrictEvolutionPathway

    pathway_names = [p.strip() for p in pathways.split(",") if p.strip()]
    if not pathway_names:
        pathway_names = await run_in_threadpool(list_pathway_names, config)

    def fn():
        results = []
        all_years = []
        for pname in pathway_names:
            try:
                pathway = DistrictEvolutionPathway(config, pathway_name=pname)
                intervals = pathway.get_building_lifecycle_intervals()
                building_intervals = intervals.get(building_name, [])
                results.append({
                    "pathway_name": pname,
                    "intervals": [{"start": s, "end": e} for s, e in building_intervals],
                })
                all_years.extend(pathway.required_state_years())
            except (FileNotFoundError, ValueError):
                continue
        overview = get_pathway_overview(config)
        span = overview.get("span", {})
        return {
            "building_name": building_name,
            "pathways": results,
            "span": span,
        }

    return await run_in_threadpool(fn)


@router.get("/{pathway_name}/building-lifecycle/{building_name}")
async def get_building_lifecycle(config: CEAConfig, pathway_name: str, building_name: str) -> dict[str, Any]:
    from cea.datamanagement.district_pathways.pathway_state import DistrictEvolutionPathway

    def fn():
        pathway = DistrictEvolutionPathway(config, pathway_name=pathway_name)
        intervals = pathway.get_building_lifecycle_intervals()
        building_intervals = intervals.get(building_name, [])
        return {
            "building_name": building_name,
            "pathway_name": pathway_name,
            "intervals": [{"start": s, "end": e} for s, e in building_intervals],
        }

    try:
        return await run_in_threadpool(fn)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{pathway_name}/years/{year}/geojson")
async def get_state_geojson(config: CEAConfig, pathway_name: str, year: int) -> dict[str, Any]:
    from cea.interfaces.dashboard.api.inputs import df_to_json

    locator = cea.inputlocator.InputLocator(config.scenario)
    state_folder = locator.get_state_in_time_scenario_folder(pathway_name, year)
    # The state folder is itself a scenario, so a state-scoped locator
    # owns the canonical zone-geometry path.
    state_locator = cea.inputlocator.InputLocator(state_folder)
    zone_path = state_locator.get_zone_geometry()

    if not os.path.exists(zone_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No baked geometry found for pathway '{pathway_name}' year {year}.",
        )

    def fn():
        geojson, crs = df_to_json(zone_path)
        return {"geojson": geojson, "crs": crs}

    return await run_in_threadpool(fn)


@router.get("/{pathway_name}/timeline")
async def get_timeline(config: CEAConfig, pathway_name: str) -> dict[str, Any]:
    try:
        return await run_in_threadpool(get_pathway_timeline, config, pathway_name)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{pathway_name}/years/{year}", dependencies=[CEASeverDemoAuthCheck])
async def post_year(config: CEAConfig, pathway_name: str, year: int) -> dict[str, Any]:
    try:
        return await run_in_threadpool(create_pathway_year, config, pathway_name, year)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StockYearRequiresEditError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "state_kind": "stock",
                "requires_edit": True,
            },
        ) from exc
    except YearRequiresEditError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "requires_edit": True,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{pathway_name}/years/{year}/editor-options")
async def get_editor_options(
    config: CEAConfig,
    pathway_name: str,
    year: int,
) -> dict[str, Any]:
    try:
        return await run_in_threadpool(
            get_year_editor_options,
            config,
            pathway_name,
            year,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{pathway_name}/years/{year}/building-events", dependencies=[CEASeverDemoAuthCheck])
async def post_building_events(
    config: CEAConfig,
    pathway_name: str,
    year: int,
    payload: BuildingEventsPayload,
) -> dict[str, Any]:
    try:
        return await run_in_threadpool(
            update_year_building_events,
            config,
            pathway_name,
            year,
            new_buildings=payload.new_buildings,
            demolished_buildings=payload.demolished_buildings,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{pathway_name}/years/{year}/apply-templates", dependencies=[CEASeverDemoAuthCheck])
async def post_apply_templates(
    config: CEAConfig,
    pathway_name: str,
    year: int,
    payload: ApplyTemplatesPayload,
) -> dict[str, Any]:
    try:
        return await run_in_threadpool(
            apply_templates_to_year,
            config,
            pathway_name,
            year,
            template_names=payload.template_names,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put("/{pathway_name}/years/{year}/yaml", dependencies=[CEASeverDemoAuthCheck])
async def put_year_yaml(
    config: CEAConfig,
    pathway_name: str,
    year: int,
    payload: RawYearYamlPayload,
) -> dict[str, Any]:
    try:
        return await run_in_threadpool(
            update_year_yaml,
            config,
            pathway_name,
            year,
            raw_yaml=payload.raw_yaml,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{pathway_name}/years/{year}", dependencies=[CEASeverDemoAuthCheck])
async def delete_year(config: CEAConfig, pathway_name: str, year: int) -> dict[str, Any]:
    try:
        return await run_in_threadpool(delete_or_clear_state, config, pathway_name, year)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StockOnlyStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "state_kind": "stock",
                "can_delete": False,
                "can_clear_manual_changes": False,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{pathway_name}/years/{year}/validate-state", dependencies=[CEASeverDemoAuthCheck])
async def post_validate_state(
    config: CEAConfig,
    pathway_name: str,
    year: int,
) -> dict[str, Any]:
    try:
        return await run_in_threadpool(
            validate_baked_state,
            config,
            pathway_name,
            year,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{pathway_name}/validate-log")
async def post_validate_log(config: CEAConfig, pathway_name: str) -> dict[str, Any]:
    try:
        return await run_in_threadpool(validate_pathway_log, config, pathway_name)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


