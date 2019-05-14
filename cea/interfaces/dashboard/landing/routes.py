from flask import Blueprint, render_template, current_app, redirect, request, url_for, jsonify

import os, shutil
import json
import geopandas
from shapely.geometry import shape
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

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
    return render_template('project_overview.html', project_name=project_name, scenarios=scenarios)


@blueprint.route('/project-overview/<scenario>/<func>')
def route_project_overview_function(scenario, func):
    if func == 'delete':
        return render_template('modal/delete_scenario.html', scenario=scenario)


@blueprint.route('/project-overview/delete/<scenario>', methods=['POST'])
def route_delete_scenario(scenario):
    cea_config = current_app.cea_config
    scenario_path = os.path.join(cea_config.project, scenario)
    shutil.rmtree(scenario_path)
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

    if request.form.get('input-files') == 'import':
        # TODO
        pass

    elif request.form.get('input-files') == 'copy':
        shutil.copytree(os.path.join(cea_config.project, request.form.get('scenario'), 'inputs'),
                        os.path.join(scenario_path, 'inputs'))

    elif request.form.get('input-files') == 'generate':
        tools = request.form.getlist('tools')
        print(tools)
        if tools is not None:
            for tool in tools:
                print(tool)
                if tool == 'zone-helper':
                    # FIXME: Setup a proper endpoint for site creation
                    data = json.loads(request.form.get('poly-string'))
                    site = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                                  geometry=[shape(data['geometry'])])
                    locator = cea.inputlocator.InputLocator(scenario_path)
                    site_path = locator.get_site_polygon()
                    site.to_file(site_path)
                    print('site.shp file created at %s' % site_path)
                    cea.api.zone_helper(cea_config)
                elif tool == 'district-helper':
                    cea.api.district_helper(cea_config)
                elif tool == 'streets-helper':
                    cea.api.streets_helper(cea_config)
                elif tool == 'terrain-helper':
                    cea.api.terrain_helper(cea_config)

    return redirect(url_for('inputs_blueprint.route_table_get', db='zone'))


@blueprint.route('/open-project')
def route_open_project():
    cea_config = current_app.cea_config
    project = cea_config.project
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
    return redirect(url_for('inputs_blueprint.route_table_get', db='zone'))


@blueprint.route('/create-scenario/<script_name>/settings')
def route_script_settings(script_name):
    config = current_app.cea_config
    locator = cea.inputlocator.InputLocator(config.scenario)
    script = cea.scripts.by_name(script_name)
    return render_template('script_settings.html', script=script, parameters=parameters_for_script(script_name, config))


def parameters_for_script(script_name, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    parameters = [p for _, p in config.matching_parameters(cea.scripts.by_name(script_name).parameters)]
    return parameters


@blueprint.route('/save-config/<script>', methods=['POST'])
def route_save_config(script):
    """Save the configuration for this tool to the configuration file"""
    for parameter in parameters_for_script(script, current_app.cea_config):
        print('%s: %s' % (parameter.name, request.form.get(parameter.name)))
        parameter.set(parameter.decode(request.form.get(parameter.name)))
    current_app.cea_config.save()
    return jsonify(True)


@blueprint.route('/restore-defaults/<script_name>', methods=['POST'])
def route_restore_defaults(script_name):
    """Restore the default configuration values for the CEA"""
    config = current_app.cea_config
    default_config = cea.config.Configuration(config_file=cea.config.DEFAULT_CONFIG)

    for parameter in parameters_for_script(script_name, config):
        parameter.set(default_config.sections[parameter.section.name].parameters[parameter.name].get())
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
