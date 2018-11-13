from __future__ import division
from __future__ import print_function

"""
Organizes the plots for the CEA. The dashboard uses the package structure of cea.plots to group the plots into
categories and find the implementations of the plots.

Each sub-package of ``cea.plots`` is a plot category. The ``__init__.py`` file of that sub-package is expected to
have an attribute ``label`` which is used as the user-visible label of that category.

Each module contained such a sub-package is considered a plot.

The module ``cea.plots.categories`` contains helper-methods for dealing with the categories.
"""

import os
import yaml
import cea.config
import cea.inputlocator
from cea.plots.base import PlotBase
import cea.plots.categories

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_dashboards(config):
    """
    Return a list of dashboard configurations for a given project. The dashboard is loaded from the
    dashboard.yml file located in the project_path (parent folder of the scenario). If no such file is
    found, a default one is returned (but not written to disk).
    """
    dashboard_yml = os.path.join(config.project, 'dashboard.yml')

    try:
        with open(dashboard_yml, 'r') as f:
            return [Dashboard(config, dashboard_dict) for dashboard_dict in yaml.load(f)]
    except (IOError, TypeError):
        dashboards = [default_dashboard(config)]
        with open(dashboard_yml, 'w') as f:
            yaml.dump([d.to_dict() for d in dashboards], f)
        return dashboards


def default_dashboard(config):
    """Return a default Dashboard"""
    return Dashboard(config, {'name': 'Default Dashboard',
                              'plots': [{'plot': 'energy-balance',
                                         'category': 'demand',
                                         'scenario': config.scenario,
                                         'parameters': {'buildings': []}}]})


class Dashboard(object):
    """Implements a dashboard - an editable collection of configured plots."""
    def __init__(self, config, dashboard_dict):
        self.name = dashboard_dict['name']
        self.plots = [load_plot(config, plot_dict) for plot_dict in dashboard_dict['plots']]

    def to_dict(self):
        """Return a dict representation for storing in yaml"""
        return {'name': self.name,
                'plots': [{'plot': p.id(),
                           'category': p.category_name,
                           'parameters': p.parameters} for p in self.plots]}


def load_plot(config, plot_definition):
    """Load a plot based on a plot definition dictionary as used in the dashboard_yml file"""
    print('load_plot', config.scenario, plot_definition)
    category_name = plot_definition['category']
    plot_id = plot_definition['plot']
    scenario = plot_definition['scenario']
    plot_class = cea.plots.categories.load_plot_by_id(category_name, plot_id)
    parameters = plot_definition['parameters']
    locator = cea.inputlocator.InputLocator(scenario=scenario)
    return plot_class(config, locator, **parameters)


def write_default_dashboard(dashboard_yml, scenario_name):
    """Write out a default dashboard configuration to the path located by ``dashboard_yml``"""
    dashboard = [
        {'name': 'Default Dashboard',
         'scenario': scenario_name,
         'plot': 'energy-balance',
         'category': 'demand'}
    ]


def main(config):
    """Test the dashboard functionality"""
    print(read_dashboards(config))


if __name__ == '__main__':
    main(cea.config.Configuration())