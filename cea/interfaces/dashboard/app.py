from contextlib import asynccontextmanager
import os
import signal

from fastapi import FastAPI, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import cea.interfaces.dashboard.api as api
import cea.interfaces.dashboard.plots.routes as plots
import cea.interfaces.dashboard.server as server
from cea.interfaces.dashboard.lib.database.models import create_db_and_tables
from cea.interfaces.dashboard.lib.database.session import close_db_connection
from cea.interfaces.dashboard.lib.cache.provider import cleanup_cache_connections
from cea.interfaces.dashboard.lib.logs import logger, getCEAServerLogger
from cea.interfaces.dashboard.lib.socketio import socket_app
from cea.interfaces.dashboard.settings import get_settings

zombie_logger = getCEAServerLogger("cea-server-zombie")


def setup_sigchld_handler():
    """
    Setup SIGCHLD handler to automatically reap zombie processes.

    When child processes (cea-worker) exit, they become zombies until the parent
    calls wait(). This handler automatically reaps any zombie children to prevent
    accumulation.

    This is especially important in Docker/Linux where zombies can accumulate if
    workers exit unexpectedly or before the cleanup_worker_process() is called.

    Note: This is Unix-specific and will be skipped on Windows.
    """
    # SIGCHLD only exists on Unix systems
    if not hasattr(signal, 'SIGCHLD'):
        zombie_logger.info("SIGCHLD not available on this platform (Windows), skipping zombie reaping handler")
        return

    def sigchld_handler(signum, frame):
        """Reap all zombie children without blocking"""
        while True:
            try:
                # waitpid with WNOHANG returns immediately if no zombie children
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    # No more zombie children
                    break
                zombie_logger.debug(f"Reaped zombie process {pid} with status {status}")
            except ChildProcessError:
                # No more children to reap
                break
            except Exception as e:
                zombie_logger.error(f"Error in SIGCHLD handler: {e}")
                break

    # Register SIGCHLD handler
    signal.signal(signal.SIGCHLD, sigchld_handler)
    zombie_logger.info("SIGCHLD handler registered for automatic zombie reaping")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Setup zombie process reaping
    setup_sigchld_handler()

    try:
        # FIXME: sqlite not working with async adapter
        await create_db_and_tables()
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

    # Cleanup old and stale downloads on startup
    try:
        from cea.interfaces.dashboard.server.downloads import cleanup_old_downloads, cleanup_stale_downloads
        from cea.interfaces.dashboard.lib.database.session import get_session_context
        async with get_session_context() as session:
            await cleanup_old_downloads(session)
            await cleanup_stale_downloads(session)
    except Exception as e:
        logger.error(f"Failed to cleanup downloads: {e}")

    yield

    logger.info("Shutting down server...")
    # Shutdown all worker processes on exit
    await server.shutdown_worker_processes()
    # Close database connections
    await close_db_connection()
    # Close Redis connections if they exist
    await cleanup_cache_connections()


app = FastAPI(lifespan=lifespan)
socket_app.other_asgi_app = app

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount socketio app
app.mount("/socket.io", socket_app, "socketio")

# Import other routers
app.include_router(api.router, prefix='/api')
app.include_router(plots.router, prefix='/plots')
app.include_router(server.router, prefix='/server')


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Found validation errors: {exc.errors()}")
    if request:
        logger.error(f"request: {request}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": get_settings().cors_origin,
        }
    )

@app.exception_handler(Exception)
async def uncaught_exception_handler(request: Request, exc: Exception):
    logger.error(f"Uncaught exception in \"{request.method} {request.url.path}\":\n"
                 f"{exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Uncaught exception: {exc}"},
        headers={
            "Access-Control-Allow-Origin": get_settings().cors_origin,
        }
    )
