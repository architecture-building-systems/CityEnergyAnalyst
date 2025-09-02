from fastapi import APIRouter

import cea
import cea.interfaces.dashboard.server.jobs as jobs
import cea.interfaces.dashboard.server.streams as streams
from cea.interfaces.dashboard.dependencies import get_worker_processes, CEAServerSettings, CEAUser
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
async def get_settings(user: CEAUser):
    # TODO: Shift limits to user properties
    limits = LimitSettings()

    # Pro users get 3x the limits and 5 scenarios
    if user.get("pro_user", False):
        limits.num_projects = limits.num_projects * 3 if limits.num_projects else None
        limits.num_scenarios = 5
        limits.num_buildings = limits.num_buildings * 3 if limits.num_buildings else None

    return {'limits': limits}
