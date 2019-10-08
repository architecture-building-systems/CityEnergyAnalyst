from flask import Blueprint
from flask_restplus import Api
from .tools import api as tools
from .project import api as project
from .inputs import api as inputs
from .dashboard import api as dashboard
from .glossary import api as glossary


blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint)

api.add_namespace(tools, path='/tools')
api.add_namespace(project, path='/project')
api.add_namespace(inputs, path='/inputs')
api.add_namespace(dashboard, path='/dashboard')
api.add_namespace(glossary, path='/glossary')
