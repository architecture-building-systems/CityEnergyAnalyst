from flask import Blueprint, render_template, current_app, jsonify

blueprint = Blueprint(
    'tools_blueprint',
    __name__,
    url_prefix='/tools',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/index')
def index():
    return render_template('index.html')

@blueprint.route('/run/<script>')
def route_run(script):
    """Start a subprocess for the script. Store output in a queue - reference the queue by id. Return queue id.
    (this can be the process id)"""
    return jsonify(proc_id)

@blueprint.route('/<script>')
def route_tool(script):
    config = current_app.cea_config
    return render_template('tool.html', script=script, parameters=parameters_for_script(script, config))


def parameters_for_script(script, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    import cea.interfaces.cli.cli
    cli_config = cea.interfaces.cli.cli.get_cli_config()
    parameters = [p for s, p in config.matching_parameters(cli_config.get('config', script).split())]
    return parameters