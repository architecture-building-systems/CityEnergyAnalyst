"""
jobs: maintain a list of jobs to be simulated.
"""
import subprocess
from typing import Dict, Any, List

import psutil
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from cea.interfaces.dashboard.dependencies import CEAConfig, CEAServerUrl, CEAWorkerProcesses
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState, Project, get_current_time
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.server.streams import streams
from cea.interfaces.dashboard.server.socketio import sio

router = APIRouter()

class JobError(BaseModel):
    message: str
    stacktrace: str


@router.get("/")
@router.get("/list")
async def get_jobs(session: SessionDep, config: CEAConfig) -> List[JobInfo]:
    """Get a list of jobs for the current project"""
    project_id = get_project_id(session, config.project)

    return [job for job in session.exec(select(JobInfo).where(JobInfo.project_id == project_id))]


@router.get("/{job_id}")
async def get_job_info(session: SessionDep, job_id: str) -> JobInfo:
    """Return a JobInfo by id"""
    return session.get(JobInfo, job_id)


@router.post("/new")
async def create_new_job(payload: Dict[str, Any], session: SessionDep, config: CEAConfig) -> JobInfo:
    """Post a new job to the list of jobs to complete"""
    args = payload
    print(f"NewJob: args={args}")

    project_id = get_project_id(session, config.project)

    job = JobInfo(script=args["script"], parameters=args["parameters"], project_id=project_id)
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
        job.start_time = get_current_time()
        session.add(job)
        session.commit()
        session.refresh(job)

        await sio.emit("cea-worker-started", job.model_dump(mode='json'))
        return job
    except Exception as e:
        print(e)
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
        job.end_time = get_current_time()
        job.stdout = "".join(streams.get(job_id, []))
        session.add(job)
        session.commit()
        session.refresh(job)

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-success", job.model_dump(mode='json'))
        return job
    except Exception as e:
        print(e)
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/error/{job_id}")
async def set_job_error(session: SessionDep, job_id: str, error: JobError, worker_processes: CEAWorkerProcesses) -> JobInfo:
    message = error.message
    error = error.stacktrace

    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job.state = JobState.ERROR
        job.error = message
        job.end_time = get_current_time()
        job.stdout = "".join(streams.get(job_id, []))
        job.stderr = error
        session.add(job)
        session.commit()
        session.refresh(job)

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-error", job.model_dump(mode='json'))

        print(f"Error found in job {job_id}: {job.error}")
        print(job.stderr)
        return job
    except Exception as e:
        print(e)
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
        job.end_time = get_current_time()
        session.add(job)
        session.commit()
        session.refresh(job)

        await kill_job(job_id, worker_processes)
        await sio.emit("cea-worker-canceled", job.model_dump(mode='json'))
        return job
    except Exception as e:
        print(e)
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(session: SessionDep, job_id: str) -> JobInfo:
    """
    Delete a job from the database. This is only possible if the job is not running.
    """
    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.state == JobState.STARTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is still running")

    try:
        job.state = JobState.DELETED
        session.delete(job)
        session.commit()
        
        return job
    except Exception as e:
        print(e)
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def kill_job(jobid, worker_processes):
    """Kill the processes associated with a jobid"""
    if jobid not in await worker_processes.keys():
        print(f"Unable to kill job. Could no find job: {jobid}.")
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


def get_project_id(session: SessionDep, project_uri: str):
    """Get the project ID from the project URI."""
    project = session.exec(select(Project).where(Project.uri == project_uri)).first()

    # If project not found, create a new one
    if not project:
        project = Project(name=project_uri, uri=project_uri)
        session.add(project)
        session.commit()
        session.refresh(project)
    
    return project.id