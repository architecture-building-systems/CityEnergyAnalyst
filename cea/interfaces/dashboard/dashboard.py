from flask import Flask

import cea.config
import cea.plots

import yaml
import os


def list_tools():
    """List the tools known to the CEA. The result is grouped by category.
    """
    import cea.scripts
    from itertools import groupby

    tools = sorted(cea.scripts.for_interface('dashboard'), key=lambda t: t.category)
    result = {}
    for category, group in groupby(tools, lambda t: t.category):
        result[category] = [t for t in group]
    return result


def load_plots_data():
    plots_yml = os.path.join(os.path.dirname(cea.plots.__file__), 'plots.yml')
    return yaml.load(open(plots_yml).read())


def main(config):
    config.restricted_to = None  # allow access to the whole config file
    app = Flask(__name__, static_folder='base/static')
    app.config.from_mapping({'DEBUG': True,
                             'SECRET_KEY': 'secret'})

    # provide the list of tools
    @app.context_processor
    def tools_processor():
        return dict(tools=list_tools())

    @app.context_processor
    def dashboards_processor():
        dashboards = cea.plots.read_dashboards(config)
        return dict(dashboards=dashboards)

    @app.template_filter('escapejs')
    def escapejs(text):
        """Escape text for a javascript string (without surrounding quotes)"""
        escapes = {
            '\\': '\\u005C',
            '\'': '\\u0027',
            '"': '\\u0022',
            '>': '\\u003E',
            '<': '\\u003C',
            '&': '\\u0026',
            '=': '\\u003D',
            '-': '\\u002D',
            ';': '\\u003B',
            u'\u2028': '\\u2028',
            u'\u2029': '\\u2029'
        }
        # Escape every ASCII character with a value less than 32.
        escapes.update(('%c' % z, '\\u%04X' % z) for z in xrange(32))

        retval = []
        for char in text:
            if escapes.has_key(char):
                retval.append(escapes[char])
            else:
                retval.append(char)
        return "".join(retval)

    @app.template_filter('join_path')
    def join_path(path1, path2):
        return os.path.join(path1, path2)

    @app.template_filter('join_paths')
    def join_paths(path_list, loop_index):
        if path_list and path_list[0].endswith(':'):
            # os.path.join will not add a separator to "C:", see here:
            path_list[0] = path_list[0] + os.path.sep
        result = os.path.join(*path_list[:loop_index])
        print('join_paths(%(path_list)s, %(loop_index)s) --> %(result)s' % locals())
        return result

    import base.routes
    import tools.routes
    import plots.routes
    import inputs.routes
    import project.routes
    import webbrowser
    app.register_blueprint(base.routes.blueprint)
    app.register_blueprint(tools.routes.blueprint)
    app.register_blueprint(plots.routes.blueprint)
    app.register_blueprint(inputs.routes.blueprint)
    app.register_blueprint(project.routes.blueprint)

    # keep a copy of the configuration we're using
    app.cea_config = config
    app.plots_data = load_plots_data()

    # keep a list of running scripts - (Process, Connection)
    # the protocol for the Connection messages is tuples ('stdout'|'stderr', str)
    app.workers = {}  # script-name -> (Process, Connection)

    webbrowser.open("http://localhost:5050/")
    app.run(host='localhost', port=5050, threaded=False)



if __name__ == '__main__':
    main(cea.config.Configuration())