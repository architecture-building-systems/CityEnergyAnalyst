"""
streams: maintain a list of streams containing ``cea-worker`` output for jobs.

FIXME: when does this data get cleared?
"""
from __future__ import division
from __future__ import print_function

from flask import request
from flask_restplus import Namespace, Resource, fields

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

api = Namespace('Streams', description='A collection of output from cea-worker processes')

streams = {}


@api.route("/write/<int:jobid>")
class WriteStream(Resource):
    def put(self, jobid):
        # FIXME: this output needs to bubble up to the user interface...
        print(request.data, end='')