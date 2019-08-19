from flask_restplus import Namespace, Resource, fields

import cea.scripts
import cea.config

api = Namespace('Files', description='Reading and writing files for cea-worker jobs')


@api.route('/<project>/<scenario>/<location>')
class File(Resource):
    def get(self, project, scenario, location):
        return "hello, world!"
