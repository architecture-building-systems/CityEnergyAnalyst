from flask import Blueprint, render_template, current_app, request, abort, jsonify

import cea.inputlocator
import cea.utilities.dbf
import geopandas
import yaml
import os
import json
import pandas


blueprint = Blueprint(
    'inputs_blueprint',
    __name__,
    url_prefix='/inputs',
    template_folder='templates',
    static_folder='static',
)

# mapping of input files to columns and data-types
def read_inputs_field_types():
    """Parse the inputs.yaml file and create the dictionary of column types"""
    inputs = yaml.load(open(os.path.join(os.path.dirname(__file__), 'inputs.yml')).read())
    types = {
        'int': int,
        'float': float,
        'str': str,
        'year': int,
    }

    for db in inputs.keys():
        inputs[db]['fieldtypes'] = {field['name']: types[field['type']] for field in inputs[db]['fields']}
        inputs[db]['fieldnames'] = [field['name'] for field in inputs[db]['fields']]
    return inputs
INPUTS = read_inputs_field_types()


@blueprint.route('/geojson/<db>')
def route_geojson(db):
    """Return a GeoJSON representation of the input file for use in Leaflet.js"""
    if not db in INPUTS:
        abort(404, 'Input file not found: %s' % db)
    db_info = INPUTS[db]
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    location = getattr(locator, db_info['location'])()
    if db_info['type'] != 'shp':
        abort(404, 'Invalid database for geojson: %s' % location)
    table_df = geopandas.GeoDataFrame.from_file(location)
    table_df = table_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    return jsonify(json.loads(table_df.to_json(show_bbox=True)))


@blueprint.route('/geojson/networks/<type>')
def route_geojson_networks(type):
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    # TODO: Get a list of names and send all in the json
    name = ''
    edges = locator.get_network_layout_edges_shapefile(type, name)
    nodes = locator.get_network_layout_nodes_shapefile(type, name)
    network_json = df_to_json(edges)
    network_json['features'].extend(df_to_json(nodes)['features'])
    return jsonify(network_json)


@blueprint.route('/geojson/others/streets')
def route_geojson_streets():
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    location = locator.get_street_network()
    return jsonify(df_to_json(location))


@blueprint.route('/building-properties', methods=['GET'])
def route_get_building_properties():
    import cea.plots
    import cea.glossary

    # FIXME: Find a better way to ensure order of tabs
    tabs = ['zone','age','occupancy','architecture','internal-loads','supply-systems','district','restrictions']

    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    store = {'tables': {}, 'geojsons': {}, 'columns': {}, 'column_types': {}, 'crs': {}, 'glossary': {}}
    glossary = cea.glossary.read_glossary_df()
    for db in INPUTS:
        db_info = INPUTS[db]
        location = getattr(locator, db_info['location'])()
        try:
            if db_info['type'] == 'shp':
                table_df = geopandas.GeoDataFrame.from_file(location)
                store['crs'][db] = table_df.crs
                from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
                store['geojsons'][db] = json.loads(table_df.to_crs(get_geographic_coordinate_system()).to_json(show_bbox=True))

                table_df = pandas.DataFrame(table_df.drop(columns='geometry'))
                if 'REFERENCE' in db_info['fieldnames'] and 'REFERENCE' not in table_df.columns:
                    table_df['REFERENCE'] = None
                store['tables'][db] = json.loads(table_df.set_index('Name').to_json(orient='index'))
            else:
                assert db_info['type'] == 'dbf', 'Unexpected database type: %s' % db_info['type']
                table_df = cea.utilities.dbf.dbf_to_dataframe(location)
                if 'REFERENCE' in db_info['fieldnames'] and 'REFERENCE' not in table_df.columns:
                    table_df['REFERENCE'] = None
                store['tables'][db] = json.loads(table_df.set_index('Name').to_json(orient='index'))

            store['columns'][db] = db_info['fieldnames']
            store['column_types'][db] = {k: v.__name__ for k, v in db_info['fieldtypes'].items()}

            filenames = glossary['FILE_NAME'].str.split(pat='/').str[-1]
            store['glossary'].update(json.loads(glossary[filenames == '%s.%s' % (db.replace('-','_'), db_info['type'])]
                                                [['VARIABLE', 'UNIT', 'DESCRIPTION']].set_index('VARIABLE').to_json(orient='index')))

        except IOError as e:
            print(e)
            store['tables'][db] = {}
    return render_template('table.html', store=store, tabs=tabs, last_updated=dir_last_updated())


@blueprint.route('/building-properties', methods=['POST'])
def route_save_building_properties():
    data = request.get_json()
    changes = data['changes']
    tables = data['tables']
    geojson = data['geojson']
    crs = data['crs']

    out = {'tables': {}, 'geojsons': {}}

    # TODO: Maybe save the files to temp location in case something fails
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    for db in INPUTS:
        db_info = INPUTS[db]
        location = getattr(locator, db_info['location'])()

        if len(tables[db]) != 0:
            if db_info['type'] == 'shp':
                from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
                table_df = geopandas.GeoDataFrame.from_features(geojson[db]['features'], crs=get_geographic_coordinate_system())
                out['geojsons'][db] = json.loads(table_df.to_json(show_bbox=True))
                table_df = table_df.to_crs(crs[db])
                table_df.to_file(location, driver='ESRI Shapefile', encoding='ISO-8859-1')

                table_df = pandas.DataFrame(table_df.drop(columns='geometry'))
                out['tables'][db] = json.loads(table_df.set_index('Name').to_json(orient='index'))
            elif db_info['type'] == 'dbf':
                table_df = pandas.read_json(json.dumps(tables[db]))
                cea.utilities.dbf.dataframe_to_dbf(table_df, location)

                out['tables'][db] = json.loads(table_df.set_index('Name').to_json(orient='index'))
        else:  # delete file if empty
            out['tables'][db] = {}
            if os.path.isfile(location):
                if db_info['type'] == 'shp':
                    import glob
                    for filepath in glob.glob(os.path.join(locator.get_building_geometry_folder(), '%s.*' % db)):
                        os.remove(filepath)
                elif db_info['type'] == 'dbf':
                    os.remove(location)
            if db_info['type'] == 'shp':
                out['geojsons'][db] = {}

    return jsonify(out)


def df_to_json(file_location):
    try:
        table_df = geopandas.GeoDataFrame.from_file(file_location)
        from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
        table_df = table_df.to_crs(get_geographic_coordinate_system())  # make sure that the geojson is coded in latitude / longitude
        return json.loads(table_df.to_json())
    except IOError as e:
        print(e)
        abort(404, 'Input file not found: %s' % file_location)


def dir_last_updated():
    return str(max(os.path.getmtime(os.path.join(root_path, f))
               for root_path, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), 'static'))
               for f in files))
