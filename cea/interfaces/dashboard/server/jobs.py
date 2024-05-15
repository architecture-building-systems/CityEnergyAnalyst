"""
jobs: maintain a list of jobs to be simulated.
"""

import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime

import psutil

from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, current_app

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
JOB_STATE_CANCELED = 4

job_info_model = api.model('JobInfo', {
    'id': fields.Integer,
    'script': fields.String,
    'state': fields.Integer,
    'error': fields.String,
    'parameters': fields.Raw,
    'start_time': fields.DateTime,
    'end_time': fields.DateTime,
})

job_info_request_parser = reqparse.RequestParser()
job_info_request_parser.add_argument("id", type=int, location="json")
job_info_request_parser.add_argument("script", type=str, required=True, location="json")
job_info_request_parser.add_argument("state", location="json")
job_info_request_parser.add_argument("error", location="json")
job_info_request_parser.add_argument("parameters", type=dict, location="json")


worker_processes = {}  # jobid -> subprocess.Popen


def next_id():
    """FIXME: replace with better solution"""
    try:
        return max(jobs.keys()) + 1
    except ValueError:
        # this is the first job...
        return 1


# FIXME: replace with database or similar solution
@dataclass
class JobInfo:
    """Store all the information required to run a job"""
    id: str
    script: str
    parameters: dict
    state: int = JOB_STATE_PENDING
    error: str = None
    start_time: datetime = None
    end_time: datetime = None


jobs = {
    # jobid -> JobInfo
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
        current_app.socketio.emit("cea-job-created", api.marshal(job, job_info_model))
        return job


@api.route("/list")
class ListJobs(Resource):
    def get(self):
        return [asdict(job) for job in jobs.values()]


@api.route("/started/<int:jobid>")
class JobStarted(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_STARTED
        job.start_time = datetime.now()
        current_app.socketio.emit("cea-worker-started", api.marshal(job, job_info_model))
        return job


@api.route("/success/<int:jobid>")
class JobSuccess(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_SUCCESS
        job.error = None
        job.end_time = datetime.now()
        if job.id in worker_processes:
            del worker_processes[job.id]
        current_app.socketio.emit("cea-worker-success", api.marshal(job, job_info_model))
        return job


@api.route("/error/<int:jobid>")
class JobError(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_ERROR
        job.error = request.data.decode()
        job.end_time = datetime.now()
        if job.id in worker_processes:
            del worker_processes[job.id]
        current_app.socketio.emit("cea-worker-error", api.marshal(job, job_info_model))
        return job


@api.route('/start/<int:jobid>')
class JobStart(Resource):
    def post(self, jobid):
        """Start a ``cea-worker`` subprocess for the script. (FUTURE: add support for cloud-based workers"""
        print("tools/route_start: {jobid}".format(**locals()))
        worker_processes[jobid] = subprocess.Popen(["python", "-m", "cea.worker", "{jobid}".format(jobid=jobid)])
        return jobid


@api.route("/cancel/<int:jobid>")
class JobCanceled(Resource):
    @api.marshal_with(job_info_model)
    def post(self, jobid):
        job = jobs[jobid]
        job.state = JOB_STATE_CANCELED
        job.error = "Canceled by user"
        job.end_time = datetime.now()
        kill_job(jobid)
        current_app.socketio.emit("cea-worker-canceled", api.marshal(job, job_info_model))
        return job


def kill_job(jobid):
    """Kill the processes associated with a jobid"""
    if jobid not in worker_processes:
        return

    popen = worker_processes[jobid]
    # using code from here: https://stackoverflow.com/a/4229404/2260
    # to terminate child processes too
    print("killing child processes of {jobid} ({pid})".format(jobid=jobid, pid=popen.pid))
    try:
        process = psutil.Process(popen.pid)
    except psutil.NoSuchProcess:
        return
    children = process.children(recursive=True)
    for child in children:
        print("-- killing child {pid}".format(pid=child.pid))
        child.kill()
    process.kill()
    del worker_processes[jobid]
