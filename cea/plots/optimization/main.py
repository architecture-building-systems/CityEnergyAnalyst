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
from cea.plots.optimization.individual_activation_curve import individual_activation_curve
from cea.plots.optimization.cost_analysis_curve import cost_analysis_curve
from cea.plots.optimization.pareto_capacity_installed import pareto_capacity_installed
from cea.plots.optimization.pareto_curve import pareto_curve
from cea.plots.optimization.pareto_curve_over_generations import pareto_curve_over_generations
from cea.plots.optimization.thermal_storage_curve import thermal_storage_activation_curve

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # local variables
    generations = config.plots.generations
    individual = config.plots.individual

    # initialize class
    plots = Plots(locator, individual, generations, config)

    # generate plots
    plots.pareto_multiple_generations()
    plots.pareto_final_generation()
    plots.cost_analysis_central_decentral()

    if config.plots.network_type == 'DH':
        plots.pareto_final_generation_capacity_installed_heating()
        plots.individual_heating_activation_curve()
        plots.individual_heating_storage_activation_curve()
        plots.individual_electricity_activation_curve_heating()
        plots.cost_analysis_heating_centralized()
        plots.cost_analysis_heating()
        plots.cost_analysis_cooling_decentralized()

    if config.plots.network_type == 'DC':
        plots.pareto_final_generation_capacity_installed_cooling()
        plots.individual_cooling_activation_curve()
        plots.individual_electricity_activation_curve_cooling()
        plots.cost_analysis_cooling_centralized()
        plots.cost_analysis_cooling()
        plots.cost_analysis_cooling_decentralized()

    return


class Plots():

    def __init__(self, locator, individual, generations, config):
        # local variables
        self.locator = locator
        self.individual = individual
        self.generations = generations
        self.config = config
        self.final_generation = self.preprocess_final_generation(generations)
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
                                                   "Opex_var_pump"
                                                   "Disconnected_costs"]
        self.analysis_fields_cost_decentralized = ["Capex_Decentralized", "Opex_Decentralized"]

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
                                                         "Capex_Lake",
                                                         "Capex_Sewage",
                                                         "Capex_pump",
                                                         "Opex_HP_Sewage",
                                                         "Opex_HP_Lake",
                                                         "Opex_GHP",
                                                         "Opex_CHP_Total",
                                                         "Opex_Furnace_Total",
                                                         "Opex_Boiler_Total",
                                                         "Disconnected_costs"]
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
                                                                            self.data_processed['final_generation'],
                                                                            self.individual, self.config)
        self.data_processed_cost = self.preprocessing_final_generation_data_cost(self.locator,
                                                                                 self.data_processed['final_generation'],
                                                                                 self.individual,
                                                                                 self.config)

    def preprocess_final_generation(self, generations):
        if len(generations) == 1:
            return generations[0]
        else:
            return generations[-1:][0]

    def preprocessing_generations_data(self):

        data_processed = []
        for generation in self.generations:
            with open(self.locator.get_optimization_checkpoint(generation), "rb") as fp:
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

            data_processed.append(
                {'population': df_population, 'halloffame': df_halloffame, 'capacities_W': df_capacities,
                 'disconnected_capacities_W': df_disc_capacities_final, 'network': df_network,
                 'spread': data['spread'], 'euclidean_distance': data['euclidean_distance'],
                 'individual_barcode': def_individual_barcode})

        return {'all_generations': data_processed, 'final_generation': data_processed[-1:][0]}

    def preprocessing_individual_data(self, locator, data_raw, individual, config):

        # get netwoork name
        string_network = data_raw['network'].loc[individual].values[0]
        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

        # get data about hourly demands in these buildings
        building_demands_df = pd.read_csv(locator.get_optimization_network_results_summary(string_network)).set_index(
            "DATE")

        # get data about the activation patterns of these buildings
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
        # get data about the activation patterns of these buildings (main units)
        if config.plots.network_type == 'DH':
            data_activation_path = os.path.join(
                locator.get_optimization_slave_heating_activation_pattern(individual_number, generation_number))
            df_heating = pd.read_csv(data_activation_path).set_index("DATE")

            data_activation_path = os.path.join(
                locator.get_optimization_slave_electricity_activation_pattern_heating(individual_number, generation_number))
            df_electricity = pd.read_csv(data_activation_path).set_index("DATE")

            # get data about the activation patterns of these buildings (storage)
            data_storage_path = os.path.join(
                locator.get_optimization_slave_storage_operation_data(individual_number, generation_number))
            df_SO = pd.read_csv(data_storage_path).set_index("DATE")

            # join into one database
            data_processed = df_heating.join(df_electricity).join(df_SO).join(building_demands_df)

        elif config.plots.network_type == 'DC':
            data_activation_path = os.path.join(
                locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number))
            df_cooling = pd.read_csv(data_activation_path).set_index("DATE")

            data_activation_path = os.path.join(
                locator.get_optimization_slave_electricity_activation_pattern_cooling(individual_number, generation_number))
            df_electricity = pd.read_csv(data_activation_path).set_index("DATE")

            # join into one database
            data_processed = df_cooling.join(building_demands_df).join(df_electricity)

        return data_processed

    def preprocessing_final_generation_data_cost(self, locator, data_raw, individual, config):

        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

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

        individual_index = data_raw['individual_barcode'].index.values
        if config.plots.network_type == 'DH':
            data_activation_path = os.path.join(
                locator.get_optimization_slave_investment_cost_detailed(1, 1))
            df_heating_costs = pd.read_csv(data_activation_path)
            column_names = df_heating_costs.columns.values
            column_names = np.append(column_names, ['Opex_HP_Sewage', 'Opex_HP_Lake', 'Opex_GHP', 'Opex_CHP_BG',
                                                    'Opex_CHP_NG', 'Opex_Furnace_wet', 'Opex_Furnace_dry',
                                                    'Opex_BaseBoiler_BG', 'Opex_BaseBoiler_NG', 'Opex_PeakBoiler_BG',
                                                    'Opex_PeakBoiler_NG', 'Opex_BackupBoiler_BG', 'Opex_BackupBoiler_NG',
                                                    'Capex_SC', 'Capex_PVT', 'Capex_Boiler_backup', 'Capex_storage_HEX',
                                                    'Capex_furnace', 'Capex_Boiler', 'Capex_Boiler_peak', 'Capex_Lake',
                                                    'Capex_Sewage', 'Capex_pump', 'Opex_Total', 'Capex_Total', 'Capex_Boiler_Total',
                                                    'Opex_Boiler_Total', 'Opex_CHP_Total', 'Opex_Furnace_Total', 'Disconnected_costs',
                                                    'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized', 'Opex_Centralized'])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names)]), columns=column_names)

        elif config.plots.network_type == 'DC':
            data_activation_path = os.path.join(
                locator.get_optimization_slave_investment_cost_detailed_cooling(1, 1))
            df_cooling_costs = pd.read_csv(data_activation_path)
            column_names = df_cooling_costs.columns.values
            column_names = np.append(column_names,
                                     ['Opex_var_ACH', 'Opex_var_CCGT', 'Opex_var_CT', 'Opex_var_Lake', 'Opex_var_VCC',
                                      'Opex_var_VCC_backup', 'Capex_ACH', 'Capex_CCGT', 'Capex_CT', 'Capex_Tank', 'Capex_VCC',
                                      'Capex_VCC_backup', 'Capex_a_pump', 'Opex_Total', 'Capex_Total', 'Opex_var_pump', 'Disconnected_costs',
                                      'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized', 'Opex_Centralized'])

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

            if config.plots.network_type == 'DH':
                data_activation_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number))
                df_heating_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    locator.get_optimization_slave_heating_activation_pattern(individual_number, generation_number))
                df_heating = pd.read_csv(data_activation_path).set_index("DATE")

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



                data_processed.loc[individual_code]['Opex_Total'] \
                    = data_processed.loc[individual_code]['Opex_HP_Sewage'] + data_processed.loc[individual_code]['Opex_HP_Lake'] + \
                      data_processed.loc[individual_code]['Opex_GHP'] + data_processed.loc[individual_code]['Opex_CHP_BG'] + \
                      data_processed.loc[individual_code]['Opex_CHP_NG'] + data_processed.loc[individual_code]['Opex_Furnace_wet'] + \
                      data_processed.loc[individual_code]['Opex_Furnace_dry'] + data_processed.loc[individual_code]['Opex_BaseBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_BaseBoiler_NG'] + data_processed.loc[individual_code]['Opex_PeakBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_PeakBoiler_NG'] + data_processed.loc[individual_code]['Opex_BackupBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_BackupBoiler_NG']

                data_processed.loc[individual_code]['Capex_Total'] = data_processed.loc[individual_code]['Capex_SC'] + \
                            data_processed.loc[individual_code]['Capex_PVT'] + data_processed.loc[individual_code]['Capex_Boiler_backup'] + \
                            data_processed.loc[individual_code]['Capex_storage_HEX'] + data_processed.loc[individual_code]['Capex_furnace'] + \
                            data_processed.loc[individual_code]['Capex_Boiler'] + data_processed.loc[individual_code]['Capex_Boiler_peak'] + \
                            data_processed.loc[individual_code]['Capex_Lake'] + data_processed.loc[individual_code]['Capex_Sewage'] + \
                            data_processed.loc[individual_code]['Capex_pump']

                data_processed.loc[individual_code]['Capex_Decentralized'] = df_heating_costs['Capex_Disconnected']
                data_processed.loc[individual_code]['Opex_Decentralized'] = df_heating_costs['Opex_Disconnected']
                data_processed.loc[individual_code]['Capex_Centralized'] = data_processed.loc[individual_code]['Capex_Total']
                data_processed.loc[individual_code]['Opex_Centralized'] = data_processed.loc[individual_code]['Opex_Total']

            elif config.plots.network_type == 'DC':
                data_activation_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number))
                disconnected_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed_cooling(individual_number, generation_number))
                df_cooling_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number))
                df_cooling = pd.read_csv(data_activation_path).set_index("DATE")

                for column_name in df_cooling_costs.columns.values:
                    data_processed.loc[individual_code][column_name] = df_cooling_costs[column_name].values

                data_processed.loc[individual_code]['Opex_var_ACH'] = np.sum(df_cooling['Opex_var_ACH'])
                data_processed.loc[individual_code]['Opex_var_CCGT'] = np.sum(df_cooling['Opex_var_CCGT'])
                data_processed.loc[individual_code]['Opex_var_CT'] = np.sum(df_cooling['Opex_var_CT'])
                data_processed.loc[individual_code]['Opex_var_Lake'] = np.sum(df_cooling['Opex_var_Lake'])
                data_processed.loc[individual_code]['Opex_var_VCC'] = np.sum(df_cooling['Opex_var_VCC'])
                data_processed.loc[individual_code]['Opex_var_VCC_backup'] = np.sum(df_cooling['Opex_var_VCC_backup'])
                data_processed.loc[individual_code]['Opex_var_pump'] = data_processed.loc[individual_code]['Opex_var_pump']

                data_processed.loc[individual_code]['Capex_ACH'] = data_processed.loc[individual_code]['Capex_a_ACH'] + data_processed.loc[individual_code]['Opex_fixed_ACH']
                data_processed.loc[individual_code]['Capex_CCGT'] = data_processed.loc[individual_code]['Capex_a_CCGT'] + data_processed.loc[individual_code]['Opex_fixed_CCGT']
                data_processed.loc[individual_code]['Capex_CT'] = data_processed.loc[individual_code]['Capex_a_CT']+ data_processed.loc[individual_code]['Opex_fixed_CT']
                data_processed.loc[individual_code]['Capex_Tank'] = data_processed.loc[individual_code]['Capex_a_Tank'] + data_processed.loc[individual_code]['Opex_fixed_Tank']
                data_processed.loc[individual_code]['Capex_VCC'] = data_processed.loc[individual_code]['Capex_a_VCC']+ data_processed.loc[individual_code]['Opex_fixed_VCC']
                data_processed.loc[individual_code]['Capex_VCC_backup'] = data_processed.loc[individual_code]['Capex_a_VCC_backup'] + data_processed.loc[individual_code]['Opex_fixed_VCC_backup']
                data_processed.loc[individual_code]['Capex_a_pump'] = data_processed.loc[individual_code]['Capex_pump']+ data_processed.loc[individual_code]['Opex_fixed_pump']

                data_processed.loc[individual_code]['Disconnected_costs'] = disconnected_costs['CostDiscBuild']
                data_processed.loc[individual_code]['Capex_Decentralized'] = disconnected_costs['Capex_Disconnected']
                data_processed.loc[individual_code]['Opex_Decentralized'] = disconnected_costs['Opex_Disconnected']

                data_processed.loc[individual_code]['Opex_Total'] = data_processed.loc[individual_code]['Opex_var_ACH'] + data_processed.loc[individual_code]['Opex_var_CCGT'] + \
                                               data_processed.loc[individual_code]['Opex_var_CT'] + data_processed.loc[individual_code]['Opex_var_Lake'] + \
                                               data_processed.loc[individual_code]['Opex_var_VCC'] + data_processed.loc[individual_code]['Opex_var_VCC_backup'] + data_processed.loc[individual_code]['Opex_var_pump']

                data_processed.loc[individual_code]['Capex_Total'] = data_processed.loc[individual_code]['Capex_a_ACH'] + data_processed.loc[individual_code]['Capex_a_CCGT'] + \
                                               data_processed.loc[individual_code]['Capex_a_CT'] + data_processed.loc[individual_code]['Capex_a_Tank'] + \
                                               data_processed.loc[individual_code]['Capex_a_VCC'] + data_processed.loc[individual_code]['Capex_a_VCC_backup'] + \
                                               data_processed.loc[individual_code]['Capex_pump'] + data_processed.loc[individual_code]['Opex_fixed_ACH'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_CCGT'] + data_processed.loc[individual_code]['Opex_fixed_CT'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_Tank'] + data_processed.loc[individual_code]['Opex_fixed_VCC'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_VCC_backup'] + data_processed.loc[individual_code]['Opex_fixed_pump']

                data_processed.loc[individual_code]['Capex_Centralized'] = data_processed.loc[individual_code]['Capex_Total']
                data_processed.loc[individual_code]['Opex_Centralized'] = data_processed.loc[individual_code]['Opex_Total']

        return data_processed

    def pareto_multiple_generations(self):
        title = 'Pareto Curve for Multiple Generations'
        output_path = self.locator.get_timeseries_plots_file('District_pareto_multiple_generations')
        data = self.data_processed['all_generations']
        plot = pareto_curve_over_generations(data, self.generations, title, output_path)
        return plot

    def pareto_final_generation(self):
        title = 'Pareto Curve for Final Generation ' + str(self.generations[-1:][0])
        output_path = self.locator.get_timeseries_plots_file('District_pareto_final_generation')
        data = self.data_processed['final_generation']
        plot = pareto_curve(data, title, output_path)
        return plot

    def pareto_final_generation_capacity_installed_heating(self):
        title = 'Capacity Installed in Final Generation' + str(self.generations[-1:][0])
        output_path = self.locator.get_timeseries_plots_file('District_pareto_final_generation_capacity_installed')
        data = self.data_processed['final_generation']
        plot = pareto_capacity_installed(data, self.analysis_fields_individual_heating, self.renewable_sources_fields, title, output_path)
        return plot

    def pareto_final_generation_capacity_installed_cooling(self):
        title = 'Capacity Installed in Final Generation' + str(self.generations[-1:][0])
        output_path = self.locator.get_timeseries_plots_file('District_pareto_final_generation_capacity_installed')
        data = self.data_processed['final_generation']
        plot = pareto_capacity_installed(data, self.analysis_fields_individual_cooling, self.renewable_sources_fields, title, output_path)
        return plot

    def individual_heating_activation_curve(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_heating_activation_curve')
        anlysis_fields_loads = self.analysis_fields_heating_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_heating, title, output_path)
        return plot

    def individual_heating_storage_activation_curve(self):
        title = 'Storage Activation curve  for Individual ' + self.individual + " in generation " + str(
            self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_heating_storage_activation_curve')
        analysis_fields_charging = self.analysis_fields_heating_storage_charging
        analysis_fields_discharging = self.analysis_fields_heating_storage_discharging
        analysis_fields_status = self.analysis_fields_heating_storage_status
        data = self.data_processed_individual
        plot = thermal_storage_activation_curve(data, analysis_fields_charging, analysis_fields_discharging,
                                                analysis_fields_status, title, output_path)
        return plot

    def individual_electricity_activation_curve_heating(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_DH_electricity_activation_curve')
        anlysis_fields_loads = self.analysis_fields_electricity_loads_heating
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_electricity_heating, title,
                                           output_path)
        return plot

    def individual_electricity_activation_curve_cooling(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_DC_electricity_activation_curve')
        anlysis_fields_loads = self.analysis_fields_electricity_loads_cooling
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_electricity_cooling, title,
                                           output_path)
        return plot

    def individual_cooling_activation_curve(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_cooling_activation_curve')
        anlysis_fields_loads = self.analysis_fields_cooling_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_cooling, title, output_path)
        return plot

    def cost_analysis_cooling_centralized(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_DCN_cost_analysis_split')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_cooling_centralized, title, output_path)
        return plot

    def cost_analysis_heating_centralized(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_DHN_cost_analysis_split')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_heating_centralized, title, output_path)
        return plot

    def cost_analysis_cooling_decentralized(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_DCN_decentralized_cost_analysis_split')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_decentralized, title, output_path)
        return plot

    def cost_analysis_heating_decentralized(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_DHN_decentralized_cost_analysis_split')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_decentralized, title, output_path)
        return plot

    def cost_analysis_cooling(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_DCN_cost_analysis_total')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_cooling_total, title, output_path)
        return plot

    def cost_analysis_heating(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_DHN_cost_analysis_total')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_heating_total, title, output_path)
        return plot

    def cost_analysis_central_decentral(self):
        title = 'Cost Analysis for generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation) + '_cost_central_vs_decentral')
        data = self.data_processed_cost
        plot = cost_analysis_curve(data, self.analysis_fields_cost_central_decentral, title, output_path)
        return plot

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generations = %s" % config.plots.generations)
    print("Running dashboard with the next individual = %s" % config.plots.individual)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())