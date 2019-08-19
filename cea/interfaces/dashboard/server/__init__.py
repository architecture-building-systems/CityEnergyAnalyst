"""
The /server api blueprint is used by cea-worker processes to manage jobs and files.
"""

from __future__ import print_function
from __future__ import division

from flask import Blueprint
from flask_restplus import Api
from .jobs import api as jobs
from .files import api as files

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


blueprint = Blueprint('server', __name__, url_prefix='/server')
api = Api(blueprint)

api.add_namespace(jobs, path='/jobs')
api.add_namespace(files, path='/files')