import os
import shutil
import glob
from functools import wraps
import traceback

import geopandas
from flask import current_app, request
from flask_restplus import Namespace, Resource, fields, abort
from staticmap import StaticMap, Polygon
from shapely.geometry import shape

import cea.inputlocator
import cea.api
import cea.config
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

api = Namespace('Project', description='Current project for CEA')

# PATH_REGEX = r'(^[a-zA-Z]:\\[\\\S|*\S]?.*$)|(^(/[^/ ]*)+/?$)'


PROJECT_PATH_MODEL = api.model('Project Path', {
    'path': fields.String(description='Path of Project'),
})

SCENARIO_PATH_MODEL = api.inherit('Scenario Path', PROJECT_PATH_MODEL, {
    'scenario': fields.String(description='Name of Scenario')
})

PROJECT_MODEL = api.inherit('Project', SCENARIO_PATH_MODEL, {
    'name': fields.String(description='Name of Project'),
    'scenarios': fields.List(fields.String, description='Name of Current Scenario')
})


@api.route('/')
class Project(Resource):
    @api.marshal_with(PROJECT_MODEL)
    @api.doc(params={'path': 'Path of Project (Leave blank to use path in config)'})
    def get(self):
        project_path = request.args.get('path')
        if project_path is None:
            config = current_app.cea_config
            scenario = config.scenario_name
        else:
            if not os.path.exists(project_path):
                abort(400, 'Project path: "{project_path}" does not exist'.format(project_path=project_path))
            # Prevent changing current_app config
            config = cea.config.Configuration()
            config.project = project_path
            scenario = None

        return {'name': os.path.basename(config.project), 'path': config.project, 'scenario': scenario,
                'scenarios': list_scenario_names_for_project(config)}

    def post(self):
        """Create new project folder"""
        name = api.payload.get('name')
        project_path = api.payload.get('path')

        if name is not None and project_path is not None:
            project_path = os.path.join(project_path, name)
            try:
                os.makedirs(project_path)
            except OSError as e:
                abort(400, str(e))

            return {'message': 'Project folder created', 'path': project_path}
        else:
            abort(400, 'Parameters not valid - Project Name: {name}, Project Path: {project_path}'.format(
                name=name, project_path=project_path
            ))


@api.route('/scenario/')
class Scenarios(Resource):
    def post(self):
        """Create new scenario"""
        config = current_app.cea_config
        payload = api.payload
        new_scenario_path = os.path.join(config.project, payload['name'])

        # Make sure that the scenario folder exists
        try:
            os.makedirs(new_scenario_path)
        except OSError as e:
            print(e.message)

        locator = cea.inputlocator.InputLocator(new_scenario_path)

        # Run database_initializer to copy databases to input
        if 'databases-path' in payload:
            try:
                cea.api.data_initializer(config, scenario=new_scenario_path, databases_path=payload['databases-path'])
            except Exception as e:
                trace = traceback.format_exc()
                return {'message': 'data_initializer: {}'.format(e.message), 'trace': trace}, 500

        if payload['input-data'] == 'import':
            files = payload['files']

            if files is not None:
                try:
                    # Local variables
                    if 'terrain' not in files:
                        files['terrain'] = ''
                    if 'streets' not in files:
                        files['streets'] = ''
                    if 'surroundings' not in files:
                        files['surroundings'] = ''
                    if 'typology' not in files:
                        files['typology'] = ''
                    cea.api.create_new_scenario(config,
                                               scenario=new_scenario_path,
                                               zone=files['zone'],
                                               surroundings=files['surroundings'],
                                               streets=files['streets'],
                                               terrain=files['terrain'],
                                               typology=files['typology'])

                except Exception as e:
                    trace = traceback.format_exc()
                    return {'message': e.message, 'trace': trace}, 500

        elif payload['input-data'] == 'copy':
            try:
                source_scenario = os.path.join(config.project, payload['copy-scenario'])
                shutil.copytree(cea.inputlocator.InputLocator(source_scenario).get_input_folder(),
                                locator.get_input_folder())
            except OSError as e:
                trace = traceback.format_exc()
                return {'message': e.message, 'trace': trace}, 500

        elif payload['input-data'] == 'generate':
            tools = payload['tools']
            if tools is not None:
                for tool in tools:
                    try:
                        if tool == 'zone':
                            # FIXME: Setup a proper endpoint for site creation
                            site = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                                          geometry=[shape(payload['geojson']['features'][0]['geometry'])])
                            site_path = locator.get_site_polygon()
                            locator.ensure_parent_folder_exists(site_path)
                            site.to_file(site_path)
                            print('site.shp file created at %s' % site_path)
                            cea.api.zone_helper(config, scenario=new_scenario_path)
                        elif tool == 'surroundings':
                            cea.api.surroundings_helper(config, scenario=new_scenario_path)
                        elif tool == 'streets':
                            cea.api.streets_helper(config, scenario=new_scenario_path)
                        elif tool == 'terrain':
                            cea.api.terrain_helper(config, scenario=new_scenario_path)
                        elif tool == 'weather':
                            cea.api.weather_helper(config, scenario=new_scenario_path)
                    except Exception as e:
                        trace = traceback.format_exc()
                        return {'message': '{}_helper: {}'.format(tool, e.message), 'trace': trace}, 500

        return {'scenarios': list_scenario_names_for_project(config)}


def glob_shapefile_auxilaries(shapefile_path):
    """Returns a list of files in the same folder as ``shapefile_path``, but allows for varying extensions.
    This gets the .dbf, .shx, .prj, .shp and .cpg files"""
    return glob.glob('{basepath}.*'.format(basepath=os.path.splitext(shapefile_path)[0]))


def check_scenario_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        config = current_app.cea_config
        choices = list_scenario_names_for_project(config)
        if kwargs['scenario'] not in choices:
            abort(400, 'Scenario does not exist', choices=choices)
        else:
            return func(*args, **kwargs)
    return wrapper


# FIXME: Potential Issue. Need to check if the scenario being deleted/renamed is running in scripts.
@api.route('/scenario/<string:scenario>')
class Scenario(Resource):
    method_decorators = [check_scenario_exists]

    def get(self, scenario):
        """Scenario details"""
        return {'name': scenario}

    def put(self, scenario):
        """Update scenario"""
        config = current_app.cea_config
        scenario_path = os.path.join(config.project, scenario)
        payload = api.payload
        try:
            if 'name' in payload:
                new_path = os.path.join(config.project, payload['name'])
                os.rename(scenario_path, new_path)
                if config.scenario_name == scenario:
                    config.scenario_name = payload['name']
                    config.save()
                return {'name': payload['name']}
        except WindowsError:
            abort(400, 'Make sure that the scenario you are trying to rename is not open in any application. '
                       'Try and refresh the page again.')

    def delete(self, scenario):
        """Delete scenario from project"""
        config = current_app.cea_config
        scenario_path = os.path.join(config.project, scenario)
        try:
            if config.scenario_name == scenario:
                config.scenario_name = ''
                config.save()
            shutil.rmtree(scenario_path)
            return {'scenarios': list_scenario_names_for_project(config)}
        except WindowsError:
            abort(400, 'Make sure that the scenario you are trying to delete is not open in any application. '
                       'Try and refresh the page again.')


@api.route('/scenario/<string:scenario>/image')
class ScenarioImage(Resource):
    @api.doc(params={'projectPath': 'Path of Project (Leave blank to use path in config)'})
    def get(self, scenario):
        project_path = request.args.get('projectPath')
        if project_path is None:
            config = current_app.cea_config
        else:
            if not os.path.exists(project_path):
                abort(400, 'Project path: "{project_path}" does not exist'.format(project_path=project_path))
            config = cea.config.Configuration()
            config.project = project_path

        choices = list_scenario_names_for_project(config)
        if scenario in choices:
            locator = cea.inputlocator.InputLocator(os.path.join(config.project, scenario))
            zone_path = locator.get_zone_geometry()
            if os.path.isfile(zone_path):
                cache_path = os.path.join(config.project, '.cache')
                image_path = os.path.join(cache_path, scenario + '.png')

                zone_modified = os.path.getmtime(zone_path)
                if not os.path.isfile(image_path):
                    image_modified = 0
                else:
                    image_modified = os.path.getmtime(image_path)

                if zone_modified > image_modified:
                    # Make sure .cache folder exists
                    if not os.path.exists(cache_path):
                        os.makedirs(cache_path)

                    try:
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
                    except Exception as e:
                        abort(400, str(e))

                import base64
                with open(image_path, 'rb') as imgFile:
                    image = base64.b64encode(imgFile.read())

                return {'image': image}
            abort(400, 'Zone file not found')
        else:
            abort(400, 'Scenario does not exist', choices=choices)


def list_scenario_names_for_project(config):
    return config.get_parameter('general:scenario-name')._choices

