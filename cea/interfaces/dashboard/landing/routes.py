from flask import Blueprint, render_template, current_app, redirect, request, url_for, jsonify

import os
import geopandas
from shapely.geometry import shape
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

import cea.inputlocator
import cea.scripts
from . import worker

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
    # TODO: Could add some preprocessing steps
    return render_template('new_scenario.html')


@blueprint.route('/project-overview')
def route_project_overview():
    cea_config = current_app.cea_config
    project_path = cea_config.project
    project_name = os.path.basename(project_path)

    # Get the list of scenarios
    scenarios = get_scenarios(project_path)
    return render_template('project_overview.html', project_name=project_name, scenarios=scenarios)


@blueprint.route('/create-zone')
def route_create_zone():
    scenario = request.args['scenario']
    return render_template('project_map.html', scenario=scenario)


@blueprint.route('/create-poly', methods=['POST'])
def route_poly_creator():
    # Get polygon points and create .shp file
    data = request.get_json()
    poly = shape(data['geometry'])
    poly = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(), geometry=[poly])

    cea_config = current_app.cea_config
    # Save current scenario name
    temp = cea_config.scenario_name
    cea_config.scenario_name = request.args['scenario']
    scenario_path = cea_config.scenario
    locator = cea.inputlocator.InputLocator(scenario_path)
    poly_path = locator.get_site_polygon()

    poly.to_file(poly_path)
    print('site.shp file created at %s' % poly_path)

    # FIXME: THIS IS A HACK, refactor this! This emulates tool/start/script to run zone_helper.py
    ###########################################
    form = {
        'scenario': scenario_path,
        'height-ag': '',
        'floors-ag': '',
        'year-construction': 2000,
        'height-bg': 3,
        'floors-bg': 1,
        'occupancy - type': 'MULTI_RES'
    }

    kwargs = {}
    script = 'zone-helper'
    print('/start/%s' % script)
    parameters = [p for _, p in cea_config.matching_parameters(cea.scripts.by_name(script).parameters)]
    for parameter in parameters:
        print('%s: %s' % (parameter.name, form.get(parameter.name)))
        kwargs[parameter.name] = parameter.decode(form.get(parameter.name))
    current_app.workers[script] = worker.main(script, **kwargs)
    ##########################################
    cea_config.scenario_name = temp

    return jsonify(dict(redirect='/landing/project-overview'))


@blueprint.route('/create-project/save', methods=['POST'])
def route_create_project_save():
    # FIXME: Cannot create new project if current project in config does not exist
    cea_config = current_app.cea_config
    # FIXME: A scenario will created based on the current scenario of the config
    cea_config.scenario_name = 'baseline'
    cea_config.project = os.path.join(request.form.get('projectPath'), request.form.get('projectName'))

    # Make sure that the project folder exists
    try:
        os.makedirs(cea_config.project)
    except OSError as e:
        print(e.message)
    cea_config.save()
    return redirect(url_for('landing_blueprint.route_project_overview'))


@blueprint.route('/create-scenario/save', methods=['POST'])
def route_create_scenario_save():
    cea_config = current_app.cea_config
    scenario = request.form.get('scenarioName')

    try:
        os.makedirs(os.path.join(cea_config.project, scenario))
    except OSError as e:
        print(e.message)

    if request.form.get('create-zone') == 'on':
        return redirect(url_for('landing_blueprint.route_create_zone', scenario=scenario))
    else:
        return redirect(url_for('landing_blueprint.route_project_overview'))


@blueprint.route('/open-project')
def route_open_project():
    cea_config = current_app.cea_config
    project = cea_config.project
    return render_template('open_project.html', project=project)


@blueprint.route('/open-project/save', methods=['POST'])
def route_open_project_save():
    cea_config = current_app.cea_config
    project_path = request.form.get('projectPath')
    scenarios = get_scenarios(project_path)

    cea_config.scenario_name = scenarios[0]
    cea_config.project = project_path
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
    return redirect(url_for('inputs_blueprint.route_table_get', db='zone'))


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
        if os.path.isdir(os.path.join(path, directory)):
            scenarios.append(directory)
    return scenarios
