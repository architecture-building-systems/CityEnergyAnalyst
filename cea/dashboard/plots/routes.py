from flask import Blueprint, render_template, current_app, request, abort, make_response, redirect, url_for

import cea.inputlocator
from cea.config import MultiChoiceParameter
import cea.plots
import cea.plots.categories

import importlib
import plotly.offline
import json
import yaml


blueprint = Blueprint(
    'plots_blueprint',
    __name__,
    url_prefix='/plots',
    template_folder='templates',
    static_folder='static',
)

categories = {c.name: {'label': c.label, 'plots': [{'id': p.id(), 'name': p.name} for p in c.plots]}
              for c in cea.plots.categories.list_categories()}


@blueprint.route('/index')
def index():
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=0))


@blueprint.route('/dashboard/<int:dashboard_index>')
def route_dashboard(dashboard_index):
    """
    Route the i-th dashboard from the dashboard configuratino file.
    In case of an out-of-bounds error, show the 0-th dashboard (that is guaranteed to exist)
    """
    cea_config = current_app.cea_config
    dashboards = cea.plots.read_dashboards(cea_config)
    dashboard = dashboards[dashboard_index]
    return render_template('dashboard.html', dashboard_index=dashboard_index, dashboard=dashboard, categories=categories)


@blueprint.route('/dashboard/new')
def route_new_dashboard():
    """
    Append a dashboard to the list of dashboards and open it for editing.
    """
    cea_config = current_app.cea_config
    dashboard_index = cea.plots.new_dashboard(cea_config)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/rename/<int:dashboard_index>', methods=['POST'])
def route_rename_dashboard(dashboard_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config)
    dashboard = dashboards[dashboard_index]
    dashboard.name = request.form.get('new-name', dashboard.name)
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/add-plot/<int:dashboard_index>', methods=['POST'])
def route_add_plot_to_dashboard(dashboard_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config)
    dashboard = dashboards[dashboard_index]
    category = request.form.get('category', next(iter(categories)))
    plot_id = request.form.get('plot-id', next(iter(categories[category]['plots']))['id'])
    dashboard.add_plot(category, plot_id)
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/remove-plot/<int:dashboard_index>/<int:plot_index>')
def route_remove_plot_from_dashboard(dashboard_index, plot_index):
    """Remove a plot from a dashboard by index."""
    dashboards = cea.plots.read_dashboards(current_app.cea_config)
    dashboard = dashboards[dashboard_index]
    dashboard.remove_plot(plot_index)
    if len(dashboard.plots) == 0:
        cea.plots.delete_dashboard(current_app.cea_config, dashboard_index)
        return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=0))
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))

@blueprint.route('/dashboard/move_plot_up/<int:dashboard_index>/<int:plot_index>')
def route_move_plot_up(dashboard_index, plot_index):
    """Move a plot up in the dashboard"""
    if plot_index > 0:
        dashboards = cea.plots.read_dashboards(current_app.cea_config)
        dashboard = dashboards[dashboard_index]
        if plot_index < len(dashboard.plots):
            swap(dashboard.plots, plot_index - 1, plot_index)
            cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


def swap(lst, i, j):
    """Swap positions of elements in a list as given by their indexes i and j"""
    lst[i], lst[j] = lst[j], lst[i]

@blueprint.route('/dashboard/move_plot_down/<int:dashboard_index>/<int:plot_index>')
def route_move_plot_down(dashboard_index, plot_index):
    """Move a plot down in the dashboard"""
    if plot_index >= 0:
        dashboards = cea.plots.read_dashboards(current_app.cea_config)
        dashboard = dashboards[dashboard_index]
        if plot_index < (len(dashboard.plots) - 1):
            swap(dashboard.plots, plot_index, plot_index + 1)
            cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/plot-parameters/<int:dashboard_index>/<int:plot_index>', methods=['GET'])
def route_get_plot_parameters(dashboard_index, plot_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config)
    dashboard = dashboards[dashboard_index]
    plot = dashboard.plots[plot_index]
    parameters = []
    for pname, fqname in plot.expected_parameters.items():
        parameter = current_app.cea_config.get_parameter(fqname)
        if pname in plot.parameters:
            parameter.set(plot.parameters[pname])
        parameters.append(parameter)
    return render_template('parameters.html', parameters=parameters, weather_dict={})


@blueprint.route('/dashboard/plot-parameters/<int:dashboard_index>/<int:plot_index>', methods=['POST'])
def route_post_plot_parameters(dashboard_index, plot_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config)
    dashboard = dashboards[dashboard_index]
    plot = dashboard.plots[plot_index]
    parameters = []
    for pname, fqname in plot.expected_parameters.items():
        parameter = current_app.cea_config.get_parameter(fqname)
        if isinstance(parameter, MultiChoiceParameter):
            plot.parameters[pname] = parameter.decode(','.join(request.form.getlist(pname)))
        else:
            plot.parameters[pname] = parameter.decode(request.form[pname])
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))



@blueprint.route('/category/<category>')
def route_category(category):
    """FIXME: this will be removed soon..."""
    if not cea.plots.categories.is_valid_category(category):
        return abort(404)

    cea_config = current_app.cea_config
    locator = cea.inputlocator.InputLocator(scenario=cea_config.scenario)
    buildings = cea_config.plots.buildings

    category = cea.plots.categories.load_category(category)
    plots = [plot_class(cea_config, locator, parameters={'buildings': buildings}) for plot_class in category.plots]
    return render_template('category.html', category=category, plots=plots)


@blueprint.route('/div/<int:dashboard_index>/<int:plot_index>')
def route_div(dashboard_index, plot_index):
    """Return the plot as a div to be used in an AJAX call"""
    try:
        plot = load_plot(dashboard_index, plot_index)
    except Exception as ex:
        return abort(500, ex)
    return make_response(plot.plot_div(), 200)


def load_plot(dashboard_index, plot_index):
    """Load a plot from the dashboard_yml"""
    cea_config = current_app.cea_config
    dashboards = cea.plots.read_dashboards(cea_config)
    dashboard_index = dashboards[dashboard_index]
    plot = dashboard_index.plots[plot_index]
    return plot


@blueprint.route('/plot/<int:dashboard_index>/<int:plot_index>')
def route_plot(dashboard_index, plot_index):
    try:
        plot = load_plot(dashboard_index, plot_index)
    except Exception as ex:
        return abort(500, ex)

    return render_template('plot.html', dashboard_index=dashboard_index, plot_index=plot_index, plot=plot)