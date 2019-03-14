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
from cea.optimization.lca_calculations import lca_calculations
from cea.optimization.slave.electricity_main import electricity_calculations_of_all_buildings
from cea.technologies.solar.photovoltaic import calc_Cinv_pv
from cea.optimization.constants import PUMP_ETA
from cea.constants import DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3
from cea.optimization.constants import SIZING_MARGIN
from cea.analysis.multicriteria.optimization_post_processing.individual_configuration import calc_opex_PV
from cea.technologies.chiller_vapor_compression import calc_Cinv_VCC
from cea.technologies.chiller_absorption import calc_Cinv_ACH
from cea.technologies.cooling_tower import calc_Cinv_CT
import cea.optimization.distribution.network_opt_main as network_opt
from cea.analysis.multicriteria.optimization_post_processing.locating_individuals_in_generation_script import locating_individuals_in_generation_script
from math import ceil, log


__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def multi_criteria_main(locator, config):
    # local variables
    generation = config.multi_criteria.generations
    category = "optimization-detailed"
    if not os.path.exists(locator.get_address_of_individuals_of_a_generation(generation)):
        data_address = locating_individuals_in_generation_script(generation, locator)
    else:
        data_address = pd.read_csv(locator.get_address_of_individuals_of_a_generation(generation))

    # initialize class
    data_generation = preprocessing_generations_data(locator, generation)
    objectives = data_generation['final_generation']['population']
    individual_list = objectives.axes[0].values
    data_processed = preprocessing_cost_data(locator, data_generation['final_generation'], individual_list[0], generation, data_address, config)
    column_names = data_processed.columns.values

    compiled_data = pd.DataFrame(np.zeros([len(individual_list), len(column_names)]), columns=column_names)

    for i, individual in enumerate(individual_list):
        data_processed = preprocessing_cost_data(locator, data_generation['final_generation'], individual, generation, data_address, config)
        for name in column_names:
            compiled_data.loc[i][name] = data_processed[name][0]

    compiled_data = compiled_data.assign(individual=individual_list)

    if (max(compiled_data['TAC_Mio']) - min(compiled_data['TAC_Mio'])) > 1E-8:
        normalized_TAC = (compiled_data['TAC_Mio'] - min(compiled_data['TAC_Mio'])) / (
                    max(compiled_data['TAC_Mio']) - min(compiled_data['TAC_Mio']))
    else:
        normalized_TAC = [1] * len(compiled_data['TAC_Mio'])

    if (max(compiled_data['total_emissions_kiloton']) - min(compiled_data['total_emissions_kiloton'])) > 1E-8:
        normalized_emissions = (compiled_data['total_emissions_kiloton'] - min(compiled_data['total_emissions_kiloton'])) / (
                    max(compiled_data['total_emissions_kiloton']) - min(compiled_data['total_emissions_kiloton']))
    else:
        normalized_emissions = [1] * len(compiled_data['total_emissions_kiloton'])

    if (max(compiled_data['total_prim_energy_TJ']) - min(compiled_data['total_prim_energy_TJ'])) > 1E-8:
        normalized_prim = (compiled_data['total_prim_energy_TJ'] - min(compiled_data['total_prim_energy_TJ'])) / (
                max(compiled_data['total_prim_energy_TJ']) - min(compiled_data['total_prim_energy_TJ']))
    else:
        normalized_prim = [1] * len(compiled_data['total_prim_energy_TJ'])

    if (max(compiled_data['Capex_total_Mio']) - min(compiled_data['Capex_total_Mio'])) > 1E-8:
        normalized_Capex_total = (compiled_data['Capex_total_Mio'] - min(compiled_data['Capex_total_Mio'])) / (
                max(compiled_data['Capex_total_Mio']) - min(compiled_data['Capex_total_Mio']))
    else:
        normalized_Capex_total = [1] * len(compiled_data['Capex_total_Mio'])

    if (max(compiled_data['Opex_total_Mio']) - min(compiled_data['Opex_total_Mio'])) > 1E-8:
        normalized_Opex = (compiled_data['Opex_total_Mio'] - min(compiled_data['Opex_total_Mio'])) / (
                max(compiled_data['Opex_total_Mio']) - min(compiled_data['Opex_total_Mio']))
    else:
        normalized_Opex = [1] * len(compiled_data['Opex_total_Mio'])

    if (max(compiled_data['renewable_share_electricity']) - min(compiled_data['renewable_share_electricity'])) > 1E-8:
        normalized_renewable_share = (compiled_data['renewable_share_electricity'] - min(compiled_data['renewable_share_electricity'])) / (
                max(compiled_data['renewable_share_electricity']) - min(compiled_data['renewable_share_electricity']))
    else:
        normalized_renewable_share = [1] * compiled_data['renewable_share_electricity']

    compiled_data = compiled_data.assign(normalized_TAC=normalized_TAC)
    compiled_data = compiled_data.assign(normalized_emissions=normalized_emissions)
    compiled_data = compiled_data.assign(normalized_prim=normalized_prim)
    compiled_data = compiled_data.assign(normalized_Capex_total=normalized_Capex_total)
    compiled_data = compiled_data.assign(normalized_Opex=normalized_Opex)
    compiled_data = compiled_data.assign(normalized_renewable_share=normalized_renewable_share)

    compiled_data['TAC_rank'] = compiled_data['normalized_TAC'].rank(ascending=True)
    compiled_data['emissions_rank'] = compiled_data['normalized_emissions'].rank(ascending=True)
    compiled_data['prim_rank'] = compiled_data['normalized_prim'].rank(ascending=True)

    # user defined mcda
    compiled_data['user_MCDA'] = compiled_data['normalized_Capex_total'] * config.multi_criteria.capextotal * config.multi_criteria.economicsustainability + \
                                 compiled_data['normalized_Opex'] * config.multi_criteria.opex * config.multi_criteria.economicsustainability + \
                                 compiled_data['normalized_TAC'] * config.multi_criteria.annualizedcosts * config.multi_criteria.economicsustainability + \
                                 compiled_data['normalized_emissions'] *config.multi_criteria.emissions * config.multi_criteria.environmentalsustainability + \
                                 compiled_data['normalized_prim'] *config.multi_criteria.primaryenergy * config.multi_criteria.environmentalsustainability + \
                                 compiled_data['normalized_renewable_share'] * config.multi_criteria.renewableshare * config.multi_criteria.socialsustainability

    compiled_data['user_MCDA_rank'] = compiled_data['user_MCDA'].rank(ascending=True)

    compiled_data.to_csv(locator.get_multi_criteria_analysis(generation))

    return compiled_data


def preprocessing_generations_data(locator, generations):

    data_processed = []
    with open(locator.get_optimization_checkpoint(generations), "rb") as fp:
        data = json.load(fp)
    # get lists of data for performance values of the population
    costs_Mio = [round(objectives[0] / 1000000, 2) for objectives in
                 data['tested_population_fitness']]  # convert to millions
    emissions_kiloton = [round(objectives[1] / 1000000, 2) for objectives in
                     data['tested_population_fitness']]  # convert to tons x 10^3 (kiloton)
    prim_energy_TJ = [round(objectives[2] / 1000000, 2) for objectives in
                      data['tested_population_fitness']]  # convert to gigajoules x 10^3 (Terajoules)
    individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]

    df_population = pd.DataFrame({'Name': individual_names, 'costs_Mio': costs_Mio,
                                  'emissions_kiloton': emissions_kiloton, 'prim_energy_TJ': prim_energy_TJ
                                  }).set_index("Name")

    individual_barcode = [[str(ind) if type(ind) == float else str(ind) for ind in
                           individual] for individual in data['tested_population']]
    def_individual_barcode = pd.DataFrame({'Name': individual_names,
                                           'individual_barcode': individual_barcode}).set_index("Name")

    # get lists of data for performance values of the population (hall_of_fame
    costs_Mio_HOF = [round(objectives[0] / 1000000, 2) for objectives in
                     data['halloffame_fitness']]  # convert to millions
    emissions_kiloton_HOF = [round(objectives[1] / 1000000, 2) for objectives in
                         data['halloffame_fitness']]  # convert to tons x 10^3
    prim_energy_TJ_HOF = [round(objectives[2] / 1000000, 2) for objectives in
                          data['halloffame_fitness']]  # convert to gigajoules x 10^3
    individual_names_HOF = ['ind' + str(i) for i in range(len(costs_Mio_HOF))]
    df_halloffame = pd.DataFrame({'Name': individual_names_HOF, 'costs_Mio': costs_Mio_HOF,
                                  'emissions_kiloton': emissions_kiloton_HOF,
                                  'prim_energy_TJ': prim_energy_TJ_HOF}).set_index("Name")
    for i, individual in enumerate(individual_names):
        dict_network = data['DCN_list_All'][i]
        if i == 0:
            df_network = pd.DataFrame({"network": dict_network}, index=[individual])
        else:
            df_network = df_network.append(pd.DataFrame({"network": dict_network}, index=[individual]))

    data_processed.append(
        {'population': df_population, 'halloffame': df_halloffame, 'network': df_network,
         'spread': data['spread'], 'euclidean_distance': data['euclidean_distance'],
         'individual_barcode': def_individual_barcode})

    return {'all_generations': data_processed, 'final_generation': data_processed[-1:][0]}

def preprocessing_cost_data(locator, data_raw, individual, generations, data_address, config):

    string_network = data_raw['network'].loc[individual].values[0]
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    individual_barcode_list = data_raw['individual_barcode'].loc[individual].values[0]

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

    data_address = data_address[data_address['individual_list'] == individual]

    generation_number = data_address['generation_number_address'].values[0]
    individual_number = data_address['individual_number_address'].values[0]
    # get data about the activation patterns of these buildings (main units)

    if config.multi_criteria.network_type == 'DH':
        building_demands_df = pd.read_csv(locator.get_optimization_network_results_summary(string_network)).set_index(
            "DATE")
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

    elif config.multi_criteria.network_type == 'DC':

        data_costs = pd.read_csv(os.path.join(locator.get_optimization_slave_investment_cost_detailed_cooling(individual_number, generation_number)))
        data_cooling = pd.read_csv(os.path.join(locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number)))
        data_electricity = pd.read_csv(os.path.join(locator.get_optimization_slave_electricity_activation_pattern_cooling(individual_number, generation_number)))
        data_emissions = pd.read_csv(os.path.join(locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number)))

        # Total CAPEX calculations
        # Absorption Chiller

        data_costs['Capex_total_ACH_USD'] = data_costs['Capex_ACH_USD'].values[0]
        data_costs['Opex_total_ACH_USD'] = np.sum(data_cooling['Opex_var_ACH_USD']) + data_costs['Opex_fixed_ACH_USD']

        # VCC
        data_costs['Capex_total_VCC_USD'] = data_costs['Capex_VCC_USD'].values[0]
        data_costs['Opex_total_VCC_USD'] = np.sum(data_cooling['Opex_var_VCC_USD']) + data_costs['Opex_fixed_VCC_USD']

        # VCC Backup
        data_costs['Capex_total_VCC_backup_USD'] = data_costs['Capex_VCC_backup_USD']
        data_costs['Opex_total_VCC_backup_USD'] = np.sum(data_cooling['Opex_var_VCC_backup_USD']) + data_costs['Opex_fixed_VCC_backup_USD']

        # Storage Tank
        data_costs['Capex_total_storage_tank_USD'] = data_costs['Capex_Tank_USD']
        data_costs['Opex_total_storage_tank_USD'] =  data_costs['Opex_fixed_Tank_USD']

        # Cooling Tower
        data_costs['Capex_total_CT_USD'] = data_costs['Capex_CT_USD']
        data_costs['Opex_total_CT_USD'] = np.sum(data_cooling['Opex_var_CT_USD']) + data_costs['Opex_fixed_CT_USD']

        # CCGT
        data_costs['Capex_total_CCGT_USD'] = data_costs['Capex_CCGT_USD']
        data_costs['Opex_total_CCGT_USD'] = np.sum(data_cooling['Opex_var_CCGT_USD']) + data_costs['Opex_fixed_CCGT_USD']

        # pump
        data_costs['Capex_total_pumps_USD'] = data_emissions['Capex_pump'].values[0]
        data_costs['Opex_total_pumps_USD'] = data_costs['Opex_fixed_pump_USD'] + data_costs['Opex_var_pump_USD']

        # Lake - No lake in singapore, should be modified in future
        data_costs['Opex_fixed_Lake_USD'] = [0]
        data_costs['Opex_total_Lake_USD'] = [0]
        data_costs['Capex_total_Lake_USD'] = [0]
        data_costs['Capex_a_Lake_USD'] = [0]


        # PV

        data_costs['Capex_total_PV_USD'] = data_emissions['Capex_PV'].values[0]
        data_costs['Opex_total_PV_USD'] = data_emissions['Opex_fixed_PV'].values[0]
        data_costs['Opex_fixed_PV_USD'] = data_emissions['Opex_fixed_PV'].values[0]
        data_costs['Capex_a_PV_USD'] = data_emissions['Capex_a_PV'].values[0]

        # Disconnected Buildings
        Capex_total_disconnected_USD = 0
        Opex_total_disconnected_USD = 0
        Capex_a_total_disconnected_USD = 0
        DCN_barcode = string_network

        for (index, building_name) in zip(DCN_barcode, building_names):
            if index is '0':
                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_name,
                                                                                                      configuration='AHU_ARU_SCU'))
                dfBest = df[df["Best configuration"] == 1]

                if dfBest['VCC to AHU_ARU_SCU Share'].iloc[0] == 1: #FIXME: Check for other options
                    VCC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheet_name="Chiller")
                    VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
                    max_VCC_chiller_size = max(VCC_cost_data['cap_max'].values)
                    Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
                    Inv_LT = VCC_cost_data.iloc[0]['LT_yr']

                if dfBest['single effect ACH to AHU_ARU_SCU Share (FP)'].iloc[0] == 1:
                    Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(config.region),
                                                                 sheet_name="Absorption_chiller")
                    Absorption_chiller_cost_data = Absorption_chiller_cost_data[
                        ['type', 'code', 'cap_min', 'cap_max', 'a', 'b', 'c', 'd', 'e', 'IR_%', 'LT_yr', 'O&M_%']]
                    Absorption_chiller_cost_data = Absorption_chiller_cost_data[
                        Absorption_chiller_cost_data['type'] == 'double']
                    max_ACH_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)
                    Inv_IR = (Absorption_chiller_cost_data.iloc[0]['IR_%']) / 100
                    Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']

                Opex_total_disconnected_USD += dfBest["Operation Costs [CHF]"].iloc[0]
                Capex_a_total_disconnected_USD += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                Capex_total_disconnected_USD += (dfBest["Annualized Investment Costs [CHF]"].iloc[0] * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
        data_costs['Capex_total_disconnected_Mio'] = Capex_total_disconnected_USD / 1000000
        data_costs['Opex_total_disconnected_Mio'] = Opex_total_disconnected_USD / 1000000
        data_costs['Capex_a_disconnected_Mio'] = Capex_a_total_disconnected_USD / 1000000

        data_costs['Capex_a_disconnected_USD'] = Capex_a_total_disconnected_USD
        data_costs['Opex_total_disconnected_USD'] = Opex_total_disconnected_USD

        data_costs['costs_Mio'] = data_raw['population']['costs_Mio'][individual]
        data_costs['emissions_kiloton'] = data_raw['population']['emissions_kiloton'][individual]
        data_costs['prim_energy_TJ'] = data_raw['population']['prim_energy_TJ'][individual]

        # Network costs
        network_features = network_opt.network_opt_main(config, locator)
        network_costs_a_USD = network_features.pipesCosts_DCN_USD * DCN_barcode.count("1") / len(DCN_barcode)
        data_costs['Network_costs_USD'] = network_costs_a_USD
        Inv_IR = 0.05
        Inv_LT = 20
        network_costs_total_USD = (network_costs_a_USD * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
        data_costs['Network_costs_Total_USD'] = network_costs_total_USD
        # Substation costs
        substation_costs_a_USD = 0
        substation_costs_total_USD = 0
        for (index, building_name) in zip(DCN_barcode, building_names):
            if index == "1":
                if df_current_individual['Data Centre'][0] == 1:
                    df = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                     usecols=["Q_space_cooling_and_refrigeration_W"])
                else:
                    df = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                     usecols=["Q_space_cooling_data_center_and_refrigeration_W"])

                subsArray = np.array(df)

                Q_max_W = np.amax(subsArray)
                HEX_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheet_name="HEX")
                HEX_cost_data = HEX_cost_data[HEX_cost_data['code'] == 'HEX1']
                # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
                # capacity for the corresponding technology from the database
                if Q_max_W < HEX_cost_data.iloc[0]['cap_min']:
                    Q_max_W = HEX_cost_data.iloc[0]['cap_min']
                HEX_cost_data = HEX_cost_data[
                    (HEX_cost_data['cap_min'] <= Q_max_W) & (HEX_cost_data['cap_max'] > Q_max_W)]

                Inv_a = HEX_cost_data.iloc[0]['a']
                Inv_b = HEX_cost_data.iloc[0]['b']
                Inv_c = HEX_cost_data.iloc[0]['c']
                Inv_d = HEX_cost_data.iloc[0]['d']
                Inv_e = HEX_cost_data.iloc[0]['e']
                Inv_IR = (HEX_cost_data.iloc[0]['IR_%']) / 100
                Inv_LT = HEX_cost_data.iloc[0]['LT_yr']
                Inv_OM = HEX_cost_data.iloc[0]['O&M_%'] / 100

                InvC = Inv_a + Inv_b * (Q_max_W) ** Inv_c + (Inv_d + Inv_e * Q_max_W) * log(Q_max_W)

                Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
                Opex_fixed = Capex_a * Inv_OM
                substation_costs_total_USD += InvC
                substation_costs_a_USD += Capex_a + Opex_fixed

        data_costs['Substation_costs_USD'] = substation_costs_a_USD
        data_costs['Substation_costs_Total_USD'] = substation_costs_total_USD
        # Electricity Details/Renewable Share
        lca = lca_calculations(locator, config)

        data_costs['Total_electricity_demand_GW'] = (data_electricity['E_total_req_W'].sum()) / 1000000000 # GW
        data_costs['Electricity_for_hotwater_GW'] = (data_electricity['E_hotwater_total_W'].sum()) / 1000000000 # GW
        data_costs['Electricity_for_appliances_GW'] = (data_electricity['E_appliances_total_W'].sum()) / 1000000000 # GW

        renewable_share_electricity = (data_electricity['E_PV_directload_W'].sum() +
                                       data_electricity['E_PV_grid_W'].sum() + data_electricity['E_PVT_directload_W'].sum() +
                                       data_electricity['E_PVT_grid_W'].sum()) * 100 / \
                                      (data_costs['Total_electricity_demand_GW'] * 1000000000)
        data_costs['renewable_share_electricity'] = renewable_share_electricity

        data_costs['Electricity_Costs_Mio'] = ((data_electricity['E_GRID_directload_W'].sum() +
                                                data_electricity[
                                               'E_total_to_grid_W_negative'].sum()) * lca.ELEC_PRICE.mean()) / 1000000


        data_costs['Capex_a_ACH_USD'] = data_costs['Capex_a_ACH_USD'].values[0]
        data_costs['Capex_a_VCC_USD'] = data_costs['Capex_a_VCC_USD'].values[0]
        data_costs['Capex_a_VCC_backup_USD'] = data_costs['Capex_a_VCC_backup_USD'].values[0]
        data_costs['Capex_a_CT_USD'] = data_costs['Capex_a_CT_USD'].values[0]
        data_costs['Capex_a_storage_tank_USD'] = data_costs['Capex_a_Tank_USD'].values[0]
        data_costs['Capex_a_total_pumps_USD'] = data_emissions['Capex_a_pump'].values[0]
        data_costs['Capex_a_CCGT_USD'] = data_costs['Capex_a_CCGT_USD'].values[0]
        data_costs['Capex_a_PV_USD'] = data_emissions['Capex_a_PV'].values[0]

        data_costs['Capex_a_total_Mio'] = (data_costs['Capex_a_ACH_USD'] + data_costs['Capex_a_VCC_USD'] + \
                                           data_costs['Capex_a_VCC_backup_USD'] + data_costs['Capex_a_CT_USD'] + data_costs['Capex_a_storage_tank_USD'] + \
                                           data_costs['Capex_a_total_pumps_USD'] + data_costs['Capex_a_CCGT_USD'] + data_costs['Capex_a_PV_USD'] + Capex_a_total_disconnected_USD + substation_costs_a_USD + network_costs_a_USD) / 1000000

        data_costs['Capex_total_Mio'] = (data_costs['Capex_total_ACH_USD'] + data_costs['Capex_total_VCC_USD'] + data_costs['Capex_total_VCC_backup_USD'] + \
                                    data_costs['Capex_total_storage_tank_USD'] + data_costs['Capex_total_CT_USD'] + data_costs['Capex_total_CCGT_USD'] + \
                                    data_costs['Capex_total_pumps_USD'] + data_costs['Capex_total_PV_USD'] + Capex_total_disconnected_USD + substation_costs_total_USD + network_costs_total_USD) / 1000000

        data_costs['Opex_total_Mio'] = (((data_costs['Opex_total_ACH_USD'] + data_costs['Opex_total_VCC_USD'] + data_costs['Opex_total_VCC_backup_USD'] + \
                                   data_costs['Opex_total_storage_tank_USD'] + data_costs['Opex_total_CT_USD'] + data_costs['Opex_total_CCGT_USD'] + \
                                   data_costs['Opex_total_pumps_USD'] + Opex_total_disconnected_USD)) + data_costs['Opex_total_PV_USD'] + \
                                   data_costs['Total_electricity_demand_GW'] * 1000000000 * lca.ELEC_PRICE.mean()) / 1000000

        data_costs['TAC_Mio'] = data_costs['Capex_a_total_Mio'] + data_costs['Opex_total_Mio']

        # temporary fix for bug in emissions calculation, change it after executive course
        data_costs['total_emissions_kiloton'] = data_costs['emissions_kiloton'] - abs(2 * data_emissions['CO2_PV_disconnected'] / 1000000)
        data_costs['total_prim_energy_TJ'] = data_costs['prim_energy_TJ'] - abs(2 * data_emissions['Eprim_PV_disconnected'] / 1000000)


    return data_costs

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running multicriteria with scenario = %s" % config.scenario)
    print("Running multicriteria for generation = %s" % config.multi_criteria.generations)

    multi_criteria_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())