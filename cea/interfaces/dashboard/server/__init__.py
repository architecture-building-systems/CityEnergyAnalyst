from fastapi import APIRouter

import cea
import cea.interfaces.dashboard.server.jobs as jobs
import cea.interfaces.dashboard.server.streams as streams
from cea.interfaces.dashboard.dependencies import get_worker_processes, get_streams, CEAServerLimits
from cea.interfaces.dashboard.lib.database.session import get_session_context
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

router = APIRouter()

router.include_router(jobs.router, prefix='/jobs')
router.include_router(streams.router, prefix='/streams')

logger = getCEAServerLogger("cea-server-shutdown")


async def shutdown_worker_processes():
    """
    When shutting down the server, kill all running jobs and attempt to notify users.

    During SIGTERM shutdown, Socket.IO connections are typically already closed by the time
    this handler runs. Jobs are always marked as KILLED in the database, and Socket.IO
    notifications are attempted on a best-effort basis (will likely fail since connections
    are closed). Users will see the KILLED status when they reconnect. See issue #2408.
    """
    worker_processes = await get_worker_processes()
    streams = await get_streams()
    job_ids = list(await worker_processes.keys())

    if not job_ids:
        logger.info("No running worker processes to clean up")
        return

    logger.info(f"Killing {len(job_ids)} running job(s) due to server shutdown")
    logger.info("Note: Socket.IO notifications are best-effort and may not be delivered during shutdown")

    async with get_session_context() as session:
        for job_id in job_ids:
            try:
                # FIXME: Should it kill or try to gracefully stop?
                logger.info(f"Killing job {job_id} (DB update + best-effort notification)")
                await jobs.kill_job(session, job_id, worker_processes, streams)
                logger.info(f"Job {job_id} killed successfully")
            except Exception as e:
                logger.error(f"Error killing job {job_id} during shutdown: {e}")
                # Continue with other jobs even if one fails


@router.get("/alive")
async def get_health_check():
    return {'success': True}


@router.get("/version")
async def get_version():
    return {'version': cea.__version__}


@router.get("/settings")
async def get_settings(limits: CEAServerLimits):
    return {'limits': limits}
