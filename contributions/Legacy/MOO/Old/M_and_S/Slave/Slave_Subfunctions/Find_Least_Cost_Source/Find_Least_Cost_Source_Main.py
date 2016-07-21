# -*- coding: utf-8 -*-
"""
Find Least Cost Source Main :
    This file is able to find the least cost source for power generation upon the 
    limitations given
    
"""
# Define Data Paths :
SolarPowerHandler_Results_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/\
Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Subfunctions/Results_from_Subfunctions"

Functions_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/\
M_and_S/Slave/Slave_Subfunctions/Find_Least_Cost_Source/Functions"

MS_Var_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

Cost_Maps_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/\
Slave/Slave_Subfunctions/Cost_Map_Functions"

import os
import pandas as pd
import numpy as np
os.chdir(Functions_Path)
import Import_Network_Data_functions as INDf
reload (INDf)

os.chdir(MS_Var_Path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)
os.chdir(MS_Var.Energy_Models_path)
import globalVar as gV
reload(gV)


Network_Raw_Data_Path = MS_Var.Network_Raw_Data_Path
HOUR = 30



""" IMPORT DATA """

# Import Demand Data:
os.chdir(SolarPowerHandler_Results_Path)
CSV_NAME = "Data_with_Storage_applied.csv"
Centralized_Plant_Requirements = INDf.import_CentralizedPlant_data(CSV_NAME, gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY)
Q_DH_networkload, Q_aux_ch,Q_aux_dech, Q_missing, Q_storage_content_Wh, Q_to_storage, Solar_Q_th_W = Centralized_Plant_Requirements

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
if (MS_Var.Boiler_on) == 1:
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





""" MINIMAL COST ALGORITHM STARTS """

# Run the Centralized Plant Merit Order Cost Algorithm

# Import Data - Network
Q_therm_req = Q_DH_networkload[HOUR,0]
#Q_therm_req = Q_therm_req*10.0
mdot_DH_req = mdot_DH[HOUR,0]
tdhsup = tdhsup
tdhret = tdhret[HOUR,0]

# Import Data - Systems
mdotsew = 10 + 273.0
tsupsew = 20 + 273.0
tground = 8 + 273.0


""" TRY TO COVER WITH 1 PLANT """

# ask for specific cost


def find_minimum_cost(Q_therm_req):
            
        # Combined Cycle CHP
    if (MS_Var.CHP_on) == 1:
        CC_op_cost_data = CC_op_cost(MS_Var.CHP_GT_SIZE, tdhsup, MS_Var.gt_fuel)
        cost_per_Wh_CC_fn =CC_op_cost_data[2]
        Q_used_prim_CC_fn  = CC_op_cost_data[1]
        Q_CC_min = CC_op_cost_data[3]
        Q_CC_max = CC_op_cost_data[4]
        
        if Q_therm_req > Q_CC_min:
            if Q_therm_req < Q_CC_max:
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_therm_req)
                print "Combined Cyle in Normal Operation"
                Q_CC_delivered = Q_therm_req
            else:
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CC_max)
                Q_CC_delivered = Q_CC_max
                print "CC at maximum capacity"
            Cost_CC = cost_per_Wh_CC * Q_CC_delivered 
            
        #        create a mini-costmap  for the CC operation: 
            it_len = 20
            CC_it = 0
            
            # cut the operation in 20 linear sections
            Q_CC_therm_range = np.linspace(Q_CC_min, Q_CC_delivered, it_len)
        
            cost_per_Wh_CC_it = np.zeros(it_len)
            Q_used_prim_CC_it = np.zeros(it_len)
            Q_CC_min_it = np.zeros(it_len)
            Q_CC_max_it = np.zeros(it_len)
            
            for CC_it in range(it_len):
                Q_CC_it = Q_CC_therm_range[CC_it]
                CC_op_cost_data= CC_op_cost(MS_Var.CHP_GT_SIZE, tdhsup, MS_Var.gt_fuel)
                cost_per_Wh_CC_it[CC_it] = CC_op_cost_data[2](Q_CC_it)
                Q_used_prim_CC_it[CC_it]  = CC_op_cost_data[1](Q_CC_it)
            
        else:
            Q_CC_delivered = 0
            cost_per_Wh_CC = np.inf
            cost_per_Wh_CC_it = [np.inf, np.inf]
            print "CC below Part Load"
            Cost_CC = 0
    else:
        Q_CC_delivered = 0
        Cost_CC = np.inf
        cost_per_Wh_CC_it = [np.inf, np.inf]
    
        print "CC not active"
    
    
        # Furnace
    if (MS_Var.Furnace_on) == 1:
        def Furnace_operation(Q_therm_req):     
            if Q_therm_req > gV.Furn_min_Load * MS_Var.Furnace_P_max:
                
                if Q_therm_req > MS_Var.Furnace_P_max:
                    
                    Furnace_Cost_Data = Furnace_op_cost(Q_therm_req, MS_Var.Furnace_P_max, tdhret, MS_Var.Furn_Moist_type)
                    C_Furn_therm = Furnace_Cost_Data[0]
                    cost_per_Wh_Furn = Furnace_Cost_Data[1]
                    Q_Furn_prim = Furnace_Cost_Data[2]
                    Q_Furn_therm = Furnace_Cost_Data[3]
                    print "Furnace at maximum capacity"
                
                else:
                    Furnace_Cost_Data = Furnace_op_cost(Q_therm_req, MS_Var.Furnace_P_max, tdhret, MS_Var.Furn_Moist_type)
                    cost_per_Wh_Furn = Furnace_Cost_Data[1]
                    Q_Furn_prim = Furnace_Cost_Data[2]
                    C_Furn_therm = Furnace_Cost_Data[0]
                    Q_Furn_therm = Furnace_Cost_Data[3]
        
        #        create a mini-costmap  for the furnace operation: 
                it_len = 20
                Furn_it = 0
                
                # cut the operation in 20 linear sections
                Q_Furn_therm_range = np.linspace(gV.Furn_min_Load * MS_Var.Furnace_P_max + 0.1, Q_Furn_therm, it_len)
                C_Furn_therm_iter = np.zeros(it_len)
                cost_per_Wh_Furn_iter = np.zeros(it_len)
                Q_Furn_prim_iter = np.zeros(it_len)
                Q_Furn_therm_iter = np.zeros(it_len)
                print "Furnace : regular oparation possible"
                for Furn_it in range(it_len):
                    Q_Furn_it = Q_Furn_therm_range[Furn_it]
                    Furnace_Cost_Data= Furnace_op_cost(Q_Furn_it, MS_Var.Furnace_P_max, tdhret, MS_Var.Furn_Moist_type)
                    C_Furn_therm_iter[Furn_it] = Furnace_Cost_Data[0]
                    cost_per_Wh_Furn_iter[Furn_it]  = Furnace_Cost_Data[1]
                    Q_Furn_prim_iter[Furn_it]  = Furnace_Cost_Data[2]
                    Q_Furn_therm_iter[Furn_it]  = Furnace_Cost_Data[3]
                    
            else:
                C_Furn_therm = np.inf
                Q_Furn_prim = np.inf
                cost_per_Wh_Furn = np.inf
                Q_Furn_therm = np.inf
                print "Furnace below Part Load" 
            return C_Furn_therm, cost_per_Wh_Furn, Q_Furn_prim, Q_Furn_therm
            
        C_Furn_therm, cost_per_Wh_Furn, Q_Furn_prim, Q_Furn_therm = Furnace_operation(Q_therm_req)
    
    else:
        C_Furn_therm = np.inf
        Q_prim_Furn = np.inf
        Cost_Furn = np.inf
        Q_Furn_therm = np.inf
        print "Furnace not active"
        
        # Heat Pumps - DO NOT GO ABOVE tcond = tsup + gV.HP_deltaT_cond = 85°C
            # Geothermal Heat Pump
    if (MS_Var.GHP_on) == 1:
        
        if Q_therm_req > MS_Var.GHP_max:
            Q_therm_GHP = MS_Var.GHP_max
            mdot_GHP = mdot_DH_req * Q_therm_GHP / Q_therm_req #scale down the mass flow if the thermal demand is lowered
            print "Geothermal Heat Pump at maximum capacity"
        else:
            Q_therm_GHP = Q_therm_req
            mdot_GHP = mdot_DH_req
            print "Geothermal HP : regular operation possible"
    
        GHP_Cost_Data = GHP_op_cost(mdot_GHP, tdhsup, tdhret, MS_Var.T_ground)
        C_GHP_el, C_GHP_per_kWh_th, Q_GHP_cold_primary, Q_GHP_therm  = GHP_Cost_Data
        
    else:
        C_GHP_el, C_GHP_per_kWh_th, Q_GHP_cold_primary, Q_GHP_therm = [np.inf, np.inf, np.inf, np.inf]
    
    
    if (MS_Var.HP_Lake_on) == 1:
        
        if Q_therm_req > MS_Var.HP_maxSize:
            Q_therm_Lake = MS_Var.HP_maxSize
            mdot_Lake = mdot_DH_req * Q_therm_Lake / Q_therm_req #scale down the mass flow if the thermal demand is lowered
            print "Lake Heat Pump at maximum capacity"
            
        else:
            Q_therm_GHP = Q_therm_req
            mdot_Lake = mdot_DH_req
            print "Lake HP : regular operation possible"
        
        HP_Lake_Cost_Data = HPLake_op_cost(mdot_Lake, tdhsup, tdhret, MS_Var.T_Lake)
        C_HPL_el, C_HPL_per_kWh_th, Q_HPL_cold_primary, Q_HPL_therm = HP_Lake_Cost_Data
    
    else: 
        C_HPL_el, C_HPL_per_kWh_th, Q_HPL_cold_primary, Q_HPL_therm  = [np.inf, np.inf, np.inf, np.inf] 
    
    if (MS_Var.HP_Sew_on) == 1:
    
        if Q_therm_req > MS_Var.HP_maxSize:
            Q_therm_Sew = MS_Var.HP_maxSize
            mdot_Sew = mdot_DH_req * Q_therm_Lake / Q_therm_req #scale down the mass flow if the thermal demand is lowered
            print "Sewage Heat Pump at maximum capacity"  
        else:
            Q_therm_GHP = Q_therm_req
            mdot_Sew = mdot_DH_req
            print "Sewage HP : regular operation possible"
        
        HP_Sew_Cost_Data = HPSew_op_cost(mdot_Sew, tdhsup, tdhret, mdotsew, tsupsew)
        C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm = HP_Sew_Cost_Data
    
    else:
        C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm = [np.inf, np.inf, np.inf, np.inf]    
    
        # REMARK ! using the lake heat pump  is limited over the year!! + takes additional pumping requirements!! (Auxillary power of HP?)
    
    
    if (MS_Var.Boiler_on) == 1:
        if Q_therm_req > gV.Boiler_min*MS_Var.Boiler_SIZE and Q_therm_req <=MS_Var.Boiler_SIZE:
            Q_therm_boiler = Q_therm_req
            
            if Q_therm_req > MS_Var.Boiler_SIZE:
                Q_therm_boiler = MS_Var.Boiler_SIZE
                print "Boiler at maximum Load"
            else:
                print "Boiler: regular Operation possible"
            Boiler_Cost_Data = BoilerCond_op_cost(Q_therm_boiler, MS_Var.Boiler_SIZE, tdhret)
            C_boil_therm, C_boil_per_Wh, Q_primary = Boiler_Cost_Data
            
            # Iterate over Boiler Cost (should the boiler-load be lowered?)
            it_len = 20
            Boil_it = 0
            
            # cut the operation in 20 linear sections
            Q_Boil_therm_range = np.linspace(gV.Boiler_min*MS_Var.Boiler_SIZE, Q_therm_boiler, it_len)
            C_boil_therm_it = np.zeros(it_len)
            C_boil_per_Wh_it = np.zeros(it_len)
            Q_primary_it = np.zeros(it_len)
    
            for Boil_it in range(it_len):
                Q_Boil_it = Q_Boil_therm_range[Boil_it]
                Boiler_Cost_Data = BoilerCond_op_cost(Q_Boil_it, Q_therm_boiler, tdhret)
                C_boil_therm_it[Boil_it] = Boiler_Cost_Data[0]
                C_boil_per_Wh_it[Boil_it] = Boiler_Cost_Data[1]
                Q_primary_it[Boil_it] = Boiler_Cost_Data[2]
                
        else:
            C_boil_therm = np.inf
            C_boil_per_Wh = np.inf
            Q_primary = np.inf
            C_boil_per_Wh_it = [np.inf, np.inf]
            Q_therm_boiler = 0
            print "Boiler not activated, below minimum Part Load"
    else:
        C_boil_therm = np.inf
        C_boil_per_Wh = np.inf
        Q_primary = np.inf
        Q_therm_boiler = 0
        C_boil_per_Wh_it = [np.inf, np.inf]
        "Boiler not in System"
        
    # compare all tech upon price:
    # Constant marginal Cost for all Heat Pumps, slight change expected at
    
    if (MS_Var.Boiler_on) == 1:
        if min(C_boil_per_Wh_it) >= C_boil_per_Wh:
            print "no Boiler Optimization"
            C_boil_per_Wh_it_min = C_boil_per_Wh
            Boiler_optimization = 0
        else:
            Boiler_optimization = 1
            C_boil_per_Wh_it_min = min(C_boil_per_Wh_it)
            print "Boiler can be optimized"
    else:
        C_boil_per_Wh_it_min = np.inf
        Boiler_optimization = 0
    
        
    
    if (MS_Var.CHP_on) == 1:
        if min(cost_per_Wh_CC_it) >= cost_per_Wh_CC:
            print "no CC optimization"
            cost_per_Wh_CC_it_min = cost_per_Wh_CC
            CC_optimization = 0
        else: 
            CC_optimization = 1
            cost_per_Wh_CC_it_min = min(cost_per_Wh_CC_it)
            print "CC can be optimized"
            
    else:
        cost_per_Wh_CC_it = np.inf
        cost_per_Wh_CC = np.inf
        cost_per_Wh_CC_it_min = np.inf
        Q_CC_delivered = np.inf
        Cost_CC = np.inf
        CC_optimization = 0
    
    
    
    if (MS_Var.Furnace_on) == 1:
        
        if min(cost_per_Wh_Furn_iter) >= cost_per_Wh_Furn:
            Furnace_optimization = 0
            cost_per_Wh_Furn_iter_min = cost_per_Wh_Furn
            print "no Furnace optimization"
        else: 
            Furnace_optimization = 1
            cost_per_Wh_Furn_iter_min = min(cost_per_Wh_Furn_iter)
            
            print "Furnace can be optimized"
    else:
        cost_per_Wh_Furn_iter_min = np.inf
        cost_per_Wh_Furn = np.inf
        Furnace_optimization = 0
    
        
    # store this data into a list (easier comparison)
    
    Qtot = [Q_therm_req, Q_therm_boiler, Q_Furn_therm, Q_GHP_therm, Q_HPL_therm, Q_HPSew_therm, Q_CC_delivered]
    Ctot =  [np.inf, C_boil_therm, C_Furn_therm, C_GHP_el, C_HPL_el, C_HPSew_el_pure, Cost_CC]
    Cmarg = [np.inf, C_boil_per_Wh, cost_per_Wh_Furn, C_GHP_per_kWh_th, C_HPL_per_kWh_th,\
                C_HPSew_per_kWh_th_pure, cost_per_Wh_CC]
    Cmarg_min = [np.inf, C_boil_per_Wh_it_min, cost_per_Wh_Furn_iter_min, C_GHP_per_kWh_th, \
                C_HPL_per_kWh_th, C_HPSew_per_kWh_th_pure, cost_per_Wh_CC_it_min]
    
    
    name_array = ["DH_Requirement","Boiler", "Furnace", "GHP", "HP_Lake", "HP_Sew", "CHP"]
    
    df = pd.DataFrame({'Qtot': Qtot, 'Ctot' : Ctot , 'Cmarg': Cmarg, 'Cmarg_min': Cmarg_min}, index=name_array) 
    
    print df
    
    
    first_source = np.argmin(Cmarg_min)
    print name_array[first_source]
    #Q_by_first = np.pop.Qtot[first_source]
    
    #Q_remaining = Qtot[0] - Q_by_first
    
    min_source = df.sort('Cmarg', ascending=True)
    min_marg_source = df.sort('Cmarg', ascending=True)
    
    print min_source
    
    Q_provided = min_source.Qtot[0]
    Cmarg_used = min_source.Cmarg[0]
    Ctot_used = min_source.Ctot[0]
    Q_remaining = Q_therm_req - Q_provided
    
    if min_source.Cmarg[0] == min_marg_source.Cmarg_min[0]:
        print "minimum found"
        
    else:
        print "no"
        
    return