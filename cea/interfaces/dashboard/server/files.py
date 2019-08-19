from flask_restplus import Namespace, Resource, fields
from flask import current_app

import os
import cea.scripts
import cea.inputlocator

api = Namespace('Files', description='Reading and writing files for cea-worker jobs')


@api.route('/<project>/<scenario>/<location>')
class File(Resource):
    def get(self, project, scenario, location):
        project_root = current_app.cea_config.server.project_root
        scenario_path = os.path.join(project_root, project, scenario)
        locator = cea.inputlocator.InputLocator(scenario=scenario_path)
        file_path = getattr(locator, location)()
        return file_path
