from flask import Blueprint, render_template, current_app, jsonify, request, abort
import cea.plots
import os
import yaml
import importlib
import plotly.offline

blueprint = Blueprint(
    'plots_blueprint',
    __name__,
    url_prefix='/plots',
    template_folder='templates',
    static_folder='static',
)


def load_plots_data():
    plots_yml = os.path.join(os.path.dirname(cea.plots.__file__), 'plots.yml')
    return yaml.load(open(plots_yml).read())


plots_data = load_plots_data()


@blueprint.route('/index')
def index():
    return render_template('dashboard.html')

@blueprint.route('/<plot>')
def route_plot(plot):
    if not plot in plots_data:
        return abort(404)

    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)

    module_name, class_name = os.path.splitext(plots_data[plot]['preprocessor'])
    class_name = class_name[1:]
    module = importlib.import_module(module_name)
    preprocessor = getattr(module, class_name)(locator, buildings=['B01'])
    plot_function = getattr(preprocessor, plots_data[plot]['plot-function'])
    fig = plot_function()
    fig['layout']['autosize'] = True
    plot_div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False)
    return render_template('plot.html', plot_div=plot_div, plot=plot)