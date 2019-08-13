from flask import Blueprint, render_template, current_app, request, abort, make_response, redirect, url_for, jsonify

import cea.inputlocator
from cea.config import MultiChoiceParameter
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
    plot_cache = current_app.plot_cache
    dashboards = cea.plots.read_dashboards(cea_config, plot_cache)
    dashboard = dashboards[dashboard_index]
    layout = dashboard.layout

    # add new layouts here
    if layout not in {"map", "row", "grid"}:
        layout = "row"  # this is the default layout for Dashboards

    return render_template('layout/{}_layout.html'.format(layout), dashboard_index=dashboard_index, dashboards=dashboards,
                           dashboard=dashboard, categories=categories, last_updated=dir_last_updated())


@blueprint.route('/dashboard/manage')
def route_manage_dashboards():
    cea_config = current_app.cea_config
    plot_cache = current_app.plot_cache
    dashboards = cea.plots.read_dashboards(cea_config, plot_cache)
    return render_template('manage.html', dashboards=dashboards)


@blueprint.route('/dashboard/new')
def route_new_dashboard_modal():
    return render_template('modal/new_dashboard.html')


@blueprint.route('/dashboard/new/save', methods=['POST'])
def route_new_dashboard():
    """
    Append a dashboard to the list of dashboards and open it for editing.
    """
    cea_config = current_app.cea_config
    plot_cache = current_app.plot_cache
    dashboard_index = cea.plots.new_dashboard(cea_config, plot_cache, request.form.get('name'),
                                              request.form.get('description'), request.form.get('layout'))
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/delete/<int:dashboard_index>')
def route_delete_dashboard_modal(dashboard_index):
    cea_config = current_app.cea_config
    plot_cache = current_app.plot_cache
    dashboards = cea.plots.read_dashboards(cea_config, plot_cache)
    dashboard_name = dashboards[dashboard_index].name

    return render_template('modal/delete_dashboard.html', dashboard_index=dashboard_index,
                           dashboard_name=dashboard_name)


@blueprint.route('/dashboard/rename/<int:dashboard_index>')
def route_rename_dashboard_modal(dashboard_index):
    cea_config = current_app.cea_config
    plot_cache = current_app.plot_cache
    dashboards = cea.plots.read_dashboards(cea_config, plot_cache)
    dashboard_name = dashboards[dashboard_index].name
    dashboard_description = dashboards[dashboard_index].description

    return render_template('modal/rename_dashboard.html', dashboard_index=dashboard_index,
                           dashboard_name=dashboard_name, dashboard_description=dashboard_description)


@blueprint.route('/dashboard/duplicate/<int:dashboard_index>')
def route_duplicate_dashboard_modal(dashboard_index):
    cea_config = current_app.cea_config
    plot_cache = current_app.plot_cache
    dashboards = cea.plots.read_dashboards(cea_config, plot_cache)
    dashboard_name = dashboards[dashboard_index].name
    dashboard_description = dashboards[dashboard_index].description

    return render_template('modal/duplicate_dashboard.html', dashboard_index=dashboard_index,
                           dashboard_name=dashboard_name, dashboard_description=dashboard_description)


@blueprint.route('/dashboard/delete/<int:dashboard_index>', methods=['POST'])
def route_delete_dashboard(dashboard_index):
    cea_config = current_app.cea_config
    cea.plots.delete_dashboard(cea_config, dashboard_index)
    return redirect(url_for('plots_blueprint.route_manage_dashboards'))


@blueprint.route('/dashboard/rename/<int:dashboard_index>', methods=['POST'])
def route_rename_dashboard(dashboard_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
    dashboard = dashboards[dashboard_index]
    dashboard.name = request.form.get('new-name', dashboard.name)
    dashboard.description = request.form.get('new-description', dashboard.description)
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_manage_dashboards'))


@blueprint.route('/dashboard/duplicate/<int:dashboard_index>', methods=['POST'])
def route_duplicate_dashboard(dashboard_index):
    cea_config = current_app.cea_config
    plot_cache = current_app.plot_cache
    duplicate_index = cea.plots.duplicate_dashboard(cea_config, plot_cache, request.form.get('name'),
                                                    request.form.get('description'), dashboard_index)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=duplicate_index))


@blueprint.route('/dashboard/add-plot/<int:dashboard_index>', methods=['POST'])
def route_add_plot_to_dashboard(dashboard_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
    dashboard = dashboards[dashboard_index]
    category = request.form.get('category', next(iter(categories)))
    plot_id = request.form.get('plot-id', next(iter(categories[category]['plots']))['id'])
    dashboard.add_plot(category, plot_id)
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/replace-plot/<int:dashboard_index>/<int:plot_index>', methods=['POST'])
def route_replace_plot(dashboard_index, plot_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
    dashboard = dashboards[dashboard_index]
    category = request.form.get('category', next(iter(categories)))
    plot_id = request.form.get('plot-id', next(iter(categories[category]['plots']))['id'])
    dashboard.replace_plot(category, plot_id, plot_index)
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/remove-plot/<int:dashboard_index>/<int:plot_index>')
def route_remove_plot_from_dashboard(dashboard_index, plot_index):
    """Remove a plot from a dashboard by index."""
    dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
    dashboard = dashboards[dashboard_index]
    dashboard.remove_plot(plot_index)
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/move_plot_up/<int:dashboard_index>/<int:plot_index>')
def route_move_plot_up(dashboard_index, plot_index):
    """Move a plot up in the dashboard"""
    if plot_index > 0:
        dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
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
        dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
        dashboard = dashboards[dashboard_index]
        if plot_index < (len(dashboard.plots) - 1):
            swap(dashboard.plots, plot_index, plot_index + 1)
            cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return redirect(url_for('plots_blueprint.route_dashboard', dashboard_index=dashboard_index))


@blueprint.route('/dashboard/plot-parameters/<int:dashboard_index>/<int:plot_index>', methods=['GET'])
def route_get_plot_parameters(dashboard_index, plot_index):
    dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
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
    dashboards = cea.plots.read_dashboards(current_app.cea_config, current_app.plot_cache)
    dashboard = dashboards[dashboard_index]
    plot = dashboard.plots[plot_index]
    print('route_post_plot_parameters: expected_parameters: {}'.format(plot.expected_parameters.items()))
    for pname, fqname in plot.expected_parameters.items():
        parameter = current_app.cea_config.get_parameter(fqname)
        print('route_post_plot_parameters: fqname={fqname}, pname={pname}'.format(fqname=fqname, pname=pname))
        if isinstance(parameter, MultiChoiceParameter):
            plot.parameters[pname] = parameter.decode(','.join(request.form.getlist(pname)))
        else:
            plot.parameters[pname] = parameter.decode(request.form[pname])
    cea.plots.write_dashboards(current_app.cea_config, dashboards)
    return jsonify(plot.parameters)


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


@blueprint.route('/table/<int:dashboard_index>/<int:plot_index>')
def route_table(dashboard_index, plot_index):
    """Return the table for the plot as a div to be used in an AJAX call"""
    try:
        plot = load_plot(dashboard_index, plot_index)
    except Exception as ex:
        return abort(500, ex)
    if not plot.missing_input_files():
        return make_response(plot.table_div(), 200)


def script_suggestions(locator_names):
    """Return a list of CeaScript objects that produce the output for each locator name"""
    import cea.scripts
    schemas = cea.scripts.schemas()
    script_names = []
    for name in locator_names:
        script_names.extend(schemas[name]['created_by'])
    return [cea.scripts.by_name(n) for n in sorted(set(script_names))]


def load_plot(dashboard_index, plot_index):
    """Load a plot from the dashboard_yml"""
    cea_config = current_app.cea_config
    dashboards = cea.plots.read_dashboards(cea_config, current_app.plot_cache)
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


def dir_last_updated():
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), 'static'))
                   for f in files))
