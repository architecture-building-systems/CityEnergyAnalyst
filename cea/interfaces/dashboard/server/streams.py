"""
streams: maintain a list of streams containing ``cea-worker`` output for jobs.

FIXME: when does this data get cleared?
"""
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import undefer_group

from cea.interfaces.dashboard.dependencies import CEAStreams, CEAUserID
from cea.interfaces.dashboard.lib.database.models import JobInfo
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.lib.socketio import sio

logger = getCEAServerLogger("cea-server-streams")

router = APIRouter()


@router.get("/read/{job_id}")
async def read_stream(session: SessionDep, streams: CEAStreams, job_id: str, user_id: CEAUserID):
    job = await session.get(JobInfo, job_id, options=[undefer_group('logs')])
    if job is None:
        logger.info(f"read_stream: job {job_id} not found")
        return ""  # Return empty string for non-existent jobs

    # Authorization check: only the job's creator can read its output
    if job.created_by != user_id:
        logger.warning(f"User {user_id} attempted to read stream for job {job_id} owned by {job.created_by}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to read this job's output"
        )

    stdout = await streams.get(job_id)
    if stdout is None:
        stdout = job.stdout
    else:
        stdout = ''.join(stdout)

    return stdout


@router.put("/write/{job_id}")
async def write_stream(session: SessionDep, streams: CEAStreams, job_id: str, user_id: CEAUserID, request: Request):
    job = await session.get(JobInfo, job_id)
    if job is None:
        return

    # Authorization check: only the job's own worker (or its creator) can write output
    if job.created_by != user_id:
        logger.warning(f"User {user_id} attempted to write stream for job {job_id} owned by {job.created_by}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to update this job's output"
        )

    body = await request.body()
    message = body.decode("utf-8")

    stream = await streams.get(job_id, [])
    stream.append(message)
    await streams.set(job_id, stream)

    # emit the message using socket.io
    await sio.emit('cea-worker-message', {"message": message, "jobid": job_id}, room=f"user-{job.created_by}")
