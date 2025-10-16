import io
import json
import os
import shutil
import sys
import tempfile
import traceback
import warnings
from collections import defaultdict
from contextlib import redirect_stdout
from typing import Dict, Any
import zipfile

from fastapi.responses import StreamingResponse
import geopandas
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fiona.errors import DriverError
from pydantic import BaseModel, Field

import cea.config
import cea.inputlocator
import cea.schemas
from cea.databases import CEADatabase, CEADatabaseException
from cea.datamanagement.format_helper.cea4_verify_db import cea4_verify_db
from cea.interfaces.dashboard.dependencies import CEAProjectInfo, CEASeverDemoAuthCheck
from cea.interfaces.dashboard.utils import secure_path
from cea.plots.supply_system.a_supply_system_map import get_building_connectivity, newer_network_layout_exists
from cea.plots.variable_naming import get_color_array
from cea.technologies.network_layout.main import layout_network, NetworkLayout
from cea.utilities.schedule_reader import schedule_to_file, read_cea_schedule, save_cea_schedules
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

router = APIRouter()

COLORS = {
    'surroundings': get_color_array('grey_light'),
    'disconnected': get_color_array('white')
}

# List of input databases (db_name, locator/schema_key)
INPUT_DATABASES = [
    ('zone', 'get_zone_geometry'),
    ('envelope', 'get_building_architecture'),
    ('internal-loads', 'get_building_internal'),
    ('indoor-comfort', 'get_building_comfort'),
    ('hvac', 'get_building_air_conditioning'),
    ('supply', 'get_building_supply'),
    ('surroundings', 'get_surroundings_geometry'),
    ('trees', "get_tree_geometry")
]


def get_input_database_schemas():
    """Parse the schemas.yml file and create the dictionary of column types"""
    schemas = cea.schemas.schemas(plugins=[])
    input_database_schemas = dict()
    for db_name, locator in INPUT_DATABASES:
        schema = schemas[locator]
        input_database_schemas[db_name] = {
            'file_type': schema['file_type'],
            'location': locator,
            'columns': schema['schema']['columns']
        }
    return input_database_schemas


INPUTS = get_input_database_schemas()
INPUT_KEYS = INPUTS.keys()
GEOJSON_KEYS = ['zone', 'surroundings', 'trees', 'streets', 'dc', 'dh']
NETWORK_KEYS = ['dc', 'dh']


@router.get("/")
async def get_keys():
    return {'buildingProperties': INPUT_KEYS, 'geoJSONs': GEOJSON_KEYS}


@router.get('/building-properties/{db}')
async def get_building_props_db(db: str):
    if db not in INPUTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Input file not found: {db}',
        )
    db_info = INPUTS[db]
    columns = dict()
    for column_name, column in db_info['columns'].items():
        columns[column_name] = column['type']
    return columns


@router.get('/geojson/{kind}')
async def get_input_geojson(project_info: CEAProjectInfo, kind: str):
    locator = cea.inputlocator.InputLocator(project_info.scenario)

    if kind not in GEOJSON_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Input file not found: {kind}',
        )
    # Building geojsons
    elif kind in INPUT_KEYS and kind in GEOJSON_KEYS:
        db_info = INPUTS[kind]
        locator = cea.inputlocator.InputLocator(project_info.scenario)
        location = getattr(locator, db_info['location'])()
        if db_info['file_type'] != 'shp':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Invalid database for geojson: {location}',
            )
        return df_to_json(location)[0]
    elif kind in NETWORK_KEYS:
        return get_network(project_info.scenario, kind)[0]
    elif kind == 'streets':
        return df_to_json(locator.get_street_network())[0]


@router.get('/building-properties')
async def get_building_props(project_info: CEAProjectInfo):
    return get_building_properties(project_info.scenario)


@router.get('/all-inputs')
async def get_all_inputs(project_info: CEAProjectInfo):
    locator = cea.inputlocator.InputLocator(project_info.scenario)

    # FIXME: Find a better way, current used to test for Input Editor
    def fn():
        store = get_building_properties(project_info.scenario)
        store['geojsons'] = {}
        store['connected_buildings'] = {'dc': [], 'dh': []}
        store['crs'] = {}
        store['geojsons']['zone'], store['crs']['zone'] = df_to_json(locator.get_zone_geometry())
        store['geojsons']['surroundings'], store['crs']['surroundings'] = df_to_json(
            locator.get_surroundings_geometry())
        store['geojsons']['trees'], store['crs']['trees'] = df_to_json(locator.get_tree_geometry())
        store['geojsons']['streets'], store['crs']['streets'] = df_to_json(locator.get_street_network())
        # store['geojsons']['dc'], store['connected_buildings']['dc'], store['crs']['dc'] = get_network(config, 'dc')
        # store['geojsons']['dh'], store['connected_buildings']['dh'],  store['crs']['dh'] = get_network(config, 'dh')
        store['geojsons']['dc'] = None
        store['geojsons']['dh'] = None
        store['colors'] = COLORS
        store['schedules'] = {}

        return store

    return await run_in_threadpool(fn)


class InputForm(BaseModel):
    tables: Dict[str, Any] = Field(default_factory=dict)
    geojsons: Dict[str, Any] = Field(default_factory=dict)
    crs: Dict[str, Any] = Field(default_factory=dict)
    schedules: Dict[str, Any] = Field(default_factory=dict)


@router.put('/all-inputs', dependencies=[CEASeverDemoAuthCheck])
async def save_all_inputs(project_info: CEAProjectInfo, form: InputForm):
    locator = cea.inputlocator.InputLocator(project_info.scenario)

    tables = form.tables
    geojsons = form.geojsons
    crs = form.crs
    schedules = form.schedules

    def fn():
        out = {'tables': {}, 'geojsons': {}}

        # TODO: Maybe save the files to temp location in case something fails
        for db in INPUTS:
            db_info = INPUTS[db]
            location = getattr(locator, db_info['location'])()
            file_type = db_info['file_type']

            if tables.get(db) is None:  # ignore if table does not exist
                continue

            if len(tables[db]):
                if file_type == 'shp':
                    table_df = geopandas.GeoDataFrame.from_features(geojsons[db]['features'],
                                                                    crs=get_geographic_coordinate_system())
                    out['geojsons'][db] = json.loads(table_df.to_json())
                    table_df = table_df.to_crs(crs[db])
                    table_df.to_file(location, driver='ESRI Shapefile', encoding='ISO-8859-1')

                    table_df = pd.DataFrame(table_df.drop(columns='geometry'))
                    out['tables'][db] = json.loads(table_df.set_index('name').to_json(orient='index'))
                elif file_type == 'csv':
                    table_df = pd.DataFrame.from_dict(tables[db], orient='index')

                    # Make sure index name is 'Name;
                    table_df.index.name = 'name'
                    table_df = table_df.reset_index()
                    table_df.to_csv(location, index=False)
                    out['tables'][db] = json.loads(table_df.set_index('name').to_json(orient='index'))

            else:  # delete file if empty unless it is surroundings (allow for empty surroundings file)
                if db == "surroundings":
                    table_df = geopandas.GeoDataFrame(columns=["name", "height_ag", "floors_ag"], geometry=[],
                                                      crs=get_geographic_coordinate_system())
                    table_df.to_file(location)

                    out['tables'][db] = []

                elif os.path.isfile(location):
                    if file_type == 'shp':
                        import glob
                        for filepath in glob.glob(os.path.join(locator.get_building_geometry_folder(), '%s.*' % db)):
                            os.remove(filepath)
                    elif file_type == 'dbf':
                        os.remove(location)

                if file_type == 'shp':
                    out['geojsons'][db] = {}

        if schedules:
            for building in schedules:
                schedule_dict = schedules[building]
                schedule_path = locator.get_building_weekly_schedules(building)
                schedule_data = schedule_dict['SCHEDULES']
                # schedule_complementary_data = {'MONTHLY_MULTIPLIER': schedule_dict['MONTHLY_MULTIPLIER'],
                #                                'METADATA': schedule_dict['METADATA']}
                data = pd.DataFrame()
                for day in ['WEEKDAY', 'SATURDAY', 'SUNDAY']:
                    df = pd.DataFrame({'HOUR': range(1, 25), 'DAY': [day] * 24})
                    for schedule_type, schedule in schedule_data.items():
                        df[schedule_type] = schedule[day]
                    data = pd.concat([df, data], ignore_index=True)
                save_cea_schedules(data.to_dict('list'), schedule_path)
                print('Schedule file written to {}'.format(schedule_path))

        return out

    return await run_in_threadpool(fn)


def get_building_properties(scenario: str):
    locator = cea.inputlocator.InputLocator(scenario)
    store = {'tables': {}, 'columns': {}}
    for db in INPUTS:
        db_info = INPUTS[db]
        locator_method = db_info['location']
        file_path = getattr(locator, locator_method)()
        file_type = db_info['file_type']
        db_columns = db_info['columns']

        # Get building property data from file
        try:
            if file_type == 'shp':
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

                table_df = geopandas.read_file(file_path)
                table_df = pd.DataFrame(
                    table_df.drop(columns='geometry'))
                if 'geometry' in db_columns:
                    del db_columns['geometry']
                if 'reference' in db_columns and 'reference' not in table_df.columns:
                    table_df['reference'] = None
                store['tables'][db] = json.loads(
                    table_df.set_index('name').to_json(orient='index'))
            else:
                table_df = pd.read_csv(file_path)
                if 'reference' in db_columns and 'reference' not in table_df.columns:
                    table_df['reference'] = None
                store['tables'][db] = table_df.set_index("name").to_dict(orient='index')
        except (IOError, DriverError, ValueError, FileNotFoundError) as e:
            print(f"Error reading {db} from {file_path}: {e}")
            # Continue to try getting column definitions
            store['tables'][db] = None

        # Get column definitions from schema
        columns = defaultdict(dict)
        try:
            for column_name, column in db_columns.items():
                columns[column_name]['type'] = column['type']
                if 'choice' in column:
                    path = getattr(locator, column['choice']['lookup']['path'])()
                    columns[column_name]['path'] = path
                    # TODO: Try to optimize this step to decrease the number of file reading
                    columns[column_name]['choices'] = get_choices(column['choice'], path)
                if 'constraints' in column:
                    columns[column_name]['constraints'] = column['constraints']
                if 'regex' in column:
                    columns[column_name]['regex'] = column['regex']
                    if 'example' in column:
                        columns[column_name]['example'] = column['example']
                if 'nullable' in column:
                    columns[column_name]['nullable'] = column['nullable']

                columns[column_name]['description'] = column["description"]
                columns[column_name]['unit'] = column["unit"]
            store['columns'][db] = dict(columns)
        except Exception as e:
            print(f"Error reading column property from schemas: {e}")
            # Set data to None as well if column definitions cannot be read
            store['tables'][db] = None
            store['columns'][db] = None

    return store


def get_network(scenario: str, network_type):
    # TODO: Get a list of names and send all in the json
    try:
        locator = cea.inputlocator.InputLocator(scenario)
        building_connectivity = get_building_connectivity(locator)
        network_type = network_type.upper()
        connected_buildings = building_connectivity[building_connectivity['{}_connectivity'.format(
            network_type)] == 1]['name'].values.tolist()
        network_name = 'today'

        # Do not calculate if no connected buildings
        if len(connected_buildings) < 2:
            return None, [], None

        # Generate network files
        if newer_network_layout_exists(locator, network_type, network_name):
            config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
            config.scenario = scenario
            config.network_layout.network_type = network_type
            config.network_layout.connected_buildings = connected_buildings
            # Ignore demand and creating plants for layout in map
            config.network_layout.consider_only_buildings_with_demand = False
            network_layout = NetworkLayout(network_layout=config.network_layout)
            layout_network(network_layout, locator, output_name_network=network_name)

        edges = locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes = locator.get_network_layout_nodes_shapefile(network_type, network_name)

        network_json, crs = df_to_json(edges)
        if network_json is None:
            return None, [], None

        nodes_json, _ = df_to_json(nodes)
        network_json['features'].extend(nodes_json['features'])
        network_json['properties'] = {'connected_buildings': connected_buildings}
        return network_json, connected_buildings, crs
    except IOError as e:
        print(e)
        return None, [], None
    except Exception:
        traceback.print_exc()
        return None, [], None


def df_to_json(file_location):
    from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

    try:
        file_location = secure_path(file_location)
        if not os.path.exists(file_location):
            raise FileNotFoundError(f"File not found: {file_location}")

        table_df = geopandas.GeoDataFrame.from_file(file_location)
        # Save coordinate system
        if table_df.empty:
            # Set crs to generic projection if empty
            crs = table_df.crs.to_proj4()
        else:
            lat, lon = get_lat_lon_projected_shapefile(table_df)
            crs = get_projected_coordinate_system(lat, lon)

        if "name" in table_df.columns:
            table_df['name'] = table_df['name'].astype('str')

        # make sure that the geojson is coded in latitude / longitude
        out = table_df.to_crs(get_geographic_coordinate_system())
        out = json.loads(out.to_json())
        return out, crs
    except (IOError, DriverError, FileNotFoundError) as e:
        print(e)
        return None, None
    except Exception:
        traceback.print_exc()
        return None, None


@router.get('/building-schedule/{building}')
async def get_building_schedule(project_info: CEAProjectInfo, building: str):
    locator = cea.inputlocator.InputLocator(project_info.scenario)
    try:
        schedule_data, schedule_complementary_data = read_cea_schedule(locator, use_type=None, building=building)
        df = pd.DataFrame(schedule_data).set_index(['hour'])
        out = {'SCHEDULES': {
            schedule_type: {day: df.loc[day][schedule_type].values.tolist() for day in df.index.levels[0]}
            for schedule_type in df.columns}}
        out.update(schedule_complementary_data)
        return out
    except IOError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get('/databases')
async def get_input_database_data(project_info: CEAProjectInfo):
    locator = cea.inputlocator.InputLocator(project_info.scenario)
    try:
        cea_db = await run_in_threadpool(lambda: CEADatabase.from_locator(locator))
    except CEADatabaseException as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    if cea_db.is_empty():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Database not found',
        )
    return cea_db.to_dict()


@router.put('/databases', dependencies=[CEASeverDemoAuthCheck])
async def put_input_database_data(project_info: CEAProjectInfo, payload: Dict[str, Any]):
    locator = cea.inputlocator.InputLocator(project_info.scenario)
    try:
        def fn():
            db = CEADatabase.from_dict(payload)
            db.save(locator)
            return {'message': 'Database updated'}
        return await run_in_threadpool(fn)
    except CEADatabaseException as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post('/databases/upload', dependencies=[CEASeverDemoAuthCheck])
async def upload_input_database(project_info: CEAProjectInfo, file: UploadFile):
    locator = cea.inputlocator.InputLocator(project_info.scenario)

    # Create a lock file path specific to this scenario
    lock_file_path = os.path.join(tempfile.gettempdir(), f'cea_db_upload_{hash(project_info.scenario)}.lock')

    def do_upload():
        """Perform the upload operation with file-based locking"""
        with FileLock(lock_file_path):
            contents_sync = file.file.read()
            with zipfile.ZipFile(io.BytesIO(contents_sync)) as z:
                # Only process CSV files
                csv_files = [file_info for file_info in z.infolist()
                             if not file_info.filename.startswith('__MACOSX/')
                             and file_info.filename.endswith('.csv')
                             and not file_info.is_dir()]
                if not csv_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Invalid ZIP file: No CSV files found.',
                    )

                # Extract all files to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_scenario_path = os.path.join(temp_dir, 'temp_scenario')
                    locator_temp = cea.inputlocator.InputLocator(temp_scenario_path)
                    temp_db_folder = locator_temp.get_db4_folder()
                    db_directory_name = os.path.basename(temp_db_folder)

                    for file_info in csv_files:
                        # Adjust the filename to remove any leading directory structure if user zipped the db4 folder
                        adjusted_filename = file_info.filename
                        if adjusted_filename.startswith(db_directory_name + '/'):
                            adjusted_filename = os.path.relpath(adjusted_filename, db_directory_name)

                        # Normalize and validate the path to prevent directory traversal attacks
                        member_path = os.path.normpath(adjusted_filename)

                        # Construct the full target path
                        target_path = os.path.join(temp_db_folder, member_path)

                        # Verify the resolved path is within the target directory
                        target_path_resolved = os.path.realpath(target_path)
                        db_folder_resolved = os.path.realpath(temp_db_folder)

                        if os.path.isabs(member_path) or '..' in member_path.split(os.sep) or not target_path_resolved.startswith(db_folder_resolved + os.sep):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'Invalid ZIP file: {adjusted_filename}',
                            )

                        # Manually extract the file using copyfileobj for safety
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with z.open(file_info) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)

                    # Validate the extracted databases
                    try:
                        verify_database(temp_scenario_path)
                    except CEADatabaseException as e:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'Invalid database files: {str(e.message)}',
                        )

                    # Atomically replace the database folder to prevent data loss
                    db_folder = locator.get_db4_folder()
                    backup_folder = None

                    try:
                        # If the current database exists, create a backup
                        if os.path.exists(db_folder):
                            import time
                            backup_folder = f"{db_folder}.bak.{int(time.time())}"
                            os.rename(db_folder, backup_folder)

                        # Move the new database into place
                        shutil.move(locator_temp.get_db4_folder(), db_folder)

                    except Exception as e:
                        # If move failed and we have a backup, restore it
                        if backup_folder and os.path.exists(backup_folder):
                            # Remove partial new database if it exists
                            if os.path.exists(db_folder):
                                shutil.rmtree(db_folder)
                            # Restore the backup
                            os.rename(backup_folder, db_folder)

                        # Re-raise the exception
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Failed to replace database folder: {str(e)}',
                        )

                    # Clean up backup outside critical section
                    # If backup cleanup fails, log but don't fail the request
                    if backup_folder and os.path.exists(backup_folder):
                        try:
                            shutil.rmtree(backup_folder)
                        except Exception as e:
                            # Log the error but don't fail the upload
                            print(f"Warning: Failed to remove backup folder {backup_folder}: {str(e)}")

        return {'message': 'Database uploaded successfully'}

    return await run_in_threadpool(do_upload)

@router.get('/databases/download', dependencies=[CEASeverDemoAuthCheck])
async def download_input_database(project_info: CEAProjectInfo):
    locator = cea.inputlocator.InputLocator(project_info.scenario)
    filename = 'database.zip'

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_zip_path = os.path.join(temp_dir, filename)
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            db_folder = locator.get_db4_folder()
            if not os.path.exists(db_folder):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Database folder not found.',
                )
            for root, _, files in os.walk(db_folder):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, db_folder)
                        z.write(file_path, arcname)

        with open(temp_zip_path, 'rb') as f:
            zip_contents = f.read()

        return StreamingResponse(
            io.BytesIO(zip_contents),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(os.path.getsize(temp_zip_path)),  # Add Content-Length header
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
            }
        )


# Move to database route
@router.get('/databases/check')
async def check_input_database(project_info: CEAProjectInfo):
    """Check if the databases are valid"""
    scenario = project_info.scenario

    try:
        verify_database(scenario)
        return {'status': 'success', 'message': True}
    except CEADatabaseException as e:
        output = str(e.message).strip()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'status': "warning",
                'message': output
            },
        )



def database_dict_to_file(db_dict, csv_path):
    """
    Save a dictionary of DataFrames as a single CSV file, merging sheets horizontally on 'code' if available.

    Parameters:
    - db_dict (dict): Dictionary where keys are sheet names and values are DataFrames or lists of dicts.
    - csv_path (str): Path to the output CSV file.

    Returns:
    - None
    """
    if not db_dict:
        print("Warning: The database dictionary is empty. No file written.")
        return

    merged_df = None  # Initialize merged dataframe

    try:
        for sheet_name, data in db_dict.items():
            # Convert to DataFrame if it's a list of dictionaries
            df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data.copy()

            # Determine merge method
            if merged_df is None:
                merged_df = df
            else:
                merge_column = "code" if "code" in df.columns and "code" in merged_df.columns else None
                merged_df = pd.merge(merged_df, df, on=merge_column, how="outer") if merge_column else pd.concat(
                    [merged_df, df], axis=1)

        if merged_df is not None and not merged_df.empty:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            merged_df.to_csv(csv_path, index=False)
            print(f"Database successfully saved to {csv_path}")
        else:
            print("Warning: No valid data to write. No CSV file created.")

    except Exception as e:
        print(f"Error writing database file: {e}")


def schedule_dict_to_file(schedule_dict, schedule_path):
    schedule = dict()
    for key, data in schedule_dict.items():
        schedule[key] = pd.DataFrame(data)
    schedule_to_file(schedule, schedule_path)


def get_choices(choice_properties, path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Unable to generate choices. Could not find file: {path}")

    lookup = choice_properties['lookup']

    # TODO: Remove this once all databases are in .csv format
    if path.endswith('.xlsx'):
        warnings.warn(f'Database {path} is in .xlsx format. This will be deprecated in the future.')
        df = pd.read_excel(path, lookup['sheet'])
    else:
        df = pd.read_csv(path)

    if lookup['column'] not in df.columns:
        raise ValueError(f"column {lookup['column']} not found in {path}: check the file or schemas")

    choices = df[lookup['column']].tolist()
    out = []
    if 'none_value' in choice_properties:
        out.append({'value': choice_properties['none_value'], 'label': ''})
    for choice in choices:
        label = df.loc[df[lookup['column']] == choice, 'Description'].values[0] if 'Description' in df.columns else ''

        # Prevent labels to be encoded as NaN in JSON
        if str(label) == 'nan':
            label = 'none'
        out.append({'value': choice, 'label': label})
    return out


class FileLock:
    """Cross-process file-based lock using platform-specific file locking"""
    def __init__(self, lock_file_path):
        self.lock_file_path = lock_file_path
        self.lock_file = None

    def __enter__(self):
        self.lock_file = open(self.lock_file_path, 'w')
        if sys.platform == 'win32':
            import msvcrt
            # Lock the file on Windows
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            # Lock the file on Unix-like systems
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            if sys.platform == 'win32':
                import msvcrt
                # Unlock the file on Windows
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                # Unlock the file on Unix-like systems
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
        return False


def verify_database(scenario: str):
    """Check if the databases are valid and raise CEADatabaseException with missing files if not"""
    # Redirect stdout to variable to capture output
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            dict_missing_db = cea4_verify_db(scenario, verbose=True)
        output = buf.getvalue()
    finally:
        buf.close()

    if any(len(missing_files) > 0 for missing_files in dict_missing_db.values()):
        raise CEADatabaseException(output)