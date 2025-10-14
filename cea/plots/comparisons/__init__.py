



import os

import pandas as pd

import cea.config
import cea.inputlocator
import cea.plots.cache
from cea.plots.base import PlotBase

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

class ComparisonsPlotBase(PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "comparisons"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {'scenarios-and-systems':'plots-comparisons:scenarios-and-systems',
                           'normalization': 'plots:normalization',
                           }

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

    @property
    def locator(self):
        """
        :return: cea.inputlocator.InputLocator
        """
        return cea.inputlocator.InputLocator(os.path.join(self.project, self.scenarios_and_systems[0][1]))

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
                data_raw_df = self.normalize_data_costs(data_raw_df, self.normalization, self.analysis_fields)
            else:
                data_raw_df = pd.read_csv(locator_scenario.get_optimization_slave_total_performance(individual, generation))
                data_raw_df = self.normalize_data_costs(data_raw_df, self.normalization, self.analysis_fields)

            data_raw_df['scenario_name'] = scenario_and_system
            data_processed = pd.concat([data_processed, data_raw_df], sort=True, ignore_index=True)
        return data_processed

    @cea.plots.cache.cached
    def preprocessing_annual_emissions_scenarios(self):
        # Import multi-criteria data
        # local variables
        data_processed = pd.DataFrame()
        for scenario_and_system, scenario_name, generation, individual, locator_scenario in self.scenarios_and_systems:
            # get data
            path_to_scenario = os.path.join(self.project, scenario_name)
            locator_scenario = cea.inputlocator.InputLocator(path_to_scenario)

            if generation == "today":
                data_building_emissions = pd.read_csv(locator_scenario.get_lca_operation()).sum(axis=0)
                data_building_emissions['GHG_sys_embodied_tonCO2yr'] = pd.read_csv(self.locator.get_lca_embodied())['GHG_sys_embodied_tonCO2yr'].sum()
                data_raw_df = pd.DataFrame(data_building_emissions).T
                data_raw_df = self.normalize_data_emissions(data_raw_df, self.normalization, self.analysis_fields)
            else:
                data_raw_df = pd.read_csv(locator_scenario.get_optimization_slave_total_performance(individual, generation))
                data_raw_df = self.normalize_data_emissions(data_raw_df, self.normalization, self.analysis_fields)

            data_raw_df['scenario_name'] = scenario_and_system
            data_processed = pd.concat([data_processed, data_raw_df], sort=True, ignore_index=True)
        return data_processed

    def normalize_data_costs(self, data_processed, normalization, analysis_fields):
        if normalization == "gross floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['GFA_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
        elif normalization == "net floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['Aocc_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
        elif normalization == "air conditioned floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['Af_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
        elif normalization == "building occupancy":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['people0'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
        return data_processed

    def normalize_data_emissions(self, data_processed, normalization, analysis_fields):
        if normalization == "gross floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['GFA_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_district_scale_tonCO2'] = data_processed['GHG_sys_district_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_building_scale_tonCO2'] = data_processed['GHG_sys_building_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_embodied_tonCO2yr'] = data_processed['GHG_sys_embodied_tonCO2yr'] * 1000  # convert to kg
        elif normalization == "net floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['Aocc_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_district_scale_tonCO2'] = data_processed['GHG_sys_district_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_building_scale_tonCO2'] = data_processed['GHG_sys_building_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_embodied_tonCO2yr'] = data_processed['GHG_sys_embodied_tonCO2yr'] * 1000  # convert to kg
        elif normalization == "air conditioned floor area":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['Af_m2'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_district_scale_tonCO2'] = data_processed['GHG_sys_district_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_building_scale_tonCO2'] = data_processed['GHG_sys_building_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_embodied_tonCO2yr'] = data_processed['GHG_sys_embodied_tonCO2yr'] * 1000  # convert to kg
        elif normalization == "building occupancy":
            data = pd.read_csv(self.locator.get_total_demand())
            normalization_factor = sum(data['people0'])
            data_processed = data_processed.apply(
                lambda x: x / normalization_factor if x.name in analysis_fields else x)
            data_processed['GHG_sys_district_scale_tonCO2'] = data_processed['GHG_sys_district_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_building_scale_tonCO2'] = data_processed['GHG_sys_building_scale_tonCO2'] * 1000  # convert to kg
            data_processed['GHG_sys_embodied_tonCO2yr'] = data_processed['GHG_sys_embodied_tonCO2yr'] * 1000  # convert to kg
        return data_processed
