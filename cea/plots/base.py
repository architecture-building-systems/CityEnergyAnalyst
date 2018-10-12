from __future__ import division
from __future__ import print_function

"""
Implements base classes to derive plot classes from. The code in py:mod:`cea.plots.categories` uses 
py:class:`cea.plots.base.PlotBase` to figure out the list of plots in a category.
"""

import plotly.graph_objs
import plotly.offline

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

    def __init__(self, config, locator, buildings):
        self.name = None  # override this in plot subclasses!
        self.category_path = None  # override this in the __init__.py subclasses for each category (see cea/plots/demand/__init__.py for an example)
        self.data = None  # override this in the plot subclasses! set it to the pandas DataFrame to use as data
        self.layout = None # override this in the plot subclasses! set it to a plotly.graph_objs.Layout object
        self.analysis_fields = None  # override this in the plot subclasses! set it to a list of fields in self.data

        self.config = config
        self.locator = locator
        self.buildings = buildings if buildings else locator.get_zone_building_names()

    @property
    def title(self):
        if self.buildings:
            if len(self.buildings) == 1:
                return "%s for Building %s" % (self.name, self.buildings[0])
            else:
                return "%s for Selected Buildings" % self.name
        else:
            return "%s for District" % self.name

    @property
    def output_path(self):
        """The output path to use for the """
        assert self.name, "Attribute 'name' not defined for this plot (%s)" % self.__class__
        assert self.category_path, "Attribute 'category_path' not defined for this plot(%s)" % self.__class__

        prefix = 'Building_%s' % self.buildings[0] if self.buildings and len(self.buildings) == 1 else 'District'
        fname = "%s_%s" % (prefix, self.name.lower().replace(' ', '_'))
        return self.locator.get_timeseries_plots_file(fname, self.category_path)

    def calc_graph(self):
        """Calculate a plotly Data object as to be passed to the data attribute of Figure"""
        raise NotImplementedError('Subclass needs to implement calc_graph for plot!')

    def plot(self, auto_open=False):
        """Plots the graphs to the filename (see output_path)"""
        fig = plotly.graph_objs.Figure(data=self.calc_graph(), layout=self.layout)
        plotly.offline.plot(fig, auto_open=auto_open, filename=self.output_path)
        print("Plotted %s to %s" % (self.name, self.output_path))