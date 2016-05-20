Least_Cost_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/\
M_and_S/Slave/Slave_Subfunctions/Find_Least_Cost_Source"

Storage_Optimization_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/\
M_and_S/Slave/Slave_Subfunctions/Storage_Power_Operation_Losses_Partload"

Substation_Model_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Substation_Model/"

Network_Summary_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Summarize_Network_States/"


import os
os.chdir(Least_Cost_Path)
import Find_Least_Cost_Source_Main_V7_PresetOrder as Least_Cost
reload(Least_Cost)

os.chdir(Storage_Optimization_Path)
import Storage_Optimizer_incl_Losses_main_2 as Storage_Opt
reload(Storage_Opt)

os.chdir(Substation_Model_Path)
import substation_combined_main_V4_NOhextype_NewNames as Substation_Model
os.chdir(Substation_Model_Path)
reload(Substation_Model)

os.chdir(Network_Summary_Path)
import summarize_network_main as Network_Summary
reload(Network_Summary)

# run Substation Model 
Substation_Model.Substation_Calculation()

# run Network Summary 


def Slave_optimisation(input_path, output_path):
    """
    input_path : string
        contains summarized network data (hourly data, what the centralized PP sees)
        
    output_path : string
        contains the storage size file, activation pattern file
        
    """
    # run storage optimization
    Storage_Opt.Storage_Optimization(input_path)
    
    # run PP activation
    E_oil_eq_MJ, CO2_kg_eq, cost_sum = Least_Cost.Least_Cost_Optimization(output_path)
    
    
    return E_oil_eq_MJ, CO2_kg_eq, cost_sum 
