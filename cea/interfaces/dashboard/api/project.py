import glob
import os
import shutil
import tempfile
import traceback
from typing import Dict, Any, Optional

import geopandas
import pandas as pd
from fastapi import APIRouter, HTTPException, status, Request, Path, Depends
from pydantic import BaseModel
from shapely.geometry import shape
from fastapi.concurrency import run_in_threadpool
from staticmap import StaticMap, Polygon

import cea.config
import cea.api
import cea.inputlocator
from cea.databases import get_regions, databases_folder_path
from cea.datamanagement.create_new_scenario import generate_default_typology, copy_typology, copy_terrain
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings, \
    verify_input_typology, COLUMNS_ZONE_TYPOLOGY, COLUMNS_ZONE_GEOMETRY
from cea.datamanagement.surroundings_helper import generate_empty_surroundings
from cea.interfaces.dashboard.dependencies import CEAConfig
from cea.interfaces.dashboard.settings import get_settings
from cea.interfaces.dashboard.utils import secure_path, InvalidPathError
from cea.plots.colors import color_to_rgb
from cea.utilities.dbf import dataframe_to_dbf
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

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
    project_root: str


class CreateScenario(BaseModel):
    project: str
    scenario_name: str
    database: str
    user_zone: str
    user_surroundings: str
    generate_zone: Optional[dict] = None
    generate_surroundings: Optional[int] = None
    typology: Optional[str] = None
    weather: str
    terrain: str
    street: str

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


@router.get('/')
async def get_project_info(config: CEAConfig, project: str = None):
    if project is None:
        scenario_name = config.scenario_name
    else:
        project = secure_path(project)
        if not os.path.exists(project):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Project path: "{project}" does not exist',
            )
        config.project = project
        scenario_name = None

    # FIXME: This exposes the project path to the frontend. Should be removed.
    project_info = {
        'project_name': os.path.basename(config.project),
        'project': config.project,
        'scenario_name': scenario_name,
        'scenarios_list': list_scenario_names_for_project(config)
    }

    # List projects if no path transversal is allowed
    if not get_settings().allow_path_transversal():
        def valid_project(project_name):
            return not project_name.startswith(".")

        projects = [
            project_name for project_name in os.listdir(get_settings().project_root)
            if valid_project(project_name)
        ]
        project_info['projects'] = projects

    return project_info


@router.post('/')
async def create_new_project(new_project: NewProject):
    """
    Create new project folder
    """
    project_name = new_project.project_name
    project_root = new_project.project_root

    if project_name and project_root:
        try:
            project = secure_path(os.path.join(project_root, project_name))
        except InvalidPathError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path `{project_root}` is not a valid path. Path is outside of project root.",
            )
        try:
            os.makedirs(project, exist_ok=True)
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        return {'message': 'Project folder created', 'project': project}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Parameters not valid - project_name: {project_name}, project_root: {project_root}',
        )


@router.put('/')
async def update_project(config: CEAConfig, scenario_path: ScenarioPath):
    """
    Update Project info in config
    """
    project = secure_path(scenario_path.project)
    scenario_name = scenario_path.scenario_name

    if project and scenario_name:
        # Project path must exist but scenario does not have to
        if os.path.exists(project):
            config.project = project
            config.scenario_name = scenario_name
            await config.save()
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
async def create_new_scenario_v2(scenario_form: CreateScenario):
    print(f'ScenarioForm: {scenario_form}')
    new_scenario_path = secure_path(os.path.join(scenario_form.project, str(scenario_form.scenario_name).strip()))

    if os.path.exists(new_scenario_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Scenario already exists - project: {scenario_form.project}, scenario_name: {scenario_form.scenario_name}',
        )

    def create_zone(scenario_form, locator):
        # Generate / Copy zone and surroundings
        if scenario_form.should_generate_zone():
            site_geojson = scenario_form.generate_zone
            site_df = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                             geometry=[shape(site_geojson['features'][0]['geometry'])])
            site_path = locator.get_site_polygon()
            locator.ensure_parent_folder_exists(site_path)
            site_df.to_file(site_path)
            # Generate using zone helper
            cea.api.zone_helper(config)

            # Ensure that zone exists
            zone_df = geopandas.read_file(locator.get_zone_geometry())
        else:
            # Copy zone using path
            zone_df = geopandas.read_file(scenario_form.user_zone).to_crs(get_geographic_coordinate_system())

            # Make sure zone column names are in correct case
            zone_df.columns = [col.lower() for col in zone_df.columns]
            rename_dict = {col.lower(): col for col in COLUMNS_ZONE_GEOMETRY}
            zone_df.rename(columns=rename_dict, inplace=True)

            verify_input_geometry_zone(zone_df)

            # Replace invalid characters in building name (characters that would affect path and csv files)
            zone_df["Name"] = zone_df["Name"].str.replace(r'[\\\/\.,\s]', '_', regex=True)

            zone_path = locator.get_zone_geometry()
            locator.ensure_parent_folder_exists(zone_path)
            zone_df[COLUMNS_ZONE_GEOMETRY + ['geometry']].to_file(zone_path)

        return zone_df

    def create_surroundings(scenario_form, zone_df, locator):
        if scenario_form.should_generate_surroundings():
            # Generate using surroundings helper
            config.surroundings_helper.buffer = scenario_form.generate_surroundings
            cea.api.surroundings_helper(config)
        elif scenario_form.user_surroundings == EMTPY_GEOMETRY:
            # Generate empty surroundings
            surroundings_df = generate_empty_surroundings(zone_df.crs)

            surroundings_path = locator.get_surroundings_geometry()
            locator.ensure_parent_folder_exists(surroundings_path)
            surroundings_df.to_file(surroundings_path)
        else:
            # Copy surroundings using path
            surroundings_df = geopandas.read_file(scenario_form.user_surroundings).to_crs(
                get_geographic_coordinate_system())
            verify_input_geometry_surroundings(surroundings_df)

            surroundings_path = locator.get_surroundings_geometry()
            locator.ensure_parent_folder_exists(surroundings_path)
            surroundings_df.to_file(surroundings_path)

    def create_typology(scenario_form, zone_df, locator):
        # Only process typology if zone is not generated
        if scenario_form.should_generate_zone():
            return

        locator.ensure_parent_folder_exists(locator.get_building_typology())
        if scenario_form.should_generate_typology():
            # Generate using default typology
            generate_default_typology(zone_df, locator)
        elif scenario_form.typology is not None:
            # Copy typology using path
            _, extension = os.path.splitext(scenario_form.typology)
            if extension == ".xlsx":
                typology_df = pd.read_excel(scenario_form.typology)
            else:
                typology_df = geopandas.read_file(scenario_form.typology)

            # Make sure typology column names are in correct case
            typology_df.columns = [col.lower() for col in typology_df.columns]
            rename_dict = {col.lower(): col for col in COLUMNS_ZONE_TYPOLOGY}
            typology_df.rename(columns=rename_dict, inplace=True)

            verify_input_typology(typology_df)

            # Check if typology index matches zone
            zone_names = set(zone_df["Name"])
            typology_names = set(typology_df["Name"])
            if not zone_names == typology_names:
                only_in_zone = zone_names.difference(typology_names)
                only_in_typology = typology_names.difference(zone_names)

                zone_message =  f'zone has additional names: {", ".join(only_in_zone)} ' if only_in_zone else ''
                typology_message = f'typology has additional names: {", ".join(only_in_typology)}' if only_in_typology else ''

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Names found in Building geometries (zone) and Building information (typology) do not match. '
                           'Ensure the `Name` columns of the two files are identical. '
                            f'{zone_message}{"," if zone_message and typology_message else ""}{typology_message}',
                )

            copy_typology(scenario_form.typology, locator)
        else:
            # Try extracting typology from zone
            print('Trying to extract typology from zone')

            # Make sure typology column names are in correct case
            zone_df.columns = [col.lower() for col in zone_df.columns]
            rename_dict = {col.lower(): col for col in COLUMNS_ZONE_TYPOLOGY}
            zone_df.rename(columns=rename_dict, inplace=True)

            try:
                verify_input_typology(zone_df)
            except Exception as e:
                print(f'Could not extract typology from zone: {e}')
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Not enough information to generate typology file from zone file.'
                           'Check zone file for the required typology.',
                )

            typology_df = zone_df[COLUMNS_ZONE_TYPOLOGY]
            dataframe_to_dbf(typology_df, locator.get_building_typology())
            print(f'Typology file created at {locator.get_building_typology()}')

    def create_terrain(scenario_form, zone_df, locator):
        if scenario_form.should_generate_terrain():
            # Run terrain helper
            cea.api.terrain_helper(config)
        else:
            # Copy terrain using path
            centroid = zone_df.dissolve().centroid.values[0]
            lat, lon = centroid.y, centroid.x
            locator.ensure_parent_folder_exists(locator.get_terrain())
            copy_terrain(scenario_form.terrain, locator, lat, lon)

    def create_street(scenario_form, locator):
        if scenario_form.should_generate_street():
            # Run street helper
            cea.api.streets_helper(config)
        elif scenario_form.street != EMTPY_GEOMETRY:
            # Copy street using path
            street_df = geopandas.read_file(scenario_form.street).to_crs(get_geographic_coordinate_system())
            locator.ensure_parent_folder_exists(locator.get_street_network())
            street_df.to_file(locator.get_street_network())

    with tempfile.TemporaryDirectory() as tmp:
        # Create temporary project before copying to actual scenario path
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.project = tmp
        config.scenario_name = "temp_scenario"
        locator = cea.inputlocator.InputLocator(config.scenario)

        try:
            # Run database_initializer to copy databases to input
            cea.api.data_initializer(config, databases_path=scenario_form.database)

            # Generate / Copy zone
            zone_df = create_zone(scenario_form, locator)

            # Generate / Copy typology
            create_typology(scenario_form, zone_df, locator)

            # Generate / Copy surroundings
            create_surroundings(scenario_form, zone_df, locator)

            # Run weather helper
            config.weather_helper.weather = scenario_form.weather
            cea.api.weather_helper(config)

            # Generate / Copy terrain
            create_terrain(scenario_form, zone_df, locator)

            # Generate / Copy street
            create_street(scenario_form, locator)

            # Run archetypes mapper
            cea.api.archetypes_mapper(config)

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


@router.post('/scenario/')
async def create_new_scenario(config: CEAConfig, payload: Dict[str, Any]):
    """
    Create new scenario
    """
    project = secure_path(payload.get('project'))
    scenario_name = payload.get('scenario_name')
    if scenario_name is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='scenario_name parameter cannot be empty',
        )

    databases_path = payload.get('databases_path')
    input_data = payload.get('input_data')

    # Ignore using secure databases_path and only allow the default databases_path
    if databases_path not in (os.path.join(databases_folder_path, region) for region in get_regions()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid databases_path: {databases_path}',
        )

    with tempfile.TemporaryDirectory() as tmp:
        config.project = tmp
        config.scenario_name = "temp_scenario"

        _project = project or config.project

        locator = cea.inputlocator.InputLocator(config.scenario)

        # Run database_initializer to copy databases to input
        if databases_path is not None:
            try:
                cea.api.data_initializer(config, databases_path=databases_path)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f'data_initializer: {e}',
                ) from e

        if input_data == 'import':
            files = payload.get('files')
            if files is not None:
                try:
                    output_path, project_name = os.path.split(config.project)
                    cea.api.create_new_scenario(config,
                                                output_path=output_path,
                                                project=project_name,
                                                scenario=config.scenario_name,
                                                zone=files.get('zone'),
                                                surroundings=files.get('surroundings'),
                                                streets=files.get('streets'),
                                                terrain=files.get('terrain'),
                                                typology=files.get('typology'))
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'create_new_scenario: {e}',
                    ) from e

        elif input_data == 'copy':
            source_scenario_name = payload.get('copy_scenario')
            source_scenario = secure_path(os.path.join(_project, source_scenario_name))
            os.makedirs(locator.get_input_folder(), exist_ok=True)
            shutil.copytree(cea.inputlocator.InputLocator(source_scenario).get_input_folder(),
                            locator.get_input_folder())

        elif input_data == 'generate':
            tools = payload.get('tools', [])
            for tool in tools:
                try:
                    if tool == 'zone':
                        # FIXME: Setup a proper endpoint for site creation
                        site_geojson = payload.get('geojson')
                        if site_geojson is None:
                            raise ValueError('Could not find GeoJson for site polygon')
                        site = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                                      geometry=[shape(site_geojson['features'][0]['geometry'])])
                        site_path = locator.get_site_polygon()
                        locator.ensure_parent_folder_exists(site_path)
                        site.to_file(site_path)
                        print(f'site.shp file created at {site_path}')
                        cea.api.zone_helper(config)
                    elif tool == 'surroundings':
                        cea.api.surroundings_helper(config)
                    elif tool == 'streets':
                        cea.api.streets_helper(config)
                    elif tool == 'terrain':
                        cea.api.terrain_helper(config)
                    elif tool == 'weather':
                        # Fetch weather as default if weather is not set
                        # (old versions of GUI might return empty string as default)
                        if config.weather_helper.weather == "":
                            config.weather_helper.weather = "climate.onebuilding.org"
                        cea.api.weather_helper(config)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'{tool}_helper: {e}',
                    ) from e

        # Move temp scenario to correct path
        new_scenario_path = secure_path(os.path.join(_project, str(scenario_name).strip()))
        print(f"Moving from {config.scenario} to {new_scenario_path}")
        shutil.move(config.scenario, new_scenario_path)

    return {'scenarios_list': list_scenario_names_for_project(config)}


def glob_shapefile_auxilaries(shapefile_path):
    """Returns a list of files in the same folder as ``shapefile_path``, but allows for varying extensions.
    This gets the .dbf, .shx, .prj, .shp and .cpg files"""
    return glob.glob('{basepath}.*'.format(basepath=os.path.splitext(shapefile_path)[0]))


def list_scenario_names_for_project(config):
    with config.ignore_restrictions():
        return config.get_parameter('general:scenario-name')._choices


async def check_scenario_exists(request: Request, config: CEAConfig, scenario: str = Path()):
    try:
        data = await request.json()
    except Exception:
        data = None

    if len(data):
        try:
            config.project = data["project"]
        except Exception:
            pass
    choices = list_scenario_names_for_project(config)
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
                await config.save()
            return {'name': new_scenario_name}
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Make sure that the scenario you are trying to rename is not open in any application. '
                   'Try and refresh the page again.',
        )


@router.delete('/scenario/{scenario}', dependencies=[Depends(check_scenario_exists)])
async def delete(config: CEAConfig, scenario: str):
    """Delete scenario from project"""
    scenario_path = secure_path(os.path.join(config.project, scenario))
    try:
        shutil.rmtree(scenario_path)
        return {'scenarios': list_scenario_names_for_project(config)}
    except OSError:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Make sure that the scenario you are trying to delete is not open in any application. '
                   'Try and refresh the page again.',
        )


class ZoneFileNotFound(ValueError):
    """Raised when a zone file is not found."""


def generate_scenario_image(config, scenario: str, image_path: str, building_limit: int = 500):
    locator = cea.inputlocator.InputLocator(os.path.join(config.project, scenario))
    zone_path = locator.get_zone_geometry()

    if not os.path.isfile(zone_path):
        raise ZoneFileNotFound

    zone_modified = os.path.getmtime(zone_path)
    if not os.path.isfile(image_path):
        image_modified = 0
    else:
        image_modified = os.path.getmtime(image_path)

    if zone_modified > image_modified:
        print(f'Generating preview image for scenario: {scenario}')
        # Make sure .cache folder exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        zone_df = geopandas.read_file(zone_path)
        zone_df = zone_df.to_crs(get_geographic_coordinate_system())
        polygons = zone_df['geometry']

        m = StaticMap(256, 160, url_template='http://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png')
        if len(polygons) <= building_limit:
            polygons = [list(polygons.geometry.exterior[row_id].coords) for row_id in range(polygons.shape[0])]
            for polygon in polygons:
                out = Polygon(polygon, color_to_rgb('purple'), 'black', False)
                m.add_polygon(out)
        else:
            print(f'Number of buildings({len(polygons)}) exceed building limit({building_limit}): '
                  f'Generating simplified image')
            # Generate only the shape outline of the zone area
            convex_hull = polygons.unary_union.convex_hull
            polygon = convex_hull.exterior.coords
            out = Polygon(polygon, None, color_to_rgb('purple'), False)
            m.add_polygon(out)

        image = m.render()
        image.save(image_path)


@router.get('/scenario/{scenario}/image')
async def get_scenario_image(config: CEAConfig, project: str, scenario: str):
    if project is not None:
        project = secure_path(project)
        if not os.path.exists(project):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Project path: "{project}" does not exist',
            )
        config.project = project

    choices = list_scenario_names_for_project(config)

    if scenario not in choices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Scenario does not exist',
        )

    cache_path = os.path.join(config.project, '.cache')
    image_path = os.path.join(cache_path, scenario + '.png')
    try:
        await run_in_threadpool(lambda: generate_scenario_image(config, scenario, image_path))
    except ZoneFileNotFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Zone file not found',
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    import base64
    with open(image_path, 'rb') as imgFile:
        image = base64.b64encode(imgFile.read())

    return {'image': image.decode("utf-8")}
