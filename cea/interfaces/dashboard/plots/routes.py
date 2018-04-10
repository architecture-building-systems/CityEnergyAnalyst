from flask import Blueprint, render_template, current_app, jsonify, request

blueprint = Blueprint(
    'plots_blueprint',
    __name__,
    url_prefix='/plots',
    template_folder='templates',
    static_folder='static',
)

@blueprint.route('/index')
def index():
    return render_template('dashboard.html')

@blueprint.route('/<plot>')
def route_plot(plot):
    # load plot (check for data??)
    pass