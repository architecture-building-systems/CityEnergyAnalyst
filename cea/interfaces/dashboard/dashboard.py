from flask import Flask
from importlib import import_module

import cea.config


def register_blueprints(app):
    for module_name in ('forms', 'ui', 'home', 'tables', 'data', 'additional', 'base'):
        module = import_module('cea.interfaces.dashboard.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def list_tools():
    """List the tools known to the CEA. The result is grouped by category.
    FIXME: refactor the way the ArcGIS interface and the CLI interface configure their toolboxes and use that
           instead of this hack.
    """
    from cea.interfaces.arcgis.CityEnergyAnalyst import Toolbox
    from itertools import groupby

    result = {}
    tools = sorted([t() for t in Toolbox().tools], key=lambda t: t.category)
    for category, group in groupby(tools, lambda t: t.category):
        result[category] = [t for t in group]
    return result



def main(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_mapping({'DEBUG': True,
                             'SECRET_KEY': 'secret'})

    # provide the list of tools
    @app.context_processor
    def tools_processor():
        return dict(tools=list_tools())

    import cea.interfaces.dashboard.base.routes
    import cea.interfaces.dashboard.home.routes
    import cea.interfaces.dashboard.tools.routes

    app.register_blueprint(cea.interfaces.dashboard.base.routes.blueprint)
    app.register_blueprint(cea.interfaces.dashboard.home.routes.blueprint)
    app.register_blueprint(cea.interfaces.dashboard.tools.routes.blueprint)

    app.cea_config = config

    app.run(host='0.0.0.0', port=config.dashboard.port, threaded=False)


if __name__ == '__main__':
    main(cea.config.Configuration())