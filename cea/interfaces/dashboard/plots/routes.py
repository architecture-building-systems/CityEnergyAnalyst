from flask import Blueprint, render_template, current_app, abort, make_response

import cea.inputlocator
import cea.plots
import cea.plots.categories

import re
import os

blueprint = Blueprint(
    'plots_blueprint',
    __name__,
    url_prefix='/plots',
    template_folder='templates',
    static_folder='static',
)


def script_suggestions(locator_names):
    """Return a list of CeaScript objects that produce the output for each locator name"""
    import cea.scripts
    schemas = cea.scripts.schemas()
    script_names = []
    for name in locator_names:
        script_names.extend(schemas[name]['created_by'])
    return [cea.scripts.by_name(n) for n in sorted(set(script_names))]


def load_plot(dashboard, plot_index):
    """Load a plot from the dashboard_yml"""
    cea_config = current_app.cea_config
    dashboards = cea.plots.read_dashboards(cea_config, current_app.plot_cache)
    dashboard = dashboards[dashboard]
    plot = dashboard.plots[plot_index]
    return plot


@blueprint.route('/div/<int:dashboard_index>/<int:plot_index>')
def route_div(dashboard_index, plot_index):
    """Return the plot as a div to be used in an AJAX call"""
    try:
        plot = load_plot(dashboard_index, plot_index)
    except Exception as ex:
        return abort(500, ex)
    if not plot.missing_input_files():
        plot_div = plot.plot_div()
        # BUGFIX for (#2102 - Can't add the same plot twice in a dashboard)
        # update id of div to include dashboard_index and plot_index
        if plot_div.startswith("<div id="):
            div_id = re.match('<div id="([0-9a-f-]+)"', plot_div).group(1)
            plot_div = plot_div.replace(div_id, "{div_id}-{dashboard_index}-{plot_index}".format(
                div_id=div_id, dashboard_index=dashboard_index, plot_index=plot_index))
        return make_response(plot_div, 200)
    else:
        return render_template('missing_input_files.html',
                               missing_input_files=[lm(*args) for lm, args in plot.missing_input_files()],
                               script_suggestions=script_suggestions(lm.__name__ for lm, _ in plot.missing_input_files())), 404


@blueprint.route('/plot/<int:dashboard_index>/<int:plot_index>')
def route_plot(dashboard_index, plot_index):
    try:
        plot = load_plot(dashboard_index, plot_index)
        plot_title = plot.title
        if 'scenario-name' in plot.parameters:
            plot_title += ' - {}'.format(plot.parameters['scenario-name'])
    except Exception as ex:
        return abort(500, ex)

    if not plot.missing_input_files():
        plot_div = plot.plot_div()
    else:
        return render_template('missing_input_files.html',
                               missing_input_files=[lm(*args) for lm, args in plot.missing_input_files()],
                               script_suggestions=script_suggestions(
                                   lm.__name__ for lm, _ in plot.missing_input_files())), 404

    return render_template('plot.html', plot_div=plot_div, plot_title=plot_title)
