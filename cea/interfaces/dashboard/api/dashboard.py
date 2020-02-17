import hashlib

from flask import current_app, request
from flask_restplus import Namespace, Resource

import cea.config
import cea.plots.cache
from utils import deconstruct_parameters

api = Namespace('Dashboard', description='Dashboard plots')

LAYOUTS = ['row', 'grid']
CATEGORIES = {c.name: {'label': c.label, 'plots': [{'id': p.id(), 'name': p.name} for p in c.plots]}
              for c in cea.plots.categories.list_categories()}



def dashboard_to_dict(dashboard):
    out = dashboard.to_dict()
    for i, plot in enumerate(out['plots']):
        if plot['plot'] != 'empty':
            plot['hash'] = hashlib.md5(repr(sorted(plot.items()))).hexdigest()
            plot['title'] = dashboard.plots[i].title
    return out


def get_parameters_from_plot(plot, scenario_name=None):
    config = cea.config.Configuration()
    parameters = []
    # Make sure to set scenario name to config first
    if 'scenario-name' in plot.expected_parameters:
        if scenario_name is not None:
            config.scenario_name = scenario_name
        elif 'scenario-name' in plot.parameters:
            config.scenario_name = plot.parameters['scenario-name']

    for pname, fqname in sorted(plot.expected_parameters.items(), key=lambda x: x[1]):
        parameter = config.get_parameter(fqname)
        if pname in plot.parameters and pname != 'scenario-name':
            try:
                parameter.set(plot.parameters[pname])
            # FIXME: Use a custom exception instead
            except AssertionError as e:
                if isinstance(parameter, cea.config.MultiChoiceParameter):
                    parameter.set([])
                print(e)
        parameters.append(deconstruct_parameters(parameter))
    return parameters


def get_parameters_from_plot_class(plot_class, scenario_name=None):
    config = cea.config.Configuration()
    parameters = []
    # Make sure to set scenario name to config first
    if 'scenario-name' in plot_class.expected_parameters and scenario_name is not None:
        config.scenario_name = scenario_name

    for pname, fqname in sorted(plot_class.expected_parameters.items(), key=lambda x: x[1]):
        parameter = config.get_parameter(fqname)
        parameters.append(deconstruct_parameters(parameter))
    return parameters


@api.route('/')
class Dashboards(Resource):
    def get(self):
        """
        Get list of Dashboards
        """
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)

        out = []
        for d in dashboards:
            out.append(dashboard_to_dict(d))

        return out

    def post(self):
        """
        Create Dashboard
        """
        form = api.payload
        config = current_app.cea_config

        if 'grid' in form['layout']:
            types = [[2] + [1] * 4, [1] * 6, [1] * 3 + [3], [2, 1] * 2]
            grid_width = types[int(form['layout'].split('-')[-1]) - 1]
            dashboard_index = cea.plots.new_dashboard(config, current_app.plot_cache, form['name'], 'grid',
                                                      grid_width=grid_width)
        else:
            dashboard_index = cea.plots.new_dashboard(config, current_app.plot_cache, form['name'], form['layout'])

        return {'new_dashboard_index': dashboard_index}


@api.route('/duplicate')
class DashboardDuplicate(Resource):
    def post(self):
        form = api.payload
        config = current_app.cea_config
        dashboard_index = cea.plots.duplicate_dashboard(config, current_app.plot_cache, form['name'],
                                                        form['dashboard_index'])

        return {'new_dashboard_index': dashboard_index}


@api.route('/<int:dashboard_index>')
class Dashboard(Resource):
    def get(self, dashboard_index):
        """
        Get Dashboard
        """
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)

        return dashboard_to_dict(dashboards[dashboard_index])

    def delete(self, dashboard_index):
        """
        Delete Dashboard
        """
        config = current_app.cea_config
        cea.plots.delete_dashboard(config, dashboard_index)

        return {'message': 'deleted dashboard'}

    def patch(self, dashboard_index):
        """
        Update Dashboard properties
        """
        form = api.payload
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.cea_config)

        dashboard = dashboards[dashboard_index]
        dashboard.set_scenario(form['scenario'])
        cea.plots.write_dashboards(config, dashboards)

        return {'new_dashboard_index': dashboard_index}


@api.route('/plot-categories')
class DashboardPlotCategories(Resource):
    """
    Get Plot Categories
    """

    def get(self):
        return CATEGORIES


@api.route('/plot-categories/<string:category_name>/plots/<string:plot_id>/parameters')
class DashboardPlotCategoriesParameters(Resource):
    """
    Get Plot Form Parameters from Config
    """

    def get(self, category_name, plot_id):
        plot_class = cea.plots.categories.load_plot_by_id(category_name, plot_id)
        return get_parameters_from_plot_class(plot_class, request.args.get('scenario'))


@api.route('/<int:dashboard_index>/plots/<int:plot_index>')
class DashboardPlot(Resource):
    def get(self, dashboard_index, plot_index):
        """
        Get Dashboard Plot
        """
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)

        return dashboard_to_dict(dashboards[dashboard_index])['plots'][plot_index]

    def put(self, dashboard_index, plot_index):
        """
        Create/Replace a new Plot at specified index
        """
        form = api.payload
        config = current_app.cea_config

        # avoid overwriting original config.scenario for plot
        temp_config = cea.config.Configuration()
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)
        dashboard = dashboards[dashboard_index]

        if 'category' in form and 'plot_id' in form:
            dashboard.add_plot(form['category'], form['plot_id'], plot_index)

        # Set parameters if included in form and plot exists
        if 'parameters' in form:
            plot = dashboard.plots[plot_index]
            plot_parameters = plot.expected_parameters.items()
            if 'scenario-name' in plot.expected_parameters:
                temp_config.scenario_name = form['parameters']['scenario-name']
            print('expected_parameters: {}'.format(plot_parameters))
            for pname, fqname in plot_parameters:
                parameter = temp_config.get_parameter(fqname)
                if isinstance(parameter, cea.config.MultiChoiceParameter):
                    plot.parameters[pname] = parameter.decode(','.join(form['parameters'][pname]))
                else:
                    plot.parameters[pname] = parameter.decode(form['parameters'][pname])

        cea.plots.write_dashboards(config, dashboards)

        return dashboard_to_dict(dashboards[dashboard_index])['plots'][plot_index]

    def delete(self, dashboard_index, plot_index):
        """
        Delete Plot from Dashboard
        """
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)

        dashboard = dashboards[dashboard_index]
        dashboard.remove_plot(plot_index)
        cea.plots.write_dashboards(config, dashboards)

        return dashboard_to_dict(dashboard)


@api.route('/<int:dashboard_index>/plots/<int:plot_index>/parameters')
class DashboardPlotParameters(Resource):
    def get(self, dashboard_index, plot_index):
        """
        Get Plot Form Parameters of Plot in Dashboard
        """
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)

        dashboard = dashboards[dashboard_index]
        plot = dashboard.plots[plot_index]

        return get_parameters_from_plot(plot, request.args.get('scenario'))


@api.route('/<int:dashboard_index>/plots/<int:plot_index>/input-files')
class DashboardPlotInputFiles(Resource):
    def get(self, dashboard_index, plot_index):
        """
        Get input files of Plot
        """
        config = current_app.cea_config
        dashboards = cea.plots.read_dashboards(config, current_app.plot_cache)

        dashboard = dashboards[dashboard_index]
        plot = dashboard.plots[plot_index]

        return [locator_method(*args) for locator_method, args in plot.input_files]
