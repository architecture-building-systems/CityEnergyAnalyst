import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


def configure_app(config):
    global app

    origins = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:5050",
    ]

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
    _app = configure_app(config)
    try:
        uvicorn.run(_app, host="127.0.0.1", port=5050)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    import cea.config
    main(cea.config.Configuration())
