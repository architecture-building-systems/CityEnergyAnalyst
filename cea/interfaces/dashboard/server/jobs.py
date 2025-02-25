"""
jobs: maintain a list of jobs to be simulated.
"""
import subprocess
from datetime import datetime
from typing import Dict, Any

import psutil
from fastapi import APIRouter, Request

from cea.interfaces.dashboard.dependencies import CEAJobs, CEAServerUrl, CEAWorkerProcesses
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState
from cea.interfaces.dashboard.server.socketio import sio

router = APIRouter()


@router.get("/")
@router.get("/list")
async def get_jobs(jobs: CEAJobs):
    return [job.dict() for job in await jobs.values()]


@router.get("/{job_id}")
async def get_job_info(jobs: CEAJobs, job_id: str):
    """Return a JobInfo by id"""
    return await jobs.get(job_id)


@router.post("/new")
async def create_new_job(jobs: CEAJobs, payload: Dict[str, Any]):
    """Post a new job to the list of jobs to complete"""
    args = payload
    print(f"NewJob: args={args}")

    async def next_id():
        """
        FIXME: replace with better solution
        """
        try:
            return str(len(await jobs.keys()) + 1)
        except ValueError:
            # this is the first job...
            return str(1)

    job = JobInfo(id=await next_id(), script=args["script"], parameters=args["parameters"])
    await jobs.set(job.id, job)
    await sio.emit("cea-job-created", job.model_dump(mode='json'))
    return job


@router.post("/started/{job_id}")
async def set_job_started(jobs: CEAJobs, job_id: str) -> JobInfo:
    job = await jobs.get(job_id)
    job.state = JobState.STARTED
    job.start_time = datetime.now()
    await jobs.set(job.id, job)

    await sio.emit("cea-worker-started", job.model_dump(mode='json'))
    return job


@router.post("/success/{job_id}")
async def set_job_success(jobs: CEAJobs, job_id: str, worker_processes: CEAWorkerProcesses) -> JobInfo:
    job = await jobs.get(job_id)
    job.state = JobState.SUCCESS
    job.error = None
    job.end_time = datetime.now()
    await jobs.set(job.id, job)

    if job.id in await worker_processes.values():
        await worker_processes.delete(job.id)
    await sio.emit("cea-worker-success", job.model_dump(mode='json'))
    return job


@router.post("/error/{job_id}")
async def set_job_error(jobs: CEAJobs, job_id: str, worker_processes: CEAWorkerProcesses, request: Request) -> JobInfo:
    body = await request.body()
    error = body.decode("utf-8")

    job = await jobs.get(job_id)
    job.state = JobState.ERROR
    job.error = error
    job.end_time = datetime.now()
    await jobs.set(job.id, job)

    if job.id in await worker_processes.values():
        await worker_processes.delete(job.id)
    await sio.emit("cea-worker-error", job.model_dump(mode='json'))
    return job


@router.post('/start/{job_id}')
async def start_job(worker_processes: CEAWorkerProcesses, server_url: CEAServerUrl, job_id: str):
    """Start a ``cea-worker`` subprocess for the script. (FUTURE: add support for cloud-based workers"""
    print(f"tools/route_start: {job_id}")
    process = subprocess.Popen([
        "python", "-m", "cea.worker", f"{job_id}", f"{server_url}"
    ])
    await worker_processes.set(job_id, process.pid)
    return job_id


@router.post("/cancel/{job_id}")
async def cancel_job(jobs: CEAJobs, job_id: str, worker_processes: CEAWorkerProcesses) -> JobInfo:
    job = await jobs.get(job_id)
    job.state = JobState.CANCELED
    job.error = "Canceled by user"
    job.end_time = datetime.now()
    await jobs.set(job.id, job)

    await kill_job(job_id, worker_processes)
    await sio.emit("cea-worker-canceled", job.model_dump(mode='json'))
    return job


async def kill_job(jobid, worker_processes):
    """Kill the processes associated with a jobid"""
    if jobid not in await worker_processes.values():
        return

    pid = await worker_processes.get(jobid)
    # using code from here: https://stackoverflow.com/a/4229404/2260
    # to terminate child processes too
    print(f"killing child processes of {jobid} ({pid})")
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    children = process.children(recursive=True)
    for child in children:
        print(f"-- killing child {pid}")
        child.kill()
    process.kill()
    await worker_processes.delete(jobid)
