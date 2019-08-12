from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import cea.plots.cache

"""
Implements py:class:`cea.plots.OptimizationOverviewPlotBase` as a base class for all plots in the category "optimization-overview" and also
set's the label for that category.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'Optimization overview'


class GenerationPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "optimization"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'multicriteria': 'plots-optimization:multicriteria',
        'generation': 'plots-optimization:generation',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        """

        :param project: The project to base plots on (some plots span scenarios)
        :param parameters: The plot parameters as, e.g., per the dashboard.yml file
        :param cea.plots.PlotCache cache: a PlotCache instance for speeding up plotting
        """
        super(GenerationPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('testing', 'optimization-overview')
        self.generation = self.parameters['generation']

    @cea.plots.cache.cached
    def process_generation_total_performance(self):
        # Import multi-criteria data
        if self.multi_criteria:
            try:
                data_processed = pd.read_csv(self.locator.get_multi_criteria_analysis(self.generation))
            except IOError:
                raise IOError("Please run the multi-criteria analysis tool first or set multi-criteria = False")

        else:
            data_processed = pd.read_csv(self.locator.get_optimization_generation_total_performance(self.generation))
        return data_processed


if __name__ == '__main__':
    # run all the plots in this category
    config = cea.config.Configuration()
    from cea.plots.categories import list_categories
    from cea.plots.cache import NullPlotCache, PlotCache
    import time


    def plot_category(cache):
        for category in list_categories():
            if category.label != label:
                continue
            print('category:', category.name, ':', category.label)
            for plot_class in category.plots:
                print('plot_class:', plot_class)
                parameters = {
                    k: config.get(v) for k, v in plot_class.expected_parameters.items()
                }
                plot = plot_class(config.project, parameters=parameters, cache=cache)
                assert plot.name, 'plot missing name: %s' % plot
                assert plot.category_name == category.name
                print('plot:', plot.name, '/', plot.id(), '/', plot.title)

                # plot the plot!
                plot.plot()


    null_plot_cache = NullPlotCache()
    plot_cache = PlotCache(config.project)

    # test plots with cache
    t0 = time.time()
    for i in range(3):
        plot_category(plot_cache)
    time_with_cache = (time.time() - t0) / 3

    # test plots without cache
    t0 = time.time()
    for i in range(3):
        plot_category(null_plot_cache)
    time_without_cache = (time.time() - t0) / 3

    print('Average without cache: %.2f seconds' % time_without_cache)
    print('Average with cache: %.2f seconds' % time_with_cache)
