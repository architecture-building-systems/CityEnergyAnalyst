"""
jobs: maintain a list of jobs to be simulated.
"""
import subprocess
import sys
import uuid
from typing import Dict, Any, List
from urllib.parse import urlparse

import psutil
import sqlalchemy.exc
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from cea.interfaces.dashboard.dependencies import CEAServerUrl, CEAWorkerProcesses, CEAProjectID, CEAServerSettings, \
    CEAUserID, CEASeverDemoAuthCheck, CEAStreams
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState, get_current_time
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.lib.socketio import sio

# FIXME: Add auth checks after giving workers access token
router = APIRouter()
logger = getCEAServerLogger("cea-server-jobs")


class JobError(BaseModel):
    message: str
    stacktrace: str


class JobOutput(BaseModel):
    output: Any


@router.get("/", dependencies=[CEASeverDemoAuthCheck])
@router.get("/list")
async def get_jobs(session: SessionDep, project_id: CEAProjectID) -> List[JobInfo]:
    """Get a list of jobs for the current project"""
    result = await session.execute(select(JobInfo).where(JobInfo.project_id == project_id))
    return result.scalars().all()


@router.get("/{job_id}")
async def get_job_info(session: SessionDep, job_id: str) -> JobInfo:
    """Return a JobInfo by id"""
    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/new", dependencies=[CEASeverDemoAuthCheck])
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
    await session.commit()
    await session.refresh(job)

    await sio.emit("cea-job-created", job.model_dump(mode='json'), room=f"user-{job.created_by}")
    return job


@router.post("/started/{job_id}")
async def set_job_started(session: SessionDep, job_id: str) -> JobInfo:
    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.STARTED
        job.start_time = get_current_time()
        await session.commit()
        await session.refresh(job)

        await sio.emit("cea-worker-started", job.model_dump(mode='json'), room=f"user-{job.created_by}")
        return job
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/success/{job_id}")
async def set_job_success(session: SessionDep, job_id: str, streams: CEAStreams,
                          worker_processes: CEAWorkerProcesses, output: JobOutput) -> JobInfo:
    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.SUCCESS
        job.error = None
        job.end_time = get_current_time()
        job.stdout = "".join(await streams.pop(job_id, []))
        await session.commit()
        await session.refresh(job)

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)

        job_info = job.model_dump(mode='json')
        job_info["output"] = output.output
        await sio.emit("cea-worker-success", job_info, room=f"user-{job.created_by}")
        return job
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/error/{job_id}")
async def set_job_error(session: SessionDep, job_id: str, error: JobError, streams: CEAStreams,
                        worker_processes: CEAWorkerProcesses) -> JobInfo:
    message = error.message
    stacktrace = error.stacktrace

    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.ERROR
        job.error = message
        job.end_time = get_current_time()
        job.stdout = "".join(await streams.pop(job_id, []))
        job.stderr = stacktrace
        await session.commit()
        await session.refresh(job)

        if job.id in await worker_processes.values():
            await worker_processes.delete(job.id)
        await sio.emit("cea-worker-error", job.model_dump(mode='json'), room=f"user-{job.created_by}")

        logger.warning(f"Error found in job {job_id}: {job.error}")
        logger.error(f"stacktrace:\n{job.stderr}")
        return job
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/start/{job_id}', dependencies=[CEASeverDemoAuthCheck])
async def start_job(session: SessionDep, worker_processes: CEAWorkerProcesses, server_url: CEAServerUrl, job_id: str,
                    settings: CEAServerSettings):
    """Start a ``cea-worker`` subprocess for the script. (FUTURE: add support for cloud-based workers"""

    # Validate job_id is a valid UUID
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format. Must be a valid UUID.")

    # Validate server_url is a valid HTTP/HTTPS URL
    try:
        parsed_url = urlparse(str(server_url))
        if not parsed_url.scheme or parsed_url.scheme not in ['http', 'https']:
            raise HTTPException(status_code=400, detail="Invalid server_url. Must be a valid HTTP or HTTPS URL.")
        if not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Invalid server_url. Missing hostname.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid server_url format.")

    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Use validated parameters in command
    command = [sys.executable, "-m", "cea.worker", job_id, str(server_url)]
    logger.debug(f"command: {command}")
    process = subprocess.Popen(command)

    await worker_processes.set(job_id, process.pid)
    return job_id


@router.post("/cancel/{job_id}", dependencies=[CEASeverDemoAuthCheck])
async def cancel_job(session: SessionDep, job_id: str, worker_processes: CEAWorkerProcesses) -> JobInfo:
    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.CANCELED
        job.error = "Canceled by user"
        job.end_time = get_current_time()
        await session.commit()
        await session.refresh(job)

        await kill_job(job_id, worker_processes)
        await sio.emit("cea-worker-canceled", job.model_dump(mode='json'), room=f"user-{job.created_by}")
        return job
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}", dependencies=[CEASeverDemoAuthCheck])
async def delete_job(session: SessionDep, job_id: str) -> JobInfo:
    """
    Delete a job from the database. This is only possible if the job is not running.
    """
    try:
        job = await session.get(JobInfo, job_id)
    except sqlalchemy.exc.OperationalError as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.state == JobState.STARTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is still running")

    try:
        job.state = JobState.DELETED
        await session.delete(job)
        await session.commit()

        return job
    except Exception as e:
        logger.error(e)
        await session.rollback()
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

        children = process.children(recursive=True)
        for child in children:
            logger.warning(f"-- killing child {pid}")
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        process.kill()
    except psutil.NoSuchProcess:
        return
    finally:
        await worker_processes.delete(jobid)
