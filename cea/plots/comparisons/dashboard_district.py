"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os

import pandas as pd
from cea.plots.comparisons.primary_energy_intensity import primary_energy_intensity

import cea.config
import cea.inputlocator
from cea.plots.comparisons.emissions import emissions
from cea.plots.comparisons.emissions_intensity import emissions_intensity
from cea.plots.comparisons.energy_demand import energy_demand_district
from cea.plots.comparisons.energy_use_intensity import energy_use_intensity
from cea.plots.comparisons.operation_costs import operation_costs_district
from cea.plots.comparisons.primary_energy import primary_energy

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(config):
    # local variables
    scenarios = config.dashboard.scenarios

    # initialize class
    plots = Plots(scenarios)
    plots.demand_comparison()
    plots.demand_intensity_comparison()
    plots.operation_costs_comparison()
    plots.emissions_comparison()
    plots.primary_energy_comparison()
    plots.emissions_intensity_comparison()
    plots.primary_energy_intensity_comparison()


class Plots():

    def __init__(self, scenarios):
        self.analysis_fields_demand = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
        self.analysis_fields_costs = ['Qhsf_cost_yr', 'Qwwf_cost_yr', 'QCf_cost_yr', 'Ef_cost_yr']
        self.analysis_fields_costs_m2 = ['Qhsf_cost_m2yr', 'Qwwf_cost_m2yr', 'QCf_cost_m2yr', 'Ef_cost_m2yr']
        self.analysis_fields_emissions = ['E_ghg_ton', 'O_ghg_ton', 'M_ghg_ton']
        self.analysis_fields_emissions_m2 = ['E_ghg_kgm2', 'O_ghg_kgm2', 'M_ghg_kgm2']
        self.analysis_fields_primary_energy = ['E_nre_pen_GJ', 'O_nre_pen_GJ', 'M_nre_pen_GJ']
        self.analysis_fields_primary_energy_m2 = ['E_nre_pen_MJm2', 'O_nre_pen_MJm2', 'M_nre_pen_MJm2']
        self.scenarios = scenarios
        self.locator = cea.inputlocator.InputLocator(scenarios[0])
        self.data_processed_demand = self.preprocessing_demand_scenarios()
        self.data_processed_costs = self.preprocessing_costs_scenarios()
        self.data_processed_life_cycle = self.preprocessing_lca_scenarios()

    def preprocessing_demand_scenarios(self):
        data_processed = pd.DataFrame()
        for i, scenario in enumerate(self.scenarios):
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            data_raw = (pd.read_csv(locator.get_total_demand())[self.analysis_fields_demand + ["GFA_m2"]]).sum(axis=0)
            data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T
            data_processed = data_processed.append(data_raw_df)
        return data_processed

    def preprocessing_costs_scenarios(self):
        data_processed = pd.DataFrame()
        for scenario in self.scenarios:
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            data_raw = (pd.read_csv(locator.get_costs_operation_file())[
                self.analysis_fields_costs + self.analysis_fields_costs_m2]).sum(axis=0)
            data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T
            data_processed = data_processed.append(data_raw_df)
        return data_processed

    def preprocessing_lca_scenarios(self):
        data_processed = pd.DataFrame()
        for scenario in self.scenarios:
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            data_raw_embodied_emissions = pd.read_csv(locator.get_lca_embodied()).set_index('Name')
            data_raw_operation_emissions = pd.read_csv(locator.get_lca_operation()).set_index('Name')
            data_raw_mobility_emissions = pd.read_csv(locator.get_lca_mobility()).set_index('Name')
            data_raw = data_raw_embodied_emissions.join(data_raw_operation_emissions, lsuffix='y').join(
                data_raw_mobility_emissions, lsuffix='y2')
            data_raw = data_raw.sum(axis=0)
            data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T
            data_processed = data_processed.append(data_raw_df)
        return data_processed

    def demand_comparison(self):
        title = "Energy Demand of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_demand")
        data = self.data_processed_demand
        plot = energy_demand_district(data, self.analysis_fields_demand, title, output_path)
        return plot

    def demand_intensity_comparison(self):
        title = "Energy Use Intensity of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_use_intensity")
        data = self.data_processed_demand
        plot = energy_use_intensity(data, self.analysis_fields_demand, title, output_path)
        return plot

    def operation_costs_comparison(self):
        title = "Operation Costs of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_operation_costs")
        data = self.data_processed_costs
        plot = operation_costs_district(data, self.analysis_fields_costs, title, output_path)
        return plot

    def primary_energy_comparison(self):
        title = "Primary Energy Consumption of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_primary_energy")
        data = self.data_processed_life_cycle
        plot = primary_energy(data, self.analysis_fields_primary_energy, title, output_path)
        return plot

    def primary_energy_intensity_comparison(self):
        title = "Primary Energy Consumption of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_primary_energy_intensity")
        data = self.data_processed_life_cycle
        plot = primary_energy_intensity(data, self.analysis_fields_primary_energy_m2, title, output_path)
        return plot

    def emissions_comparison(self):
        title = "Green House Gas Emissions of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_emissions")
        data = self.data_processed_life_cycle
        plot = emissions(data, self.analysis_fields_emissions, title, output_path)
        return plot

    def emissions_intensity_comparison(self):
        title = "Green House Gas Emissions of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_emissions_intensity")
        data = self.data_processed_life_cycle
        plot = emissions_intensity(data, self.analysis_fields_emissions_m2, title, output_path)
        return plot


def main(config):
    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plots_main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
