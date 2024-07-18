from fastapi import APIRouter

import cea.interfaces.dashboard.server.jobs as jobs
import cea.interfaces.dashboard.server.streams as streams

router = APIRouter()

router.include_router(jobs.router, prefix='/jobs')
router.include_router(streams.router, prefix='/streams')


def shutdown_worker_processes():
    """When shutting down the flask server, make sure any subprocesses are also terminated. See issue #2408."""
    for jobid in jobs.worker_processes.keys():
        jobs.kill_job(jobid)


@router.get("/alive")
async def get_health_check():
    return {'success': True}
