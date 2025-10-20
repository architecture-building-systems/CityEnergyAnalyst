


"""
Organizes the plots for the CEA. The dashboard uses the package structure of cea.plots to group the plots into
categories and find the implementations of the plots.

Each sub-package of ``cea.plots`` is a plot category. The ``__init__.py`` file of that sub-package is expected to
have an attribute ``label`` which is used as the user-visible label of that category.

Each module contained such a sub-package is considered a plot.

The module ``cea.plots.categories`` contains helper-methods for dealing with the categories.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import os
import yaml
import cea.plots.categories

if TYPE_CHECKING:
    import cea.config

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_dashboards(config, cache):
    """
    Return a list of dashboard configurations for a given project. The dashboard is loaded from the
    dashboard.yml file located in the project_path (parent folder of the scenario). If no such file is
    found, a default one is returned (but not written to disk).
    """
    try:
        with open(dashboard_yml_path(config), 'r') as f:
            dashboards = [Dashboard(config, dashboard_dict, cache)
                          for dashboard_dict in yaml.load(f, Loader=yaml.CSafeLoader)]
            if not dashboards:
                dashboards = [default_dashboard(config, cache)]
            return dashboards
    except (IOError, TypeError):
        import traceback
        traceback.print_exc()
        # problems reading the dashboard_yml file - instead, create a default set of dashboards.
        dashboards = [default_dashboard(config, cache)]
        write_dashboards(config, dashboards)
        return dashboards


def write_dashboards(config, dashboards):
    """Write a list of Dashboard objects to disk"""
    yaml.SafeDumper.ignore_aliases = lambda *args: True
    with open(dashboard_yml_path(config), 'w') as f:
        yaml.safe_dump([d.to_dict() for d in dashboards], f)


def dashboard_yml_path(config):
    """The path to the dashboard_yml file"""
    dashboard_yml = os.path.join(config.project, 'dashboard.yml')
    return dashboard_yml


def default_dashboard(config, cache):
    """Return a default Dashboard"""
    return Dashboard(config, {
        'name': 'Default Dashboard',
        'layout': 'row',
        'plots': []
    }, cache)


def new_dashboard(config, cache, name, layout, grid_width=None):
    """
    Append a new dashboard to the dashboard configuration and write it back to disk.
    Returns the index of the new dashboard in the dashboards list.
    """
    dashboard_dict = {
        'name': name,
        'layout': layout,
        'plots': []
    }
    if layout == 'grid':
        dashboard_dict['grid_width'] = grid_width
        dashboard_dict['plots'] = [{'plot': 'empty'}] * len(grid_width)
    dashboards = read_dashboards(config, cache)
    dashboards.append(Dashboard(config, dashboard_dict, cache))
    write_dashboards(config, dashboards)
    return len(dashboards) - 1


def duplicate_dashboard(config, cache, name, dashboard_index):
    dashboards = read_dashboards(config, cache)
    dashboard = dashboards[dashboard_index].to_dict()
    dashboards.append(Dashboard(config, {
        'name': name,
        'layout': dashboard['layout'],
        'plots': dashboard['plots']
    }, cache))
    write_dashboards(config, dashboards)
    return len(dashboards) - 1


def delete_dashboard(config, dashboard_index):
    """Remove the dashboard with that index from the dashboard configuration file"""
    import cea.plots.cache
    dashboards = read_dashboards(config, cea.plots.cache.NullPlotCache())
    dashboards.pop(dashboard_index)
    write_dashboards(config, dashboards)


class Dashboard(object):
    """Implements a dashboard - an editable collection of configured plots."""
    def __init__(self, config, dashboard_dict, cache):
        self.config = config
        self.name = dashboard_dict['name']
        self.cache = cache
        self.plots = [load_plot(config.project, plot_dict, cache, config.plugins) for plot_dict in
                      dashboard_dict['plots']]
        try:
            layout = dashboard_dict['layout']
            self.layout = 'grid' if layout == 'map' else layout
        except KeyError:
            self.layout = 'row'
        if self.layout == 'grid':
            try:
                self.grid_width = dashboard_dict['grid_width']
            except KeyError:
                self.grid_width = [1] * len(self.plots)

    def add_plot(self, category, plot_id, plugins, index=None):
        """Add a new plot to the specified index in the dashboard"""
        plot_class = cea.plots.categories.load_plot_by_id(category, plot_id, plugins)
        parameters = plot_class.get_default_parameters(self.config)

        plot = plot_class(self.config.project, parameters, self.cache)

        if index is None:
            index = len(self.plots)
        if index == len(self.plots):
            self.plots.append(plot)
        else:
            self.plots[index] = plot

    def remove_plot(self, plot_index):
        """Remove a plot by index"""
        if self.layout == 'grid':
            self.plots[plot_index] = None
        else:
            self.plots.pop(plot_index)

    def set_scenario(self, scenario):
        """Set all scenario parameters of dashboard plots"""
        for plot in self.plots:
            if plot is not None:
                if 'scenario-name' in plot.parameters:
                    plot.parameters['scenario-name'] = scenario

    def to_dict(self):
        """Return a dict representation for storing in yaml"""
        out = {'name': self.name, 'layout': self.layout, 
               'plots': [{'plot': p.id(), 
                          'category': p.category_name, 
                          'parameters': p.parameters} if p is not None else {'plot': 'empty'} for p in self.plots]}
        if self.layout == 'grid':
            out['grid_width'] = self.grid_width
        return out


def load_plot(project, plot_definition, cache, plugins):
    """Load a plot based on a plot definition dictionary as used in the dashboard_yml file"""
    if plot_definition['plot'] == 'empty':
        return None
    category_name = plot_definition['category']
    plot_id = plot_definition['plot']
    plot_class = cea.plots.categories.load_plot_by_id(category_name, plot_id, plugins)
    parameters = plot_definition['parameters']
    return plot_class(project, parameters, cache)


def main(config: cea.config.Configuration):
    """Test the dashboard functionality. Run it twice, because the dashboard.yml might have been created as a result"""
    import cea.plots.cache
    print(read_dashboards(config, cea.plots.cache.NullPlotCache()))


if __name__ == '__main__':
    import cea.config
    main(cea.config.Configuration())
