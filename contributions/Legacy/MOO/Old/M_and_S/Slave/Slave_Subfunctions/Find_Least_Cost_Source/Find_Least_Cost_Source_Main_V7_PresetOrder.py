# -*- coding: utf-8 -*-
"""
Find Least Cost Source Main :
    This file is able to find the least cost source for power generation upon the 
    limitations given
    
"""
# Define Data Paths :
SolarPowerHandler_Results_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/\
Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Subfunctions/Results_from_Subfunctions"

Slave_PP_Activator_Results = "/Users/Tim/Desktop/ETH/Masterarbeit/\
Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Results"

Functions_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/\
M_and_S/Slave/Slave_Subfunctions/Find_Least_Cost_Source/Functions"

MS_Var_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

Cost_Maps_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/\
Slave/Slave_Subfunctions/Cost_Map_Functions"



import time
import os
import pandas as pd
import numpy as np
os.chdir(Functions_Path)
import Find_min_cost_functions as fn
reload (fn)
os.chdir(Functions_Path)
import Import_Network_Data_functions as INDf
reload (INDf)

os.chdir(MS_Var_Path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)
os.chdir(MS_Var.Energy_Models_path)
import globalVar as gV
reload(gV)

print "Least Cost Optimization Ready"


def Least_Cost_Optimization():
    """
    This function runs the least cost optimization code and returns cost, co2 and primary energy required. On the go, it saves the operation pattern
    
    Parameters
    ----------
    - NONE -
    
    Returns
    -------
    E_oil_eq_MJ : float
        MJ oil Equivalent used during operation
    
    CO2_kg_eq : float
        kg of CO2-Equivalent emitted during operation
        
    cost_sum : float
        total cost in CHF used for operation 
    
    """
    
    t = time.time()
    Network_Raw_Data_Path = MS_Var.Network_Raw_Data_Path
    
    class MS_VarError(Exception):
        """Base class for exceptions in this module."""
        pass
    
    class ModelError(Exception):
        """Base class for exceptions in this module."""
        pass
    """ IMPORT DATA """
    
    # Import Demand Data:
    os.chdir(SolarPowerHandler_Results_Path)
    CSV_NAME = "Data_with_Storage_applied.csv"
    Centralized_Plant_Requirements = INDf.import_CentralizedPlant_data(CSV_NAME, gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY)
    Q_DH_networkload, Q_aux_ch,Q_aux_dech, Q_missing, Q_storage_content_Wh, Q_to_storage, Solar_Q_th_W = Centralized_Plant_Requirements
    Q_missing_copy = Q_missing.copy()
    
    NETWORK_DATA_FILE = MS_Var.NETWORK_DATA_FILE
    
    # Import Temperatures from Network Summary: 
    
    os.chdir(Network_Raw_Data_Path)
    tdhret = np.array(pd.read_csv(NETWORK_DATA_FILE, usecols=["T_sst_heat_return_netw_total"], nrows=gV.DAYS_IN_YEAR* gV.HOURS_IN_DAY))
    mdot_DH = np.array(pd.read_csv(NETWORK_DATA_FILE, usecols=["mdot_heat_netw_total"], nrows=gV.DAYS_IN_YEAR* gV.HOURS_IN_DAY))
    tdhsup = MS_Var.Network_Supply_Temp
    
    # import Marginal Cost of PP Data :
    os.chdir(Cost_Maps_Path)
    
        
    
    """ LOAD MODULES """
    
    #    Boiler
    if (MS_Var.Boiler_on) == 1 or (MS_Var.BoilerPeak_on) == 1:
        os.chdir(Cost_Maps_Path)
        import Cost_Mapping_Boiler as CMBoil
        os.chdir(Cost_Maps_Path)
        reload(CMBoil)
        BoilerCond_op_cost = CMBoil.BoilerCond_op_cost
    
    #   Furnace
    if (MS_Var.Furnace_on) == 1:
        os.chdir(Cost_Maps_Path)
        import Cost_Mapping_Furnace as CMFurn
        os.chdir(Cost_Maps_Path)
        reload(CMFurn)
        Furnace_op_cost = CMFurn.Furnace_op_cost
    
    # Heat Pumps
    if (MS_Var.GHP_on) == 1 or (MS_Var.HP_Lake_on) == 1 or (MS_Var.HP_Sew_on) == 1 :
        os.chdir(Cost_Maps_Path)
        import Cost_Mapping_HP as CMHP
        os.chdir(Cost_Maps_Path)
        reload(CMHP)
        HPLake_op_cost = CMHP.HPLake_op_cost
        HPSew_op_cost = CMHP.HPSew_op_cost
        GHP_op_cost = CMHP.GHP_op_cost
    
    
    # CHP 
    if (MS_Var.CHP_on) == 1:
        os.chdir(Cost_Maps_Path)
        import Cost_Mapping_CC_PartLoad_givenGTSizeAndTDH_final as CMCC_fn
        os.chdir(Cost_Maps_Path)
        reload(CMCC_fn)
        CC_op_cost = CMCC_fn.CC_Find_Operation_Point_Functions
        # How to use: for e.g. cost_per_Wh(Q_therm):
        # type cost_per_Wh_fn = CC_op_cost(10E6, 273+70.0, "NG")[2]
        # similar: Q_used_prim_fn = CC_op_cost(10E6, 273+70.0, "NG")[1]
        # then: ask for Q_therm_req: 
        # Q_used_prim = Q_used_prim_fn(Q_therm_req) OR cost_per_Wh = cost_per_Wh_fn(Q_therm_req)
    
    
    
    
    
    """ MINIMAL COST ALGORITHM STARTS """ # Run the Centralized Plant Operation Scheme
    
    # Import Data - Systems
    # Space-Holder for Sewage Data
    mdotsew = 10.0
    tsupsew = 20 + 273.0
    tground = 8 + 273.0
    
    def source_activator(Q_therm_req, hour):
        current_source = gV.act_first # Start with first source, no cost yet
        mdot_DH_req = mdot_DH[hour,0]
        tdhret_req = tdhret[hour,0]
        
        # Initializing resulting values (necessairy as not all of them are over-written):
        
        costHPSew, costHPLake, costGHP, costCC, costFurnace, costBoiler, costBackup = 0,0,0,0,0,0,0
        
        sHPSew = 'off'
        sHPLake = 'off'  
        srcGHP = 'off'  
        sorcCC = 'off'
        sorcFurnace = 'off'
        sBoiler = 'off'
        sBackup = 'off'
        
        Q_HPSew, Q_HPLake, Q_GHP, Q_CC, Q_Furnace, Q_Boiler, Q_Backup = 0,0,0,0,0,0,0
        E_el_HPSew, E_el_HPLake, E_el_GHP, E_el_CC, E_el_Furnace, E_el_Boiler, E_el_Backup = 0,0,0,0,0,0,0
        E_gas_HPSew, E_gas_HPLake, E_gas_GHP, E_gas_CC, E_gas_Furnace, E_gas_Boiler, E_gas_Backup = 0,0,0,0,0,0,0
        E_wood_HPSew, E_wood_HPLake, E_wood_GHP, E_wood_CC, E_wood_Furnace, E_wood_Boiler, E_wood_Backup = 0,0,0,0,0,0,0
        E_coldsource_HPSew, E_coldsource_HPLake,  E_coldsource_GHP, E_coldsource_CC, \
                            E_coldsource_Furnace, E_coldsource_Boiler,  E_coldsource_Backup = 0,0,0,0,0,0,0
    
        
        while Q_therm_req > 0: # cover demand as long as the supply is lower than demand!
    
            if current_source == 'HP':# use heat pumps available!
                
                if (MS_Var.HP_Sew_on) == 1 and Q_therm_req  > 0: # activate if its available
                    
                    sHPSew = 'off'
                    costHPSew= 0.0
                    Q_HPSew = 0.0
                    E_el_HPSew = 0.0
                    E_coldsource_HPSew = 0.0
                    
                    if Q_therm_req > MS_Var.HPSew_maxSize:
                        Q_therm_Sew = MS_Var.HPSew_maxSize
                        mdot_DH_to_Sew = mdot_DH_req * Q_therm_Sew / Q_therm_req.copy() #scale down the mass flow if the thermal demand is lowered
                        Q_therm_req -= MS_Var.HPSew_maxSize
                    
                    else:
                        Q_therm_Sew = Q_therm_req.copy()
                        mdot_DH_to_Sew = mdot_DH_req.copy()
                        Q_therm_req = 0
                    
                    HP_Sew_Cost_Data = HPSew_op_cost(mdot_DH_to_Sew, tdhsup, tdhret_req, mdotsew, tsupsew)
                    C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm = HP_Sew_Cost_Data
    
                    # Storing data for further processing
                    sHPSew = 'on'
                    costHPSew= C_HPSew_el_pure
                    Q_HPSew = Q_therm_Sew
                    E_el_HPSew = C_HPSew_el_pure
                    E_coldsource_HPSew = Q_HPSew_cold_primary
                    
                
                if (MS_Var.GHP_on) == 1 and hour > MS_Var.GHP_SEASON_ON and  hour <= MS_Var.GHP_SEASON_OFF and Q_therm_req > 0: 
                                                                # activating GHP plant if possible
                    srcGHP = 'off'
                    costGHP = 0.0
                    Q_GHP = 0.0
                    E_el_GHP = 0.0
                    E_coldsource_GHP = 0.0
                    
                    Q_max = MS_Var.GHP_max
                    
                    if Q_therm_req > Q_max:
                        mdot_DH_to_GHP = Q_max / (gV.cp *(tdhsup -tdhret_req))
                        Q_therm_req -= Q_max
    
                    else: # regular operation possible, demand is covered
                        mdot_DH_to_GHP = Q_therm_req.copy() / (gV.cp * (tdhsup -tdhret_req))
                        Q_therm_req = 0
                        
                    GHP_Cost_Data = GHP_op_cost(mdot_DH_to_GHP, tdhsup, tdhret_req, MS_Var.T_ground)
                    C_GHP_el, C_GHP_per_kWh_th, Q_GHP_cold_primary, Q_GHP_therm  = GHP_Cost_Data
                    
                    # Storing data for further processing
                    srcGHP = 'on'
                    costGHP = C_GHP_el
                    Q_GHP = Q_GHP_therm
                    E_el_GHP = C_GHP_el
                    E_coldsource_GHP = Q_GHP_cold_primary
    
                if (MS_Var.HP_Lake_on) == 1 and Q_therm_req > 0: # run Heat Pump Lake
                    sHPLake  = 'off'
                    costHPLake = 0
                    Q_HPLake = 0
                    E_el_HPLake = 0
                    E_coldsource_HPLake = 0
                    
                    if Q_therm_req > MS_Var.HPLake_maxSize: # Scale down Load, 100% load achieved
                        Q_therm_HPL = MS_Var.HPLake_maxSize
                        mdot_DH_to_Lake = Q_therm_HPL / (gV.cp *(tdhsup - tdhret_req)) #scale down the mass flow if the thermal demand is lowered
                        Q_therm_req -=  MS_Var.HPLake_maxSize
    
                    else: # regular operation possible
                        Q_therm_HPL = Q_therm_req.copy()
                        mdot_DH_to_Lake = Q_therm_HPL / (gV.cp *(tdhsup - tdhret_req))
                        Q_therm_req = 0
                    
                    HP_Lake_Cost_Data = HPLake_op_cost(mdot_DH_to_Lake, tdhsup, tdhret_req, MS_Var.T_Lake)
                    C_HPL_el, C_HPL_per_kWh_th, Q_HPL_cold_primary, Q_HPL_therm = HP_Lake_Cost_Data
                    
                    # Storing Data
                    sHPLake  = 'on'
                    costHPLake = C_HPL_el
                    Q_HPLake = Q_therm_HPL
                    E_el_HPLake = C_HPL_el
                    E_coldsource_HPLake = Q_HPL_cold_primary
                                
                
            if current_source == 'CC' and Q_therm_req > 0: # start activating the combined cycles
                #By definition, one can either activate the CHP (NG-CC) or ORC (Furnace)
                Cost_CC = 0.0 
                sorcCC = 'off'
                costCC = 0.0
                Q_CC = 0.0
                E_gas_CC = 0.0
                
                if (MS_Var.CHP_on) == 1 and Q_therm_req > 0: # only operate if the plant is available
                    CC_op_cost_data = CC_op_cost(MS_Var.CHP_GT_SIZE, tdhsup, MS_Var.gt_fuel) # create cost information
                    cost_per_Wh_CC_fn = CC_op_cost_data[2] #gets interpolated cost function
                    Q_used_prim_CC_fn  = CC_op_cost_data[1] 
                    Q_CC_min = CC_op_cost_data[3]
                    Q_CC_max = CC_op_cost_data[4]
    
                    if Q_therm_req > Q_CC_min: # operation Possible if above minimal load
                        
                        if Q_therm_req < Q_CC_max:# Normal operation Possible within partload regime
                            cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_therm_req)
                            Q_used_prim_CC = Q_used_prim_CC_fn(Q_therm_req)
                            Q_CC_delivered = Q_therm_req.copy()
                            Q_therm_req = 0
                            
                        else: # Only part of the demand can be delivered as 100% load achieved
                            cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CC_max)
                            Q_used_prim_CC = Q_used_prim_CC_fn(Q_CC_max)
                            Q_CC_delivered = Q_CC_max
                            Q_therm_req -= Q_CC_max
                        
                        Cost_CC = cost_per_Wh_CC * Q_CC_delivered 
                        sorcCC = 'on'
                        costCC = Cost_CC
                        Q_CC = Q_CC_delivered
                        E_gas_CC = Q_used_prim_CC                   
            
                if (MS_Var.Furnace_on) == 1 and Q_therm_req > 0: # Activate Furnace if its there. By definition, either ORC or NG-CC!
                    Q_Furn_therm = 0
                    sorcFurnace = 'off'
                    costFurnace = 0.0
                    Q_Furnace = 0.0
                    E_wood_Furnace = 0.0
                    Q_Furn_prim = 0.0
                    
                    if Q_therm_req > (gV.Furn_min_Load * MS_Var.Furnace_P_max): # Operate only if its above minimal load
    
                        if Q_therm_req > MS_Var.Furnace_P_max: # scale down if above maximum load, Furnace operates at max. capacity
                            Furnace_Cost_Data = Furnace_op_cost(MS_Var.Furnace_P_max, MS_Var.Furnace_P_max, tdhret_req, MS_Var.Furn_Moist_type)
                            
                            C_Furn_therm = Furnace_Cost_Data[0]
                            Q_Furn_prim = Furnace_Cost_Data[2]
                            Q_Furn_therm = MS_Var.Furnace_P_max
                            Q_therm_req -= Q_Furn_therm
                        
    
            
                        else: # Normal Operation Possible
                            Furnace_Cost_Data = Furnace_op_cost(Q_therm_req, MS_Var.Furnace_P_max, tdhret_req, MS_Var.Furn_Moist_type)
    
                            Q_Furn_prim = Furnace_Cost_Data[2]
                            C_Furn_therm = Furnace_Cost_Data[0]
                            Q_Furn_therm = Q_therm_req.copy()
                            Q_therm_req = 0 
                            
                        sorcFurnace = 'on'
                        costFurnace = C_Furn_therm.copy()
                        Q_Furnace = Q_Furn_therm
                        E_wood_Furnace = Q_Furn_prim
                        
            if current_source == 'Boiler' and Q_therm_req > 0:
                Q_therm_boiler = 0
                if (MS_Var.Boiler_on) == 1:
                    sBoiler = 'off'
                    costBoiler = 0.0
                    Q_Boiler = 0.0                     
                    E_gas_Boiler = 0.0
                    
                    if Q_therm_req >= gV.Boiler_min*MS_Var.Boiler_SIZE: # Boiler can be activated?
                        #Q_therm_boiler = Q_therm_req
                        
                        if Q_therm_req >= MS_Var.Boiler_SIZE: # Boiler above maximum Load?
                            Q_therm_boiler = MS_Var.Boiler_SIZE
                        else:
                            Q_therm_boiler = Q_therm_req.copy()
                            
                        Boiler_Cost_Data = BoilerCond_op_cost(Q_therm_boiler, MS_Var.Boiler_SIZE, tdhret_req)
                        C_boil_therm, C_boil_per_Wh, Q_primary = Boiler_Cost_Data
                        
                        sBoiler = 'on'
                        costBoiler = C_boil_therm
                        Q_Boiler = Q_therm_boiler                     
                        E_gas_Boiler = Q_primary
                                            
                        Q_therm_req -= Q_therm_boiler
                
                
            if current_source == 'BoilerPeak' and Q_therm_req > 0:
    
    
                if (MS_Var.BoilerPeak_on) == 1:
                    sBackup = 'off'
                    costBackup = 0.0
                    Q_Backup = 0.0 
                    E_gas_Backup = 0
                    
                    if Q_therm_req > 0: #gV.Boiler_min*MS_Var.BoilerPeak_SIZE: # Boiler can be activated?
    
                        if Q_therm_req > MS_Var.BoilerPeak_SIZE: # Boiler above maximum Load?
                            Q_therm_boilerP = MS_Var.BoilerPeak_SIZE
                            Q_therm_req -= Q_therm_boilerP
                        else:                     
                            Q_therm_boilerP = Q_therm_req.copy()
                            Q_therm_req = 0
    
                        Boiler_Cost_DataP = BoilerCond_op_cost(Q_therm_boilerP, MS_Var.BoilerPeak_SIZE, tdhret_req)
                        C_boil_thermP, C_boil_per_WhP, Q_primaryP = Boiler_Cost_DataP
                        
                        sBackup = 'on'
                        costBackup = C_boil_thermP
                        Q_Backup = Q_therm_boilerP 
                        E_gas_Backup = Q_primaryP
    
    
            if np.floor(Q_therm_req) > 0:
                if current_source == gV.act_first:
                    current_source = gV.act_second
                elif current_source == gV.act_second:
                    current_source = gV.act_third
                elif current_source == gV.act_third:
                    current_source = gV.act_fourth
                else:
                    """
                    print "not covered demand: ", Q_remaining, "Wh"
                    print "last source tested: ", current_source
                    print "occured in hour: ", hour
                    print "insufficient capacity installed! Cannot cover the network demand (check Slave code, find_least_cost_source_main"
                    #break
                    """
                    print "not sufficient capacity installed in hour : ", hour
                    print Q_therm_req
                    
            elif Q_therm_req != 0:
                print "ERROR - TOO MUCH POWER! - ", -Q_therm_req/1000.0,"kWh in excess"
        
        
        cost_data = costHPSew, costHPLake, costGHP, costCC, costFurnace, costBoiler, costBackup
        source_info = sHPSew, sHPLake,  srcGHP,  sorcCC, sorcFurnace, sBoiler,  sBackup
        Q_source_data = Q_HPSew, Q_HPLake, Q_GHP, Q_CC, Q_Furnace, Q_Boiler, Q_Backup 
        E_el_data = E_el_HPSew, E_el_HPLake, E_el_GHP, E_el_CC, E_el_Furnace, E_el_Boiler, E_el_Backup
        E_gas_data = E_gas_HPSew, E_gas_HPLake, E_gas_GHP, E_gas_CC,  E_gas_Furnace, E_gas_Boiler, E_gas_Backup
        E_wood_data = E_wood_HPSew, E_wood_HPLake, E_wood_GHP, E_wood_CC, E_wood_Furnace, E_wood_Boiler, E_wood_Backup
        E_coldsource_data =  E_coldsource_HPSew,  E_coldsource_HPLake,  E_coldsource_GHP,  E_coldsource_CC, \
                            E_coldsource_Furnace, E_coldsource_Boiler,  E_coldsource_Backup
        
        return  cost_data, source_info, Q_source_data, E_coldsource_data, E_el_data, E_gas_data, E_wood_data
    
    
    
    cost_data = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7))
    source_info = np.chararray((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7), itemsize = 5)
    Q_source_data = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7))
    E_coldsource_data  = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7))
    E_el_data  = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7))
    E_gas_data  = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7))
    E_wood_data  = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,7))
    
    # Iterate over all hours in the year
    for hour in range(gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR):
        Q_therm_req = Q_missing[hour]
        PP_activation_data= source_activator(Q_therm_req, hour)
        cost_data[hour], source_info[hour], Q_source_data[hour], E_coldsource_data[hour], \
                E_el_data[hour], E_gas_data[hour], E_wood_data[hour] = PP_activation_data
    
    
    # save data 
    
    elapsed = time.time() - t
    
    print np.round(elapsed, decimals=0), "seconds used for this optimization"
    current_time = time.time()
    
    save_file = 1
    
    if save_file == 1:
        results = pd.DataFrame({    "Q_Network_Demand_after_Storage":Q_missing_copy[:,0],\
                                "Total_Cost_HPSew":cost_data[:,0],"Total_Cost_HPLake":cost_data[:,1],"Total_Cost_GHP":cost_data[:,2],\
                                "Total_Cost_CC":cost_data[:,3], "Total_Cost_Furnace":cost_data[:,4],"Total_Cost_Boiler":cost_data[:,5],\
                                "Total_Cost_Backup":cost_data[:,6],\
                                "HPSew_Status":source_info[:,0],"HPLake_Status":source_info[:,1], "GHP_Status":source_info[:,2],\
                                "CC_Status":source_info[:,3],"Furnace_Status":source_info[:,4], "Boiler_Status":source_info[:,5],\
                                "Backup_Status":source_info[:,6],\
                                "Q_HPSew":Q_source_data[:,0], "Q_HPLake":Q_source_data[:,1], "Q_GHP":Q_source_data[:,2],\
                                "Q_CC":Q_source_data[:,3], "Q_Furnace":Q_source_data[:,4], "Q_Boiler":Q_source_data[:,5], \
                                "Q_Backup":Q_source_data[:,6]})
        Name = "PP_Activation_Results_" + str(int(np.round(current_time,0))) + ".csv"
        os.chdir(Slave_PP_Activator_Results)
        results.to_csv(Name, sep= ',')
        
        print "PP Activation Results saved in : ", Slave_PP_Activator_Results
        print " as : ", Name
        
    # sum up results from PP Activation
    E_HPSew_sum = np.sum(E_el_data)
    E_el_sum = np.sum(E_el_data)
    E_gas_sum = np.sum(E_gas_data)
    E_wood_sum = np.sum(E_wood_data)
    E_coldsource_sum = np.sum(E_coldsource_data)
    cost_sum = np.sum(cost_data)
    
    
    # Differenciate between NG and BG as input
    if MS_Var.gt_fuel == 'BG':
        gas_to_oil = gV.BG_TO_OIL_EQ
        gas_to_co2 = gV.BG_TO_CO2
    else:
        gas_to_oil = gV.NG_TO_OIL_EQ
        gas_to_co2 = gV.NG_TO_CO2
    
    # Differenciate between Normal and green power
    if MS_Var.EL_TYPE == 'green':
        el_to_oil = gV.EL_TO_OIL_EQ_GREEN
        el_to_co2 = gV.EL_TO_CO2_GREEN
    else:
        el_to_oil = gV.EL_TO_OIL_EQ
        el_to_co2 = gV.EL_TO_CO2
    
    # Sum up the parameters  required to hand over to master 
    E_oil_eq_MJ = gV.Wh_to_J /1.0E6 * (E_el_sum * el_to_oil + E_gas_sum * gas_to_oil + E_wood_sum * gV.WOOD_TO_OIL_EQ)
    CO2_kg_eq = gV.Wh_to_J /1.0E6 * (E_el_sum * el_to_co2 + E_gas_sum * gas_to_co2 + E_wood_sum * gV.WOOD_TO_CO2)
    
    if save_file == 1:
        results = pd.DataFrame({"E_oil_eq_MJ":[E_oil_eq_MJ], "CO2_kg_eq":[CO2_kg_eq],"cost_sum":[cost_sum]})
        Name = "Slave_to_Master_Variables_" + str(int(np.round(current_time,0))) + ".csv"
        os.chdir(Slave_PP_Activator_Results)
        results.to_csv(Name, sep= ',')
        print "Slave to Master Variables saved in : ", Slave_PP_Activator_Results
        print " as : ", Name
        
    return E_oil_eq_MJ, CO2_kg_eq, cost_sum