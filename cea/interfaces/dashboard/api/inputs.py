from flask_restplus import Namespace, Resource, fields, abort

import cea.config
import cea.inputlocator
import cea.utilities.dbf
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from cea.plots.variable_naming import get_color_array
from cea.plots.supply_system.supply_system_map import get_building_connectivity
from cea.technologies.network_layout.main import network_layout

import pandas
import geopandas
import os
import json
import yaml

from collections import OrderedDict

api = Namespace('Inputs', description='Input data for CEA')

COLORS = {
    'district': get_color_array('white'),
    'dh': get_color_array('red'),
    'dc': get_color_array('blue'),
    'disconnected': get_color_array('grey')
}

def read_inputs_field_types():
    """Parse the inputs.yaml file and create the dictionary of column types"""
    inputs = yaml.load(
        open(os.path.join(os.path.dirname(__file__), '../inputs/inputs.yml')).read())
    types = {
        'int': int,
        'float': float,
        'str': str,
        'year': int,
    }

    for db in inputs.keys():
        inputs[db]['fieldtypes'] = {
            field['name']: types[field['type']] for field in inputs[db]['fields']}
        inputs[db]['fieldnames'] = [field['name']
                                    for field in inputs[db]['fields']]
    return inputs


INPUTS = read_inputs_field_types()
INPUT_KEYS = INPUTS.keys()
GEOJSON_KEYS = ['zone', 'district', 'streets', 'dc', 'dh']

# INPUT_MODEL = api.model('Input', {
#     'fields': fields.List(fields.String, description='Column names')
# })

# GEOJSON_MODEL = api.model('GeoJSON',{
#     'test': fields.String()
# })

# BUILDING_PROPS_MODEL = api.model('Building Properties', {
#     'geojsons': fields.List(fields.Nested(GEOJSON_MODEL)),
#     'tables': fields.List(fields.String)
# })


@api.route('/')
class InputList(Resource):
    def get(self):
        return {'buildingProperties': INPUT_KEYS, 'others': ['streets', 'dc', 'dh']}


@api.route('/building-properties/<string:db>')
class Input(Resource):
    def get(self, db):
        if db not in INPUTS:
            abort(400, 'Input file not found: %s' % db, choices=INPUT_KEYS)
        db_info = INPUTS[db]
        columns = OrderedDict()
        for column in db_info['fieldnames']:
            columns[column] = db_info['fieldtypes'][column].__name__
        return columns


@api.route('/building-properties/<string:db>/geojson')
class InputDatabases(Resource):
    def get(self, db):
        if not (db in INPUT_KEYS and db in GEOJSON_KEYS):
            abort(400, 'Input file not found: %s' % db, choices=list(set(INPUT_KEYS) & set(GEOJSON_KEYS)))
        db_info = INPUTS[db]
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)
        location = getattr(locator, db_info['location'])()
        if db_info['type'] != 'shp':
            abort(400, 'Invalid database for geojson: %s' % location)
        return df_to_json(location, bbox=True)[0]


@api.route('/others/<string:kind>/geojson')
class InputOthers(Resource):
    def get(self, kind):
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(
            config.scenario)
        if kind == 'streets':
            return df_to_json(locator.get_street_network())[0]
        if kind in ['dc', 'dh']:
            return get_network(config, kind)[0]
        abort(400, 'Input file not found: %s' % kind, choices=['streets', 'dh', 'dc'])


@api.route('/building-properties')
class BuildingProperties(Resource):
    def get(self):
        return get_building_properties()


@api.route('/all-inputs')
class AllInputs(Resource):
    def get(self):
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)

        # FIXME: Find a better way, current used to test for Input Editor
        store = get_building_properties()
        store['geojsons'] = {}
        store['crs'] = {}
        store['geojsons']['zone'], store['crs']['zone'] = df_to_json(locator.get_zone_geometry(), bbox=True, trigger_abort=False)
        store['geojsons']['district'], store['crs']['district'] = df_to_json(locator.get_district_geometry(), bbox=True, trigger_abort=False)
        store['geojsons']['streets'], store['crs']['streets'] = df_to_json(locator.get_street_network(), trigger_abort=False)
        store['geojsons']['dc'], store['crs']['dc'] = get_network(config, 'dc', trigger_abort=False)
        store['geojsons']['dh'], store['crs']['dh'] = get_network(config, 'dh', trigger_abort=False)
        store['colors'] = COLORS

        return store


def get_building_properties():
    import cea.glossary
    # FIXME: Find a better way to ensure order of tabs
    tabs = ['zone', 'age', 'occupancy', 'architecture', 'internal-loads',
            'supply-systems', 'indoor-comfort', 'district', 'restrictions']

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    store = {'tables': {}, 'columns': {}, 'order': tabs}
    glossary = cea.glossary.read_glossary_df()
    filenames = glossary['FILE_NAME'].str.split(pat='/').str[-1]
    for db in INPUTS:
        db_info = INPUTS[db]
        location = getattr(locator, db_info['location'])()
        try:
            if db_info['type'] == 'shp':
                table_df = geopandas.GeoDataFrame.from_file(location)
                table_df = pandas.DataFrame(
                    table_df.drop(columns='geometry'))
                if 'REFERENCE' in db_info['fieldnames'] and 'REFERENCE' not in table_df.columns:
                    table_df['REFERENCE'] = None
                store['tables'][db] = json.loads(
                    table_df.set_index('Name').to_json(orient='index'))
            else:
                assert db_info['type'] == 'dbf', 'Unexpected database type: %s' % db_info['type']
                table_df = cea.utilities.dbf.dbf_to_dataframe(location)
                if 'REFERENCE' in db_info['fieldnames'] and 'REFERENCE' not in table_df.columns:
                    table_df['REFERENCE'] = None
                store['tables'][db] = json.loads(
                    table_df.set_index('Name').to_json(orient='index'))

            columns = OrderedDict()
            db_glossary = json.loads(glossary[filenames == '%s.%s' % (db.replace('-', '_'), db_info['type'])]
            [['VARIABLE', 'UNIT', 'DESCRIPTION']].set_index('VARIABLE').to_json(orient='index'))

            for column in db_info['fieldnames']:
                if column == 'REFERENCE':
                    continue
                columns[column] = {}
                columns[column]['type'] = db_info['fieldtypes'][column].__name__
                columns[column]['description'] = db_glossary[column]['DESCRIPTION']
                columns[column]['unit'] = db_glossary[column]['UNIT']
            store['columns'][db] = columns

        except IOError as e:
            print(e)
            store['tables'][db] = {}

    return store


def get_network(config, network_type, trigger_abort=True):
    # TODO: Get a list of names and send all in the json
    locator = cea.inputlocator.InputLocator(config.scenario)
    building_connectivity = get_building_connectivity(locator)
    network_type = network_type.upper()
    connected_buildings = building_connectivity[building_connectivity['{}_connectivity'.format(network_type)] == 1]['Name'].values.tolist()
    network_name = 'base'

    # Do not calculate if no connected buildings
    if len(connected_buildings) == 0:
        return None, [], None

    edges = locator.get_network_layout_edges_shapefile(network_type, network_name)
    nodes = locator.get_network_layout_nodes_shapefile(network_type, network_name)
    supply_system = locator.get_building_supply()

    no_network_file = not os.path.isfile(edges) or not os.path.isfile(nodes)
    supply_system_modified = os.path.getmtime(supply_system)

    # Generate network files
    if no_network_file or supply_system_modified > os.path.getmtime(edges) or supply_system_modified > os.path.getmtime(nodes):
        config.network_layout.network_type = network_type
        config.network_layout.connected_buildings = connected_buildings
        network_layout(config, locator, output_name_network=network_name)

    network_json, crs = df_to_json(edges, trigger_abort=trigger_abort)
    nodes_json, _ = df_to_json(nodes, trigger_abort=trigger_abort)
    network_json['features'].extend(nodes_json['features'])
    network_json['properties'] = {'connected_buildings': connected_buildings}
    return network_json, crs


def df_to_json(file_location, bbox=False, trigger_abort=True):
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
    except IOError as e:
        print(e)
        if trigger_abort:
            abort(400, 'Input file not found: %s' % file_location)
    except RuntimeError as e:
        print(e)
        if trigger_abort:
            abort(400, e.message)
