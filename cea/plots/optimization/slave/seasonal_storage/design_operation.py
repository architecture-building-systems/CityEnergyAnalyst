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

def Storage_Design(CSV_NAME, SOLCOL_TYPE, T_storage_old_K, Q_in_storage_old_W, locator,
                   STORAGE_SIZE_m3, STORE_DATA, context, P_HP_max_W, gV):
    """

    :param CSV_NAME:
    :param SOLCOL_TYPE:
    :param T_storage_old_K:
    :param Q_in_storage_old_W:
    :param locator:
    :param STORAGE_SIZE_m3:
    :param STORE_DATA:
    :param context:
    :param P_HP_max_W:
    :param gV:
    :type CSV_NAME:
    :type SOLCOL_TYPE:
    :type T_storage_old_K:
    :type Q_in_storage_old_W:
    :type locator:
    :type STORAGE_SIZE_m3:
    :type STORE_DATA:
    :type context:
    :type P_HP_max_W:
    :type gV:
    :return:
    :rtype:
    """

    MS_Var = context

    # Import Network Data
    Network_Data = pd.read_csv(locator.get_optimization_network_data_folder(CSV_NAME))

    # recover Network  Data:
    mdot_heat_netw_total_kgpers = Network_Data['mdot_DH_netw_total_kgpers'].values
    Q_DH_networkload_W = Network_Data['Q_DHNf_W'].values
    T_DH_return_array_K =  Network_Data['T_DHNf_re_K'].values
    T_DH_supply_array_K = Network_Data['T_DHNf_sup_K'].values
    Q_wasteheatServer_kWh =  Network_Data['Qcdata_netw_total_kWh'].values
    Q_wasteheatCompAir_kWh = Network_Data['Ecaf_netw_total_kWh'].values
    
    Solar_Data_SC = np.zeros((8760, 7))
    Solar_Data_PVT = np.zeros((8760, 7))
    Solar_Data_PV = np.zeros((8760, 7))
    
    Solar_Tscr_th_SC_K = Solar_Data_SC[:,6]
    Solar_E_aux_SC_req_kWh = Solar_Data_SC[:,1]
    Solar_Q_th_SC_kWh = Solar_Data_SC[:,1]
    
    Solar_Tscr_th_PVT_K = Solar_Data_PVT[:,6]
    Solar_E_aux_PVT_kW = Solar_Data_PVT[:,1]
    Solar_Q_th_SC_kWh = Solar_Data_PVT[:,2]
    PVT_kWh = Solar_Data_PVT[:,5]
    Solar_E_aux_PV_kWh = Solar_Data_PV[:,1]
    PV_kWh = Solar_Data_PV[:,5]
    
    # Import Solar Data
    os.chdir(locator.get_potentials_solar_folder())
    
    fNameArray = [MS_Var.SOLCOL_TYPE_PVT, MS_Var.SOLCOL_TYPE_SC, MS_Var.SOLCOL_TYPE_PV]
    
        #LOOP AROUND ALL SC TYPES
    for solartype in range(3):
        fName = fNameArray[solartype]
    
        if MS_Var.SOLCOL_TYPE_SC != "NONE" and fName == MS_Var.SOLCOL_TYPE_SC:
            Solar_Area_SC_m2, Solar_E_aux_SC_req_kWh, Solar_Q_th_SC_kWh, Solar_Tscs_th_SC, Solar_mcp_SC_kWperC, SC_kWh, Solar_Tscr_th_SC_K\
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_SC)
        
        if MS_Var.SOLCOL_TYPE_PVT != "NONE" and fName == MS_Var.SOLCOL_TYPE_PVT:
            Solar_Area_PVT_m2, Solar_E_aux_PVT_kW, Solar_Q_th_PVT_kW, Solar_Tscs_th_PVT, Solar_mcp_PVT_kWperC, PVT_kWh, Solar_Tscr_th_PVT_K \
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_PVT)

        if MS_Var.SOLCOL_TYPE_PV != "NONE" and fName == MS_Var.SOLCOL_TYPE_PV:
            Solar_Area_PV_m2, Solar_E_aux_PV_kWh, Solar_Q_th_PV_kW, Solar_Tscs_th_PV, Solar_mcp_PV_kWperC, PV_kWh, Solar_Tscr_th_PV_K\
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_PV)

    
    # Recover Solar Data
    Solar_E_aux_W = np.ravel(Solar_E_aux_SC_req_kWh * 1000 * MS_Var.SOLAR_PART_SC) + np.ravel(Solar_E_aux_PVT_kW * 1000 * MS_Var.SOLAR_PART_PVT) \
                            + np.ravel(Solar_E_aux_PV_kWh * 1000 * MS_Var.SOLAR_PART_PV)

    
    Q_SC_gen_Wh = Solar_Q_th_SC_kWh * 1000 * MS_Var.SOLAR_PART_SC
    Q_PVT_gen_Wh = Solar_Q_th_PVT_kW * 1000 * MS_Var.SOLAR_PART_PVT
    Q_SCandPVT_gen_Wh = np.zeros(8760)

    for hour in range(len(Q_SCandPVT_gen_Wh)):
        Q_SCandPVT_gen_Wh[hour] = Q_SC_gen_Wh[hour] + Q_PVT_gen_Wh[hour]

    
    E_PV_Wh = PV_kWh * 1000 * MS_Var.SOLAR_PART_PV
    E_PVT_Wh = PVT_kWh * 1000  * MS_Var.SOLAR_PART_PVT

    HOUR = 0
    Q_to_storage_avail_W = np.zeros(8760)
    Q_from_storage_W = np.zeros(8760)
    to_storage = np.zeros(8760)
    Q_storage_content_fin_W = np.zeros(8760)
    Q_server_to_directload_W = np.zeros(8760)
    Q_server_to_storage_W = np.zeros(8760)
    Q_compair_to_directload_W = np.zeros(8760)
    Q_compair_to_storage_W = np.zeros(8760)
    Q_PVT_to_directload_W = np.zeros(8760)
    Q_PVT_to_storage_W = np.zeros(8760)
    Q_SC_to_directload_W = np.zeros(8760)
    Q_SC_to_storage_W = np.zeros(8760)
    T_storage_fin_K = np.zeros(8760)
    Q_from_storage_fin_W = np.zeros(8760)
    Q_to_storage_fin_W = np.zeros(8760)
    E_aux_ch_fin_W = np.zeros(8760)
    E_aux_dech_fin_W = np.zeros(8760)
    #E_PV_Wh_fin = np.zeros(8760)
    E_aux_solar_W = np.zeros(8760)
    Q_missing_fin_W = np.zeros(8760)
    Q_from_storage_used_fin_W = np.zeros(8760)
    Q_rejected_fin_W = np.zeros(8760)
    mdot_DH_fin_kgpers = np.zeros(8760)
    Q_uncontrollable_fin_Wh = np.zeros(8760)
    E_aux_solar_and_heat_recovery_Wh = np.zeros(8760)
    HPServerHeatDesignArray_kWh = np.zeros(8760)
    HPpvt_designArray_Wh = np.zeros(8760)
    HPCompAirDesignArray_kWh = np.zeros(8760)
    HPScDesignArray_Wh = np.zeros(8760)
    
    T_amb_K = 10 + 273.0 # K
    T_storage_min_K = MS_Var.T_ST_MAX
    Q_disc_seasonstart_W = [0]
    Q_loss_tot_W = 0
    
    while HOUR < 8760:
        # Store later on this data
        HPServerHeatDesign_kWh = 0
        HPpvt_design_Wh = 0
        HPCompAirDesign_kWh = 0
        HPScDesign_Wh = 0
        
        T_DH_sup_K = T_DH_supply_array_K[HOUR]
        T_DH_return_K = T_DH_return_array_K[HOUR]
        mdot_DH_kgpers = mdot_heat_netw_total_kgpers[HOUR]
        if MS_Var.WasteServersHeatRecovery == 1:
            Q_server_gen_kW = Q_wasteheatServer_kWh[HOUR]
        else:
            Q_server_gen_kW = 0
        if MS_Var.WasteCompressorHeatRecovery == 1:
            Q_compair_gen_kW= Q_wasteheatCompAir_kWh[HOUR]
        else:
            Q_compair_gen_kW = 0
        Q_SC_gen_W = Q_SC_gen_Wh[HOUR]
        Q_PVT_gen_W = Q_PVT_gen_Wh[HOUR]
        
        # check if each source needs a heat-pump, calculate the final energy 
        if T_DH_sup_K > TElToHeatSup - gV.dT_heat: #and checkpoint_ElToHeat == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (TElToHeatSup - gV.dT_heat))
            COP = HP_etaex * COP_th
            E_aux_Server_kWh = Q_server_gen_kW * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_Server_kWh > 0:
                HPServerHeatDesign_kWh = Q_server_gen_kW
                Q_server_gen_kW += E_aux_Server_kWh
            
        else:
            E_aux_Server_kWh = 0.0
            
        if T_DH_sup_K > TfromServer - gV.dT_heat:# and checkpoint_QfromServer == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (TfromServer - gV.dT_heat))
            COP = HP_etaex * COP_th
            E_aux_CAH_kWh = Q_compair_gen_kW * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_Server_kWh > 0:
                HPCompAirDesign_kWh = Q_compair_gen_kW
                Q_compair_gen_kW += E_aux_CAH_kWh
        else:
            E_aux_CAH_kWh = 0.0

        if T_DH_sup_K > Solar_Tscr_th_PVT_K[HOUR] - gV.dT_heat:# and checkpoint_PVT == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_PVT_K[HOUR] - gV.dT_heat))
            COP = HP_etaex * COP_th
            E_aux_PVT_Wh = Q_PVT_gen_W * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_PVT_Wh > 0:
                HPpvt_design_Wh = Q_PVT_gen_W
                Q_PVT_gen_W += E_aux_PVT_Wh
                
        else:
            E_aux_PVT_Wh = 0.0
            
        if T_DH_sup_K > Solar_Tscr_th_SC_K[HOUR] - gV.dT_heat:# and checkpoint_SC == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_SC_K[HOUR] - gV.dT_heat))
            COP = HP_etaex * COP_th
            E_aux_SC_Wh = Q_SC_gen_W * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_SC_Wh > 0:
                HPScDesign_Wh = Q_SC_gen_W
                Q_SC_gen_W += E_aux_SC_Wh
        else:  
            E_aux_SC_Wh = 0.0
        
        
        HPServerHeatDesignArray_kWh[HOUR] = HPServerHeatDesign_kWh
        HPpvt_designArray_Wh[HOUR] = HPpvt_design_Wh
        HPCompAirDesignArray_kWh[HOUR] = HPCompAirDesign_kWh
        HPScDesignArray_Wh[HOUR] = HPScDesign_Wh
        
        
        E_aux_HP_uncontrollable_Wh = float(E_aux_SC_Wh + E_aux_PVT_Wh + E_aux_CAH_kWh + E_aux_Server_kWh)

        # Heat Recovery has some losses, these are taken into account as "overall Losses", i.e.: from Source to DH Pipe
        # hhhhhhhhhhhhhh GET VALUES
        Q_server_gen_W = Q_server_gen_kW * etaServerToHeat * 1000 # converting to W
        Q_compair_gen_W = Q_compair_gen_kW *etaElToHeat * 1000


        Q_network_demand_W = Q_DH_networkload_W[HOUR]


        Storage_Data = SPH_fn.Storage_Operator(Q_PVT_gen_W, Q_SC_gen_W, Q_server_gen_W, Q_compair_gen_W, Q_network_demand_W, T_storage_old_K, T_DH_sup_K, T_amb_K, \
                                               Q_in_storage_old_W, T_DH_return_K, mdot_DH_kgpers, STORAGE_SIZE_m3, context, P_HP_max_W, gV)
    
        Q_in_storage_new_W = Storage_Data[0]
        T_storage_new_K = Storage_Data[1]
        Q_to_storage_final_W = Storage_Data[3]
        Q_from_storage_req_final_W = Storage_Data[2]
        E_aux_ch_W = Storage_Data[4]
        E_aux_dech_W = Storage_Data[5]
        Q_missing_W = Storage_Data[6]
        Q_from_storage_used_fin_W[HOUR] = Storage_Data[7]
        Q_loss_tot_W += Storage_Data[8]
        mdot_DH_afterSto_kgpers = Storage_Data[9]
        Q_server_to_directload_W[HOUR] = Storage_Data[10]
        Q_server_to_storage_W[HOUR] = Storage_Data[11]
        Q_compair_to_directload_W[HOUR] = Storage_Data[12]
        Q_compair_to_storage_W[HOUR] = Storage_Data[13]
        Q_PVT_to_directload_W[HOUR] = Storage_Data[14]
        Q_PVT_to_storage_W[HOUR] = Storage_Data[15]
        Q_SC_to_directload_W[HOUR] = Storage_Data[16]
        Q_SC_to_storage_W[HOUR] = Storage_Data[17]
        
        if Q_in_storage_new_W < 0.0001:
            Q_in_storage_new_W = 0
    
        
        if T_storage_new_K >= MS_Var.T_ST_MAX-0.001: # no more charging possible - reject energy
            Q_in_storage_new_W = min(Q_in_storage_old_W, Storage_Data[0])
            Q_to_storage_final_W = max(Q_in_storage_new_W - Q_in_storage_old_W, 0)
            Q_rejected_fin_W[HOUR] = Q_PVT_gen_W + Q_SC_gen_W + Q_compair_gen_W + Q_server_gen_W - Storage_Data[3]
            T_storage_new_K = min(T_storage_old_K, T_storage_new_K)
            E_aux_ch_W = 0

        Q_storage_content_fin_W[HOUR] = Q_in_storage_new_W
        Q_in_storage_old_W = Q_in_storage_new_W
        
        T_storage_fin_K[HOUR] = T_storage_new_K
        T_storage_old_K = T_storage_new_K
        
        if T_storage_old_K < T_amb_K-1: # chatch an error if the storage temperature is too low
            # print "ERROR!"
            break
        
        Q_from_storage_fin_W[HOUR] = Q_from_storage_req_final_W
        Q_to_storage_fin_W[HOUR] = Q_to_storage_final_W
        E_aux_ch_fin_W[HOUR] = E_aux_ch_W
        E_aux_dech_fin_W[HOUR] = E_aux_dech_W
        E_aux_solar_W[HOUR] = Solar_E_aux_W[HOUR]
        Q_missing_fin_W[HOUR] = Q_missing_W
        Q_uncontrollable_fin_Wh[HOUR] = Q_PVT_gen_W + Q_SC_gen_W + Q_compair_gen_W + Q_server_gen_W
        E_aux_solar_and_heat_recovery_Wh[HOUR] = float(E_aux_HP_uncontrollable_Wh)
        mdot_DH_fin_kgpers[HOUR] = mdot_DH_afterSto_kgpers
        
        Q_from_storage_fin_W[HOUR] = Q_DH_networkload_W[HOUR] - Q_missing_W
        
        if T_storage_new_K <= T_storage_min_K:
            T_storage_min_K = T_storage_new_K
            Q_disc_seasonstart_W[0] += Q_from_storage_req_final_W

        HOUR += 1
        
        
        """ STORE DATA """
    E_aux_solar_and_heat_recovery_flat_Wh = E_aux_solar_and_heat_recovery_Wh.flatten()
    # Calculate imported and exported Electricity Arrays:
    E_produced_total_W = np.zeros(8760)
    E_consumed_for_storage_solar_and_heat_recovery_W = np.zeros(8760)
    
    for hour in range(8760):
        E_produced_total_W[hour] = E_PV_Wh[hour] + E_PVT_Wh[hour]
        E_consumed_for_storage_solar_and_heat_recovery_W[hour] = E_aux_ch_fin_W[hour] + E_aux_dech_fin_W[hour] + E_aux_solar_and_heat_recovery_Wh[hour]


    if STORE_DATA == "yes":
        date = Network_Data.DATE.values
        results = pd.DataFrame(
            {"DATE": date,
             "Q_storage_content_W":Q_storage_content_fin_W,
             "Q_DH_networkload_W":Q_DH_networkload_W,
             "Q_uncontrollable_hot_W":Q_uncontrollable_fin_Wh,
             "Q_to_storage_W":Q_to_storage_fin_W,
             "Q_from_storage_used_W":Q_from_storage_used_fin_W,
             "Q_server_to_directload_W":Q_server_to_directload_W,
             "Q_server_to_storage_W":Q_server_to_storage_W,
             "Q_compair_to_directload_W":Q_compair_to_directload_W,
             "Q_compair_to_storage_W":Q_compair_to_storage_W,
             "Q_PVT_to_directload_W":Q_PVT_to_directload_W,
             "Q_PVT_to_storage_W": Q_PVT_to_storage_W,
             "Q_SC_to_directload_W":Q_SC_to_directload_W,
             "Q_SC_to_storage_W":Q_SC_to_storage_W,
             "E_aux_ch_W":E_aux_ch_fin_W,
             "E_aux_dech_W":E_aux_dech_fin_W,
             "Q_missing_W":Q_missing_fin_W,
             "mdot_DH_fin_kgpers":mdot_DH_fin_kgpers,
             "E_aux_solar_and_heat_recovery_Wh": E_aux_solar_and_heat_recovery_Wh,
             "E_consumed_for_storage_solar_and_heat_recovery_W": E_consumed_for_storage_solar_and_heat_recovery_W,
             "E_PV_Wh":E_PV_Wh,
             "E_PVT_Wh":E_PVT_Wh,
             "E_produced_from_solar_W": E_produced_total_W,
             "Storage_Size_m3":STORAGE_SIZE_m3,
             "Q_SC_gen_Wh":Q_SC_gen_Wh,
             "Q_PVT_gen_Wh": Q_PVT_gen_Wh,
             "HPServerHeatDesignArray_kWh":HPServerHeatDesignArray_kWh,
             "HPpvt_designArray_Wh":HPpvt_designArray_Wh,
             "HPCompAirDesignArray_kWh":HPCompAirDesignArray_kWh,
             "HPScDesignArray_Wh":HPScDesignArray_Wh,
             "Q_rejected_fin_W":Q_rejected_fin_W,
             "P_HPCharge_max_W":P_HP_max_W
            })
        storage_operation_data_path = locator.get_optimization_slave_storage_operation_data(MS_Var.configKey)
        results.to_csv(storage_operation_data_path, index=False)

    Q_stored_max_W = np.amax(Q_storage_content_fin_W)
    T_st_max_K = np.amax(T_storage_fin_K)
    T_st_min_K = np.amin(T_storage_fin_K)
        
    return Q_stored_max_W, Q_rejected_fin_W, Q_disc_seasonstart_W, T_st_max_K, T_st_min_K, Q_storage_content_fin_W, T_storage_fin_K, \
                                    Q_loss_tot_W, mdot_DH_fin_kgpers, Q_uncontrollable_fin_Wh
    
""" DESCRIPTION FOR FUTHER USAGE"""
# Q_missing_fin  : has to be replaced by other means, like a HP
# Q_from_storage_fin : What is used from Storage
# Q_aus_fin : how much energy was spent on Auxillary power !! NOT WORKING PROPERLY !!
# Q_from_storage_fin : How much energy was used from the storage !! NOT WORKING PROPERLY !!
# Q_missing_fin : How much energy is missing

