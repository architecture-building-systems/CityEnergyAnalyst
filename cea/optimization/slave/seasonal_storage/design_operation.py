    # -*- coding: utf-8 -*-
""" 

Storage Design And Operation  
    This File is called by "Storage_Optimizer_incl_Losses_main.py" (Optimization Routine) and 
    will operate the storage according to the inputs given by the main file.
    
    The operation data is stored 
            
"""

import pandas as pd
import os
import numpy as np
import Import_Network_Data_functions as fn
import SolarPowerHandler_incl_Losses as SPH_fn


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
    os.chdir(locator.get_optimization_network_results_folder())
    MS_Var = context
    HOURS_IN_DAY = 24
    DAYS_IN_YEAR = 365

    # Import Network Data
    Network_Data = pd.read_csv(CSV_NAME)

    # recover Network  Data:
    mdot_heat_netw_total_kgpers = Network_Data['mdot_DH_netw_total_kgpers'].values
    Q_DH_networkload_W = Network_Data['Q_DHNf_W'].values
    T_DH_return_array_K = Network_Data['T_DHNf_re_K'].values
    T_DH_supply_array_K = Network_Data['T_DHNf_sup_K'].values
    Q_wasteheatServer_kWh = Network_Data['Qcdata_netw_total_kWh'].values #np.array(fn.extract_csv(fName, "Q_DH_building_netw_total", DAYS_IN_YEAR))
    Q_wasteheatCompAir_kWh = Network_Data['Ecaf_netw_total_kWh'].values
    
    Solar_Data_SC = np.zeros((HOURS_IN_DAY* DAYS_IN_YEAR, 7))
    Solar_Data_PVT = np.zeros((HOURS_IN_DAY* DAYS_IN_YEAR, 7))
    Solar_Data_PV = np.zeros((HOURS_IN_DAY* DAYS_IN_YEAR, 7))
    
    Solar_Tscr_th_SC_K = Solar_Data_SC[:,6]
    Solar_E_aux_SC_req_kWh = Solar_Data_SC[:,1]
    Solar_Q_th_SC_kWh = Solar_Data_SC[:,1]
    
    Solar_Tscr_th_PVT_K = Solar_Data_PVT[:,6]
    Solar_E_aux_PVT_kWh = Solar_Data_PVT[:,1]
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
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_SC, DAYS_IN_YEAR, HOURS_IN_DAY)
        
        if MS_Var.SOLCOL_TYPE_PVT != "NONE" and fName == MS_Var.SOLCOL_TYPE_PVT:
            Solar_Area_PVT_m2, Solar_E_aux_PVT_kWh, Solar_Q_th_PVT_kWh, Solar_Tscs_th_PVT, Solar_mcp_PVT_kWperC, PVT_kWh, Solar_Tscr_th_PVT_K \
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_PVT, DAYS_IN_YEAR, HOURS_IN_DAY)
            #Solar_Data_PVT= fn.import_solar_data(MS_Var.SOLCOL_TYPE_PVT, DAYS_IN_YEAR, HOURS_IN_DAY)
    
        if MS_Var.SOLCOL_TYPE_PV != "NONE" and fName == MS_Var.SOLCOL_TYPE_PV:
            Solar_Area_PV_m2, Solar_E_aux_PV_kWh, Solar_Q_th_PV_kWh, Solar_Tscs_th_PV, Solar_mcp_PV_kWperC, PV_kWh, Solar_Tscr_th_PV_K\
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_PV, DAYS_IN_YEAR, HOURS_IN_DAY)

    #print "\n ........---------........."
    #print "sum of PV_kWh_PVT in Storage desing op v2", np.sum(PV_kWh_PVT) 
    # ADD SOLAR COLLECTOR AND SELL ELECTRICITY!
    
    # Recover Solar Data
   # Solar_Area = Solar_Data_SC[0] * MS_Var.SOLAR_PART_SC + Solar_Data_PVT[0] * MS_Var.SOLAR_PART_PVT + Solar_Data_PV[0] * MS_Var.SOLAR_PART_PV
    Solar_E_aux_W = np.ravel(Solar_E_aux_SC_req_kWh * 1000 * MS_Var.SOLAR_PART_SC) + np.ravel(Solar_E_aux_PVT_kWh * 1000 * MS_Var.SOLAR_PART_PVT) \
                            + np.ravel(Solar_E_aux_PV_kWh * 1000 * MS_Var.SOLAR_PART_PV)
    #print "Solar_E_aux_W", np.shape(Solar_E_aux_W), Solar_E_aux_W
    #print "Solar_Data_SC", Solar_Data_SC
    
    Q_SC_gen_Wh = Solar_Q_th_SC_kWh * 1000 * MS_Var.SOLAR_PART_SC
    #print Q_SC, "Q_SC"
    Q_PVT_gen_Wh = Solar_Q_th_PVT_kWh * 1000 * MS_Var.SOLAR_PART_PVT
    Q_SCandPVT_gen_Wh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    
    #Q_SCandPVT = float(np.sum(Q_SC) + np.sum(Q_PVT))
    #Q_SCandPVT = Q_SC + Q_PVT
    for hour in range(len(Q_SCandPVT_gen_Wh)):
        Q_SCandPVT_gen_Wh[hour] = Q_SC_gen_Wh[hour] + Q_PVT_gen_Wh[hour]
        
    #print Q_SCandPVT
    #print "shape", np.shape(Q_SCandPVT)
    
    E_PV_Wh = PV_kWh * 1000 * MS_Var.SOLAR_PART_PV
    E_PVT_Wh = PVT_kWh * 1000  * MS_Var.SOLAR_PART_PVT
    #print "PV_kWh_PV", np.shape(PV_kWh_PV)
    #print "PV_kWh_PVT", np.shape(PV_kWh_PVT)
    
    
    #if MS_Var.SOLCOL_TYPE_SC == 'SC_60.csv': #or MS_Var.SOLCOL_TYPE_SC == 'SC_ET50.csv':
    #    Solar_Tscr_th_SC = 60 + 273.0 #K
    
    #else: 
    #    Solar_Tscr_th_SC = 75 + 273.0 # K
    
    #Solar_Tscr_th_PVT = 35 + 273.0 #K 
    
    
    #Solar_Tscs_th = Solar_Data_SC[3] + 273.0
    #Solar_mcp_W_C = Solar_Data_SC[4] * 1000
    
    #iterate over this loop: 
    HOUR = 0
    Q_to_storage_avail_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_from_storage_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    to_storage = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_storage_content_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    T_storage_fin_K = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_from_storage_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_to_storage_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_ch_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_dech_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    #E_PV_Wh_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_solar_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_missing_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_from_storage_used_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_rejected_fin_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    mdot_DH_fin_kgpers = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_uncontrollable_fin_Wh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_HP_uncontrollable_fin_Wh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPServerHeatDesignArray_kWh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPpvt_designArray_Wh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPCompAirDesignArray_kWh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPScDesignArray_Wh = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    
    T_amb_K = 10 + 273.0 # K
    T_storage_min_K = MS_Var.T_ST_MAX
    Q_disc_seasonstart_W = [0]
    Q_loss_tot_W = 0
    
    while HOUR < HOURS_IN_DAY*DAYS_IN_YEAR:
        # Store later on this data
        HPServerHeatDesign_kWh = 0
        HPpvt_design_Wh = 0
        HPCompAirDesign_kWh = 0
        HPScDesign_Wh = 0
        
        T_DH_sup_K = T_DH_supply_array_K[HOUR]
        T_DH_return_K = T_DH_return_array_K[HOUR]
        mdot_DH_kgpers = mdot_heat_netw_total_kgpers[HOUR]
        if MS_Var.WasteServersHeatRecovery == 1:
            QServerHeat_kWh = Q_wasteheatServer_kWh[HOUR]
        else:
            QServerHeat_kWh = 0
        #print QServerHeat, "QServerHeat"
        if MS_Var.WasteCompressorHeatRecovery == 1:
            QCompAirHeat_kWh= Q_wasteheatCompAir_kWh[HOUR]
        else:
            QCompAirHeat_kWh = 0
        #print Q_SC,"Q_SC", len(Q_SC)
        Qsc_Wh = Q_SC_gen_Wh[HOUR]
        Qpvt_Wh = Q_PVT_gen_Wh[HOUR]
        
        # check if each source needs a heat-pump, calculate the final energy 
        if T_DH_sup_K > gV.TElToHeatSup - gV.dT_heat: #and checkpoint_ElToHeat == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (gV.TElToHeatSup - gV.dT_heat))
            COP = gV.HP_etaex * COP_th
            E_aux_Server_kWh = QServerHeat_kWh * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_Server_kWh > 0:
                HPServerHeatDesign_kWh = QServerHeat_kWh
                QServerHeat_kWh += E_aux_Server_kWh
            
        else:
            E_aux_Server_kWh = 0.0
            
        if T_DH_sup_K > gV.TfromServer - gV.dT_heat:# and checkpoint_QfromServer == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (gV.TfromServer - gV.dT_heat))
            COP = gV.HP_etaex * COP_th
            E_aux_CAH_kWh = QCompAirHeat_kWh * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_Server_kWh > 0:
                HPCompAirDesign_kWh = QCompAirHeat_kWh
                QCompAirHeat_kWh += E_aux_CAH_kWh
        else:
            E_aux_CAH_kWh = 0.0

        if T_DH_sup_K > Solar_Tscr_th_PVT_K[HOUR] - gV.dT_heat:# and checkpoint_PVT == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_PVT_K[HOUR] - gV.dT_heat))
            COP = gV.HP_etaex * COP_th
            E_aux_PVT_Wh = Qpvt_Wh * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_PVT_Wh > 0:
                HPpvt_design_Wh = Qpvt_Wh
                Qpvt_Wh += E_aux_PVT_Wh
                
        else:
            E_aux_PVT_Wh = 0.0
            
        if T_DH_sup_K > Solar_Tscr_th_SC_K[HOUR] - gV.dT_heat:# and checkpoint_SC == 1:
            #use a heat pump to bring it to distribution temp
            COP_th = T_DH_sup_K / (T_DH_sup_K - (Solar_Tscr_th_SC_K[HOUR] - gV.dT_heat))
            #print Solar_Tscr_th_SC[HOUR], "Solar_Tscr_th_SC[HOUR]"
            COP = gV.HP_etaex * COP_th
            E_aux_SC_Wh = Qsc_Wh * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_SC_Wh > 0:
                HPScDesign_Wh = Qsc_Wh
                Qsc_Wh += E_aux_SC_Wh
        else:  
            E_aux_SC_Wh = 0.0
        
        
        HPServerHeatDesignArray_kWh[HOUR] = HPServerHeatDesign_kWh
        HPpvt_designArray_Wh[HOUR] = HPpvt_design_Wh
        HPCompAirDesignArray_kWh[HOUR] = HPCompAirDesign_kWh
        HPScDesignArray_Wh[HOUR] = HPScDesign_Wh
        
        
        E_aux_HP_uncontrollable_Wh = float(E_aux_SC_Wh + E_aux_PVT_Wh + E_aux_CAH_kWh * 1000 + E_aux_Server_kWh * 1000)
        
        #print E_aux_HP_uncontrollable, len(E_aux_HP_uncontrollable), type(E_aux_HP_uncontrollable)
        
        # Heat Recovery has some losses, these are taken into account as "overall Losses", i.e.: from Source to DH Pipe
        # hhhhhhhhhhhhhh GET VALUES
        Q_uncontrollable_Wh = (Qpvt_Wh + Qsc_Wh + QServerHeat_kWh * 1000 * gV.etaServerToHeat + QCompAirHeat_kWh * 1000 * gV.etaElToHeat )

        #print "Q_uncontrollable = ", Q_uncontrollable
        #print "E_aux_HP_uncontrollable = ", E_aux_HP_uncontrollable
        
        Q_network_demand_W = Q_DH_networkload_W[HOUR]
        Q_to_storage_avail_W[HOUR], Q_from_storage_W[HOUR], to_storage[HOUR] = SPH_fn.StorageGateway(Q_uncontrollable_Wh, Q_network_demand_W, P_HP_max_W, gV)
        
       
        #print HOUR, Q_to_storage_avail[HOUR], Q_from_storage[HOUR], to_storage[HOUR] 
        Storage_Data = SPH_fn.Storage_Operator(Q_uncontrollable_Wh, Q_network_demand_W, T_storage_old_K, T_DH_sup_K, T_amb_K, \
                                               Q_in_storage_old_W, T_DH_return_K, mdot_DH_kgpers, STORAGE_SIZE_m3, context, P_HP_max_W, gV)
    
        Q_in_storage_new_W = Storage_Data[0]
        #print "Q_in_storage_new in Storage desing and operation: ", Q_in_storage_new
        T_storage_new_K = Storage_Data[1]
        Q_to_storage_final_W = Storage_Data[3]
        Q_from_storage_req_final_W = Storage_Data[2]
        #print "Q_from_storage_req_final", Q_from_storage_req_final
        #print "Q_to_storage_final", Q_to_storage_final
        E_aux_ch_W = Storage_Data[4]
        E_aux_dech_W = Storage_Data[5]
        Q_missing_W = Storage_Data[6]
        Q_from_storage_used_fin_W[HOUR] = Storage_Data[7]
        Q_loss_tot_W += Storage_Data[8]
        mdot_DH_afterSto_kgpers = Storage_Data[9]
        
        if Q_in_storage_new_W < 0.0001:
            Q_in_storage_new_W = 0
    
        
        if T_storage_new_K >= MS_Var.T_ST_MAX-0.001: # no more charging possible - reject energy
            Q_in_storage_new_W = min(Q_in_storage_old_W, Storage_Data[0])
            Q_to_storage_final_W = max(Q_in_storage_new_W - Q_in_storage_old_W, 0)
            Q_rejected_fin_W[HOUR] = Q_uncontrollable_Wh - Storage_Data[3]
            T_storage_new_K = min(T_storage_old_K, T_storage_new_K)
            E_aux_ch_W = 0
            print "Storage Full!"
            

            
        Q_storage_content_fin_W[HOUR] = Q_in_storage_new_W
        Q_in_storage_old_W = Q_in_storage_new_W
        
        T_storage_fin_K[HOUR] = T_storage_new_K
        T_storage_old_K = T_storage_new_K
        
        if T_storage_old_K < T_amb_K-1: # chatch an error if the storage temperature is too low
            print "ERROR!"
            break
        
        Q_from_storage_fin_W[HOUR] = Q_from_storage_req_final_W
        Q_to_storage_fin_W[HOUR] = Q_to_storage_final_W
        E_aux_ch_fin_W[HOUR] = E_aux_ch_W
        E_aux_dech_fin_W[HOUR] = E_aux_dech_W
        E_aux_solar_W[HOUR] = Solar_E_aux_W[HOUR]
        Q_missing_fin_W[HOUR] = Q_missing_W
        Q_uncontrollable_fin_Wh[HOUR] = Q_uncontrollable_Wh
        
        
        E_aux_HP_uncontrollable_fin_Wh[HOUR] = float(E_aux_HP_uncontrollable_Wh)
        #print type(E_aux_HP_uncontrollable_fin[HOUR]),
        mdot_DH_fin_kgpers[HOUR] = mdot_DH_afterSto_kgpers
        
        Q_from_storage_fin_W[HOUR] = Q_DH_networkload_W[HOUR] - Q_missing_W
        
        if T_storage_new_K <= T_storage_min_K:
            T_storage_min_K = T_storage_new_K
            Q_disc_seasonstart_W[0] += Q_from_storage_req_final_W
            
        
        HOUR += 1
        
        
        """ STORE DATA """
    E_aux_HP_uncontrollable_fin_flat_Wh = E_aux_HP_uncontrollable_fin_Wh.flatten()
    #print len(E_aux_HP_uncontrollable_fin_flat), np.shape(E_aux_HP_uncontrollable_fin_flat)
    #print "Q_storage_content_fin", np.shape(Q_storage_content_fin)
    #print "Q_DH_networkload[:,0]", np.shape(Q_DH_networkload[:,0])
    #print "Q_to_storage_fin", np.shape(Q_to_storage_fin)
    #print "Q_from_storage_used_fin", np.shape(Q_from_storage_used_fin)
    #print "E_aux_ch_fin", np.shape(E_aux_ch_fin)
    #print "E_aux_dech_fin", np.shape(E_aux_dech_fin)
    #print "Q_missing_fin", np.shape(Q_missing_fin)
    #print "mdot_DH_fin", np.shape(mdot_DH_fin)
    #print "E_PV_Wh", np.shape(E_PV_Wh)
    
    #print np.shape(E_aux_HP_uncontrollable_fin_flat[:,0])
    #print "sum of uncontrollable auxPower: " , np.sum(E_aux_HP_uncontrollable_fin)
    #print "sum of uncontrollable power: ", np.sum(Q_uncontrollable) 
    
    
    # Calculate imported and exported Electricity Arrays:
    E_produced_total_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_consumed_total_without_buildingdemand_W = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    
    for hour in range(DAYS_IN_YEAR, HOURS_IN_DAY):
        E_produced_total_W[hour] = E_PV_Wh[hour] + E_PVT_Wh[hour]
        E_consumed_total_without_buildingdemand_W[hour] = E_aux_ch_W[hour] + E_aux_dech_W[hour] + E_aux_HP_uncontrollable_Wh[hour]


    if STORE_DATA == "yes":
        
        results = pd.DataFrame(
            {"Q_storage_content_W":Q_storage_content_fin_W,
             "Q_DH_networkload_W":Q_DH_networkload_W,
             "Q_uncontrollable_hot_W":Q_uncontrollable_fin_Wh,
             "Q_to_storage_W":Q_to_storage_fin_W,
             "Q_from_storage_used_W":Q_from_storage_used_fin_W,
             "E_aux_ch_W":E_aux_ch_fin_W,
             "E_aux_dech_W":E_aux_dech_fin_W,
             "Q_missing_W":Q_missing_fin_W,
             "mdot_DH_fin_kgpers":mdot_DH_fin_kgpers,
             "E_aux_HP_uncontrollable_Wh":E_aux_HP_uncontrollable_fin_flat_Wh,
             "E_PV_Wh":E_PV_Wh,
             "E_PVT_Wh":E_PVT_Wh,
             "Storage_Size_m3":STORAGE_SIZE_m3,
             "Q_SCandPVT_gen_Wh":Q_SCandPVT_gen_Wh,
             "E_produced_total_W":E_produced_total_W,
             "E_consumed_total_without_buildingdemand_W":E_consumed_total_without_buildingdemand_W,
             "HPServerHeatDesignArray_kWh":HPServerHeatDesignArray_kWh,
             "HPpvt_designArray_Wh":HPpvt_designArray_Wh,
             "HPCompAirDesignArray_kWh":HPCompAirDesignArray_kWh,
             "HPScDesignArray_Wh":HPScDesignArray_Wh,
             "Q_rejected_fin_W":Q_rejected_fin_W,
             "P_HPCharge_max_W":P_HP_max_W
            })
        storage_operation_data_path = locator.get_optimization_slave_storage_operation_data(MS_Var.configKey)
        results.to_csv(storage_operation_data_path, sep= ',')
        
        print "Results saved in :", locator.get_optimization_slave_results_folder()
        print " as : ", storage_operation_data_path
    
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

