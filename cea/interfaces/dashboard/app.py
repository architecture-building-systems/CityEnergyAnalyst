from contextlib import asynccontextmanager
import os
import signal

from fastapi import FastAPI, Depends, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import cea.interfaces.dashboard.api as api
import cea.interfaces.dashboard.plots.routes as plots
import cea.interfaces.dashboard.server as server
from cea.interfaces.dashboard.lib.database.models import create_db_and_tables
from cea.interfaces.dashboard.lib.database.session import close_db_connection
from cea.interfaces.dashboard.lib.cache.provider import cleanup_cache_connections, get_cache, init_cache
from cea.interfaces.dashboard.lib.cors import CORSConfig
from cea.interfaces.dashboard.lib.logs import logger, getCEAServerLogger
from cea.interfaces.dashboard.lib.socketio import socket_app
from cea.interfaces.dashboard.dependencies import require_authenticated
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

    await init_cache()

    # With multiple uvicorn workers, each worker process runs this lifespan
    # independently, so DB migrations and download cleanup would otherwise run
    # once per worker concurrently (racy SQLite writes, duplicate cleanup
    # queries). Redis is required whenever workers > 1 (see
    # Settings.validate_multi_worker_mode), so an atomic add() doubles as a
    # cheap leader election: only the worker that wins it runs startup-only
    # work. In single-worker/local mode the cache is process-local, so this
    # worker always wins and behaviour is unchanged.
    try:
        is_startup_leader = await get_cache().add("dashboard:startup-lock", True, ttl=60)
    except ValueError:
        # Key already exists: another worker holds the lock and is running startup tasks.
        is_startup_leader = False
    except Exception as e:
        logger.warning(f"Startup lock unavailable ({e}), running startup tasks unconditionally")
        is_startup_leader = True

    if is_startup_leader:
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
    else:
        logger.debug("Another worker is handling startup DB init/cleanup; skipping")

    yield

    logger.info("Shutting down server...")
    # Shutdown all worker processes on exit
    await server.shutdown_worker_processes()
    # Close database connections
    await close_db_connection()
    # Close Redis connections if they exist
    await cleanup_cache_connections()


app = FastAPI(lifespan=lifespan, dependencies=[Depends(require_authenticated)])
socket_app.other_asgi_app = app

# Setup CORS
cors_origin = get_settings().cors_origin

# Parse comma-separated origins
if cors_origin == "*":
    origins = ["*"]
    # Disable credentials with wildcard origin for security
    allow_credentials = False
else:
    origins = [o.strip() for o in cors_origin.split(",")]
    allow_credentials = True

# CORS configuration - centralised
cors_config = CORSConfig(
    origins=origins,
    allow_credentials=allow_credentials,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    headers=["Content-Type", "Authorization", "X-Requested-With", "Accept",
             "X-CEA-Project", "X-CEA-Scenario-Name", "X-CEA-Child-Scenario"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.origins,
    allow_credentials=cors_config.allow_credentials,
    allow_methods=cors_config.methods,
    allow_headers=cors_config.headers,
)

# Mount socketio app
app.mount("/socket.io", socket_app, "socketio")

# Import other routers
app.include_router(api.router, prefix='/api')
app.include_router(plots.router, prefix='/plots')
app.include_router(server.router, prefix='/server')

# Mount the public demo sub-app when demo scenarios are configured.
# The sub-app is a standalone FastAPI instance and does NOT inherit the
# require_authenticated dependency above — the anonymous boundary is structural.
if get_settings().public_demo_scenarios:
    from cea.interfaces.dashboard.api.demo import app as demo_app
    app.mount("/api/demo", demo_app)
    logger.info(
        "Public demo sub-app mounted at /api/demo (%d scenario(s))",
        len(get_settings().public_demo_scenarios),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Found validation errors: {exc.errors()}")
    if request:
        logger.error(f"request: {request}")

    # Get CORS headers matching CORSMiddleware configuration
    request_origin = request.headers.get("Origin")
    cors_headers = cors_config.get_response_headers(request_origin)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers=cors_headers
    )

@app.exception_handler(Exception)
async def uncaught_exception_handler(request: Request, exc: Exception):
    logger.error(f"Uncaught exception [{type(exc).__name__}] in \"{request.method} {request.url.path}\":\n"
                 f"{exc}")

    # Get CORS headers matching CORSMiddleware configuration
    request_origin = request.headers.get("Origin")
    cors_headers = cors_config.get_response_headers(request_origin)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Uncaught exception: {exc}"},
        headers=cors_headers
    )
