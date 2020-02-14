from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import numpy as np
import cea.plots.cache

"""
Implements py:class:`cea.plots.OptimizationOverviewPlotBase` as a base class for all plots in the category "optimization-overview" and also
set's the label for that category.
"""

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'H - Scenario comparisons'

class ComparisonsPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "comparisons"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {'scenarios-and-systems':'plots-comparisons:scenarios-and-systems'}

    def __init__(self, project, parameters, cache):
        """
        :param project: The project to base plots on (some plots span scenarios)
        :param parameters: The plot parameters as, e.g., per the dashboard.yml file
        :param cea.plots.PlotCache cache: a PlotCache instance for speeding up plotting
        """
        super(ComparisonsPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('testing', 'comparisons')
        self.project = project
        self.scenarios_and_systems = [(x, x.rsplit('_', 3)[0], x.rsplit('_', 3)[2], x.rsplit('_', 3)[3],
                                       cea.inputlocator.InputLocator(os.path.join(self.project, x.rsplit('_', 3)[0])))
                                      for x in self.parameters['scenarios-and-systems']]

    @cea.plots.cache.cached
    def preprocessing_annual_costs_scenarios(self):
        # Import multi-criteria data
        # local variables
        data_processed = pd.DataFrame()
        for scenario_and_system, scenario_name, generation, individual, locator_scenario in self.scenarios_and_systems:
            # get data
            path_to_scenario = os.path.join(self.project, scenario_name)
            locator_scenario = cea.inputlocator.InputLocator(path_to_scenario)

            if generation == "today":
                data_building_costs = pd.read_csv(locator_scenario.get_costs_operation_file())
                data_raw_df = pd.DataFrame(data_building_costs.sum(axis=0)).T
                data_raw_df['scenario_name'] = scenario_name+"<br>"+"sys_"+"today"
            else:
                data_raw_df = pd.read_csv(locator_scenario.get_optimization_slave_total_performance(individual, generation))
                data_raw_df['scenario_name'] = scenario_name+"<br>"+"sys_"+generation+"_"+individual

            data_raw_df['scenario_name'] = scenario_and_system
            data_processed = pd.concat([data_processed, data_raw_df], sort=True, ignore_index=True)
        return data_processed
