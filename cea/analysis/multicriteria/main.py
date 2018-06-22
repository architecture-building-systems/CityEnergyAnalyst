"""
Multi criteria decision analysis
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
from cea.plots.optimization.pareto_curve_over_generations import pareto_curve_over_generations

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # local variables
    generations = config.plots.generations

    # initialize class
    plots = Plots(locator, generations, config)

    return


class Plots():

    def __init__(self, locator, generations, config):
        # local variables
        self.locator = locator
        self.generations = generations
        self.config = config
        self.final_generation = self.preprocess_final_generation(generations)

        self.data_processed = self.preprocessing_generations_data()
        self.data_processed_cost_centralized = self.preprocessing_final_generation_data_cost_centralized(self.locator,
                                                                                                         self.data_processed['final_generation'],
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

        columns = ['Capex_a_ACH',
                   'Capex_a_CCGT',
                   'Capex_a_CT',
                   'Capex_a_Tank',
                   'Capex_a_VCC',
                   'Capex_a_VCC_backup',
                   'Capex_pump',
                   ]
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

    def preprocessing_final_generation_data_cost_centralized(self, locator, data_raw, config):

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
                                                    'Capex_furnace', 'Capex_Boiler', 'Capex_Boiler_peak', 'Capex_Lake', 'Capex_CHP',
                                                    'Capex_Sewage', 'Capex_pump', 'Opex_Total', 'Capex_Total', 'Capex_Boiler_Total',
                                                    'Opex_Boiler_Total', 'Opex_CHP_Total', 'Opex_Furnace_Total', 'Disconnected_costs',
                                                    'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized', 'Opex_Centralized', 'Electricity_Costs', 'Process_Heat_Costs'])

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

        individual_names = ['ind' + str(i) for i in data_processed.index.values]
        data_processed['indiv'] = individual_names
        data_processed.set_index('indiv', inplace=True)
        return data_processed

    def preprocessing_final_generation_data_decentralized(self, locator, data_raw, individual, config):

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

        individual_index = data_raw['individual_barcode'].index.values
        column_names_decentralized = []
        if config.plots.network_type == 'DH':
            data_activation_path = os.path.join(
                locator.get_optimization_disconnected_folder_building_result_heating(building_names[0]))
            df_heating_costs = pd.read_csv(data_activation_path)
            column_names = df_heating_costs.columns.values
            column_names = column_names[1:]
            for i in building_names:
                for j in range(len(column_names)):
                    column_names_decentralized.append(str(i) + " " + column_names[j])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names_decentralized)]),
                                          columns=column_names_decentralized)

        elif config.plots.network_type == 'DC':
            data_activation_path = os.path.join(
                locator.get_optimization_disconnected_folder_building_result_cooling(building_names[0], 'AHU_ARU_SCU'))
            df_cooling_costs = pd.read_csv(data_activation_path)
            column_names = df_cooling_costs.columns.values
            for i in building_names:
                for j in range(len(column_names)):
                    column_names_decentralized.append(str(i) + " " + column_names[j])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names_decentralized)]),
                                          columns=column_names_decentralized)

        for individual_code in range(len(data_raw['individual_barcode'])):

            individual_barcode_list = data_raw['individual_barcode'].loc[individual_index[individual_code]].values[0]
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


            if config.plots.network_type == 'DH':
                for i in building_names:  # DHN
                    if df_decentralized[str(i) + ' DHN'].values[0] == 0:
                        data_activation_path = os.path.join(
                            locator.get_optimization_disconnected_folder_building_result_heating(i))
                        df_heating_costs = pd.read_csv(data_activation_path)
                        df_heating_costs = df_heating_costs[df_heating_costs["Best configuration"] == 1]
                        for j in range(len(column_names)):
                            name_of_column = str(i) + " " + column_names[j]
                            data_processed.loc[individual_code][name_of_column] = df_heating_costs[column_names[j]].values


            elif config.plots.network_type == 'DC':
                for i in building_names:  # DCN
                    if df_decentralized[str(i) + ' DCN'].values[0] == 0:
                        data_activation_path = os.path.join(
                            locator.get_optimization_disconnected_folder_building_result_cooling(i, 'AHU_ARU_SCU'))
                        df_cooling_costs = pd.read_csv(data_activation_path)
                        df_cooling_costs = df_cooling_costs[df_cooling_costs["Best configuration"] == 1]
                        for j in range(len(column_names)):
                            name_of_column = str(i) + " " + column_names[j]
                            data_processed.loc[individual_code][name_of_column] = df_cooling_costs[column_names[j]].values

        return data_processed


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generations = %s" % config.plots.generations)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())