from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cea.interfaces.dashboard.server.socketio import socket_app

import cea.interfaces.dashboard.api as api
import cea.interfaces.dashboard.plots.routes as plots
import cea.interfaces.dashboard.server as server


app = FastAPI()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
