from flask import Blueprint, render_template, redirect, url_for, current_app, request, abort, make_response, jsonify

import cea.inputlocator
import geopandas
import yaml
import os
import numpy as np

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
    }

    for db in inputs.keys():
        inputs[db]['fieldtypes'] = {field['name']: types[field['type']] for field in inputs[db]['fields']}
        inputs[db]['fieldnames'] = [field['name'] for field in inputs[db]['fields']]
    return inputs
INPUTS = read_inputs_field_types()


@blueprint.route('/test')
def route_test():
    return render_template('test.html')


@blueprint.route('/json/<db>',  methods=['GET'])
def route_get_json(db):
    """Return the records of an input database in JSON format suitable for the bootstrap-table-editable"""
    if not db in INPUTS:
        abort(404, 'Input file not found: %s' % db)

    db_info = INPUTS[db]
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    location = getattr(locator, db_info['location'])()
    if db_info['type'] == 'shp':
        table_df = geopandas.GeoDataFrame.from_file(location).drop('geometry', 1)
    else:
        table_df = None
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
        rows = table_df[table_df[db_info['pk']] == pk].index
        assert len(rows) == 1, "PK for table %s is not unique!" % db
        row = rows[0]
        table_df.loc[row, column] = value
        table_df.to_file(location, driver='ESRI Shapefile', encoding='ISO-8859-1')
    else:
        table_df = None
    return jsonify(True)


@blueprint.route('/zone')
def zone():
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    table_df = geopandas.GeoDataFrame.from_file(locator.get_zone_geometry()).drop('geometry', 1)
    table_rows = [{column: getattr(row, column) for column in table_df.columns} for row in table_df.itertuples()]

    return render_template('table.html', pk='Name', table_name='zone', table_columns=table_df.columns,
                           table_rows=table_rows)