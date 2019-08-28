from flask_restplus import Namespace, Resource, fields, abort

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
