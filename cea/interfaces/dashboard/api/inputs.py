import json
import os
import shutil
import traceback
from collections import OrderedDict

import geopandas
import pandas
from flask import current_app, request
from flask_restplus import Namespace, Resource, abort

import cea.inputlocator
import cea.utilities.dbf
import cea.scripts
import cea.schemas
from cea.datamanagement.databases_verification import InputFileValidator
from cea.interfaces.dashboard.api.databases import read_all_databases, DATABASES_SCHEMA_KEYS
from cea.plots.supply_system.a_supply_system_map import get_building_connectivity, newer_network_layout_exists
from cea.plots.variable_naming import get_color_array
from cea.technologies.network_layout.main import layout_network, NetworkLayout
from cea.utilities.schedule_reader import schedule_to_file, get_all_schedule_names, schedule_to_dataframe, \
    read_cea_schedule, save_cea_schedule
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from fiona.errors import DriverError

api = Namespace('Inputs', description='Input data for CEA')

COLORS = {
    'surroundings': get_color_array('white'),
    'dh': get_color_array('red'),
    'dc': get_color_array('blue'),
    'disconnected': get_color_array('grey')
}

# List of input databases (db_name, locator/schema_key)
INPUT_DATABASES = [
    ('zone', 'get_zone_geometry'),
    ('typology', 'get_building_typology'),
    ('architecture', 'get_building_architecture'),
    ('internal-loads', 'get_building_internal'),
    ('indoor-comfort', 'get_building_comfort'),
    ('air-conditioning-systems', 'get_building_air_conditioning'),
    ('supply-systems', 'get_building_supply'),
    ('surroundings', 'get_surroundings_geometry')
]


def get_input_database_schemas():
    """Parse the schemas.yml file and create the dictionary of column types"""
    schemas = cea.schemas.schemas(plugins=[])
    input_database_schemas = OrderedDict()
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
GEOJSON_KEYS = ['zone', 'surroundings', 'streets', 'dc', 'dh']
NETWORK_KEYS = ['dc', 'dh']


@api.route('/')
class InputList(Resource):
    def get(self):
        return {'buildingProperties': INPUT_KEYS, 'geoJSONs': GEOJSON_KEYS}


@api.route('/building-properties/<string:db>')
class InputBuildingProperties(Resource):
    def get(self, db):
        if db not in INPUTS:
            abort(400, 'Input file not found: %s' % db, choices=INPUT_KEYS)
        db_info = INPUTS[db]
        columns = OrderedDict()
        for column_name, column in db_info['columns'].items():
            columns[column_name] = column['type']
        return columns


@api.route('/geojson/<string:kind>')
class InputGeojson(Resource):
    def get(self, kind):
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)

        if kind not in GEOJSON_KEYS:
            abort(400, 'Input file not found: %s' % kind, choices=GEOJSON_KEYS)
        # Building geojsons
        elif kind in INPUT_KEYS and kind in GEOJSON_KEYS:
            db_info = INPUTS[kind]
            config = current_app.cea_config
            locator = cea.inputlocator.InputLocator(config.scenario)
            location = getattr(locator, db_info['location'])()
            if db_info['file_type'] != 'shp':
                abort(500, 'Invalid database for geojson: %s' % location)
            return df_to_json(location, bbox=True)[0]
        elif kind in NETWORK_KEYS:
            return get_network(config, kind)[0]
        elif kind == 'streets':
            return df_to_json(locator.get_street_network())[0]


@api.route('/building-properties')
class BuildingProperties(Resource):
    def get(self):
        return get_building_properties()


@api.route('/all-inputs')
class AllInputs(Resource):
    def get(self):
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)

        # FIXME: Find a better way, current used to test for Input Editor
        store = get_building_properties()
        store['geojsons'] = {}
        store['connected_buildings'] = {}
        store['crs'] = {}
        store['geojsons']['zone'], store['crs']['zone'] = df_to_json(locator.get_zone_geometry(), bbox=True)
        store['geojsons']['surroundings'], store['crs']['surroundings'] = df_to_json(
            locator.get_surroundings_geometry(), bbox=True)
        store['geojsons']['streets'], store['crs']['streets'] = df_to_json(locator.get_street_network())
        store['geojsons']['dc'], store['connected_buildings']['dc'], store['crs']['dc'] = get_network(config, 'dc')
        store['geojsons']['dh'], store['connected_buildings']['dh'],  store['crs']['dh'] = get_network(config, 'dh')
        store['colors'] = COLORS
        store['schedules'] = {}

        return store

    def put(self):
        form = json.loads(request.data)
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)

        tables = form['tables']
        geojsons = form['geojsons']
        crs = form['crs']
        schedules = form['schedules']

        out = {'tables': {}, 'geojsons': {}}

        # TODO: Maybe save the files to temp location in case something fails
        for db in INPUTS:
            db_info = INPUTS[db]
            location = getattr(locator, db_info['location'])()
            file_type = db_info['file_type']

            if len(tables[db]) != 0:
                if file_type == 'shp':
                    from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
                    table_df = geopandas.GeoDataFrame.from_features(geojsons[db]['features'],
                                                                    crs=get_geographic_coordinate_system())
                    out['geojsons'][db] = json.loads(table_df.to_json(show_bbox=True))
                    table_df = table_df.to_crs(crs[db])
                    table_df.to_file(location, driver='ESRI Shapefile', encoding='ISO-8859-1')

                    table_df = pandas.DataFrame(table_df.drop(columns='geometry'))
                    out['tables'][db] = json.loads(table_df.set_index('Name').to_json(orient='index'))
                elif file_type == 'dbf':
                    table_df = pandas.read_json(json.dumps(tables[db]), orient='index')

                    # Make sure index name is 'Name;
                    table_df.index.name = 'Name'
                    table_df = table_df.reset_index()

                    cea.utilities.dbf.dataframe_to_dbf(table_df, location)
                    out['tables'][db] = json.loads(table_df.set_index('Name').to_json(orient='index'))

            else:  # delete file if empty
                out['tables'][db] = {}
                if os.path.isfile(location):
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
                schedule_complementary_data = {'MONTHLY_MULTIPLIER': schedule_dict['MONTHLY_MULTIPLIER'],
                                               'METADATA': schedule_dict['METADATA']}
                data = pandas.DataFrame()
                for day in ['WEEKDAY', 'SATURDAY', 'SUNDAY']:
                    df = pandas.DataFrame({'HOUR': range(1, 25), 'DAY': [day] * 24})
                    for schedule_type, schedule in schedule_data.items():
                        df[schedule_type] = schedule[day]
                    data = data.append(df, ignore_index=True)
                save_cea_schedule(data.to_dict('list'), schedule_complementary_data, schedule_path)
                print('Schedule file written to {}'.format(schedule_path))
        return out


def get_building_properties():
    import cea.glossary

    config = current_app.cea_config

    locator = cea.inputlocator.InputLocator(config.scenario)
    store = {'tables': {}, 'columns': {}}
    for db in INPUTS:
        db_info = INPUTS[db]
        locator_method = db_info['location']
        file_path = getattr(locator, locator_method)()
        file_type = db_info['file_type']
        db_columns = db_info['columns']
        try:
            if file_type == 'shp':
                table_df = geopandas.GeoDataFrame.from_file(file_path)
                table_df = pandas.DataFrame(
                    table_df.drop(columns='geometry'))
                if 'geometry' in db_columns:
                    del db_columns['geometry']
                if 'REFERENCE' in db_columns and 'REFERENCE' not in table_df.columns:
                    table_df['REFERENCE'] = None
                store['tables'][db] = json.loads(
                    table_df.set_index('Name').to_json(orient='index'))
            else:
                assert file_type == 'dbf', 'Unexpected database type: %s' % file_type
                table_df = cea.utilities.dbf.dbf_to_dataframe(file_path)
                if 'REFERENCE' in db_columns and 'REFERENCE' not in table_df.columns:
                    table_df['REFERENCE'] = None
                store['tables'][db] = json.loads(
                    table_df.set_index('Name').to_json(orient='index'))

            columns = {}
            for column_name, column in db_columns.items():
                columns[column_name] = {}
                if column_name == 'REFERENCE':
                    continue
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
                columns[column_name]['description'] = column["description"]
                columns[column_name]['unit'] = column["unit"]
            store['columns'][db] = columns

        except (IOError, DriverError, ValueError) as e:
            print(e)
            store['tables'][db] = {}
            store['columns'][db] = {}

    return store


def get_network(config, network_type):
    # TODO: Get a list of names and send all in the json
    try:
        locator = cea.inputlocator.InputLocator(config.scenario)
        building_connectivity = get_building_connectivity(locator)
        network_type = network_type.upper()
        connected_buildings = building_connectivity[building_connectivity['{}_connectivity'.format(
            network_type)] == 1]['Name'].values.tolist()
        network_name = 'today'

        # Do not calculate if no connected buildings
        if len(connected_buildings) < 2:
            return None, [], None

        # Generate network files
        if newer_network_layout_exists(locator, network_type, network_name):
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
    except Exception as e:
        traceback.print_exc()
        return None, [], None


def df_to_json(file_location, bbox=False):
    from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

    try:
        table_df = geopandas.GeoDataFrame.from_file(file_location)
        # Save coordinate system
        lat, lon = get_lat_lon_projected_shapefile(table_df)
        crs = get_projected_coordinate_system(lat, lon)
        # make sure that the geojson is coded in latitude / longitude
        out = table_df.to_crs(get_geographic_coordinate_system())
        out = json.loads(out.to_json(show_bbox=bbox))
        return out, crs
    except (IOError, DriverError) as e:
        print(e)
        return None, None
    except Exception as e:
        traceback.print_exc()
        return None, None


@api.route('/building-schedule/<string:building>')
class BuildingSchedule(Resource):
    def get(self, building):
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)
        try:
            schedule_path = locator.get_building_weekly_schedules(building)
            schedule_data, schedule_complementary_data = read_cea_schedule(schedule_path)
            df = pandas.DataFrame(schedule_data).set_index(['DAY', 'HOUR'])
            out = {'SCHEDULES': {
                schedule_type: {day: df.loc[day][schedule_type].values.tolist() for day in df.index.levels[0]}
                for schedule_type in df.columns}}
            out.update(schedule_complementary_data)
            return out
        except IOError as e:
            print(e)
            abort(500, 'File not found')


@api.route('/databases')
class InputDatabaseData(Resource):
    def get(self):
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)
        try:
            return read_all_databases(locator.get_databases_folder())
        except IOError as e:
            print(e)
            abort(500, e.message)

    def put(self):
        config = current_app.cea_config
        payload = json.loads(request.data)
        locator = cea.inputlocator.InputLocator(config.scenario)

        for db_type in payload:
            for db_name in payload[db_type]:
                if db_name == 'USE_TYPES':
                    database_dict_to_file(payload[db_type]['USE_TYPES']['USE_TYPE_PROPERTIES'],
                                          locator.get_database_use_types_properties())
                    for archetype, schedule_dict in payload[db_type]['USE_TYPES']['SCHEDULES'].items():
                        schedule_dict_to_file(
                            schedule_dict,
                            locator.get_database_standard_schedules_use(
                                archetype
                            )
                        )
                else:
                    locator_method = DATABASES_SCHEMA_KEYS[db_name][0]
                    db_path = locator.__getattribute__(locator_method)()
                    database_dict_to_file(payload[db_type][db_name], db_path)

        return payload


@api.route('/databases/copy')
class InputDatabaseCopy(Resource):
    def put(self):
        config = current_app.cea_config
        payload = api.payload
        locator = cea.inputlocator.InputLocator(config.scenario)

        if payload and 'path' in payload and 'name' in payload:
            copy_path = os.path.join(payload['path'], payload['name'])
            if os.path.exists(copy_path):
                abort(500, 'Copy path {} already exists. Choose a different path/name.'.format(copy_path))
            locator.ensure_parent_folder_exists(copy_path)
            shutil.copytree(locator.get_databases_folder(), copy_path)
            return {'message': 'Database copied to {}'.format(copy_path)}
        else:
            abort(500, "'path' and 'name' required")


@api.route('/databases/check')
class InputDatabaseCheck(Resource):
    def get(self):
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)
        try:
            locator.verify_database_template()
        except IOError as e:
            print(e)
            abort(500, e.message)
        return {'message': 'Database in path seems to be valid.'}


@api.route("/databases/validate")
class InputDatabaseValidate(Resource):
    def get(self):
        import cea.scripts
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)
        schemas = cea.schemas.schemas(plugins=[])
        validator = InputFileValidator(locator, plugins=config.plugins)
        out = OrderedDict()

        for db_name, schema_keys in DATABASES_SCHEMA_KEYS.items():
            for schema_key in schema_keys:
                schema = schemas[schema_key]
                if schema_key != 'get_database_standard_schedules_use':
                    db_path = locator.__getattribute__(schema_key)()
                    try:
                        df = pandas.read_excel(db_path, sheet_name=None)
                        errors = validator.validate(df, schema)
                        if errors:
                            out[db_name] = errors
                    except IOError as e:
                        out[db_name] = [{}, 'Could not find or read file: {}'.format(db_path)]
                else:
                    for use_type in get_all_schedule_names(locator.get_database_use_types_folder()):
                        db_path = locator.__getattribute__(schema_key)(use_type)
                        try:
                            df = schedule_to_dataframe(db_path)
                            errors = validator.validate(df, schema)
                            if errors:
                                out[use_type] = errors
                        except IOError as e:
                            out[use_type] = [{}, 'Could not find or read file: {}'.format(db_path)]
        return out


def database_dict_to_file(db_dict, db_path):
    with pandas.ExcelWriter(db_path) as writer:
        for sheet_name, data in db_dict.items():
            df = pandas.DataFrame(data).dropna(axis=0, how='all')
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print('Database file written to {}'.format(db_path))


def schedule_dict_to_file(schedule_dict, schedule_path):
    schedule = OrderedDict()
    for key, data in schedule_dict.items():
        schedule[key] = pandas.DataFrame(data)
    schedule_to_file(schedule, schedule_path)


def get_choices(choice_properties, path):
    lookup = choice_properties['lookup']
    df = pandas.read_excel(path, lookup['sheet'])
    choices = df[lookup['column']].tolist()
    out = []
    if 'none_value' in choice_properties:
        out.append({'value': choice_properties['none_value'], 'label': ''})
    for choice in choices:
        label = df.loc[df[lookup['column']] == choice, 'Description'].values[0] if 'Description' in df.columns else ''
        out.append({'value': choice, 'label': label})
    return out


if __name__ == "__main__":
    print(get_input_database_schemas())
