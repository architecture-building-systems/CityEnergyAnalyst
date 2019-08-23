"""
jobs: maintain a list of jobs to be simulated.
"""
from __future__ import division
from __future__ import print_function

from flask_restplus import Namespace, Resource, fields, reqparse
from flask import request

from cea.interfaces.dashboard.dashboard import socketio

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
    'error': fields.String,
    'parameters': fields.Raw,
})

job_info_request_parser = reqparse.RequestParser()
job_info_request_parser.add_argument('id', type=int)
job_info_request_parser.add_argument('script', required=True)
job_info_request_parser.add_argument('state', )
job_info_request_parser.add_argument('error')
job_info_request_parser.add_argument('parameters', type=dict)


def next_id():
    """FIXME: replace with better solution"""
    return max(jobs.keys()) + 1


# FIXME: replace with database or similar solution
class JobInfo(object):
    """Store all the information required to run a job"""
    def __init__(self, id, script, parameters):
        self.id = id
        self.script = script
        self.parameters = parameters
        self.state = JOB_STATE_PENDING
        self.error = None

    def __repr__(self):
        return "<JobInfo(id={id}, script={script}, state={state}>".format(**self.__dict__)


jobs = {
    1: JobInfo(id=1, script="data-helper", parameters={
        "scenario": r"c:\Users\darthoma\Documents\CityEnergyAnalyst\projects\reference-case-open\baseline",
    }),
}


@api.route("/<int:jobid>")
class Job(Resource):
    @api.marshal_with(job_info_model)
    def get(self, jobid):
        """Return a JobInfo by id"""
        return jobs[jobid]


@api.route("/new")
class NewJob(Resource):
    @api.marshal_with(job_info_model)
    def post(self):
        """Post a new job to the list of jobs to complete"""
        args = job_info_request_parser.parse_args()
        print("NewJob: args={args}".format(**locals()))
        job = JobInfo(id=next_id(), script=args.script, parameters=args.parameters)
        jobs[job.id] = job
        print("NewJob: args={args}, job={job}".format(**locals()))
        return job


@api.route("/list")
class ListJobs(Resource):
    @api.marshal_with(job_info_model, as_list=True)
    def get(self):
        return jobs.values()


@api.route("/started/<int:jobid>")
class JobStarted(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_STARTED
        socketio.emit("cea-worker-started", api.marshal(job, job_info_model))
        return job


@api.route("/success/<int:jobid>")
class JobSuccess(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_SUCCESS
        job.error = None
        socketio.emit("cea-worker-success", api.marshal(job, job_info_model))
        return job


@api.route("/error/<int:jobid>")
class JobError(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_ERROR
        job.error = request.data
        socketio.emit("cea-worker-error", api.marshal(job, job_info_model))
        return job
