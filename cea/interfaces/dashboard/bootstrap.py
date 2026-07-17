"""One-time dashboard preparation run before web workers are started."""
import asyncio

from cea.interfaces.dashboard.lib.database.models import create_db_and_tables
from cea.interfaces.dashboard.lib.database.session import close_db_connection, get_session_context
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.server.downloads import cleanup_old_downloads, cleanup_stale_downloads


async def initialize_dashboard() -> None:
    """Prepare shared dashboard state before starting one or more web workers.

    This function deliberately runs outside FastAPI's lifespan: Uvicorn invokes
    that lifespan once per worker, while database migration and startup download
    recovery must run once per dashboard launch.
    """
    logger.info("Starting dashboard bootstrap")
    try:
        # FIXME: sqlite not working with async adapter
        await create_db_and_tables()
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

    try:
        async with get_session_context() as session:
            await cleanup_old_downloads(session)
            await cleanup_stale_downloads(session)
    except Exception as e:
        logger.error(f"Failed to cleanup downloads: {e}")
    finally:
        # The launcher may fork worker processes. Dispose the launcher's engine
        # before that happens so workers create and own their own connections.
        await close_db_connection()
        logger.info("Dashboard bootstrap finished")


def main() -> None:
    """Run dashboard preparation as a standalone deployment init job."""
    asyncio.run(initialize_dashboard())


if __name__ == "__main__":
    main()
