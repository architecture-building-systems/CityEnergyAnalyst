import hashlib
import io
import json
import os
import shutil
import tempfile
import traceback
import warnings
from collections import defaultdict
from contextlib import redirect_stdout
from typing import Dict, Any, Literal
import zipfile

from fastapi.responses import StreamingResponse
import geopandas
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fiona.errors import DriverError
from pydantic import BaseModel, Field

import cea.config
import cea.databases
import cea.inputlocator
from cea.datamanagement import archetype_lock
from cea.datamanagement.archetypes_mapper import archetypes_mapper
from cea.datamanagement.district_pathways.pathway_timeline import PathwayChildScenario
from cea.datamanagement.utils import VOID_FLOORS_COLUMN
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
import cea.schemas
from cea.databases import CEADatabase, CEADatabaseException, databases_folder_path
from cea.datamanagement.database.assemblies import CROSS_CHECK_REL_TOLERANCE
from cea.datamanagement.format_helper.cea4_verify_db import cea4_verify_db

from cea.interfaces.dashboard.utils import (
    secure_path,
    secure_join_under_root,
    OutsideProjectRootError,
)
from cea.interfaces.dashboard.api.utils import CEAScenario
from cea.plots.supply_system.a_supply_system_map import get_building_connectivity, newer_network_layout_exists
from cea.plots.variable_naming import get_color_array
from cea.technologies.network_layout.main import auto_layout_network, NetworkLayout
from cea.utilities.file_lock import FileLock
from cea.utilities.schedule_reader import schedule_to_file, read_cea_schedule, save_cea_schedules
from cea.utilities.standardize_coordinates import (
    get_geographic_coordinate_system,
    validate_geometries_before_crs_transform,
)

router = APIRouter()

logger = getCEAServerLogger("cea-server-inputs")


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
    return {'buildingProperties': list(INPUT_KEYS), 'geoJSONs': GEOJSON_KEYS}


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
async def get_input_geojson(scenario: CEAScenario, kind: str):
    locator = cea.inputlocator.InputLocator(scenario)

    if kind not in GEOJSON_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Input file not found: {kind}',
        )
    # Building geojsons
    elif kind in INPUT_KEYS and kind in GEOJSON_KEYS:
        db_info = INPUTS[kind]
        location = getattr(locator, db_info['location'])()
        if db_info['file_type'] != 'shp':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Invalid database for geojson: {location}',
            )
        return df_to_json(location, root=scenario)[0]
    elif kind in NETWORK_KEYS:
        return get_network(scenario, kind)[0]
    elif kind == 'streets':
        return df_to_json(locator.get_street_network(), root=scenario)[0]


@router.get('/building-properties')
async def get_building_props(scenario: CEAScenario):
    return get_building_properties(scenario)


@router.get('/all-inputs')
async def get_all_inputs(scenario: CEAScenario):
    locator = cea.inputlocator.InputLocator(scenario)

    # FIXME: Find a better way, current used to test for Input Editor
    def fn():
        store = get_building_properties(scenario)
        store['geojsons'] = {}
        store['connected_buildings'] = {'dc': [], 'dh': []}
        store['crs'] = {}
        store['geojsons']['zone'], store['crs']['zone'] = df_to_json(locator.get_zone_geometry(), root=scenario)
        store['geojsons']['surroundings'], store['crs']['surroundings'] = df_to_json(
            locator.get_surroundings_geometry(), root=scenario)
        store['geojsons']['trees'], store['crs']['trees'] = df_to_json(locator.get_tree_geometry(), root=scenario)
        store['geojsons']['streets'], store['crs']['streets'] = df_to_json(locator.get_street_network(), root=scenario)
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


class ArchetypeLockForm(BaseModel):
    locked: bool


@router.get('/archetype-lock')
async def get_archetype_lock(scenario: CEAScenario):
    """The lock state, plus whether the derived tables have drifted from the last mapping."""
    locator = cea.inputlocator.InputLocator(scenario)

    def fn():
        state = archetype_lock.read_lock(locator)
        return {
            'locked': state.locked,
            'drifted': archetype_lock.is_drifted(locator),
            'mapped_at': state.mapped_at,
            'derived_tabs': list(archetype_lock.ARCHETYPE_DERIVED_TABS),
            'archetype_key_columns': list(archetype_lock.ARCHETYPE_KEY_COLUMNS),
        }

    return await run_in_threadpool(fn)


@router.put('/archetype-lock')
async def set_archetype_lock(scenario: CEAScenario, form: ArchetypeLockForm):
    """Lock or unlock the archetype-derived tables.

    Unlocking changes nothing on disk -- the user simply takes ownership of those tables.

    Locking regenerates all five of them, plus schedules, from each building's archetype, so
    any edits made while unlocked are lost. The client is expected to have confirmed that;
    this is the point of no return, not the modal.
    """
    locator = cea.inputlocator.InputLocator(scenario)

    def fn():
        if not form.locked:
            # Keep the fingerprint from the last mapping. It is the only record of what the
            # derived tables looked like when they matched their archetypes, so discarding it
            # here would make every later edit undetectable -- and detecting them is the
            # reason for unlocking in the first place.
            previous = archetype_lock.read_lock(locator)
            archetype_lock.write_lock(
                locator, locked=False,
                signature=previous.mapped_signature, mapped_at=previous.mapped_at)
            return {'locked': False,
                    'drifted': archetype_lock.is_drifted(locator),
                    'remapped': False}

        buildings = list(locator.get_zone_building_names())
        archetypes_mapper(
            locator=locator,
            update_architecture_dbf=True,
            update_air_conditioning_systems_dbf=True,
            update_indoor_comfort_dbf=True,
            update_internal_loads_dbf=True,
            update_supply_systems_dbf=True,
            update_schedule_operation_cea=True,
            list_buildings=buildings,
        )
        state = archetype_lock.write_lock(
            locator, locked=True, signature=archetype_lock.derived_signature(locator))
        return {'locked': True, 'drifted': False, 'remapped': True,
                'building_count': len(buildings), 'mapped_at': state.mapped_at}

    return await run_in_threadpool(fn)


def shapefile_payload_problems(db: str, table: Any, geojson: Any) -> list[str]:
    """Reasons a shapefile payload must not be written, as user-facing sentences.

    The save writes each table in turn, so anything wrong has to be found before the first
    write -- a failure discovered halfway leaves the scenario partly updated with the client
    still holding the version it thought it saved.

    Only what the user just did and can undo:

    - a footprint is malformed (self-intersecting, unclosed). Cannot reach here today, because
      `df_to_json` fails to read such a file at all and the caller skips the table; the check
      is what makes editing geometry safe to add.
    - two rows share a name. The write does `set_index('name')`, so one would silently win.

    A *missing* footprint is deliberately not a reason to refuse. The editor offers no way to
    give a building one, so rejecting the save would leave deleting the row as the only escape
    -- the very data loss this guards against. `restore_rows_without_geometry` carries those
    rows through the write instead, and the banner in the editor says they are there.

    :param db: input name, used in the messages (e.g. ``zone``).
    :param table: the table as sent by the client, ``{name: {column: value}}``.
    :param geojson: the matching geojson as sent by the client.
    :return: problems found, empty when the payload is safe to write.
    """
    features = (geojson or {}).get('features')
    if not features:
        # Geometry that failed to load is skipped by the caller, not rejected.
        return []

    try:
        gdf = geopandas.GeoDataFrame.from_features(
            features, crs=get_geographic_coordinate_system())
    except Exception as e:
        # Deliberately broad. This is arbitrary client input, and the ways it can fail to parse
        # are open-ended -- shapely alone raises `GeometryTypeError` for an unknown `type`.
        # Whatever it is, the answer is the same: tell the user we could not read it, rather
        # than let a traceback out as a 500.
        return [f"{db}: the geometry sent could not be read ({type(e).__name__}: {e})."]

    problems = []
    try:
        validate_geometries_before_crs_transform(
            gdf, shapefile_name=db, require_geometry=False)
    except ValueError as e:
        problems.append(str(e))

    if 'name' not in gdf.columns:
        return problems

    names = gdf['name'].astype(str)

    duplicated = sorted(set(names[names.duplicated()]))
    if duplicated:
        problems.append(
            f"{db}: more than one row is named {', '.join(duplicated)}. "
            f"Names must be unique - saving would keep only one row of each.")

    return problems


def restore_rows_without_geometry(table_df: geopandas.GeoDataFrame, table: Any) -> geopandas.GeoDataFrame:
    """Put back the rows the client could not send a footprint for.

    `df_to_json` drops null-geometry rows so the map can still draw, while
    `get_building_properties` keeps them in the table. The shapefile is rebuilt from the
    features alone, so without this those rows are deleted from the file on the next save --
    silently, and with their attributes.

    A shapefile stores a null geometry happily and reads it back as `None`, so the row survives
    a round trip intact and can be fixed or deleted later.

    :param table_df: the frame built from the payload's features.
    :param table: the table as sent by the client, ``{name: {column: value}}``.
    :return: `table_df` with any table-only rows appended, geometry unset.
    """
    if 'name' not in table_df.columns or not table:
        return table_df

    present = set(table_df['name'].astype(str))
    absent = [name for name in table if str(name) not in present]
    if not absent:
        return table_df

    logger.warning(
        f"{len(absent)} row(s) have no footprint and were written without one: "
        f"{', '.join(map(str, absent))}")

    restored = geopandas.GeoDataFrame(
        [{**table[name], 'name': name} for name in absent],
        geometry=[None] * len(absent),
        crs=table_df.crs,
    )
    # Reindexed to the written columns so a stray key in the table cannot add one, and a
    # column the row never had arrives as NA rather than shifting the frame.
    restored = restored.reindex(columns=table_df.columns)
    return pd.concat([table_df, restored], ignore_index=True)


@router.put('/all-inputs')
async def save_all_inputs(scenario: CEAScenario, form: InputForm):
    locator = cea.inputlocator.InputLocator(scenario)

    tables = form.tables
    geojsons = form.geojsons
    crs = form.crs
    schedules = form.schedules

    def fn():
        out = {'tables': {}, 'geojsons': {}, 'skipped_tables': []}

        # Archetype Lock. While locked, CEA owns the archetype-derived tables, so the payload's
        # copies of them are not written.
        #
        # This has to happen server-side, not only by grey-ing out the inputs: the editor holds
        # every table in memory and PUTs all of them on each save, so a client that is merely
        # *stale* -- one opened before the lock, or one whose copy predates an auto-remap --
        # would otherwise overwrite tables it never meant to touch.
        #
        # Skipped rather than rejected: the derived tables are in every payload, so rejecting
        # their presence would reject every save. They are reported back in `skipped_tables`
        # so the UI can say what was ignored, rather than dropping them silently.
        lock = archetype_lock.read_lock(locator)
        if lock.locked:
            for tab in archetype_lock.ARCHETYPE_DERIVED_TABS:
                if tables.get(tab):
                    out['skipped_tables'].append(tab)
                    tables[tab] = None

        # Which buildings changed archetype, decided here rather than trusted from the client.
        remap_buildings = []
        if lock.locked and tables.get('zone'):
            try:
                existing_zone = geopandas.read_file(locator.get_zone_geometry())
                existing_zone = pd.DataFrame(existing_zone.drop(columns='geometry')).set_index('name')
                remap_buildings = archetype_lock.buildings_needing_remap(
                    tables['zone'], existing_zone)
            except (IOError, DriverError, ValueError, KeyError, FileNotFoundError) as e:
                logger.warning(f"Could not compare archetype keys, skipping the re-map: {e}")

        # Nothing is written until every shapefile payload has been checked. The loop below
        # writes tables one at a time, so a problem found partway through would leave the
        # scenario half-updated -- and unlike a rejected save, there is no way back from that.
        geometry_problems = []
        for db, db_info in INPUTS.items():
            if db_info['file_type'] == 'shp' and tables.get(db):
                geometry_problems.extend(
                    shapefile_payload_problems(db, tables[db], geojsons.get(db)))
        if geometry_problems:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'message': 'Nothing was saved: the geometry has problems that would '
                               'corrupt the scenario.',
                    'problems': geometry_problems,
                },
            )

        # TODO: Maybe save the files to temp location in case something fails
        for db in INPUTS:
            db_info = INPUTS[db]
            location = getattr(locator, db_info['location'])()
            file_type = db_info['file_type']

            if tables.get(db) is None:  # ignore if table does not exist
                continue

            if len(tables[db]):
                if file_type == 'shp':
                    # The editor sends back what the GET gave it, and the GET builds `tables`
                    # and `geojsons` from two independent reads. When the geometry read failed
                    # the table can arrive populated with no geojson beside it; writing the
                    # shapefile needs the geometry, so skip rather than raise a TypeError from
                    # `None['features']`.
                    if not (geojsons.get(db) or {}).get('features'):
                        logger.warning(
                            f"Skipping {db}: its rows were sent without any geometry. The "
                            f"geometry file likely failed to load - check the log from when "
                            f"the scenario was opened.")
                        out['tables'][db] = tables[db]
                        continue

                    table_df = geopandas.GeoDataFrame.from_features(geojsons[db]['features'],
                                                                    crs=get_geographic_coordinate_system())
                    table_df = restore_rows_without_geometry(table_df, tables[db])
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

        if lock.locked:
            if remap_buildings:
                # Only the buildings whose archetype moved, or that are new. `archetypes_mapper`
                # merges a subset into the existing tables rather than replacing them, so the
                # rest of the district is left alone -- and a district-wide re-derive on every
                # `const_type` edit would be needlessly slow for a large scenario.
                archetypes_mapper(
                    locator=locator,
                    update_architecture_dbf=True,
                    update_air_conditioning_systems_dbf=True,
                    update_indoor_comfort_dbf=True,
                    update_internal_loads_dbf=True,
                    update_supply_systems_dbf=True,
                    update_schedule_operation_cea=True,
                    list_buildings=remap_buildings,
                )
                out['remapped_buildings'] = remap_buildings

                # Hand back what the mapper wrote. Without this the client keeps the values it
                # sent, and its next save would write them straight back over the re-map.
                for tab in archetype_lock.ARCHETYPE_DERIVED_TABS:
                    tab_location = getattr(locator, INPUTS[tab]['location'])()
                    if os.path.isfile(tab_location):
                        remapped = pd.read_csv(tab_location)
                        out['tables'][tab] = json.loads(
                            remapped.set_index('name').to_json(orient='index'))

            # Re-fingerprint either way: the save may have touched schedules.
            archetype_lock.write_lock(
                locator, locked=True, signature=archetype_lock.derived_signature(locator))

        return out

    result = await run_in_threadpool(fn)

    # If the save happened inside a pathway state (sub-scenario), mark
    # the state as custom so the pathway viewer shows it in purple and
    # bake/simulate can handle it appropriately.
    child_scenario = PathwayChildScenario.parse(scenario)
    if child_scenario:
        from cea.datamanagement.district_pathways.pathway_status import record_custom_state
        parent_locator = cea.inputlocator.InputLocator(child_scenario.parent)
        try:
            await run_in_threadpool(
                record_custom_state,
                parent_locator,
                pathway_name=child_scenario.pathway_name,
                year=child_scenario.year,
            )
        except OSError:
            pass

    return result


def _build_choices_cache(locator):
    """Pre-read all choice lookup files once, keyed by (locator_method, column)."""
    cache = {}
    for db_info in INPUTS.values():
        for column in db_info['columns'].values():
            if 'choice' not in column:
                continue
            lookup_path_method = column['choice']['lookup']['path']
            path = getattr(locator, lookup_path_method)()
            key = (lookup_path_method, column['choice']['lookup']['column'])
            if key not in cache:
                cache[key] = (path, get_choices(column['choice'], path))
    return cache


def get_building_properties(scenario: str):
    locator = cea.inputlocator.InputLocator(scenario)
    store = {'tables': {}, 'columns': {}}

    choices_cache = _build_choices_cache(locator)

    for db, db_info in INPUTS.items():
        locator_method = db_info['location']
        file_path = getattr(locator, locator_method)()
        file_type = db_info['file_type']
        db_columns = db_info['columns']

        # Get building property data from file. `available_columns` stays empty if the read
        # fails, which is fine: the table is None then, so there is nothing to render anyway.
        available_columns = set()
        try:
            if file_type == 'shp':
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

                table_df = geopandas.read_file(file_path)
                table_df = pd.DataFrame(table_df.drop(columns='geometry'))
                if 'geometry' in db_columns:
                    del db_columns['geometry']
                if 'reference' in db_columns and 'reference' not in table_df.columns:
                    table_df['reference'] = None
                available_columns = set(table_df.columns)
                store['tables'][db] = json.loads(table_df.set_index('name').to_json(orient='index'))
            else:
                table_df = pd.read_csv(file_path)
                if 'reference' in db_columns and 'reference' not in table_df.columns:
                    table_df['reference'] = None
                available_columns = set(table_df.columns)
                store['tables'][db] = table_df.set_index("name").to_dict(orient='index')
        except (IOError, DriverError, ValueError, FileNotFoundError) as e:
            logger.warning(f"Error reading {db} from {file_path}: {e}")
            store['tables'][db] = None

        # Get column definitions from schema
        #
        # `void_deck` is deprecated in favour of `height_vd`, so it is advertised only to
        # scenarios that already carry it. A scenario CEA generates today has `height_vd` and
        # never had `void_deck`; offering the legacy column there would show two columns for
        # one concept and invite new data into the form being retired. `height_vd` is always
        # advertised, so an older scenario can opt into metres.
        hide_deprecated_void_deck = VOID_FLOORS_COLUMN not in available_columns

        columns = defaultdict(dict)
        try:
            for column_name, column in db_columns.items():
                if hide_deprecated_void_deck and column_name == VOID_FLOORS_COLUMN:
                    continue
                columns[column_name]['type'] = column['type']
                if 'choice' in column:
                    lookup_path_method = column['choice']['lookup']['path']
                    lookup_col = column['choice']['lookup']['column']
                    path, choices = choices_cache[(lookup_path_method, lookup_col)]
                    columns[column_name]['path'] = path
                    columns[column_name]['choices'] = choices
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
            logger.warning(f"Error reading column property from schemas: {e}")
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
            auto_layout_network(network_layout, locator, output_name_network=network_name)

        edges = locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes = locator.get_network_layout_nodes_shapefile(network_type, network_name)

        network_json, crs = df_to_json(edges, root=scenario)
        if network_json is None:
            return None, [], None

        nodes_json, _ = df_to_json(nodes, root=scenario)
        network_json['features'].extend(nodes_json['features'])
        network_json['properties'] = {'connected_buildings': connected_buildings}
        return network_json, connected_buildings, crs
    except IOError as e:
        logger.warning(f"Error reading network layout: {e}")
        return None, [], None
    except Exception:
        traceback.print_exc()
        return None, [], None


def df_to_json(file_location, root=None):
    from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

    try:
        file_location = secure_path(file_location, root=root)
        if not os.path.exists(file_location):
            raise FileNotFoundError(f"File not found: {file_location}")

        table_df = geopandas.GeoDataFrame.from_file(file_location)

        # Drop rows with no geometry, for display only.
        #
        # `get_lat_lon_projected_shapefile` rejects the whole file if any row fails validation,
        # so a single row with a null footprint blanks the entire map -- every other building
        # included -- while the table beside it still lists them all. For the editor it is more
        # useful to draw what can be drawn and say what was left out; the row stays in the
        # table, which is where the user can fix or delete it.
        #
        # Simulation scripts call the validator directly and still refuse to run, which is
        # right: a missing footprint is a real error, not a display inconvenience.
        missing_geometry = table_df.geometry.isna()
        if missing_geometry.any():
            names = table_df.loc[missing_geometry].get('name')
            logger.warning(
                f"{int(missing_geometry.sum())} row(s) in {os.path.basename(file_location)} "
                f"have no geometry and are not drawn on the map"
                + (f": {', '.join(map(str, names))}" if names is not None else "")
                + ". They remain in the table - give them a footprint or delete them."
            )
            table_df = table_df.loc[~missing_geometry]

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
        # Through the logger, naming the file. Returning None here is invisible until a later
        # save trips over it -- `save_all_inputs` reads `geojsons[db]['features']` -- so the
        # 500 it eventually raises points at the save, not at whatever actually failed here.
        logger.warning(f"Could not read geometry for the Input Editor from {file_location}: {e}")
        return None, None
    except Exception:
        logger.exception(f"Could not read geometry for the Input Editor from {file_location}")
        return None, None


@router.get('/building-schedule/{building}')
async def get_building_schedule(scenario: CEAScenario, building: str):
    locator = cea.inputlocator.InputLocator(scenario)
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
async def get_input_database_data(scenario: CEAScenario):
    locator = cea.inputlocator.InputLocator(scenario)
    try:
        # Lenient: a database with a broken row must still open, or the user cannot reach the
        # editor to fix it. `/databases/check` reports what is wrong.
        cea_db = await run_in_threadpool(lambda: CEADatabase.from_locator(locator, strict=False))
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


@router.put('/databases')
async def put_input_database_data(
    scenario: CEAScenario,
    payload: Dict[str, Any],
    overwrite_derived: bool = False,
):
    """Save the database, deriving envelope U/GHG values from the material layers.

    A row whose stored U/GHG disagree with its layers is reported as a conflict and the whole
    save is refused (409) unless `overwrite_derived` is set. Refusing everything rather than
    the offending rows keeps the file consistent with what the user last saw: a partial save
    would leave the editor showing values that were not written.
    """
    locator = cea.inputlocator.InputLocator(scenario)
    try:
        def fn():
            db = CEADatabase.from_dict(payload)
            materials = getattr(db.components.materials, 'materials', None)
            conflicts = db.assemblies.envelope.apply_material_derivation(materials)
            if conflicts and not overwrite_derived:
                return conflicts
            db.save(locator)
            return None

        conflicts = await run_in_threadpool(fn)
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    'status': 'derived_conflict',
                    'message': (
                        f'{len(conflicts)} value(s) disagree with their material layers by more '
                        f'than {CROSS_CHECK_REL_TOLERANCE:.0%}. Material layers are the source of '
                        f'truth, so saving replaces them with values derived from the layers.'
                    ),
                    'conflicts': conflicts,
                },
            )
        return {'message': 'Database updated'}
    except CEADatabaseException as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


class SeedMaterialsDatabase(BaseModel):
    source: Literal['CH']


@router.post('/databases/components/materials')
async def seed_materials_database(scenario: CEAScenario, payload: SeedMaterialsDatabase):
    """Give a scenario a MATERIALS.csv it does not have yet."""
    # Only the CH database ships one, and every existing copy path is folder-granular
    # (`database_helper` copytree's the whole COMPONENTS tree, clobbering the siblings).
    locator = cea.inputlocator.InputLocator(scenario)
    destination = locator.get_database_components_materials()
    if os.path.exists(destination):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This scenario already has a materials database.",
        )

    # Mirror the destination's own sub-path inside the region database, so moving the file
    # is a locator change rather than a locator change plus this literal.
    source = os.path.join(
        databases_folder_path,
        payload.source,
        os.path.relpath(destination, locator.get_db4_folder()),
    )

    def do_copy():
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copyfile(source, destination)

    await run_in_threadpool(do_copy)

    return {'source': payload.source}


@router.post('/databases/upload')
async def upload_input_database(scenario: CEAScenario, file: UploadFile):
    locator = cea.inputlocator.InputLocator(scenario)

    # Create a lock file path specific to this scenario
    scenario_id = hashlib.sha256(scenario.encode('utf-8')).hexdigest()
    lock_file_path = os.path.join(tempfile.gettempdir(), f'cea_db_upload_{scenario_id}.lock')

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

                        # Construct the full target path and enforce root containment
                        if os.path.isabs(member_path) or '..' in member_path.split(os.sep):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'Invalid ZIP file: {adjusted_filename}',
                            )
                        try:
                            target_path = secure_join_under_root(temp_db_folder, member_path)
                        except OutsideProjectRootError:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'Invalid ZIP file: {adjusted_filename}',
                            )

                        # Manually extract the file using copyfileobj for safety
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with z.open(file_info) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)

                    # FIXME: Validation disabled for now, rethink validation strategy
                    # Validate the extracted databases
                    # try:
                    #     verify_database(temp_scenario_path)
                    # except CEADatabaseException as e:
                    #     raise HTTPException(
                    #         status_code=status.HTTP_400_BAD_REQUEST,
                    #         detail=f'Invalid database files: {str(e.message)}',
                    #     )

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

@router.get('/databases/download')
async def download_input_database(scenario: CEAScenario):
    locator = cea.inputlocator.InputLocator(scenario)
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
async def check_input_database(scenario: CEAScenario):
    """Check if the databases are valid"""
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