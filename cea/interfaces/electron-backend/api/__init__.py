from flask import Blueprint
from flask_restplus import Api
from .tools import api as tools
from .project import api as project
from .inputs import api as inputs


blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint)

api.add_namespace(tools, path='/tools')
api.add_namespace(project, path='/project')
api.add_namespace(inputs, path='/inputs')


# @api.errorhandler(InvalidPathException)
# def handle_path_exception(error):
#     return {'message': 'Invalid Path given'}, 400
