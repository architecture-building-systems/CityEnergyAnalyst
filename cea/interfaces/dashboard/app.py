from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from cea.interfaces.dashboard.lib.database.session import close_db_connection
from cea.interfaces.dashboard.lib.database.models import create_db_and_tables
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.lib.socketio import socket_app

import cea.interfaces.dashboard.api as api
import cea.interfaces.dashboard.plots.routes as plots
import cea.interfaces.dashboard.server as server
from cea.interfaces.dashboard.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield
    logger.info("Shutting down server...")
    # Shutdown all worker processes on exit
    await server.shutdown_worker_processes()
    # Close database connections
    close_db_connection()


app = FastAPI(lifespan=lifespan)

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
    logger.error("Found validation errors:", exc.errors())
    logger.error("url", request.url)

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
