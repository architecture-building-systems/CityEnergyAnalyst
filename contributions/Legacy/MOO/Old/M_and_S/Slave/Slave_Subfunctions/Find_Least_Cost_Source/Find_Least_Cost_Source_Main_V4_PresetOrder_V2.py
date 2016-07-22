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

t = time.time()
Network_Raw_Data_Path = MS_Var.Network_Raw_Data_Path
HOUR = 200

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





""" MINIMAL COST ALGORITHM STARTS """ # Run the Centralized Plant Operation Scheme

# Import Data - Network
Q_therm_req = Q_DH_networkload[HOUR,0]
mdot_DH_req = mdot_DH[HOUR,0]
tdhret = tdhret[HOUR,0]

# Import Data - Systems
mdotsew = 10.0
tsupsew = 20 + 273.0
tground = 8 + 273.0



def source_activator(Q_therm_req, HOUR):
    
    current_source = gV.act_first # Start with first source, no cost yet
    
    checkpoint = 0
    
    cost1 = [0,0,0]
    cost2 = 0
    cost3 = 0
    source1 = ['none','none','none']
    source2 = 'none'
    source3 = 'none'
    Q_source1 = [0,0,0]
    Q_source2 = 0
    Q_source3 = 0
    Eprim1 = [0,0,0]
    Eprim2 = 0
    Eprim3 = 0
    Eprim4 = 0
    
    it_counter = 0 
    while checkpoint == 0: # cover demand as long as the supply is lower than demand!
        
        if current_source == 'HP':# use heat pumps available!
            quitter = 0
            
            Q_therm_Sew = 0
            Q_therm_GHP = 0
            Q_therm_HPL = 0
            
            if (MS_Var.HP_Sew_on) == 1: # activate if its available
                

                if Q_therm_req > MS_Var.HPSew_maxSize:
                    Q_therm_Sew = MS_Var.HPSew_maxSize
                    mdot_DH_to_Sew = mdot_DH_req * Q_therm_Sew / Q_therm_req #scale down the mass flow if the thermal demand is lowered
                    quitter = 0
                    #print "Sewage Heat Pump at maximum capacity"  
                
                else:
                    Q_therm_Sew = Q_therm_req
                    mdot_DH_to_Sew = mdot_DH_req
                    quitter = 1
                # print "Sewage HP : regular operation possible"
                
                
                HP_Sew_Cost_Data = HPSew_op_cost(mdot_DH_to_Sew, tdhsup, tdhret, mdotsew, tsupsew)
                C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm = HP_Sew_Cost_Data
                
                # Storing data for further processing
                source1[0] = 'HP_Sew'
                cost1[0]= C_HPSew_el_pure
                Q_source1[0] = Q_therm_Sew
                Eprim1[0] = Q_HPSew_therm - Q_HPSew_cold_primary 
            if quitter == 1: # all the demand has been covered already, finish the loop
                Q_therm_req = 0
                break
            else:
                Q_therm_req -= Q_therm_Sew # calculates the remaining demand from another plant
                           
            
            if (MS_Var.GHP_on) == 1 and HOUR > MS_Var.GHP_SEASON_ON and  HOUR <= MS_Var.GHP_SEASON_OFF: # activating GHP plant if possible

                if Q_therm_req > MS_Var.GHP_max:
                    Q_therm_GHP = MS_Var.GHP_max
                    mdot_DH_to_GHP = mdot_DH_req * Q_therm_GHP / Q_therm_req #scale down the mass flow if the thermal demand is lowered
                    #print "Geothermal Heat Pump at maximum capacity"
                    quitter = 0
                else:
                    Q_therm_GHP = Q_therm_req
                    mdot_DH_to_GHP = mdot_DH_req
                    quitter = 1
                    #print "Geothermal HP : regular operation possible"
            
                GHP_Cost_Data = GHP_op_cost(mdot_DH_to_GHP, tdhsup, tdhret, MS_Var.T_ground)
                C_GHP_el, C_GHP_per_kWh_th, Q_GHP_cold_primary, Q_GHP_therm  = GHP_Cost_Data
                
                # Storing data for further processing
             
                source1[1] = 'GHP'
                cost1[1] = C_GHP_el
                Q_source1[1] = Q_therm_GHP
                
                
            if quitter == 1: # all the demand has been covered already, finish the loop
                Q_therm_req = 0
                break
                
            else:
                Q_therm_req -= Q_therm_GHP # calculates the remaining demand from another plant
            

            
            if (MS_Var.HP_Lake_on) == 1: # run Heat Pump Lake
                
                if Q_therm_req > MS_Var.HPLake_maxSize:
                    Q_therm_HPL = MS_Var.HPLake_maxSize
                    mdot_DH_to_Lake = mdot_DH_req * Q_therm_HPL / Q_therm_req #scale down the mass flow if the thermal demand is lowered
                    quitter = 0
                else:
                    Q_therm_HPL = Q_therm_req
                    mdot_DH_to_Lake = mdot_DH_req
                    quitter = 1
                
                HP_Lake_Cost_Data = HPLake_op_cost(mdot_DH_to_Lake, tdhsup, tdhret, MS_Var.T_Lake)
                C_HPL_el, C_HPL_per_kWh_th, Q_HPL_cold_primary, Q_HPL_therm = HP_Lake_Cost_Data
                
              
                source1[2] = 'HP_Lake'
                cost1[2] = C_HPL_el
                Q_source1[2] = Q_therm_HPL

            if quitter == 1: # all the demand has been covered already, finish the loop
                Q_therm_req = 0
                break
            else:
                Q_therm_req -= Q_therm_HPL # calculates the remaining demand from another plant
                
            Q_remaining = Q_therm_req
            print Q_remaining
    

        elif current_source == 'CC': # start activating the combined cycles

            #By definition, one can either activate the CHP (NG-CC) or ORC (Furnace)
            if (MS_Var.CHP_on) == 1: # only operate if the plant is available
                CC_op_cost_data = CC_op_cost(MS_Var.CHP_GT_SIZE, tdhsup, MS_Var.gt_fuel) # create cost information
                cost_per_Wh_CC_fn = CC_op_cost_data[2] #gets interpolated cost function
                Q_used_prim_CC_fn  = CC_op_cost_data[1] 
                Q_CC_min = CC_op_cost_data[3]
                Q_CC_max = CC_op_cost_data[4]
                

                if Q_therm_req > Q_CC_min: # operation Possible
                    
                    if Q_therm_req < Q_CC_max:# Normal operation Possible
                        cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_therm_req)
                        Q_CC_delivered = Q_therm_req
                        quitter = 1
                    else: # Only part of the demand can be delivered as 100% load achieved
                        cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CC_max)
                        Q_CC_delivered = Q_CC_max
                        quitter = 0
                    
                    Cost_CC = cost_per_Wh_CC * Q_CC_delivered 
                    Q_therm_req -= Q_CC_delivered
                    if Q_therm_req < 0: # negative numbers could occur: Iterative approach could lead to unrealistic numbers, catch that.
                        Q_therm_req = 0
                    source2 = 'CC'
                    cost2 = Cost_CC
                    Q_source2 = Q_CC_delivered
                    
                    if quitter == 1: # all the demand has been covered already, finish the loop
                        Q_therm_req = 0
                        break
                    else:
                         Q_therm_req -= Q_CC_delivered # calculates the remaining demand from another plant

           
            if (MS_Var.Furnace_on) == 1: # Activate Furnace if its there. By definition, either ORC or NG-CC!
                
                if Q_therm_req > gV.Furn_min_Load * MS_Var.Furnace_P_max: # Operate only if its above minimal load
                    
                    if Q_therm_req > MS_Var.Furnace_P_max: # scale down if above maximum load, Furnace operates at max. capacity
                        Q_therm_Furn = MS_Var.Furnace_P_max
                        Furnace_Cost_Data = Furnace_op_cost(Q_therm_Furn, MS_Var.Furnace_P_max, tdhret, MS_Var.Furn_Moist_type)
                        C_Furn_therm = Furnace_Cost_Data[0]
                        cost_per_Wh_Furn = Furnace_Cost_Data[1]
                        Q_Furn_prim = Furnace_Cost_Data[2]
                        #Q_Furn_therm = Furnace_Cost_Data[3]
                        Q_Furn_therm = MS_Var.Furnace_P_max
                        Q_remaining = Q_therm_req - Q_Furn_therm
                        source2 = 'Furnace'
                        cost2 = C_Furn_therm
                        Q_source2 = Q_therm_req
                        quitter = 0
        
                    else: # Normal Operation Possible
                        Furnace_Cost_Data = Furnace_op_cost(Q_therm_req, MS_Var.Furnace_P_max, tdhret, MS_Var.Furn_Moist_type)
                        cost_per_Wh_Furn = Furnace_Cost_Data[1]
                        Q_Furn_prim = Furnace_Cost_Data[2]
                        C_Furn_therm = Furnace_Cost_Data[0]
                        Q_Furn_therm = Furnace_Cost_Data[3]
                        Q_remaining = 0 
                        source2 = 'Furnace'
                        cost2 = C_Furn_therm
                        Q_source2 = Q_therm_req
                        #break outside loop?!
                        quitter = 1
                        
     
                else: # Furnace below part load, not active
                    Q_Furn_therm = 0
                    quitter = 0
                
                    
            if quitter == 1: # all the demand has been covered already, finish the loop
                Q_therm_req = 0
                break
            else:
                Q_therm_req -= Q_Furn_therm # calculates the remaining demand from another plant
            
             
        elif current_source == 'Boiler':
            
            if (MS_Var.Boiler_on) == 1:
                
                if Q_therm_req > gV.Boiler_min*MS_Var.Boiler_SIZE: # Boiler can be activated?
                    quitter  = 1
                    Q_therm_boiler = Q_therm_req
                    
                    if Q_therm_req > MS_Var.Boiler_SIZE: # Boiler above maximum Load?
                        Q_therm_boiler = MS_Var.Boiler_SIZE
                        quitter = 0

                    Boiler_Cost_Data = BoilerCond_op_cost(Q_therm_boiler, MS_Var.Boiler_SIZE, tdhret)
                    C_boil_therm, C_boil_per_Wh, Q_primary = Boiler_Cost_Data
                    
                    source3 = 'Boiler'
                    cost3 = C_boil_therm
                    Q_source3 = Q_therm_boiler 
                    
                                           
                else: # print "Boiler not activated, below minimum Part Load"
                    C_boil_therm = 0
                    C_boil_per_Wh = 0
                    Q_primary = 0
                    Q_therm_boiler = 0
                    quitter = 0

                
            if quitter == 1: # all the demand has been covered already, finish the loop
                Q_therm_req = 0
                break
            else:
                Q_therm_req -= Q_therm_boiler # calculates the remaining demand from another plant
            
        elif current_source == 'BoilerPeak':


            if (MS_Var.Boiler_on) == 1:
                if Q_therm_req > gV.Boiler_min*MS_Var.BoilerPeak_SIZE: # Boiler can be activated?
                    quitter  = 1
                    Q_therm_boiler = Q_therm_req
                    
                    if Q_therm_req > MS_Var.BoilerPeak_SIZE: # Boiler above maximum Load?
                        Q_therm_boiler = MS_Var.BoilerPeak_SIZE
                        quitter = 0

                    Boiler_Cost_Data = BoilerCond_op_cost(Q_therm_boiler, MS_Var.Boiler_SIZE, tdhret)
                    C_boil_therm, C_boil_per_Wh, Q_primary = Boiler_Cost_Data
                    
                    source4 = 'BoilerPeak'
                    cost4 = C_boil_therm
                    Q_source4 = Q_therm_boiler 
                    

                                           
                else: # print "Boiler not activated, below minimum Part Load"
                    C_boil_therm = 0
                    C_boil_per_Wh = 0
                    Q_primary = 0
                    Q_therm_boiler = 0
                    quitter = 0

                
            if quitter == 1: # all the demand has been covered already, finish the loop
                Q_therm_req = 0
                break
            else:
                Q_therm_req -= Q_therm_boiler # calculates the remaining demand from another plant
            
        
            
        #obtain: Cost1, Q_source1 Q_therm_req
        Q_remaining = Q_therm_req
        print Q_remaining
        if np.round(Q_remaining) > 0:
            if current_source == gV.act_first:
                current_source = gV.act_second
            elif current_source == gV.act_second:
                current_source = gV.act_third
            elif current_source == gV.act_third:
                current_source = gV.act_fourth
            else:
                print "not covered demand: ", Q_remaining, "Wh"
                print "insufficient capacity installed! Cannot cover the network demand (check Slave code, find_least_cost_source_main"
                #break
                raise MS_VarError
                
                
            checkpoint = 0
            print it_counter, "counter"
            it_counter += 1
            #if it_counter>20:
                

                
        else:
            checkpoint = 1
        
        if checkpoint == 1:
            print "All demand covered"
        else:
            print Q_remaining, "Wh not covered"
        
    return cost1, cost2, cost3, cost4, source1, source2, source3, source4, Q_source1, Q_source2, Q_source3, Q_source4









"""
    
Ctot = np.zeros(gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR)
Cmarg_tot = np.zeros(gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR)
used_sources_res = np.chararray((8760,2), itemsize=5)
Q_provided = np.zeros((gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR,2))

for HOUR in range(gV.HOURS_IN_DAY * gV.DAYS_IN_YEAR):
    Q_therm_req = Q_DH_networkload[HOUR]
    data = PP_Activator(Q_therm_req, opt_round, Q_provided1, Q_remaining1, used_sources, HOUR)
    Ctot[HOUR], Cmarg_tot[HOUR], used_sources_res[HOUR],Q_provided[HOUR] \
                = PP_Activator(Q_therm_req, opt_round, Q_provided1, Q_remaining1, used_sources,HOUR)
# save data 


elapsed = time.time() - t
print np.round(elapsed, decimals=0), "seconds used for this optimization"

save_file = 0
if save_file == 1:

    results = pd.DataFrame({"Total_Cost":Ctot,"T_initial":Cmarg_tot, "Q_initial":Q_initial})
    Name = "Storage_Sizing_Parameters.csv"
    os.chdir(SolarPowerHandler_Results_Path)
    results.to_csv(Name, sep= ',')
    print "results saved in : ", SolarPowerHandler_Results_Path
    print " as : ", Name
"""