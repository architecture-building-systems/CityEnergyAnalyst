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
    try:
        with open(dashboard_yml_path(config), 'r') as f:
            dashboards = [Dashboard(config, dashboard_dict) for dashboard_dict in yaml.load(f)]
            if not dashboards:
                dashboards = [default_dashboard(config)]
            return dashboards
    except (IOError, TypeError):
        # problems reading the dashboard_yml file - instead, create a default set of dashboards.
        dashboards = [default_dashboard(config)]
        write_dashboards(config, dashboards)
        return dashboards


def write_dashboards(config, dashboards):
    """Write a list of Dashboard objects to disk"""
    with open(dashboard_yml_path(config), 'w') as f:
        yaml.dump([d.to_dict() for d in dashboards], f)


def dashboard_yml_path(config):
    """The path to the dashboard_yml file"""
    dashboard_yml = os.path.join(config.project, 'dashboard.yml')
    return dashboard_yml


def default_dashboard(config):
    """Return a default Dashboard"""
    return Dashboard(config, {'name': 'Default Dashboard',
                              'plots': [{'plot': 'energy-balance',
                                         'category': 'demand',
                                         'parameters': {'buildings': [],
                                                        'scenario-name': config.scenario_name}}]})


def new_dashboard(config):
    """
    Append a new dashboard to the dashboard configuration and write it back to disk.
    Returns the index of the new dashboard in the dashboards list.
    """
    dashboards = read_dashboards(config)
    dashboards.append(default_dashboard(config))
    write_dashboards(config, dashboards)
    return len(dashboards) - 1


def delete_dashboard(config, dashboard_index):
    """Remove the dashboard with that index from the dashboard configuration file"""
    dashboards = read_dashboards(config)
    dashboards.pop(dashboard_index)
    write_dashboards(config, dashboards)


class Dashboard(object):
    """Implements a dashboard - an editable collection of configured plots."""
    def __init__(self, config, dashboard_dict):
        self.config = config
        self.name = dashboard_dict['name']
        self.plots = [load_plot(config.project, plot_dict) for plot_dict in dashboard_dict['plots']]

    def add_plot(self, category, plot_id):
        """Add a new plot to the dashboard"""
        plot_class = cea.plots.categories.load_plot_by_id(category, plot_id)
        parameters = plot_class.get_default_parameters(self.config)
        plot = plot_class(self.config.project, parameters)
        self.plots.append(plot)

    def remove_plot(self, plot_index):
        """Remove a plot by index"""
        self.plots.pop(plot_index)

    def to_dict(self):
        """Return a dict representation for storing in yaml"""
        return {'name': self.name,
                'plots': [{'plot': p.id(),
                           'category': p.category_name,
                           'parameters': p.parameters} for p in self.plots]}


def load_plot(project, plot_definition):
    """Load a plot based on a plot definition dictionary as used in the dashboard_yml file"""
    print('load_plot', project, plot_definition)
    category_name = plot_definition['category']
    plot_id = plot_definition['plot']
    plot_class = cea.plots.categories.load_plot_by_id(category_name, plot_id)
    parameters = plot_definition['parameters']
    return plot_class(project, parameters)


def main(config):
    """Test the dashboard functionality. Run it twice, because the dashboard.yml might have been created as a result"""
    print(read_dashboards(config))
    print(read_dashboards(config))


if __name__ == '__main__':
    main(cea.config.Configuration())