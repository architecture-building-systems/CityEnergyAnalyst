import os
import shutil
import glob
from functools import wraps

import geopandas
from flask import current_app
from flask_restplus import Namespace, Resource, fields, abort
from staticmap import StaticMap, Polygon
from shapely.geometry import shape

import cea.inputlocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

api = Namespace('Project', description='Current project for CEA')

# PATH_REGEX = r'(^[a-zA-Z]:\\[\\\S|*\S]?.*$)|(^(/[^/ ]*)+/?$)'


PROJECT_PATH_MODEL = api.model('Project Path', {
    'path': fields.String(description='Path of Project'),
    'scenario': fields.String(description='Path of Scenario')
})

PROJECT_MODEL = api.inherit('Project', PROJECT_PATH_MODEL, {
    'name': fields.String(description='Name of Project'),
    'scenario': fields.String(description='Name of Current Scenario'),
    'scenarios': fields.List(fields.String, description='Name of Current Scenario')
})

NEW_PROJECT_MODEL = api.model('New Project', {
    'name': fields.String(description='Name of Project'),
    'path': fields.String(description='Path of Project')
})


@api.route('/')
class Project(Resource):
    @api.marshal_with(PROJECT_MODEL)
    def get(self):
        config = current_app.cea_config
        name = os.path.basename(config.project)
        if not os.path.exists(config.project):
            abort(400, 'Project path does not exist')
        if not os.path.exists(config.scenario):
            config.scenario_name = ''
            config.save()
        return {'name': name, 'path': config.project, 'scenario': config.scenario_name,
                'scenarios': config.get_parameter('general:scenario-name')._choices}

    @api.doc(body=PROJECT_PATH_MODEL, responses={200: 'Success', 400: 'Invalid Path given'})
    def put(self):
        """Update Project"""
        config = current_app.cea_config
        payload = api.payload

        if 'path' in payload:
            path = payload['path']
            if os.path.exists(path):
                config.project = path
                if 'scenario' not in payload:
                    config.scenario_name = ''
                    config.save()
                    return {'message': 'Project path changed'}
            else:
                abort(400, 'Path given does not exist')

        if 'scenario' in payload:
            scenario = payload['scenario']
            choices = config.get_parameter('general:scenario-name')._choices
            if scenario in choices:
                config.scenario_name = scenario
                config.save()
                return {'message': 'Scenario changed'}
            else:
                abort(400, 'Scenario does not exist', choices=choices)

    @api.doc(body=NEW_PROJECT_MODEL, responses={200: 'Success'})
    def post(self):
        """Create new project"""
        config = current_app.cea_config
        payload = api.payload

        if 'path' in payload:
            path = payload['path']
            name = payload['name']
            project_path = os.path.join(path, name)
            try:
                os.makedirs(project_path)
            except OSError as e:
                abort(400, str(e))

            config.project = project_path
            config.scenario_name = ''
            config.save()

            return {'message': 'Project created at {}'.format(project_path)}


@api.route('/scenario/')
class Scenarios(Resource):
    def post(self):
        """Create new scenario"""
        config = current_app.cea_config
        payload = api.payload

        # Make sure that the scenario folder exists
        try:
            os.makedirs(os.path.join(config.project, payload['name']))
        except OSError as e:
            print(e.message)

        config.scenario_name = payload['name']
        config.save()

        scenario_path = config.scenario

        locator = cea.inputlocator.InputLocator(scenario_path)

        if payload['input-data'] == 'import':
            files = payload['files']

            if files is not None:
                # since we're creating a new scenario, go ahead and and make sure we have
                # the folders _before_ we try copying to them
                locator.ensure_parent_folder_exists(locator.get_zone_geometry())
                locator.ensure_parent_folder_exists(locator.get_terrain())
                locator.ensure_parent_folder_exists(locator.get_building_age())
                locator.ensure_parent_folder_exists(locator.get_building_occupancy())
                locator.ensure_parent_folder_exists(locator.get_street_network())

                if 'zone' in files:
                    for filename in glob_shapefile_auxilaries(files['zone']):
                        shutil.copy(filename, locator.get_building_geometry_folder())
                if 'surroundings' in files:
                    for filename in glob_shapefile_auxilaries(files['surroundings']):
                        shutil.copy(filename, locator.get_building_geometry_folder())
                if 'surroundings' in files:
                    for filename in glob_shapefile_auxilaries(files['surroundings']):
                        shutil.copy(filename, locator.get_building_geometry_folder())
                if 'terrain' in files:
                    shutil.copyfile(files['terrain'], locator.get_terrain())
                if 'streets' in files:
                    shutil.copyfile(files['streets'], locator.get_street_network())

                from cea.datamanagement.zone_helper import calculate_age_file, calculate_occupancy_file
                if 'age' in files and files['age'] != '':
                    shutil.copyfile(files['age'], locator.get_building_age())
                elif 'zone' in files:
                    zone_df = geopandas.read_file(files['zone'])
                    calculate_age_file(zone_df, None, locator.get_building_age())

                if 'occupancy' in files and files['occupancy'] != '':
                    shutil.copyfile(files['occupancy'], locator.get_building_occupancy())
                elif 'zone' in files:
                    zone_df = geopandas.read_file(files['zone'])
                    if 'category' not in zone_df.columns:
                        # set 'MULTI_RES' as default
                        calculate_occupancy_file(zone_df, 'MULTI_RES', locator.get_building_occupancy())
                    else:
                        calculate_occupancy_file(zone_df, 'Get it from open street maps', locator.get_building_occupancy())

        elif payload['input-data'] == 'copy':
            source_scenario = os.path.join(config.project, payload['copy-scenario'])
            shutil.copytree(cea.inputlocator.InputLocator(source_scenario).get_input_folder(),
                            locator.get_input_folder())

        elif payload['input-data'] == 'generate':
            tools = payload['tools']
            if tools is not None:
                for tool in tools:
                    if tool == 'zone':
                        # FIXME: Setup a proper endpoint for site creation
                        site = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                                      geometry=[shape(payload['geojson']['features'][0]['geometry'])])
                        site_path = locator.get_site_polygon()
                        locator.ensure_parent_folder_exists(site_path)
                        site.to_file(site_path)
                        print('site.shp file created at %s' % site_path)
                        cea.api.zone_helper(config)
                    elif tool == 'surroundings':
                        cea.api.surroundings_helper(config)
                    elif tool == 'surroundings':
                        cea.api.surroundings_helper(config)
                    elif tool == 'streets':
                        cea.api.streets_helper(config)
                    elif tool == 'terrain':
                        cea.api.terrain_helper(config)
                    elif tool == 'weather':
                        cea.api.weather_helper(config)

        return {'scenarios': config.get_parameter('general:scenario-name')._choices}

def glob_shapefile_auxilaries(shapefile_path):
    """Returns a list of files in the same folder as ``shapefile_path``, but allows for varying extensions.
    This gets the .dbf, .shx, .prj, .shp and .cpg files"""
    return glob.glob('{basepath}.*'.format(basepath=os.path.splitext(shapefile_path)[0]))


def check_scenario_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        config = current_app.cea_config
        choices = config.get_parameter('general:scenario-name')._choices
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
            return {'scenarios': config.get_parameter('general:scenario-name')._choices}
        except WindowsError:
            abort(400, 'Make sure that the scenario you are trying to delete is not open in any application. '
                       'Try and refresh the page again.')


@api.route('/scenario/<string:scenario>/image')
class ScenarioImage(Resource):
    def get(self, scenario):
        config = current_app.cea_config
        choices = config.get_parameter('general:scenario-name')._choices
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

