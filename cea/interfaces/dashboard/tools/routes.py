from flask import Blueprint, render_template, current_app, jsonify, request
import cea.interfaces.dashboard.tools.worker as worker

blueprint = Blueprint(
    'tools_blueprint',
    __name__,
    url_prefix='/tools',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/index')
def index():
    return render_template('index.html')


@blueprint.route('/start/<script>', methods=['POST'])
def route_start(script):
    """Start a subprocess for the script. Store output in a queue - reference the queue by id. Return queue id.
    (this can be the process id)"""
    kwargs = {}
    for parameter in parameters_for_script(script, current_app.cea_config):
        print('%s: %s' % (parameter.name, request.form.get(parameter.name)))
        kwargs[parameter.name] = parameter.decode(request.form.get(parameter.name))
    current_app.workers[script] = worker.main(script, **kwargs)
    return jsonify(script)


@blueprint.route('/echo', methods=['POST'])
def route_echo():
    """echo back the parameters"""
    data = request.form
    print(data)
    return jsonify(data)


@blueprint.route('/kill/<script>')
def route_kill(script):
    if not script in current_app.workers:
        return jsonify(False)
    worker, connection = current_app.workers[script]
    worker.terminate()
    return jsonify(True)


@blueprint.route('/exitcode/<script>')
def route_exitcode(script):
    if not script in current_app.workers:
        return jsonify(None)
    worker, connection = current_app.workers[script]
    return jsonify(worker.exitcode)


@blueprint.route('/is-alive/<script>')
def is_alive(script):
    if not script in current_app.workers:
        return jsonify(False)
    worker, connection = current_app.workers[script]
    return jsonify(worker.is_alive())

@blueprint.route('/read/<script>')
def read(script):
    """Reads the next message as a json dict {stream: stdout|stdin, message: str}"""
    if not script in current_app.workers:
        return jsonify(None)
    worker, connection = current_app.workers[script]
    try:
        stream, message = connection.recv()
    except EOFError:
        return jsonify(None)
    return jsonify(dict(stream=stream, message=message))


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