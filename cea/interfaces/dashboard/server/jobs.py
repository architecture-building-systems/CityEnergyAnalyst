"""
jobs: maintain a list of jobs to be simulated.
"""
import subprocess
from typing import Dict, Any, List

import psutil
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from cea.interfaces.dashboard.dependencies import CEAServerUrl, CEAWorkerProcesses, CEAProjectID, CEAServerSettings, \
    CEACheckAuth, CEAUserID
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState, get_current_time
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.server.streams import streams
from cea.interfaces.dashboard.server.socketio import sio

# FIXME: Add auth checks after giving workers access token
router = APIRouter()
logger = getCEAServerLogger("cea-server-jobs")


class JobError(BaseModel):
    message: str
    stacktrace: str


@router.get("/")
@router.get("/list")
async def get_jobs(session: SessionDep, project_id: CEAProjectID) -> List[JobInfo]:
    """Get a list of jobs for the current project"""
    return [job for job in session.exec(select(JobInfo).where(JobInfo.project_id == project_id))]


@router.get("/{job_id}")
async def get_job_info(session: SessionDep, job_id: str) -> JobInfo:
    """Return a JobInfo by id"""
    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/new")
async def create_new_job(payload: Dict[str, Any], session: SessionDep, project_id: CEAProjectID, user_id: CEAUserID,
                         settings: CEAServerSettings) -> JobInfo:
    """Post a new job to the list of jobs to complete"""
    args = payload
    logger.info(f"Adding new job: args={args}")

    parameters = args["parameters"]

    # FIXME: Forcing remote multiprocessing to be disabled for now,
    #  find solution for restricting number of processes per user
    if not settings.local:
        parameters["multiprocessing"] = False

    job = JobInfo(script=args["script"], parameters=parameters, project_id=project_id, created_by=user_id)
    session.add(job)
    session.commit()
    session.refresh(job)

    await sio.emit("cea-job-created", job.model_dump(mode='json'), room=f"user-{job.created_by}")
    return job


@router.post("/started/{job_id}")
async def set_job_started(session: SessionDep, job_id: str) -> JobInfo:
    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.STARTED
        job.start_time = get_current_time()
        session.commit()
        session.refresh(job)

        await sio.emit("cea-worker-started", job.model_dump(mode='json'), room=f"user-{job.created_by}")
        return job
    except Exception as e:
        logger.error(e)
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
        session.commit()
        session.refresh(job)

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-success", job.model_dump(mode='json'), room=f"user-{job.created_by}")
        return job
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/error/{job_id}")
async def set_job_error(session: SessionDep, job_id: str, error: JobError,
                        worker_processes: CEAWorkerProcesses) -> JobInfo:
    message = error.message
    stacktrace = error.stacktrace

    job = session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.ERROR
        job.error = message
        job.end_time = get_current_time()
        job.stdout = "".join(streams.get(job_id, []))
        job.stderr = stacktrace
        session.commit()
        session.refresh(job)

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-error", job.model_dump(mode='json'), room=f"user-{job.created_by}")

        logger.warning(f"Error found in job {job_id}: {job.error}")
        logger.error(f"stacktrace:\n{job.stderr}")
        return job
    except Exception as e:
        logger.error(e)
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
        session.commit()
        session.refresh(job)

        await kill_job(job_id, worker_processes)
        await sio.emit("cea-worker-canceled", job.model_dump(mode='json'), room=f"user-{job.created_by}")
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
        logger.warning(f"Unable to kill job. Could no find job: {jobid}.")
        return

    pid = await worker_processes.get(jobid)
    # using code from here: https://stackoverflow.com/a/4229404/2260
    # to terminate child processes too
    logger.warning(f"killing child processes of {jobid} ({pid})")
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    children = process.children(recursive=True)
    for child in children:
        logger.warning(f"-- killing child {pid}")
        child.kill()
    process.kill()
    await worker_processes.delete(jobid)
