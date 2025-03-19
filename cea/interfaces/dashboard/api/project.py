import glob
import json
import os
import shutil
import tempfile
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List, Union

import geopandas
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, HTTPException, status, Request, Path, Depends
from geopandas import GeoDataFrame
from osgeo import gdal
from pydantic import BaseModel
from shapely.geometry import shape
from starlette.datastructures import UploadFile as _UploadFile
from typing_extensions import Annotated

import cea.api
import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings, \
    verify_input_typology, COLUMNS_ZONE_TYPOLOGY, COLUMNS_ZONE_GEOMETRY, verify_input_terrain
from cea.datamanagement.surroundings_helper import generate_empty_surroundings
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAProjectRoot, CEAProjectInfo
from cea.interfaces.dashboard.utils import secure_path, OutsideProjectRootError
from cea.utilities.dbf import dbf_to_dataframe
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system, raster_to_WSG_and_UTM

router = APIRouter()

# PATH_REGEX = r'(^[a-zA-Z]:\\[\\\S|*\S]?.*$)|(^(/[^/ ]*)+/?$)'

GENERATE_ZONE_CEA = 'generate-zone-cea'
GENERATE_SURROUNDINGS_CEA = 'generate-surroundings-cea'
GENERATE_TYPOLOGY_CEA = 'generate-typology-cea'
GENERATE_TERRAIN_CEA = 'generate-terrain-cea'
GENERATE_STREET_CEA = 'generate-street-cea'
EMTPY_GEOMETRY = 'none'


class ScenarioPath(BaseModel):
    project: str
    scenario_name: str


class NewProject(BaseModel):
    project_name: str
    project_root: Optional[str] = None


class CreateScenario(BaseModel):
    project: str
    scenario_name: str
    database: Union[str, UploadFile]
    user_zone: Union[str, UploadFile]
    user_surroundings: Union[str, UploadFile]
    generate_zone: Optional[str] = None
    generate_surroundings: Optional[int] = None
    typology: Optional[Union[str, UploadFile]] = None
    weather: Union[str, UploadFile]
    terrain: Union[str, UploadFile]
    street: Union[str, UploadFile]

    @staticmethod
    async def _get_file_path(file: Union[str, UploadFile], directory: str, filename: str) -> str:
        if isinstance(file, str):
            return file

        elif isinstance(file, _UploadFile):
            filepath = os.path.join(directory, filename)
            with open(filepath, "wb") as f:
                f.write(await file.read())
            return filepath

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Could not retrieve {filename}',
            )

    @staticmethod
    async def _get_geometry_data(file: Union[str, UploadFile], filename: str) -> GeoDataFrame:
        source = file

        with tempfile.TemporaryDirectory() as tmpdir:
            if isinstance(source, _UploadFile):

                def extract_zip(filestream: bytes, destination: str) -> None:
                    import zipfile
                    from io import BytesIO

                    with zipfile.ZipFile(BytesIO(filestream)) as zf:
                        zf.extractall(destination)

                extract_zip(await source.read(), tmpdir)

                source = os.path.join(tmpdir, filename)
                if not os.path.exists(source):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Could not find {filename} in zip file',
                    )

            data = geopandas.read_file(source).to_crs(get_geographic_coordinate_system())
        return data

    async def get_zone_file(self):
        return await self._get_geometry_data(self.user_zone, "zone.shp")

    async def get_surroundings_file(self):
        return await self._get_geometry_data(self.user_surroundings, "surroundings.shp")

    async def get_street_file(self):
        return await self._get_geometry_data(self.street, "street.shp")

    @asynccontextmanager
    async def get_weather_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield await self._get_file_path(self.weather, tmpdir, "weather.epw")

    @asynccontextmanager
    async def get_terrain_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield await self._get_file_path(self.terrain, tmpdir, "terrain.tif")

    def should_generate_zone(self) -> bool:
        return self.user_zone == GENERATE_ZONE_CEA

    def should_generate_surroundings(self) -> bool:
        return self.user_surroundings == GENERATE_SURROUNDINGS_CEA

    def should_generate_typology(self) -> bool:
        return self.typology == GENERATE_TYPOLOGY_CEA

    def should_generate_terrain(self) -> bool:
        return self.terrain == GENERATE_TERRAIN_CEA

    def should_generate_street(self) -> bool:
        return self.street == GENERATE_STREET_CEA


class ProjectInfo(BaseModel):
    name: str
    project: str
    scenarios_list: List[str]


class ConfigProjectInfo(BaseModel):
    project: str
    scenario: str



@router.get('/choices')
async def get_project_choices(project_root: CEAProjectRoot):
    """Return project choices based on the project root"""
    if project_root is None or project_root == "":
        raise HTTPException(
            status_code=400,
            detail="Project root not defined",
        )

    try:
        projects = []
        for _path in os.listdir(project_root):
            full_path = os.path.join(project_root, _path)
            if os.path.isdir(full_path) and os.access(full_path, os.R_OK):
                # Optionally: Add validation that this is a valid project directory
                projects.append(_path)
        if not projects:
            return {"projects": [], "warning": "No valid projects found in directory"}
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Permission denied accessing project root",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Project root directory not found",
        )
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read project root: {str(e)}",
        )
    return {
        "projects": projects
    }

@router.get('/config')
async def config_project_info(project_info: CEAProjectInfo) -> ConfigProjectInfo:
    """Return the current project and scenario in the config"""
    return ConfigProjectInfo(
        project=project_info.project,
        scenario=project_info.scenario,
    )


@router.get('/')
async def get_project_info(project_root: CEAProjectRoot, project: str) -> ProjectInfo:
    project_path = project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    try:
        cea_project = secure_path(project_path)
    except OutsideProjectRootError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not os.path.exists(cea_project):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Project: "{project}" does not exist',
        )

    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = cea_project

    project_info = {
        'name': os.path.basename(config.project),
        'project': config.project,
        'scenarios_list': cea.config.get_scenarios_list(config.project)
    }

    return ProjectInfo(**project_info)


@router.post('/')
async def create_new_project(project_root: CEAProjectRoot, new_project: NewProject):
    """
    Create new project folder
    """
    if new_project.project_root is None and project_root is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project root not defined",
        )

    _root = new_project.project_root or project_root
    try:
        project = secure_path(os.path.join(_root, new_project.project_name))
    except OutsideProjectRootError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    try:
        os.makedirs(project, exist_ok=True)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {'message': 'Project folder created', 'project': project}


@router.put('/')
async def update_project(project_root: CEAProjectRoot, config: CEAConfig, scenario_path: ScenarioPath):
    """
    Update Project info in config
    """
    project_path = scenario_path.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    project = secure_path(project_path)
    scenario_name = scenario_path.scenario_name

    if project and scenario_name:
        # Project path must exist but scenario does not have to
        if os.path.exists(project):
            config.project = project
            config.scenario_name = scenario_name
            config.save()
            return {'message': 'Updated project info in config', 'project': project, 'scenario_name': scenario_name}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'project: "{project}" does not exist',
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Parameters not valid - project: {project}, scenario_name: {scenario_name}',
        )


# TODO: Rename this endpoint once the old one is removed
# Temporary endpoint to prevent breaking existing frontend
@router.post('/scenario/v2')
async def create_new_scenario_v2(project_root: CEAProjectRoot, scenario_form: Annotated[CreateScenario, Form()]):
    project_path = scenario_form.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    try:
        cea_project = secure_path(project_path)
    except OutsideProjectRootError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    new_scenario_path = secure_path(os.path.join(cea_project, str(scenario_form.scenario_name).strip()))

    if os.path.exists(new_scenario_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Scenario already exists - project: {cea_project}, scenario_name: {scenario_form.scenario_name}',
        )

    async def create_zone(scenario_form, locator):
        # Generate / Copy zone and surroundings
        if scenario_form.should_generate_zone():
            site_geojson = json.loads(scenario_form.generate_zone)
            site_df = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                             geometry=[shape(site_geojson['features'][0]['geometry'])])
            site_path = locator.get_site_polygon()
            locator.ensure_parent_folder_exists(site_path)
            site_df.to_file(site_path)
            # Generate using zone helper
            from cea.datamanagement.zone_helper import main as zone_helper
            zone_helper(config)

            # Ensure that zone exists
            zone_df = geopandas.read_file(locator.get_zone_geometry())

        # Copy zone from user-input
        else:
            # Copy zone using path
            zone_df = await scenario_form.get_zone_file()

            # Make sure zone column names are in correct case
            zone_df.columns = [col.lower() for col in zone_df.columns]
            rename_dict = {col.lower(): col for col in COLUMNS_ZONE_GEOMETRY}
            zone_df.rename(columns=rename_dict, inplace=True)

            verify_input_geometry_zone(zone_df)

            # Replace invalid characters in building name (characters that would affect path and csv files)
            zone_df["name"] = zone_df["name"].str.replace(r'[\\\/\.,\s]', '_', regex=True)

            zone_path = locator.get_zone_geometry()
            locator.ensure_parent_folder_exists(zone_path)
            zone_df[COLUMNS_ZONE_GEOMETRY + ['geometry']].to_file(zone_path)

        return zone_df

    async def create_surroundings(scenario_form, zone_df, locator):
        if scenario_form.should_generate_surroundings():
            # Generate using surroundings helper
            config.surroundings_helper.buffer = scenario_form.generate_surroundings

            from cea.datamanagement.surroundings_helper import main as surroundings_helper
            surroundings_helper(config)
        elif scenario_form.user_surroundings == EMTPY_GEOMETRY:
            # Generate empty surroundings
            surroundings_df = generate_empty_surroundings(zone_df.crs)

            surroundings_path = locator.get_surroundings_geometry()
            locator.ensure_parent_folder_exists(surroundings_path)
            surroundings_df.to_file(surroundings_path)
        else:
            # Copy surroundings using path
            surroundings_df = await scenario_form.get_surroundings_file()
            verify_input_geometry_surroundings(surroundings_df)

            surroundings_path = locator.get_surroundings_geometry()
            locator.ensure_parent_folder_exists(surroundings_path)
            surroundings_df.to_file(surroundings_path)

    def add_typology(scenario_form, zone_df, locator):
        # Only process typology if zone is not generated from OSM
        if scenario_form.should_generate_zone():
            return

        if scenario_form.typology is not None:
            # Copy typology using path
            _, extension = os.path.splitext(scenario_form.typology)
            if extension == ".dbf":
                typology_df = dbf_to_dataframe(scenario_form.typology)
            elif extension == ".xlsx":
                typology_df = pd.read_excel(scenario_form.typology)
            else:
                raise Exception("Typology file must be a .dbf or .xlsx file")

            # Make sure typology column names are in correct case
            typology_df.columns = [col.lower() for col in typology_df.columns]
            rename_dict = {col.lower(): col for col in COLUMNS_ZONE_TYPOLOGY}
            typology_df.rename(columns=rename_dict, inplace=True)

            verify_input_typology(typology_df)

            # Check if typology index matches zone
            zone_names = set(zone_df["name"])
            typology_names = set(typology_df["name"])
            if not zone_names == typology_names:
                only_in_zone = zone_names.difference(typology_names)
                only_in_typology = typology_names.difference(zone_names)

                zone_message = f'zone has additional names: {", ".join(only_in_zone)} ' if only_in_zone else ''
                typology_message = f'typology has additional names: {", ".join(only_in_typology)}' if only_in_typology else ''

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Building names found in Building geometries (zone) and Building information (typology) do not match. '
                           'Ensure the `name` columns of the two files are identical. '
                           f'{zone_message}{"," if zone_message and typology_message else ""}{typology_message}',
                )

            # merge the typology with the zone
            merged_gdf = zone_df.merge(typology_df, on='name', how='left')

            # create new file
            merged_gdf.to_file(locator.get_zone_geometry(), driver='ESRI Shapefile')
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='User to provide Building information: construction year, '
                                       'construction type, use types and their ratios.',
                                )

    async def create_terrain(scenario_form, zone_df, locator):
        if scenario_form.should_generate_terrain():
            # Run terrain helper
            from cea.datamanagement.terrain_helper import main as terrain_helper
            terrain_helper(config)
        else:
            # Copy terrain using path
            centroid = zone_df.dissolve().centroid.values[0]
            lat, lon = centroid.y, centroid.x
            locator.ensure_parent_folder_exists(locator.get_terrain())

            async with scenario_form.get_terrain_file() as terrain_path:
                # Ensure terrain is the same projection system
                terrain = raster_to_WSG_and_UTM(terrain_path, lat, lon)
                driver = gdal.GetDriverByName('GTiff')
                verify_input_terrain(terrain)
                driver.CreateCopy(locator.get_terrain(), terrain)

    async def create_street(scenario_form, locator):
        if scenario_form.should_generate_street():
            # Run street helper
            from cea.datamanagement.streets_helper import main as streets_helper
            streets_helper(config)
        elif scenario_form.street != EMTPY_GEOMETRY:
            # Copy street using path
            street_df = await scenario_form.get_street_file()
            locator.ensure_parent_folder_exists(locator.get_street_network())
            street_df.to_file(locator.get_street_network())

    with tempfile.TemporaryDirectory() as tmp:
        # Create temporary project before copying to actual scenario path
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.project = tmp
        config.scenario_name = "temp_scenario"
        locator = cea.inputlocator.InputLocator(config.scenario)

        from cea.datamanagement.database_helper import main as database_helper

        try:
            # Run database-helper to copy databases to input
            config.database_helper.databases_path = scenario_form.database
            database_helper(config)

            # Generate / Copy zone
            zone_df = await create_zone(scenario_form, locator)

            # Add typology to zone
            add_typology(scenario_form, zone_df, locator)

            # Generate / Copy surroundings
            await create_surroundings(scenario_form, zone_df, locator)

            # Run weather helper
            async with scenario_form.get_weather_file() as weather_path:
                config.weather_helper.weather = weather_path
                from cea.datamanagement.weather_helper import main as weather_helper
                weather_helper(config)

            # Generate / Copy terrain
            await create_terrain(scenario_form, zone_df, locator)

            # Generate / Copy street
            await create_street(scenario_form, locator)

            # Run archetypes mapper
            from cea.datamanagement.archetypes_mapper import main as archetypes_mapper
            archetypes_mapper(config)

            # Move temp scenario to correct path
            print(f"Moving from {config.scenario} to {new_scenario_path}")
            shutil.move(config.scenario, new_scenario_path)
        except HTTPException as e:
            raise e from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Uncaught exception: {e}',
            ) from e

    return {
        'message': 'Scenario created successfully',
        'project': scenario_form.project,
        'scenario_name': scenario_form.scenario_name
    }


def glob_shapefile_auxilaries(shapefile_path):
    """Returns a list of files in the same folder as ``shapefile_path``, but allows for varying extensions.
    This gets the .dbf, .shx, .prj, .shp and .cpg files"""
    return glob.glob('{basepath}.*'.format(basepath=os.path.splitext(shapefile_path)[0]))


async def check_scenario_exists(request: Request, scenario: str = Path()):
    try:
        data = await request.json()
        project = data.get("project")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine project and scenario",
        )

    choices = cea.config.get_scenarios_list(project)
    if scenario not in choices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Scenario does not exist.',
        )


# FIXME: Potential Issue. Need to check if the scenario being deleted/renamed is running in scripts.
@router.get('/scenario/{scenario}', dependencies=[Depends(check_scenario_exists)])
async def get(scenario: str):
    """Scenario details"""
    return {'name': scenario}


@router.put('/scenario/{scenario}', dependencies=[Depends(check_scenario_exists)])
async def put(config: CEAConfig, scenario: str, payload: Dict[str, Any]):
    """Update scenario"""
    scenario_path = secure_path(os.path.join(config.project, scenario))
    new_scenario_name: str = payload.get('name')
    try:
        if new_scenario_name is not None:
            new_path = secure_path(os.path.join(config.project, new_scenario_name))
            os.rename(scenario_path, new_path)
            if config.scenario_name == scenario:
                config.scenario_name = new_scenario_name
                config.save()
            return {'name': new_scenario_name}
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Make sure that the scenario you are trying to rename is not open in any application. '
                   'Try and refresh the page again.',
        )


@router.delete('/scenario/{scenario}', dependencies=[Depends(check_scenario_exists)])
async def delete(project_info: CEAProjectInfo, scenario: str):
    """Delete scenario from project"""
    scenario_path = secure_path(os.path.join(project_info.project, scenario))
    try:
        # TODO: Check for any current open scenarios or jobs
        shutil.rmtree(scenario_path)
        return {'scenarios': cea.config.get_scenarios_list(project_info.project)}
    except OSError:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Make sure that the scenario you are trying to delete is not open in any application. '
                   'Try and refresh the page again.',
        )


class ZoneFileNotFound(ValueError):
    """Raised when a zone file is not found."""
