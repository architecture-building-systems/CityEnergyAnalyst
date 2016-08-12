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


def Storage_Design(CSV_NAME, SOLCOL_TYPE, T_storage_old, Q_in_storage_old, Network_Data_Path, Solar_Data_Path, pathSlaveRes,\
                    STORAGE_SIZE, STORE_DATA, context, P_HP_max, gV):
    os.chdir(Network_Data_Path)
    MS_Var = context
    HOURS_IN_DAY = 24
    DAYS_IN_YEAR = 365

    # Import Network Data
    Network_Data = fn.import_network_data(CSV_NAME, DAYS_IN_YEAR, HOURS_IN_DAY)
    
    # recover Network  Data:
    mdot_heat_netw_total = Network_Data[0]
    #mdot_cool_netw_total = Network_Data[1]
    Q_DH_networkload = Network_Data[2]
    #Q_DC_networkload = Network_Data[3]
    T_DH_return_array = Network_Data[4]
    T_DH_supply_array = Network_Data[6]
    #T_DC_return_array = Network_Data[5]
    Q_wasteheatServer = Network_Data[8] #np.array(fn.extract_csv(fName, "Q_DH_building_netw_total", DAYS_IN_YEAR))
    Q_wasteheatCompAir = Network_Data[7]
    
    Solar_Data_SC = np.zeros((HOURS_IN_DAY* DAYS_IN_YEAR, 7))
    Solar_Data_PVT = np.zeros((HOURS_IN_DAY* DAYS_IN_YEAR, 7))
    Solar_Data_PV = np.zeros((HOURS_IN_DAY* DAYS_IN_YEAR, 7))
    
    Solar_Tscr_th_SC = Solar_Data_SC[:,6]
    Solar_E_aux_kW_SC = Solar_Data_SC[:,1]
    Solar_Q_th_kW_SC = Solar_Data_SC[:,1]
    
    Solar_Tscr_th_PVT = Solar_Data_PVT[:,6]
    Solar_E_aux_kW_PVT = Solar_Data_PVT[:,1]
    Solar_Q_th_kW_SC = Solar_Data_PVT[:,2]
    PV_kWh_PVT = Solar_Data_PVT[:,5]
    Solar_E_aux_kW_PV = Solar_Data_PV[:,1]
    PV_kWh_PV = Solar_Data_PV[:,5]
    
    # Import Solar Data
    os.chdir(Solar_Data_Path)
    
    fNameArray = [MS_Var.SOLCOL_TYPE_PVT, MS_Var.SOLCOL_TYPE_SC, MS_Var.SOLCOL_TYPE_PV]
    
        #LOOP AROUND ALL SC TYPES
    for solartype in range(3):
        fName = fNameArray[solartype]
    
        if MS_Var.SOLCOL_TYPE_SC != "NONE" and fName == MS_Var.SOLCOL_TYPE_SC:
            Solar_Area_SC, Solar_E_aux_kW_SC, Solar_Q_th_kW_SC, Solar_Tscs_th_SC, Solar_mcp_kW_C_SC, PV_kWh_SC, Solar_Tscr_th_SC\
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_SC, DAYS_IN_YEAR, HOURS_IN_DAY)
        
        if MS_Var.SOLCOL_TYPE_PVT != "NONE" and fName == MS_Var.SOLCOL_TYPE_PVT:
            Solar_Area_PVT, Solar_E_aux_kW_PVT, Solar_Q_th_kW_PVT, Solar_Tscs_th_PVT, Solar_mcp_kW_C_PVT, PV_kWh_PVT, Solar_Tscr_th_PVT \
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_PVT, DAYS_IN_YEAR, HOURS_IN_DAY)
            #Solar_Data_PVT= fn.import_solar_data(MS_Var.SOLCOL_TYPE_PVT, DAYS_IN_YEAR, HOURS_IN_DAY)
    
        if MS_Var.SOLCOL_TYPE_PV != "NONE" and fName == MS_Var.SOLCOL_TYPE_PV:
            Solar_Area_PV, Solar_E_aux_kW_PV, Solar_Q_th_kW_PV, Solar_Tscs_th_PV, Solar_mcp_kW_C_PV, PV_kWh_PV, Solar_Tscr_th_PV\
                            = fn.import_solar_data(MS_Var.SOLCOL_TYPE_PV, DAYS_IN_YEAR, HOURS_IN_DAY)

    #print "\n ........---------........."
    #print "sum of PV_kWh_PVT in Storage desing op v2", np.sum(PV_kWh_PVT) 
    # ADD SOLAR COLLECTOR AND SELL ELECTRICITY!
    
    # Recover Solar Data
   # Solar_Area = Solar_Data_SC[0] * MS_Var.SOLAR_PART_SC + Solar_Data_PVT[0] * MS_Var.SOLAR_PART_PVT + Solar_Data_PV[0] * MS_Var.SOLAR_PART_PV
    Solar_E_aux_W = np.ravel(Solar_E_aux_kW_SC * 1000 * MS_Var.SOLAR_PART_SC) + np.ravel(Solar_E_aux_kW_PVT * 1000 * MS_Var.SOLAR_PART_PVT) \
                            + np.ravel(Solar_E_aux_kW_PV * 1000 * MS_Var.SOLAR_PART_PV)
    #print "Solar_E_aux_W", np.shape(Solar_E_aux_W), Solar_E_aux_W
    #print "Solar_Data_SC", Solar_Data_SC
    
    Q_SC = Solar_Q_th_kW_SC * 1000 * MS_Var.SOLAR_PART_SC
    #print Q_SC, "Q_SC"
    Q_PVT = Solar_Q_th_kW_PVT * 1000 * MS_Var.SOLAR_PART_PVT
    Q_SCandPVT = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    
    #Q_SCandPVT = float(np.sum(Q_SC) + np.sum(Q_PVT))
    #Q_SCandPVT = Q_SC + Q_PVT
    for hour in range(len(Q_SCandPVT)):
        Q_SCandPVT[hour] = Q_SC[hour] + Q_PVT[hour]
        
    #print Q_SCandPVT
    #print "shape", np.shape(Q_SCandPVT)
    
    E_PV_Wh = PV_kWh_PV * 1000 * MS_Var.SOLAR_PART_PV
    E_PVT_Wh = PV_kWh_PVT * 1000  * MS_Var.SOLAR_PART_PVT
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
    Q_to_storage_avail = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_from_storage = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    to_storage = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_storage_content_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    T_storage_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_from_storage_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_to_storage_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_ch_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_dech_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    #E_PV_Wh_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_solar = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_missing_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_from_storage_used_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_rejected_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    mdot_DH_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    Q_uncontrollable_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_aux_HP_uncontrollable_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPServerHeatDesignArray = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPpvt_designArray = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPCompAirDesignArray = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    HPScDesignArray = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    
    T_amb = 10 + 273.0 # K
    T_storage_min = MS_Var.T_ST_MAX
    Q_disc_seasonstart = [0] 
    Q_loss_tot = 0 
    
    while HOUR < HOURS_IN_DAY*DAYS_IN_YEAR:
        # Store later on this data
        HPServerHeatDesign = 0
        HPpvt_design = 0
        HPCompAirDesign = 0
        HPScDesign = 0
        
        T_DH_sup = T_DH_supply_array[HOUR]
        T_DH_return = T_DH_return_array[HOUR]
        mdot_DH = mdot_heat_netw_total[HOUR]
        if MS_Var.WasteServersHeatRecovery == 1:
            QServerHeat = Q_wasteheatServer[HOUR]
        else:
            QServerHeat = 0
        #print QServerHeat, "QServerHeat"
        if MS_Var.WasteCompressorHeatRecovery == 1:
            QCompAirHeat= Q_wasteheatCompAir[HOUR]
        else:
            QCompAirHeat = 0
        #print Q_SC,"Q_SC", len(Q_SC)
        Qsc = Q_SC[HOUR]
        Qpvt = Q_PVT[HOUR]
        
        # check if each source needs a heat-pump, calculate the final energy 
        if T_DH_sup > gV.TElToHeatSup - gV.dT_heat: #and checkpoint_ElToHeat == 1:
            #use a heat pump to bring it to network temp
            COP_th = T_DH_sup / (T_DH_sup - (gV.TElToHeatSup - gV.dT_heat)) 
            COP = gV.HP_etaex * COP_th
            E_aux_Server = QServerHeat * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_Server > 0:
                HPServerHeatDesign = QServerHeat
                QServerHeat += E_aux_Server
            
        else:
            E_aux_Server = 0.0
            
        if T_DH_sup > gV.TfromServer - gV.dT_heat:# and checkpoint_QfromServer == 1: 
            #use a heat pump to bring it to network temp
            COP_th = T_DH_sup / (T_DH_sup - (gV.TfromServer - gV.dT_heat)) 
            COP = gV.HP_etaex * COP_th
            E_aux_CAH = QCompAirHeat * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_Server > 0:
                HPCompAirDesign = QCompAirHeat
                QCompAirHeat += E_aux_CAH
        else:
            E_aux_CAH = 0.0

        if T_DH_sup > Solar_Tscr_th_PVT[HOUR] - gV.dT_heat:# and checkpoint_PVT == 1:
            #use a heat pump to bring it to network temp
            COP_th = T_DH_sup / (T_DH_sup - (Solar_Tscr_th_PVT[HOUR] - gV.dT_heat)) 
            COP = gV.HP_etaex * COP_th
            E_aux_PVT = Qpvt * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_PVT > 0:
                HPpvt_design = Qpvt
                Qpvt += E_aux_PVT
                
        else:
            E_aux_PVT = 0.0
            
        if T_DH_sup > Solar_Tscr_th_SC[HOUR] - gV.dT_heat:# and checkpoint_SC == 1:
            #use a heat pump to bring it to network temp
            COP_th = T_DH_sup / (T_DH_sup - (Solar_Tscr_th_SC[HOUR] - gV.dT_heat)) 
            #print Solar_Tscr_th_SC[HOUR], "Solar_Tscr_th_SC[HOUR]"
            COP = gV.HP_etaex * COP_th
            E_aux_SC = Qsc * (1/COP) # assuming the losses occur after the heat pump
            if E_aux_SC > 0:
                HPScDesign = Qsc
                Qsc += E_aux_SC
        else:  
            E_aux_SC = 0.0
        
        
        HPServerHeatDesignArray[HOUR] = HPServerHeatDesign
        HPpvt_designArray[HOUR] = HPpvt_design
        HPCompAirDesignArray[HOUR] = HPCompAirDesign
        HPScDesignArray[HOUR] = HPScDesign
        
        
        E_aux_HP_uncontrollable = float(E_aux_SC + E_aux_PVT + E_aux_CAH + E_aux_Server)
        
        #print E_aux_HP_uncontrollable, len(E_aux_HP_uncontrollable), type(E_aux_HP_uncontrollable)
        
        # Heat Recovery has some losses, these are taken into account as "overall Losses", i.e.: from Source to DH Pipe
        # hhhhhhhhhhhhhh GET VALUES
        Q_uncontrollable = (Qpvt + Qsc + QServerHeat * gV.etaServerToHeat + QCompAirHeat *gV.etaElToHeat ) 

        #print "Q_uncontrollable = ", Q_uncontrollable
        #print "E_aux_HP_uncontrollable = ", E_aux_HP_uncontrollable
        
        Q_network_demand = Q_DH_networkload[HOUR]
        Q_to_storage_avail[HOUR], Q_from_storage[HOUR], to_storage[HOUR] = SPH_fn.StorageGateway(Q_uncontrollable, Q_network_demand, P_HP_max, gV)
        
       
        #print HOUR, Q_to_storage_avail[HOUR], Q_from_storage[HOUR], to_storage[HOUR] 
        Storage_Data = SPH_fn.Storage_Operator(Q_uncontrollable, Q_network_demand, T_storage_old, T_DH_sup, T_amb, \
                                        Q_in_storage_old, T_DH_return, mdot_DH, STORAGE_SIZE, context, P_HP_max, gV)
    
        Q_in_storage_new = Storage_Data[0]
        #print "Q_in_storage_new in Storage desing and operation: ", Q_in_storage_new
        T_storage_new = Storage_Data[1]
        Q_to_storage_final = Storage_Data[3]
        Q_from_storage_req_final = Storage_Data[2]
        #print "Q_from_storage_req_final", Q_from_storage_req_final
        #print "Q_to_storage_final", Q_to_storage_final
        E_aux_ch = Storage_Data[4]
        E_aux_dech = Storage_Data[5]
        Q_missing = Storage_Data[6]
        Q_from_storage_used_fin[HOUR] = Storage_Data[7]
        Q_loss_tot += Storage_Data[8]
        mdot_DH_afterSto = Storage_Data[9]
        
        if Q_in_storage_new < 0.0001:
            Q_in_storage_new = 0
    
        
        if T_storage_new >= MS_Var.T_ST_MAX-0.001: # no more charging possible - reject energy
            Q_in_storage_new = min(Q_in_storage_old, Storage_Data[0])
            Q_to_storage_final = max(Q_in_storage_new - Q_in_storage_old,0)
            Q_rejected_fin[HOUR] = Q_uncontrollable - Storage_Data[3]
            T_storage_new = min(T_storage_old, T_storage_new)
            E_aux_ch = 0
            print "Storage Full!"
            

            
        Q_storage_content_fin[HOUR] = Q_in_storage_new
        Q_in_storage_old = Q_in_storage_new
        
        T_storage_fin[HOUR] = T_storage_new
        T_storage_old = T_storage_new
        
        if T_storage_old < T_amb-1: # chatch an error if the storage temperature is too low
            print "ERROR!"
            break
        
        Q_from_storage_fin[HOUR] = Q_from_storage_req_final
        Q_to_storage_fin[HOUR] = Q_to_storage_final
        E_aux_ch_fin[HOUR] = E_aux_ch
        E_aux_dech_fin[HOUR] = E_aux_dech
        E_aux_solar[HOUR] = Solar_E_aux_W[HOUR]
        Q_missing_fin[HOUR] = Q_missing
        Q_uncontrollable_fin[HOUR] = Q_uncontrollable
        
        
        E_aux_HP_uncontrollable_fin[HOUR] = float(E_aux_HP_uncontrollable)
        #print type(E_aux_HP_uncontrollable_fin[HOUR]),
        mdot_DH_fin[HOUR] = mdot_DH_afterSto
        
        Q_from_storage_fin[HOUR] = Q_DH_networkload[HOUR,0] - Q_missing
        
        if T_storage_new <= T_storage_min:
            T_storage_min = T_storage_new
            Q_disc_seasonstart[0] += Q_from_storage_req_final
            
        
        HOUR += 1
        
        
        """ STORE DATA """
    E_aux_HP_uncontrollable_fin_flat = E_aux_HP_uncontrollable_fin.flatten()
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
    E_produced_total = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    E_consumed_total_without_buildingdemand = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
    
    for hour in range(DAYS_IN_YEAR, HOURS_IN_DAY):
        E_produced_total[hour] = E_PV_Wh[hour] + E_PVT_Wh[hour]
        E_consumed_total_without_buildingdemand[hour] = E_aux_ch[hour] + E_aux_dech[hour] + E_aux_HP_uncontrollable[hour]


    if STORE_DATA == "yes":
        
        results = pd.DataFrame(
            {"Q_storage_content_Wh":Q_storage_content_fin, 
             "Q_DH_networkload":Q_DH_networkload[:,0],
             "Q_uncontrollable_hot":Q_uncontrollable_fin,
             "Q_to_storage":Q_to_storage_fin, 
             "Q_from_storage_used":Q_from_storage_used_fin,
             "E_aux_ch":E_aux_ch_fin, 
             "E_aux_dech":E_aux_dech_fin, 
             "Q_missing":Q_missing_fin, 
             "mdot_DH_fin":mdot_DH_fin,
             "E_aux_HP_uncontrollable":E_aux_HP_uncontrollable_fin_flat,
             "E_PV_Wh":E_PV_Wh,
             "E_PVT_Wh":E_PVT_Wh,
             "Storage_Size":STORAGE_SIZE,
             "Q_SCandPVT_coldstream":Q_SCandPVT,
             "E_produced_total":E_produced_total,
             "E_consumed_total_without_buildingdemand":E_consumed_total_without_buildingdemand,
             "HPServerHeatDesignArray":HPServerHeatDesignArray,
             "HPpvt_designArray":HPpvt_designArray,
             "HPCompAirDesignArray":HPCompAirDesignArray,
             "HPScDesignArray":HPScDesignArray,
             "Q_rejected_fin":Q_rejected_fin,
             "P_HPCharge_max":P_HP_max
            })
        Name = MS_Var.configKey + "StorageOperationData.csv"
        os.chdir(pathSlaveRes)
        results.to_csv(Name, sep= ',')
        
        print "Results saved in :", pathSlaveRes
        print " as : ", Name 
    
    Q_stored_max = np.amax(Q_storage_content_fin)
    T_st_max = np.amax(T_storage_fin)
    T_st_min = np.amin(T_storage_fin)
        
    return Q_stored_max, Q_rejected_fin, Q_disc_seasonstart, T_st_max, T_st_min, Q_storage_content_fin, T_storage_fin, \
                                    Q_loss_tot, mdot_DH_fin, Q_uncontrollable_fin
    
""" DESCRIPTION FOR FUTHER USAGE"""
# Q_missing_fin  : has to be replaced by other means, like a HP
# Q_from_storage_fin : What is used from Storage
# Q_aus_fin : how much energy was spent on Auxillary power !! NOT WORKING PROPERLY !!
# Q_from_storage_fin : How much energy was used from the storage !! NOT WORKING PROPERLY !!
# Q_missing_fin : How much energy is missing

