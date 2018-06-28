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
from cea.plots.optimization.cost_analysis_curve_centralized import cost_analysis_curve_centralized
from cea.plots.optimization.pareto_capacity_installed import pareto_capacity_installed
from cea.plots.optimization.pareto_curve import pareto_curve
from cea.optimization.lca_calculations import lca_calculations
from cea.plots.optimization.pareto_curve_over_generations import pareto_curve_over_generations
from cea.analysis.multicriteria.optimization_post_processing.individual_configuration import supply_system_configuration
from cea.technologies.solar.photovoltaic import calc_Cinv_pv
from cea.optimization.constants import SIZING_MARGIN
from cea.analysis.multicriteria.optimization_post_processing.locating_individuals_in_generation_script import locating_individuals_in_generation_script
from math import ceil, log

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
    generation = config.plots_optimization.generation
    categories = config.plots_optimization.categories

    scenario = config.scenario
    type_of_network = config.plots_optimization.network_type


    # generate plots
    category = "optimization-overview"

    if not os.path.exists(locator.get_address_of_individuals_of_a_generation(generation, category)):
        data_address = locating_individuals_in_generation_script(generation, locator)
    else:
        data_address = pd.read_csv(locator.get_address_of_individuals_of_a_generation(generation, category))

    # initialize class
    plots = Plots(locator, generation, config, type_of_network, data_address)

    if "pareto_curve" in categories:
        plots.pareto_curve_for_one_generation(category)

    if "system_sizes" in categories:
        plots.cost_analysis_central_decentral(category)
        if config.plots_optimization.network_type == 'DH':
            plots.comparison_capacity_installed_heating_supply_system_one_generation(category)
        if config.plots_optimization.network_type == 'DC':
            plots.comparison_capacity_installed_cooling_supply_system_one_generation(category)

    if "costs_analysis" in categories:
        plots.cost_analysis_central_decentral(category)
        if config.plots_optimization.network_type == 'DH':
            plots.comparison_capex_opex_heating_supply_system_for_one_generation_per_production_unit(category)
        if config.plots_optimization.network_type == 'DC':
            plots.comparison_capex_opex_cooling_supply_system_for_one_generation_per_production_unit(category)

    return


class Plots():

    def __init__(self, locator, generation, config, type_of_network, data_address):
        # local variables
        self.locator = locator
        self.config = config
        self.generation = generation
        self.network_type = type_of_network
        self.final_generation = [generation]
        self.data_address = data_address
        # fields of loads in the systems of heating, cooling and electricity
        self.analysis_fields_cost_cooling_centralized = ["Capex_a_ACH",
                                                   "Capex_a_CCGT",
                                                   "Capex_a_CT",
                                                   "Capex_a_Tank",
                                                   "Capex_a_VCC",
                                                   "Capex_a_VCC_backup",
                                                   "Capex_a_pump",
                                                   "Capex_a_PV",
                                                   "Opex_var_ACH",
                                                   "Opex_var_CCGT",
                                                   "Opex_var_CT",
                                                   "Opex_var_Lake",
                                                   "Opex_var_VCC",
                                                   "Opex_var_VCC_backup",
                                                   "Opex_var_pumps",
                                                   "Opex_var_PV",
                                                   "Electricitycosts_for_hotwater",
                                                   "Electricitycosts_for_appliances"]

        self.analysis_fields_cost_central_decentral = ["Capex_Centralized",
                                                       "Capex_Decentralized",
                                                       "Opex_Centralized",
                                                       "Opex_Decentralized"]
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
        self.analysis_fields_individual_heating = ['Base_boiler_BG_capacity_W', 'Base_boiler_NG_capacity_W', 'CHP_BG_capacity_W',
                                'CHP_NG_capacity_W', 'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                                'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                                'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                                'Peak_boiler_NG_capacity_W', 'SC_ET_capacity_W', 'SC_FP_capacity_W',
                                                   'Disconnected_Boiler_BG_capacity_W',
                                                   'Disconnected_Boiler_NG_capacity_W',
                                                   'Disconnected_FC_capacity_W',
                                                   'Disconnected_GHP_capacity_W']
        self.analysis_fields_individual_cooling = ['Lake_kW', 'VCC_LT_kW', 'VCC_HT_kW', 'single_effect_ACH_LT_kW',
                                   'single_effect_ACH_HT_kW', 'DX_kW', 'CHP_CCGT_thermal_kW', 'Storage_thermal_kW']
        self.data_processed = self.preprocessing_generations_data()
        self.data_processed_cost_centralized = self.preprocessing_final_generation_data_cost_centralized(self.locator,
                                                                                                         self.data_processed['final_generation'],
                                                                                                         self.config, self.data_address)
        self.data_processed_multicriteria = self.preprocessing_multi_criteria_data(self.locator, self.final_generation[0])
        self.data_processed_capacities = self.preprocessing_capacities_data(self.locator, self.data_processed['final_generation'], self.generation, self.network_type, config, self.data_address)

    def preprocessing_generations_data(self):

        data_processed = []
        for generation in self.final_generation:
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

    def preprocessing_capacities_data(self, locator, data_generation, generation, network_type, config, data_address):

        column_names = ['Lake_kW', 'VCC_LT_kW', 'VCC_HT_kW', 'single_effect_ACH_LT_kW',
                        'single_effect_ACH_HT_kW', 'DX_kW', 'CHP_CCGT_thermal_kW',
                        'Storage_thermal_kW', 'CT_kW', 'Buildings Connected Share']
        individual_index = data_generation['individual_barcode'].index.values
        capacities_of_generation =pd.DataFrame(np.zeros([len(individual_index), len(column_names)]), columns=column_names)

        for i, ind in enumerate(individual_index):

            data_address_individual = data_address[data_address['individual_list'] == ind]

            generation_pointer = data_address_individual['generation_number_address'].values[0]  # points to the correct file to be referenced from optimization folders
            individual_pointer = data_address_individual['individual_number_address'].values[0]
            district_supply_sys, building_connectivity = supply_system_configuration(generation_pointer, individual_pointer, locator, network_type, config)

            for name in column_names:
                if name is 'Buildings Connected Share':
                    connected_buildings = len(building_connectivity.loc[building_connectivity.Type == "CENTRALIZED"])
                    total_buildings = connected_buildings + len(
                        building_connectivity.loc[building_connectivity.Type == "DECENTRALIZED"])
                    capacities_of_generation.iloc[i][name] = np.float(connected_buildings * 100 / total_buildings)
                else:
                    capacities_of_generation.iloc[i][name] = district_supply_sys[name].sum()

        capacities_of_generation['indiv'] = individual_index
        capacities_of_generation.set_index('indiv', inplace=True)
        return {'capacities_of_final_generation': capacities_of_generation}


    def preprocessing_final_generation_data_cost_centralized(self, locator, data_raw, config, data_address):

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
        if config.plots_optimization.network_type == 'DH':
            data_activation_path = os.path.join(
                locator.get_optimization_slave_investment_cost_detailed(1, 1))
            df_heating_costs = pd.read_csv(data_activation_path)
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

        elif config.plots_optimization.network_type == 'DC':
            data_activation_path = os.path.join(
                locator.get_optimization_slave_investment_cost_detailed_cooling(1, 1))
            df_cooling_costs = pd.read_csv(data_activation_path)
            column_names = df_cooling_costs.columns.values
            column_names = np.append(column_names,
                                     ['Opex_var_ACH', 'Opex_var_CCGT', 'Opex_var_CT', 'Opex_var_Lake', 'Opex_var_VCC', 'Opex_var_PV',
                                      'Opex_var_VCC_backup', 'Capex_ACH', 'Capex_CCGT', 'Capex_CT', 'Capex_Tank', 'Capex_VCC', 'Capex_a_PV',
                                      'Capex_VCC_backup', 'Capex_a_pump', 'Opex_Total', 'Capex_Total', 'Opex_var_pumps', 'Disconnected_costs',
                                      'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized', 'Opex_Centralized', 'Electricitycosts_for_appliances',
                                      'Process_Heat_Costs', 'Electricitycosts_for_hotwater'])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names)]), columns=column_names)


        for individual_code in range(len(data_raw['individual_barcode'])):

            individual_barcode_list = data_raw['individual_barcode'].loc[individual_index[individual_code]].values[0]
            df_current_individual = pd.DataFrame(np.zeros(shape = (1, len(columns_of_saved_files))), columns=columns_of_saved_files)
            for i, ind in enumerate((columns_of_saved_files)):
                df_current_individual[ind] = individual_barcode_list[i]
            data_address_individual = data_address[data_address['individual_list'] == individual_index[individual_code]]

            generation_pointer = data_address_individual['generation_number_address'].values[0]  # points to the correct file to be referenced from optimization folders
            individual_pointer = data_address_individual['individual_number_address'].values[0]

            if config.plots_optimization.network_type == 'DH':
                data_activation_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed(individual_pointer, generation_pointer))
                df_heating_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    locator.get_optimization_slave_heating_activation_pattern(individual_pointer, generation_pointer))
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

            elif config.plots_optimization.network_type == 'DC':
                data_activation_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed(individual_pointer, generation_pointer))
                disconnected_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    locator.get_optimization_slave_investment_cost_detailed_cooling(individual_pointer, generation_pointer))
                df_cooling_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    locator.get_optimization_slave_cooling_activation_pattern(individual_pointer, generation_pointer))
                df_cooling = pd.read_csv(data_activation_path).set_index("DATE")
                data_load = pd.read_csv(os.path.join(
                    locator.get_optimization_slave_cooling_activation_pattern(individual_pointer, generation_pointer)))
                data_load_electricity = pd.read_csv(os.path.join(
                    locator.get_optimization_slave_electricity_activation_pattern_cooling(individual_pointer, generation_pointer)))

                for column_name in df_cooling_costs.columns.values:
                    data_processed.loc[individual_code][column_name] = df_cooling_costs[column_name].values

                data_processed.loc[individual_code]['Opex_var_ACH'] = np.sum(df_cooling['Opex_var_ACH'])
                data_processed.loc[individual_code]['Opex_var_CCGT'] = np.sum(df_cooling['Opex_var_CCGT'])
                data_processed.loc[individual_code]['Opex_var_CT'] = np.sum(df_cooling['Opex_var_CT'])
                data_processed.loc[individual_code]['Opex_var_Lake'] = np.sum(df_cooling['Opex_var_Lake'])
                data_processed.loc[individual_code]['Opex_var_VCC'] = np.sum(df_cooling['Opex_var_VCC'])
                data_processed.loc[individual_code]['Opex_var_VCC_backup'] = np.sum(df_cooling['Opex_var_VCC_backup'])
                data_processed.loc[individual_code]['Opex_var_pumps'] = np.sum(data_processed.loc[individual_code]['Opex_var_pump'])
                data_processed.loc[individual_code]['Opex_var_PV'] = -np.sum(data_load_electricity['KEV'])

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

                PV_peak_kW = data_load_electricity['E_PV_W'].max() / 1000
                Capex_a_PV, Opex_fixed_PV = calc_Cinv_pv(PV_peak_kW, locator, config)

                data_processed.loc[individual_code]['Capex_ACH'] = (data_processed.loc[individual_code]['Capex_a_ACH'] + data_processed.loc[individual_code]['Opex_fixed_ACH']) * number_of_ACH_chillers
                data_processed.loc[individual_code]['Capex_CCGT'] = data_processed.loc[individual_code]['Capex_a_CCGT'] + data_processed.loc[individual_code]['Opex_fixed_CCGT']
                data_processed.loc[individual_code]['Capex_CT'] = data_processed.loc[individual_code]['Capex_a_CT']+ data_processed.loc[individual_code]['Opex_fixed_CT']
                data_processed.loc[individual_code]['Capex_Tank'] = data_processed.loc[individual_code]['Capex_a_Tank'] + data_processed.loc[individual_code]['Opex_fixed_Tank']
                data_processed.loc[individual_code]['Capex_VCC'] = (data_processed.loc[individual_code]['Capex_a_VCC']+ data_processed.loc[individual_code]['Opex_fixed_VCC']) * number_of_VCC_chillers
                data_processed.loc[individual_code]['Capex_VCC_backup'] = data_processed.loc[individual_code]['Capex_a_VCC_backup'] + data_processed.loc[individual_code]['Opex_fixed_VCC_backup']
                data_processed.loc[individual_code]['Capex_a_pump'] = data_processed.loc[individual_code]['Capex_pump']+ data_processed.loc[individual_code]['Opex_fixed_pump']
                data_processed.loc[individual_code]['Capex_a_PV'] =  Capex_a_PV + Opex_fixed_PV

                data_processed.loc[individual_code]['Disconnected_costs'] = disconnected_costs['CostDiscBuild']
                data_processed.loc[individual_code]['Capex_Decentralized'] = disconnected_costs['Capex_Disconnected']
                data_processed.loc[individual_code]['Opex_Decentralized'] = disconnected_costs['Opex_Disconnected']

                data_processed.loc[individual_code]['Electricitycosts_for_appliances'] = preprocessing_costs['elecCosts'].values[0]
                data_processed.loc[individual_code]['Process_Heat_Costs'] = preprocessing_costs['hpCosts'].values[0]

                E_for_hot_water_demand_W = np.zeros(8760)
                lca = lca_calculations(locator, config)

                for name in building_names:  # adding the electricity demand from the decentralized buildings
                    building_demand = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                                  usecols=['E_ww_kWh'])

                    E_for_hot_water_demand_W += building_demand['E_ww_kWh'] * 1000

                data_processed.loc[individual_code]['Electricitycosts_for_hotwater'] = E_for_hot_water_demand_W.sum() * lca.ELEC_PRICE


                data_processed.loc[individual_code]['Opex_Centralized'] = data_processed.loc[individual_code]['Opex_var_ACH'] + data_processed.loc[individual_code]['Opex_var_CCGT'] + \
                                               data_processed.loc[individual_code]['Opex_var_CT'] + data_processed.loc[individual_code]['Opex_var_Lake'] + \
                                               data_processed.loc[individual_code]['Opex_var_VCC'] + data_processed.loc[individual_code]['Opex_var_VCC_backup'] + data_processed.loc[individual_code]['Opex_var_pumps'] + \
                                               data_processed.loc[individual_code]['Electricitycosts_for_appliances'] + data_processed.loc[individual_code]['Process_Heat_Costs'] + \
                                               data_processed.loc[individual_code]['Opex_var_PV'] + data_processed.loc[individual_code]['Electricitycosts_for_hotwater']

                data_processed.loc[individual_code]['Capex_Centralized'] = data_processed.loc[individual_code]['Capex_a_ACH'] + data_processed.loc[individual_code]['Capex_a_CCGT'] + \
                                               data_processed.loc[individual_code]['Capex_a_CT'] + data_processed.loc[individual_code]['Capex_a_Tank'] + \
                                               data_processed.loc[individual_code]['Capex_a_VCC'] + data_processed.loc[individual_code]['Capex_a_VCC_backup'] + \
                                               data_processed.loc[individual_code]['Capex_pump'] + data_processed.loc[individual_code]['Opex_fixed_ACH'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_CCGT'] + data_processed.loc[individual_code]['Opex_fixed_CT'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_Tank'] + data_processed.loc[individual_code]['Opex_fixed_VCC'] + \
                                               data_processed.loc[individual_code]['Opex_fixed_VCC_backup'] + data_processed.loc[individual_code]['Opex_fixed_pump'] + Capex_a_PV + Opex_fixed_PV


                data_processed.loc[individual_code]['Capex_Total'] = data_processed.loc[individual_code]['Capex_Centralized'] + data_processed.loc[individual_code]['Capex_Decentralized']
                data_processed.loc[individual_code]['Opex_Total'] = data_processed.loc[individual_code]['Opex_Centralized'] + data_processed.loc[individual_code]['Opex_Decentralized']

        individual_names = ['ind' + str(i) for i in data_processed.index.values]
        data_processed['indiv'] = individual_names
        data_processed.set_index('indiv', inplace=True)
        return data_processed

    def erase_zeros(self, data, fields):
        analysis_fields_no_zero = []
        for field in fields:
            if isinstance(data[field], float):
                sum = data[field]
            else:
                sum = data[field].sum()
            if not np.isclose(sum, 0.0):
                analysis_fields_no_zero += [field]
        return analysis_fields_no_zero

    def preprocessing_multi_criteria_data(self, locator, generation):

        data_multi_criteria = pd.read_csv(locator.get_multi_criteria_analysis(generation))

        return data_multi_criteria

    def pareto_curve_for_one_generation(self, category):
        title = 'Pareto curve for generation ' + str(self.final_generation[0])
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.final_generation[0]) + '_pareto_curve', category)
        objectives = ['TAC_Mio','emissions_kiloton', 'prim_energy_TJ']
        analysis_fields = ['individual', 'TAC_Mio','emissions_kiloton', 'prim_energy_TJ', 'renewable_share_electricity',
                           'Capex_total_Mio', 'Opex_total_Mio']
        data= self.data_processed_multicriteria
        plot = pareto_curve(data, objectives, analysis_fields, title, output_path)
        return plot

    def comparison_capacity_installed_heating_supply_system_one_generation(self, category):
        title = 'Capacity installed in generation ' + str(self.final_generation[0])
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.final_generation[0]) + '_centralized_and_decentralized_capacities_installed', category)
        data = self.data_processed_capacities['capacities_of_final_generation'].copy()
        analysis_fields_clean = self.erase_zeros(data, self.analysis_fields_individual_heating)
        plot = pareto_capacity_installed(data, analysis_fields_clean, title, output_path)
        return plot

    def comparison_capacity_installed_cooling_supply_system_one_generation(self, category):
        title = 'Capacity installed in generation' + str(self.final_generation[0])
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.final_generation[0]) + '_centralized_and_decentralized_capacities_installed', category)
        data = self.data_processed_capacities['capacities_of_final_generation'].copy()
        analysis_fields_clean = self.erase_zeros(data, self.analysis_fields_individual_cooling)
        plot = pareto_capacity_installed(data, analysis_fields_clean, title, output_path)
        return plot

    def comparison_capex_opex_cooling_supply_system_for_one_generation_per_production_unit(self, category):
        title = 'CAPEX vs. OPEX district cooling network for every optimal supply system scenario in generation ' + str(self.final_generation[0])
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.final_generation[0]) + '_centralized_costs_per_generation_unit', category)
        data = self.data_processed_cost_centralized.copy()
        plot = cost_analysis_curve_centralized(data, self.analysis_fields_cost_cooling_centralized, title, output_path)
        return plot

    def comparison_capex_opex_heating_supply_system_for_one_generation_per_production_unit(self, category):
        title = 'CAPEX vs. OPEX of centralized system in generation ' + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.final_generation[0]) + '_centralized_costs_per_generation_unit', category)
        data = self.data_processed_cost_centralized.copy()
        plot = cost_analysis_curve_centralized(data, self.analysis_fields_cost_heating_centralized, title, output_path)
        return plot

    def cost_analysis_central_decentral(self, category):
        title = 'CAPEX vs. OPEX of centralized system in generation ' + str(self.final_generation[0])
        output_path = self.locator.get_timeseries_plots_file(
            'gen' + str(self.final_generation[0]) + '_centralized_and_decentralized_costs_total', category)
        data = self.data_processed_cost_centralized.copy()
        plot = cost_analysis_curve_centralized(data, self.analysis_fields_cost_central_decentral, title, output_path)
        return plot

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generation = %s" % config.plots_optimization.generation)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())