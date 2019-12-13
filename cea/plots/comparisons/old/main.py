"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import pandas as pd
from cea.plots.comparisons.old.primary_energy_intensity import primary_energy_intensity

import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe
from cea.plots.comparisons.old.emissions import emissions
from cea.plots.comparisons.old.emissions_intensity import emissions_intensity
from cea.plots.comparisons.old.energy_demand import energy_demand_district
from cea.plots.comparisons.old.energy_use_intensity import energy_use_intensity
from cea.plots.comparisons.old.operation_costs import operation_costs_district
from cea.plots.comparisons.old.primary_energy import primary_energy
from cea.plots.comparisons.old.occupancy_types import occupancy_types_district
import numpy as np


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def plots_main(config):

    if not len(config.plots_scenario_comparisons.urban_energy_system_scenarios) >= 2:
        raise cea.ConfigError('Comparison plots require at least two scenarios to compare. See config.plots.scenarios.')

    # local variables
    project = config.general.project
    categories = config.plots_scenario_comparisons.categories
    urban_and_energy_scenarios = config.plots_scenario_comparisons.urban_energy_system_scenarios
    category = "comparisons"

    # EXTRACT PATHS FROM SCENARIOS:
    #TODO: @Daren please convert this into a ListParameter in config, it is important that the dashboard can read the contents
    urban_scenarios = []
    energy_system_scenarios_generation = []
    energy_system_scenarios_individual = []
    for urban_and_energy_scenario in np.array(urban_and_energy_scenarios).reshape(3,3):
        urban_scenarios.append(urban_and_energy_scenario[0])
        energy_system_scenarios_generation.apppend(urban_and_energy_scenario[1])
        energy_system_scenarios_individual.apppend(urban_and_energy_scenario[2])


    plots = Plots(project, urban_scenarios, energy_system_scenarios_generation, energy_system_scenarios_individual, config)

    # create plots according to categories
    if "demand" in categories:
        plots.comparison_demand(category)  # the same independent of the supply scenario
        plots.comparison_demand_intensity(category)  # the same independent of the supply scenario

    if "supply_mix" in categories:
        plots.comparison_supply_mix(category)
        plots.comparison_supply_mix_intensity(category)

    if "costs_analysis" in categories:
        plots.CAPEX_vs_OPEX_comparison(category)
        plots.CAPEX_vs_OPEX_comparison_intensity(category)

    if "life_cycle_analysis" in categories:
        plots.comparison_emissions(category)
        plots.comparison_emissions_intensity(category)
        plots.comparison_primary_energy(category)
        plots.comparison_primary_energy_intensity(category)

    if "land_use" in categories:
        plots.occupancy_types_comparison(category)


class Plots(object):
    def __init__(self, project, urban_scenarios, energy_system_scenarios_generation, energy_system_scenarios_individual, config):
        self.project = project
        self.urban_scenarios = urban_scenarios
        self.energy_system_scenarios_generation = energy_system_scenarios_generation # where to store the results
        self.energy_system_scenarios_individual = energy_system_scenarios_individual
        self.config = config
        self.analysis_fields_demand = ["DH_hs_MWhyr", "DH_ww_MWhyr",
                                       'SOLAR_ww_MWhyr', 'SOLAR_hs_MWhyr',
                                       "DC_cs_MWhyr", 'DC_cdata_MWhyr', 'DC_cre_MWhyr',
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
        self.analysis_fields_costs = ['Opex_a_sys_connected_USD',
                                      'Opex_a_sys_disconnected_USD',
                                      'Capex_a_sys_disconnected_USD',
                                      'Capex_a_sys_connected_USD',
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

        # self.data_processed_demand = self.preprocessing_demand_scenarios()
        # self.data_processed_supply = self.preprocessing_supply_scenarios()
        self.data_processed_costs = self.preprocessing_costs_scenarios()
        # self.data_processed_life_cycle = self.preprocessing_lca_scenarios()
        # self.data_processed_occupancy_type = self.preprocessing_occupancy_type_comparison()

    def preprocessing_demand_scenarios(self):
        data_processed = pd.DataFrame()
        scenarios_clean = []
        for i, scenario_name in enumerate(self.scenarios_names):
            if scenario_name in scenarios_clean:
                scenario_name = scenario_name + "_duplicated_" + str(i)
            scenarios_clean.append(scenario_name)

        for scenario, scenario_name in zip(self.scenarios, scenarios_clean):
            locator = cea.inputlocator.InputLocator(scenario)
            data_raw = (pd.read_csv(locator.get_total_demand())[self.analysis_fields_demand + ["GFA_m2"]]).sum(axis=0)
            data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T
            data_processed = data_processed.append(data_raw_df)
        return data_processed

    def preprocessing_supply_scenarios(self):
        data_processed = pd.DataFrame()
        scenarios_clean = []
        for i, scenario in enumerate(self.scenarios_names):
            if scenario in scenarios_clean:
                scenario = scenario + "_duplicated_" + str(i)
            scenarios_clean.append(scenario)

        for scenario, generation, individual, gen_pointer, ind_pointer, scenario_name in zip(self.scenarios,
                                                                                             self.generations,
                                                                                             self.individuals,
                                                                                             self.generation_pointers,
                                                                                             self.individual_pointers,
                                                                                             scenarios_clean):
            locator = cea.inputlocator.InputLocator(scenario)
            if generation == "none" or individual == "none":
                data_raw = (pd.read_csv(locator.get_total_demand())[self.analysis_fields_demand + ["GFA_m2"]]).sum(
                    axis=0)
                data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T

                data_raw_df["E_PV_to_directload_MWhyr"] = data_raw_df[["PV_MWhyr"]].copy()
                data_raw_df["GRID_MWhyr"] = data_raw_df[["GRID_MWhyr"]].copy()
                data_raw_df["NG_CCGT_MWhyr"] = 0.0  ##TODO: fix in demand so there is for cooling systems
            else:
                data_raw_df = energy_mix_based_on_technologies_script(gen_pointer, ind_pointer,
                                                                      locator, self.network_type)
                # add gfa
                data_gfa = pd.read_csv(locator.get_total_demand())["GFA_m2"].sum(axis=0)
                data_raw_df["GFA_m2"] = data_gfa
                data_raw_df.index = [scenario_name]
            data_processed = data_processed.append(data_raw_df)
        return data_processed

    def preprocessing_costs_scenarios(self):
        # local variables
        data_processed = {}
        for urban_scenario_name, generation, individual in self.urban_scenarios,\
                                                           self.energy_system_scenarios_generation, \
                                                           self.energy_system_scenarios_individual:
            #if there is no generation or individual indicated use the baseline
            if generation == "none" or individual == "none": #use the original system
                scenario_name = urban_scenario_name + " - System original"
                locator = cea.inputlocator.InputLocator(urban_scenario_name)
                data_raw_df = pd.read_csv(locator.get_costs_operation_file())
            else: #if there is a geneartion and individual indicated
                scenario_name = urban_scenario_name + " - System "+individual
                data_raw_df = pd.read_csv(locator.get_optimization_slave_total_performance(individual, generation))

            #add name of scenario
            data_raw_df['scenario'] = scenario_name
            data_raw_df.set_index('scenario', inplace=True)
            data_processed

        return data_processed

    def preprocessing_lca_scenarios(self):
        data_processed = pd.DataFrame()
        scenarios_clean = []
        for i, scenario in enumerate(self.scenarios_names):
            if scenario in scenarios_clean:
                scenario = scenario + "_duplicated_" + str(i)
            scenarios_clean.append(scenario)

        for scenario, generation, individual, scenario_name in zip(self.scenarios, self.generations, self.individuals,
                                                                   scenarios_clean):
            locator = cea.inputlocator.InputLocator(scenario)
            data_raw_embodied_emissions = pd.read_csv(locator.get_lca_embodied()).set_index('Name')
            data_raw_mobility_emissions = pd.read_csv(locator.get_lca_mobility()).set_index('Name')

            if generation == "none" or individual == "none":
                data_raw_operation_emissions = pd.read_csv(locator.get_lca_operation()).set_index('Name')
                data_raw = data_raw_embodied_emissions.join(data_raw_operation_emissions, lsuffix='y').join(
                    data_raw_mobility_emissions, lsuffix='y2')
                data_raw = data_raw.sum(axis=0)
                for category in ['E', 'O', 'M']:
                    data_raw[category+'_ghg_kgm2'] = data_raw[category+'_ghg_ton'] * 1000 / data_raw['GFA_m2']
                    data_raw[category+'_nre_pen_MJm2'] = data_raw[category+'_nre_pen_GJ'] * 1000 / data_raw['GFA_m2']
                data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T
            else:
                data_raw_mobility_emissions = pd.read_csv(locator.get_lca_mobility()).set_index('Name')
                data_raw_embodied_emissions = pd.read_csv(locator.get_lca_embodied()).set_index('Name')
                data_raw = data_raw_mobility_emissions.join(data_raw_embodied_emissions, lsuffix='y')
                data_raw = data_raw.sum(axis=0)
                for category in ['E', 'M']:
                    data_raw[category + '_ghg_kgm2'] = data_raw[category + '_ghg_ton'] * 1000 / data_raw['GFA_m2']
                    data_raw[category + '_nre_pen_MJm2'] = data_raw[category + '_nre_pen_GJ'] * 1000 / data_raw[
                        'GFA_m2']

                # get operation
                data_raw_operation = pd.read_csv(locator.get_multi_criteria_analysis(generation))
                data_individual = data_raw_operation.loc[data_raw_operation["individual"] == individual]
                data_raw['O_ghg_ton'] = data_individual["total_emissions_kiloton"].values[0] * 1000
                data_raw['O_ghg_kgm2'] = data_individual["total_emissions_kiloton"].values[0] * 1000 * 1000 / data_raw[
                    'GFA_m2']
                data_raw['O_nre_pen_GJ'] = data_individual["total_prim_energy_TJ"].values[0] * 1000
                data_raw['O_nre_pen_MJm2'] = data_individual["total_prim_energy_TJ"].values[0] * 1000 * 1000 / data_raw[
                    'GFA_m2']
                data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T

            data_processed = data_processed.append(data_raw_df)
        return data_processed

    def preprocessing_occupancy_type_comparison(self):
        data_processed = pd.DataFrame()
        scenarios_clean = []
        for i, scenario_name in enumerate(self.scenarios_names):
            if scenario_name in scenarios_clean:
                scenario_name = scenario_name + "_duplicated_" + str(i)
            scenarios_clean.append(scenario_name)

        for scenario, scenario_name in zip(self.scenarios, scenarios_clean):
            locator = cea.inputlocator.InputLocator(scenario)
            district_occupancy_df = dbf_to_dataframe(locator.get_building_occupancy())
            district_occupancy_df.set_index('Name', inplace=True)
            district_gfa_df = pd.read_csv(locator.get_total_demand())[['GFA_m2'] + ["Name"]]
            district_gfa_df.set_index('Name', inplace=True)
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
            if sum > 0:
                analysis_fields_no_zero += [field]
        return analysis_fields_no_zero

    def comparison_demand(self, category):
        title = "Energy demand per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_demand", category)
        data = self.data_processed_demand.copy()
        analysis_fields = ["E_sys_MWhyr", "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                           "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def comparison_demand_intensity(self, category):
        title = "Energy use intensity per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_use_intensity", category)
        data = self.data_processed_demand.copy()
        analysis_fields = ["E_sys_MWhyr", "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                           "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_use_intensity(data, analysis_fields, title, output_path)
        return plot

    def comparison_supply_mix(self, category):
        title = "Energy supply per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_supply", category)
        data = self.data_processed_supply.copy()
        analysis_fields = ["E_PV_to_directload_MWhyr",
                           "GRID_MWhyr",
                           "NG_CCGT_MWhyr",
                           ]
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def comparison_supply_mix_intensity(self, category):
        title = "Energy supply intensity per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_supply_intensity", category)
        data = self.data_processed_supply.copy()
        analysis_fields = ["E_PV_to_directload_MWhyr",
                           "GRID_MWhyr",
                           "NG_CCGT_MWhyr",
                           ]
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_use_intensity(data, analysis_fields, title, output_path)
        return plot

    def CAPEX_vs_OPEX_comparison(self, category):
        title = "Operation costs per scenario"
        yaxis_title = "Operation costs [$USD(2015)/yr]"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_CAPEX_OPEX_costs", category)
        anlysis_fields = ["Opex_Centralized",
                          "Capex_Centralized",
                          "Capex_Decentralized",
                          "Opex_Decentralized"]
        data = self.data_processed_costs.copy()
        analysis_fields = self.erase_zeros(data, anlysis_fields)
        plot = operation_costs_district(data, analysis_fields, title, yaxis_title, output_path)
        return plot

    def CAPEX_vs_OPEX_comparison_intensity(self, category):
        title = "Operation costs relative to GFA per scenario"
        yaxis_title = "Operation costs [$USD(2015)/m2.yr]"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_CAPEX_OPEX_costs_intensity", category)
        anlysis_fields = ["Opex_Centralized_m2",
                          "Capex_Centralized_m2",
                          "Capex_Decentralized_m2",
                          "Opex_Decentralized_m2"]
        data = self.data_processed_costs.copy()
        analysis_fields = self.erase_zeros(data, anlysis_fields)
        plot = operation_costs_district(data, analysis_fields, title, yaxis_title, output_path)
        return plot

    def comparison_primary_energy(self, category):
        title = "Primary energy use intensity (non-renewable) per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_primary_energy", category)
        data = self.data_processed_life_cycle.copy()
        plot = primary_energy(data, self.analysis_fields_primary_energy, title, output_path)
        return plot

    def comparison_primary_energy_intensity(self, category):
        title = "Primary energy use intensity (non-renewable) per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_primary_energy_intensity", category)
        data = self.data_processed_life_cycle.copy()
        plot = primary_energy_intensity(data, self.analysis_fields_primary_energy_m2, title, output_path)
        return plot

    def comparison_emissions(self, category):
        title = "Green house gas emissions per scenario"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_emissions", category)
        data = self.data_processed_life_cycle.copy()
        plot = emissions(data, self.analysis_fields_emissions, title, output_path)
        return plot

    def comparison_emissions_intensity(self, category):
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


def main(config):
    plots_main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
