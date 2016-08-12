
import cea.optimization.slave.Find_Least_Cost_Source_PresetOrder as Least_Cost
reload(Least_Cost)

#Least_Cost_Path =  "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/Slave/Slave_Subfunctions/Find_Least_Cost_Source"

#Storage_Optimization_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/Slave/Slave_Subfunctions/Storage_Power_Operation_Losses_Partload/"

#Substation_Model_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/Slave/Slave_Subfunctions/Substation_Model/"

#Network_Summary_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/Slave/Slave_Subfunctions/Summarize_Network_States/"

import time

#import os
#os.chdir(Least_Cost_Path)
#import Find_Least_Cost_Source_Main_V7_PresetOrder as Least_Cost
#reload(Least_Cost)

#os.chdir(Storage_Optimization_Path)
import cea.optimization.slave.Storage_Power_Operation_Losses_Partload.Storage_Optimizer_incl_Losses_main_2 as Storage_Opt
reload(Storage_Opt)

#os.chdir(Substation_Model_Path)
#import substation_combined_main_V4_NOhextype_NewNames as Substation_Model
#os.chdir(Substation_Model_Path)
#reload(Substation_Model)

#os.chdir(Network_Summary_Path)
#import summarize_network_main as Network_Summary
#reload(Network_Summary)

# run Substation Model 
#Substation_Model.Substation_Calculation()

# run Network Summary 


#import MasterToSlaveVariables
#reload(MasterToSlaveVariables)
#import os
#import pandas as pd
#import globalVar as gV
#context = MasterToSlaveVariables.MasterSlaveVariables()


# run storage optimization
def slaveMain(pathX, fName_NetworkData, context, solarFeat, gV):
    """
    Main Slave Function, calls storage optimization and least cost optimization
    
    
    """
    t_zero = time.time()
    
    # run Storage Optimization
    Storage_Opt.Storage_Optimization(pathX, fName_NetworkData, context, gV)
    
    # run PP activation
    E_oil_eq_MJ, CO2_kg_eq, cost_sum, QUncoveredDesign, QUncoveredAnnual = Least_Cost.Least_Cost_Optimization(pathX, context, solarFeat, gV)
    
    #read Q_uncovered and design a PP for this, run it and cost it!
        
        
    t_end = time.time()
    print " ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- -----"
    print " Slave Optimization done (", round(t_end-t_zero,1)," seconds used for this task)"

    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, QUncoveredDesign, QUncoveredAnnual
    
    