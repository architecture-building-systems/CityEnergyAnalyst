# -*- coding: utf-8 -*-
"""
Storage Design And Operation
    This File is called by "Storage_Optimizer_incl_Losses_main.py" (Optimization Routine) and
    will operate the storage according to the inputs given by the main file.

    The operation data is stored

"""

from __future__ import division
import pandas as pd
import os
import numpy as np
import Import_Network_Data_functions as fn
import SolarPowerHandler_incl_Losses as SPH_fn
from cea.optimization.constants import *
from cea.technologies.constants import DT_HEAT
from cea.resources.geothermal import calc_ground_temperature
from cea.utilities import epwreader
from cea.constants import HOURS_IN_YEAR

def Storage_Design(CSV_NAME, SOLCOL_TYPE, T_storage_old_K, Q_in_storage_old_W, locator,
                   STORAGE_SIZE_m3, STORE_DATA, master_to_slave_vars, P_HP_max_W, config):
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
    :type gV:
    :return:
    :rtype:
    """


    # Get network summary
    Network_Data, \
    Q_DH_networkload_W, Q_wasteheatServer_kWh, \
    T_DH_return_array_K, T_DH_supply_array_K, \
    mdot_heat_netw_total_kgpers = read_data_from_Network_summary(CSV_NAME, locator)

    # Get installation and production data of all types of solar technologies
    PVT_kWh, \
    Q_PVT_gen_Wh, Q_SC_ET_gen_Wh, Q_SC_FP_gen_Wh, Q_SCandPVT_gen_Wh, \
    Solar_E_aux_Wh, \
    Solar_Tscr_th_PVT_K, \
    Solar_Tscr_th_SC_ET_K, \
    Solar_Tscr_th_SC_FP_K = read_solar_technologies_data(locator, master_to_slave_vars)
    E_PVT_Wh = PVT_kWh * 1000 * master_to_slave_vars.SOLAR_PART_PVT
    # Get ground temperatures
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C','relhum_percent',
                                                              'windspd_ms', 'skytemp_C']]
    T_ground_K = calc_ground_temperature(locator, config, weather_data['drybulb_C'], depth_m=10)

    # Calculate total solar thermal production
    for hour in range(len(Q_SCandPVT_gen_Wh)):
        Q_SCandPVT_gen_Wh[hour] = Q_SC_ET_gen_Wh[hour] + Q_SC_FP_gen_Wh[hour] + Q_PVT_gen_Wh[hour]

    # Calculate DH operation with on-site energy sources and storage
    HOUR = 0
    Q_to_storage_avail_W = np.zeros(HOURS_IN_YEAR)
    Q_from_storage_W = np.zeros(HOURS_IN_YEAR)
    to_storage = np.zeros(HOURS_IN_YEAR)
    Q_storage_content_final_W = np.zeros(HOURS_IN_YEAR)
    Q_server_to_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_server_to_storage_W = np.zeros(HOURS_IN_YEAR)
    Q_compair_to_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_compair_to_storage_W = np.zeros(HOURS_IN_YEAR)
    Q_PVT_to_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_PVT_to_storage_W = np.zeros(HOURS_IN_YEAR)
    Q_SC_ET_to_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_SC_ET_to_storage_W = np.zeros(HOURS_IN_YEAR)
    Q_SC_FP_to_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_SC_FP_to_storage_W = np.zeros(HOURS_IN_YEAR)
    T_storage_final_K = np.zeros(HOURS_IN_YEAR)
    Q_from_storage_final_W = np.zeros(HOURS_IN_YEAR)
    Q_to_storage_final_W = np.zeros(HOURS_IN_YEAR)
    E_aux_ch_final_W = np.zeros(HOURS_IN_YEAR)
    E_aux_dech_final_W = np.zeros(HOURS_IN_YEAR)
    E_aux_solar_W = np.zeros(HOURS_IN_YEAR)
    Q_missing_final_W = np.zeros(HOURS_IN_YEAR)
    Q_from_storage_used_final_W = np.zeros(HOURS_IN_YEAR)
    Q_rejected_final_W = np.zeros(HOURS_IN_YEAR)
    mdot_DH_final_kgpers = np.zeros(HOURS_IN_YEAR)
    Q_uncontrollable_final_W = np.zeros(HOURS_IN_YEAR)
    E_aux_solar_and_heat_recovery_Wh = np.zeros(HOURS_IN_YEAR)
    HPServerHeatDesignArray_kWh = np.zeros(HOURS_IN_YEAR)
    HPpvt_designArray_Wh = np.zeros(HOURS_IN_YEAR)
    HPCompAirDesignArray_kWh = np.zeros(HOURS_IN_YEAR)
    HPScDesignArray_Wh = np.zeros(HOURS_IN_YEAR)

    T_amb_K = 10 + 273.15 # K # FIXME: CONSTANT
    T_storage_min_K = master_to_slave_vars.T_ST_MAX
    Q_disc_seasonstart_W = [0]
    Q_loss_tot_W = 0

    while HOUR < HOURS_IN_YEAR:
        # Get network temperatures and capacity flow rates
        T_DH_sup_K = T_DH_supply_array_K[HOUR]
        T_DH_return_K = T_DH_return_array_K[HOUR]
        mdot_DH_kgpers = mdot_heat_netw_total_kgpers[HOUR]

        # Get heating proved by on-site energy sources
        E_aux_HP_for_temperature_boosting_Wh, \
        Q_PVT_gen_W, \
        Q_SC_ET_gen_W, \
        Q_SC_FP_gen_W, \
        Q_compair_gen_W, \
        Q_server_gen_W = get_heating_provided_by_onsite_energy_sources(
            HOUR, HPCompAirDesignArray_kWh, HPScDesignArray_Wh,
            HPServerHeatDesignArray_kWh, HPpvt_designArray_Wh, Q_PVT_gen_Wh,
            Q_SC_ET_gen_Wh, Q_SC_FP_gen_Wh, Q_wasteheatServer_kWh, Solar_Tscr_th_PVT_K, Solar_Tscr_th_SC_ET_K,
            Solar_Tscr_th_SC_FP_K, T_DH_sup_K, master_to_slave_vars)

        # Get heating demand in DH
        Q_network_demand_W = Q_DH_networkload_W[HOUR]

        # Calculate storage operation
        Storage_Data = SPH_fn.Storage_Operator(Q_PVT_gen_W, Q_SC_ET_gen_W, Q_SC_FP_gen_W, Q_server_gen_W, Q_compair_gen_W, \
                                               Q_network_demand_W, T_storage_old_K, T_DH_sup_K, T_amb_K, \
                                               Q_in_storage_old_W, T_DH_return_K, mdot_DH_kgpers, STORAGE_SIZE_m3,
                                               master_to_slave_vars, P_HP_max_W, T_ground_K[HOUR])

        Q_in_storage_new_W = Storage_Data[0]
        T_storage_new_K = Storage_Data[1]
        Q_to_storage_fin_W = Storage_Data[3]
        Q_from_storage_req_final_W = Storage_Data[2]
        E_aux_ch_W = Storage_Data[4]
        E_aux_dech_W = Storage_Data[5]
        Q_missing_W = Storage_Data[6] # amount of heat required from heating plants
        Q_from_storage_used_final_W[HOUR] = Storage_Data[7]
        Q_loss_tot_W += Storage_Data[8]
        mdot_DH_afterSto_kgpers = Storage_Data[9] # amount of heat required from heating plants
        Q_server_to_directload_W[HOUR] = Storage_Data[10]
        Q_server_to_storage_W[HOUR] = Storage_Data[11]
        Q_compair_to_directload_W[HOUR] = Storage_Data[12]
        Q_compair_to_storage_W[HOUR] = Storage_Data[13]
        Q_PVT_to_directload_W[HOUR] = Storage_Data[14]
        Q_PVT_to_storage_W[HOUR] = Storage_Data[15]
        Q_SC_ET_to_directload_W[HOUR] = Storage_Data[16]
        Q_SC_ET_to_storage_W[HOUR] = Storage_Data[17]
        Q_SC_FP_to_directload_W[HOUR] = Storage_Data[18]
        Q_SC_FP_to_storage_W[HOUR] = Storage_Data[19]

        ## Modify storage level according to temeprature
        if Q_in_storage_new_W < 0.0001:
            Q_in_storage_new_W = 0
        # if storage temperature too high, no more charging possible - reject energy
        if T_storage_new_K >= master_to_slave_vars.T_ST_MAX-0.001:
            Q_in_storage_new_W = min(Q_in_storage_old_W, Storage_Data[0])
            Q_to_storage_fin_W = max(Q_in_storage_new_W - Q_in_storage_old_W, 0)
            Q_rejected_final_W[HOUR] = Q_PVT_gen_W + Q_SC_ET_gen_W + Q_SC_FP_gen_W + Q_compair_gen_W + Q_server_gen_W \
                                       - Q_to_storage_fin_W
            T_storage_new_K = min(T_storage_old_K, T_storage_new_K)
            E_aux_ch_W = 0

        ## Overwrite values for the calculation in the next timestep
        Q_in_storage_old_W = Q_in_storage_new_W
        T_storage_old_K = T_storage_new_K

        # catch an error if the storage temperature is too low
        if T_storage_old_K < T_amb_K - 1:
            print "Storage temperature is too lower than ambient, please check the calculation"
            break

        ## Save values for the current timestep
        Q_storage_content_final_W[HOUR] = Q_in_storage_new_W
        T_storage_final_K[HOUR] = T_storage_new_K
        Q_from_storage_final_W[HOUR] = Q_from_storage_req_final_W
        Q_to_storage_final_W[HOUR] = Q_to_storage_fin_W
        E_aux_ch_final_W[HOUR] = E_aux_ch_W
        E_aux_dech_final_W[HOUR] = E_aux_dech_W
        E_aux_solar_W[HOUR] = Solar_E_aux_Wh[HOUR]

        # heating demand satisfied directly from these technologies
        Q_uncontrollable_final_W[HOUR] = Q_PVT_to_directload_W[HOUR] + Q_SC_ET_to_directload_W[HOUR] + \
                                          Q_SC_FP_to_directload_W[HOUR] + Q_compair_to_directload_W[HOUR] + \
                                          Q_server_to_directload_W[HOUR]

        # heating demand required from heating plant
        Q_missing_final_W[HOUR] = Q_network_demand_W - Q_uncontrollable_final_W[HOUR] - Q_from_storage_used_final_W[HOUR]
        # auxiliary electricity to operate booster heat pumps
        E_aux_solar_and_heat_recovery_Wh[HOUR] = float(E_aux_HP_for_temperature_boosting_Wh)
        # amount of heat required from heating plants
        mdot_DH_final_kgpers[HOUR] = mdot_DH_afterSto_kgpers

        if T_storage_new_K <= T_storage_min_K:
            T_storage_min_K = T_storage_new_K
            Q_disc_seasonstart_W[0] += Q_from_storage_req_final_W

        HOUR += 1


    # Calculate imported and exported Electricity Arrays:
    E_consumed_for_storage_solar_and_heat_recovery_W = np.zeros(HOURS_IN_YEAR)
    for hour in range(HOURS_IN_YEAR):
        E_consumed_for_storage_solar_and_heat_recovery_W[hour] = E_aux_ch_final_W[hour] + E_aux_dech_final_W[hour] + \
                                                                 E_aux_solar_and_heat_recovery_Wh[hour]
    storage_dispatch = {
         "Q_storage_content_W":Q_storage_content_final_W,
         "Q_DH_networkload_W":Q_DH_networkload_W,
         "Q_uncontrollable_hot_W":Q_uncontrollable_final_W,
         "Q_to_storage_W":Q_to_storage_final_W,
         "Q_from_storage_used_W":Q_from_storage_used_final_W,
         "Q_server_to_directload_W":Q_server_to_directload_W,
         "Q_server_to_storage_W":Q_server_to_storage_W,
         "Q_compair_to_directload_W":Q_compair_to_directload_W,
         "Q_compair_to_storage_W":Q_compair_to_storage_W,
         "Q_PVT_to_directload_W":Q_PVT_to_directload_W,
         "Q_PVT_to_storage_W": Q_PVT_to_storage_W,
         "Q_SC_ET_to_directload_W":Q_SC_ET_to_directload_W,
         "Q_SC_ET_to_storage_W":Q_SC_ET_to_storage_W,
         "Q_SC_FP_to_directload_W": Q_SC_FP_to_directload_W,
         "Q_SC_FP_to_storage_W": Q_SC_FP_to_storage_W,
         "E_PVT_gen_W": E_PVT_Wh,
         "E_used_Storage_charging_W":E_aux_ch_final_W,
         "E_used_Storage_discharging_W":E_aux_dech_final_W,
         "Q_missing_W":Q_missing_final_W,
         "mdot_DH_fin_kgpers":mdot_DH_final_kgpers,
         "E_aux_solar_and_heat_recovery_W": E_aux_solar_and_heat_recovery_Wh,
         "E_consumed_for_storage_solar_and_heat_recovery_W": E_consumed_for_storage_solar_and_heat_recovery_W,
         "Storage_Size_m3":STORAGE_SIZE_m3,
         "Q_SC_ET_gen_Wh":Q_SC_ET_gen_Wh,
         "Q_SC_FP_gen_Wh": Q_SC_FP_gen_Wh,
         "Q_PVT_gen_Wh": Q_PVT_gen_Wh,
         "HPServerHeatDesignArray_kWh":HPServerHeatDesignArray_kWh,
         "HPpvt_designArray_Wh":HPpvt_designArray_Wh,
         "HPCompAirDesignArray_kWh":HPCompAirDesignArray_kWh,
         "HPScDesignArray_Wh":HPScDesignArray_Wh,
         "Q_rejected_fin_W":Q_rejected_final_W,
         "P_HPCharge_max_W":P_HP_max_W
        }

    Q_stored_max_W = np.amax(Q_storage_content_final_W)
    T_st_max_K = np.amax(T_storage_final_K)
    T_st_min_K = np.amin(T_storage_final_K)

    return (Q_stored_max_W, Q_rejected_final_W, Q_disc_seasonstart_W, T_st_max_K, T_st_min_K, Q_storage_content_final_W, \
           T_storage_final_K, Q_loss_tot_W, mdot_DH_final_kgpers, Q_uncontrollable_final_W), storage_dispatch


def get_heating_provided_by_onsite_energy_sources(HOUR, HPCompAirDesignArray_kWh, HPScDesignArray_Wh,
                                                  HPServerHeatDesignArray_kWh, HPpvt_designArray_Wh,
                                                  Q_PVT_gen_Wh, Q_SC_ET_gen_Wh, Q_SC_FP_gen_Wh, Q_wasteheatServer_kWh,
                                                  Solar_Tscr_th_PVT_K, Solar_Tscr_th_SC_ET_K, Solar_Tscr_th_SC_FP_K,
                                                  T_DH_sup_K, master_to_slave_vars):
    # Store later on this data
    HPServerHeatDesign_kWh = 0
    HPpvt_design_Wh = 0
    HPCompAirDesign_kWh = 0
    HPScDesign_Wh = 0
    # Get heat production from server waste heat, SC_ET, SC_FP, PVT
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        Q_server_gen_kW = Q_wasteheatServer_kWh[HOUR]
    else:
        Q_server_gen_kW = 0
    # if MS_Var.WasteCompressorHeatRecovery == 1:
    #     Q_compair_gen_kW= Q_wasteheatCompAir_kWh[HOUR]
    # else:
    #     Q_compair_gen_kW = 0
    Q_SC_ET_gen_W = Q_SC_ET_gen_Wh[HOUR]
    Q_SC_FP_gen_W = Q_SC_FP_gen_Wh[HOUR]
    Q_PVT_gen_W = Q_PVT_gen_Wh[HOUR]
    # Check if each source needs a heat-pump, calculate the final energy required
    # server
    if T_DH_sup_K > T_EL_TO_HEAT_SUP - DT_HEAT:  # and checkpoint_ElToHeat == 1:
        # use a heat pump to bring it to distribution temp
        COP_th = T_DH_sup_K / (T_DH_sup_K - (T_EL_TO_HEAT_SUP - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_aux_Server_kWh = Q_server_gen_kW * (1 / COP)  # assuming the losses occur after the heat pump
        if E_aux_Server_kWh > 0:
            HPServerHeatDesign_kWh = Q_server_gen_kW
            Q_server_gen_kW += E_aux_Server_kWh  # heat output from the condenser = el + Qevap
    else:
        E_aux_Server_kWh = 0.0
    # FIXME: this part below might be redundant
    # if T_DH_sup_K > T_FROM_SERVER - DT_HEAT:# and checkpoint_QfromServer == 1:
    #     #use a heat pump to bring it to distribution temp
    #     COP_th = T_DH_sup_K / (T_DH_sup_K - (T_FROM_SERVER - DT_HEAT))
    #     COP = HP_ETA_EX * COP_th
    #     E_aux_CAH_kWh = Q_compair_gen_kW * (1/COP) # assuming the losses occur after the heat pump
    #     if E_aux_Server_kWh > 0:
    #         HPCompAirDesign_kWh = Q_compair_gen_kW
    #         Q_compair_gen_kW += E_aux_CAH_kWh
    # else:
    #     E_aux_CAH_kWh = 0.0
    # eliminating compressed air of the code
    E_aux_CAH_kWh = 0
    Q_compair_gen_kW = 0
    # PVT
    if T_DH_sup_K > Solar_Tscr_th_PVT_K[HOUR] - DT_HEAT:  # and checkpoint_PVT == 1:
        COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_PVT_K[HOUR] - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_aux_PVT_Wh = Q_PVT_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
        if E_aux_PVT_Wh > 0:
            HPpvt_design_Wh = Q_PVT_gen_W
            Q_PVT_gen_W += E_aux_PVT_Wh
    else:
        E_aux_PVT_Wh = 0.0
    # SC_ET
    if T_DH_sup_K > Solar_Tscr_th_SC_ET_K[HOUR] - DT_HEAT:  # and checkpoint_SC == 1:
        COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_SC_ET_K[HOUR] - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_aux_SC_ET_Wh = Q_SC_ET_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
        if E_aux_SC_ET_Wh > 0:
            HPScDesign_Wh = Q_SC_ET_gen_W
            Q_SC_ET_gen_W += E_aux_SC_ET_Wh
    else:
        E_aux_SC_ET_Wh = 0.0
    # SC_FP
    if T_DH_sup_K > Solar_Tscr_th_SC_FP_K[HOUR] - DT_HEAT:  # and checkpoint_SC == 1:
        COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_SC_FP_K[HOUR] - DT_HEAT))
        COP = HP_ETA_EX * COP_th
        E_aux_SC_FP_Wh = Q_SC_FP_gen_W * (1 / COP)  # assuming the losses occur after the heat pump
        if E_aux_SC_FP_Wh > 0:
            HPScDesign_Wh = Q_SC_FP_gen_W
            Q_SC_FP_gen_W += E_aux_SC_FP_Wh
    else:
        E_aux_SC_FP_Wh = 0.0
    HPServerHeatDesignArray_kWh[HOUR] = HPServerHeatDesign_kWh
    HPpvt_designArray_Wh[HOUR] = HPpvt_design_Wh
    HPCompAirDesignArray_kWh[HOUR] = HPCompAirDesign_kWh
    HPScDesignArray_Wh[HOUR] = HPScDesign_Wh
    E_aux_HP_for_temperature_boosting_Wh = float(
        E_aux_SC_FP_Wh + E_aux_SC_ET_Wh + E_aux_PVT_Wh + E_aux_CAH_kWh + E_aux_Server_kWh)
    # Heat Recovery has some losses, these are taken into account as "overall Losses", i.e.: from Source to DH Pipe
    # GET VALUES
    Q_server_gen_W = Q_server_gen_kW * ETA_SERVER_TO_HEAT * 1000  # converting to W
    Q_compair_gen_W = Q_compair_gen_kW * ETA_EL_TO_HEAT * 1000
    return E_aux_HP_for_temperature_boosting_Wh, Q_PVT_gen_W, Q_SC_ET_gen_W, Q_SC_FP_gen_W, Q_compair_gen_W, Q_server_gen_W


def read_solar_technologies_data(locator, master_to_slave_vars):
    # Initialize solar data
    Solar_Data_SC = np.zeros((HOURS_IN_YEAR, 7))
    Solar_Data_PVT = np.zeros((HOURS_IN_YEAR, 7))
    Solar_Data_PV = np.zeros((HOURS_IN_YEAR, 7))
    Solar_Tscr_th_SC_K = Solar_Data_SC[:, 6]
    Solar_E_aux_SC_req_kWh = Solar_Data_SC[:, 1]
    Solar_Q_th_SC_kWh = Solar_Data_SC[:, 1]
    Solar_Tscr_th_PVT_K = Solar_Data_PVT[:, 6]
    Solar_E_aux_PVT_kWh = Solar_Data_PVT[:, 1]
    Solar_Q_th_SC_kWh = Solar_Data_PVT[:, 2]
    PVT_kWh = Solar_Data_PVT[:, 5]
    Solar_E_aux_PV_kWh = Solar_Data_PV[:, 1]
    # Import Solar Data
    os.chdir(locator.get_potentials_solar_folder())
    fNameArray = [master_to_slave_vars.SOLCOL_TYPE_PVT, master_to_slave_vars.SOLCOL_TYPE_SC_ET,
                  master_to_slave_vars.SOLCOL_TYPE_SC_FP, master_to_slave_vars.SOLCOL_TYPE_PV]
    for solartype in range(len(fNameArray)):
        fName = fNameArray[solartype]
        # SC_ET
        if master_to_slave_vars.SOLCOL_TYPE_SC_ET != "NONE" and fName == master_to_slave_vars.SOLCOL_TYPE_SC_ET:
            Solar_Area_SC_ET_m2, Solar_E_aux_SC_ET_req_kWh, Solar_Q_th_SC_ET_kWh, Solar_Tscs_th_SC_ET, \
            Solar_mcp_SC_ET_kWperC, SC_ET_kWh, Solar_Tscr_th_SC_ET_K \
                = fn.import_solar_thermal_data(master_to_slave_vars.SOLCOL_TYPE_SC_ET)
        # SC_FP
        if master_to_slave_vars.SOLCOL_TYPE_SC_FP != "NONE" and fName == master_to_slave_vars.SOLCOL_TYPE_SC_FP:
            Solar_Area_SC_FP_m2, Solar_E_aux_SC_FP_req_kWh, Solar_Q_th_SC_FP_kWh, Solar_Tscs_th_SC_FP, \
            Solar_mcp_SC_FP_kWperC, SC_FP_kWh, Solar_Tscr_th_SC_FP_K \
                = fn.import_solar_thermal_data(master_to_slave_vars.SOLCOL_TYPE_SC_FP)
        # PVT
        if master_to_slave_vars.SOLCOL_TYPE_PVT != "NONE" and fName == master_to_slave_vars.SOLCOL_TYPE_PVT:
            Solar_Area_PVT_m2, Solar_E_aux_PVT_kWh, Solar_Q_th_PVT_kWh, Solar_Tscs_th_PVT, \
            Solar_mcp_PVT_kWperC, PVT_kWh, Solar_Tscr_th_PVT_K \
                = fn.import_solar_thermal_data(master_to_slave_vars.SOLCOL_TYPE_PVT)

    # Recover Solar Data
    Solar_E_aux_Wh = np.ravel(Solar_E_aux_SC_ET_req_kWh * 1000 * master_to_slave_vars.SOLAR_PART_SC_ET) + \
                     np.ravel(Solar_E_aux_SC_FP_req_kWh * 1000 * master_to_slave_vars.SOLAR_PART_SC_FP) + \
                     np.ravel(Solar_E_aux_PVT_kWh * 1000 * master_to_slave_vars.SOLAR_PART_PVT) + \
                     np.ravel(Solar_E_aux_PV_kWh * 1000 * master_to_slave_vars.SOLAR_PART_PV)
    Q_SC_ET_gen_Wh = Solar_Q_th_SC_ET_kWh * 1000 * master_to_slave_vars.SOLAR_PART_SC_ET
    Q_SC_FP_gen_Wh = Solar_Q_th_SC_FP_kWh * 1000 * master_to_slave_vars.SOLAR_PART_SC_FP
    Q_PVT_gen_Wh = Solar_Q_th_PVT_kWh * 1000 * master_to_slave_vars.SOLAR_PART_PVT
    Q_SCandPVT_gen_Wh = np.zeros(HOURS_IN_YEAR)

    return PVT_kWh, Q_PVT_gen_Wh, Q_SC_ET_gen_Wh, Q_SC_FP_gen_Wh, Q_SCandPVT_gen_Wh, \
           Solar_E_aux_Wh, Solar_Tscr_th_PVT_K, Solar_Tscr_th_SC_ET_K, Solar_Tscr_th_SC_FP_K


def read_data_from_Network_summary(CSV_NAME, locator):
    # Import Network Data
    Network_Data = pd.read_csv(locator.get_thermal_network_data_folder(CSV_NAME))
    # recover Network Data:
    mdot_heat_netw_total_kgpers = Network_Data['mdot_DH_netw_total_kgpers'].values
    Q_DH_networkload_W = Network_Data['Q_DHNf_W'].values
    T_DH_return_array_K = Network_Data['T_DHNf_re_K'].values
    T_DH_supply_array_K = Network_Data['T_DHNf_sup_K'].values
    Q_wasteheatServer_kWh = Network_Data['Qcdata_netw_total_kWh'].values
    return Network_Data, Q_DH_networkload_W, Q_wasteheatServer_kWh, T_DH_return_array_K, T_DH_supply_array_K, mdot_heat_netw_total_kgpers


""" DESCRIPTION FOR FUTHER USAGE"""
# Q_missing_fin  : has to be replaced by other means, like a HP
# Q_from_storage_fin : What is used from Storage
# Q_aus_fin : how much energy was spent on Auxillary power !! NOT WORKING PROPERLY !!
# Q_from_storage_fin : How much energy was used from the storage !! NOT WORKING PROPERLY !!
# Q_missing_fin : How much energy is missing

