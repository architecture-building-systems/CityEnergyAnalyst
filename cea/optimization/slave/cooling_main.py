"""
Disctrict Cooling Network Calculations.

Use free cooling from Lake as long as possible ( HP Lake operation from slave)
If Lake exhausted, then use other supply technologies

"""
from __future__ import division
import time
import numpy as np
import pandas as pd
import cea.config
import cea.technologies.cooling_tower as CTModel
import cea.technologies.chiller_vapor_compression as VCCModel
import cea.technologies.pumps as PumpModel
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.cogeneration as cogeneration
import cea.technologies.storage_tank as storage_tank
import cea.technologies.thermal_storage as thermal_storage
from cea.optimization.slave.cooling_resource_activation import cooling_resource_activator
from cea.technologies.thermal_network.thermal_network import calculate_ground_temperature
from cea.constants import WH_TO_J
from cea.optimization.constants import SIZING_MARGIN, PUMP_ETA, DELTA_U, \
    ACH_T_IN_FROM_CHP, ACH_TYPE_DOUBLE, T_TANK_FULLY_CHARGED_K, T_TANK_FULLY_DISCHARGED_K, PIPEINTERESTRATE, PIPELIFETIME
import cea.technologies.pumps as pumps
from math import log, ceil


__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def cooling_calculations_of_DC_buildings(locator, master_to_slave_vars, ntwFeat, prices, lca, config, reduced_timesteps_flag):
    """
    Computes the parameters for the cooling of the complete DCN

    :param locator: path to res folder
    :param ntwFeat: network features
    :param prices: Prices imported from the database
    :type locator: string
    :type ntwFeat: class
    :type prices: class
    :return: costs, co2, prim
    :rtype: tuple
    """

    ############# Recover the cooling needs
    # Cooling demands in a neighborhood are divided into three categories currently. They are
    # 1. Space Cooling in buildings
    # 2. Data center Cooling
    # 3. Refrigeration Needs
    # Data center cooling can also be done by recovering the heat and heating other demands during the same time
    # whereas Space cooling and refrigeration needs are to be provided by District Cooling Network or decentralized cooling
    # Currently, all the buildings are assumed to be connected to DCN
    # In the following code, the cooling demands of Space cooling and refrigeration are first satisfied by using Lake and VCC
    # This is then followed by checking of the Heat recovery from Data Centre, if it is allowed, then the corresponding
    # cooling demand is ignored. If not, the corresponding coolind demand is also satisfied by DCN.

    t0 = time.time()
    DCN_barcode = master_to_slave_vars.DCN_barcode
    print ('Cooling Main is Running')

    # Space cooling previously aggregated in the substation routine
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        df = pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                     usecols=["T_DCNf_space_cooling_and_refrigeration_sup_K", "T_DCNf_space_cooling_and_refrigeration_re_K",
                              "mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers"])
        df = df.fillna(0)
        T_sup_K = df['T_DCNf_space_cooling_and_refrigeration_sup_K'].values
        T_re_K = df['T_DCNf_space_cooling_and_refrigeration_re_K'].values
        mdot_kgpers = df['mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers'].values
    else:
        df = pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                     usecols=["T_DCNf_space_cooling_data_center_and_refrigeration_sup_K",
                              "T_DCNf_space_cooling_data_center_and_refrigeration_re_K",
                              "mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers"])
        df = df.fillna(0)
        T_sup_K = df['T_DCNf_space_cooling_data_center_and_refrigeration_sup_K'].values
        T_re_K = df['T_DCNf_space_cooling_data_center_and_refrigeration_re_K'].values
        mdot_kgpers = df['mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers'].values
    DCN_operation_parameters = df.fillna(0)
    DCN_operation_parameters_array = DCN_operation_parameters.values

    Qc_DCN_W = np.array(
        pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                    usecols=["Q_DCNf_space_cooling_and_refrigeration_W",
                             "Q_DCNf_space_cooling_data_center_and_refrigeration_W"]))  # importing the cooling demands of DCN (space cooling + refrigeration)
    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdata_sys_MWhyr"])
    arrayData = np.array(df)

    # total cooling requirements based on the Heat Recovery Flag
    Q_cooling_req_W = np.zeros(8760)
    if master_to_slave_vars.WasteServersHeatRecovery == 0:
        for hour in range(8760):  # summing cooling loads of space cooling, refrigeration and data center
            Q_cooling_req_W[hour] = Qc_DCN_W[hour][1]
    else:
        for hour in range(8760):  # only including cooling loads of space cooling and refrigeration
            Q_cooling_req_W[hour] = Qc_DCN_W[hour][0]

    ############# Recover the heat already taken from the Lake by the heat pumps
    if config.district_heating_network:
        try:
            dfSlave = pd.read_csv(
                locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                          master_to_slave_vars.generation_number),
                usecols=["Q_coldsource_HPLake_W"])
            Q_Lake_Array_W = np.array(dfSlave)

        except:
            Q_Lake_Array_W = [0]
    else:
        Q_Lake_Array_W = [0]

    ### input parameters
    Qc_VCC_max_W = master_to_slave_vars.VCC_cooling_size_W
    Qc_ACH_max_W = master_to_slave_vars.Absorption_chiller_size_W

    T_ground_K = calculate_ground_temperature(locator, config)

    # sizing cold water storage tank
    if master_to_slave_vars.Storage_cooling_size_W > 0:
        Qc_tank_discharge_peak_W = master_to_slave_vars.Storage_cooling_size_W
        Qc_tank_charge_max_W = (Qc_VCC_max_W + Qc_ACH_max_W) * 0.8  # assume reduced capacity when Tsup is lower
        peak_hour = np.argmax(Q_cooling_req_W)
        area_HEX_tank_discharege_m2, UA_HEX_tank_discharge_WperK, \
        area_HEX_tank_charge_m2, UA_HEX_tank_charge_WperK, \
        V_tank_m3 = storage_tank.calc_storage_tank_properties(DCN_operation_parameters, Qc_tank_charge_max_W,
                                                              Qc_tank_discharge_peak_W, peak_hour, master_to_slave_vars)
    else:
        Qc_tank_discharge_peak_W = 0
        Qc_tank_charge_max_W = 0
        area_HEX_tank_discharege_m2 = 0
        UA_HEX_tank_discharge_WperK = 0
        area_HEX_tank_charge_m2 = 0
        UA_HEX_tank_charge_WperK = 0
        V_tank_m3 = 0

    VCC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Chiller")
    VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
    max_VCC_chiller_size = max(VCC_cost_data['cap_max'].values)

    Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(config.region),
                                                 sheetname="Absorption_chiller")
    Absorption_chiller_cost_data = Absorption_chiller_cost_data[Absorption_chiller_cost_data['type'] == ACH_TYPE_DOUBLE]
    max_ACH_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)


    # deciding the number of chillers and the nominal size based on the maximum chiller size
    Qc_VCC_max_W = Qc_VCC_max_W * (1 + SIZING_MARGIN)
    Qc_ACH_max_W = Qc_ACH_max_W * (1 + SIZING_MARGIN)
    Q_peak_load_W = Q_cooling_req_W.max() * (1 + SIZING_MARGIN)

    Qc_VCC_backup_max_W = (Q_peak_load_W - Qc_ACH_max_W - Qc_VCC_max_W - Qc_tank_discharge_peak_W)

    if Qc_VCC_backup_max_W < 0:
        Qc_VCC_backup_max_W = 0

    if Qc_VCC_max_W <= max_VCC_chiller_size:
        Qnom_VCC_W = Qc_VCC_max_W
        number_of_VCC_chillers = 1
    else:
        number_of_VCC_chillers = int(ceil(Qc_VCC_max_W / max_VCC_chiller_size))
        Qnom_VCC_W = Qc_VCC_max_W / number_of_VCC_chillers

    if Qc_VCC_backup_max_W <= max_VCC_chiller_size:
        Qnom_VCC_backup_W = Qc_VCC_backup_max_W
        number_of_VCC_backup_chillers = 1
    else:
        number_of_VCC_backup_chillers = int(ceil(Qc_VCC_backup_max_W / max_VCC_chiller_size))
        Qnom_VCC_backup_W = Qc_VCC_backup_max_W / number_of_VCC_backup_chillers

    if Qc_ACH_max_W <= max_ACH_chiller_size:
        Qnom_ACH_W = Qc_ACH_max_W
        number_of_ACH_chillers = 1
    else:
        number_of_ACH_chillers = int(ceil(Qc_ACH_max_W / max_ACH_chiller_size))
        Qnom_ACH_W = Qc_ACH_max_W / number_of_ACH_chillers

    limits = {'Qc_VCC_max_W': Qc_VCC_max_W, 'Qc_ACH_max_W': Qc_ACH_max_W, 'Qc_peak_load_W': Qc_tank_discharge_peak_W,
              'Qnom_VCC_W': Qnom_VCC_W, 'number_of_VCC_chillers': number_of_VCC_chillers,
              'Qnom_ACH_W': Qnom_ACH_W, 'number_of_ACH_chillers': number_of_ACH_chillers,
              'Qnom_VCC_backup_W': Qnom_VCC_backup_W, 'number_of_VCC_backup_chillers': number_of_VCC_backup_chillers,
              'Qc_tank_discharge_peak_W': Qc_tank_discharge_peak_W, 'Qc_tank_charge_max_W': Qc_tank_charge_max_W,
              'V_tank_m3': V_tank_m3, 'T_tank_fully_charged_K': T_TANK_FULLY_CHARGED_K,
              'area_HEX_tank_discharge_m2': area_HEX_tank_discharege_m2,
              'UA_HEX_tank_discharge_WperK': UA_HEX_tank_discharge_WperK,
              'area_HEX_tank_charge_m2': area_HEX_tank_charge_m2,
              'UA_HEX_tank_charge_WperK': UA_HEX_tank_charge_WperK}

    ### input variables
    lake_available_cooling = pd.read_csv(locator.get_lake_potential(), usecols=['lake_potential'])
    Qc_available_from_lake_W = np.sum(lake_available_cooling).values[0] + np.sum(Q_Lake_Array_W)
    Qc_from_lake_cumulative_W = 0
    cooling_resource_potentials = {'T_tank_K': T_TANK_FULLY_DISCHARGED_K,
                                   'Qc_avail_from_lake_W': Qc_available_from_lake_W,
                                   'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}

    ############# Output results
    network_costs_USD = ntwFeat.pipesCosts_DCN_USD * DCN_barcode.count('1') / master_to_slave_vars.total_buildings
    network_costs_a_USD = network_costs_USD * PIPEINTERESTRATE * (1+ PIPEINTERESTRATE) ** PIPELIFETIME / ((1+PIPEINTERESTRATE) ** PIPELIFETIME - 1)
    costs_a_USD = network_costs_a_USD
    CO2_kgCO2 = 0
    prim_MJ = 0

    nBuild = int(np.shape(arrayData)[0])
    if reduced_timesteps_flag == False:
        start_t = 0
        stop_t = int(np.shape(DCN_operation_parameters)[0])
    else:
        # timesteps in May
        start_t = 2880
        stop_t = 3624
    timesteps = range(start_t, stop_t)

    calfactor_buildings = np.zeros(8760)
    TotalCool = 0
    Qc_from_Lake_W = np.zeros(8760)
    Qc_from_VCC_W = np.zeros(8760)
    Qc_from_ACH_W = np.zeros(8760)
    Qc_from_storage_tank_W = np.zeros(8760)
    Qc_from_VCC_backup_W = np.zeros(8760)

    Qc_req_from_CT_W = np.zeros(8760)
    Qh_req_from_CCGT_W = np.zeros(8760)
    Qh_from_CCGT_W = np.zeros(8760)
    E_gen_CCGT_W = np.zeros(8760)

    opex_var_Lake_USD = np.zeros(8760)
    opex_var_VCC_USD = np.zeros(8760)
    opex_var_ACH_USD = np.zeros(8760)
    opex_var_VCC_backup_USD = np.zeros(8760)
    opex_var_CCGT_USD = np.zeros(8760)
    opex_var_CT_USD = np.zeros(8760)
    E_used_Lake_W = np.zeros(8760)
    E_used_VCC_W = np.zeros(8760)
    E_used_VCC_backup_W = np.zeros(8760)
    E_used_ACH_W = np.zeros(8760)
    E_used_CT_W = np.zeros(8760)
    co2_Lake_kgCO2 = np.zeros(8760)
    co2_VCC_kgCO2 = np.zeros(8760)
    co2_ACH_kgCO2 = np.zeros(8760)
    co2_VCC_backup_kgCO2 = np.zeros(8760)
    co2_CCGT_kgCO2 = np.zeros(8760)
    co2_CT_kgCO2 = np.zeros(8760)
    prim_energy_Lake_MJ = np.zeros(8760)
    prim_energy_VCC_MJ = np.zeros(8760)
    prim_energy_ACH_MJ = np.zeros(8760)
    prim_energy_VCC_backup_MJ = np.zeros(8760)
    prim_energy_CCGT_MJ = np.zeros(8760)
    prim_energy_CT_MJ = np.zeros(8760)
    NG_used_CCGT_W = np.zeros(8760)
    calfactor_total = 0

    for hour in timesteps:  # cooling supply for all buildings excluding cooling loads from data centers
        performance_indicators_output, \
        Qc_supply_to_DCN, calfactor_output, \
        Qc_CT_W, Qh_CHP_ACH_W, \
        cooling_resource_potentials = cooling_resource_activator(mdot_kgpers[hour], T_sup_K[hour], T_re_K[hour],
                                                                 limits, cooling_resource_potentials,
                                                                 T_ground_K[hour], prices, lca, master_to_slave_vars, config, Q_cooling_req_W[hour], locator, hour)

        print (hour)
        # save results for each time-step
        opex_var_Lake_USD[hour] = performance_indicators_output['Opex_var_Lake_USD']
        opex_var_VCC_USD[hour] = performance_indicators_output['Opex_var_VCC_USD']
        opex_var_ACH_USD[hour] = performance_indicators_output['Opex_var_ACH_USD']
        opex_var_VCC_backup_USD[hour] = performance_indicators_output['Opex_var_VCC_backup_USD']
        E_used_Lake_W[hour] = performance_indicators_output['E_used_Lake_W']
        E_used_VCC_W[hour] = performance_indicators_output['E_used_VCC_W']
        E_used_VCC_backup_W[hour] = performance_indicators_output['E_used_VCC_backup_W']
        E_used_ACH_W[hour] = performance_indicators_output['E_used_ACH_W']
        co2_Lake_kgCO2[hour] = performance_indicators_output['CO2_Lake_kgCO2']
        co2_VCC_kgCO2[hour] = performance_indicators_output['CO2_VCC_kgCO2']
        co2_ACH_kgCO2[hour] = performance_indicators_output['CO2_ACH_kgCO2']
        co2_VCC_backup_kgCO2[hour] = performance_indicators_output['CO2_VCC_backup_kgCO2']
        prim_energy_Lake_MJ[hour] = performance_indicators_output['Primary_Energy_Lake_MJ']
        prim_energy_VCC_MJ[hour] = performance_indicators_output['Primary_Energy_VCC_MJ']
        prim_energy_ACH_MJ[hour] = performance_indicators_output['Primary_Energy_ACH_MJ']
        prim_energy_VCC_backup_MJ[hour] = performance_indicators_output['Primary_Energy_VCC_backup_MJ']
        calfactor_buildings[hour] = calfactor_output
        Qc_from_Lake_W[hour] = Qc_supply_to_DCN['Qc_from_Lake_W']
        Qc_from_storage_tank_W[hour] = Qc_supply_to_DCN['Qc_from_Tank_W']
        Qc_from_VCC_W[hour] = Qc_supply_to_DCN['Qc_from_VCC_W']
        Qc_from_ACH_W[hour] = Qc_supply_to_DCN['Qc_from_ACH_W']
        Qc_from_VCC_backup_W[hour] = Qc_supply_to_DCN['Qc_from_backup_VCC_W']
        Qc_req_from_CT_W[hour] = Qc_CT_W
        Qh_req_from_CCGT_W[hour] = Qh_CHP_ACH_W

    if reduced_timesteps_flag:
        reduced_costs_USD = np.sum(opex_var_Lake_USD) + np.sum(opex_var_VCC_USD) + np.sum(opex_var_ACH_USD) + np.sum(opex_var_VCC_backup_USD)
        reduced_CO2_kgCO2 = np.sum(co2_Lake_kgCO2) + np.sum(co2_Lake_kgCO2) + np.sum(co2_ACH_kgCO2) + np.sum(co2_VCC_backup_kgCO2)
        reduced_prim_MJ = np.sum(prim_energy_Lake_MJ) + np.sum(prim_energy_VCC_MJ) + np.sum(prim_energy_ACH_MJ) + np.sum(
        prim_energy_VCC_backup_MJ)

        costs_a_USD += reduced_costs_USD*(8760/(stop_t-start_t))
        CO2_kgCO2 += reduced_CO2_kgCO2*(8760/(stop_t-start_t))
        prim_MJ += reduced_prim_MJ*(8760/(stop_t-start_t))
    else:
        costs_a_USD += np.sum(opex_var_Lake_USD) + np.sum(opex_var_VCC_USD) + np.sum(opex_var_ACH_USD) + np.sum(opex_var_VCC_backup_USD)
        CO2_kgCO2 += np.sum(co2_Lake_kgCO2) + np.sum(co2_Lake_kgCO2) + np.sum(co2_ACH_kgCO2) + np.sum(co2_VCC_backup_kgCO2)
        prim_MJ += np.sum(prim_energy_Lake_MJ) + np.sum(prim_energy_VCC_MJ) + np.sum(prim_energy_ACH_MJ) + np.sum(
            prim_energy_VCC_backup_MJ)


    calfactor_total += np.sum(calfactor_buildings)
    TotalCool += np.sum(Qc_from_Lake_W) + np.sum(Qc_from_VCC_W) + np.sum(Qc_from_ACH_W) + np.sum(Qc_from_VCC_backup_W) + np.sum(Qc_from_storage_tank_W)
    Q_VCC_nom_W = limits['Qnom_VCC_W']
    Q_ACH_nom_W = limits['Qnom_ACH_W']
    Q_VCC_backup_nom_W = limits['Qnom_VCC_backup_W']
    Q_CT_nom_W = np.amax(Qc_req_from_CT_W)
    Qh_req_from_CCGT_max_W = np.amax(Qh_req_from_CCGT_W) # the required heat output from CCGT at peak
    mdot_Max_kgpers = np.amax(DCN_operation_parameters_array[:, 1])  # sizing of DCN network pumps
    Q_GT_nom_W = 0
    ########## Operation of the cooling tower

    if Q_CT_nom_W > 0:
        for hour in timesteps:
            wdot_CT = CTModel.calc_CT(Qc_req_from_CT_W[hour], Q_CT_nom_W)
            opex_var_CT_USD[hour] = (wdot_CT) * lca.ELEC_PRICE[hour]
            co2_CT_kgCO2[hour] = (wdot_CT) * lca.EL_TO_CO2 * 3600E-6
            prim_energy_CT_MJ[hour] = (wdot_CT) * lca.EL_TO_OIL_EQ * 3600E-6
            E_used_CT_W[hour] = wdot_CT

        if reduced_timesteps_flag:
            reduced_costs_USD = np.sum(opex_var_CT_USD)
            reduced_CO2_kgCO2 = np.sum(co2_CT_kgCO2)
            reduced_prim_MJ = np.sum(prim_energy_CT_MJ)

            costs_a_USD += reduced_costs_USD * (8760 / (stop_t - start_t))
            CO2_kgCO2 += reduced_CO2_kgCO2 * (8760 / (stop_t - start_t))
            prim_MJ += reduced_prim_MJ * (8760 / (stop_t - start_t))
        else:
            costs_a_USD += np.sum(opex_var_CT_USD)
            CO2_kgCO2 += np.sum(co2_CT_kgCO2)
            prim_MJ += np.sum(prim_energy_CT_MJ)

    ########## Operation of the CCGT
    if Qh_req_from_CCGT_max_W > 0:
        # Sizing of CCGT
        GT_fuel_type = 'NG'  # assumption for scenarios in SG
        Q_GT_nom_sizing_W = Qh_req_from_CCGT_max_W  # starting guess for the size of GT
        Qh_output_CCGT_max_W = 0  # the heat output of CCGT at currently installed size (Q_GT_nom_sizing_W)
        while (Qh_output_CCGT_max_W - Qh_req_from_CCGT_max_W) <= 0:
            Q_GT_nom_sizing_W += 1000  # update GT size
            # get CCGT performance limits and functions at Q_GT_nom_sizing_W
            CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_sizing_W, ACH_T_IN_FROM_CHP, GT_fuel_type, prices, lca.ELEC_PRICE[hour])
            Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']

        # unpack CCGT performance functions
        Q_GT_nom_W = Q_GT_nom_sizing_W * (1 + SIZING_MARGIN)  # installed CCGT capacity
        CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_W, ACH_T_IN_FROM_CHP, GT_fuel_type, prices, lca.ELEC_PRICE[hour])
        Q_used_prim_W_CCGT_fn = CCGT_performances['q_input_fn_q_output_W']
        cost_per_Wh_th_CCGT_fn = CCGT_performances[
            'fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        Qh_output_CCGT_min_W = CCGT_performances['q_output_min_W']
        Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']
        eta_elec_interpol = CCGT_performances['eta_el_fn_q_input']

        for hour in timesteps:
            if Qh_req_from_CCGT_W[hour] > Qh_output_CCGT_min_W:  # operate above minimal load
                if Qh_req_from_CCGT_W[hour] < Qh_output_CCGT_max_W:  # Normal operation Possible within partload regime
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_req_from_CCGT_W[hour])
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_req_from_CCGT_W[hour])
                    Qh_from_CCGT_W[hour] = Qh_req_from_CCGT_W[hour].copy()
                    E_gen_CCGT_W[hour] = np.float(eta_elec_interpol(Q_used_prim_CCGT_W)) * Q_used_prim_CCGT_W
                else:
                    raise ValueError('Incorrect CCGT sizing!')
            else:  # operate at minimum load
                cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_output_CCGT_min_W)
                Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_output_CCGT_min_W)
                Qh_from_CCGT_W[hour] = Qh_output_CCGT_min_W
                E_gen_CCGT_W[hour] = np.float(eta_elec_interpol(
                    Qh_output_CCGT_max_W)) * Q_used_prim_CCGT_W

            opex_var_CCGT_USD[hour] = cost_per_Wh_th * Qh_from_CCGT_W[hour] - E_gen_CCGT_W[hour] * lca.ELEC_PRICE[hour]
            co2_CCGT_kgCO2[hour] = Q_used_prim_CCGT_W * lca.NG_CC_TO_CO2_STD * WH_TO_J / 1.0E6 - E_gen_CCGT_W[hour] * lca.EL_TO_CO2 * 3600E-6
            prim_energy_CCGT_MJ[hour] = Q_used_prim_CCGT_W * lca.NG_CC_TO_OIL_STD * WH_TO_J / 1.0E6 - E_gen_CCGT_W[hour] * lca.EL_TO_OIL_EQ * 3600E-6
            NG_used_CCGT_W[hour] = Q_used_prim_CCGT_W

        if reduced_timesteps_flag:
            reduced_costs_USD = np.sum(opex_var_CCGT_USD)
            reduced_CO2_kgCO2 = np.sum(co2_CCGT_kgCO2)
            reduced_prim_MJ = np.sum(prim_energy_CCGT_MJ)

            costs_a_USD += reduced_costs_USD * (8760 / (stop_t - start_t))
            CO2_kgCO2 += reduced_CO2_kgCO2 * (8760 / (stop_t - start_t))
            prim_MJ += reduced_prim_MJ * (8760 / (stop_t - start_t))
        else:
            costs_a_USD += np.sum(opex_var_CCGT_USD)
            CO2_kgCO2 += np.sum(co2_CCGT_kgCO2)
            prim_MJ += np.sum(prim_energy_CCGT_MJ)

    ########## Add investment costs

    for i in range(limits['number_of_VCC_chillers']):
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Q_VCC_nom_W, locator, config, 'CH3')
        costs_a_USD += Capex_a_VCC_USD + Opex_fixed_VCC_USD

    for i in range(limits['number_of_VCC_backup_chillers']):
        Capex_a_VCC_backup_USD, Opex_fixed_VCC_backup_USD, Capex_VCC_backup_USD = VCCModel.calc_Cinv_VCC(Q_VCC_backup_nom_W, locator, config, 'CH3')
        costs_a_USD += Capex_a_VCC_backup_USD + Opex_fixed_VCC_backup_USD
    master_to_slave_vars.VCC_backup_cooling_size_W = Q_VCC_backup_nom_W * limits['number_of_VCC_backup_chillers']

    for i in range(limits['number_of_ACH_chillers']):
        Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Q_ACH_nom_W, locator, ACH_TYPE_DOUBLE, config)
        costs_a_USD += Capex_a_ACH_USD + Opex_fixed_ACH_USD

    Capex_a_CCGT_USD, Opex_fixed_CCGT_USD, Capex_CCGT_USD = cogeneration.calc_Cinv_CCGT(Q_GT_nom_W, locator, config)
    costs_a_USD += Capex_a_CCGT_USD + Opex_fixed_CCGT_USD

    Capex_a_Tank_USD, Opex_fixed_Tank_USD, Capex_Tank_USD = thermal_storage.calc_Cinv_storage(V_tank_m3, locator, config, 'TES2')
    costs_a_USD += Capex_a_Tank_USD + Opex_fixed_Tank_USD

    Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Q_CT_nom_W, locator, config, 'CT1')

    costs_a_USD += Capex_a_CT_USD + Opex_fixed_CT_USD

    Capex_a_pump_USD, Opex_fixed_pump_USD, Opex_var_pump_USD, Capex_pump_USD = PumpModel.calc_Ctot_pump(master_to_slave_vars, ntwFeat, locator, lca, config)
    costs_a_USD += Capex_a_pump_USD + Opex_fixed_pump_USD + Opex_var_pump_USD

    network_data = pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling))

    date = network_data.DATE.values
    results = pd.DataFrame({"DATE": date,
                            "Q_total_cooling_W": Q_cooling_req_W,
                            "Opex_var_Lake_USD": opex_var_Lake_USD,
                            "Opex_var_VCC_USD": opex_var_VCC_USD,
                            "Opex_var_ACH_USD": opex_var_ACH_USD,
                            "Opex_var_VCC_backup_USD": opex_var_VCC_backup_USD,
                            "Opex_var_CT_USD": opex_var_CT_USD,
                            "Opex_var_CCGT_USD": opex_var_CCGT_USD,
                            "E_used_Lake_W": E_used_Lake_W,
                            "E_used_VCC_W": E_used_VCC_W,
                            "E_used_VCC_backup_W": E_used_VCC_backup_W,
                            "E_used_ACH_W": E_used_ACH_W,
                            "E_used_CT_W": E_used_CT_W,
                            "NG_used_CCGT_W": NG_used_CCGT_W,
                            "CO2_from_using_Lake": co2_Lake_kgCO2,
                            "CO2_from_using_VCC": co2_VCC_kgCO2,
                            "CO2_from_using_ACH": co2_ACH_kgCO2,
                            "CO2_from_using_VCC_backup": co2_VCC_backup_kgCO2,
                            "CO2_from_using_CT": co2_CT_kgCO2,
                            "CO2_from_using_CCGT": co2_CCGT_kgCO2,
                            "Primary_Energy_from_Lake": prim_energy_Lake_MJ,
                            "Primary_Energy_from_VCC": prim_energy_VCC_MJ,
                            "Primary_Energy_from_ACH": prim_energy_ACH_MJ,
                            "Primary_Energy_from_VCC_backup": prim_energy_VCC_backup_MJ,
                            "Primary_Energy_from_CT": prim_energy_CT_MJ,
                            "Primary_Energy_from_CCGT": prim_energy_CCGT_MJ,
                            "Q_from_Lake_W": Qc_from_Lake_W,
                            "Q_from_VCC_W": Qc_from_VCC_W,
                            "Q_from_ACH_W": Qc_from_ACH_W,
                            "Q_from_VCC_backup_W": Qc_from_VCC_backup_W,
                            "Q_from_storage_tank_W": Qc_from_storage_tank_W,
                            "Qc_CT_associated_with_all_chillers_W": Qc_req_from_CT_W,
                            "Qh_CCGT_associated_with_absorption_chillers_W": Qh_from_CCGT_W,
                            "E_gen_CCGT_associated_with_absorption_chillers_W": E_gen_CCGT_W
                            })

    results.to_csv(locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                                             master_to_slave_vars.generation_number),
                   index=False)
    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calfactor_total / 50976000

    extraElec = (127865400 + 85243600) * calibration
    costs_a_USD += extraElec * lca.ELEC_PRICE.mean()
    CO2_kgCO2 += extraElec * lca.EL_TO_CO2 * 3600E-6
    prim_MJ += extraElec * lca.EL_TO_OIL_EQ * 3600E-6
    # Converting costs into float64 to avoid longer values
    costs_a_USD = np.float64(costs_a_USD)
    CO2_kgCO2 = np.float64(CO2_kgCO2)
    prim_MJ = np.float64(prim_MJ)

    # Capex_a and Opex_fixed
    results = pd.DataFrame({"Capex_a_VCC_USD": [Capex_a_VCC_USD],
                            "Opex_fixed_VCC_USD": [Opex_fixed_VCC_USD],
                            "Capex_a_VCC_backup_USD": [Capex_a_VCC_backup_USD],
                            "Opex_fixed_VCC_backup_USD": [Opex_fixed_VCC_backup_USD],
                            "Capex_a_ACH_USD": [Capex_a_ACH_USD],
                            "Opex_fixed_ACH_USD": [Opex_fixed_ACH_USD],
                            "Capex_a_CCGT_USD": [Capex_a_CCGT_USD],
                            "Opex_fixed_CCGT_USD": [Opex_fixed_CCGT_USD],
                            "Capex_a_Tank_USD": [Capex_a_Tank_USD],
                            "Opex_fixed_Tank_USD": [Opex_fixed_Tank_USD],
                            "Capex_a_CT_USD": [Capex_a_CT_USD],
                            "Opex_fixed_CT_USD": [Opex_fixed_CT_USD],
                            "Capex_a_pump_USD": [Capex_a_pump_USD],
                            "Opex_fixed_pump_USD": [Opex_fixed_pump_USD],
                            "Opex_var_pump_USD": [Opex_var_pump_USD],
                            "Capex_VCC_USD": [Capex_VCC_USD],
                            "Capex_VCC_backup_USD": [Capex_VCC_backup_USD],
                            "Capex_ACH_USD": [Capex_ACH_USD],
                            "Capex_CCGT_USD": [Capex_CCGT_USD],
                            "Capex_Tank_USD": [Capex_Tank_USD],
                            "Capex_CT_USD": [Capex_CT_USD],
                            "Capex_pump_USD": [Capex_pump_USD]
                            })

    results.to_csv(locator.get_optimization_slave_investment_cost_detailed_cooling(master_to_slave_vars.individual_number,
                                                                             master_to_slave_vars.generation_number),
                   index=False)

    # print " Cooling main done (", round(time.time()-t0, 1), " seconds used for this task)"

    # print ('Cooling costs = ' + str(costs))
    # print ('Cooling CO2 = ' + str(CO2))
    # print ('Cooling Eprim = ' + str(prim))

    return (costs_a_USD, CO2_kgCO2, prim_MJ)
