import os
import shutil

import geopandas
from flask import current_app
from flask_restplus import Namespace, Resource, fields, abort
from staticmap import StaticMap, Polygon

# import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

api = Namespace('Project', description='Current project for CEA')

# PATH_REGEX = r'(^[a-zA-Z]:\\[\\\S|*\S]?.*$)|(^(/[^/ ]*)+/?$)'


PROJECT_PATH_MODEL = api.model('Project Path', {
    'path': fields.String(description='Path of Project'),
    'scenario': fields.String(description='Path of Project')
})

PROJECT_MODEL = api.inherit('Project', PROJECT_PATH_MODEL, {
    'name': fields.String(description='Name of Project'),
    'scenario': fields.String(description='Name of Current Scenario'),
    'scenarios': fields.List(fields.String, description='Name of Current Scenario')
})


@api.route('/')
class Project(Resource):
    @api.marshal_with(PROJECT_MODEL)
    def get(self):
        config = current_app.cea_config
        name = os.path.basename(config.project)
        return {'name': name, 'path': config.project, 'scenario': config.scenario_name,
                'scenarios': config.get_parameter('general:scenario-name')._choices}

    @api.doc(body=PROJECT_PATH_MODEL, responses={200: 'Success', 400: 'Invalid Path given'})
    def post(self):
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


@api.route('/<string:scenario>')
class Scenario(Resource):
    def get(self, scenario):
        config = current_app.cea_config
        choices = config.get_parameter('general:scenario-name')._choices
        if scenario in choices:
            return {'name': scenario}
        else:
            abort(400, 'Scenario does not exist', choices=choices)

    def delete(self, scenario):
        config = current_app.cea_config
        choices = config.get_parameter('general:scenario-name')._choices
        if scenario in choices:
            scenario_path = os.path.join(config.project, scenario)
            try:
                if config.scenario_name == scenario:
                    config.scenario_name = ''
                    config.save()
                shutil.rmtree(scenario_path)

            except WindowsError:
                abort(400, 'Make sure that the scenario you are trying to delete is not open in any application.<br>'
                           'Try and refresh the page again.')
            return {'scenarios': config.get_parameter('general:scenario-name')._choices}
        else:
            abort(400, 'Scenario does not exist', choices=choices)


@api.route('/<string:scenario>/image')
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

