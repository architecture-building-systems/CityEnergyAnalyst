import sys

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing_extensions import Annotated

import cea.config
from cea.plots.cache import MemoryPlotCache

_config = cea.config.Configuration()
_mem_cache = MemoryPlotCache(_config.project)


def get_cea_config():
    return _config


def get_plot_cache():
    return _mem_cache


CEAConfig = Annotated[dict, Depends(get_cea_config)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]


def create_app():
    origins = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:5050",
    ]

    app = FastAPI()

    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount socketio app
    from cea.interfaces.dashboard.server.socketio import socket_app
    app.mount("/socket.io", socket_app, "socketio")

    # Import other routers
    import cea.interfaces.dashboard.api as api
    import cea.interfaces.dashboard.plots.routes as plots
    import cea.interfaces.dashboard.server as server

    app.include_router(api.router, prefix='/api')
    app.include_router(plots.router, prefix='/plots')
    app.include_router(server.router, prefix='/server')

    return app


def main(config):
    app = create_app()
    try:
        uvicorn.run(app, host="127.0.0.1", port=5050)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main(cea.config.Configuration())
