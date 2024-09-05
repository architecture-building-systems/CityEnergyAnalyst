import json
from typing import Literal, Optional

import osmnx
from fastapi import APIRouter, HTTPException, status

import geopandas as gpd
from pydantic import BaseModel

from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings, \
    verify_input_typology
from cea.interfaces.dashboard.utils import secure_path

router = APIRouter()


@router.get("/buildings")
async def fetch_buildings(generate: bool = False, polygon: str = None, path: str = None):
    if generate:
        if polygon is None:
            return HTTPException(status_code=400, detail="Missing polygon")
        try:
            site_polygon = gpd.read_file(polygon, crs="epsg:4326")

            if site_polygon.empty:
                raise HTTPException(status_code=400, detail="Empty polygon")

            buildings = osmnx.features_from_polygon(polygon=site_polygon['geometry'].values[0], tags={"building": True})

            # Drop all columns except geometry to reduce file size
            buildings = gpd.GeoDataFrame(geometry=buildings['geometry'], crs="epsg:4326")

            return json.loads(buildings.to_json())

        except Exception as e:
            print(e)
            return HTTPException(status_code=500, detail=str(e))

    elif path is not None:
        try:
            _path = secure_path(path)
            buildings = gpd.read_file(_path).to_crs("epsg:4326")

            return json.loads(buildings.to_json())
        except Exception as e:
            print(e)
            return HTTPException(status_code=500, detail=str(e))


class ValidateGeometry(BaseModel):
    type: Literal['path', 'file']
    building: Literal['zone', 'surroundings']
    path: Optional[str] = None
    file: Optional[str] = None

@router.post("/buildings/validate")
async def validate_building_geometry(data: ValidateGeometry):
    """Validate the given building geometry"""
    if data.type == 'path':
        if data.path is None:
            raise HTTPException(status_code=400, detail="Missing path")

        try:
            building_df = gpd.read_file(data.path)
            print(building_df)
            if data.building == 'zone':
                verify_input_geometry_zone(building_df)
            elif data.building == 'surroundings':
                verify_input_geometry_surroundings(building_df)
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        return {}


class ValidateTypology(BaseModel):
    type: Literal['path', 'file']
    path: Optional[str] = None
    file: Optional[str] = None


# TODO: Find a more suitable route
@router.post("/typology/validate")
async def validate_typology(data: ValidateTypology):
    """Validate the given typology"""
    if data.type == 'path':
        if data.path is None:
            raise HTTPException(status_code=400, detail="Missing path")

        try:
            typology_df = gpd.read_file(data.path)
            verify_input_typology(typology_df)
            print(typology_df)
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        return {}
