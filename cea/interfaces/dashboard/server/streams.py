"""
streams: maintain a list of streams containing ``cea-worker`` output for jobs.

FIXME: when does this data get cleared?
"""
from collections import defaultdict

from fastapi import APIRouter, Request

from cea.interfaces.dashboard.server.socketio import sio

router = APIRouter()

# map jobid to a list of messages
streams = defaultdict(list)


@router.get("/read/{job_id}")
async def read_stream(job_id: str):
    try:
        return ''.join(streams[job_id])
    except KeyError:
        return ''


@router.put("/write/{job_id}")
async def write_stream(job_id: str, request: Request):
    body = await request.body()
    message = body.decode("utf-8")

    streams[job_id].append(message)

    # emit the message using socket.io
    await sio.emit('cea-worker-message', {"message": message, "jobid": job_id})
