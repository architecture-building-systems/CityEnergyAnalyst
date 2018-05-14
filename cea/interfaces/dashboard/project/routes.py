from flask import Blueprint, render_template, current_app, request, abort, jsonify

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
    regions = list(cea_config.sections['general'].parameters['region']._choices)
    selected_region = cea_config.region
    scenario = cea_config.scenario
    return render_template('project.html', regions=regions, selected_region=selected_region, scenario=scenario)