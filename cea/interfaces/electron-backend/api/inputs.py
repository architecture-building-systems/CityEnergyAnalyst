from flask_restplus import Namespace, Resource, fields, abort

import cea.config
import cea.inputlocator
import cea.utilities.dbf
import pandas
import geopandas
import os
import json
import yaml

from collections import OrderedDict

api = Namespace('Inputs', description='Input data for CEA')


def read_inputs_field_types():
    """Parse the inputs.yaml file and create the dictionary of column types"""
    inputs = yaml.load(
        open(os.path.join(os.path.dirname(__file__), '../resources/inputs.yml')).read())
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
        return {'db': INPUTS.keys(), 'others': ['streets', 'networks']}


@api.route('/<string:db>')
class Input(Resource):
    def get(self, db):
        if not db in INPUTS:
            abort(400, 'Input file not found: %s' % db, choices=INPUTS.keys())
        db_info = INPUTS[db]
        columns = OrderedDict()
        for column in db_info['fieldnames']:
            columns[column] = db_info['fieldtypes'][column].__name__

        return columns


@api.route('/<string:db>/geojson')
class InputGeojson(Resource):
    def get(self, db):
        config = cea.config.Configuration()
        if not db in INPUTS:
            abort(400, 'Input file not found: %s' % db)
        db_info = INPUTS[db]
        locator = cea.inputlocator.InputLocator(
            config.scenario)
        location = getattr(locator, db_info['location'])()
        if db_info['type'] != 'shp':
            abort(400, 'Invalid database for geojson: %s' % location)
        table_df = geopandas.GeoDataFrame.from_file(location)
        # make sure that the geojson is coded in latitude / longitude
        table_df = table_df.to_crs(epsg=4326)
        return json.loads(table_df.to_json(show_bbox=True))


@api.route('/others/networks/<string:kind>/geojson')
class InputNetwork(Resource):
    def get(self, kind):
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(
            config.scenario)
        # TODO: Get a list of names and send all in the json
        name = ''
        edges = locator.get_network_layout_edges_shapefile(kind, name)
        nodes = locator.get_network_layout_nodes_shapefile(kind, name)
        network_json = df_to_json(edges)
        network_json['features'].extend(df_to_json(nodes)['features'])
        return network_json


@api.route('/others/streets/geojson')
class InputStreets(Resource):
    def get(self):
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)
        location = locator.get_street_network()
        return df_to_json(location)


@api.route('/building-properties')
class BuildingProperties(Resource):
    def get(self):
        import cea.glossary
        config = cea.config.Configuration()

        # FIXME: Find a better way to ensure order of tabs
        tabs = ['zone', 'age', 'occupancy', 'architecture', 'internal-loads',
                'supply-systems', 'indoor-comfort', 'district', 'restrictions']

        locator = cea.inputlocator.InputLocator(config.scenario)
        store = {'tables': {}, 'geojsons': {}, 'columns': {}, 'crs': {}}
        glossary = cea.glossary.read_glossary_df()
        filenames = glossary['FILE_NAME'].str.split(pat='/').str[-1]
        for db in INPUTS:
            db_info = INPUTS[db]
            location = getattr(locator, db_info['location'])()
            try:
                if db_info['type'] == 'shp':
                    table_df = geopandas.GeoDataFrame.from_file(location)
                    # Store crs of original dataframe
                    store['crs'][db] = table_df.crs
                    from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
                    store['geojsons'][db] = json.loads(table_df.to_crs(
                        get_geographic_coordinate_system()).to_json(show_bbox=True))

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


def df_to_json(file_location):
    try:
        table_df = geopandas.GeoDataFrame.from_file(file_location)
        from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
        # make sure that the geojson is coded in latitude / longitude
        table_df = table_df.to_crs(get_geographic_coordinate_system())
        return json.loads(table_df.to_json())
    except IOError as e:
        print(e)
        abort(400, 'Input file not found: %s' % file_location)
    except RuntimeError as e:
        print(e)
        abort(400, e.message)
