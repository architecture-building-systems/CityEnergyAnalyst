from flask import Blueprint, render_template, current_app, jsonify, request, abort, make_response

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


@blueprint.route('/category/<category>')
def route_category(category):
    if not category in set([plot['category'] for plot in current_app.plots_data.values()]):
        return abort(404)

    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    plots_data = current_app.plots_data

    plot_divs = []
    for plot in plots_data.keys():
        fig = get_plot_fig(locator, plot)
        plot_divs.append(plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False))
    return render_template('category.html', plot_divs=plot_divs, category=category)


@blueprint.route('/div/<plot>')
def route_div(plot):
    """Return the plot as a div to be used in an AJAX call"""
    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    fig = get_plot_fig(locator, plot)
    div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
    response = make_response(div, 200)
    return response


@blueprint.route('/<plot>')
def route_plot(plot):
    if not plot in current_app.plots_data:
        return abort(404)

    locator = cea.inputlocator.InputLocator(current_app.cea_config.scenario)
    fig = get_plot_fig(locator, plot)
    title = fig['layout']['title']
    del fig['layout']['title']
    plot_div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
    return render_template('plot.html', plot_div=plot_div, plot=plot, title=title)


def get_plot_fig(locator, plot):
    module_name, class_name = os.path.splitext(current_app.plots_data[plot]['preprocessor'])
    class_name = class_name[1:]
    module = importlib.import_module(module_name)
    preprocessor = getattr(module, class_name)(locator, buildings=['B01'])
    plot_function = getattr(preprocessor, current_app.plots_data[plot]['plot-function'])
    fig = plot_function()
    return fig