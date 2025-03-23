"""
streams: maintain a list of streams containing ``cea-worker`` output for jobs.

FIXME: when does this data get cleared?
"""
from collections import defaultdict

from fastapi import APIRouter, Request

from cea.interfaces.dashboard.lib.database.models import JobInfo
from cea.interfaces.dashboard.lib.database.session import SessionDep
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.server.socketio import sio

logger = getCEAServerLogger("cea-server-streams")

router = APIRouter()

# map jobid to a list of messages
streams = defaultdict(list)


@router.get("/read/{job_id}")
async def read_stream(session: SessionDep, job_id: str):
    stdout = streams.get(job_id)

    if stdout is None:
        job = session.get(JobInfo, job_id)
        if job is None:
            print(f"read_stream: job {job_id} not found")
            return ""  # Return empty string for non-existent jobs
        stdout = job.stdout
    else:
        stdout = ''.join(stdout)

    return stdout


@router.put("/write/{job_id}")
async def write_stream(session: SessionDep, job_id: str, request: Request):
    body = await request.body()
    message = body.decode("utf-8")

    streams[job_id].append(message)

    # TODO: Get user id from request from worker
    job = session.get(JobInfo, job_id)
    if job is None:
        return

    user_id = job.created_by
    # emit the message using socket.io
    await sio.emit('cea-worker-message', {"message": message, "jobid": job_id}, room=f"user-{user_id}")
