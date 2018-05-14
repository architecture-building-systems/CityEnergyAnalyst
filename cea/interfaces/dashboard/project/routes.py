from flask import Blueprint, render_template, current_app, request, redirect, jsonify, url_for
import cea.inputlocator

blueprint = Blueprint(
    'project_blueprint',
    __name__,
    url_prefix='/project',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/show')
def route_show():
    """Show the project inputs form."""
    cea_config = current_app.cea_config
    locator = cea.inputlocator.InputLocator(cea_config.scenario)
    regions = list(cea_config.sections['general'].parameters['region']._choices)
    selected_region = cea_config.region
    scenario = cea_config.scenario
    weather = cea_config.weather
    multiprocessing = cea_config.multiprocessing
    weather_names = locator.get_weather_names()
    return render_template('project.html', regions=regions, selected_region=selected_region, scenario=scenario,
                           weather=weather, weather_names=weather_names, multiprocessing=multiprocessing)


@blueprint.route('/save', methods=['POST'])
def route_save():
    """Save the new project data to the configuration file"""
    cea_config = current_app.cea_config
    cea_config.scenario = request.form['scenario']
    cea_config.region = request.form['region']
    cea_config.weather = request.form['weather-path']
    cea_config.multiprocessing = 'multiprocessing' in request.form
    cea_config.save()
    return redirect(url_for('project_blueprint.route_show'))


@blueprint.route('/weather/<weather_name>')
def route_weather_path(weather_name):
    cea_config = current_app.cea_config
    locator = cea.inputlocator.InputLocator(cea_config.scenario)
    weather_path = locator.get_weather(weather_name)
    return jsonify(weather_path)
