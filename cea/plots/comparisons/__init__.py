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
label = 'Scenario comparisons'

class ComparisonsPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "comparisons"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {'urban-energy-system-scenarios':'plots-scenario-comparisons:urban-energy-system-scenarios'}

    def __init__(self, project, parameters, cache):
        """
        :param project: The project to base plots on (some plots span scenarios)
        :param parameters: The plot parameters as, e.g., per the dashboard.yml file
        :param cea.plots.PlotCache cache: a PlotCache instance for speeding up plotting
        """
        super(ComparisonsPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('testing', 'comparisons')
        self.project = project
        self.urban_energy_system_scenarios = self.parameters['urban-energy-system-scenarios']
        self.urban_scenarios, \
        self.energy_system_scenarios_generation,\
        self.energy_system_scenarios_individual = self.calc_input_variables()

    def calc_input_variables(self):
        urban_scenarios = []
        energy_system_scenarios_generation = []
        energy_system_scenarios_individual = []
        for urban_and_energy_scenario in np.array(self.urban_energy_system_scenarios).reshape(3, 3):
            urban_scenarios.append(urban_and_energy_scenario[0])
            energy_system_scenarios_generation.append(urban_and_energy_scenario[1])
            energy_system_scenarios_individual.append(urban_and_energy_scenario[2])

        return urban_scenarios, energy_system_scenarios_generation, energy_system_scenarios_individual

    @cea.plots.cache.cached
    def preprocessing_annual_costs_scenarios(self):
        # Import multi-criteria data
        # local variables
        data_processed = pd.DataFrame()
        for urban_scenario_name, generation, individual in zip(self.urban_scenarios, \
                                                           self.energy_system_scenarios_generation, \
                                                           self.energy_system_scenarios_individual):
            path_to_scenario = os.path.join(self.project, urban_scenario_name)
            locator = cea.inputlocator.InputLocator(path_to_scenario)
            # if there is no generation or individual indicated use the baseline
            if generation == "none" or individual == "none":  # use the original system
                scenario_name = urban_scenario_name + " - System original"
                data_building_costs = pd.read_csv(locator.get_costs_operation_file())
                data_raw_df = pd.DataFrame(data_building_costs.sum(axis=0)).T
            else:  # if there is a geneartion and individual indicated
                scenario_name = urban_scenario_name + " - System " + individual
                data_raw_df = pd.read_csv(locator.get_optimization_slave_total_performance(individual, generation))

            data_raw_df['scenario_name'] = scenario_name
            data_processed = pd.concat([data_processed, data_raw_df], sort=True, ignore_index=True)

        return data_processed

    @property
    def locator(self):
        #there is no need of a locator here as there are many scenarios to compare from
        return cea.inputlocator.InputLocator(os.path.join(self.project, self.urban_scenarios[0]))

