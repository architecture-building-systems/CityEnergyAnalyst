from flask import Blueprint, render_template, current_app, request, abort, jsonify

import cea.inputlocator
import cea.utilities.dbf
import geopandas
import yaml
import os
import json


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


@blueprint.route('/json/<db>',  methods=['GET'])
def route_get_json(db):
    """Return the records of an input database in JSON format suitable for the bootstrap-table-editable"""
    if not db in INPUTS:
        abort(404, 'Input file not found: %s' % db)

    db_info = INPUTS[db]
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    location = getattr(locator, db_info['location'])()
    if db_info['type'] == 'shp':
        table_df = geopandas.GeoDataFrame.from_file(location)
    else:
        assert db_info['type'] == 'dbf', 'Unexpected database type: %s' % db_info['type']
        table_df = cea.utilities.dbf.dbf_to_dataframe(location)

    # Check for any missing columns from input and set it to null
    for column in db_info['fieldnames']:
        if column not in table_df.columns:
            table_df[column] = 'null'

    result = [{column: db_info['fieldtypes'][column](getattr(row, column))
               for column in db_info['fieldnames']} for row in table_df.itertuples()]
    return jsonify(result)


@blueprint.route('/json/<db>', methods=['POST'])
def route_post_json(db):
    """Save a row to the database"""
    if not db in INPUTS:
        abort(404, 'Input file not found: %s' % db)

    print('request variables: %s' % request.form)
    pk = request.form['pk']
    column = request.form['name']
    value = request.form['value']

    db_info = INPUTS[db]
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    location = getattr(locator, db_info['location'])()
    if db_info['type'] == 'shp':
        table_df = geopandas.GeoDataFrame.from_file(location)
    else:
        assert db_info['type'] == 'dbf', 'Unexpected database type: %s' % db_info['type']
        table_df = cea.utilities.dbf.dbf_to_dataframe(location)

    rows = table_df[table_df[db_info['pk']] == pk].index
    assert len(rows) == 1, "PK for table %s is not unique!" % db
    row = rows[0]
    table_df.loc[row, column] = value

    if db_info['type'] == 'shp':
        table_df.to_file(location, driver='ESRI Shapefile', encoding='ISO-8859-1')
    else:
        cea.utilities.dbf.dataframe_to_dbf(table_df, location)
    return jsonify(True)


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


@blueprint.route('/building-properties')
def route_building_properties():
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    tables = {}
    geojsons = {}
    for db in INPUTS:
        db_info = INPUTS[db]
        location = getattr(locator, db_info['location'])()
        try:
            if db_info['type'] == 'shp':
                table_df = geopandas.GeoDataFrame.from_file(location)
                from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
                geojsons[db] = json.loads(table_df.to_crs(get_geographic_coordinate_system()).to_json(show_bbox=True))

                import pandas
                table_df = pandas.DataFrame(table_df.drop(columns='geometry'))
                tables[db] = json.loads(table_df.set_index('Name').to_json(orient='index'))
            else:
                assert db_info['type'] == 'dbf', 'Unexpected database type: %s' % db_info['type']
                table_df = cea.utilities.dbf.dbf_to_dataframe(location)
                tables[db] = json.loads(table_df.set_index('Name').to_json(orient='index'))
        except IOError as e:
            print(e)
            tables['db'] = ''
    return render_template('table.html', tables=tables, geojsons=geojsons)


@blueprint.route('/table/<db>', methods=['GET'])
def route_table_get(db):
    if not db in INPUTS:
        abort(404, 'Input file not found: %s' % db)
    db_info = INPUTS[db]
    return render_template('table.html', pk='Name', table_name=db, table_columns=db_info['fieldnames'])


@blueprint.route('/table/<db>', methods=['POST'])
def route_table_post(db):
    if not db in INPUTS:
        abort(404, 'Input file not found: %s' % db)
    db_info = INPUTS[db]
    pk = db_info['pk']

    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    location = getattr(locator, db_info['location'])()
    if db_info['type'] == 'shp':
        table_df = geopandas.GeoDataFrame.from_file(location)
    else:
        assert db_info['type'] == 'dbf', 'Unexpected database type: %s' % db_info['type']
        table_df = cea.utilities.dbf.dbf_to_dataframe(location)

    # copy data from form POST data
    new_data = json.loads(request.form.get('cea-table-data'))
    column_types = table_df.dtypes
    for row in new_data:
        for column in row.keys():
            table_df.loc[table_df[pk] == row[pk], column] = row[column]
    print table_df
    # allow columns to maintain their original type
    for (types, column) in zip(column_types, table_df):
        table_df[column] = table_df[column].astype(types)

    # safe dataframe back to disk
    if db_info['type'] == 'shp':
        table_df.to_file(location, driver='ESRI Shapefile', encoding='ISO-8859-1')
    else:
        cea.utilities.dbf.dataframe_to_dbf(table_df, location)

    return render_template('table.html', pk='Name', table_name=db, table_columns=db_info['fieldnames'])

def df_to_json(file_location):
    try:
        table_df = geopandas.GeoDataFrame.from_file(file_location)
        from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
        table_df = table_df.to_crs(get_geographic_coordinate_system())  # make sure that the geojson is coded in latitude / longitude
        return json.loads(table_df.to_json())
    except IOError as e:
        print(e)
        abort(404, 'Input file not found: %s' % file_location)
