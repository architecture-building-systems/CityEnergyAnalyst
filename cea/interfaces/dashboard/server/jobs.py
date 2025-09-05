"""
jobs: maintain a list of jobs to be simulated.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Dict, Any, List
from urllib.parse import urlparse

import psutil
import sqlalchemy.exc
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from sqlmodel import select
from starlette.datastructures import UploadFile as _UploadFile

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


def get_cea_job_temp_prefix(job_id: str) -> str:
    """Get the prefix used for temporary directories for a given job ID."""
    return f"cea_job_{job_id}_"

async def process_job_parameters(parameters: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Process job parameters, handling UploadFile types by writing them to temporary storage
    and replacing the UploadFile with the file path.
    
    Returns:
        Dict with file paths substituted and temp directory path (if any files were processed)
    """
    processed_params = parameters.copy()
    temp_dir = None

    # Look for UploadFile instances in parameters
    for key, value in parameters.items():
        if isinstance(value, _UploadFile):
            # Create temp directory with job ID if not already created
            if temp_dir is None:
                temp_dir = tempfile.mkdtemp(prefix=get_cea_job_temp_prefix(job_id))
                logger.info(f"Created temporary directory for job {job_id}: {temp_dir}")
            
            # Write file to temp directory with safe filename
            safe_filename = os.path.basename(value.filename or f"upload_{key}") if value.filename else f"upload_{key}"
            # Remove any remaining path separators and null bytes
            safe_filename = safe_filename.replace(os.sep, "_").replace(os.altsep or "", "_").replace("\0", "")
            file_path = os.path.join(temp_dir, safe_filename)
            
            try:
                with open(file_path, "wb") as f:
                    # Stream the upload in chunks to avoid loading entire file into memory
                    chunk_size = 64 * 1024  # 64KB chunks
                    try:
                        while True:
                            chunk = await value.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                    finally:
                        # Ensure upload handle is closed even on exceptions
                        await value.close()
                
                # Replace UploadFile with file path in parameters
                processed_params[key] = file_path
                logger.info(f"Wrote uploaded file for parameter '{key}' to: {file_path}")
                
            except Exception as e:
                # Clean up temp directory if file writing failed
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                logger.error(f"Failed to write uploaded file for parameter '{key}': {e}")
                raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {key}")
    
    return processed_params


def cleanup_job_temp_files(job_id: str):
    """
    Clean up temporary files for a job by finding and removing temp directories
    that match the job ID pattern using glob pattern matching.
    """
    import glob
    temp_base = tempfile.gettempdir()
    pattern = os.path.join(temp_base, f"{get_cea_job_temp_prefix(job_id)}*")

    try:
        for temp_dir_path in glob.glob(pattern):
            if os.path.isdir(temp_dir_path):
                shutil.rmtree(temp_dir_path)
                logger.info(f"Cleaned up temporary directory for job {job_id}: {temp_dir_path}")
    except Exception as e:
        logger.error(f"Error cleaning up temp files for job {job_id}: {e}")


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
async def create_new_job(request: Request, session: SessionDep, project_id: CEAProjectID, user_id: CEAUserID,
                         settings: CEAServerSettings) -> JobInfo:
    """Post a new job to the list of jobs to complete"""
    content_type = request.headers.get("content-type", "")
    
    # Handle both form data and JSON payloads for backwards compatibility
    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        # Form data handling (supports file uploads)
        form_data = await request.form()
        
        # Parse nested parameters structure using regex
        parameters = {}
        script = None
        parameter_pattern = re.compile(r'^parameters\[([^\[\]]+)\]$')
        
        for key, value in form_data.items():
            if key == "script":
                script = value
            else:
                # Try to match parameter pattern
                match = parameter_pattern.match(key)
                if match:
                    param_name = match.group(1)
                    parameters[param_name] = value
        
        args = {"script": script, "parameters": parameters}
    else:
        # JSON handling (backwards compatibility)
        json_data = await request.json()
        args = json_data
        logger.info(f"Received JSON payload: {json_data}")
    
    logger.info(f"Adding new job: args={args}")

    if not args["script"]:
        raise HTTPException(status_code=422, detail="Missing required field: 'script'.")

    # Create job first to get job ID for temp file handling
    job = JobInfo(script=args["script"], parameters={}, project_id=project_id, created_by=user_id)
    session.add(job)
    await session.commit()
    await session.refresh(job)

    try:
        # Process parameters to handle any UploadFile instances
        parameters = await process_job_parameters(args["parameters"], job.id)

        # FIXME: Forcing remote multiprocessing to be disabled for now,
        #  find solution for restricting number of processes per user
        if not settings.local:
            parameters["multiprocessing"] = False

        # Update job with processed parameters
        job.parameters = parameters
        await session.commit()
        await session.refresh(job)

        await sio.emit("cea-job-created", job.model_dump(mode='json'), room=f"user-{job.created_by}")
        return job
    except Exception:
        # If parameter processing fails, clean up the job and any temp files
        cleanup_job_temp_files(job.id)
        await session.delete(job)
        await session.commit()
        raise


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

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)

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

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)

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
    command = [sys.executable, "-m", "cea.worker", "--suppress-warnings", job_id, str(server_url)]
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

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)

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

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)

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
