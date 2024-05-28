


import os
import shutil
import glob
import tempfile
from functools import wraps
import traceback

import geopandas
from flask import current_app, request
from flask_restx import Namespace, Resource, fields, abort
from staticmap import StaticMap, Polygon
from shapely.geometry import shape
import json

import cea.inputlocator
import cea.api
import cea.config
from cea.plots.colors import color_to_rgb
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

api = Namespace('Project', description='Current project for CEA')

# PATH_REGEX = r'(^[a-zA-Z]:\\[\\\S|*\S]?.*$)|(^(/[^/ ]*)+/?$)'


PROJECT_PATH_MODEL = api.model('Project Path', {
    'project': fields.String(description='Path of Project'),
})

SCENARIO_PATH_MODEL = api.inherit('Scenario Path', PROJECT_PATH_MODEL, {
    'scenario_name': fields.String(description='Name of Scenario')
})

PROJECT_MODEL = api.inherit('Project', SCENARIO_PATH_MODEL, {
    'project_name': fields.String(description='Name of Project'),
    'scenarios_list': fields.List(fields.String, description='List of Scenarios found in Project')
})

NEW_PROJECT_MODEL = api.model('New Project', {
    'project_name': fields.String(description='Name of Project'),
    'project_root': fields.String(description='Root path of Project')
})


@api.route('/')
class Project(Resource):
    @api.marshal_with(PROJECT_MODEL)
    @api.doc(params={'project': 'Path of Project (Leave blank to use path in config)'})
    def get(self):
        project = request.args.get('project')
        if project is None:
            config = current_app.cea_config
            scenario_name = config.scenario_name
        else:
            if not os.path.exists(project):
                abort(400, 'Project path: "{project}" does not exist'.format(project=project))
            # Prevent changing current_app config
            config = cea.config.Configuration()
            config.project = project
            scenario_name = None

        return {'project_name': os.path.basename(config.project), 'project': config.project,
                'scenario_name': scenario_name, 'scenarios_list': list_scenario_names_for_project(config)}

    @api.expect(NEW_PROJECT_MODEL)
    def post(self):
        """Create new project folder"""
        project_name = api.payload.get('project_name')
        project_root = api.payload.get('project_root')

        if project_name and project_root:
            project = os.path.join(project_root, project_name)
            try:
                os.makedirs(project, exist_ok=True)
            except OSError as e:
                abort(400, str(e))

            return {'message': 'Project folder created', 'project': project}
        else:
            abort(400, 'Parameters not valid - project_name: {project_name}, project_root: {project_root}'.format(
                project_name=project_name, project_root=project_root
            ))

    @api.expect(SCENARIO_PATH_MODEL)
    def put(self):
        """Update Project info in config"""
        config = current_app.cea_config
        project = api.payload.get('project')
        scenario_name = api.payload.get('scenario_name')

        if project and scenario_name:
            # Project path must exist but scenario does not have to
            if os.path.exists(project):
                config.project = project
                config.scenario_name = scenario_name
                config.save()
                return {'message': 'Updated project info in config', 'project': project, 'scenario_name': scenario_name}
            else:
                abort(400, 'project: "{project}" does not exist'.format(project=project))
        else:
            abort(400,
                  'Parameters not valid - project: {project}, scenario_name: {scenario_name}'.format(
                      project=project, scenario_name=scenario_name))


@api.route('/scenario/')
class Scenarios(Resource):
    def post(self):
        """Create new scenario"""
        payload: dict = api.payload
        project = payload.get('project')
        scenario_name = payload.get('scenario_name')
        if scenario_name is None:
            return {'message': 'scenario_name parameter cannot be empty'}, 500

        databases_path = payload.get('databases_path')
        input_data = payload.get('input_data')

        with tempfile.TemporaryDirectory() as tmp:
            config = cea.config.Configuration()
            config.project = tmp
            config.scenario_name = "temp_scenario"

            _project = project or config.project

            locator = cea.inputlocator.InputLocator(config.scenario)

            # Run database_initializer to copy databases to input
            if databases_path is not None:
                try:
                    cea.api.data_initializer(config, databases_path=databases_path)
                except Exception as e:
                    raise Exception(f'data_initializer: {e}') from e

            if input_data == 'import':
                files = payload.get('files')
                if files is not None:
                    try:
                        output_path, project_name = os.path.split(config.project)
                        cea.api.create_new_scenario(config,
                                                    output_path=output_path,
                                                    project=project_name,
                                                    scenario=config.scenario_name,
                                                    zone=files.get('zone'),
                                                    surroundings=files.get('surroundings'),
                                                    streets=files.get('streets'),
                                                    terrain=files.get('terrain'),
                                                    typology=files.get('typology'))
                    except Exception as e:
                        raise Exception(f'create_new_scenario: {e}') from e

            elif input_data == 'copy':
                source_scenario_name = payload.get('copy_scenario')
                source_scenario = os.path.join(_project, source_scenario_name)
                os.makedirs(locator.get_input_folder(), exist_ok=True)
                shutil.copytree(cea.inputlocator.InputLocator(source_scenario).get_input_folder(),
                                locator.get_input_folder())

            elif input_data == 'generate':
                tools = payload.get('tools', [])
                for tool in tools:
                    try:
                        if tool == 'zone':
                            # FIXME: Setup a proper endpoint for site creation
                            site_geojson = api.payload.get('geojson')
                            if site_geojson is None:
                                raise ValueError('Could not find GeoJson for site polygon')
                            site = geopandas.GeoDataFrame(crs=get_geographic_coordinate_system(),
                                                          geometry=[shape(site_geojson['features'][0]['geometry'])])
                            site_path = locator.get_site_polygon()
                            locator.ensure_parent_folder_exists(site_path)
                            site.to_file(site_path)
                            print(f'site.shp file created at {site_path}')
                            cea.api.zone_helper(config)
                        elif tool == 'surroundings':
                            cea.api.surroundings_helper(config)
                        elif tool == 'streets':
                            cea.api.streets_helper(config)
                        elif tool == 'terrain':
                            cea.api.terrain_helper(config)
                        elif tool == 'weather':
                            cea.api.weather_helper(config)
                    except Exception as e:
                        raise Exception(f'{tool}_helper: {e}') from e

            # Move temp scenario to correct path
            new_scenario_path = os.path.join(_project, str(scenario_name).strip())
            print(f"Moving from {config.scenario} to {new_scenario_path}")
            shutil.move(config.scenario, new_scenario_path)

        return {'scenarios_list': list_scenario_names_for_project(config)}


def glob_shapefile_auxilaries(shapefile_path):
    """Returns a list of files in the same folder as ``shapefile_path``, but allows for varying extensions.
    This gets the .dbf, .shx, .prj, .shp and .cpg files"""
    return glob.glob('{basepath}.*'.format(basepath=os.path.splitext(shapefile_path)[0]))


def check_scenario_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        config = current_app.cea_config
        if len(request.data):
            try:
                # DELETE method might have a "project" payload...
                data = json.loads(request.data.decode('utf-8'))
                config.project = data["project"]
            except Exception:
                pass
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
        new_scenario_name = api.payload.get('name')
        try:
            if new_scenario_name is not None:
                new_path = os.path.join(config.project, new_scenario_name)
                os.rename(scenario_path, new_path)
                if config.scenario_name == scenario:
                    config.scenario_name = new_scenario_name
                    config.save()
                return {'name': new_scenario_name}
        except OSError:
            abort(400, 'Make sure that the scenario you are trying to rename is not open in any application. '
                       'Try and refresh the page again.')

    def delete(self, scenario):
        """Delete scenario from project"""
        config = current_app.cea_config
        scenario_path = os.path.join(config.project, scenario)
        try:
            shutil.rmtree(scenario_path)
            return {'scenarios': list_scenario_names_for_project(config)}
        except OSError:
            traceback.print_exc()
            abort(400, 'Make sure that the scenario you are trying to delete is not open in any application. '
                       'Try and refresh the page again.')


@api.route('/scenario/<string:scenario>/image')
class ScenarioImage(Resource):
    @api.doc(params={'project': 'Path of Project (Leave blank to use path in config)'})
    def get(self, scenario):
        building_limit = 500

        project = request.args.get('project')
        if project is None:
            config = current_app.cea_config
        else:
            if not os.path.exists(project):
                abort(400, 'Project path: "{project}" does not exist'.format(project=project))
            config = cea.config.Configuration()
            config.project = project

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
                    print(f'Generating preview image for scenario: {scenario}')
                    # Make sure .cache folder exists
                    os.makedirs(cache_path, exist_ok=True)

                    try:
                        zone_df = geopandas.read_file(zone_path)
                        zone_df = zone_df.to_crs(get_geographic_coordinate_system())
                        polygons = zone_df['geometry']

                        m = StaticMap(256, 160, url_template='http://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png')
                        if len(polygons) <= building_limit:
                            polygons = [list(polygons.geometry.exterior[row_id].coords) for row_id in
                                        range(polygons.shape[0])]
                            for polygon in polygons:
                                out = Polygon(polygon, color_to_rgb('purple'), 'black', False)
                                m.add_polygon(out)
                        else:
                            print(f'Number of buildings({len(polygons)}) exceed building limit({building_limit}): '
                                  f'Generating simplified image')
                            # Generate only the shape outline of the zone area
                            convex_hull = polygons.unary_union.convex_hull
                            polygon = convex_hull.exterior.coords
                            out = Polygon(polygon, None, color_to_rgb('purple'), False)
                            m.add_polygon(out)

                        image = m.render()
                        image.save(image_path)
                    except Exception as e:
                        abort(400, str(e))

                import base64
                with open(image_path, 'rb') as imgFile:
                    image = base64.b64encode(imgFile.read())

                return {'image': image.decode("utf-8")}
            abort(400, 'Zone file not found')
        else:
            abort(400, 'Scenario does not exist', choices=choices)


def list_scenario_names_for_project(config):
    with config.ignore_restrictions():
        return config.get_parameter('general:scenario-name')._choices
