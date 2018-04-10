"""
================
Lake-cooling network connected to chiller and cooling tower
================

Use free cooling from Lake as long as possible (Qmax Lake from gv and HP Lake operation from slave)
If Lake exhausted, use VCC + CT operation

"""
from __future__ import division
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
from cea.optimization.constants import EL_TO_CO2, EL_TO_OIL_EQ, Q_MARGIN_DISCONNECTED, PUMP_ETA, DELTA_U, \
    ACH_T_IN_FROM_CHP, ACH_TYPE_DOUBLE, T_TANK_FULLY_CHARGED_K, T_TANK_FULLY_DISCHARGED_K

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

    # Space cooling previously aggregated in the substation routine
    df = pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                     usecols=["T_DCNf_sup_K", "T_DCNf_re_K", "mdot_DC_netw_total_kgpers"])
    DCN_operation_parameters = np.nan_to_num(np.array(df))

    Qc_DCN_W = np.array(
        pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                    usecols=["Q_DCNf_W",
                             "Qcdata_netw_total_kWh"]))  # importing the cooling demands of DCN (space cooling + refrigeration)
    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
    arrayData = np.array(df)

    # total cooling requirements based on the Heat Recovery Flag
    Q_cooling_req_W = np.zeros(8760)
    if master_to_slave_vars.WasteServersHeatRecovery == 0:
        for hour in range(8760):  # summing cooling loads of space cooling, refrigeration and data center
            Q_cooling_req_W[hour] = Qc_DCN_W[hour][0] + Qc_DCN_W[hour][1]
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

    Qc_available_from_lake_W = DELTA_U + np.sum(Q_Lake_Array_W)

    ### input parameters
    Qc_VCC_max_W = master_to_slave_vars.VCC_cooling_size * Q_cooling_req_W.max()
    Qc_ACH_max_W = master_to_slave_vars.Absorption_chiller_size * Q_cooling_req_W.max()
    Qc_peak_load_W = (Qc_VCC_max_W + Qc_ACH_max_W) * 0.9  # TODO: assumption, threshold to discharge storage
    Qc_from_lake_cumulative_W = 0
    T_ground_K = calculate_ground_temperature(locator)

    ### Sizing cold water storage tank
    Qc_tank_discharge_peak_W = master_to_slave_vars.Storage_cooling_size * Q_cooling_req_W.max()
    Qc_tank_charege_max_W = Qc_VCC_max_W * 0.8  # TODO: assumption of the capacity of VCC when T_sup = 4 C
    peak_hour = np.argmax(Q_cooling_req_W)
    area_HEX_tank_discharege_m2, UA_HEX_tank_discharge_WperK, \
    area_HEX_tank_charge_m2, UA_HEX_tank_charge_WperK, \
    V_tank_m3 = storage_tank.calc_storage_tank_properties(DCN_operation_parameters, Qc_tank_charege_max_W,
                                                          Qc_tank_discharge_peak_W, peak_hour)

    # input variables for hourly cooling activation
    limits = {'Qc_VCC_max_W': Qc_VCC_max_W, 'Qc_ACH_max_W': Qc_ACH_max_W, 'Qc_peak_load_W': Qc_peak_load_W,
              'Qc_tank_discharge_peak_W': Qc_tank_discharge_peak_W, 'Qc_tank_charege_max_W': Qc_tank_charege_max_W,
              'V_tank_m3': V_tank_m3, 'T_tank_fully_charged_K': T_TANK_FULLY_CHARGED_K,
              'area_HEX_tank_discharge_m2': area_HEX_tank_discharege_m2,
              'UA_HEX_tank_discharge_WperK': UA_HEX_tank_discharge_WperK,
              'area_HEX_tank_charge_m2': area_HEX_tank_charge_m2,
              'UA_HEX_tank_charge_WperK': UA_HEX_tank_charge_WperK}

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
    Q_cooling_buildings_from_Lake_W = np.zeros(8760)
    Q_cooling_buildings_from_VCC_W = np.zeros(8760)
    Q_cooling_buildings_from_ACH_W = np.zeros(8760)
    CT_load_buildings_from_chillers_W = np.zeros(8760)

    opex_var_buildings_Lake = np.zeros(8760)
    opex_var_buildings_VCC = np.zeros(8760)
    opex_var_buildings_ACH = np.zeros(8760)
    co2_list_buildings_Lake = np.zeros(8760)
    co2_list_buildings_VCC = np.zeros(8760)
    co2_list_buildings_ACH = np.zeros(8760)
    prim_list_buildings_Lake = np.zeros(8760)
    prim_list_buildings_VCC = np.zeros(8760)
    prim_list_buildings_ACH = np.zeros(8760)
    calfactor_total = 0

    opex_var_data_center_Lake = np.zeros(8760)
    opex_var_data_center_VCC = np.zeros(8760)
    opex_var_data_center_ACH = np.zeros(8760)
    co2_list_data_center_Lake = np.zeros(8760)
    co2_list_data_center_VCC = np.zeros(8760)
    co2_list_data_center_ACH = np.zeros(8760)
    prim_list_data_center_Lake = np.zeros(8760)
    prim_list_data_center_VCC = np.zeros(8760)
    prim_list_data_center_ACH = np.zeros(8760)
    calfactor_data_center = np.zeros(8760)
    Q_cooling_data_center_from_Lake_W = np.zeros(8760)
    Q_cooling_data_center_from_VCC_W = np.zeros(8760)
    Q_cooling_data_center_from_ACH_W = np.zeros(8760)
    Q_cooling_buildings_from_backup_VCC_W = np.zeros(8760)

    for hour in range(nHour):  # cooling supply for all buildings excluding cooling loads from data centers
        opex, co2, primary_energy, \
        Qc_supply_to_DCN, calfactor_output, \
        Qc_CT_W, Qh_CHP_ACH_W, \
        cooling_resource_potentials = cooling_resource_activator(DCN_operation_parameters[hour],
                                                                 limits, cooling_resource_potentials,
                                                                 T_ground_K[hour], prices, master_to_slave_vars, config)

        Qc_from_lake_cumulative_W = Qc_from_lake_cumulative_W + Qc_supply_to_DCN[
            'Qc_from_Lake_W']  # update lake cooling potential
        # save results for each time-step
        opex_var_buildings_Lake[hour] = opex['Opex_var_Lake']
        opex_var_buildings_VCC[hour] = opex['Opex_var_VCC']
        opex_var_buildings_ACH[hour] = opex['Opex_var_ACH']
        co2_list_buildings_Lake[hour] = co2['CO2_Lake']
        co2_list_buildings_VCC[hour] = co2['CO2_VCC']
        co2_list_buildings_ACH[hour] = co2['CO2_ACH']
        prim_list_buildings_Lake[hour] = primary_energy['Primary_Energy_Lake']
        prim_list_buildings_VCC[hour] = primary_energy['Primary_Energy_VCC']
        prim_list_buildings_ACH[hour] = primary_energy['Primary_Energy_ACH']
        calfactor_buildings[hour] = calfactor_output
        Q_cooling_buildings_from_Lake_W[hour] = Qc_supply_to_DCN['Qc_from_Lake_W']
        Q_cooling_buildings_from_VCC_W[hour] = Qc_supply_to_DCN['Qc_from_VCC_W']
        Q_cooling_buildings_from_ACH_W[hour] = Qc_supply_to_DCN['Qc_from_ACH_W']
        Q_cooling_buildings_from_backup_VCC_W[hour] = Qc_supply_to_DCN['Qc_from_backup_VCC_W']
        CT_load_buildings_from_chillers_W[hour] = Qc_CT_W

    costs += np.sum(opex_var_buildings_Lake) + np.sum(opex_var_buildings_VCC)
    CO2 += np.sum(co2_list_buildings_Lake) + np.sum(co2_list_buildings_Lake)
    prim += np.sum(prim_list_buildings_Lake) + np.sum(prim_list_buildings_VCC)
    calfactor_total += np.sum(calfactor_buildings)
    TotalCool += np.sum(Q_cooling_buildings_from_Lake_W) + np.sum(Q_cooling_buildings_from_VCC_W)
    Q_VCC_nom_W = np.amax(Q_cooling_buildings_from_VCC_W) * (1 + Q_MARGIN_DISCONNECTED)
    Q_ACH_nom_W = np.amax(Q_cooling_buildings_from_ACH_W) * (1 + Q_MARGIN_DISCONNECTED)
    Q_VCC_backup_nom_W = np.amax(Q_cooling_buildings_from_backup_VCC_W) * (1 + Q_MARGIN_DISCONNECTED)
    Q_CT_nom_W = np.amax(CT_load_buildings_from_chillers_W)
    mdot_Max_kgpers = np.amax(DCN_operation_parameters[:, 1]) # sizing of DCN network pumps



    ########## Operation of the cooling tower

    if Q_CT_nom_W > 0:
        for i in range(nHour):
            wdot_CT = CTModel.calc_CT(CT_load_buildings_from_chillers_W[i], Q_CT_nom_W)
            costs += (wdot_CT) * prices.ELEC_PRICE
            CO2 += (wdot_CT) * EL_TO_CO2 * 3600E-6
            prim += (wdot_CT) * EL_TO_OIL_EQ * 3600E-6

    ########## Operation of the CCGT
    if max(Qh_CHP_ACH_W) > 0:
        # Sizing of CCGT
        GT_fuel_type = 'NG'  # assumption for scenarios in SG
        Q_GT_nom_W = max(Qh_CHP_ACH_W)  # size of GT # FIXME: assumption
        Qh_output_CCGT_W = 0
        Qh_output_CCGT_max_W = 0
        while (Qh_output_CCGT_max_W - Qh_output_CCGT_W) <= 0:
            Q_GT_nom_W += 10  # FIXME: assumption
            # get CCGT performance limits and functions
            CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_W, ACH_T_IN_FROM_CHP, GT_fuel_type, prices)
            Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']

        # unpack CCGT performances
        Q_used_prim_W_CCGT_fn = CCGT_performances['q_input_fn_q_output_W']
        cost_per_Wh_th_CCGT_fn = CCGT_performances[
            'fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        Qh_output_CCGT_min_W = CCGT_performances['q_output_min_W']
        Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']
        eta_elec_interpol = CCGT_performances['eta_el_fn_q_input']

        for i in range(nHour):
            if Qh_CHP_ACH_W > Qh_output_CCGT_min_W:  # operation Possible if above minimal load
                if Qh_CHP_ACH_W < Qh_output_CCGT_max_W:  # Normal operation Possible within partload regime
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_CHP_ACH_W)
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_CHP_ACH_W)
                    Qh_from_CCGT_W = Qh_CHP_ACH_W.copy()
                    Qh_CHP_ACH_W = 0
                    E_CHP_gen_W = np.float(eta_elec_interpol(Q_used_prim_CCGT_W)) * Q_used_prim_CCGT_W

                else:  # Only part of the demand can be delivered as 100% load achieved
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_output_CCGT_max_W)
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_output_CCGT_max_W)
                    Qh_from_CCGT_W = Qh_output_CCGT_max_W
                    Qh_CHP_ACH_W -= Qh_output_CCGT_max_W  # FIXME: activate more than one CHP again?
                    E_CHP_gen_W = np.float(eta_elec_interpol(Qh_output_CCGT_max_W)) * Q_used_prim_CCGT_W

            opex_CCGT = cost_per_Wh_th * Qh_from_CCGT_W
            # FIXME: not sure how the following part are connected to the rest here...
            source_CHP = 1
            cost_CHP = opex_CCGT
            Q_CHP_gen_W = Qh_from_CCGT_W
            E_gas_CHP_W = Q_used_prim_CCGT_W

    ########## Add investment costs
    Capex_a_VCC, Opex_fixed_VCC = VCCModel.calc_Cinv_VCC(Q_VCC_nom_W, gv, locator)
    costs += (Capex_a_VCC + Opex_fixed_VCC)

    Capex_a_VCC_backup, Opex_fixed_VCC_backup = VCCModel.calc_Cinv_VCC(Q_VCC_backup_nom_W, gv, locator)
    costs += (Capex_a_VCC_backup + Opex_fixed_VCC_backup)

    Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Q_ACH_nom_W, locator, ACH_TYPE_DOUBLE, config)
    costs += (Capex_a_ACH + Opex_ACH)

    Capex_a_CCGT, Opex_fixed_CCGT = cogeneration.calc_Cinv_CCGT(Q_GT_nom_W, locator, config)
    costs += (Capex_a_CCGT, Opex_fixed_CCGT)

    Capex_a_Tank, Opex_fixed_Tank = thermal_storage.calc_Cinv_storage(V_tank_m3, locator, config,
                                                                      technology=1)  # FIXME: make sure it is pointing to TES2
    costs += (Capex_a_Tank, Opex_fixed_Tank)

    Capex_a_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(Q_CT_nom_W, gv, locator)
    costs += (Capex_a_CT + Opex_fixed_CT)

    Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_Max_kgpers, PUMP_ETA, gv,
                                                           locator)
    costs += (Capex_pump + Opex_fixed_pump)


    dfSlave1 = pd.read_csv(
        locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number))
    date = dfSlave1.DATE.values

    Opex_var_Lake = np.add(opex_var_buildings_Lake, opex_var_data_center_Lake)
    Opex_var_VCC = np.add(opex_var_buildings_VCC, opex_var_data_center_VCC)
    Opex_var_ACH = np.add(opex_var_buildings_ACH, opex_var_data_center_ACH)
    CO2_from_using_Lake = np.add(co2_list_buildings_Lake, co2_list_data_center_Lake)
    CO2_from_using_VCC = np.add(co2_list_buildings_VCC, co2_list_data_center_VCC)
    CO2_from_using_ACH = np.add(co2_list_buildings_ACH, co2_list_data_center_ACH)
    Primary_Energy_from_Lake = np.add(prim_list_buildings_Lake, prim_list_data_center_Lake)
    Primary_Energy_from_VCC = np.add(prim_list_buildings_VCC, prim_list_data_center_VCC)
    Primary_Energy_from_ACH = np.add(prim_list_buildings_ACH, prim_list_data_center_ACH)
    Q_from_Lake_W = np.add(Q_cooling_buildings_from_Lake_W, Q_cooling_data_center_from_Lake_W)
    Q_from_VCC_W = np.add(Q_cooling_buildings_from_VCC_W, Q_cooling_data_center_from_VCC_W)
    Q_from_ACH_W = np.add(Q_cooling_buildings_from_ACH_W, Q_cooling_data_center_from_ACH_W)
    CT_Load_associated_with_VCC_W = np.add(CT_load_buildings_from_chillers_W, CT_load_data_center_from_VCC_W)

    results = pd.DataFrame({"DATE": date,
                            "Q_total_cooling_W": Q_cooling_req_W,
                            "Opex_var_Lake": Opex_var_Lake[0],
                            "Opex_var_VCC": Opex_var_VCC[0],
                            "Opex_var_ACH": Opex_var_ACH,
                            "CO2_from_using_Lake": CO2_from_using_Lake[0],
                            "CO2_from_using_VCC": CO2_from_using_VCC[0],
                            "CO2_from_using_ACH": CO2_from_using_ACH[0],
                            "Primary_Energy_from_Lake": Primary_Energy_from_Lake[0],
                            "Primary_Energy_from_VCC": Primary_Energy_from_VCC[0],
                            "Primary_Energy_from_ACH": Primary_Energy_from_ACH[0],
                            "Q_from_Lake_W": Q_from_Lake_W[0],
                            "Q_from_VCC_W": Q_from_VCC_W[0],
                            "Q_from_ACH_W": Q_from_ACH_W[0],
                            "CT_Load_associated_with_VCC_W": CT_Load_associated_with_VCC_W
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

    return (costs, CO2, prim)
