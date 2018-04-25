"""
================
Lake-cooling network connected to chiller and cooling tower
================

Use free cooling from Lake as long as possible (Qmax Lake from gv and HP Lake operation from slave)
If Lake exhausted, use VCC + CT operation

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
from cea.technologies.thermal_network.thermal_network_matrix import calculate_ground_temperature
from cea.constants import WH_TO_J
from cea.optimization.constants import EL_TO_CO2, EL_TO_OIL_EQ, Q_MARGIN_DISCONNECTED, PUMP_ETA, DELTA_U, \
    ACH_T_IN_FROM_CHP, ACH_TYPE_DOUBLE, T_TANK_FULLY_CHARGED_K, T_TANK_FULLY_DISCHARGED_K, PEAK_LOAD_RATIO, \
    NG_CC_TO_CO2_STD, NG_CC_TO_OIL_STD

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def coolingMain(locator, master_to_slave_vars, ntwFeat, gv, prices, config):
    """
    Computes the parameters for the cooling of the complete DCN

    :param locator: path to res folder
    :param ntwFeat: network features
    :param gv: global variables
    :param prices: Prices imported from the database
    :type locator: string
    :type ntwFeat: class
    :type gv: class
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
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
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
    try:
        dfSlave = pd.read_csv(
            locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                      master_to_slave_vars.generation_number),
            usecols=["Q_coldsource_HPLake_W"])
        Q_Lake_Array_W = np.array(dfSlave)

    except:
        Q_Lake_Array_W = [0]

    ### input parameters
    Qc_VCC_max_W = master_to_slave_vars.VCC_cooling_size
    Qc_ACH_max_W = master_to_slave_vars.Absorption_chiller_size
    Qc_peak_load_W = Q_cooling_req_W.max() * PEAK_LOAD_RATIO  # threshold to discharge storage

    T_ground_K = calculate_ground_temperature(locator)

    # sizing cold water storage tank
    if master_to_slave_vars.Storage_cooling_size > 0:
        Qc_tank_discharge_peak_W = master_to_slave_vars.Storage_cooling_size
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


    limits = {'Qc_VCC_max_W': Qc_VCC_max_W, 'Qc_ACH_max_W': Qc_ACH_max_W, 'Qc_peak_load_W': Qc_peak_load_W,
              'Qc_tank_discharge_peak_W': Qc_tank_discharge_peak_W, 'Qc_tank_charge_max_W': Qc_tank_charge_max_W,
              'V_tank_m3': V_tank_m3, 'T_tank_fully_charged_K': T_TANK_FULLY_CHARGED_K,
              'area_HEX_tank_discharge_m2': area_HEX_tank_discharege_m2,
              'UA_HEX_tank_discharge_WperK': UA_HEX_tank_discharge_WperK,
              'area_HEX_tank_charge_m2': area_HEX_tank_charge_m2,
              'UA_HEX_tank_charge_WperK': UA_HEX_tank_charge_WperK}

    ### input variables
    Qc_available_from_lake_W = DELTA_U + np.sum(Q_Lake_Array_W)
    Qc_from_lake_cumulative_W = 0
    cooling_resource_potentials = {'T_tank_K': T_TANK_FULLY_DISCHARGED_K,
                                   'Qc_avail_from_lake_W': Qc_available_from_lake_W,
                                   'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}

    ############# Output results
    costs = ntwFeat.pipesCosts_DCN
    CO2 = 0
    prim = 0

    nBuild = int(np.shape(arrayData)[0])
    nHour = int(np.shape(DCN_operation_parameters)[0])

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

    opex_var_Lake = np.zeros(8760)
    opex_var_VCC = np.zeros(8760)
    opex_var_ACH = np.zeros(8760)
    opex_var_VCC_backup = np.zeros(8760)
    opex_var_CCGT = np.zeros(8760)
    opex_var_CT = np.zeros(8760)
    co2_Lake = np.zeros(8760)
    co2_VCC = np.zeros(8760)
    co2_ACH = np.zeros(8760)
    co2_VCC_backup = np.zeros(8760)
    co2_CCGT = np.zeros(8760)
    co2_CT = np.zeros(8760)
    prim_energy_Lake = np.zeros(8760)
    prim_energy_VCC = np.zeros(8760)
    prim_energy_ACH = np.zeros(8760)
    prim_energy_VCC_backup = np.zeros(8760)
    prim_energy_CCGT = np.zeros(8760)
    prim_energy_CT = np.zeros(8760)
    calfactor_total = 0

    for hour in range(nHour):  # cooling supply for all buildings excluding cooling loads from data centers
        performance_indicators_output, \
        Qc_supply_to_DCN, calfactor_output, \
        Qc_CT_W, Qh_CHP_ACH_W, \
        cooling_resource_potentials = cooling_resource_activator(mdot_kgpers[hour], T_sup_K[hour], T_re_K[hour],
                                                                 limits, cooling_resource_potentials,
                                                                 T_ground_K[hour], prices, master_to_slave_vars, config, Q_cooling_req_W[hour])

        # save results for each time-step
        opex_var_Lake[hour] = performance_indicators_output['Opex_var_Lake']
        opex_var_VCC[hour] = performance_indicators_output['Opex_var_VCC']
        opex_var_ACH[hour] = performance_indicators_output['Opex_var_ACH']
        opex_var_VCC_backup[hour] = performance_indicators_output['Opex_var_VCC_backup']
        co2_Lake[hour] = performance_indicators_output['CO2_Lake']
        co2_VCC[hour] = performance_indicators_output['CO2_VCC']
        co2_ACH[hour] = performance_indicators_output['CO2_ACH']
        co2_VCC_backup[hour] = performance_indicators_output['CO2_VCC_backup']
        prim_energy_Lake[hour] = performance_indicators_output['Primary_Energy_Lake']
        prim_energy_VCC[hour] = performance_indicators_output['Primary_Energy_VCC']
        prim_energy_ACH[hour] = performance_indicators_output['Primary_Energy_ACH']
        prim_energy_VCC_backup[hour] = performance_indicators_output['Primary_Energy_VCC_backup']
        calfactor_buildings[hour] = calfactor_output
        Qc_from_Lake_W[hour] = Qc_supply_to_DCN['Qc_from_Lake_W']
        Qc_from_storage_tank_W[hour] = Qc_supply_to_DCN['Qc_from_Tank_W']
        Qc_from_VCC_W[hour] = Qc_supply_to_DCN['Qc_from_VCC_W']
        Qc_from_ACH_W[hour] = Qc_supply_to_DCN['Qc_from_ACH_W']
        Qc_from_VCC_backup_W[hour] = Qc_supply_to_DCN['Qc_from_backup_VCC_W']
        Qc_req_from_CT_W[hour] = Qc_CT_W
        Qh_req_from_CCGT_W[hour] = Qh_CHP_ACH_W

    costs += np.sum(opex_var_Lake) + np.sum(opex_var_VCC) + np.sum(opex_var_ACH) + np.sum(opex_var_VCC_backup)
    CO2 += np.sum(co2_Lake) + np.sum(co2_Lake) + np.sum(co2_ACH) + np.sum(co2_VCC_backup)
    prim += np.sum(prim_energy_Lake) + np.sum(prim_energy_VCC) + np.sum(prim_energy_ACH) + np.sum(
        prim_energy_VCC_backup)
    calfactor_total += np.sum(calfactor_buildings)
    TotalCool += np.sum(Qc_from_Lake_W) + np.sum(Qc_from_VCC_W) + np.sum(Qc_from_ACH_W) + np.sum(Qc_from_VCC_backup_W) + np.sum(Qc_from_storage_tank_W)
    Q_VCC_nom_W = np.amax(Qc_from_VCC_W) * (1 + Q_MARGIN_DISCONNECTED)
    Q_ACH_nom_W = np.amax(Qc_from_ACH_W) * (1 + Q_MARGIN_DISCONNECTED)
    Q_VCC_backup_nom_W = np.amax(Qc_from_VCC_backup_W) * (1 + Q_MARGIN_DISCONNECTED)
    Q_CT_nom_W = np.amax(Qc_req_from_CT_W)
    Qh_req_from_CCGT_max_W = np.amax(Qh_req_from_CCGT_W) # the required heat output from CCGT at peak
    mdot_Max_kgpers = np.amax(DCN_operation_parameters_array[:, 1])  # sizing of DCN network pumps
    Q_GT_nom_W = 0
    ########## Operation of the cooling tower

    if Q_CT_nom_W > 0:
        for hour in range(nHour):
            wdot_CT = CTModel.calc_CT(Qc_req_from_CT_W[hour], Q_CT_nom_W)
            opex_var_CT[hour] = (wdot_CT) * prices.ELEC_PRICE
            co2_CT[hour] = (wdot_CT) * EL_TO_CO2 * 3600E-6
            prim_energy_CT[hour] = (wdot_CT) * EL_TO_OIL_EQ * 3600E-6

        costs += np.sum(opex_var_CT)
        CO2 += np.sum(co2_CT)
        prim += np.sum(prim_energy_CT)

    ########## Operation of the CCGT
    if Qh_req_from_CCGT_max_W > 0:
        # Sizing of CCGT
        GT_fuel_type = 'NG'  # assumption for scenarios in SG
        Q_GT_nom_sizing_W = Qh_req_from_CCGT_max_W  # starting guess for the size of GT
        Qh_output_CCGT_max_W = 0  # the heat output of CCGT at currently installed size (Q_GT_nom_sizing_W)
        while (Qh_output_CCGT_max_W - Qh_req_from_CCGT_max_W) <= 0:
            Q_GT_nom_sizing_W += 10  # update GT size
            # get CCGT performance limits and functions at Q_GT_nom_sizing_W
            CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_sizing_W, ACH_T_IN_FROM_CHP, GT_fuel_type, prices)
            Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']

        # unpack CCGT performance functions
        Q_GT_nom_W = Q_GT_nom_sizing_W * (1 + Q_MARGIN_DISCONNECTED)  # installed CCGT capacity
        CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_W, ACH_T_IN_FROM_CHP, GT_fuel_type, prices)
        Q_used_prim_W_CCGT_fn = CCGT_performances['q_input_fn_q_output_W']
        cost_per_Wh_th_CCGT_fn = CCGT_performances[
            'fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        Qh_output_CCGT_min_W = CCGT_performances['q_output_min_W']
        Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']
        eta_elec_interpol = CCGT_performances['eta_el_fn_q_input']

        for i in range(nHour):
            if Qh_req_from_CCGT_W[i] > Qh_output_CCGT_min_W:  # operate above minimal load
                if Qh_req_from_CCGT_W[i] < Qh_output_CCGT_max_W:  # Normal operation Possible within partload regime
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_req_from_CCGT_W[i])
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_req_from_CCGT_W[i])
                    Qh_from_CCGT_W[hour] = Qh_req_from_CCGT_W[i].copy()
                    E_gen_CCGT_W[hour] = np.float(eta_elec_interpol(Q_used_prim_CCGT_W)) * Q_used_prim_CCGT_W
                else:
                    raise ValueError('Incorrect CCGT sizing!')
            else:  # operate at minimum load
                cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_output_CCGT_min_W)
                Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_output_CCGT_min_W)
                Qh_from_CCGT_W[hour] = Qh_output_CCGT_min_W
                E_gen_CCGT_W[hour] = np.float(eta_elec_interpol(
                    Qh_output_CCGT_max_W)) * Q_used_prim_CCGT_W

            opex_var_CCGT[hour] = cost_per_Wh_th * Qh_from_CCGT_W[hour] - E_gen_CCGT_W[hour] * prices.ELEC_PRICE
            co2_CCGT[hour] = Q_used_prim_CCGT_W * NG_CC_TO_CO2_STD * WH_TO_J / 1.0E6 - E_gen_CCGT_W[hour] * EL_TO_CO2 * 3600E-6
            prim_energy_CCGT[hour] = Q_used_prim_CCGT_W * NG_CC_TO_OIL_STD * WH_TO_J / 1.0E6 - E_gen_CCGT_W[hour] * EL_TO_OIL_EQ * 3600E-6

        costs += np.sum(opex_var_CCGT)
        CO2 += np.sum(co2_CCGT)
        prim += np.sum(prim_energy_CCGT)

    ########## Add investment costs
    Capex_a_VCC, Opex_fixed_VCC = VCCModel.calc_Cinv_VCC(Q_VCC_nom_W, locator, config, 'CH3')
    costs += Capex_a_VCC + Opex_fixed_VCC

    Capex_a_VCC_backup, Opex_fixed_VCC_backup = VCCModel.calc_Cinv_VCC(Q_VCC_backup_nom_W, locator, config, 'CH3')
    costs += Capex_a_VCC_backup + Opex_fixed_VCC_backup

    Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Q_ACH_nom_W, locator, ACH_TYPE_DOUBLE, config)
    costs += Capex_a_ACH + Opex_ACH

    Capex_a_CCGT, Opex_fixed_CCGT = cogeneration.calc_Cinv_CCGT(Q_GT_nom_W, locator, config)
    costs += Capex_a_CCGT + Opex_fixed_CCGT

    Capex_a_Tank, Opex_fixed_Tank = thermal_storage.calc_Cinv_storage(V_tank_m3, locator, config, 'TES2')
    costs += Capex_a_Tank + Opex_fixed_Tank

    Capex_a_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(Q_CT_nom_W, locator, config, 'CT1')

    costs += Capex_a_CT + Opex_fixed_CT

    Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * max(ntwFeat.DeltaP_DCN), mdot_Max_kgpers, PUMP_ETA, gv,
                                                           locator, 'PU1')
    costs += Capex_pump + Opex_fixed_pump

    dfSlave1 = pd.read_csv(
        locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number))
    date = dfSlave1.DATE.values
    results = pd.DataFrame({"DATE": date,
                            "Q_total_cooling_W": Q_cooling_req_W,
                            "Opex_var_Lake": opex_var_Lake,
                            "Opex_var_VCC": opex_var_VCC,
                            "Opex_var_ACH": opex_var_ACH,
                            "Opex_var_VCC_backup": opex_var_VCC_backup,
                            "Opex_var_CT": opex_var_CT,
                            "Opex_var_CCGT": opex_var_CCGT,
                            "CO2_from_using_Lake": co2_Lake,
                            "CO2_from_using_VCC": co2_VCC,
                            "CO2_from_using_ACH": co2_ACH,
                            "CO2_from_using_VCC_backup": co2_VCC_backup,
                            "CO2_from_using_CT": co2_CT,
                            "CO2_from_using_CCGT": co2_CCGT,
                            "Primary_Energy_from_Lake": prim_energy_Lake,
                            "Primary_Energy_from_VCC": prim_energy_VCC,
                            "Primary_Energy_from_ACH": prim_energy_ACH,
                            "Primary_Energy_from_VCC_backup": prim_energy_VCC_backup,
                            "Primary_Energy_from_CT": prim_energy_CT,
                            "Primary_Energy_from_CCGT": prim_energy_CCGT,
                            "Q_from_Lake_W": Qc_from_Lake_W,
                            "Q_from_VCC_W": Qc_from_VCC_W,
                            "Q_from_ACH_W": Qc_from_ACH_W,
                            "Q_from_VCC_backup_W": Qc_from_VCC_backup_W,
                            "Q_from_storage_tank_W": Qc_from_storage_tank_W,
                            "Qc_CT_associated_with_all_chillers_W": Qc_req_from_CT_W,
                            "Qh_CCGT_associated_with_absorption_chillers": Qh_from_CCGT_W,
                            "E_gen_CCGT_associated_with_absorption_chillers": E_gen_CCGT_W
                            })

    results.to_csv(locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                                             master_to_slave_vars.generation_number),
                   index=False)
    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calfactor_total / 50976000

    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * prices.ELEC_PRICE
    CO2 += extraElec * EL_TO_CO2 * 3600E-6
    prim += extraElec * EL_TO_OIL_EQ * 3600E-6
    # Converting costs into float64 to avoid longer values
    costs = np.float64(costs)
    CO2 = np.float64(CO2)
    prim = np.float64(prim)

    # Capex_a and Opex_fixed
    results = pd.DataFrame({"Capex_a_VCC": [Capex_a_VCC],
                            "Opex_fixed_VCC": [Opex_fixed_VCC],
                            "Capex_a_VCC_backup": [Capex_a_VCC_backup],
                            "Opex_fixed_VCC_backup": [Opex_fixed_VCC_backup],
                            "Capex_a_ACH": [Capex_a_ACH],
                            "Opex_ACH": [Opex_ACH],
                            "Capex_a_CCGT": [Capex_a_CCGT],
                            "Opex_fixed_CCGT": [Opex_fixed_CCGT],
                            "Capex_a_Tank": [Capex_a_Tank],
                            "Opex_fixed_Tank": [Opex_fixed_Tank],
                            "Capex_a_CT": [Capex_a_CT],
                            "Opex_fixed_CT": [Opex_fixed_CT],
                            "Capex_pump": [Capex_pump],
                            "Opex_fixed_pump": [Opex_fixed_pump]
                            })

    results.to_csv(locator.get_optimization_slave_investment_cost_detailed_cooling(master_to_slave_vars.individual_number,
                                                                             master_to_slave_vars.generation_number),
                   index=False)

    print " Cooling main done (", round(time.time()-t0, 1), " seconds used for this task)"

    print ('Cooling costs = ' + str(costs))
    print ('Cooling CO2 = ' + str(CO2))
    print ('Cooling Eprim = ' + str(prim))

    return (costs, CO2, prim)
