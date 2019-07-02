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
from cea.optimization.lca_calculations import LcaCalculations
from cea.technologies.heat_exchangers import calc_Cinv_HEX
import cea.optimization.distribution.network_optimization_features as network_opt
from cea.analysis.multicriteria.optimization_post_processing.locating_individuals_in_generation_script import \
    locating_individuals_in_generation_script, create_data_address_file
from math import ceil, log

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def multi_criteria_main(locator, config):
    # local variables
    generation = config.multi_criteria.generations
    network_type = config.multi_criteria.network_type

    # This calculates the exact path of the individual
    # It might be that this inidividual was repeated already some generations back
    # so we make sure that a pointer to the right adress exists first
    if not os.path.exists(locator.get_address_of_individuals_of_a_generation(generation)):
        data_address = locating_individuals_in_generation_script(generation, locator)
    else:
        data_address = pd.read_csv(locator.get_address_of_individuals_of_a_generation(generation))

    # import data storing information about the geneartion
    generation_data = pd.read_csv(locator.get_optimization_individuals_in_generation(generation))

    # compile cost data
    if network_type == 'DC':
        # Preprocess data
        data_generation = preprocessing_generations_data(locator, generation, network_type)
        objectives = data_generation['population']
        individual_list = objectives.axes[0].values

        # This does the work
        compiled_data_df = pd.DataFrame()
        for i, individual in enumerate(individual_list):
            compiled_data_df = compiled_data_df.append(preprocessing_cost_data_DC(individual,
                                                                                  locator,
                                                                                  data_generation,
                                                                                  data_address,
                                                                                  config), ignore_index=True)
        compiled_data_df = compiled_data_df.assign(individual=individual_list)

    if network_type == 'DH':
        # Preprocess data
        data_generation = preprocessing_generations_data(locator, generation, config.multi_criteria.network_type)
        objectives = data_generation['population']
        individual_list = objectives.axes[0].values

        # compile the data
        compiled_data_df = pd.DataFrame()
        for i, individual in enumerate(individual_list):
            compiled_data_df = compiled_data_df.append(preprocessing_cost_data_DH(individual,
                                                                                  locator,
                                                                                  data_generation,
                                                                                  data_address,
                                                                                  config), ignore_index=True)
        compiled_data_df['individual'] = individual_list

    # normalize data
    compiled_data_df = normalize_compiled_data(compiled_data_df)
    # rank data
    compiled_data_df['TAC_rank'] = compiled_data_df['normalized_TAC'].rank(ascending=True)
    compiled_data_df['emissions_rank'] = compiled_data_df['normalized_emissions'].rank(ascending=True)
    compiled_data_df['prim_rank'] = compiled_data_df['normalized_prim'].rank(ascending=True)

    ## user defined mcda
    compiled_data_df['user_MCDA'] = compiled_data_df[
                                        'normalized_Capex_total'] * config.multi_criteria.capextotal * config.multi_criteria.economicsustainability + \
                                    compiled_data_df[
                                        'normalized_Opex'] * config.multi_criteria.opex * config.multi_criteria.economicsustainability + \
                                    compiled_data_df[
                                        'normalized_TAC'] * config.multi_criteria.annualizedcosts * config.multi_criteria.economicsustainability + \
                                    compiled_data_df[
                                        'normalized_emissions'] * config.multi_criteria.emissions * config.multi_criteria.environmentalsustainability + \
                                    compiled_data_df[
                                        'normalized_prim'] * config.multi_criteria.primaryenergy * config.multi_criteria.environmentalsustainability + \
                                    compiled_data_df[
                                        'normalized_renewable_share'] * config.multi_criteria.renewableshare * config.multi_criteria.socialsustainability

    compiled_data_df['user_MCDA_rank'] = compiled_data_df['user_MCDA'].rank(ascending=True)

    compiled_data_df.to_csv(locator.get_multi_criteria_analysis(generation))

    return


def normalize_compiled_data(compiled_data_df):
    # TAC
    if (max(compiled_data_df['TAC_Mio']) - min(compiled_data_df['TAC_Mio'])) > 1E-8:
        normalized_TAC = (compiled_data_df['TAC_Mio'] - min(compiled_data_df['TAC_Mio'])) / (
                max(compiled_data_df['TAC_Mio']) - min(compiled_data_df['TAC_Mio']))
    else:
        normalized_TAC = [1] * len(compiled_data_df['TAC_Mio'])
    # emission
    if (max(compiled_data_df['total_emissions_kiloton']) - min(compiled_data_df['total_emissions_kiloton'])) > 1E-8:
        normalized_emissions = (compiled_data_df['total_emissions_kiloton'] - min(
            compiled_data_df['total_emissions_kiloton'])) / (
                                       max(compiled_data_df['total_emissions_kiloton']) - min(
                                   compiled_data_df['total_emissions_kiloton']))
    else:
        normalized_emissions = [1] * len(compiled_data_df['total_emissions_kiloton'])
    # primary energy
    if (max(compiled_data_df['total_prim_energy_TJ']) - min(compiled_data_df['total_prim_energy_TJ'])) > 1E-8:
        normalized_prim = (compiled_data_df['total_prim_energy_TJ'] - min(compiled_data_df['total_prim_energy_TJ'])) / (
                max(compiled_data_df['total_prim_energy_TJ']) - min(compiled_data_df['total_prim_energy_TJ']))
    else:
        normalized_prim = [1] * len(compiled_data_df['total_prim_energy_TJ'])
    # capex
    if (max(compiled_data_df['Capex_total_Mio']) - min(compiled_data_df['Capex_total_Mio'])) > 1E-8:
        normalized_Capex_total = (compiled_data_df['Capex_total_Mio'] - min(compiled_data_df['Capex_total_Mio'])) / (
                max(compiled_data_df['Capex_total_Mio']) - min(compiled_data_df['Capex_total_Mio']))
    else:
        normalized_Capex_total = [1] * len(compiled_data_df['Capex_total_Mio'])
    # opex
    if (max(compiled_data_df['Opex_total_Mio']) - min(compiled_data_df['Opex_total_Mio'])) > 1E-8:
        normalized_Opex = (compiled_data_df['Opex_total_Mio'] - min(compiled_data_df['Opex_total_Mio'])) / (
                max(compiled_data_df['Opex_total_Mio']) - min(compiled_data_df['Opex_total_Mio']))
    else:
        normalized_Opex = [1] * len(compiled_data_df['Opex_total_Mio'])
    # renewable energy share
    if (max(compiled_data_df['renewable_share_electricity']) - min(
            compiled_data_df['renewable_share_electricity'])) > 1E-8:
        normalized_renewable_share = (compiled_data_df['renewable_share_electricity'] - min(
            compiled_data_df['renewable_share_electricity'])) / (
                                             max(compiled_data_df['renewable_share_electricity']) - min(
                                         compiled_data_df['renewable_share_electricity']))
    else:
        normalized_renewable_share = [1] * compiled_data_df['renewable_share_electricity']
    compiled_data_df = compiled_data_df.assign(normalized_TAC=normalized_TAC)
    compiled_data_df = compiled_data_df.assign(normalized_emissions=normalized_emissions)
    compiled_data_df = compiled_data_df.assign(normalized_prim=normalized_prim)
    compiled_data_df = compiled_data_df.assign(normalized_Capex_total=normalized_Capex_total)
    compiled_data_df = compiled_data_df.assign(normalized_Opex=normalized_Opex)
    compiled_data_df = compiled_data_df.assign(normalized_renewable_share=normalized_renewable_share)
    return compiled_data_df


def preprocessing_generations_data(locator, generation_number, district_netowrk_type):
    """
    compile data from all individuals in this generation
    :param locator:
    :param generation_number:
    :return:
    """

    # load data of geneartion
    with open(locator.get_optimization_checkpoint(generation_number), "rb") as fp:
        data = json.load(fp)

    # change units of population (e.g., form kW to MW)
    df_population, individual_barcode, individual_names = Change_units_population(generation_number, locator, data)

    # change units of the hall of fame (e.g., form kW to MW)
    df_halloffame = change_units_hall_of_fame(data)

    # get values of barcode of individuals
    df_individual_barcode = pd.DataFrame({'Name': individual_names,
                                          'individual_barcode': individual_barcode}).set_index("Name")

    # compile network barcodes
    df_network = df_network_barcodes(data, district_netowrk_type, individual_names)

    data_processed = {'population': df_population,
                      'halloffame': df_halloffame,
                      'network': df_network,
                      'spread': data['spread'],
                      'euclidean_distance': data['euclidean_distance'],
                      'individual_barcode': df_individual_barcode}

    print('compiled data of all individuals in this generation: ', generation_number)

    return data_processed


def df_network_barcodes(data, network_type, individual_names):
    network_dict = {}
    for i, ind in enumerate(individual_names):
        if network_type == 'DC':
            district_network_list = data['DCN_list_All']
        else:  # DH
            district_network_list = data['DHN_list_All']
        network_dict[ind] = str("".join(map(str, district_network_list)))
    df_network = pd.DataFrame.from_dict(network_dict, orient='index', columns=['network'])
    return df_network


def Change_units_population(generation_number, locator, data):
    # compile objectives of all individuals in this generation
    # convert to millions
    costs_Mio = [round(objectives[0] / 1000000, 2) for objectives in data['tested_population_fitness']]
    # convert to tons x 10^3 (kiloton)
    emissions_kiloton = [round(objectives[1] / 1000000, 2) for objectives in data['tested_population_fitness']]
    # convert to gigajoules x 10^3 (Terajoules)
    prim_energy_TJ = [round(objectives[2] / 1000000, 2) for objectives in data['tested_population_fitness']]
    individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]
    df_population = pd.DataFrame({'Name': individual_names, 'costs_Mio': costs_Mio,
                                  'emissions_kiloton': emissions_kiloton,
                                  'prim_energy_TJ': prim_energy_TJ
                                  }).set_index("Name")
    # compile barcodes of all individuals in this generation
    individual_barcode = [[str(ind) if type(ind) == float else str(ind) for ind in
                           individual] for individual in data['tested_population']]
    return df_population, individual_barcode, individual_names


def change_units_hall_of_fame(data):
    # compile objectives of individuals in the hall of fame in this generation
    # convert to millions
    costs_Mio_HOF = [round(objectives[0] / 1000000, 2) for objectives in data['halloffame_fitness']]
    # convert to tons x 10^3
    emissions_kiloton_HOF = [round(objectives[1] / 1000000, 2) for objectives in data['halloffame_fitness']]
    # convert to gigajoules x 10^3
    prim_energy_TJ_HOF = [round(objectives[2] / 1000000, 2) for objectives in data['halloffame_fitness']]
    individual_names_HOF = ['ind' + str(i) for i in range(len(costs_Mio_HOF))]
    df_halloffame = pd.DataFrame({'Name': individual_names_HOF, 'costs_Mio': costs_Mio_HOF,
                                  'emissions_kiloton': emissions_kiloton_HOF,
                                  'prim_energy_TJ': prim_energy_TJ_HOF}).set_index("Name")
    return df_halloffame


def preprocessing_cost_data_DC(individual, locator, data_raw, data_address, config):
    # local
    string_network = data_raw['network'].loc[individual].values[0]
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    data_address = data_address[data_address['individual_list'] == individual]

    # get data about individual (pointer)
    generation_number = data_address['generation_number_address'].values[0]
    individual_number = data_address['individual_number_address'].values[0]

    # get data about the activation patterns of these buildings (main units)
    data_costs = pd.read_csv(os.path.join(
        locator.get_optimization_slave_investment_cost_detailed_cooling(individual_number, generation_number)))
    data_cooling = pd.read_csv(
        os.path.join(locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number)))
    data_electricity = pd.read_csv(os.path.join(
        locator.get_optimization_slave_electricity_activation_pattern_cooling(individual_number, generation_number)))
    data_emissions = pd.read_csv(
        os.path.join(locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number)))

    # Total CAPEX calculations
    # Absorption Chiller
    data_costs['Capex_total_ACH_USD'] = data_costs['Capex_ACH_USD'].values[0]
    data_costs['Opex_total_ACH_USD'] = np.sum(data_cooling['Opex_var_ACH_USD']) + data_costs['Opex_fixed_ACH_USD']

    # VCC
    data_costs['Capex_total_VCC_USD'] = data_costs['Capex_VCC_USD'].values[0]
    data_costs['Opex_total_VCC_USD'] = np.sum(data_cooling['Opex_var_VCC_USD']) + data_costs['Opex_fixed_VCC_USD']

    # VCC Backup
    data_costs['Capex_total_VCC_backup_USD'] = data_costs['Capex_VCC_backup_USD']
    data_costs['Opex_total_VCC_backup_USD'] = np.sum(data_cooling['Opex_var_VCC_backup_USD']) + data_costs[
        'Opex_fixed_VCC_backup_USD']

    # Storage Tank
    data_costs['Capex_total_storage_tank_USD'] = data_costs['Capex_Tank_USD']
    data_costs['Opex_total_storage_tank_USD'] = data_costs['Opex_fixed_Tank_USD']

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
    DCN_barcode = string_network  # TODO: switch between DCN and DHN

    for (index, building_name) in zip(DCN_barcode, building_names):
        if index is '0':
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_name,
                                                                                                   configuration='AHU_ARU_SCU'))
            dfBest = df[df["Best configuration"] == 1]

            if dfBest['VCC to AHU_ARU_SCU Share'].iloc[0] == 1:  # FIXME: Check for other options
                VCC_cost_data = pd.read_excel(locator.get_supply_systems(), sheet_name="Chiller")
                VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
                max_VCC_chiller_size = max(VCC_cost_data['cap_max'].values)
                Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
                Inv_LT = VCC_cost_data.iloc[0]['LT_yr']

            if dfBest['single effect ACH to AHU_ARU_SCU Share (FP)'].iloc[0] == 1:
                Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(),
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
            Capex_total_disconnected_USD += (
                    dfBest["Annualized Investment Costs [CHF]"].iloc[0] * ((1 + Inv_IR) ** Inv_LT - 1) / (
                Inv_IR) * (1 + Inv_IR) ** Inv_LT)
    data_costs['Capex_total_disconnected_Mio'] = Capex_total_disconnected_USD / 1000000
    data_costs['Opex_total_disconnected_Mio'] = Opex_total_disconnected_USD / 1000000
    data_costs['Capex_a_disconnected_Mio'] = Capex_a_total_disconnected_USD / 1000000

    data_costs['Capex_a_disconnected_USD'] = Capex_a_total_disconnected_USD
    data_costs['Opex_total_disconnected_USD'] = Opex_total_disconnected_USD

    data_costs['costs_Mio'] = data_raw['population']['costs_Mio'][individual]
    data_costs['emissions_kiloton'] = data_raw['population']['emissions_kiloton'][individual]
    data_costs['prim_energy_TJ'] = data_raw['population']['prim_energy_TJ'][individual]

    # Network costs
    network_features = network_opt.NetworkOptimizationFeatures(config,
                                                    locator)  # TODO: check if it is using the latest run of result, if yes, it is wrong
    network_costs_a_USD = network_features.pipesCosts_DCN_USD * DCN_barcode.count("1") / len(
        DCN_barcode)  # FIXME: what does this mean?
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
            HEX_cost_data = pd.read_excel(locator.get_supply_systems(), sheet_name="HEX")
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
    lca = LcaCalculations(locator, config.detailed_electricity_pricing)

    data_costs['Total_electricity_demand_GW'] = (data_electricity['E_total_req_W'].sum()) / 1000000000  # GW
    data_costs['Electricity_for_hotwater_GW'] = (data_electricity['E_hotwater_total_W'].sum()) / 1000000000  # GW
    data_costs['Electricity_for_appliances_GW'] = (data_electricity['E_appliances_total_W'].sum()) / 1000000000  # GW

    renewable_share_electricity = (data_electricity['E_PV_directload_W'].sum() +
                                   data_electricity['E_PV_grid_W'].sum() + data_electricity[
                                       'E_PVT_directload_W'].sum() +
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
                                       data_costs['Capex_a_VCC_backup_USD'] + data_costs['Capex_a_CT_USD'] + data_costs[
                                           'Capex_a_storage_tank_USD'] + \
                                       data_costs['Capex_a_total_pumps_USD'] + data_costs['Capex_a_CCGT_USD'] +
                                       data_costs[
                                           'Capex_a_PV_USD'] + Capex_a_total_disconnected_USD + substation_costs_a_USD + network_costs_a_USD) / 1000000

    data_costs['Capex_total_Mio'] = (data_costs['Capex_total_ACH_USD'] + data_costs['Capex_total_VCC_USD'] + data_costs[
        'Capex_total_VCC_backup_USD'] + \
                                     data_costs['Capex_total_storage_tank_USD'] + data_costs['Capex_total_CT_USD'] +
                                     data_costs['Capex_total_CCGT_USD'] + \
                                     data_costs['Capex_total_pumps_USD'] + data_costs[
                                         'Capex_total_PV_USD'] + Capex_total_disconnected_USD + substation_costs_total_USD + network_costs_total_USD) / 1000000

    data_costs['Opex_total_Mio'] = (((data_costs['Opex_total_ACH_USD'] + data_costs['Opex_total_VCC_USD'] + data_costs[
        'Opex_total_VCC_backup_USD'] + \
                                      data_costs['Opex_total_storage_tank_USD'] + data_costs['Opex_total_CT_USD'] +
                                      data_costs['Opex_total_CCGT_USD'] + \
                                      data_costs['Opex_total_pumps_USD'] + Opex_total_disconnected_USD)) + data_costs[
                                        'Opex_total_PV_USD'] + \
                                    data_costs[
                                        'Total_electricity_demand_GW'] * 1000000000 * lca.ELEC_PRICE.mean()) / 1000000

    data_costs['TAC_Mio'] = data_costs['Capex_a_total_Mio'] + data_costs['Opex_total_Mio']

    # temporary fix for bug in emissions calculation, change it after executive course
    data_costs['total_emissions_kiloton'] = data_costs['emissions_kiloton'] - abs(
        2 * data_emissions['CO2_PV_disconnected'] / 1000000)
    data_costs['total_prim_energy_TJ'] = data_costs['prim_energy_TJ'] - abs(
        2 * data_emissions['Eprim_PV_disconnected'] / 1000000)

    return data_costs


def preprocessing_cost_data_DH(individual, locator, data_raw, data_address, config):
    # local variables
    string_network = data_raw['network'].loc[individual].values[0]
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    individual_barcode_list = data_raw['individual_barcode'].loc[individual].values[0]

    # get generation/individual number
    data_address = data_address[data_address['individual_list'] == individual]
    generation_number = data_address['generation_number_address'].values[0]
    individual_number = data_address['individual_number_address'].values[0]

    # get data about the activation patterns of these buildings (main units)
    data_costs = pd.read_csv(
        os.path.join(locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number)))
    data_activation_pattern = pd.read_csv(
        os.path.join(locator.get_optimization_slave_heating_activation_pattern(individual_number, generation_number)))
    data_electricity = pd.read_csv(os.path.join(
        locator.get_optimization_slave_electricity_activation_pattern_heating(individual_number, generation_number)))
    data_emissions = pd.read_csv(
        os.path.join(locator.get_optimization_slave_investment_cost_detailed(individual_number, generation_number)))

    # Disconnected Buildings
    Capex_total_disconnected_USD = 0
    Opex_total_disconnected_USD = 0
    Capex_a_total_disconnected_USD = 0
    district_network_barcode = string_network

    for (index, building_name) in zip(district_network_barcode, building_names):
        if index is '0':
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_heating(building_name))
            dfBest = df[df["Best configuration"] == 1]
            Opex_total_disconnected_USD += dfBest["Operation Costs [CHF]"].iloc[0]
            Capex_a_total_disconnected_USD += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
            Capex_total_disconnected_USD += dfBest["Total Costs [CHF]"].iloc[0]

    data_costs['Capex_total_disconnected_Mio'] = Capex_total_disconnected_USD / 1E6
    data_costs['Opex_total_disconnected_Mio'] = Opex_total_disconnected_USD / 1E6
    data_costs['Capex_a_disconnected_Mio'] = Capex_a_total_disconnected_USD / 1E6

    data_costs['Capex_a_disconnected_USD'] = Capex_a_total_disconnected_USD
    data_costs['Opex_total_disconnected_USD'] = Opex_total_disconnected_USD

    # get objectives
    data_costs['costs_Mio'] = data_raw['population']['costs_Mio'][individual]
    data_costs['emissions_kiloton'] = data_raw['population']['emissions_kiloton'][individual]
    data_costs['prim_energy_TJ'] = data_raw['population']['prim_energy_TJ'][individual]

    # get Network costs
    network_features = network_opt.NetworkOptimizationFeatures(config, locator)
    network_costs_a_USD = network_features.pipesCosts_DCN_USD * district_network_barcode.count("1") / len(
        district_network_barcode)
    data_costs['Network_costs_USD'] = network_costs_a_USD
    Inv_IR = 0.05
    Inv_LT = 20
    network_costs_total_USD = (network_costs_a_USD * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
    data_costs['Network_costs_Total_USD'] = network_costs_total_USD
    # Substation costs
    substation_costs_a_USD = 0
    substation_costs_total_USD = 0
    for (index, building_name) in zip(district_network_barcode, building_names):
        if index == "1":
            df = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                             usecols=["Q_dhw_W", "Q_heating_W"])
            subsArray = np.array(df)

            Q_max_W = np.amax(subsArray[:, 0] + subsArray[:, 1])
            Capex_a_HEX_building_USD, Opex_fixed_HEX_building_USD, Capex_HEX_building_USD = calc_Cinv_HEX(Q_max_W,
                                                                                                          locator,
                                                                                                          config,
                                                                                                          'HEX1')
            substation_costs_total_USD += Capex_HEX_building_USD
            substation_costs_a_USD += Capex_a_HEX_building_USD + Opex_fixed_HEX_building_USD

    data_costs['Substation_costs_USD'] = substation_costs_a_USD
    data_costs['Substation_costs_Total_USD'] = substation_costs_total_USD

    # Electricity Details/Renewable Share
    lca = LcaCalculations(locator, config.detailed_electricity_pricing)

    data_costs['Total_electricity_demand_GW'] = (data_electricity['E_total_req_W'].sum()) / 1E9  # GW
    data_costs['Electricity_for_hotwater_GW'] = (data_electricity['E_hotwater_total_W'].sum()) / 1E9  # GW
    data_costs['Electricity_for_appliances_GW'] = (data_electricity['E_appliances_total_W'].sum()) / 1E9  # GW

    renewable_share_electricity = (data_electricity['E_PV_directload_W'].sum() +
                                   data_electricity['E_PV_grid_W'].sum() + data_electricity[
                                       'E_PVT_directload_W'].sum() +
                                   data_electricity['E_PVT_grid_W'].sum()) * 100 / \
                                  (data_costs['Total_electricity_demand_GW'] * 1E9)  # [%]
    data_costs['renewable_share_electricity'] = renewable_share_electricity

    data_costs['Electricity_Costs_Mio'] = ((data_electricity['E_GRID_directload_W'].sum() +
                                            data_electricity[
                                                'E_total_to_grid_W_negative'].sum()) * lca.ELEC_PRICE.mean()) / 1E6

    # analyzed criteria
    capex_a_sum = data_costs.filter(like='Capex_a').sum(axis=1)[0]
    data_costs['Capex_a_total_Mio'] = (
                                              capex_a_sum + Capex_a_total_disconnected_USD + substation_costs_a_USD + network_costs_a_USD) / 1E6
    capex_sum = data_costs.filter(like='Capex').sum(axis=1)[0] - capex_a_sum
    data_costs['Capex_total_Mio'] = (
                                            capex_sum + Capex_total_disconnected_USD + substation_costs_total_USD + network_costs_total_USD) / 1E6
    opex_sum = data_costs.filter(like='Opex').sum(axis=1)[0]
    data_costs['Opex_total_Mio'] = (opex_sum + data_costs[
        'Total_electricity_demand_GW'] * 1E9 * lca.ELEC_PRICE.mean()) / 1E6

    data_costs['TAC_Mio'] = data_costs['Capex_a_total_Mio'] + data_costs['Opex_total_Mio']

    # temporary fix for bug in emissions calculation, change it after executive course
    data_costs['total_emissions_kiloton'] = data_costs['emissions_kiloton'] - abs(
        2 * data_emissions['CO2_PV_disconnected'] / 1E6)
    data_costs['total_prim_energy_TJ'] = data_costs['prim_energy_TJ'] - abs(
        2 * data_emissions['Eprim_PV_disconnected'] / 1E6)

    return data_costs


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running multicriteria with scenario = %s" % config.scenario)
    print("Running multicriteria for generation = %s" % config.multi_criteria.generations)

    multi_criteria_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
