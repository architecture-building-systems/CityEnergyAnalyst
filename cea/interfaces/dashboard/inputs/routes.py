from flask import Blueprint, render_template, redirect, url_for, current_app, request, abort, make_response, jsonify

import cea.inputlocator
import geopandas
import numpy as np

blueprint = Blueprint(
    'inputs_blueprint',
    __name__,
    url_prefix='/inputs',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/test')
def route_test():
    return render_template('test.html')


@blueprint.route('/json/<db>',  methods=['GET'])
def route_get_json(db):
    """Return the records of an input database in JSON format suitable for the bootstrap-table-editable"""
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    table_df = geopandas.GeoDataFrame.from_file(locator.get_zone_geometry()).drop('geometry', 1)
    result = [{column: fix_types(getattr(row, column)) for column in table_df.columns} for row in table_df.itertuples()]
    return jsonify(result)


@blueprint.route('/json/<db>', methods=['POST'])
def route_post_json(db):
    """Save a row to the database"""
    print('got here!')
    return jsonify(True)



def fix_types(object):
    if type(object) == np.int64:
        return int(object)
    return object

@blueprint.route('/zone')
def zone():
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    table_df = geopandas.GeoDataFrame.from_file(locator.get_zone_geometry()).drop('geometry', 1)
    table_rows = [{column: getattr(row, column) for column in table_df.columns} for row in table_df.itertuples()]

    return render_template('table.html', table_name='zone', table_columns=table_df.columns,
                           table_rows=table_rows)