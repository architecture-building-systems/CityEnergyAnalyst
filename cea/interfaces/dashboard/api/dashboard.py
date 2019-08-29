from flask_restplus import Namespace, Resource, fields, abort
from utils import deconstruct_parameters

import hashlib
import cea.config
import cea.plots.cache

api = Namespace('Dashboard', description='Dashboard plots')


LAYOUTS = ['row', 'grid', 'map']
CATEGORIES = {c.name: {'label': c.label, 'plots': [{'id': p.id(), 'name': p.name} for p in c.plots]}
              for c in cea.plots.categories.list_categories()}


@api.route('/')
class Dashboard(Resource):
    def get(self):
        """
        Get Dashboards from yaml file
        """
        config = cea.config.Configuration()
        plot_cache = cea.plots.cache.PlotCache(config)
        dashboards = cea.plots.read_dashboards(config, plot_cache)

        out = []
        for d in dashboards:
            dashboard = d.to_dict()
            for i, plot in enumerate(dashboard['plots']):
                dashboard['plots'][i]['hash'] = hashlib.md5(repr(sorted(dashboard['plots'][i].items()))).hexdigest()
                dashboard['plots'][i]['title'] = d.plots[i].title
            out.append(dashboard)

        return out


@api.route('/plot-parameters/<int:dashboard_index>/<int:plot_index>')
class DashboardParameters(Resource):
    def get(self, dashboard_index, plot_index):
        config = cea.config.Configuration()
        plot_cache = cea.plots.cache.PlotCache(config)
        dashboards = cea.plots.read_dashboards(config, plot_cache)

        dashboard = dashboards[dashboard_index]
        plot = dashboard.plots[plot_index]
        parameters = []
        for pname, fqname in plot.expected_parameters.items():
            parameter = config.get_parameter(fqname)
            if pname in plot.parameters:
                parameter.set(plot.parameters[pname])
            parameters.append(deconstruct_parameters(parameter))
        return parameters

    def post(self, dashboard_index, plot_index):
        form = api.payload
        config = cea.config.Configuration()
        plot_cache = cea.plots.cache.PlotCache(config)
        dashboards = cea.plots.read_dashboards(config, plot_cache)

        dashboard = dashboards[dashboard_index]
        plot = dashboard.plots[plot_index]
        print('route_post_plot_parameters: expected_parameters: {}'.format(plot.expected_parameters.items()))
        for pname, fqname in plot.expected_parameters.items():
            parameter = config.get_parameter(fqname)
            print('route_post_plot_parameters: fqname={fqname}, pname={pname}'.format(fqname=fqname, pname=pname))
            if isinstance(parameter, cea.config.MultiChoiceParameter):
                plot.parameters[pname] = parameter.decode(','.join(form[pname]))
            else:
                plot.parameters[pname] = parameter.decode(form[pname])
        cea.plots.write_dashboards(config, dashboards)

        return plot.parameters
