from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import cea.plots.cache
from cea.analysis.multicriteria.main import multi_criteria_main

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
label = 'Optimization'


class GenerationPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "optimization"

    # default parameters for plots in this category - override if your plot differs

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
    def process_today_system_performance(self):
        data_processed = pd.DataFrame()
        data_processed_costs = pd.read_csv(self.locator.get_costs_operation_file())
        data_processed['GHG_sys_tonCO2'] = [pd.read_csv(self.locator.get_lca_operation())['GHG_sys_tonCO2'].sum()]
        data_processed['TAC_sys_USD'] = [data_processed_costs['TAC_sys_USD'].sum()]
        data_processed['Capex_total_sys_USD'] = [data_processed_costs['Capex_total_sys_USD'].sum()]
        return data_processed

    @cea.plots.cache.cached
    def process_generation_total_performance_pareto_with_multi(self):
        multi_criteria_main(self.locator,
                            self.generation,
                            self.weight_annualized_capital_costs,
                            self.weight_total_capital_costs,
                            self.weight_annual_operation_costs,
                            self.weight_annual_emissions,
                            )
        data_processed = pd.read_csv(self.locator.get_multi_criteria_analysis(self.generation))
        return data_processed

    @cea.plots.cache.cached
    def process_generation_total_performance_pareto(self):
        data_processed = pd.read_csv(self.locator.get_optimization_generation_total_performance_pareto(self.generation))
        data_processed['GHG_sys_embodied_tonCO2'] = pd.read_csv(self.locator.get_lca_embodied())['GHG_sys_embodied_tonCO2'].sum()
        data_processed['GHG_sys_mobility_tonCO2'] = pd.read_csv(self.locator.get_lca_mobility())['GHG_sys_mobility_tonCO2'].sum()
        return data_processed

    def normalize_data(self, data_processed, normalization, analysis_fields):
        if normalization == "gross floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalizatioon_factor = sum(data['GFA_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_tonCO2'] = data_processed['GHG_sys_tonCO2'] * 1000  # convert to kg
        elif normalization == "net floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalizatioon_factor = sum(data['Aocc_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_tonCO2'] = data_processed['GHG_sys_tonCO2'] * 1000  # convert to kg
        elif normalization == "air conditioned floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalizatioon_factor = sum(data['Af_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_tonCO2'] = data_processed['GHG_sys_tonCO2'] * 1000  # convert to kg
        elif normalization == "building occupancy":
            data = pd.read_csv(self.locator.get_total_demand())
            normalizatioon_factor = sum(data['people0'])
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_tonCO2'] = data_processed['GHG_sys_tonCO2'] * 1000  # convert to kg

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
