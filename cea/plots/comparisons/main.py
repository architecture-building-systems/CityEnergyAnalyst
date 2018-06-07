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
    print(config.plots.scenarios)
    if not len(config.plots.scenarios) > 1:
        raise cea.ConfigError('Comparison plots require at least two scenarios to compare. See config.plots.scenarios.')

    # local variables
    scenarios = [os.path.join(config.scenario, '..', scenario) for scenario in config.plots.scenarios]

    # initialize class
    plots = Plots(scenarios)
    plots.demand_comparison()
    plots.demand_intensity_comparison()
    plots.demand_comparison_final()
    plots.demand_intensity_comparison_final()
    plots.operation_costs_comparison()
    plots.emissions_comparison()
    plots.primary_energy_comparison()
    plots.emissions_intensity_comparison()
    plots.primary_energy_intensity_comparison()


class Plots():

    def __init__(self, scenarios):
        self.analysis_fields_demand = ["DH_hs_MWhyr", "DH_ww_MWhyr",
                                       'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                                       "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                                       'PV_MWhyr', 'GRID_MWhyr',
                                       'NG_hs_MWhyr',
                                       'COAL_hs_MWhyr',
                                       'OIL_hs_MWhyr',
                                       'WOOD_hs_MWhyr',
                                       'NG_ww_MWhyr',
                                       'COAL_ww_MWhyr',
                                       'OIL_ww_MWhyr',
                                       'WOOD_ww_MWhyr',
                                       "E_sys_MWhyr",
                                        "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                        "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        self.analysis_fields_costs = ['DC_cs_cost_yr',
                                      'DC_cdata_cost_yr',
                                      'DC_cre_cost_yr',
                                      'DH_ww_cost_yr',
                                      'DH_hs_cost_yr',
                                      'SOLAR_ww_cost_yr',
                                      'SOLAR_hs_cost_yr',
                                      'GRID_cost_yr',
                                      'PV_cost_yr',
                                      'NG_hs_cost_yr',
                                      'COAL_hs_cost_yr',
                                      'OIL_hs_cost_yr',
                                      'WOOD_hs_cost_yr',
                                      'NG_ww_cost_yr',
                                      'COAL_ww_cost_yr',
                                      'OIL_ww_cost_yr',
                                      'WOOD_ww_cost_yr'
                                      ]
        self.analysis_fields_costs_m2 = ['DC_cs_cost_m2yr',
                                         'DC_cdata_cost_m2yr',
                                         'DC_cre_cost_m2yr',
                                         'DH_ww_cost_m2yr',
                                         'DH_hs_cost_m2yr',
                                         'SOLAR_ww_cost_m2yr',
                                         'SOLAR_hs_cost_m2yr',
                                         'GRID_cost_m2yr',
                                         'PV_cost_m2yr',
                                         'NG_hs_cost_m2yr',
                                         'COAL_hs_cost_m2yr',
                                         'OIL_hs_cost_m2yr',
                                         'WOOD_hs_cost_m2yr',
                                         'NG_ww_cost_m2yr',
                                         'COAL_ww_cost_m2yr',
                                         'OIL_ww_cost_m2yr',
                                         'WOOD_ww_cost_m2yr']
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

    def erase_zeros(self, data, fields):
        analysis_fields_no_zero = []
        for field in fields:
            sum = data[field].sum()
            if sum >0 :
                analysis_fields_no_zero += [field]
        return analysis_fields_no_zero

    def demand_comparison(self):
        title = "Energy Demand of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_demand")
        data = self.data_processed_demand
        analysis_fields = ["E_sys_MWhyr","Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                        "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def demand_intensity_comparison(self):
        title = "Energy Use Intensity of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_use_intensity")
        data = self.data_processed_demand
        analysis_fields = ["E_sys_MWhyr","Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                        "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_use_intensity(data, analysis_fields, title, output_path)
        return plot

    def demand_comparison_final(self):
        title = "Energy Demand of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_demand_supply")
        data = self.data_processed_demand
        analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr",
                           'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                           "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                           'PV_MWhyr', 'GRID_MWhyr',
                           'NG_hs_MWhyr',
                           'COAL_hs_MWhyr',
                           'OIL_hs_MWhyr',
                           'WOOD_hs_MWhyr',
                           'NG_ww_MWhyr',
                           'COAL_ww_MWhyr',
                           'OIL_ww_MWhyr',
                           'WOOD_ww_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def demand_intensity_comparison_final (self):
        title = "Energy Use Intensity of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_use_intensity_supply")
        data = self.data_processed_demand
        analysis_fields =  ["DH_hs_MWhyr", "DH_ww_MWhyr",
                           'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                           "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                           'PV_MWhyr', 'GRID_MWhyr',
                           'NG_hs_MWhyr',
                           'COAL_hs_MWhyr',
                           'OIL_hs_MWhyr',
                           'WOOD_hs_MWhyr',
                           'NG_ww_MWhyr',
                           'COAL_ww_MWhyr',
                           'OIL_ww_MWhyr',
                           'WOOD_ww_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_use_intensity(data, analysis_fields, title, output_path)
        return plot

    def operation_costs_comparison(self):
        title = "Operation Costs of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_operation_costs")
        data = self.data_processed_costs
        analysis_fields = self.erase_zeros(data, self.analysis_fields_costs)
        plot = operation_costs_district(data, analysis_fields, title, output_path)
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
