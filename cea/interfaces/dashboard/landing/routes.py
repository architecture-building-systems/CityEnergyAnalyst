from flask import Blueprint, render_template, current_app, redirect, request, url_for, jsonify

import os
import geopandas
from shapely.geometry import shape
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
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
def route_new_project():
    cea_config = current_app.cea_config
    project = os.path.dirname(cea_config.project)
    # TODO: Check if directory already exists
    return render_template('new_project.html', project=project)


@blueprint.route('/project_overview/')
def route_project_overview():
    cea_config = current_app.cea_config
    project_path = cea_config.project
    project_name = os.path.basename(project_path)

    # Get the list of scenarios
    scenarios = []
    for directory in os.listdir(project_path):
        if os.path.isdir(os.path.join(project_path, directory)):
            scenarios.append(directory)
    return render_template('project_overview.html', project_name=project_name, scenarios=scenarios)


@blueprint.route('/create_project/map')
def route_zone_creator():
    return render_template('project_map.html')


@blueprint.route('/create_poly', methods=['POST'])
def route_poly_creator():
    # Get polygon points and create .shp file
    data = request.get_json()
    poly = shape(data['geometry'])
    poly = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(), geometry=[poly])
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    poly.to_file(locator.get_site_polygon())
    print('site.shp file created at %s'%locator.get_site_polygon())
    return jsonify(dict(redirect=url_for('plots_blueprint.index')))


@blueprint.route('/create_project/save', methods=['POST'])
def route_save():
    # FIXME: Cannot create new project if current project does not exist
    cea_config = current_app.cea_config
    cea_config.scenario_name = 'baseline'
    cea_config.project = os.path.join(request.form['projectPath'], request.form['projectName'])

    # Make sure that the project folder exists
    try:
        os.makedirs(cea_config.project)
    except OSError as e:
        print(e.message)

    return redirect(url_for('landing_blueprint.route_project_overview'))


@blueprint.route('/open_project', methods=['POST'])
def route_open():
    return None


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
