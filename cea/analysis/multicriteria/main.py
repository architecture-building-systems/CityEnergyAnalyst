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
from cea.technologies.solar.photovoltaic import calc_Cinv_pv
from cea.optimization.constants import PUMP_ETA
from cea.constants import DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3
from cea.optimization.constants import SIZING_MARGIN
from cea.plots.supply_system.individual_activation_curve import individual_activation_curve
from cea.technologies.chiller_vapor_compression import calc_Cinv_VCC
from cea.technologies.chiller_absorption import calc_Cinv
from cea.technologies.cooling_tower import calc_Cinv_CT
import cea.optimization.distribution.network_opt_main as network_opt

from math import ceil, log


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
    generations = config.plots_supply_system.generation
    category = "optimal-energy-systems//single-system"

    # initialize class
    data_generation = preprocessing_generations_data(locator, generations, config)
    individual_list = data_generation['final_generation']['individual_barcode'].index.values
    data_processed = preprocessing_cost_data(locator, data_generation['final_generation'], individual_list[0], config)
    column_names = data_processed.columns.values

    compiled_data = pd.DataFrame(np.zeros([len(individual_list), len(column_names)]), columns=column_names)

    for i, individual in enumerate(individual_list):
        data_processed = preprocessing_cost_data(locator, data_generation['final_generation'], individual, config)
        for name in column_names:
            compiled_data.loc[i][name] = data_processed[name][0]

    return compiled_data


def preprocessing_generations_data(locator, generations, config):

    data_processed = []
    with open(locator.get_optimization_checkpoint(generations), "rb") as fp:
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

def preprocessing_cost_data(locator, data_raw, individual, config):

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

        data_costs = pd.read_csv(os.path.join(locator.get_optimization_slave_investment_cost_detailed_cooling(individual_number, generation_number)))
        data_cooling = pd.read_csv(os.path.join(locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number)))
        data_electricity = pd.read_csv(os.path.join(locator.get_optimization_slave_electricity_activation_pattern_cooling(individual_number, generation_number)))

        # Total CAPEX calculations
        # Absorption Chiller
        Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Absorption_chiller",
                                  usecols=['type', 'code', 'cap_min', 'cap_max', 'a', 'b', 'c', 'd', 'e', 'IR_%',
                                           'LT_yr', 'O&M_%'])
        Absorption_chiller_cost_data = Absorption_chiller_cost_data[Absorption_chiller_cost_data['type'] == 'double']
        max_ACH_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)
        Inv_IR = (Absorption_chiller_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']
        Q_ACH_max_W = data_cooling['Q_from_ACH_W'].max()
        Q_ACH_max_W = Q_ACH_max_W * (1 + SIZING_MARGIN)
        number_of_ACH_chillers = int(ceil(Q_ACH_max_W / max_ACH_chiller_size))
        Q_nom_ACH_W = Q_ACH_max_W / number_of_ACH_chillers
        Capex_a_ACH, Opex_fixed_ACH = calc_Cinv(Q_nom_ACH_W, locator, 'double', config)
        Capex_total_ACH = (Capex_a_ACH * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT) * number_of_ACH_chillers
        data_costs['Capex_total_ACH'] = Capex_total_ACH
        data_costs['Opex_total_ACH'] = np.sum(data_cooling['Opex_var_ACH']) + data_costs['Opex_fixed_ACH']

        # VCC
        VCC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Chiller")
        VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
        max_VCC_chiller_size = max(VCC_cost_data['cap_max'].values)
        Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
        Q_VCC_max_W = data_cooling['Q_from_VCC_W'].max()
        Q_VCC_max_W = Q_VCC_max_W * (1 + SIZING_MARGIN)
        number_of_VCC_chillers = int(ceil(Q_VCC_max_W / max_VCC_chiller_size))
        Q_nom_VCC_W = Q_VCC_max_W / number_of_VCC_chillers
        Capex_a_VCC, Opex_fixed_VCC = calc_Cinv_VCC(Q_nom_VCC_W, locator, config, 'CH3')
        Capex_total_VCC = (Capex_a_VCC * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT) * number_of_VCC_chillers
        data_costs['Capex_total_VCC'] = Capex_total_VCC
        data_costs['Opex_total_VCC'] = np.sum(data_cooling['Opex_var_VCC']) + data_costs['Opex_fixed_VCC']

        # VCC Backup
        Q_VCC_backup_max_W = data_cooling['Q_from_VCC_backup_W'].max()
        Q_VCC_backup_max_W = Q_VCC_backup_max_W * (1 + SIZING_MARGIN)
        number_of_VCC_backup_chillers = int(ceil(Q_VCC_backup_max_W / max_VCC_chiller_size))
        Q_nom_VCC_backup_W = Q_VCC_backup_max_W / number_of_VCC_backup_chillers
        Capex_a_VCC_backup, Opex_fixed_VCC_backup = calc_Cinv_VCC(Q_nom_VCC_backup_W, locator, config, 'CH3')
        Capex_total_VCC_backup = (Capex_a_VCC_backup * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT) * number_of_VCC_backup_chillers
        data_costs['Capex_total_VCC_backup'] = Capex_total_VCC_backup
        data_costs['Opex_total_VCC_backup'] = np.sum(data_cooling['Opex_var_VCC_backup']) + data_costs['Opex_fixed_VCC_backup']


        # Storage Tank
        storage_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="TES")
        storage_cost_data = storage_cost_data[storage_cost_data['code'] == 'TES2']
        Inv_IR = (storage_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = storage_cost_data.iloc[0]['LT_yr']
        Capex_a_storage_tank = data_costs['Capex_a_Tank'][0]
        Capex_total_storage_tank = (Capex_a_storage_tank * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
        data_costs['Capex_total_storage_tank'] = Capex_total_storage_tank
        data_costs['Opex_total_storage_tank'] = np.sum(data_cooling['Opex_var_VCC_backup']) + data_costs['Opex_fixed_Tank']


        # Cooling Tower
        CT_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="CT")
        CT_cost_data = CT_cost_data[CT_cost_data['code'] == 'CT1']
        max_CT_size = max(CT_cost_data['cap_max'].values)
        Inv_IR = (CT_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = CT_cost_data.iloc[0]['LT_yr']
        Qc_CT_max_W = data_cooling['Qc_CT_associated_with_all_chillers_W'].max()
        number_of_CT = int(ceil(Qc_CT_max_W / max_CT_size))
        Qnom_CT_W = Qc_CT_max_W/number_of_CT
        Capex_a_CT, Opex_fixed_CT = calc_Cinv_CT(Qnom_CT_W, locator, config, 'CT1')
        Capex_total_CT = (Capex_a_CT * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT) * number_of_CT
        data_costs['Capex_total_CT'] = Capex_total_CT
        data_costs['Opex_total_CT'] = np.sum(data_cooling['Opex_var_CT']) + data_costs['Opex_fixed_CT']

        # CCGT
        CCGT_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="CCGT")
        technology_code = list(set(CCGT_cost_data['code']))
        CCGT_cost_data = CCGT_cost_data[CCGT_cost_data['code'] == technology_code[0]]
        Inv_IR = (CCGT_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = CCGT_cost_data.iloc[0]['LT_yr']
        Capex_a_CCGT = data_costs['Capex_a_CCGT'][0]
        Capex_total_CCGT = (Capex_a_CCGT * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
        data_costs['Capex_total_CCGT'] = Capex_total_CCGT
        data_costs['Opex_total_CT'] = np.sum(data_cooling['Opex_var_CCGT']) + data_costs['Opex_fixed_CCGT']

        # pump
        network_features = network_opt.network_opt_main(config, locator)
        DCN_barcode = ""
        for name in building_names:
            DCN_barcode += str(df_current_individual[name + ' DCN'][0])
        if df_current_individual['Data Centre'][0] == 1:
            df = pd.read_csv(locator.get_optimization_network_data_folder("Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"),
                             usecols=["mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers"])
        else:
            df = pd.read_csv(locator.get_optimization_network_data_folder("Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"),
                             usecols=["mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers"])
        mdotA_kgpers = np.array(df)
        mdotnMax_kgpers = np.amax(mdotA_kgpers)
        deltaPmax = np.max((network_features.DeltaP_DCN) * DCN_barcode.count("1") / len(DCN_barcode))
        E_pumping_required_W = mdotnMax_kgpers * deltaPmax / DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3
        P_motor_tot_W = E_pumping_required_W / PUMP_ETA  # electricty to run the motor
        Pump_max_kW = 375.0
        Pump_min_kW = 0.5
        nPumps = int(np.ceil(P_motor_tot_W / 1000.0 / Pump_max_kW))
        # if the nominal load (electric) > 375kW, a new pump is installed
        Pump_Array_W = np.zeros((nPumps))
        Pump_Remain_W = P_motor_tot_W
        Capex_total_pumps = 0
        for pump_i in range(nPumps):
            # calculate pump nominal capacity
            Pump_Array_W[pump_i] = min(Pump_Remain_W, Pump_max_kW * 1000)
            if Pump_Array_W[pump_i] < Pump_min_kW * 1000:
                Pump_Array_W[pump_i] = Pump_min_kW * 1000
            Pump_Remain_W -= Pump_Array_W[pump_i]
            pump_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Pump")
            pump_cost_data = pump_cost_data[pump_cost_data['code'] == 'PU1']
            # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
            # capacity for the corresponding technology from the database
            if Pump_Array_W[pump_i] < pump_cost_data.iloc[0]['cap_min']:
                Pump_Array_W[pump_i] = pump_cost_data.iloc[0]['cap_min']
            pump_cost_data = pump_cost_data[
                (pump_cost_data['cap_min'] <= Pump_Array_W[pump_i]) & (
                            pump_cost_data['cap_max'] > Pump_Array_W[pump_i])]
            Inv_a = pump_cost_data.iloc[0]['a']
            Inv_b = pump_cost_data.iloc[0]['b']
            Inv_c = pump_cost_data.iloc[0]['c']
            Inv_d = pump_cost_data.iloc[0]['d']
            Inv_e = pump_cost_data.iloc[0]['e']
            Inv_IR = (pump_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = pump_cost_data.iloc[0]['LT_yr']
            Inv_OM = pump_cost_data.iloc[0]['O&M_%'] / 100
            InvC = Inv_a + Inv_b * (Pump_Array_W[pump_i]) ** Inv_c + (Inv_d + Inv_e * Pump_Array_W[pump_i]) * log(
                Pump_Array_W[pump_i])
            Capex_total_pumps += InvC
        data_costs['Capex_total_pumps'] = Capex_total_pumps
        data_costs['Opex_total_pumps'] = data_costs['Opex_fixed_pump'] + data_costs['Opex_fixed_pump']

        # PV
        PV_peak_kW = data_electricity['E_PV_W'].max() / 1000
        Capex_a_PV, Opex_fixed_PV = calc_Cinv_pv(PV_peak_kW, locator, config)
        PV_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="PV")
        technology_code = list(set(PV_cost_data['code']))
        PV_cost_data[PV_cost_data['code'] == technology_code[0]]
        Inv_IR = (PV_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = PV_cost_data.iloc[0]['LT_yr']
        Capex_total_PV = (Capex_a_PV * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
        data_costs['Capex_total_PV'] = Capex_total_PV
        data_costs['Opex_total_PV'] = -np.sum(data_electricity['KEV']) + Opex_fixed_PV

        # Disconnected Buildings
        Capex_total_disconnected = 0
        Opex_total_disconnected = 0

        for (index, building_name) in zip(DCN_barcode, building_names):
            if index is '1':
                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                                      configuration='AHU_ARU_SCU'))
                dfBest = df[df["Best configuration"] == 1]

                if dfBest['VCC to AHU_ARU_SCU Share'].iloc[0] == 1: #FIXME: Check for other options
                    Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
                    Inv_LT = VCC_cost_data.iloc[0]['LT_yr']

                if dfBest['single effect ACH to AHU_ARU_SCU Share (FP)'].iloc[0] == 1:
                    Inv_IR = (Absorption_chiller_cost_data.iloc[0]['IR_%']) / 100
                    Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']

                Opex_total_disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                Capex_total_disconnected += (dfBest["Annualized Investment Costs [CHF]"].iloc[0] * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
        data_costs['Capex_total_disconnected_Mio'] = Capex_total_disconnected / 1000000
        data_costs['Opex_total_disconnected_Mio'] = Opex_total_disconnected / 1000000

        data_costs['costs_Mio'] = data_raw['population']['costs_Mio'][individual]
        data_costs['emissions_ton'] = data_raw['population']['emissions_ton'][individual]
        data_costs['prim_energy_GJ'] = data_raw['population']['prim_energy_GJ'][individual]

        print (Capex_total_ACH)
        print (Capex_total_VCC)
        print (Capex_total_VCC_backup)
        print (Capex_total_storage_tank)
        print (Capex_total_CT)
        print (Capex_total_CCGT)
        print (Capex_total_pumps)
        print (Capex_total_PV)
        print (Capex_total_disconnected)

        # Electricity Details/Renewable Share
        renewable_share_to_directload_W = data_electricity['E_PV_to_directload_W'].sum()
        renewable_share_to_grid_W = data_electricity['E_PV_to_grid_W'].sum()
        total_electricity_demand_W = data_electricity['E_total_req_W'].sum()
        renewable_share_electricity = (renewable_share_to_directload_W + renewable_share_to_grid_W) * 100 / total_electricity_demand_W
        data_costs['renewable_share_electricity'] = renewable_share_electricity

        print (data_costs)

    return data_costs

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generations = %s" % config.plots_supply_system.generation)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())