import json
import os
from typing import Literal, Optional

import osmnx
import pandas as pd
import requests
from fastapi import APIRouter, HTTPException, status

import geopandas as gpd
from osmnx._errors import ResponseStatusCodeError
from pydantic import BaseModel

from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings, \
    verify_input_typology, COLUMNS_ZONE_TYPOLOGY, COLUMNS_ZONE_GEOMETRY, \
    OPTIONAL_COLUMNS_ZONE_GEOMETRY
from cea.interfaces.dashboard.utils import secure_path

router = APIRouter()


@router.get("/buildings")
async def fetch_buildings(generate: bool = False, polygon: str = None, path: str = None):
    if generate:
        if polygon is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing polygon")
        try:
            site_polygon = gpd.read_file(polygon, crs="epsg:4326")

            if site_polygon.empty:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty polygon")

            buildings = osmnx.features_from_polygon(polygon=site_polygon['geometry'].values[0], tags={"building": True})

            # Drop all columns except geometry to reduce file size
            buildings = gpd.GeoDataFrame(geometry=buildings['geometry'], crs="epsg:4326")

            return json.loads(buildings.to_json())

        except HTTPException:
            raise
        except (ResponseStatusCodeError, requests.RequestException) as e:
            # The public Overpass API is shared infrastructure and is often overloaded (502/503/504, timeouts)
            print(e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The OpenStreetMap (Overpass) server is currently unavailable or overloaded. "
                       "Please try again in a few minutes.")
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    elif path is not None:
        try:
            _path = secure_path(path)
            buildings = gpd.read_file(_path).to_crs("epsg:4326")

            return json.loads(buildings.to_json())
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing path")

        try:
            building_df = gpd.read_file(data.path)
            if data.building == 'zone':

                # Make sure zone column names are in correct case
                building_df.columns = [col.lower() for col in building_df.columns]
                rename_dict = {col.lower(): col
                               for col in COLUMNS_ZONE_GEOMETRY + OPTIONAL_COLUMNS_ZONE_GEOMETRY}
                building_df.rename(columns=rename_dict, inplace=True)

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing path")

        _, extension = os.path.splitext(data.path)
        try:
            if extension == ".xlsx":
                typology_df = pd.read_excel(data.path)
            else:
                typology_df = gpd.read_file(data.path)


            # Make sure typology column names are in correct case
            typology_df.columns = [col.lower() for col in typology_df.columns]
            rename_dict = {col.lower(): col for col in COLUMNS_ZONE_TYPOLOGY}
            typology_df.rename(columns=rename_dict, inplace=True)

            verify_input_typology(typology_df)
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        return {}
