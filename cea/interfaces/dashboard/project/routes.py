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
    return render_template('project.html')