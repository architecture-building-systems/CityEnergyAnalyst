from flask_restplus import Namespace, Resource, fields, abort

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

        return [{'name': d.name, 'description': d.description, 'layout':  d.layout if d.layout in LAYOUTS else 'row',
                 'plots': [{'title': plot.title, 'scenario':
                            plot.parameters['scenario-name'] if 'scenario-name' in plot.parameters.keys() else None}
                           for plot in d.plots]} for d in dashboards]
