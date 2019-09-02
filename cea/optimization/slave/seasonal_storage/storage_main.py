# -*- coding: utf-8 -*-
"""

storage sizing

This script sizes the storage and in a second part, it will plot the results of iteration.
Finally, the storage operation is performed with the parameters found in the storage optimization
All results are saved in the folder of "locator.get_optimization_slave_results_folder()".
- Data_with_Storage_applied.csv : Hourly Operation of Storage, especially Q_missing and E_aux is important for further usage
- Storage_Sizing_Parameters.csv : Saves the parameters found in the storage optimization
IMPORTANT : Storage is used for solar thermal energy ONLY!
It is possible to turn off the plots by setting Tempplot = 0 and Qplot = 0
"""
from __future__ import division

import os

import numpy as np
import pandas as pd

import cea.optimization.slave.seasonal_storage.design_operation as StDesOp
import cea.technologies.heatpumps as hp
import cea.technologies.thermal_storage as storage
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3, WH_TO_J
from cea.constants import HOURS_IN_YEAR

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def storage_optimization(locator, master_to_slave_vars, lca, prices, config):
    """
    This function performs the storage optimization and stores the results in the designated folders
    :param locator: locator class
    :param master_to_slave_vars: class MastertoSlaveVars containing the value of variables to be passed to the slave
    optimization for each individual
    :type locator: class
    :type master_to_slave_vars: class
    :return: The function saves all files when it's done in the location locator.get_potentials_solar_folder()
    :rtype: Nonetype
    """
    print "Storage Optimization Ready"

    CSV_NAME = master_to_slave_vars.network_data_file_heating

    # Initiating

    T_storage_old_K = master_to_slave_vars.T_storage_zero
    Q_in_storage_old = master_to_slave_vars.Q_in_storage_zero

    # start with initial size:
    T_ST_MAX = master_to_slave_vars.T_ST_MAX
    T_ST_MIN = master_to_slave_vars.T_ST_MIN

    # read solar technologies data
    solar_technologies_data = read_solar_technologies_data(locator, master_to_slave_vars)

    ## initial storage size
    V_storage_initial_m3 = master_to_slave_vars.STORAGE_SIZE
    V0 = V_storage_initial_m3
    Optimized_Data0, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_storage_old_K, Q_in_storage_old, locator,
                                                               V_storage_initial_m3, solar_technologies_data,
                                                               master_to_slave_vars, 1e12,
                                                               config)

    Q_stored_max0_W, Q_rejected_final_W, Q_disc_seasonstart_W, T_st_max_K, T_st_min_K, \
    Q_storage_content_final_W, T_storage_final_K, Q_loss0_W, mdot_DH_fin0_kgpers, \
    Q_uncontrollable_final_W = Optimized_Data0

    # FIXME: constant 1e12 is used as maximum discharging rate, to confirm
    # Design HP for storage uptake - limit the maximum thermal power, Criterial: 2000h operation average of a year
    # --> Oral Recommandation of Antonio (former Leibundgut Group)
    P_HP_max = np.sum(Q_uncontrollable_final_W) / 2000.0  # W? TODO: CONFIRM

    ## Start optimizing the storage size

    # first Round optimization
    Q_required_in_storage_W = Q_loss0_W + Q_stored_max0_W
    V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_required_in_storage_W, T_ST_MAX, T_ST_MIN)
    V1 = V_storage_possible_needed
    Q_initial_W = min(Q_stored_max0_W / 2.0, Q_storage_content_final_W[-1])
    T_initial_K = calc_T_initial_from_Q_and_V(Q_initial_W, T_ST_MIN, V_storage_initial_m3)

    # assume unlimited uptake to storage during first round optimisation (P_HP_max = 1e12)
    Optimized_Data, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K, Q_initial_W, locator,
                                                              V_storage_possible_needed, solar_technologies_data,
                                                              master_to_slave_vars, P_HP_max,
                                                              config)
    Q_stored_max_opt_W, Q_rejected_fin_opt_W, Q_disc_seasonstart_opt_W, T_st_max_op_K, T_st_min_op_K, \
    Q_storage_content_fin_op_W, T_storage_fin_op_K, Q_loss1_W, mdot_DH_fin1_kgpers, Q_uncontrollable_final_W = Optimized_Data

    # Design HP for storage uptake - limit the maximum thermal power, Criterial: 2000h operation average of a year
    # --> Oral Recommandation of Antonio (former Leibundgut Group)
    P_HP_max = np.sum(Q_uncontrollable_final_W) / 2000.0

    # Calculate if the initial and final storage levels are converged
    storageDeviation1 = calc_temperature_convergence(Q_storage_content_fin_op_W)

    if storageDeviation1 > 0.0001:

        Q_stored_max_needed_W = np.amax(Q_storage_content_fin_op_W) - np.amin(Q_storage_content_fin_op_W)
        V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_stored_max_needed_W, T_ST_MAX, T_ST_MIN)
        V2 = V_storage_possible_needed
        Q_initial_W = min(Q_disc_seasonstart_opt_W[0], Q_storage_content_fin_op_W[-1])
        T_initial_K = calc_T_initial_from_Q_and_V(Q_initial_W, T_ST_MIN, V_storage_possible_needed)
        Optimized_Data2, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K, Q_initial_W, locator,
                                                                   V_storage_possible_needed, solar_technologies_data,
                                                                   master_to_slave_vars, P_HP_max,
                                                                   config)
        Q_stored_max_opt2_W, Q_rejected_fin_opt2_W, Q_disc_seasonstart_opt2_W, T_st_max_op2_K, T_st_min_op2_K, \
        Q_storage_content_fin_op2_W, T_storage_fin_op2_K, Q_loss2_W, mdot_DH_fin2_kgpers, \
        Q_uncontrollable_final_W = Optimized_Data2

        # Calculate if the initial and final storage levels are converged
        storageDeviation2 = calc_temperature_convergence(Q_storage_content_fin_op2_W)

        if storageDeviation2 > 0.0001:

            # Third Round optimization
            Q_stored_max_needed_3_W = np.amax(Q_storage_content_fin_op2_W) - np.amin(Q_storage_content_fin_op2_W)
            V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_stored_max_needed_3_W, T_ST_MAX,
                                                                                  T_ST_MIN)
            V3 = V_storage_possible_needed

            Q_initial_W = min(Q_disc_seasonstart_opt2_W[0], Q_storage_content_fin_op2_W[-1])
            T_initial_K = calc_T_initial_from_Q_and_V(Q_initial_W, T_ST_MIN, V_storage_initial_m3)

            Optimized_Data3, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K, Q_initial_W, locator,
                                                                       V_storage_possible_needed,
                                                                       solar_technologies_data, master_to_slave_vars,
                                                                       P_HP_max, config)
            Q_stored_max_opt3_W, Q_rejected_fin_opt3_W, Q_disc_seasonstart_opt3_W, T_st_max_op3_K, T_st_min_op3_K, \
            Q_storage_content_fin_op3_W, T_storage_fin_op3_K, Q_loss3_W, mdot_DH_fin3_kgpers, \
            Q_uncontrollable_final_W = Optimized_Data3

            storageDeviation3 = calc_temperature_convergence(Q_storage_content_fin_op3_W)

            if storageDeviation3 > 0.0001:
                # fourth Round optimization - reduce end temperature by rejecting earlier (minimize volume)
                Q_stored_max_needed_4_W = Q_stored_max_needed_3_W - (
                        Q_storage_content_fin_op3_W[-1] - Q_storage_content_fin_op3_W[0])
                V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_stored_max_needed_4_W, T_ST_MAX,
                                                                                      T_ST_MIN)
                V4 = V_storage_possible_needed
                Q_initial_W = min(Q_disc_seasonstart_opt3_W[0], Q_storage_content_fin_op3_W[-1])
                T_initial_K = calc_T_initial_from_Q_and_V(Q_initial_W, T_ST_MIN, V_storage_initial_m3)

                Optimized_Data4, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K, Q_initial_W, locator,
                                                                           V_storage_possible_needed,
                                                                           solar_technologies_data,
                                                                           master_to_slave_vars,
                                                                           P_HP_max, config)
                Q_stored_max_opt4_W, Q_rejected_fin_opt4_W, Q_disc_seasonstart_opt4_W, T_st_max_op4_K, T_st_min_op4_K, \
                Q_storage_content_fin_op4_W, T_storage_fin_op4_K, Q_loss4_W, mdot_DH_fin4_kgpers, \
                Q_uncontrollable_final_W = Optimized_Data4

                storageDeviation4 = calc_temperature_convergence(Q_storage_content_fin_op4_W)

                if storageDeviation4 > 0.0001:

                    # fifth Round optimization - minimize volume more so the temperature reaches a T_min + dT_margin
                    Q_stored_max_needed_5 = Q_stored_max_needed_4_W - (
                            Q_storage_content_fin_op4_W[-1] - Q_storage_content_fin_op4_W[0])
                    V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_stored_max_needed_5,
                                                                                          T_ST_MAX, T_ST_MIN)
                    V5 = V_storage_possible_needed
                    Q_initial_W = min(Q_disc_seasonstart_opt4_W[0], Q_storage_content_fin_op4_W[-1])
                    if Q_initial_W != 0:
                        Q_initial_min = Q_disc_seasonstart_opt4_W - min(
                            Q_storage_content_fin_op4_W)  # assuming the minimum at the end of the season
                        Q_buffer = DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * V_storage_possible_needed * master_to_slave_vars.dT_buffer / WH_TO_J
                        Q_initial_W = Q_initial_min + Q_buffer
                        T_initial_real = calc_T_initial_from_Q_and_V(Q_initial_min, T_ST_MIN, V_storage_possible_needed)
                        T_initial_K = master_to_slave_vars.dT_buffer + T_initial_real
                    else:
                        T_initial_K = calc_T_initial_from_Q_and_V(Q_initial_W, T_ST_MIN, V_storage_initial_m3)

                    Optimized_Data5, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K, Q_initial_W,
                                                                               locator,
                                                                               V_storage_possible_needed,
                                                                               solar_technologies_data,
                                                                               master_to_slave_vars, P_HP_max, config)
                    Q_stored_max_opt5, Q_rejected_fin_opt5, Q_disc_seasonstart_opt5, T_st_max_op5, T_st_min_op5, \
                    Q_storage_content_fin_op5, T_storage_fin_op5, Q_loss5, mdot_DH_fin5, Q_uncontrollable_final_W = Optimized_Data5

                    # Attempt for debugging
                    #   Issue:    1 file showed miss-match of final to initial storage content of 30%, all others had deviations of 0.5 % max
                    #   Idea:     check the final to initial storage content with an allowed margin of 5%.
                    #             If this happens, a new storage optimization run will be performed (sixth round)
                    #
                    #             If the 5% margin is still not maintined after round 6, cover / fill
                    #             the storage with a conventional boiler up to it's final value. As this re-filling can happen during hours of low
                    #             consumption, no extra machinery will be required.

                    storageDeviation5 = calc_temperature_convergence(Q_storage_content_fin_op5)

                    if storageDeviation5 > 0.0001:
                        Q_initial_W = min(Q_disc_seasonstart_opt5[0], Q_storage_content_fin_op5[-1])

                        Q_stored_max_needed_6 = float(
                            Q_stored_max_needed_5 - (Q_storage_content_fin_op5[-1] - Q_storage_content_fin_op5[0]))
                        V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_stored_max_needed_6,
                                                                                              T_ST_MAX, T_ST_MIN)
                        V6 = V_storage_possible_needed  # overwrite V5 on purpose as this is given back in case of a change

                        # leave initial values as we adjust the final outcome only, give back values from 5th round

                        Optimized_Data6, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K, Q_initial_W,
                                                                                   locator,
                                                                                   V_storage_possible_needed,
                                                                                   solar_technologies_data,
                                                                                   master_to_slave_vars,
                                                                                   P_HP_max, config)
                        Q_stored_max_opt6, Q_rejected_fin_opt6, Q_disc_seasonstart_opt6, T_st_max_op6, T_st_min_op6, Q_storage_content_fin_op6, \
                        T_storage_fin_op6, Q_loss6, mdot_DH_fin6, Q_uncontrollable_final_W = Optimized_Data6

                        storageDeviation6 = calc_temperature_convergence(Q_storage_content_fin_op6)

                        if storageDeviation6 > 0.0001:
                            Q_initial_W = min(Q_disc_seasonstart_opt6[0], Q_storage_content_fin_op6[-1])

                            Q_stored_max_needed_7 = float(
                                Q_stored_max_needed_6 - (Q_storage_content_fin_op6[-1] - Q_storage_content_fin_op6[0]))
                            V_storage_possible_needed = calc_storage_volume_from_heat_requirement(Q_stored_max_needed_7,
                                                                                                  T_ST_MAX, T_ST_MIN)
                            V7 = V_storage_possible_needed  # overwrite V5 on purpose as this is given back in case of a change

                            # leave initial values as we adjust the final outcome only, give back values from 5th round

                            Optimized_Data7, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K,
                                                                                       Q_initial_W,
                                                                                       locator,
                                                                                       V_storage_possible_needed,
                                                                                       solar_technologies_data,
                                                                                       master_to_slave_vars, P_HP_max,
                                                                                       config)
                            Q_stored_max_opt7, Q_rejected_fin_opt7, Q_disc_seasonstart_opt7, T_st_max_op7, T_st_min_op7, Q_storage_content_fin_op7, \
                            T_storage_fin_op7, Q_loss7, mdot_DH_fin7, Q_uncontrollable_final_W = Optimized_Data7

                            storageDeviation7 = calc_temperature_convergence(Q_storage_content_fin_op7)

                            if storageDeviation7 > 0.0001:
                                Q_initial_W = min(Q_disc_seasonstart_opt7[0], Q_storage_content_fin_op7[-1])

                                Q_stored_max_needed_8 = float(
                                    Q_stored_max_needed_7 - (
                                            Q_storage_content_fin_op7[-1] - Q_storage_content_fin_op7[0]))
                                V_storage_possible_needed = calc_storage_volume_from_heat_requirement(
                                    Q_stored_max_needed_8, T_ST_MAX, T_ST_MIN)
                                V8 = V_storage_possible_needed  # overwrite V5 on purpose as this is given back in case of a change

                                # leave initial values as we adjust the final outcome only, give back values from 5th round

                                Optimized_Data8, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K,
                                                                                           Q_initial_W,
                                                                                           locator,
                                                                                           V_storage_possible_needed,
                                                                                           solar_technologies_data,
                                                                                           master_to_slave_vars,
                                                                                           P_HP_max, config)
                                Q_stored_max_opt8, Q_rejected_fin_opt8, Q_disc_seasonstart_opt8, T_st_max_op8, T_st_min_op8, Q_storage_content_fin_op8, \
                                T_storage_fin_op8, Q_loss8, mdot_DH_fin8, Q_uncontrollable_final_W = Optimized_Data8

                                storageDeviation8 = calc_temperature_convergence(Q_storage_content_fin_op8)

                                if storageDeviation8 > 0.0001:
                                    Q_initial_W = min(Q_disc_seasonstart_opt8[0], Q_storage_content_fin_op8[-1])

                                    Q_stored_max_needed_9 = float(
                                        Q_stored_max_needed_8 - (
                                                Q_storage_content_fin_op8[-1] - Q_storage_content_fin_op8[0]))
                                    V_storage_possible_needed = calc_storage_volume_from_heat_requirement(
                                        Q_stored_max_needed_9, T_ST_MAX, T_ST_MIN)
                                    V9 = V_storage_possible_needed  # overwrite V5 on purpose as this is given back in case of a change

                                    # leave initial values as we adjust the final outcome only, give back values from 5th round

                                    Optimized_Data9, storage_dispatch = StDesOp.Storage_Design(CSV_NAME, T_initial_K,
                                                                                               Q_initial_W,
                                                                                               locator,
                                                                                               V_storage_possible_needed,
                                                                                               solar_technologies_data,
                                                                                               master_to_slave_vars,
                                                                                               P_HP_max, config)
                                    Q_stored_max_opt9, Q_rejected_fin_opt9, Q_disc_seasonstart_opt9, T_st_max_op9, T_st_min_op9, Q_storage_content_fin_op9, \
                                    T_storage_fin_op9, Q_loss9, mdot_DH_fin9, Q_uncontrollable_final_W = Optimized_Data9

                                    storageDeviation9 = calc_temperature_convergence(Q_storage_content_fin_op9)

                                    if storageDeviation9 > 0.0001:
                                        Q_initial_W = min(Q_disc_seasonstart_opt9[0], Q_storage_content_fin_op9[-1])

                                        Q_stored_max_needed_10 = float(
                                            Q_stored_max_needed_9 - (
                                                    Q_storage_content_fin_op9[-1] - Q_storage_content_fin_op9[0]))
                                        V_storage_possible_needed = calc_storage_volume_from_heat_requirement(
                                            Q_stored_max_needed_10, T_ST_MAX, T_ST_MIN)
                                        V10 = V_storage_possible_needed  # overwrite V5 on purpose as this is given back in case of a change

                                        # leave initial values as we adjust the final outcome only, give back values from 5th round

                                        Optimized_Data10, storage_dispatch = StDesOp.Storage_Design(CSV_NAME,
                                                                                                    T_initial_K,
                                                                                                    Q_initial_W,
                                                                                                    locator,
                                                                                                    V_storage_possible_needed,
                                                                                                    solar_technologies_data,
                                                                                                    master_to_slave_vars,
                                                                                                    P_HP_max, config)
                                        Q_stored_max_opt10, Q_rejected_fin_opt10, Q_disc_seasonstart_opt10, T_st_max_op10, T_st_min_op10, Q_storage_content_fin_op10, \
                                        T_storage_fin_op10, Q_loss10, mdot_DH_fin10, Q_uncontrollable_final_W = Optimized_Data10

    # Get results from storage operation
    E_aux_ch_W = storage_dispatch['E_Storage_charging_req_W']
    E_aux_dech_W = storage_dispatch['E_Storage_discharging_req_W']
    E_thermalstorage_W = E_aux_ch_W + E_aux_dech_W

    # VARIABLE COSTS
    Opex_var_storage_USDhr = [load * price for load, price in zip(E_thermalstorage_W, lca.ELEC_PRICE)]
    Opex_var_storage_USD = sum(Opex_var_storage_USDhr)

    # CAPEX AND FIXED COSTS
    StorageVol_m3 = storage_dispatch["Storage_Size_m3"]  # take the first line
    Capex_a_storage_USD, Opex_fixed_storage_USD, Capex_storage_USD = storage.calc_Cinv_storage(StorageVol_m3,
                                                                                               locator, config,
                                                                                               'TES2')

    # EMISSIONS AND PRIMARY ENERGY
    GHG_storage_tonCO2 = (np.sum(E_thermalstorage_W) * WH_TO_J / 1.0E6) * lca.EL_TO_CO2 / 1E3
    PEN_storage_MJoil = (np.sum(E_thermalstorage_W) * WH_TO_J / 1.0E6) * lca.EL_TO_OIL_EQ

    # calculate electricity required to bring the temperature to convergence
    Q_storage_content_W = np.array(storage_dispatch['Q_storage_content_W'])
    StorageContentEndOfYear = Q_storage_content_W[-1]
    StorageContentStartOfYear = Q_storage_content_W[0]

    if StorageContentEndOfYear < StorageContentStartOfYear:
        QToCoverByStorageBoiler_W = float(StorageContentEndOfYear - StorageContentStartOfYear)
        eta_fictive_Boiler = 0.8  # add rather low efficiency as a penalty
        E_gasPrim_fictiveBoiler_W = QToCoverByStorageBoiler_W / eta_fictive_Boiler
    else:
        E_gasPrim_fictiveBoiler_W = 0

    GHG_storage_tonCO2 += (E_gasPrim_fictiveBoiler_W * WH_TO_J / 1.0E6) * lca.NG_BOILER_TO_CO2_STD / 1E3
    PEN_storage_MJoil += (E_gasPrim_fictiveBoiler_W * WH_TO_J / 1.0E6) * lca.NG_BOILER_TO_OIL_STD

    # FIXME: repeating line 291-309?
    # Fill up storage if end-of-season energy is lower than beginning of season
    Q_Storage_SeasonEndReheat_W = Q_storage_content_W[-1] - Q_storage_content_W[0]

    if Q_Storage_SeasonEndReheat_W > 0:
        cost_Boiler_for_Storage_reHeat_at_seasonend_USD = float(
            Q_Storage_SeasonEndReheat_W) / 0.8 * prices.NG_PRICE / 1E3  # efficiency is assumed to be 0.8
        GHG_Boiler_for_Storage_reHeat_at_seasonend_tonCO2 = ((float(
            Q_Storage_SeasonEndReheat_W) / 0.8) * WH_TO_J / 1.0E6) * (lca.NG_BOILER_TO_CO2_STD / 1E3)
        PEN_Boiler_for_Storage_reHeat_at_seasonend_MJoil = ((float(
            Q_Storage_SeasonEndReheat_W) / 0.8) * WH_TO_J / 1.0E6) * lca.NG_BOILER_TO_OIL_STD
    else:
        cost_Boiler_for_Storage_reHeat_at_seasonend_USD = 0
        GHG_Boiler_for_Storage_reHeat_at_seasonend_tonCO2 = 0
        PEN_Boiler_for_Storage_reHeat_at_seasonend_MJoil = 0

    Opex_var_storage_USD += cost_Boiler_for_Storage_reHeat_at_seasonend_USD
    GHG_storage_tonCO2 += GHG_Boiler_for_Storage_reHeat_at_seasonend_tonCO2
    PEN_storage_MJoil += PEN_Boiler_for_Storage_reHeat_at_seasonend_MJoil

    # HEATPUMP FOR SEASONAL SOLAR STORAGE OPERATION (CHARING AND DISCHARGING) TO DH
    storage_dispatch_df = pd.DataFrame(storage_dispatch)
    array = np.array(storage_dispatch_df[["E_Storage_charging_req_W", "E_Storage_discharging_req_W", "Q_Storage_gen_W",
                                          "Q_Storage_req_W"]])
    Q_HP_max_storage_W = 0
    for i in range(8760):
        if array[i][0] > 0:
            Q_HP_max_storage_W = max(Q_HP_max_storage_W, array[i][3] + array[i][0])
        elif array[i][1] > 0:
            Q_HP_max_storage_W = max(Q_HP_max_storage_W, array[i][2] + array[i][1])

    Capex_a_HP_storage_USD, Opex_fixed_HP_storage_USD, Capex_HP_storage_USD = hp.calc_Cinv_HP(Q_HP_max_storage_W,
                                                                                              locator,
                                                                                              'HP2')

    # SUMMARY OF COSTS AND EMISSIONS
    performance = {
        # annual costs
        "Capex_a_Storage_connected_USD": Capex_a_storage_USD + Capex_a_HP_storage_USD,

        # total costs
        "Capex_total_Storage_connected_USD": Capex_storage_USD + Capex_HP_storage_USD,

        # opex fixed costs
        "Opex_fixed_Storage_connected_USD": Opex_fixed_storage_USD + Opex_fixed_HP_storage_USD,

        # opex var costs
        "Opex_var_Storage_connected_USD": Opex_var_storage_USD,

        # opex annual costs
        "Opex_a_Storage_connected_USD": Opex_fixed_storage_USD + Opex_fixed_HP_storage_USD + Opex_var_storage_USD,
    }

    return performance, storage_dispatch


def calc_T_initial_from_Q_and_V(Q_initial_W, T_ST_MIN, V_storage_initial_m3):
    T_initial_K = T_ST_MIN + Q_initial_W * WH_TO_J / (
            DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * V_storage_initial_m3)
    return T_initial_K


def calc_temperature_convergence(Q_storage_content_final_W):
    InitialStorageContent = float(Q_storage_content_final_W[0])
    FinalStorageContent = float(Q_storage_content_final_W[-1])
    if InitialStorageContent == 0 or FinalStorageContent == 0:  # catch error in advance of having 0 / 0
        storageDeviation = 0
    else:
        storageDeviation = (abs(InitialStorageContent - FinalStorageContent) / FinalStorageContent)
    return storageDeviation


def calc_storage_volume_from_heat_requirement(Q_required_in_storage_W, T_ST_MAX, T_ST_MIN):
    V_storage_possible_needed = (Q_required_in_storage_W) * WH_TO_J / (
            DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_ST_MAX - T_ST_MIN))
    return V_storage_possible_needed


def read_solar_technologies_data(locator, master_to_slave_vars):
    # Import Solar Data
    if master_to_slave_vars.SC_ET_on == 1 and master_to_slave_vars.SC_ET_share > 0.0:
        share_allowed = master_to_slave_vars.SC_ET_share
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        Q_SC_ET_gen_Wh, Tscr_th_SC_ET_K, Area_SC_ET_m2, E_SC_ET_req_Wh = calc_available_generation_solar(locator,
                                                                                                         buildings,
                                                                                                         share_allowed,
                                                                                                         type="SC_ET")
    else:
        Q_SC_ET_gen_Wh = np.zeros(HOURS_IN_YEAR)
        Tscr_th_SC_ET_K = np.zeros(HOURS_IN_YEAR)
        E_SC_ET_req_Wh = np.zeros(HOURS_IN_YEAR)

    # SC_FP
    if master_to_slave_vars.SC_FP_on == 1 and master_to_slave_vars.SC_FP_share > 0.0:
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = master_to_slave_vars.SC_FP_share
        Q_SC_FP_gen_Wh, Tscr_th_SC_FP_K, Area_SC_FP_m2, E_SC_FP_req_Wh = calc_available_generation_solar(locator,
                                                                                                         buildings,
                                                                                                         share_allowed,
                                                                                                         type="SC_FP")
    else:
        Q_SC_FP_gen_Wh = np.zeros(HOURS_IN_YEAR)
        Tscr_th_SC_FP_K = np.zeros(HOURS_IN_YEAR)
        E_SC_FP_req_Wh = np.zeros(HOURS_IN_YEAR)

    # PVT
    if master_to_slave_vars.PVT_on == 1 and master_to_slave_vars.PVT_share > 0.0:
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = master_to_slave_vars.PVT_share
        E_PVT_gen_Wh, Q_PVT_gen_Wh, Area_PVT_m2, Tscr_th_PVT_K, E_PVT_req_Wh = calc_available_generation_PVT(locator,
                                                                                                             buildings,
                                                                                                             share_allowed)
    else:
        E_PVT_gen_Wh = np.zeros(HOURS_IN_YEAR)
        Q_PVT_gen_Wh = np.zeros(HOURS_IN_YEAR)
        Tscr_th_PVT_K = np.zeros(HOURS_IN_YEAR)
        E_PVT_req_Wh = np.zeros(HOURS_IN_YEAR)

    Solar_E_aux_Wh = E_SC_ET_req_Wh + E_SC_FP_req_Wh + E_PVT_req_Wh

    solar_technologies_data = {
        'E_PVT_gen_W': E_PVT_gen_Wh,
        'Q_PVT_gen_W': Q_PVT_gen_Wh,
        "Q_SC_ET_gen_W": Q_SC_ET_gen_Wh,
        "Q_SC_FP_gen_W": Q_SC_FP_gen_Wh,
        "Solar_E_aux_W": Solar_E_aux_Wh,
        "Tscr_th_PVT_K": Tscr_th_PVT_K,
        "Tscr_th_SC_ET_K": Tscr_th_SC_ET_K,
        "Tscr_th_SC_FP_K": Tscr_th_SC_FP_K
    }

    return solar_technologies_data


def calc_available_generation_PVT(locator, buildings, share_allowed):
    A_PVT_m2 = 0.0
    E_PVT_gen_kWh = np.zeros(HOURS_IN_YEAR)
    Q_PVT_gen_kWh = np.zeros(HOURS_IN_YEAR)
    E_PVT_req_kWh = np.zeros(HOURS_IN_YEAR)
    mcp_x_T = np.zeros(HOURS_IN_YEAR)
    mcp = np.zeros(HOURS_IN_YEAR)
    for building_name in buildings:
        building_PVT = pd.read_csv(
            os.path.join(locator.get_potentials_solar_folder(), building_name + '_PVT.csv')).fillna(value=0.0)
        E_PVT_gen_kWh += building_PVT['E_PVT_gen_kWh']
        Q_PVT_gen_kWh += building_PVT['Q_PVT_gen_kWh']
        E_PVT_req_kWh += building_PVT['Eaux_PVT_kWh']
        A_PVT_m2 += building_PVT['Area_PVT_m2'][0]
        mcp_x_T += building_PVT['mcp_PVT_kWperC'] * (building_PVT['T_PVT_sup_C'] + 273)  # to K
        mcp += building_PVT['mcp_PVT_kWperC']

    Tscr_th_PVT_K = (mcp_x_T / mcp)

    E_PVT_gen_Wh = E_PVT_gen_kWh * share_allowed * 1000
    Q_PVT_gen_Wh = Q_PVT_gen_kWh * share_allowed * 1000
    E_PVT_req_Wh = E_PVT_req_kWh * share_allowed * 1000
    Area_PVT_m2 = A_PVT_m2 * share_allowed

    return E_PVT_gen_Wh, Q_PVT_gen_Wh, Area_PVT_m2, Tscr_th_PVT_K, E_PVT_req_Wh


def calc_available_generation_solar(locator, buildings, share_allowed, type):
    A_PVT_m2 = 0.0
    Q_PVT_gen_kWh = np.zeros(HOURS_IN_YEAR)
    E_SC_req_kWh = np.zeros(HOURS_IN_YEAR)
    mcp_x_T = np.zeros(HOURS_IN_YEAR)
    mcp = np.zeros(HOURS_IN_YEAR)
    for building_name in buildings:
        data = pd.read_csv(
            os.path.join(locator.get_potentials_solar_folder(), building_name + '_' + type + '.csv')).fillna(value=0.0)
        Q_PVT_gen_kWh += data['Q_SC_gen_kWh']
        E_SC_req_kWh += data['Eaux_SC_kWh']
        A_PVT_m2 += data['Area_SC_m2'][0]
        mcp_x_T += data['mcp_SC_kWperC'] * (data['T_SC_sup_C'] + 273)  # to K
        mcp += data['mcp_SC_kWperC']

    Tscr_th_PVT_K = (mcp_x_T / mcp)
    Q_PVT_gen_Wh = Q_PVT_gen_kWh * share_allowed * 1000
    E_SC_req_Wh = E_SC_req_kWh * share_allowed * 1000
    Area_PVT_m2 = A_PVT_m2 * share_allowed

    return Q_PVT_gen_Wh, Tscr_th_PVT_K, Area_PVT_m2, E_SC_req_Wh
