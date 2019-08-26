from flask import Blueprint, render_template, current_app, redirect, request, url_for, jsonify, abort

import os
import shutil
import glob
import json
import geopandas
from shapely.geometry import shape
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from staticmap import StaticMap, Polygon

import cea.inputlocator
import cea.api
import cea.scripts

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


@blueprint.route('/create-project')
def route_create_project():
    cea_config = current_app.cea_config
    project = os.path.dirname(cea_config.project)
    # TODO: Check if directory already exists
    return render_template('new_project.html', project=project)


@blueprint.route('/create-scenario')
def route_create_scenario():
    scenarios = get_scenarios(current_app.cea_config.project)
    return render_template('new_scenario.html', scenarios=scenarios)


@blueprint.route('/project-overview')
def route_project_overview():
    cea_config = current_app.cea_config
    project_path = cea_config.project
    project_name = os.path.basename(project_path)

    # Get the list of scenarios
    scenarios = get_scenarios(project_path)

    # Get scenario descriptions
    descriptions = {}
    for scenario in scenarios:
        descriptions[scenario] = {}
        locator = cea.inputlocator.InputLocator(os.path.join(project_path, scenario))
        zone = locator.get_zone_geometry()
        if os.path.isfile(zone):
            try:
                zone_df = geopandas.read_file(zone).to_crs(get_geographic_coordinate_system())
                descriptions[scenario]['Coordinates'] = (float("%.5f" % ((zone_df.total_bounds[1] + zone_df.total_bounds[3])/2)),
                                                     float("%.5f" % ((zone_df.total_bounds[0] + zone_df.total_bounds[2])/2)))
            except RuntimeError as e:
                descriptions[scenario]['Warning'] = 'Could not read the Zone file. ' \
                                                    'Check if your geometries have a coordinate system.'

        else:
            descriptions[scenario]['Warning'] = 'Zone file does not exist.'

    # Clean .cache images
    for filepath in glob.glob(os.path.join(os.path.join(project_path, '.cache', '*.png'))):
        print(filepath)
        image = os.path.basename(filepath).split('.')[0]
        if image not in scenarios:
            os.remove(filepath)


    return render_template('project_overview.html', project_name=project_name, scenarios=scenarios, descriptions=descriptions)


@blueprint.route('/project-overview/<scenario>/<func>')
def route_project_overview_function(scenario, func):
    if func == 'delete':
        return render_template('modal/delete_scenario.html', scenario=scenario)


@blueprint.route('/project-overview/delete/<scenario>', methods=['POST'])
def route_delete_scenario(scenario):
    cea_config = current_app.cea_config
    scenario_path = os.path.join(cea_config.project, scenario)
    try:
        shutil.rmtree(scenario_path)
    except WindowsError:
        from flask import abort, Response
        abort(Response('Make sure that the scenario you are trying to delete is not open in any application.<br>'
                       'Try and refresh the page again.'))
    cea_config.scenario_name = ''
    return redirect(url_for('landing_blueprint.route_project_overview'))


@blueprint.route('/create-project/save', methods=['POST'])
def route_create_project_save():
    # Make sure that the project folder exists
    project_path = os.path.join(request.form.get('project-path'), request.form.get('project-name'))
    try:
        os.makedirs(project_path)
    except OSError as e:
        print(e.message)

    cea_config = current_app.cea_config
    cea_config.project = project_path
    cea_config.scenario_name = ''
    cea_config.save()

    return redirect(url_for('landing_blueprint.route_project_overview'))


@blueprint.route('/create-scenario/save', methods=['POST'])
def route_create_scenario_save():

    cea_config = current_app.cea_config

    # Make sure that the scenario folder exists
    try:
        os.makedirs(os.path.join(cea_config.project, request.form.get('scenario-name')))
    except OSError as e:
        print(e.message)

    cea_config.scenario_name = request.form.get('scenario-name')
    cea_config.save()

    scenario_path = cea_config.scenario

    locator = cea.inputlocator.InputLocator(scenario_path)

    if request.form.get('input-files') == 'import':
        zone = request.form.get('zone')
        district = request.form.get('district')
        terrain = request.form.get('terrain')
        streets = request.form.get('streets')
        age = request.form.get('age')
        occupancy = request.form.get('occupancy')

        # since we're creating a new scenario, go ahead and and make sure we have
        # the folders _before_ we try copying to them
        locator.ensure_parent_folder_exists(locator.get_zone_geometry())
        locator.ensure_parent_folder_exists(locator.get_terrain())
        locator.ensure_parent_folder_exists(locator.get_building_age())
        locator.ensure_parent_folder_exists(locator.get_building_occupancy())
        locator.ensure_parent_folder_exists(locator.get_street_network())

        if zone:
            for filename in glob_shapefile_auxilaries(zone):
                shutil.copy(filename, locator.get_building_geometry_folder())
        if district:
            for filename in glob_shapefile_auxilaries(district):
                shutil.copy(filename, locator.get_building_geometry_folder())
        if terrain:
            shutil.copyfile(terrain, locator.get_terrain())
        if streets:
            shutil.copyfile(streets, locator.get_street_network())

        from cea.datamanagement.zone_helper import calculate_age_file, calculate_occupancy_file
        if age:
            shutil.copyfile(age, locator.get_building_age())
        elif zone:
            zone_df = geopandas.read_file(zone)
            calculate_age_file(zone_df, None, locator.get_building_age())

        if occupancy:
            shutil.copyfile(occupancy, locator.get_building_occupancy())
        elif zone:
            zone_df = geopandas.read_file(zone)
            if 'category' not in zone_df.columns:
                # set 'MULTI_RES' as default
                calculate_occupancy_file(zone_df, 'MULTI_RES', locator.get_building_occupancy())
            else:
                calculate_occupancy_file(zone_df, 'Get it from open street maps', locator.get_building_occupancy())

    elif request.form.get('input-files') == 'copy':
        source_scenario = os.path.join(cea_config.project, request.form.get('scenario'))
        shutil.copytree(cea.inputlocator.InputLocator(source_scenario).get_input_folder(),
                        locator.get_input_folder())

    elif request.form.get('input-files') == 'generate':
        tools = request.form.getlist('tools')
        if tools is not None:
            for tool in tools:
                if tool == 'zone-helper':
                    # FIXME: Setup a proper endpoint for site creation
                    data = json.loads(request.form.get('poly-string'))
                    site = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                                  geometry=[shape(data['geometry'])])
                    site_path = locator.get_site_polygon()
                    locator.ensure_parent_folder_exists(site_path)
                    site.to_file(site_path)
                    print('site.shp file created at %s' % site_path)
                    cea.api.zone_helper(cea_config)
                elif tool == 'district-helper':
                    cea.api.district_helper(cea_config)
                elif tool == 'streets-helper':
                    cea.api.streets_helper(cea_config)
                elif tool == 'terrain-helper':
                    cea.api.terrain_helper(cea_config)
                elif tool == 'weather-helper':
                    cea.api.weather_helper(cea_config)

    return redirect(url_for('inputs_blueprint.route_get_building_properties'))


def glob_shapefile_auxilaries(shapefile_path):
    """Returns a list of files in the same folder as ``shapefile_path``, but allows for varying extensions.
    This gets the .dbf, .shx, .prj, .shp and .cpg files"""
    return glob.glob('{basepath}.*'.format(basepath=os.path.splitext(shapefile_path)[0]))


@blueprint.route('/open-project')
def route_open_project():
    cea_config = current_app.cea_config
    project = cea_config.project
    # Check if the path exists
    if not os.path.exists(project):
        project = ''
    return render_template('open_project.html', project=project)


@blueprint.route('/open-project/save', methods=['POST'])
def route_open_project_save():
    cea_config = current_app.cea_config
    project_path = request.form.get('projectPath')

    cea_config.project = project_path
    cea_config.scenario_name = ''
    cea_config.save()
    return redirect(url_for('landing_blueprint.route_project_overview'))


@blueprint.route('/open-project/<scenario>')
def route_open_project_scenario(scenario):
    """Open project based on the scenario"""
    cea_config = current_app.cea_config
    # Make sure the scenario exists
    assert scenario in get_scenarios(cea_config.project)
    cea_config.scenario_name = scenario
    cea_config.save()
    return redirect(url_for('inputs_blueprint.route_get_building_properties'))


@blueprint.route('/get-image/<scenario>')
def route_get_images(scenario):
    cea_config = current_app.cea_config
    project_path = cea_config.project
    locator = cea.inputlocator.InputLocator(os.path.join(project_path, scenario))
    zone_path = locator.get_zone_geometry()
    if not os.path.isfile(zone_path):
        abort(404, 'Zone file not found')
    cache_path = os.path.join(project_path, '.cache')
    image_path = os.path.join(cache_path, scenario+'.png')

    zone_modified = os.path.getmtime(zone_path)
    if not os.path.isfile(image_path):
        image_modified = 0
    else:
        image_modified = os.path.getmtime(image_path)

    if zone_modified > image_modified:
        # Make sure .cache folder exists
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        zone_df = geopandas.read_file(zone_path)
        zone_df = zone_df.to_crs(get_geographic_coordinate_system())
        polygons = zone_df['geometry']

        polygons = [list(polygons.geometry.exterior[row_id].coords) for row_id in range(polygons.shape[0])]

        m = StaticMap(256, 160)
        for polygon in polygons:
            out = Polygon(polygon, 'blue', 'black', False)
            m.add_polygon(out)

        image = m.render()
        image.save(image_path)

    import base64
    with open(image_path, 'rb') as imgFile:
        image = base64.b64encode(imgFile.read())
    return image


@blueprint.route('/create-scenario/<script_name>/settings')
def route_script_settings(script_name):
    config = current_app.cea_config
    locator = cea.inputlocator.InputLocator(config.scenario)
    weather_dict = {wn: locator.get_weather(wn) for wn in locator.get_weather_names()}
    script = cea.scripts.by_name(script_name)
    return render_template('script_settings.html', script=script, weather_dict=weather_dict,
                           parameters=parameters_for_script(script_name, config))


def parameters_for_script(script_name, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    parameters = [p for _, p in config.matching_parameters(cea.scripts.by_name(script_name).parameters)]
    return parameters


@blueprint.route('/restore-defaults/<script_name>', methods=['POST'])
def route_restore_defaults(script_name):
    """Restore the default configuration values for the CEA"""
    config = current_app.cea_config

    for parameter in parameters_for_script(script_name, config):
        if parameter.name != 'scenario':
            parameter.set(parameter.default)
    config.save()
    return jsonify(True)


# FIXME: this should be refactored, as it is originally from tools/routes.py
@blueprint.route('/open-folder-dialog/<fqname>')
def route_open_folder_dialog(fqname):
    """Return html of folder structure for that parameter"""

    # these arguments are only set when called with the `navigate_to` function on an already open
    # folder dialog
    current_folder = request.args.get('current_folder')
    folder = request.args.get('folder')

    config = current_app.cea_config
    section, parameter_name = fqname.split(':')
    parameter = config.sections[section].parameters[parameter_name]

    if not current_folder:
        # first time calling, use current value of parameter for current folder
        current_folder = os.path.abspath(parameter.get())
        folder = None
    else:
        current_folder = os.path.abspath(os.path.join(current_folder, folder))

    if not os.path.exists(current_folder):
        # use home directory if it doesn't exist
        current_folder = os.path.expanduser('~')

    folders = []
    for entry in os.listdir(current_folder):
        if os.path.isdir(os.path.join(current_folder, entry)):
            folders.append(entry)

    current_folder = os.path.normpath(current_folder)
    breadcrumbs = current_folder.split(os.path.sep)

    return render_template('folder_listing.html', current_folder=current_folder,
                           folders=folders, title=parameter.help, fqname=fqname,
                           parameter_name=parameter.name, breadcrumbs=breadcrumbs)


# FIXME: this should be refactored, as it is originally from tools/routes.py
@blueprint.route('/open-file-dialog/<fqname>')
def route_open_file_dialog(fqname):
    """Return html of file structure for that parameter"""

    # these arguments are only set when called with the `navigate_to` function on an already open
    # file dialog
    current_folder = request.args.get('current_folder')
    folder = request.args.get('folder')

    config = current_app.cea_config
    section, parameter_name = fqname.split(':')
    parameter = config.sections[section].parameters[parameter_name]

    if not current_folder:
        # first time calling, use current value of parameter for current folder
        current_folder = os.path.dirname(parameter.get())
        folder = None
    else:
        current_folder = os.path.abspath(os.path.join(current_folder, folder))

    if not os.path.exists(current_folder):
        # use home directory if it doesn't exist
        current_folder = os.path.expanduser('~')

    folders = []
    files = []
    for entry in os.listdir(current_folder):
        if os.path.isdir(os.path.join(current_folder, entry)):
            folders.append(entry)
        else:
            ext = os.path.splitext(entry)[1]
            if parameter._extensions and ext and ext[1:] in parameter._extensions:
                files.append(entry)
            elif not parameter._extensions:
                # any file can be added
                files.append(entry)

    breadcrumbs = os.path.normpath(current_folder).split(os.path.sep)

    return render_template('file_listing.html', current_folder=current_folder,
                           folders=folders, files=files, title=parameter.help, fqname=fqname,
                           parameter_name=parameter.name, breadcrumbs=breadcrumbs)


def get_scenarios(path):
    """Return list of scenarios based on folder structure"""
    scenarios = []
    for directory in os.listdir(path):
        if os.path.isdir(os.path.join(path, directory)) and not directory.startswith('.'):
            scenarios.append(directory)
    return scenarios
