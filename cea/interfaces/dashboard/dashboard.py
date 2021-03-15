from flask import Flask
from flask_socketio import SocketIO

import cea.config
import cea.plots
import cea.plots.cache

socketio = None


def main(config):
    config.restricted_to = None  # allow access to the whole config file
    plot_cache = cea.plots.cache.MemoryPlotCache(config.project)
    app = Flask(__name__, static_folder='base/static', )
    app.config.from_mapping({'SECRET_KEY': 'secret'})

    global socketio
    socketio = SocketIO(app)

    from cea.interfaces.dashboard.plots.routes import blueprint as plots_blueprint
    from cea.interfaces.dashboard.server import blueprint as server_blueprint
    from cea.interfaces.dashboard.api import blueprint as api_blueprint

    app.register_blueprint(plots_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(server_blueprint)

    # keep a copy of the configuration we're using
    app.cea_config = config
    app.plot_cache = plot_cache
    app.socketio = socketio

    print("start socketio.run")
    socketio.run(app, host=config.server.host, port=config.server.port)
    print("done socketio.run")


if __name__ == '__main__':
    main(cea.config.Configuration())
