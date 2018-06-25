"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import json
import os

import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.plots.supply_system.individual_activation_curve import individual_activation_curve
from cea.plots.supply_system.cost_analysis_curve_decentralized import cost_analysis_curve_decentralized
from cea.plots.supply_system.thermal_storage_curve import thermal_storage_activation_curve
from cea.plots.supply_system.pie_chart import pie_chart
from cea.optimization.constants import SIZING_MARGIN
from math import ceil

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # local variables
    scenario = config.scenario
    generation = config.plots_supply_system.generation
    individual = config.plots_supply_system.individual
    type_of_network = config.plots_supply_system.network_type

    # initialize class
    plots = Plots(locator, individual, generation, config)
    category = "optimal-energy-systems//single-system"

    # generate plots
    if type_of_network == 'DH':
        plots.individual_heating_dispatch_curve(category)
        plots.individual_heating_storage_dispatch_curve(category)
        plots.individual_electricity_dispatch_curve_heating(category)
        plots.cost_analysis_heating_decentralized(config, category)

    if type_of_network == 'DC':
        plots.individual_cooling_dispatch_curve(category)
        plots.individual_electricity_dispatch_curve_cooling(category)
        plots.cost_analysis_cooling_decentralized(config, category)

    # plots.map_location_size_customers_energy_system(type_of_network, category) ##TODO: create data inputs for these new 5 plots.
    # plots.pie_import_exports(category)
    # plots.pie_total_costs(category)
    # plots.pie_energy_supply_mix(category)
    # plots.pie_renewable_share(category)

    return


class Plots():

    def __init__(self, locator, individual, generation, config):
        # local variables
        self.locator = locator
        self.individual = individual
        self.config = config
        self.generation = generation
        # fields of loads in the systems of heating, cooling and electricity
        self.analysis_fields_electricity_loads_heating = ['Electr_netw_total_W', "E_HPSew_req_W", "E_HPLake_req_W",
                                                  "E_GHP_req_W",
                                                  "E_BaseBoiler_req_W",
                                                  "E_PeakBoiler_req_W",
                                                  "E_AddBoiler_req_W",
                                                  "E_aux_storage_solar_and_heat_recovery_req_W",
                                                  "E_total_req_W"]
        self.analysis_fields_electricity_loads_cooling = ["E_total_req_W"]
        self.analysis_fields_heating_loads = ['Q_DHNf_W']
        self.analysis_fields_cooling_loads = ['Q_total_cooling_W']
        self.analysis_fields_heating = ["Q_PVT_to_directload_W",
                                        "Q_SC_ET_to_directload_W",
                                        "Q_SC_FP_to_directload_W",
                                        "Q_server_to_directload_W",
                                        "Q_compair_to_directload_W",
                                        "Q_from_storage_used_W",
                                        "Q_HPLake_W",
                                        "Q_HPSew_W",
                                        "Q_GHP_W",
                                        "Q_CHP_W",
                                        "Q_Furnace_W",
                                        "Q_BaseBoiler_W",
                                        "Q_PeakBoiler_W",
                                        "Q_AddBoiler_W"]
        self.analysis_fields_heating_storage_charging = ["Q_PVT_to_storage_W",
                                                         "Q_SC_ET_to_storage_W",
                                                         "Q_SC_FP_to_storage_W",
                                                         "Q_server_to_storage_W"]
        self.analysis_fields_cost_cooling_centralized = ["Capex_a_ACH",
                                                   "Capex_a_CCGT",
                                                   "Capex_a_CT",
                                                   "Capex_a_Tank",
                                                   "Capex_a_VCC",
                                                   "Capex_a_VCC_backup",
                                                   "Capex_a_pump",
                                                   "Opex_var_ACH",
                                                   "Opex_var_CCGT",
                                                   "Opex_var_CT",
                                                   "Opex_var_Lake",
                                                   "Opex_var_VCC",
                                                   "Opex_var_VCC_backup",
                                                   "Opex_var_pump",
                                                   "Electricity_Costs"]
        self.analysis_fields_cost_decentralized_cooling = ["Capex_Decentralized", "Opex_Decentralized"]
        self.analysis_fields_cost_cooling_total = ["Capex_Total",
                                                   "Opex_Total"]
        self.analysis_fields_cost_central_decentral = ["Capex_Centralized",
                                                       "Capex_Decentralized",
                                                       "Opex_Centralized",
                                                       "Opex_Decentralized"]
        self.analysis_fields_cost_heating_total = ["Capex_Total",
                                                   "Opex_Total"]
        self.analysis_fields_cost_heating_centralized = ["Capex_SC",
                                                         "Capex_PVT",
                                                         "Capex_furnace",
                                                         "Capex_Boiler_Total",
                                                         "Capex_CHP",
                                                         "Capex_Lake",
                                                         "Capex_Sewage",
                                                         "Capex_pump",
                                                         "Opex_HP_Sewage",
                                                         "Opex_HP_Lake",
                                                         "Opex_GHP",
                                                         "Opex_CHP_Total",
                                                         "Opex_Furnace_Total",
                                                         "Opex_Boiler_Total",
                                                         "Electricity_Costs"]
        self.analysis_fields_heating_storage_discharging = ["Q_from_storage_used_W"]
        self.analysis_fields_heating_storage_status = ["Q_storage_content_W"]
        self.analysis_fields_cooling = ['Q_from_Lake_W',
                                        'Q_from_VCC_W',
                                        'Q_from_ACH_W',
                                        'Q_from_VCC_backup_W',
                                        'Q_from_storage_tank_W']
        self.analysis_fields_electricity_heating = ["E_PV_to_directload_W",
                                            "E_PVT_to_directload_W",
                                            "E_CHP_to_directload_W",
                                            "E_Furnace_to_directload_W",
                                            "E_PV_to_grid_W",
                                            "E_PVT_to_grid_W",
                                            "E_CHP_to_grid_W",
                                            "E_Furnace_to_grid_W",
                                                    "E_from_grid_W"]
        self.analysis_fields_electricity_cooling = ["E_CHP_to_directload_W",
                                                    "E_CHP_to_grid_W",
                                                    "E_PV_to_directload_W",
                                                    "E_PV_to_grid_W",
                                                    "E_from_grid_W"]
        self.analysis_fields_individual_heating = ['Base_boiler_BG_capacity_W', 'Base_boiler_NG_capacity_W', 'CHP_BG_capacity_W',
                                'CHP_NG_capacity_W', 'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                                'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                                'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                                'Peak_boiler_NG_capacity_W', 'SC_ET_capacity_W', 'SC_FP_capacity_W',
                                                   'Disconnected_Boiler_BG_capacity_W',
                                                   'Disconnected_Boiler_NG_capacity_W',
                                                   'Disconnected_FC_capacity_W',
                                                   'Disconnected_GHP_capacity_W']
        self.analysis_fields_individual_cooling = ['VCC_capacity_W', 'Absorption_Chiller_capacity_W',
                                                   'Lake_cooling_capacity_W', 'storage_cooling_capacity_W',
                                                   'Disconnected_VCC_to_AHU_capacity_cooling_W',
                                                   'Disconnected_VCC_to_ARU_capacity_cooling_W',
                                                   'Disconnected_VCC_to_SCU_capacity_cooling_W',
                                                   'Disconnected_VCC_to_AHU_ARU_capacity_cooling_W',
                                                   'Disconnected_VCC_to_AHU_SCU_capacity_cooling_W',
                                                   'Disconnected_VCC_to_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_AHU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_AHU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_ARU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_ARU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_SCU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_SCU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_AHU_ARU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_AHU_ARU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_AHU_SCU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_AHU_SCU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_double_effect_ACH_to_AHU_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_AHU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_ARU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_SCU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W',
                                                   'Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W']
        self.renewable_sources_fields = ['Base_boiler_BG_capacity_W', 'CHP_BG_capacity_W',
                                         'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                                         'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                                         'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                                         'SC_ET_capacity_W', 'SC_FP_capacity_W',
                                         'Disconnected_Boiler_BG_capacity_W',
                                         'Disconnected_FC_capacity_W',
                                         'Disconnected_GHP_capacity_W']
        self.cost_analysis_cooling_fields = ['Capex_a_ACH', 'Capex_a_CCGT', 'Capex_a_CT', 'Capex_a_Tank', 'Capex_a_VCC',
                                             'Capex_a_VCC_backup', 'Capex_pump', 'Opex_fixed_ACH', 'Opex_fixed_CCGT',
                                             'Opex_fixed_CT', 'Opex_fixed_Tank', 'Opex_fixed_VCC',
                                             'Opex_fixed_VCC_backup', 'Opex_fixed_pump',
                                             'Opex_var_Lake', 'Opex_var_VCC', 'Opex_var_ACH',
                                             'Opex_var_VCC_backup', 'Opex_var_CT', 'Opex_var_CCGT']
        self.data_processed = self.preprocessing_generations_data()
        self.data_processed_individual = self.preprocessing_individual_data(self.locator,
                                                                            self.data_processed['generation'],
                                                                            self.individual, self.config)
        self.data_processed_cost_centralized = self.preprocessing_generation_data_cost_centralized(self.locator,
                                                                                                         self.data_processed['generation'],
                                                                                                         self.config)
        self.data_processed_cost_decentralized = self.preprocessing_generation_data_decentralized(self.locator,
                                                                                 self.data_processed['generation'], self.individual,
                                                                                 self.config)


    def preprocessing_generations_data(self):

        with open(self.locator.get_optimization_checkpoint(self.generation), "rb") as fp:
            data = json.load(fp)
        # get lists of data for performance values of the population
        costs_Mio = [round(objectives[0] / 1000000, 2) for objectives in
                     data['population_fitness']]  # convert to millions
        emissions_ton = [round(objectives[1] / 1000000, 2) for objectives in
                         data['population_fitness']]  # convert to tons x 10^3
        prim_energy_GJ = [round(objectives[2] / 1000000, 2) for objectives in
                          data['population_fitness']]  # convert to gigajoules x 10^3
        individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]

        df_population = pd.DataFrame({'Name': individual_names, 'costs_Mio': costs_Mio,
                                      'emissions_ton': emissions_ton, 'prim_energy_GJ': prim_energy_GJ
                                      }).set_index("Name")

        individual_barcode = [[str(ind) if type(ind) == float else str(ind) for ind in
                               individual] for individual in data['population']]
        def_individual_barcode = pd.DataFrame({'Name': individual_names,
                                               'individual_barcode': individual_barcode}).set_index("Name")

        # get lists of data for performance values of the population (hall_of_fame
        costs_Mio_HOF = [round(objectives[0] / 1000000, 2) for objectives in
                         data['halloffame_fitness']]  # convert to millions
        emissions_ton_HOF = [round(objectives[1] / 1000000, 2) for objectives in
                             data['halloffame_fitness']]  # convert to tons x 10^3
        prim_energy_GJ_HOF = [round(objectives[2] / 1000000, 2) for objectives in
                              data['halloffame_fitness']]  # convert to gigajoules x 10^3
        individual_names_HOF = ['ind' + str(i) for i in range(len(costs_Mio_HOF))]
        df_halloffame = pd.DataFrame({'Name': individual_names_HOF, 'costs_Mio': costs_Mio_HOF,
                                      'emissions_ton': emissions_ton_HOF,
                                      'prim_energy_GJ': prim_energy_GJ_HOF}).set_index("Name")

        # get dataframe with capacity installed per individual
        for i, individual in enumerate(individual_names):
            dict_capacities = data['capacities'][i]
            dict_network = data['disconnected_capacities'][i]["network"]
            list_dict_disc_capacities = data['disconnected_capacities'][i]["disconnected_capacity"]
            for building, dict_disconnected in enumerate(list_dict_disc_capacities):
                if building == 0:
                    df_disc_capacities = pd.DataFrame(dict_disconnected, index=[dict_disconnected['building_name']])
                else:
                    df_disc_capacities = df_disc_capacities.append(
                        pd.DataFrame(dict_disconnected, index=[dict_disconnected['building_name']]))
            df_disc_capacities = df_disc_capacities.set_index('building_name')
            dict_disc_capacities = df_disc_capacities.sum(axis=0).to_dict()  # series with sum of capacities

            if i == 0:
                df_disc_capacities_final = pd.DataFrame(dict_disc_capacities, index=[individual])
                df_capacities = pd.DataFrame(dict_capacities, index=[individual])
                df_network = pd.DataFrame({"network": dict_network}, index=[individual])
            else:
                df_capacities = df_capacities.append(pd.DataFrame(dict_capacities, index=[individual]))
                df_network = df_network.append(pd.DataFrame({"network": dict_network}, index=[individual]))
                df_disc_capacities_final = df_disc_capacities_final.append(
                    pd.DataFrame(dict_disc_capacities, index=[individual]))

        data_processed = {'population': df_population, 'halloffame': df_halloffame, 'capacities_W': df_capacities,
             'disconnected_capacities_W': df_disc_capacities_final, 'network': df_network,
             'spread': data['spread'], 'euclidean_distance': data['euclidean_distance'],
             'individual_barcode': def_individual_barcode}

        return {'generation':data_processed}

    def preprocessing_individual_data(self, locator, data_raw, individual, config):

        # get netwoork name
        string_network = data_raw['network'].loc[individual].values[0]
        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

        # get data about hourly demands in these buildings
        building_demands_df = pd.read_csv(locator.get_optimization_network_results_summary(string_network)).set_index(
            "DATE")

        # get data about the dispatch patterns of these buildings
        individual_barcode_list = data_raw['individual_barcode'].loc[individual].values[0]
        df_all_generations = pd.read_csv(locator.get_optimization_all_individuals())

        # The current structure of CEA has the following columns saved, in future, this will be slightly changed and
        # correspondingly these columns_of_saved_files needs to be changed
        columns_of_saved_files = ['CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler',
                                  'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
                                  'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP',
                                  'GHP Share',
                                  'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share', 'SC_ET',
                                  'SC_ET Area Share', 'SC_FP', 'SC_FP Area Share', 'DHN Temperature', 'DHN unit configuration',
                                  'Lake Cooling', 'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
                                  'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share',
                                  'DCN Temperature', 'DCN unit configuration']
        for i in building_names:  # DHN
            columns_of_saved_files.append(str(i) + ' DHN')

        for i in building_names:  # DCN
            columns_of_saved_files.append(str(i) + ' DCN')


        df_current_individual = pd.DataFrame(np.zeros(shape = (1, len(columns_of_saved_files))), columns=columns_of_saved_files)
        for i, ind in enumerate((columns_of_saved_files)):
            df_current_individual[ind] = individual_barcode_list[i]
        for i in range(len(df_all_generations)):
            matching_number_between_individuals = 0
            for j in columns_of_saved_files:
                if np.isclose(float(df_all_generations[j][i]), float(df_current_individual[j][0])):
                    matching_number_between_individuals = matching_number_between_individuals + 1

            if matching_number_between_individuals >= (len(columns_of_saved_files) - 1):
                # this should ideally be equal to the length of the columns_of_saved_files, but due to a bug, which
                # occasionally changes the type of Boiler from NG to BG or otherwise, this round about is figured for now
                generation_number = df_all_generations['generation'][i]
                individual_number = df_all_generations['individual'][i]

        generation_number = int(generation_number)
        individual_number = int(individual_number)
        # get data about the dispatch patterns of these buildings (main units)
        if config.plots_supply_system.network_type == 'DH':
            data_dispatch_path = os.path.join(
                locator.get_optimization_slave_heating_activation_pattern(individual_number, generation_number))
            df_heating = pd.read_csv(data_dispatch_path).set_index("DATE")

            data_dispatch_path = os.path.join(
                locator.get_optimization_slave_electricity_activation_pattern_heating(individual_number, generation_number))
            df_electricity = pd.read_csv(data_dispatch_path).set_index("DATE")

            # get data about the dispatch patterns of these buildings (storage)
            data_storage_path = os.path.join(
                locator.get_optimization_slave_storage_operation_data(individual_number, generation_number))
            df_SO = pd.read_csv(data_storage_path).set_index("DATE")

            # join into one database
            data_processed = df_heating.join(df_electricity).join(df_SO).join(building_demands_df)

        elif config.plots_supply_system.network_type == 'DC':
            data_dispatch_path = os.path.join(
                locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number))
            df_cooling = pd.read_csv(data_dispatch_path).set_index("DATE")

            data_dispatch_path = os.path.join(
                locator.get_optimization_slave_electricity_activation_pattern_cooling(individual_number, generation_number))
            df_electricity = pd.read_csv(data_dispatch_path).set_index("DATE")

            # join into one database
            data_processed = df_cooling.join(building_demands_df).join(df_electricity)

        return data_processed

    def preprocessing_generation_data_cost_centralized(self, locator, data_raw, config):

        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

        df_all_generations = pd.read_csv(locator.get_optimization_all_individuals())
        preprocessing_costs = pd.read_csv(locator.get_preprocessing_costs())

        # The current structure of CEA has the following columns saved, in future, this will be slightly changed and
        # correspondingly these columns_of_saved_files needs to be changed
        columns_of_saved_files = ['CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler',
                                  'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
                                  'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP',
                                  'GHP Share',
                                  'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share', 'SC_ET',
                                  'SC_ET Area Share', 'SC_FP', 'SC_FP Area Share', 'DHN Temperature', 'DHN unit configuration',
                                  'Lake Cooling', 'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
                                  'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share',
                                  'DCN Temperature', 'DCN unit configuration']
        for i in building_names:  # DHN
            columns_of_saved_files.append(str(i) + ' DHN')

        for i in building_names:  # DCN
            columns_of_saved_files.append(str(i) + ' DCN')

        individual_index = data_raw['individual_barcode'].index.values
        if config.plots_supply_system.network_type == 'DH':
            data_dispatch_path = os.path.join(
                locator.get_optimization_slave_investment_cost_detailed(1, 1))
            df_heating_costs = pd.read_csv(data_dispatch_path)
            column_names = df_heating_costs.columns.values
            column_names = np.append(column_names, ['Opex_HP_Sewage', 'Opex_HP_Lake', 'Opex_GHP', 'Opex_CHP_BG',
                                                    'Opex_CHP_NG', 'Opex_Furnace_wet', 'Opex_Furnace_dry',
                                                    'Opex_BaseBoiler_BG', 'Opex_BaseBoiler_NG', 'Opex_PeakBoiler_BG',
                                                    'Opex_PeakBoiler_NG', 'Opex_BackupBoiler_BG', 'Opex_BackupBoiler_NG',
                                                    'Capex_SC', 'Capex_PVT', 'Capex_Boiler_backup', 'Capex_storage_HEX',
                                                    'Capex_furnace', 'Capex_Boiler', 'Capex_Boiler_peak', 'Capex_Lake', 'Capex_CHP',
                                                    'Capex_Sewage', 'Capex_pump', 'Opex_Total', 'Capex_Total', 'Capex_Boiler_Total',
                                                    'Opex_Boiler_Total', 'Opex_CHP_Total', 'Opex_Furnace_Total', 'Disconnected_costs',
                                                    'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized', 'Opex_Centralized', 'Electricity_Costs', 'Process_Heat_Costs'])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names)]), columns=column_names)

        elif config.plots_supply_system.network_type == 'DC':
            data_dispatch_path = os.path.join(
                locator.get_optimization_slave_investment_cost_detailed_cooling(1, 1))
            df_cooling_costs = pd.read_csv(data_dispatch_path)
            column_names = df_cooling_costs.columns.values
            column_names = np.append(column_names,
                                     ['Opex_var_ACH', 'Opex_var_CCGT', 'Opex_var_CT', 'Opex_var_Lake', 'Opex_var_VCC',
                                      'Opex_var_VCC_backup', 'Capex_ACH', 'Capex_CCGT', 'Capex_CT', 'Capex_Tank', 'Capex_VCC',
                                      'Capex_VCC_backup', 'Capex_a_pump', 'Opex_Total', 'Capex_Total', 'Opex_var_pump', 'Disconnected_costs',
                                      'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized', 'Opex_Centralized', 'Electricity_Costs', 'Process_Heat_Costs'])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names)]), columns=column_names)


        for individual_code in range(len(data_raw['individual_barcode'])):
            individual_barcode_list = data_raw['individual_barcode'].loc[individual_index[individual_code]].values[0]
            df_current_individual = pd.DataFrame(np.zeros(shape = (1, len(columns_of_saved_files))), columns=columns_of_saved_files)
            for i, ind in enumerate((columns_of_saved_files)):
                df_current_individual[ind] = individual_barcode_list[i]
            for i in range(len(df_all_generations)):
                matching_number_between_individuals = 0
                for j in columns_of_saved_files:
                    if np.isclose(float(df_all_generations[j][i]), float(df_current_individual[j][0])):
                        matching_number_between_individuals = matching_number_between_individuals + 1

                if matching_number_between_individuals >= (len(columns_of_saved_files) - 1):
                    # this should ideally be equal to the length of the columns_of_saved_files, but due to a bug, which
                    # occasionally changes the type of Boiler from NG to BG or otherwise, this round about is figured for now
                    generation_number = df_all_generations['generation'][i]
                    individual_number = df_all_generations['individual'][i]
            generation_number = int(generation_number)
            individual_number = int(individual_number)

            if config.plots_supply_system.network_type == 'DH':
                data_dispatch_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number))
                df_heating_costs = pd.read_csv(data_dispatch_path)

                data_dispatch_path = os.path.join(
                    locator.get_optimization_slave_heating_activation_pattern(individual_number, generation_number))
                df_heating = pd.read_csv(data_dispatch_path).set_index("DATE")

                for column_name in df_heating_costs.columns.values:
                    data_processed.loc[individual_code][column_name] = df_heating_costs[column_name].values


                data_processed.loc[individual_code]['Opex_HP_Sewage'] = np.sum(df_heating['Opex_var_HP_Sewage'])
                data_processed.loc[individual_code]['Opex_HP_Lake'] = np.sum(df_heating['Opex_var_HP_Lake'])
                data_processed.loc[individual_code]['Opex_GHP'] = np.sum(df_heating['Opex_var_GHP'])
                data_processed.loc[individual_code]['Opex_CHP_BG'] = np.sum(df_heating['Opex_var_CHP_BG'])
                data_processed.loc[individual_code]['Opex_CHP_NG'] = np.sum(df_heating['Opex_var_CHP_NG'])
                data_processed.loc[individual_code]['Opex_Furnace_wet'] = np.sum(df_heating['Opex_var_Furnace_wet'])
                data_processed.loc[individual_code]['Opex_Furnace_dry'] = np.sum(df_heating['Opex_var_Furnace_dry'])
                data_processed.loc[individual_code]['Opex_BaseBoiler_BG'] = np.sum(df_heating['Opex_var_BaseBoiler_BG'])
                data_processed.loc[individual_code]['Opex_BaseBoiler_NG'] = np.sum(df_heating['Opex_var_BaseBoiler_NG'])
                data_processed.loc[individual_code]['Opex_PeakBoiler_BG'] = np.sum(df_heating['Opex_var_PeakBoiler_BG'])
                data_processed.loc[individual_code]['Opex_PeakBoiler_NG'] = np.sum(df_heating['Opex_var_PeakBoiler_NG'])
                data_processed.loc[individual_code]['Opex_BackupBoiler_BG'] = np.sum(df_heating['Opex_var_BackupBoiler_BG'])
                data_processed.loc[individual_code]['Opex_BackupBoiler_NG'] = np.sum(df_heating['Opex_var_BackupBoiler_NG'])


                data_processed.loc[individual_code]['Capex_SC'] = data_processed.loc[individual_code]['Capex_a_SC'] + data_processed.loc[individual_code]['Opex_fixed_SC']
                data_processed.loc[individual_code]['Capex_PVT'] = data_processed.loc[individual_code]['Capex_a_PVT'] + data_processed.loc[individual_code]['Opex_fixed_PVT']
                data_processed.loc[individual_code]['Capex_Boiler_backup'] = data_processed.loc[individual_code]['Capex_a_Boiler_backup']+ data_processed.loc[individual_code]['Opex_fixed_Boiler_backup']
                data_processed.loc[individual_code]['Capex_storage_HEX'] = data_processed.loc[individual_code]['Capex_a_storage_HEX'] + data_processed.loc[individual_code]['Opex_fixed_storage_HEX']
                data_processed.loc[individual_code]['Capex_furnace'] = data_processed.loc[individual_code]['Capex_a_furnace']+ data_processed.loc[individual_code]['Opex_fixed_furnace']
                data_processed.loc[individual_code]['Capex_Boiler'] = data_processed.loc[individual_code]['Capex_a_Boiler'] + data_processed.loc[individual_code]['Opex_fixed_Boiler']
                data_processed.loc[individual_code]['Capex_Boiler_peak'] = data_processed.loc[individual_code]['Capex_a_Boiler_peak']+ data_processed.loc[individual_code]['Opex_fixed_Boiler_peak']
                data_processed.loc[individual_code]['Capex_Lake'] = data_processed.loc[individual_code]['Capex_a_Lake']+ data_processed.loc[individual_code]['Opex_fixed_Lake']
                data_processed.loc[individual_code]['Capex_Sewage'] = data_processed.loc[individual_code]['Capex_a_Sewage'] + data_processed.loc[individual_code]['Opex_fixed_Boiler']
                data_processed.loc[individual_code]['Capex_pump'] = data_processed.loc[individual_code]['Capex_a_pump'] + data_processed.loc[individual_code]['Opex_fixed_pump']
                data_processed.loc[individual_code]['Capex_CHP'] = data_processed.loc[individual_code]['Capex_a_CHP'] + data_processed.loc[individual_code]['Opex_fixed_CHP']
                data_processed.loc[individual_code]['Disconnected_costs'] = df_heating_costs['CostDiscBuild']

                data_processed.loc[individual_code]['Capex_Boiler_Total'] = data_processed.loc[individual_code]['Capex_Boiler'] + \
                                                                            data_processed.loc[individual_code][
                                                                                'Capex_Boiler_peak'] + \
                                                                            data_processed.loc[individual_code][
                                                                                'Capex_Boiler_backup']
                data_processed.loc[individual_code]['Opex_Boiler_Total'] = data_processed.loc[individual_code]['Opex_BackupBoiler_NG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_BackupBoiler_BG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_PeakBoiler_NG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_PeakBoiler_BG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_BaseBoiler_NG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_BaseBoiler_BG']
                data_processed.loc[individual_code]['Opex_CHP_Total'] = data_processed.loc[individual_code]['Opex_CHP_NG'] + \
                                                                        data_processed.loc[individual_code][
                                                                            'Opex_CHP_BG']

                data_processed.loc[individual_code]['Opex_Furnace_Total'] = data_processed.loc[individual_code]['Opex_Furnace_wet'] + \
                                                                          data_processed.loc[individual_code]['Opex_Furnace_dry']

                data_processed.loc[individual_code]['Electricity_Costs'] = preprocessing_costs['elecCosts'].values[0]
                data_processed.loc[individual_code]['Process_Heat_Costs'] = preprocessing_costs['hpCosts'].values[0]




                data_processed.loc[individual_code]['Opex_Centralized'] \
                    = data_processed.loc[individual_code]['Opex_HP_Sewage'] + data_processed.loc[individual_code]['Opex_HP_Lake'] + \
                      data_processed.loc[individual_code]['Opex_GHP'] + data_processed.loc[individual_code]['Opex_CHP_BG'] + \
                      data_processed.loc[individual_code]['Opex_CHP_NG'] + data_processed.loc[individual_code]['Opex_Furnace_wet'] + \
                      data_processed.loc[individual_code]['Opex_Furnace_dry'] + data_processed.loc[individual_code]['Opex_BaseBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_BaseBoiler_NG'] + data_processed.loc[individual_code]['Opex_PeakBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_PeakBoiler_NG'] + data_processed.loc[individual_code]['Opex_BackupBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_BackupBoiler_NG'] + \
                      data_processed.loc[individual_code]['Electricity_Costs'] + data_processed.loc[individual_code][
                          'Process_Heat_Costs']

                data_processed.loc[individual_code]['Capex_Centralized'] = data_processed.loc[individual_code]['Capex_SC'] + \
                            data_processed.loc[individual_code]['Capex_PVT'] + data_processed.loc[individual_code]['Capex_Boiler_backup'] + \
                            data_processed.loc[individual_code]['Capex_storage_HEX'] + data_processed.loc[individual_code]['Capex_furnace'] + \
                            data_processed.loc[individual_code]['Capex_Boiler'] + data_processed.loc[individual_code]['Capex_Boiler_peak'] + \
                            data_processed.loc[individual_code]['Capex_Lake'] + data_processed.loc[individual_code]['Capex_Sewage'] + \
                            data_processed.loc[individual_code]['Capex_pump']

                data_processed.loc[individual_code]['Capex_Decentralized'] = df_heating_costs['Capex_Disconnected']
                data_processed.loc[individual_code]['Opex_Decentralized'] = df_heating_costs['Opex_Disconnected']
                data_processed.loc[individual_code]['Capex_Total'] = data_processed.loc[individual_code]['Capex_Centralized'] + data_processed.loc[individual_code]['Capex_Decentralized']
                data_processed.loc[individual_code]['Opex_Total'] = data_processed.loc[individual_code]['Opex_Centralized'] + data_processed.loc[individual_code]['Opex_Decentralized']

            elif config.plots_supply_system.network_type == 'DC':
                data_dispatch_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number))
                disconnected_costs = pd.read_csv(data_dispatch_path)

                data_dispatch_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed_cooling(individual_number, generation_number))
                df_cooling_costs = pd.read_csv(data_dispatch_path)

                data_dispatch_path = os.path.join(
                    locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number))
                df_cooling = pd.read_csv(data_dispatch_path).set_index("DATE")

                data_load = pd.read_csv(os.path.join(
                    locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number)))

                for column_name in df_cooling_costs.columns.values:
                    data_processed.loc[individual_code][column_name] = df_cooling_costs[column_name].values

                data_processed.loc[individual_code]['Opex_var_ACH'] = np.sum(df_cooling['Opex_var_ACH'])
                data_processed.loc[individual_code]['Opex_var_CCGT'] = np.sum(df_cooling['Opex_var_CCGT'])
                data_processed.loc[individual_code]['Opex_var_CT'] = np.sum(df_cooling['Opex_var_CT'])
                data_processed.loc[individual_code]['Opex_var_Lake'] = np.sum(df_cooling['Opex_var_Lake'])
                data_processed.loc[individual_code]['Opex_var_VCC'] = np.sum(df_cooling['Opex_var_VCC'])
                data_processed.loc[individual_code]['Opex_var_VCC_backup'] = np.sum(df_cooling['Opex_var_VCC_backup'])
                data_processed.loc[individual_code]['Opex_var_pump'] = data_processed.loc[individual_code]['Opex_var_pump']

                Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(config.region),
                                                             sheetname="Absorption_chiller",
                                                             usecols=['type', 'code', 'cap_min', 'cap_max', 'a', 'b',
                                                                      'c', 'd', 'e', 'IR_%',
                                                                      'LT_yr', 'O&M_%'])
                Absorption_chiller_cost_data = Absorption_chiller_cost_data[
                    Absorption_chiller_cost_data['type'] == 'double']
                max_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)

                Q_ACH_max_W = data_load['Q_from_ACH_W'].max()
                Q_ACH_max_W = Q_ACH_max_W * (1 + SIZING_MARGIN)
                number_of_ACH_chillers = int(ceil(Q_ACH_max_W / max_chiller_size))

                VCC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Chiller")
                VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
                max_VCC_chiller_size = max(VCC_cost_data['cap_max'].values)

                Q_VCC_max_W = data_load['Q_from_VCC_W'].max()
                Q_VCC_max_W = Q_VCC_max_W * (1 + SIZING_MARGIN)
                number_of_VCC_chillers = int(ceil(Q_VCC_max_W / max_VCC_chiller_size))

                data_processed.loc[individual_code]['Capex_ACH'] = (data_processed.loc[individual_code]['Capex_a_ACH'] + data_processed.loc[individual_code]['Opex_fixed_ACH']) * number_of_ACH_chillers
                data_processed.loc[individual_code]['Capex_CCGT'] = data_processed.loc[individual_code]['Capex_a_CCGT'] + data_processed.loc[individual_code]['Opex_fixed_CCGT']
                data_processed.loc[individual_code]['Capex_CT'] = data_processed.loc[individual_code]['Capex_a_CT']+ data_processed.loc[individual_code]['Opex_fixed_CT']
                data_processed.loc[individual_code]['Capex_Tank'] = data_processed.loc[individual_code]['Capex_a_Tank'] + data_processed.loc[individual_code]['Opex_fixed_Tank']
                data_processed.loc[individual_code]['Capex_VCC'] = (data_processed.loc[individual_code]['Capex_a_VCC']+ data_processed.loc[individual_code]['Opex_fixed_VCC']) * number_of_VCC_chillers
                data_processed.loc[individual_code]['Capex_VCC_backup'] = data_processed.loc[individual_code]['Capex_a_VCC_backup'] + data_processed.loc[individual_code]['Opex_fixed_VCC_backup']
                data_processed.loc[individual_code]['Capex_a_pump'] = data_processed.loc[individual_code]['Capex_pump']+ data_processed.loc[individual_code]['Opex_fixed_pump']

                data_processed.loc[individual_code]['Disconnected_costs'] = disconnected_costs['CostDiscBuild']
                data_processed.loc[individual_code]['Capex_Decentralized'] = disconnected_costs['Capex_Disconnected']
                data_processed.loc[individual_code]['Opex_Decentralized'] = disconnected_costs['Opex_Disconnected']

                data_processed.loc[individual_code]['Electricity_Costs'] = preprocessing_costs['elecCosts'].values[0]
                data_processed.loc[individual_code]['Process_Heat_Costs'] = preprocessing_costs['hpCosts'].values[0]

                data_processed.loc[individual_code]['Opex_Centralized'] = data_processed.loc[individual_code]['Opex_var_ACH'] + data_processed.loc[individual_code]['Opex_var_CCGT'] + \
                                               data_processed.loc[individual_code]['Opex_var_CT'] + data_processed.loc[individual_code]['Opex_var_Lake'] + \
                                               data_processed.loc[individual_code]['Opex_var_VCC'] + data_processed.loc[individual_code]['Opex_var_VCC_backup'] + data_processed.loc[individual_code]['Opex_var_pump'].values[0] + \
                                               data_processed.loc[individual_code]['Electricity_Costs'] + data_processed.loc[individual_code]['Process_Heat_Costs']

                data_processed.loc[individual_code]['Capex_Centralized'] = data_processed.loc[individual_code]['Capex_a_ACH'] + data_processed.loc[individual_code]['Capex_a_CCGT'] + \
                                               data_processed.loc[individual_code]['Capex_a_CT'] + data_processed.loc[individual_code]['Capex_a_Tank'] + \
                                               data_processed.loc[individual_code]['Capex_a_VCC'] + data_processed.loc[individual_code]['Capex_a_VCC_backup'] + \
                                               data_processed.loc[individual_code]['Capex_pump'] + data_processed.loc[individual_code]['Opex_fixed_ACH'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_CCGT'] + data_processed.loc[individual_code]['Opex_fixed_CT'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_Tank'] + data_processed.loc[individual_code]['Opex_fixed_VCC'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_VCC_backup'] + data_processed.loc[individual_code]['Opex_fixed_pump']


                data_processed.loc[individual_code]['Capex_Total'] = data_processed.loc[individual_code]['Capex_Centralized'] + data_processed.loc[individual_code]['Capex_Decentralized']
                data_processed.loc[individual_code]['Opex_Total'] = data_processed.loc[individual_code]['Opex_Centralized'] + data_processed.loc[individual_code]['Opex_Decentralized']

        return data_processed

    def preprocessing_generation_data_decentralized(self, locator, data_raw, individual, config):

        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

        df_all_generations = pd.read_csv(locator.get_optimization_all_individuals())

        # The current structure of CEA has the following columns saved, in future, this will be slightly changed and
        # correspondingly these columns_of_saved_files needs to be changed
        columns_of_saved_files = ['CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler',
                                  'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
                                  'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP',
                                  'GHP Share',
                                  'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share',
                                  'SC_ET',
                                  'SC_ET Area Share', 'SC_FP', 'SC_FP Area Share', 'DHN Temperature',
                                  'DHN unit configuration',
                                  'Lake Cooling', 'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
                                  'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share',
                                  'DCN Temperature', 'DCN unit configuration']
        for i in building_names:  # DHN
            columns_of_saved_files.append(str(i) + ' DHN')

        for i in building_names:  # DCN
            columns_of_saved_files.append(str(i) + ' DCN')

        column_names_decentralized = []
        if config.plots_supply_system.network_type == 'DH':
            data_dispatch_path = os.path.join(
                locator.get_optimization_disconnected_folder_building_result_heating(building_names[0]))
            df_heating_costs = pd.read_csv(data_dispatch_path)
            column_names = df_heating_costs.columns.values
            column_names = column_names[1:]
            for i in building_names:
                for j in range(len(column_names)):
                    column_names_decentralized.append(str(i) + " " + column_names[j])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names_decentralized)]),
                                          columns=column_names_decentralized)

        elif config.plots_supply_system.network_type == 'DC':
            data_dispatch_path = os.path.join(
                locator.get_optimization_disconnected_folder_building_result_cooling(building_names[0], 'AHU_ARU_SCU'))
            df_cooling_costs = pd.read_csv(data_dispatch_path)
            column_names = df_cooling_costs.columns.values
            for i in building_names:
                for j in range(len(column_names)):
                    column_names_decentralized.append(str(i) + " " + column_names[j])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names_decentralized)]),
                                          columns=column_names_decentralized)


        individual_barcode_list = data_raw['individual_barcode'].loc[individual].values[0]
        df_current_individual = pd.DataFrame(np.zeros(shape=(1, len(columns_of_saved_files))),
                                             columns=columns_of_saved_files)
        for i, ind in enumerate((columns_of_saved_files)):
            df_current_individual[ind] = individual_barcode_list[i]
        for i in range(len(df_all_generations)):
            matching_number_between_individuals = 0
            for j in columns_of_saved_files:
                if np.isclose(float(df_all_generations[j][i]), float(df_current_individual[j][0])):
                    matching_number_between_individuals = matching_number_between_individuals + 1

            if matching_number_between_individuals >= (len(columns_of_saved_files) - 1):
                # this should ideally be equal to the length of the columns_of_saved_files, but due to a bug, which
                # occasionally changes the type of Boiler from NG to BG or otherwise, this round about is figured for now
                generation_number = df_all_generations['generation'][i]
                individual_number = df_all_generations['individual'][i]
        generation_number = int(generation_number)
        individual_number = int(individual_number)

        df_decentralized = df_all_generations[df_all_generations['generation'] == generation_number]
        df_decentralized = df_decentralized[df_decentralized['individual'] == individual_number]


        if config.plots_supply_system.network_type == 'DH':
            for i in building_names:  # DHN
                if df_decentralized[str(i) + ' DHN'].values[0] == 0:
                    data_dispatch_path = os.path.join(
                        locator.get_optimization_disconnected_folder_building_result_heating(i))
                    df_heating_costs = pd.read_csv(data_dispatch_path)
                    df_heating_costs = df_heating_costs[df_heating_costs["Best configuration"] == 1]
                    for j in range(len(column_names)):
                        name_of_column = str(i) + " " + column_names[j]
                        data_processed.loc[0][name_of_column] = df_heating_costs[column_names[j]].values


        elif config.plots_supply_system.network_type == 'DC':
            for i in building_names:  # DCN
                if df_decentralized[str(i) + ' DCN'].values[0] == 0:
                    data_dispatch_path = os.path.join(
                        locator.get_optimization_disconnected_folder_building_result_cooling(i, 'AHU_ARU_SCU'))
                    df_cooling_costs = pd.read_csv(data_dispatch_path)
                    df_cooling_costs = df_cooling_costs[df_cooling_costs["Best configuration"] == 1]
                    for j in range(len(column_names)):
                        name_of_column = str(i) + " " + column_names[j]
                        data_processed.loc[0][name_of_column] = df_cooling_costs[column_names[j]].values

        return data_processed

    def preprocessing_create_thermal_network(self, config, locator, output_name_network, output_type_network, buildings_connected):
        from cea.technologies.thermal_network.network_layout.main import network_layout
        from cea.technologies.thermal_network.thermal_network_matrix import thermal_network_main

        # configure layout script to create the new network adn store in the folder inputs.
        config.network_layout.network_type = output_type_network
        config.network_layout.create_plant = True
        config.network_layout.buildings = buildings_connected
        network_layout(config, locator, output_name_network)

        # configure thermal network (reduced simulation and create diagram of new network.
        network_name = output_name_network
        network_type = output_type_network  # set to either 'DH' or 'DC'
        file_type = config.thermal_network.file_type  # set to csv or shp
        set_diameter = config.thermal_network.set_diameter  # boolean
        config.thermal_network.use_representative_week_per_month = False

        if network_type == 'DC':
            substation_cooling_systems = ['ahu', 'aru', 'scu', 'data',
                                          're']  # list of cooling demand types supplied by network to substation
            substation_heating_systems = []
        else:
            substation_cooling_systems = []
            substation_heating_systems = ['ahu', 'aru', 'shu',
                                          'ww']  # list of heating demand types supplied by network to substation

        # combine into a dictionary to pass fewer arguments
        substation_systems = {'heating': substation_heating_systems, 'cooling': substation_cooling_systems}
        thermal_network_main(locator, network_type, network_name, file_type, set_diameter, config, substation_systems)

    def individual_heating_dispatch_curve(self, category):
        title = 'Dispatch curve for configuration' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_centralized_heating_dispatch_curve', category)
        anlysis_fields_loads = self.analysis_fields_heating_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_heating, title, output_path)
        return plot

    def individual_heating_storage_dispatch_curve(self, category):
        title = 'Dispatch curve for configuration ' + self.individual + " in generation " + str(
            self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_centralized_heating_storage_dispatch_curve', category)
        analysis_fields_charging = self.analysis_fields_heating_storage_charging
        analysis_fields_discharging = self.analysis_fields_heating_storage_discharging
        analysis_fields_status = self.analysis_fields_heating_storage_status
        data = self.data_processed_individual
        plot = thermal_storage_activation_curve(data, analysis_fields_charging, analysis_fields_discharging,
                                                analysis_fields_status, title, output_path)
        return plot

    def individual_electricity_dispatch_curve_heating(self, category):
        title = 'Dispatch curve for configuration ' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_centralized_electricity_dispatch_curve', category)
        anlysis_fields_loads = self.analysis_fields_electricity_loads_heating
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_electricity_heating, title,
                                           output_path)
        return plot

    def individual_electricity_dispatch_curve_cooling(self, category):
        title = 'Dispatch curve for configuration ' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_centralized_electricity_dispatch_curve', category)
        anlysis_fields_loads = self.analysis_fields_electricity_loads_cooling
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_electricity_cooling, title,
                                           output_path)
        return plot

    def individual_cooling_dispatch_curve(self, category):
        title = 'Dispatch curve for configuration ' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_centralized_cooling_dispatch_curve', category)
        anlysis_fields_loads = self.analysis_fields_cooling_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_cooling, title, output_path)
        return plot

    def cost_analysis_cooling_decentralized(self, config, category):

        data = self.data_processed_cost_decentralized
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_decentralized_costs_per_generation_unit', category)
        plot = cost_analysis_curve_decentralized(data, self.locator, self.generation, self.individual, config, output_path)
        return plot

    def cost_analysis_heating_decentralized(self, config, category):

        data = self.data_processed_cost_decentralized
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_decentralized_costs_per_generation_unit', category)
        plot = cost_analysis_curve_decentralized(data, self.locator, self.generation, self.individual, config, output_path)
        return plot

    def pie_import_exports(self, category):
        title = 'Imports vs exports in ' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_pie_import_exports', category)
        anlysis_fields = []##TODO: get data it should be a list with the names of the variables (e.g., import_grid_MWhyr, export_PV_MWhyr, export_CHP_MWhyr, import_NG_MWhyr, export_NG_MWyr, etc)
        data = []##TODO: get data  it should be a dataaframe with columns presenting the variable names  and one single row showing the values for the individual
        plot = pie_chart(data, anlysis_fields, title, output_path)
        return plot

    def pie_total_costs(self, category):
        title = 'CAPEX vs OPEX for' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_pie_costs', category)
        anlysis_fields = []##TODO: get data it should be a list with the names of the variables (e.g., CAPEX_tot_$yr, OPEX_$yr / central and decentral etc)
        data = []##TODO: get data  it should be a dataaframe with columns presenting the diffrent variable names  and one single row showing the values for the individual
        plot = pie_chart(data, anlysis_fields, title, output_path)
        return plot

    def pie_energy_supply_mix(self, category):
        title = 'Energy supply mix of' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_pie_costs', category)
        anlysis_fields = []##TODO: get data it should be a list with the names of the variables (e.g., VCC_gen_MWhyr, import_grid_MWyr, Direct_PV_MWyr) etc)
        data = []##TODO: get data  it should be a dataframe with columns presenting the diffrent variable names and one single row showing the values for the individual
        plot = pie_chart(data, anlysis_fields, title, output_path)
        return plot

    def pie_renewable_share(self, category):
        title = 'Renewable energy share in ' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_pie_costs', category)
        anlysis_fields = []##TODO: get data it should be a list with the names of the variables (e.g., Renewables_MWyr, non_renewables_MWyr) etc)
        data = []##TODO: get data  it should be a dataframe with columns presenting the diffrent variable names and one single row showing the values for the individual
        plot = pie_chart(data, anlysis_fields, title, output_path)
        return plot

    def map_location_size_customers_energy_system(self, output_type_network, category):
        from cea.plots.supply_system.map_chart import map_chart
        output_name_network = "scenario_gen1_ind12" ##TODO: automate to get the sceanrio
        buildings_connected = ["B001", "B002"] ##TODO:automate to get selection of building names from the scenario
        self.preprocessing_create_thermal_network(self.config, self.locator,
                                                  output_name_network, output_type_network,
                                                  buildings_connected)
        title = 'Energy system map for' + self.individual + " in generation " + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.generation) + '_' + self.individual + '_energy_system_map', category)
        data = [] #TODO: create dataframe with data for the table, and also connected and disconnected buildings.
        anlysis_fields = [] #TODO: add analysis fields
        plot = map_chart(data, self.locator, anlysis_fields, title, output_path,
                         output_name_network, output_type_network,
                         buildings_connected)
        return plot

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generations = %s" % config.plots_supply_system.generation)
    print("Running dashboard with the next individual = %s" % config.plots_supply_system.individual)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())