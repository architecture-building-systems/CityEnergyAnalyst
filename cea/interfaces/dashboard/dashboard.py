from flask import Flask
from importlib import import_module

import cea.config

def register_blueprints(app):
    for module_name in ('forms', 'ui', 'home', 'tables', 'data', 'additional', 'base'):
        module = import_module('cea.interfaces.dashboard.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def main(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_mapping({'DEBUG': True,
                             'SECRET_KEY': 'secret'})
    # register_blueprints(app)

    import cea.interfaces.dashboard.base.routes
    import cea.interfaces.dashboard.home.routes
    app.register_blueprint(cea.interfaces.dashboard.base.routes.blueprint)
    app.register_blueprint(cea.interfaces.dashboard.home.routes.blueprint)

    app.run(host='0.0.0.0', port=config.dashboard.port, threaded=False)


if __name__ == '__main__':
    main(cea.config.Configuration())