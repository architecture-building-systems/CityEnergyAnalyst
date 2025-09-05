from contextlib import asynccontextmanager

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
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.lib.socketio import socket_app
from cea.interfaces.dashboard.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        # FIXME: sqlite not working with async adapter
        await create_db_and_tables()
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

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
