from flask import Blueprint, render_template, redirect, request, url_for, jsonify, current_app

import cea.plots
import cea.glossary


blueprint = Blueprint(
    'base_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/get-tools')
def route_get_tools():
    import cea.scripts
    from itertools import groupby

    tools = sorted(cea.scripts.for_interface('dashboard'), key=lambda t: t.category)
    result = {}
    for category, group in groupby(tools, lambda t: t.category):
        result[category] = [{t.name: {'label': t.label, 'description': t.description}} for t in group]

    return jsonify(result)


@blueprint.route('get-tools/<script_name>')
def route_get_tools_parameters(script_name):
    config = current_app.cea_config
    script = cea.scripts.by_name(script_name)

    parameters = []
    categories = {}
    for _, parameter in config.matching_parameters(script.parameters):
        if parameter.category:
            if parameter.category not in categories:
                categories[parameter.category] = []
            categories[parameter.category].append(deconstruct_parameters(parameter))
        else:
            parameters.append(deconstruct_parameters(parameter))

    out = {
        'label': script.label,
        'category': script.category,
        'parameters': parameters,
        'categorical_parameters': categories,
    }
    return jsonify(out)


def deconstruct_parameters(p):
    params = {'name': p.name, 'type': p.typename, 'value': p.get(), 'help': p.help}
    try:
        params['choices'] = p._choices
    except AttributeError:
        pass
    if p.typename == 'WeatherPathParameter':
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)
        params['choices'] = {wn: locator.get_weather(wn) for wn in locator.get_weather_names()}
    return params


@blueprint.route('/')
def route_default():
    return redirect(url_for('landing_blueprint.index'))


@blueprint.route('/glossary_search')
def route_glossary_search():
    query = request.args.get('query')
    glossary = cea.glossary.read_glossary_dicts()
    return jsonify(filter(lambda row: query.lower() in row['VARIABLE'].lower(), glossary))


@blueprint.route('/fixed_<template>')
def route_fixed_template(template):
    return render_template('fixed/fixed_{}.html'.format(template))


@blueprint.route('/page_<error>')
def route_errors(error):
    return render_template('errors/page_{}.html'.format(error))

## Login & Registration



@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

## Errors



@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404


@blueprint.app_errorhandler(500)
def internal_error(error):
    import traceback
    error_trace = traceback.format_exc()
    return error_trace, 500
