"""
jobs: maintain a list of jobs to be simulated.
"""
import json
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
from fastapi import APIRouter, HTTPException, status, Request, Query
from pydantic import BaseModel
from sqlmodel import select, desc
from starlette.datastructures import UploadFile as _UploadFile

from cea.interfaces.dashboard.dependencies import CEAServerUrl, CEAWorkerProcesses, CEAProjectID, CEAServerSettings, \
    CEAUserID, CEASeverDemoAuthCheck, CEAStreams
from cea.interfaces.dashboard.lib.database.models import JobInfo, JobState, get_current_time
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.lib.socketio import emit_with_retry

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
            if value.filename:
                safe_filename = os.path.basename(value.filename)
                # Remove dangerous characters but preserve the original filename structure
                import string
                safe_chars = string.ascii_letters + string.digits + ".-_"
                safe_filename = "".join(c if c in safe_chars else "_" for c in safe_filename)
                # Ensure filename is not empty after sanitization
                if not safe_filename or safe_filename.startswith("."):
                    safe_filename = f"upload_{key}"
            else:
                safe_filename = f"upload_{key}"
            file_path = os.path.join(temp_dir, safe_filename)
            # Normalize and ensure the file path is within temp_dir
            normalized_file_path = os.path.realpath(file_path)
            if not normalized_file_path.startswith(os.path.realpath(temp_dir) + os.sep):
                logger.error(f"Attempt to write file outside temp_dir detected for job {job_id}. Path: {normalized_file_path}")
                raise ValueError("Unsafe file path detected.")
            
            try:
                with open(normalized_file_path, "wb") as f:
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
async def get_jobs(
    session: SessionDep,
    project_id: CEAProjectID,
    limit: int | None = Query(None, description="Maximum number of jobs to return (most recent first)"),
    state: int | None = Query(None, description="Filter by job state (0=PENDING, 1=STARTED, 2=SUCCESS, 3=ERROR, 4=CANCELED, 5=KILLED)"),
    exclude_deleted: bool = Query(True, description="Exclude deleted jobs from results")
) -> List[JobInfo]:
    """
    Get a list of jobs for the current project with optional filtering.

    By default, returns all non-deleted jobs ordered by creation time (most recent first).
    Jobs are filtered by deleted_at field rather than state to preserve completion states.
    """
    query = select(JobInfo).where(JobInfo.project_id == project_id)

    # Filter by state if specified
    if state is not None:
        # Validate state is a valid JobState value
        try:
            job_state = JobState(state)
            query = query.where(JobInfo.state == job_state)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid state value. Must be between 0 and 5.")

    # Exclude deleted jobs by default based on deleted_at field
    if exclude_deleted:
        query = query.where(JobInfo.deleted_at.is_(None))

    # Order by created_time descending (most recent first)
    query = query.order_by(desc(JobInfo.created_time))

    # Apply limit if specified
    if limit is not None and limit > 0:
        query = query.limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())


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
    if "application/json" in content_type:
        # JSON handling (backwards compatibility)
        json_data = await request.json()

        script = json_data.get("script")
        parameters = json_data.get("parameters")
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        # Form data handling (supports file uploads)
        form_data = await request.form()
        script = form_data.get("script")
        parameters = {}

        # Regex to match parameters[key] pattern
        parameter_pattern = re.compile(r'^parameters\[([^\[\]]+)\]$')
        for key, value in form_data.items():
            match = parameter_pattern.match(key)
            if match:
                param_name = match.group(1)
                # Convert string booleans to actual booleans for form data
                if isinstance(value, _UploadFile):
                    parameters[param_name] = value  # Keep UploadFile as is for processing later
                elif isinstance(value, str):
                    # Handle nested JSON structures or boolean string in form data
                    try:
                        parameters[param_name] = json.loads(value)  # parse if it's JSON
                    except Exception:
                        parameters[param_name] = value
    else:
        raise HTTPException(status_code=400, detail="Unsupported content type.")

    if script is None:
        raise HTTPException(status_code=422, detail="Missing required field: 'script'.")

    # Create job first with empty parameters to get job ID for temp file handling
    job = JobInfo(script=script, parameters={}, project_id=project_id, created_by=user_id)

    try:
        # Process parameters to handle any UploadFile instances
        parameters = await process_job_parameters(parameters, job.id)

        # FIXME: Forcing remote multiprocessing to be disabled for now,
        #  find solution for restricting number of processes per user
        if not settings.local:
            parameters["multiprocessing"] = False

        # Update job with processed parameters
        job.parameters = parameters
    except Exception as e:
        # If parameter processing fails, clean up the job and any temp files
        cleanup_job_temp_files(job.id)
        raise e

    session.add(job)
    await session.commit()
    await session.refresh(job)

    await emit_with_retry("cea-job-created", job.model_dump(mode='json'), room=f"user-{job.created_by}")
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
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Emit event outside try-except so emit failures don't cause rollback
    await emit_with_retry("cea-worker-started", job.model_dump(mode='json'), room=f"user-{job.created_by}")
    return job


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
        
        stdout_capture = await streams.pop(job_id, [])
        if stdout_capture:
            job.stdout = "".join(stdout_capture)
        await session.commit()
        await session.refresh(job)

        # Ensure worker process is terminated and removed from tracking
        await cleanup_worker_process(job.id, worker_processes)

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Emit event outside try-except so emit failures don't cause rollback
    job_info = job.model_dump(mode='json')
    job_info["output"] = output.output
    await emit_with_retry("cea-worker-success", job_info, room=f"user-{job.created_by}")
    return job


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

        stdout_capture = await streams.pop(job_id, [])
        if stdout_capture:
            job.stdout = "".join(stdout_capture)
        job.stderr = stacktrace
        await session.commit()
        await session.refresh(job)

        # Ensure worker process is terminated and removed from tracking
        await cleanup_worker_process(job.id, worker_processes)

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Emit event outside try-except so emit failures don't cause rollback
    await emit_with_retry("cea-worker-error", job.model_dump(mode='json'), room=f"user-{job.created_by}")

    logger.warning(f"Error found in job {job_id}: {job.error}")
    logger.error(f"stacktrace:\n{job.stderr}")
    return job


@router.post('/start/{job_id}', dependencies=[CEASeverDemoAuthCheck])
async def start_job(session: SessionDep, worker_processes: CEAWorkerProcesses, server_url: CEAServerUrl, job_id: str,
                    user_id: CEAUserID, settings: CEAServerSettings):
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

    # Lock the row to prevent concurrent modifications (TOCTOU protection)
    result = await session.execute(
        select(JobInfo).where(JobInfo.id == job_id).with_for_update()
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Authorization check: only job creator can start
    if job.created_by != user_id:
        logger.warning(f"User {user_id} attempted to start job {job_id} owned by {job.created_by}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to start this job"
        )

    # Validate job state: must be PENDING and not deleted
    if job.state != JobState.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start job: job is not pending (current state: {job.state.name})"
        )

    if job.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start job: job has been deleted"
        )

    # Use validated parameters in command
    command = [sys.executable, "-m", "cea.worker", "--suppress-warnings", job_id, str(server_url)]
    logger.debug(f"command: {command}")
    process = subprocess.Popen(command)

    await worker_processes.set(job_id, process.pid)
    return job_id


@router.post("/cancel/{job_id}", dependencies=[CEASeverDemoAuthCheck])
async def cancel_job(session: SessionDep, job_id: str, user_id: CEAUserID,
                     worker_processes: CEAWorkerProcesses, streams: CEAStreams) -> JobInfo:
    # Lock the row to prevent concurrent modifications (TOCTOU protection)
    result = await session.execute(
        select(JobInfo).where(JobInfo.id == job_id).with_for_update()
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Authorization check: only job creator can cancel
    if job.created_by != user_id:
        logger.warning(f"User {user_id} attempted to cancel job {job_id} owned by {job.created_by}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to cancel this job"
        )

    # Validate state: can only cancel PENDING or STARTED jobs (protected by row lock)
    if job.state not in (JobState.PENDING, JobState.STARTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job: job is {job.state.name}"
        )

    # Check if job is deleted
    if job.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel job: job has been deleted"
        )

    try:
        job.state = JobState.CANCELED
        job.error = "Canceled by user"
        job.end_time = get_current_time()

        # Save any remaining stream output before clearing
        stdout_capture = await streams.pop(job_id, [])
        if stdout_capture:
            job.stdout = "".join(stdout_capture)

        await session.commit()
        await session.refresh(job)

        # Terminate worker process gracefully to allow cleanup functions to run
        await cleanup_worker_process(job_id, worker_processes, force=False)

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Emit event outside try-except so emit failures don't cause rollback
    await emit_with_retry("cea-worker-canceled", job.model_dump(mode='json'), room=f"user-{job.created_by}")
    return job


async def kill_job(session, job_id: str, worker_processes, streams) -> JobInfo:
    """
    Kill a job (server-initiated termination, e.g., during shutdown).
    This is different from cancel_job which is user-initiated.

    Args:
        session: Database session
        job_id: The job ID to kill
        worker_processes: Worker processes tracking store
        streams: Streams cache

    Returns:
        Updated JobInfo object with KILLED state
    """
    job = await session.get(JobInfo, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.state = JobState.KILLED
        job.error = "Killed by server shutdown"
        job.end_time = get_current_time()

        # Save any remaining stream output before clearing
        stdout_capture = await streams.pop(job_id, [])
        if stdout_capture:
            job.stdout = "".join(stdout_capture)

        await session.commit()
        await session.refresh(job)

        # Force kill the worker process immediately
        await cleanup_worker_process(job_id, worker_processes, force=True)

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Emit event outside try-except so emit failures don't cause rollback
    await emit_with_retry("cea-worker-killed", job.model_dump(mode='json'), room=f"user-{job.created_by}")
    return job


@router.delete("/{job_id}", dependencies=[CEASeverDemoAuthCheck])
async def delete_job(session: SessionDep, job_id: str, user_id: CEAUserID) -> JobInfo:
    """
    Mark a job as deleted (soft delete). The job row is not removed from the database,
    and the original completion state (SUCCESS/ERROR/CANCELED/KILLED) is preserved.
    Only the deleted_at and deleted_by fields are set. This is only possible if the job is not running.

    Uses row-level locking to prevent TOCTOU race conditions.
    """
    try:
        # Lock the row to prevent concurrent modifications (TOCTOU protection)
        result = await session.execute(
            select(JobInfo).where(JobInfo.id == job_id).with_for_update()
        )
        job = result.scalar_one_or_none()
    except sqlalchemy.exc.OperationalError as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Authorization check: only job creator can delete
    if job.created_by != user_id:
        logger.warning(f"User {user_id} attempted to delete job {job_id} owned by {job.created_by}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this job"
        )

    if job.state == JobState.STARTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is still running")

    # Prevent double deletion
    if job.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job already deleted")

    try:
        # Soft delete: preserve original state, add deletion metadata
        job.deleted_at = get_current_time()
        job.deleted_by = user_id

        await session.commit()
        await session.refresh(job)

        # Clean up temporary files for this job
        cleanup_job_temp_files(job.id)
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    await emit_with_retry("cea-job-deleted", job.model_dump(mode='json'), room=f"user-{job.created_by}")
    return job


def _force_kill_process(process: psutil.Process, pid: int, job_id: str):
    """
    Force kill a process and its children, waiting to reap them to prevent zombies.

    Args:
        process: The psutil.Process object
        pid: Process ID (for logging)
        job_id: Job ID (for logging)
    """
    logger.warning(f"Force killing worker process {pid} and children for job {job_id}")

    # Kill all children first
    children = process.children(recursive=True)
    for child in children:
        logger.warning(f"-- killing child process {child.pid}")
        try:
            child.kill()
            child.wait(timeout=1)  # Wait to reap and prevent zombies
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied as e:
            logger.warning(f"Access denied killing child process {child.pid}: {e}")
        except psutil.TimeoutExpired:
            logger.debug(f"Child process {child.pid} did not terminate within timeout")

    # Kill main process
    try:
        process.kill()
        process.wait(timeout=3)  # Wait to reap and prevent zombies
        logger.info(f"Worker process {pid} force killed")
    except psutil.NoSuchProcess:
        pass
    except psutil.AccessDenied as e:
        logger.warning(f"Access denied killing worker process {pid}: {e}")
    except psutil.TimeoutExpired:
        logger.warning(f"Worker process {pid} did not terminate within timeout after kill()")


async def cleanup_worker_process(job_id: str, worker_processes, force: bool = False, timeout: float = 0.5):
    """
    Clean up worker process for a job. Checks if process still exists and terminates it if needed.
    Always removes the job from worker_processes tracking.

    Args:
        job_id: The job ID to clean up
        worker_processes: The worker processes tracking store
        force: If True, immediately force kill without graceful termination attempt.
               Use sparingly (e.g., server shutdown). Default False (graceful shutdown).
        timeout: Time in seconds to wait for graceful termination before force killing.
                 Only used if force is False. Default is 0.5 seconds (worker exits immediately via os._exit).

    Usage:
        - cleanup_worker_process(job_id, wp, force=False) -> Standard cleanup (SUCCESS/ERROR/CANCEL)
        - cleanup_worker_process(job_id, wp, force=True)  -> Emergency cleanup (server shutdown)

    Graceful termination (force=False) sends SIGTERM, waits for timeout, then force kills if needed.
    Worker signal handler uses os._exit(0) for immediate termination (<10ms), so timeout rarely expires.
    """
    # Atomically fetch-and-remove to avoid TOCTOU race conditions
    pid = await worker_processes.pop(job_id, None)
    if pid is None:
        log_level = logger.warning if force else logger.debug
        log_level(f"Job {job_id} not in worker_processes tracking, skipping cleanup")
        return

    try:
        process = psutil.Process(pid)

        # Check if process is still running
        if process.is_running():
            if force:
                # Emergency force kill (e.g., server shutdown)
                _force_kill_process(process, pid, job_id)
            else:
                # Graceful termination (allows cleanup handlers to run)
                logger.info(f"Worker process {pid} for job {job_id} still running, terminating gracefully...")
                process.terminate()

                # Wait up to timeout seconds for graceful termination
                try:
                    process.wait(timeout=timeout)
                    logger.info(f"Worker process {pid} terminated gracefully")
                except psutil.TimeoutExpired:
                    # Force kill if graceful termination fails
                    logger.warning(f"Worker process {pid} did not terminate gracefully, force killing...")
                    _force_kill_process(process, pid, job_id)
        else:
            logger.debug(f"Worker process {pid} for job {job_id} already terminated")

    except psutil.NoSuchProcess:
        logger.debug(f"Worker process {pid} for job {job_id} no longer exists")
    except Exception as e:
        logger.error(f"Error cleaning up worker process {pid} for job {job_id}: {e}")
    finally:
        # Best-effort: ensure tracking is clear, ignore if already removed
        try:
            await worker_processes.delete(job_id)
            logger.debug(f"Removed job {job_id} from worker_processes tracking")
        except KeyError:
            # Already removed (e.g., by concurrent cleanup call)
            pass
