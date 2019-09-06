from flask_restplus import Namespace, Resource, fields, abort

import cea.config
import os
import re

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
        config = cea.config.Configuration()
        name = os.path.basename(config.project)
        return {'name': name, 'path': config.project, 'scenario': config.scenario_name, 'scenarios': config.get_parameter('general:scenario-name')._choices}

    @api.doc(body=PROJECT_PATH_MODEL, responses={200: 'Success', 400: 'Invalid Path given'})
    def post(self):
        config = cea.config.Configuration()
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
            choices = config.get_parameter(
                'general:scenario-name')._choices
            if scenario in choices:
                config.scenario_name = scenario
                config.save()
                return {'message': 'Scenario changed'}
            else:
                abort(
                    400, 'Scenario does not exist', choices=choices)
