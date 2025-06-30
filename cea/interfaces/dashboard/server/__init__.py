from fastapi import APIRouter

import cea
import cea.interfaces.dashboard.server.jobs as jobs
import cea.interfaces.dashboard.server.streams as streams
from cea.interfaces.dashboard.dependencies import get_worker_processes, CEAServerSettings
from cea.interfaces.dashboard.settings import LimitSettings

router = APIRouter()

router.include_router(jobs.router, prefix='/jobs')
router.include_router(streams.router, prefix='/streams')


async def shutdown_worker_processes():
    """When shutting down the flask server, make sure any subprocesses are also terminated. See issue #2408."""
    worker_processes = await get_worker_processes()
    for jobid in await worker_processes.keys():
        await jobs.kill_job(jobid, worker_processes)


@router.get("/alive")
async def get_health_check():
    return {'success': True}


@router.get("/version")
async def get_version():
    return {'version': cea.__version__}


@router.get("/settings")
async def get_settings(settings: CEAServerSettings):
    # TODO: Shift limits to user properties
    limits = LimitSettings()
    return {'limits': limits}
