from flask import Blueprint, render_template, current_app, jsonify, request, abort

import cea.inputlocator
import os

import importlib
import plotly.offline

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
    if not plot in current_app.plots_data:
        return abort(404)

    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)

    module_name, class_name = os.path.splitext(current_app.plots_data[plot]['preprocessor'])
    class_name = class_name[1:]
    module = importlib.import_module(module_name)
    preprocessor = getattr(module, class_name)(locator, buildings=['B01'])
    plot_function = getattr(preprocessor, current_app.plots_data[plot]['plot-function'])
    fig = plot_function()
    fig['layout']['autosize'] = True
    title = fig['layout']['title']
    del fig['layout']['title']
    plot_div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
    return render_template('plot.html', plot_div=plot_div, plot=plot, title=title)