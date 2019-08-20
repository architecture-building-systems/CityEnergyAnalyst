"""
jobs: maintain a list of jobs to be simulated.
"""
from __future__ import division
from __future__ import print_function

from flask_restplus import Namespace, Resource, fields

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

api = Namespace('Jobs', description='A job server for cea-worker processes')

# Job states
JOB_STATE_PENDING = 0
JOB_STATE_STARTED = 1
JOB_STATE_SUCCESS = 2
JOB_STATE_ERROR = 3

job_info_model = api.model('JobInfo', {
    'id': fields.Integer,
    'script': fields.String,
    'state': fields.Integer,
    'parameters': fields.Raw,
})


# FIXME: replace with database or similar solution
class JobInfo(object):
    """Store all the information required to run a job"""
    def __init__(self, id, script, parameters):
        self.id = id
        self.script = script
        self.parameters = parameters
        self.state = JOB_STATE_PENDING


jobs = {
    1: JobInfo(id=1, script="data-helper", parameters={
        "scenario": r"c:\Users\darthoma\Documents\CityEnergyAnalyst\projects\reference-case-open\baseline",
    }),
}


@api.route("/<int:jobid>")
class Job(Resource):
    @api.marshal_with(job_info_model)
    def get(self, jobid):
        return jobs[jobid]


@api.route("/list")
class ListJobs(Resource):
    @api.marshal_with(job_info_model, as_list=True)
    def get(self):
        return jobs.values()
