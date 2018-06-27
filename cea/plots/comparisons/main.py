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
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf
from cea.plots.comparisons.emissions import emissions
from cea.plots.comparisons.emissions_intensity import emissions_intensity
from cea.plots.comparisons.energy_demand import energy_demand_district
from cea.plots.comparisons.energy_use_intensity import energy_use_intensity
from cea.plots.comparisons.operation_costs import operation_costs_district
from cea.plots.comparisons.primary_energy import primary_energy
from cea.plots.comparisons.occupancy_types import occupancy_types_district
from cea.plots.comparisons.energy_supply_mix import energy_supply_mix

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(config):
    print(config.plots_scenario_comparisons.scenarios)
    if not len(config.plots_scenario_comparisons.scenarios) > 1:
        raise cea.ConfigError('Comparison plots require at least two scenarios to compare. See config.plots.scenarios.')

    # local variables
    # TODO: We need to create the plots and integrate the case whne none generations/ individuals etc,
    # the current status is for Daren to create the interface.
    project = config.plots_scenario_comparisons.project
    scenario_baseline = config.plots_scenario_comparisons.base_scenario
    scenario_base_path = os.path.join(project, scenario_baseline.split("/")[0])
    generation_base = scenario_baseline.split('/')[1] if len(scenario_baseline.split('/'))>1 else "none"
    individual_base = scenario_baseline.split('/')[2] if len(scenario_baseline.split('/'))>1 else "none"
    scenarios_path = [os.path.join(project, scenario.split("/")[0]) for scenario in config.plots_scenario_comparisons.scenarios]
    generations = [scenario.split('/')[1] if len(scenario.split('/')) > 1 else "none"
                   for scenario in config.plots_scenario_comparisons.scenarios]
    individuals = [scenario.split('/')[2] if len(scenario.split('/')) > 1 else "none"
                   for scenario in config.plots_scenario_comparisons.scenarios]

    # initialize class
    category = "comparison"
    plots = Plots(scenario_base_path, scenarios_path)
    plots.demand_comparison(category)
    plots.demand_intensity_comparison(category)
    plots.demand_comparison_final(category)
    plots.demand_intensity_comparison_final(category)
    plots.operation_costs_comparison(category)
    plots.emissions_comparison(category)
    plots.primary_energy_comparison(category)
    plots.emissions_intensity_comparison(category)
    plots.primary_energy_intensity_comparison(category)
    plots.occupancy_types_comparison(category)
    plots.operation_costs_comparison_intensity(category)

    # capex_opex_comparison(self, category) ##TODO: create data inputs for these new two plots.
    # energy_mix_comparison(self, category)



class Plots(object):

    def __init__(self, scenario_base, scenarios):
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
                                        "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr',
                                       "Eal_MWhyr",
                                       "Epro_MWhyr",
                                       "Edata_MWhyr",
                                       "E_cs_MWhyr",
                                       "E_hs_MWhyr",
                                       "E_ww_MWhyr",
                                       "Eaux_MWhyr",
                                       "E_cdata_MWhyr",
                                       "E_cre_MWhyr"]
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
        self.analysis_fields_occupancy_type = ['COOLROOM', 'FOODSTORE', 'GYM', 'HOSPITAL', 'HOTEL', 'INDUSTRIAL',
                                               'LIBRARY', 'MULTI_RES', 'OFFICE', 'PARKING', 'RESTAURANT', 'RETAIL',
                                               'SCHOOL', 'SERVERROOM', 'SINGLE_RES', 'SWIMMING']
        self.scenarios = [scenario_base] + scenarios
        self.locator = cea.inputlocator.InputLocator(scenario_base) # where to store the results
        self.data_processed_demand = self.preprocessing_demand_scenarios()
        self.data_processed_costs = self.preprocessing_costs_scenarios()
        self.data_processed_life_cycle = self.preprocessing_lca_scenarios()
        self.data_processed_occupancy_type = self.preprocessing_occupancy_type_comparison()

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

    def preprocessing_occupancy_type_comparison(self):

        data_processed = pd.DataFrame()
        for scenario in self.scenarios:
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            # read occupancy dbf of scenario
            district_occupancy_df = dbf_to_dataframe(locator.get_building_occupancy())
            district_occupancy_df.set_index('Name', inplace=True)
            # read total demand results for GFA of scenario
            district_gfa_df = pd.read_csv(locator.get_total_demand())[['GFA_m2'] + ["Name"]]
            district_gfa_df.set_index('Name', inplace=True)
            # multiply dataframes
            # https://stackoverflow.com/questions/21022865/pandas-elementwise-multiplication-of-two-dataframes
            data_raw = pd.DataFrame(district_occupancy_df.values * district_gfa_df.values,
                                    columns=district_occupancy_df.columns, index=district_occupancy_df.index)
            # sum per function
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

    def demand_comparison(self, category):
        title = "Energy demand per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_demand", category)
        data = self.data_processed_demand.copy()
        analysis_fields = ["E_sys_MWhyr","Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                        "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def demand_intensity_comparison(self, category):
        title = "Energy use intensity per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_use_intensity", category)
        data = self.data_processed_demand.copy()
        analysis_fields = ["E_sys_MWhyr","Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                        "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_use_intensity(data, analysis_fields, title, output_path)
        return plot

    def demand_comparison_final(self, category):
        title = "Energy supply per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_supply", category)
        data = self.data_processed_demand.copy()
        analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr",
                           'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                           "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                           'PV_MWhyr',
                           'NG_hs_MWhyr',
                           'COAL_hs_MWhyr',
                           'OIL_hs_MWhyr',
                           'WOOD_hs_MWhyr',
                           'NG_ww_MWhyr',
                           'COAL_ww_MWhyr',
                           'OIL_ww_MWhyr',
                           'WOOD_ww_MWhyr',
                           "Eal_MWhyr",
                           "Epro_MWhyr",
                           "Edata_MWhyr",
                           "E_cs_MWhyr",
                           "E_hs_MWhyr",
                           "E_ww_MWhyr",
                           "Eaux_MWhyr",
                           "E_cdata_MWhyr",
                           "E_cre_MWhyr"
                           ]
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def demand_intensity_comparison_final(self, category):
        title = "Energy supply intensity per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_supply_intensity", category)
        data = self.data_processed_demand.copy()
        analysis_fields =  ["DH_hs_MWhyr", "DH_ww_MWhyr",
                           'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                           "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                           'PV_MWhyr',
                           'NG_hs_MWhyr',
                           'COAL_hs_MWhyr',
                           'OIL_hs_MWhyr',
                           'WOOD_hs_MWhyr',
                           'NG_ww_MWhyr',
                           'COAL_ww_MWhyr',
                           'OIL_ww_MWhyr',
                           'WOOD_ww_MWhyr',
                            "Eal_MWhyr",
                            "Epro_MWhyr",
                            "Edata_MWhyr",
                            "E_cs_MWhyr",
                            "E_hs_MWhyr",
                            "E_ww_MWhyr",
                            "Eaux_MWhyr",
                            "E_cdata_MWhyr",
                            "E_cre_MWhyr"
                            ]
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_use_intensity(data, analysis_fields, title, output_path)
        return plot

    def operation_costs_comparison(self, category):
        title = "Operation costs per scenario"
        yaxis_title = "Operation costs [$USD(2015)/yr]"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_operation_costs", category)
        data = self.data_processed_costs.copy()
        analysis_fields = self.erase_zeros(data, self.analysis_fields_costs)
        plot = operation_costs_district(data, analysis_fields, title, yaxis_title, output_path)
        return plot

    def operation_costs_comparison_intensity(self, category):
        title = "Operation costs relative to GFA per scenario"
        yaxis_title = "Operation costs [$USD(2015)/m2.yr]"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_operation_costs_intensity", category)
        data = self.data_processed_costs.copy()
        analysis_fields = self.erase_zeros(data, self.analysis_fields_costs_m2)
        plot = operation_costs_district(data, analysis_fields, title, yaxis_title, output_path)
        return plot

    def primary_energy_comparison(self, category):
        title = "Primary energy use intensity (non-renewable) per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_primary_energy", category)
        data = self.data_processed_life_cycle.copy()
        plot = primary_energy(data, self.analysis_fields_primary_energy, title, output_path)
        return plot

    def primary_energy_intensity_comparison(self, category):
        title = "Primary energy use intensity (non-renewable) per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_primary_energy_intensity", category)
        data = self.data_processed_life_cycle.copy()
        plot = primary_energy_intensity(data, self.analysis_fields_primary_energy_m2, title, output_path)
        return plot

    def emissions_comparison(self, category):
        title = "Green house gas emissions per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_emissions", category)
        data = self.data_processed_life_cycle.copy()
        plot = emissions(data, self.analysis_fields_emissions, title, output_path)
        return plot

    def emissions_intensity_comparison(self, category):
        title = "Green house gas emissions intensity per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_emissions_intensity", category)
        data = self.data_processed_life_cycle.copy()
        plot = emissions_intensity(data, self.analysis_fields_emissions_m2, title, output_path)
        return plot

    def occupancy_types_comparison(self, category):
        title = "Occupancy Types of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_occupancy_types", category)
        data = self.data_processed_occupancy_type.copy()
        analysis_fields = self.erase_zeros(data, self.analysis_fields_occupancy_type)
        plot = occupancy_types_district(data, analysis_fields, title, output_path)
        return plot

    def capex_opex_comparison(self, category):
        title = "Annualized CAPEX vs. OPEX per scenario"
        yaxis_title = "Costs [$USD(2015)/yr]"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_costs", category)
        data = [] ##TODO: to create dataframe to make these costs show up. (columns are the analysis fields, rows are the sceanrios, the index should be the name of the scenario)
        analysis_fields = [] ##TODO: add list of all analyzis fields
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = operation_costs_district(data, analysis_fields, title, yaxis_title, output_path)
        return plot

    def energy_mix_comparison(self, category):
        title = "Energy supply mix per scenario"
        yaxis_title = "Energy supply mix [%]"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_supply_mix", category)
        data = []  ##TODO: to create dataframe to make these values show up. (columns are the analysis fields in MWH/yr, rows are the sceanrios, the index should be the name of the scenario)
        analysis_fields = [] ##TODO: add list of all analyzis fields
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_supply_mix(data, analysis_fields, title, yaxis_title, output_path)
        return plot


def main(config):
    plots_main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
