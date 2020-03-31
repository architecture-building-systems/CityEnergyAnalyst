"""
Implements base classes to derive plot classes from. The code in py:mod:`cea.plots.categories` uses
py:class:`cea.plots.base.PlotBase` to figure out the list of plots in a category.
"""
from __future__ import division
from __future__ import print_function

import os
import re

import jinja2
import plotly.graph_objs
import plotly.offline

import cea.config
import cea.inputlocator
from cea import MissingInputDataException
from cea.plots.variable_naming import COLOR, NAMING

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

    # override these in plot subclasses!
    name = None  # a label to name the plot
    category_name = None  # name of the category this plot belongs to (can be inherited from category base plot)
    category_path = None  # a relative path for outputting the plot to (FIXME: maybe we remove this later on)
    expected_parameters = {}  # maps parameter-name -> "section:parameter"

    @classmethod
    def id(cls):
        name = re.sub('\s+\(.*\)', '', cls.name)  # remove parenthesis
        return name.lower().replace(' ', '_').replace('/', '_')  # use for js/html etc.

    def __init__(self, project, parameters, cache):
        self.cache = cache  # a PlotCache implementation for reading cached data
        self.project = project  # full path to the project this plot belongs to
        self.category_path = None  # override this in the __init__.py subclasses for each category (see cea/plots/demand/__init__.py for an example)
        # self.analysis_fields = None  # override this in the plot subclasses! set it to a list of fields in self.data
        # self.input_files = []  # override this in the plot subclasses! set it to a list of tuples (locator.method, args)
        self.parameters = parameters
        self.buildings = self.process_buildings_parameter() if 'buildings' in self.expected_parameters else None

        for parameter_name in self.expected_parameters:
            # Try to load missing parameters with default values
            if parameter_name not in parameters:
                try:
                    self.parameters[parameter_name] = cea.config.Configuration(cea.config.DEFAULT_CONFIG).get(
                        'plots:{}'.format(parameter_name))
                except Exception:
                    assert parameter_name in parameters, "Missing parameter {}".format(parameter_name)

    def missing_input_files(self):
        """Return the list of missing input files for this plot"""
        result = []
        for locator_method, args in self.input_files:
            if not os.path.exists(locator_method(*args)):
                result.append((locator_method, args))
        return result

    @property
    def locator(self):
        """
        :return: cea.inputlocator.InputLocator
        """
        return cea.inputlocator.InputLocator(os.path.join(self.project, self.parameters['scenario-name']))

    @property
    def layout(self):
        # override this in the plot subclasses! set it to a plotly.graph_objs.Layout object
        return None

    @property
    def title(self):
        """Override the version in PlotBase"""
        if set(self.buildings) != set(self.locator.get_zone_building_names()):
            if len(self.buildings) == 1:
                return "%s for Building %s" % (self.name, self.buildings[0])
            else:
                return "%s for Selected Buildings" % self.name
        return "%s for District" % self.name

    def totals_bar_plot(self):
        """Creates a plot based on the totals data in percentages."""
        traces = []
        data = self.data
        data['total'] = data[self.analysis_fields].sum(axis=1)
        data = data.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        for field in self.analysis_fields:
            y = data[field]
            total_percent = (y / data['total'] * 100).round(2).values
            total_percent_txt = ["(%.2f %%)" % x for x in total_percent]
            name = NAMING[field]
            trace = plotly.graph_objs.Bar(x=data["Name"], y=y, name=name, marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces

    @property
    def output_path(self):
        """The output path to use for the solar-potential plots"""
        assert self.name, "Attribute 'name' not defined for this plot (%s)" % self.__class__
        assert self.category_path, "Attribute 'category_path' not defined for this plot(%s)" % self.__class__

        if len(self.buildings) == 1:
            prefix = 'Building_%s' % self.buildings[0]
        elif len(self.buildings) < len(self.locator.get_zone_building_names()):
            prefix = 'Selected_Buildings'
        else:
            prefix = 'District'
        file_name = "%s_%s" % (prefix, self.id())
        return self.locator.get_timeseries_plots_file(file_name, self.category_path)

    def remove_unused_fields(self, data, fields):
        """
        Helper method that, given a data frame and a list of fields in that data frame, returns the subset of those
        fields that actually have data.

        FIXME: what about columns with negative values?
        """
        import numpy as np
        fields = [field for field in fields if field in data.columns]
        return [field for field in fields if np.isclose(data[field].sum(), 1e-8)==False]

    def calc_graph(self):
        """Calculate a plotly Data object as to be passed to the data attribute of Figure"""
        raise NotImplementedError('Subclass needs to implement calc_graph for plot!')

    def calc_table(self):
        """Calculates a pandas.Dataframe to display as table."""
        raise NotImplementedError('This plot has no table')

    def plot(self, auto_open=False):
        """Plots the graphs to the filename (see output_path)"""
        if self.missing_input_files():
            raise MissingInputDataException("Dear developer: Run check_input_files() first, before plotting!")
        # PLOT
        template_path = os.path.join(os.path.dirname(__file__), 'plot.html')
        template = jinja2.Template(open(template_path, 'r').read())
        plot_html = template.render(plot_div=self.plot_div(), table_div=self.table_div(), title=self.title)
        with open(self.output_path, 'w') as f:
            f.write(plot_html)

        print("Plotted '%s' to %s" % (self.name, self.output_path))
        if auto_open:
            import webbrowser
            webbrowser.open(self.output_path)

    def plot_div(self):
        """Return the plot as an html <div/> for use in the dashboard. Override this method in subclasses"""
        if self.missing_input_files():
            raise MissingInputDataException("Dear developer: Run check_input_files() first, before plotting!")
        return self.cache.lookup_plot_div(self, self._plot_div_producer)

    def _plot_div_producer(self):
        fig = self._plot_figure_producer()
        fig['layout'].update({
            'margin': dict(l=50, r=50, t=50, b=50),
            'hovermode': 'closest',
            'font': dict(size=10),
            'yaxis': dict(hoverformat=".2f")
        })
        div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
        return div

    def _plot_figure_producer(self):
        try:
            plotly_data = self.cache.lookup_plot_data(self, self.calc_graph)
            return plotly.graph_objs.Figure(data=plotly_data, layout=self.layout)
        except NotImplementedError:  # if self.calc_graph() is not implemented
            return None

    def plot_data_to_file(self):
        import pandas as pd
        import collections
        import re

        plot_figure = self._plot_figure_producer()

        # Return None if plotly figure does not exist
        if plot_figure is None:
            return None

        plotly_data = plot_figure.data
        x_axis = plot_figure['layout']['xaxis']['title']
        y_axis = plot_figure['layout']['yaxis']['title']

        data = []
        scatter_plots = collections.OrderedDict()
        for trace in plotly_data:
            name = trace.get('name')
            x = trace.get('x')
            y = trace.get('y')
            if x is not None and y is not None and len(x) == len(y):
                if trace.yaxis:  # Assign correct title if plot contains multiple y_axis
                    y_axis = plot_figure['layout']['yaxis{}'.format(trace.yaxis.split('y')[1])]['title']

                if trace.type == 'bar':
                    column_name = name
                    units = re.search(r'\[.*?\]', y_axis)
                    if units:
                        column_name = '{} {}'.format(name, units.group())
                    df = pd.DataFrame({x_axis: list(x), column_name: list(y)}).set_index(x_axis)
                    data.append(df)
                elif trace.type == 'scattergl' and name is not None:
                    column_name = y_axis
                    df = pd.DataFrame({x_axis: list(x), column_name: list(y)}).set_index(x_axis)
                    scatter_plots[name] = df

        if data:
            data = pd.concat(data, axis=1)
            # Try to merge any scatter plots with bar data which have the same index name
            for data_name, scatter_data in scatter_plots.items():
                try:
                    data = pd.concat([data, scatter_data], axis=1)
                except Exception as e:
                    print(e)
            # Export data as .csv
            data.to_csv(os.path.splitext(self.output_path)[0] + '.csv')
        elif scatter_plots:
            # Export data as .xlsx
            with pd.ExcelWriter(os.path.splitext(self.output_path)[0] + '.xlsx') as writer:
                for data_name, scatter_data in scatter_plots.items():
                    sheet_name = data_name[:31]  # Sheet name cannot be more than 31 characters
                    scatter_data.to_excel(writer, sheet_name=sheet_name)
        else:  # Return None if could not parse any data from plot
            data = None
        return data

    def table_div(self):
        """Returns the html div for a table, or an empty string if no table is to be produced"""
        if self.missing_input_files():
            raise MissingInputDataException("Dear developer: Run check_input_files() first, before plotting!")
        return self.cache.lookup_table_div(self, self._table_div_producer)

    def _table_div_producer(self):
        """Default producer for table divs (override if you need more control)"""
        try:
            table_df = self.calc_table()
            template_path = os.path.join(os.path.dirname(__file__), 'table.html')
            template = jinja2.Template(open(template_path, 'r').read())
            table_html = template.render(table_df=table_df)
            return table_html
        except NotImplementedError:
            return ''

    @classmethod
    def get_default_parameters(cls, config):
        """Return a dictionary of parameters taken by using the values in the config file"""
        return {
            k: config.get(v)
            for k, v in cls.expected_parameters.items()
        }

    def process_buildings_parameter(self):
        """
        Make sure the buildings parameter contains only buildings in the zone. Returns (and updates) the parameter.
        """
        # all plots in this category use the buildings parameter. make it easier to access
        # handle special case of buildings... (only allow buildings for the scenario in question)
        zone_building_names = self.locator.get_zone_building_names()

        if not self.parameters['buildings']:
            self.parameters['buildings'] = zone_building_names
        self.parameters['buildings'] = ([b for b in self.parameters['buildings'] if
                                         b in zone_building_names]
                                        or zone_building_names)
        return self.parameters['buildings']
