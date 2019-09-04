# -*- coding: utf-8 -*-
"""
Storage Design And Operation
    This File is called by "Storage_Optimizer_incl_Losses_main.py" (Optimization Routine) and
    will operate the storage according to the inputs given by the main file.

    The operation data is stored

"""

from __future__ import division

import os

import numpy as np
import pandas as pd

import SolarPowerHandler_incl_Losses as SPH_fn
from cea.constants import HOURS_IN_YEAR
from cea.optimization.constants import *
from cea.resources.geothermal import calc_ground_temperature
from cea.technologies.constants import DT_HEAT
from cea.utilities import epwreader


def Storage_Design(CSV_NAME, T_storage_old_K, Q_in_storage_old_W, locator,
                   STORAGE_SIZE_m3, solar_technologies_data, master_to_slave_vars, P_HP_max_W, config):
    """

    :param CSV_NAME:
    :param SOLCOL_TYPE:
    :param T_storage_old_K:
    :param Q_in_storage_old_W:
    :param locator:
    :param STORAGE_SIZE_m3:
    :param STORE_DATA:
    :param master_to_slave_vars:
    :param P_HP_max_W:
    :type CSV_NAME:
    :type SOLCOL_TYPE:
    :type T_storage_old_K:
    :type Q_in_storage_old_W:
    :type locator:
    :type STORAGE_SIZE_m3:
    :type STORE_DATA:
    :type master_to_slave_vars:
    :type P_HP_max_W:
    :return:
    :rtype:
    """

    # Get network summary
    Network_Data, \
    Q_DH_networkload_Wh, \
    Q_wasteheatServer_Wh, \
    T_DH_return_array_K, \
    T_DH_supply_array_K, \
    mdot_heat_netw_total_kgpers = read_data_from_Network_summary(CSV_NAME, locator)

    # Get ground temperatures
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent',
                                                       'windspd_ms', 'skytemp_C']]
    T_ground_K = calc_ground_temperature(locator, weather_data['drybulb_C'], depth_m=10)

    # Calculate DH operation with on-site energy sources and storage
    T_amb_K = weather_data['drybulb_C'] + 273.15  # K
    T_storage_min_K = master_to_slave_vars.T_ST_MAX
    Q_disc_seasonstart_W = [0]

    # Get installation and production data of all types of solar technologies for every hour of the year
    E_PVT_gen_Whr = solar_technologies_data['E_PVT_gen_W']
    Q_PVT_gen_Whr = solar_technologies_data['Q_PVT_gen_W']
    Q_SC_ET_gen_Whr = solar_technologies_data['Q_SC_ET_gen_W']
    Q_SC_FP_gen_Whr = solar_technologies_data['Q_SC_FP_gen_W']
    Solar_Tscr_th_PVT_K_hour = solar_technologies_data['Tscr_th_PVT_K']
    Solar_Tscr_th_SC_ET_K_hour = solar_technologies_data['Tscr_th_SC_ET_K']
    Solar_Tscr_th_SC_FP_K_hour = solar_technologies_data['Tscr_th_SC_FP_K']

    # Initialize variables
    Q_storage_content_final_Whr = np.zeros(HOURS_IN_YEAR)
    T_storage_final_Khr = np.zeros(HOURS_IN_YEAR)
    Q_from_storage_final_Whr = np.zeros(HOURS_IN_YEAR)
    Q_to_storage_final_Whr = np.zeros(HOURS_IN_YEAR)
    E_aux_ch_final_Whr = np.zeros(HOURS_IN_YEAR)
    E_aux_dech_final_Whr = np.zeros(HOURS_IN_YEAR)
    Q_uncontrollable_final_Whr = np.zeros(HOURS_IN_YEAR)
    Q_missing_final_Whr = np.zeros(HOURS_IN_YEAR)
    Q_rejected_final_W = np.zeros(HOURS_IN_YEAR)
    mdot_DH_final_kgpers = np.zeros(HOURS_IN_YEAR)
    E_HPSC_FP_final_req_Whr = np.zeros(HOURS_IN_YEAR)
    E_HPSC_ET_final_req_Whr = np.zeros(HOURS_IN_YEAR)
    E_HPPVT_final_req_Whr = np.zeros(HOURS_IN_YEAR)
    E_HPServer_final_req_Whr = np.zeros(HOURS_IN_YEAR)
    Q_PVT_to_directload_Whr = np.zeros(HOURS_IN_YEAR)
    Q_SC_ET_to_directload_Whr = np.zeros(HOURS_IN_YEAR)
    Q_SC_FP_to_directload_Whr = np.zeros(HOURS_IN_YEAR)
    Q_server_to_directload_Whr = np.zeros(HOURS_IN_YEAR)
    Q_PVT_to_storage_Whr = np.zeros(HOURS_IN_YEAR)
    Q_SC_ET_to_storage_Whr = np.zeros(HOURS_IN_YEAR)
    Q_SC_FP_to_storage_Whr = np.zeros(HOURS_IN_YEAR)
    Q_server_to_storage_Whr = np.zeros(HOURS_IN_YEAR)
    Q_HP_Server_Whr = np.zeros(HOURS_IN_YEAR)
    Q_HP_PVT_Whr = np.zeros(HOURS_IN_YEAR)
    Q_HP_SC_ET_Whr = np.zeros(HOURS_IN_YEAR)
    Q_HP_SC_FP_Whr = np.zeros(HOURS_IN_YEAR)
    Q_loss_Whr = np.zeros(HOURS_IN_YEAR)

    for HOUR in range(HOURS_IN_YEAR):  # no idea why, but if we try a for loop it does not work
        # Get network temperatures and capacity flow rates
        T_DH_sup_K = T_DH_supply_array_K[HOUR]
        T_DH_return_K = T_DH_return_array_K[HOUR]
        mdot_DH_kgpers = mdot_heat_netw_total_kgpers[HOUR]
        Q_Server_gen_initial_W = Q_wasteheatServer_Wh[HOUR]
        Q_PVT_gen_W = Q_PVT_gen_Whr[HOUR]
        Q_SC_ET_gen_W = Q_SC_ET_gen_Whr[HOUR]
        Q_SC_FP_gen_W = Q_SC_FP_gen_Whr[HOUR]
        Solar_Tscr_th_PVT_K = Solar_Tscr_th_PVT_K_hour[HOUR]
        Solar_Tscr_th_SC_ET_K = Solar_Tscr_th_SC_ET_K_hour[HOUR]
        Solar_Tscr_th_SC_FP_K = Solar_Tscr_th_SC_FP_K_hour[HOUR]

        # Get heating demand in DH
        Q_network_demand_W = Q_DH_networkload_Wh[HOUR]

        # Get heating proved by SOLAR AND DATA CENTER (IF ANY)
        E_HP_solar_and_server_req_W, \
        Q_PVT_gen_W, \
        Q_SC_ET_gen_W, \
        Q_SC_FP_gen_W, \
        Q_Server_gen_W, \
        E_HPSC_FP_req_W, \
        E_HPSC_ET_req_W, \
        E_HPPVT_reg_W, \
        E_HPServer_reg_W, \
        Q_HP_Server_W, \
        Q_HP_PVT_W, \
        Q_HP_SC_ET_W, \
        Q_HP_SC_FP_W = get_heating_provided_by_onsite_energy_sources(Q_PVT_gen_W,
                                                                     Q_SC_ET_gen_W,
                                                                     Q_SC_FP_gen_W,
                                                                     Q_Server_gen_initial_W,
                                                                     Solar_Tscr_th_PVT_K,
                                                                     Solar_Tscr_th_SC_ET_K,
                                                                     Solar_Tscr_th_SC_FP_K,
                                                                     T_DH_sup_K,
                                                                     master_to_slave_vars)

        # Calculate storage operation
        Q_in_storage_new_W, \
        T_storage_new_K, \
        Q_from_storage_req_W, \
        Q_to_storage_W, \
        E_aux_ch_W, \
        E_aux_dech_W, \
        Q_missing_W, \
        Q_loss_W, \
        mdot_DH_missing_kgpers, \
        Q_server_to_directload_W, \
        Q_server_to_storage_W, \
        Q_PVT_to_directload_W, \
        Q_PVT_to_storage_W, \
        Q_SC_ET_to_directload_W, \
        Q_SC_ET_to_storage_W, \
        Q_SC_FP_to_directload_W, \
        Q_SC_FP_to_storage_W = SPH_fn.Storage_Operator(Q_PVT_gen_W, Q_SC_ET_gen_W, Q_SC_FP_gen_W, Q_Server_gen_W,
                                                       Q_network_demand_W, T_storage_old_K, T_DH_sup_K, T_amb_K[HOUR],
                                                       Q_in_storage_old_W, T_DH_return_K, mdot_DH_kgpers,
                                                       STORAGE_SIZE_m3,
                                                       master_to_slave_vars, P_HP_max_W, T_ground_K[HOUR])

        ## Modify storage level according to temeprature
        if Q_in_storage_new_W < 0.0001:
            Q_in_storage_new_W = 0.0

        # if storage temperature too high, no more charging possible - reject energy
        if T_storage_new_K >= master_to_slave_vars.T_ST_MAX - 0.001:
            Q_in_storage_new_W = min(Q_in_storage_old_W, Q_in_storage_new_W)
            Q_to_storage_W = max(Q_in_storage_new_W - Q_in_storage_old_W, 0)
            Q_rejected_final_W[HOUR] = Q_PVT_gen_W + \
                                       Q_SC_ET_gen_W + \
                                       Q_SC_FP_gen_W + \
                                       Q_Server_gen_W \
                                       - Q_to_storage_W
            T_storage_new_K = min(T_storage_old_K, T_storage_new_K)
            E_aux_ch_W = 0

        ## Overwrite values for the calculation in the next timestep
        Q_in_storage_old_W = Q_in_storage_new_W
        T_storage_old_K = T_storage_new_K

        # catch an error if the storage temperature is too low
        # if T_storage_old_K < T_amb_K[HOUR] - 1:
        #     # print "Storage temperature is too lower than ambient, please check the calculation"

        ## Save values for the current timestep
        Q_storage_content_final_Whr[HOUR] = Q_in_storage_new_W
        T_storage_final_Khr[HOUR] = T_storage_new_K
        Q_from_storage_final_Whr[HOUR] = Q_from_storage_req_W
        Q_to_storage_final_Whr[HOUR] = Q_to_storage_W
        E_aux_ch_final_Whr[HOUR] = E_aux_ch_W
        E_aux_dech_final_Whr[HOUR] = E_aux_dech_W

        # scale to the fraction taht goes directly to the grid. the rest is considered in the storage charging and discharging
        E_HPSC_FP_final_req_Whr[HOUR] = E_HPSC_FP_req_W
        E_HPSC_ET_final_req_Whr[HOUR] = E_HPSC_ET_req_W
        E_HPPVT_final_req_Whr[HOUR] = E_HPPVT_reg_W
        E_HPServer_final_req_Whr[HOUR] = E_HPServer_reg_W

        Q_PVT_to_directload_Whr[HOUR] = Q_PVT_to_directload_W
        Q_SC_ET_to_directload_Whr[HOUR] = Q_SC_ET_to_directload_W
        Q_SC_FP_to_directload_Whr[HOUR] = Q_SC_FP_to_directload_W
        Q_server_to_directload_Whr[HOUR] = Q_server_to_directload_W
        Q_PVT_to_storage_Whr[HOUR] = Q_PVT_to_storage_W
        Q_SC_ET_to_storage_Whr[HOUR] = Q_SC_ET_to_storage_W
        Q_SC_FP_to_storage_Whr[HOUR] = Q_SC_FP_to_storage_W
        Q_server_to_storage_Whr[HOUR] = Q_server_to_storage_W
        Q_HP_Server_Whr[HOUR] = Q_HP_Server_W
        Q_HP_PVT_Whr[HOUR] = Q_HP_PVT_W
        Q_HP_SC_ET_Whr[HOUR] = Q_HP_SC_ET_W
        Q_HP_SC_FP_Whr[HOUR] = Q_HP_SC_FP_W
        Q_loss_Whr[HOUR] = Q_loss_W
        # heating demand satisfied directly from these technologies
        Q_uncontrollable_final_Whr[HOUR] = Q_PVT_to_directload_W + \
                                           Q_SC_ET_to_directload_W + \
                                           Q_SC_FP_to_directload_W + \
                                           Q_server_to_directload_W

        # heating demand required from heating plant
        Q_missing_final_Whr[HOUR] = Q_network_demand_W - Q_uncontrollable_final_Whr[HOUR] - Q_from_storage_final_Whr[
            HOUR]

        # amount of heat required from heating plants
        mdot_DH_final_kgpers[HOUR] = mdot_DH_missing_kgpers

        if T_storage_new_K <= T_storage_min_K:
            T_storage_min_K = T_storage_new_K
            Q_disc_seasonstart_W[0] += Q_from_storage_req_W

    storage_dispatch = {

        # TOTAL ENERGY GENERATED
        "Q_SC_ET_gen_W": Q_SC_ET_gen_Whr,
        "Q_SC_FP_gen_W": Q_SC_FP_gen_Whr,
        "Q_PVT_gen_W": Q_PVT_gen_Whr,
        "Q_HP_Server_gen_W": Q_server_to_storage_Whr + Q_server_to_directload_Whr,

        # ENERGY GOING DIRECTLY TO CUSTOMERS
        "Q_PVT_gen_directload_W": Q_PVT_to_directload_Whr,
        "Q_SC_ET_gen_directload_W": Q_SC_ET_to_directload_Whr,
        "Q_SC_FP_gen_directload_W": Q_SC_FP_to_directload_Whr,
        "Q_HP_Server_gen_directload_W": Q_server_to_directload_Whr,

        # ENERGY GOING INTO THE STORAGE
        # total
        "Q_Storage_req_W": Q_to_storage_final_Whr,
        # per technology
        "Q_PVT_gen_storage_W": Q_PVT_to_storage_Whr,
        "Q_SC_ET_gen_storage_W": Q_SC_ET_to_storage_Whr,
        "Q_SC_FP_gen_storage_W": Q_SC_FP_to_storage_Whr,
        "Q_HP_Server_gen_storage_W": Q_server_to_storage_Whr,

        # ENERGY COMMING FROM THE STORAGE
        "Q_Storage_gen_W": Q_from_storage_final_Whr,

        # AUXILIARY LOADS NEEDED TO CHARGE/DISCHARGE THE STORAGE
        "E_Storage_charging_req_W": E_aux_ch_final_Whr,
        "E_Storage_discharging_req_W": E_aux_dech_final_Whr,
        "E_HP_SC_FP_req_W": E_HPSC_FP_final_req_Whr,  # this is included in charging the storage
        "E_HP_SC_ET_req_W": E_HPSC_ET_final_req_Whr,  # this is included in charging the storage
        "E_HP_PVT_req_W": E_HPPVT_final_req_Whr,  # this is included in charging the storage
        "E_HP_Server_req_W": E_HPServer_final_req_Whr,  # this is included in charging the storage

        # ENERGY THAT NEEDS TO BE SUPPLIED (NEXT)
        "Q_req_after_storage_W": Q_missing_final_Whr,

        # mass flow rate of the network, size and energy generated
        "mdot_DH_fin_kgpers": mdot_DH_final_kgpers,
        "E_PVT_gen_W": E_PVT_gen_Whr,  # useful later on for the electricity dispatch curve
        "Storage_Size_m3": STORAGE_SIZE_m3,
        "Q_storage_content_W": Q_storage_content_final_Whr,
        "Q_DH_networkload_W": Q_DH_networkload_Wh,

        # this helps to know the peak (thermal) of the heatpumps
        "Q_HP_Server_W": Q_HP_PVT_Whr,
        "Q_HP_PVT_W": Q_HP_PVT_Whr,
        "Q_HP_SC_ET_W": Q_HP_SC_ET_Whr,
        "Q_HP_SC_FP_W": Q_HP_SC_FP_Whr,
    }

    Q_stored_max_W = np.amax(Q_storage_content_final_Whr)
    T_st_max_K = np.amax(T_storage_final_Khr)
    T_st_min_K = np.amin(T_storage_final_Khr)
    Q_loss_tot_W = np.sum(Q_loss_Whr)

    return (Q_stored_max_W, Q_rejected_final_W, Q_disc_seasonstart_W, T_st_max_K, T_st_min_K,
            Q_storage_content_final_Whr, T_storage_final_Khr, Q_loss_tot_W, mdot_DH_final_kgpers,
            Q_uncontrollable_final_Whr), storage_dispatch


def get_heating_provided_by_onsite_energy_sources(Q_PVT_gen_W,
                                                  Q_SC_ET_gen_W,
                                                  Q_SC_FP_gen_W,
                                                  Q_Server_gen_initial_W,
                                                  Solar_Tscr_th_PVT_K,
                                                  Solar_Tscr_th_SC_ET_K,
                                                  Solar_Tscr_th_SC_FP_K,
                                                  T_DH_sup_K,
                                                  master_to_slave_vars):
    # Check if each source needs a heat-pump, calculate the final energy required
    # server
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        Q_Server_gen_W = Q_Server_gen_initial_W * ETA_SERVER_TO_HEAT  # accounting for innefficiencies
        E_HPServer_req_W = 0.0
        if T_DH_sup_K > T_FROM_SERVER - DT_HEAT:  # and checkpoint_QfromServer == 1:
            # use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (T_FROM_SERVER - DT_HEAT))
            COP = HP_ETA_EX * COP_th
            E_HPServer_req_W = Q_Server_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
            if E_HPServer_req_W > 0:
                Q_HP_Server_W = Q_Server_gen_W
                Q_Server_gen_W += E_HPServer_req_W
            else:
                Q_HP_Server_W = 0.0
        else:
            Q_HP_Server_W = 0.0
    else:
        Q_Server_gen_W = 0.0
        E_HPServer_req_W = 0.0
        Q_HP_Server_W = 0.0

    # PVT
    if T_DH_sup_K > Solar_Tscr_th_PVT_K - DT_HEAT:  # and checkpoint_PVT == 1:
        COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_PVT_K - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_HPPVT_req_W = Q_PVT_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
        if E_HPPVT_req_W > 0:
            Q_HP_PVT_W = Q_PVT_gen_W
            Q_PVT_gen_W += E_HPPVT_req_W
        else:
            Q_HP_PVT_W = 0.0
    else:
        E_HPPVT_req_W = 0.0
        Q_HP_PVT_W = 0.0

    # SC_ET
    if T_DH_sup_K > Solar_Tscr_th_SC_ET_K - DT_HEAT:  # and checkpoint_SC == 1:
        COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_SC_ET_K - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_HPSC_ET_req_W = Q_SC_ET_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
        if E_HPSC_ET_req_W > 0:
            Q_HP_SC_ET_W = Q_SC_ET_gen_W
            Q_SC_ET_gen_W += E_HPSC_ET_req_W
        else:
            Q_HP_SC_ET_W = 0.0
    else:
        E_HPSC_ET_req_W = 0.0
        Q_HP_SC_ET_W = 0.0

    # SC_FP
    if T_DH_sup_K > Solar_Tscr_th_SC_FP_K - DT_HEAT:  # and checkpoint_SC == 1:
        COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_SC_FP_K - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_HPSC_FP_req_W = Q_SC_FP_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
        if E_HPSC_FP_req_W > 0:
            Q_HP_SC_FP_W = Q_SC_FP_gen_W
            Q_SC_FP_gen_W += E_HPSC_FP_req_W
        else:
            Q_HP_SC_FP_W = 0.0
    else:
        E_HPSC_FP_req_W = 0.0
        Q_HP_SC_FP_W = 0.0

    E_HP_solar_and_server_req_Wh = float(E_HPSC_FP_req_W + E_HPSC_ET_req_W + E_HPPVT_req_W + E_HPServer_req_W)
    # Heat Recovery has some losses, these are taken into account as "overall Losses", i.e.: from Source to DH Pipe

    return E_HP_solar_and_server_req_Wh, \
           Q_PVT_gen_W, \
           Q_SC_ET_gen_W, \
           Q_SC_FP_gen_W, \
           Q_Server_gen_W, \
           E_HPSC_FP_req_W, \
           E_HPSC_ET_req_W, \
           E_HPPVT_req_W, \
           E_HPServer_req_W, \
           Q_HP_Server_W, \
           Q_HP_PVT_W, \
           Q_HP_SC_ET_W, \
           Q_HP_SC_FP_W



def read_data_from_Network_summary(CSV_NAME, locator):
    # Import Network Data
    Network_Data = pd.read_csv(locator.get_optimization_thermal_network_data_file(CSV_NAME))
    # recover Network Data:
    mdot_heat_netw_total_kgpers = Network_Data['mdot_DH_netw_total_kgpers'].values
    Q_DH_networkload_W = Network_Data['Q_DHNf_W'].values
    T_DH_return_array_K = Network_Data['T_DHNf_re_K'].values
    T_DH_supply_array_K = Network_Data['T_DHNf_sup_K'].values
    Q_wasteheatServer_W = Network_Data['Qcdata_netw_total_kWh'].values * 1000
    return Network_Data, Q_DH_networkload_W, Q_wasteheatServer_W, T_DH_return_array_K, T_DH_supply_array_K, mdot_heat_netw_total_kgpers


""" DESCRIPTION FOR FUTHER USAGE"""
# Q_missing_fin  : has to be replaced by other means, like a HP
# Q_from_storage_fin : What is used from Storage
# Q_aus_fin : how much energy was spent on Auxillary power !! NOT WORKING PROPERLY !!
# Q_from_storage_fin : How much energy was used from the storage !! NOT WORKING PROPERLY !!
# Q_missing_fin : How much energy is missing
