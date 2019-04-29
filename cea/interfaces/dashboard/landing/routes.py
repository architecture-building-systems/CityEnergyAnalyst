from flask import Blueprint, render_template, current_app, redirect, request, url_for

import geopandas
from shapely.geometry import shape
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system
import cea.inputlocator

blueprint = Blueprint(
    'landing_blueprint',
    __name__,
    url_prefix='/landing',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/welcome')
def index():
    return render_template('landing.html')


@blueprint.route('/create_project')
def route_project_creator():

    return render_template('project_creator.html')


@blueprint.route('/create_poly', methods=['POST'])
def route_poly_creator():
    data = request.get_json()
    print(data)
    poly = shape(data['geometry'])
    # TODO: check coordinate system
    poly = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(), geometry=[poly])
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    poly.to_file(locator.get_site_polygon())

    return 'Zone Shapefile created'


@blueprint.route('/create/<name>', methods=['POST'])
def route_create_project(name):

    return None
