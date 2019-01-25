from flask import Blueprint, render_template, current_app, request, redirect, jsonify, url_for
import os
import cea.inputlocator

blueprint = Blueprint(
    'project_blueprint',
    __name__,
    url_prefix='/project',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/show')
def route_show():
    """Show the project inputs form."""
    cea_config = current_app.cea_config
    locator = cea.inputlocator.InputLocator(cea_config.scenario)
    regions = list(cea_config.sections['general'].parameters['region']._choices)
    selected_region = cea_config.region
    scenario = cea_config.scenario
    weather = cea_config.weather
    multiprocessing = cea_config.multiprocessing
    weather_names = locator.get_weather_names()

    parameters = cea_config.sections['general'].parameters.values()
    weather_dict = {wn: locator.get_weather(wn) for wn in locator.get_weather_names()}

    return render_template('project.html', parameters=parameters, weather_dict=weather_dict, regions=regions, selected_region=selected_region,
                           weather=weather, weather_names=weather_names, multiprocessing=multiprocessing)


@blueprint.route('/save', methods=['POST'])
def route_save():
    """Save the new project data to the configuration file"""
    cea_config = current_app.cea_config
    print(request.form)
    cea_config.scenario_name = request.form['scenario-name']
    cea_config.project = request.form['project']
    cea_config.region = request.form['region']
    cea_config.weather = request.form['weather']
    cea_config.number_of_cpus_to_keep_free = int(request.form['number-of-cpus-to-keep-free'])
    cea_config.multiprocessing = 'multiprocessing' in request.form
    cea_config.debug = 'debug' in request.form
    cea_config.district_heating_network = 'district-heating-network' in request.form
    cea_config.district_cooling_network = 'district-cooling-network' in request.form
    cea_config.save()
    return redirect(url_for('project_blueprint.route_show'))


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
