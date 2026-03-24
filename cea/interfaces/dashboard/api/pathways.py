from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

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

router = APIRouter()


class CreatePathwayPayload(BaseModel):
    pathway_name: str


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
