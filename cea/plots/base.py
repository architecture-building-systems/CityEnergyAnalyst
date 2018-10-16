from __future__ import division
from __future__ import print_function

"""
Implements base classes to derive plot classes from. The code in py:mod:`cea.plots.categories` uses 
py:class:`cea.plots.base.PlotBase` to figure out the list of plots in a category.
"""

import plotly.graph_objs
import plotly.offline
from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class PlotBase(object):
    """A base class for plots containing helper methods used by all plots."""
    name = None  # override this in plot subclasses!

    @classmethod
    def id(cls):
        return cls.name.lower().replace(' ', '-')  # use for js/html etc.

    def __init__(self, config, locator, buildings):
        self.category_path = None  # override this in the __init__.py subclasses for each category (see cea/plots/demand/__init__.py for an example)
        self.data = None  # override this in the plot subclasses! set it to the pandas DataFrame to use as data
        self.layout = None # override this in the plot subclasses! set it to a plotly.graph_objs.Layout object
        self.analysis_fields = None  # override this in the plot subclasses! set it to a list of fields in self.data

        self.config = config
        self.locator = locator
        if not buildings:
            buildings = locator.get_zone_building_names()
        self.buildings = ([b for b in buildings if
                           b in locator.get_zone_building_names()] or locator.get_zone_building_names())

    @property
    def title(self):
        if set(self.buildings) != set(self.locator.get_zone_building_names()):
            if len(self.buildings) == 1:
                return "%s for Building %s" % (self.name, self.buildings[0])
            else:
                return "%s for Selected Buildings" % self.name
        return "%s for District" % self.name

    def totals_bar_plot(self):
        """Creates a plot based on the totals data in percentages."""
        traces = []
        self.data['total'] = self.data[self.analysis_fields].sum(axis=1)
        self.data = self.data.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        for field in self.analysis_fields:
            y = self.data[field]
            total_percent = (y / self.data['total'] * 100).round(2).values
            total_percent_txt = ["(%.2f %%)" % x for x in total_percent]
            name = NAMING[field]
            trace = plotly.graph_objs.Bar(x=self.data["Name"], y=y, name=name, marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces

    @property
    def output_path(self):
        """The output path to use for the """
        assert self.name, "Attribute 'name' not defined for this plot (%s)" % self.__class__
        assert self.category_path, "Attribute 'category_path' not defined for this plot(%s)" % self.__class__

        if len(self.buildings) == 1:
            prefix = 'Building_%s' % self.buildings[0]
        elif len(self.buildings) < len(self.locator.get_zone_building_names()):
            prefix = 'Selected_Buildings'
        else:
            prefix = 'District'
        fname = "%s_%s" % (prefix, self.name.lower().replace(' ', '_'))
        return self.locator.get_timeseries_plots_file(fname, self.category_path)

    def remove_unused_fields(self, data, fields):
        """
        Helper method that, given a data frame and a list of fields in that data frame, returns the subset of those
        fields that actually have data.

        FIXME: what about columns with negative values?
        """
        return [field for field in fields if data[field].sum() > 0.0]

    def calc_graph(self):
        """Calculate a plotly Data object as to be passed to the data attribute of Figure"""
        raise NotImplementedError('Subclass needs to implement calc_graph for plot!')

    def plot(self, auto_open=False):
        """Plots the graphs to the filename (see output_path)"""
        fig = plotly.graph_objs.Figure(data=self.calc_graph(), layout=self.layout)
        plotly.offline.plot(fig, auto_open=auto_open, filename=self.output_path)
        print("Plotted %s to %s" % (self.name, self.output_path))

    def plot_div(self):
        """Return the plot as an html <div/> for use in the dashboard. Override this method in subclasses"""
        fig = plotly.graph_objs.Figure(data=self.calc_graph(), layout=self.layout)
        div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
        return div
