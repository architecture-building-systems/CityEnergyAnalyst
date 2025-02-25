"""
jobs: maintain a list of jobs to be simulated.
"""
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any
import uuid

import psutil
from fastapi import APIRouter, Request, HTTPException

from cea.interfaces.dashboard.dependencies import CEAServerUrl, CEAWorkerProcesses
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.server.socketio import sio

router = APIRouter()


@router.get("/")
@router.get("/list")
async def get_jobs(session: SessionDep):
    return [job.model_dump(mode='json') for job in session.query(JobInfo)]


@router.get("/{job_id}")
async def get_job_info(session: SessionDep, job_id: str):
    """Return a JobInfo by id"""
    return session.get(JobInfo, job_id)


@router.post("/new")
async def create_new_job(payload: Dict[str, Any], session: SessionDep):
    """Post a new job to the list of jobs to complete"""
    args = payload
    print(f"NewJob: args={args}")

    job = JobInfo(id=str(uuid.uuid4()), script=args["script"], parameters=args["parameters"])
    session.add(job)
    session.commit()
    session.refresh(job)

    await sio.emit("cea-job-created", job.model_dump(mode='json'))
    return job


@router.post("/started/{job_id}")
async def set_job_started(session: SessionDep, job_id: str) -> JobInfo:
    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job.state = JobState.STARTED
        job.start_time = datetime.now(timezone.utc)
        session.add(job)
        session.commit()
        session.refresh(job)

        await sio.emit("cea-worker-started", job.model_dump(mode='json'))
        return job
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/success/{job_id}")
async def set_job_success(session: SessionDep, job_id: str, worker_processes: CEAWorkerProcesses) -> JobInfo:
    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job.state = JobState.SUCCESS
        job.error = None
        job.end_time = datetime.now()
        session.commit()

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-success", job.model_dump(mode='json'))
        return job
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/error/{job_id}")
async def set_job_error(session: SessionDep, job_id: str, worker_processes: CEAWorkerProcesses, request: Request) -> JobInfo:
    body = await request.body()
    error = body.decode("utf-8")

    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job.state = JobState.ERROR
        job.error = error
        job.end_time = datetime.now()

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-error", job.model_dump(mode='json'))
        return job
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))



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
async def cancel_job(session: SessionDep, job_id: str, worker_processes: CEAWorkerProcesses) -> JobInfo:
    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job.state = JobState.CANCELED
        job.error = "Canceled by user"
        job.end_time = datetime.now()
        session.commit()

        await kill_job(job_id, worker_processes)
        await sio.emit("cea-worker-canceled", job.model_dump(mode='json'))
        return job
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
