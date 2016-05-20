"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant

WORK IN PROCESS 

"""


# Mapping CC Cost


Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

import os
import numpy as np
os.chdir(Energy_Models_path)
import Model_CC as MCC
reload (MCC)
os.chdir(Energy_Models_path)
import globalVar as gV
reload(gV)
os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)
os.chdir(Energy_Models_path)

from scipy import interpolate

def CC_Find_Operation_Point_Functions(GT_SIZE, T_DH_Supply, fuel):
    """
    Retruns the Operation Point of CC for a requested Q_therm and its associated cost for every Q_therm
    
    How to use : input Q_therm_requested into the output function
                Conditions: not below or above boundaries Q_therm_min & Q_therm_max
                
    Parameters 
    ----------
    
    GT_SIZE : float
        Electric Size of Gas Turbine (only GT) 
        
    T_DH_Supply : float
        Supply Temperature of DH network
        
    fuel : string
        state either "NG" or "BG"
        
    
    Returns
    -------
    wdot_interpol : function
        interpolation function that is able to tell for every Q_therm_requested
        the required electric part load (wdot_required)
        
    Q_used_prim_interpol: function
        gives the primary energy used when asking for a thermal energy output
        
    cost_per_Wh_th_incl_el_interpol : interpol
        gives the cost per Wh energy used when asking for a thermal energy output

    Q_therm_min : float
        minimum thermal energy output possible
        
    Q_therm_max : float
        maximum thermal energy output possible

    
    """
    
    it_len = 50
    
    # create empty arrays
    wdotfin = np.zeros( it_len)
    qdot = np.zeros( it_len)
    eta_elec = np.zeros( it_len)
    eta_heat = np.zeros( it_len)
    Q_used_prim = np.zeros( it_len)
    cost_per_Wh_th_incl_el =  np.zeros( it_len)
    

    wdot_range = np.linspace(GT_SIZE*gV.GT_minload, GT_SIZE, it_len)
    qdot = np.zeros(it_len)
    
    for wdot_it in range(len(wdot_range)):

        wdot_in = wdot_range[wdot_it]
            
        CC_OpInfo = MCC.CC_Op(wdot_in, GT_SIZE, fuel, T_DH_Supply)
        
        wdotfin[wdot_it] = CC_OpInfo[0] # Electricity asked for
        qdot[wdot_it] = CC_OpInfo[1]     # Thermal output
        eta_elec[wdot_it] = CC_OpInfo[2]
        eta_heat[wdot_it] = CC_OpInfo[3]
        
        Q_used_prim[wdot_it] = CC_OpInfo[1] / CC_OpInfo[3] # = qdot  / eta_heat  
        cost_per_Wh_th_incl_el[wdot_it] = gV.NG_PRICE / CC_OpInfo[3] - CC_OpInfo[0] * gV.ELEC_PRICE / CC_OpInfo[1]  \
        # gV.NG_PRICE / eta_heat - wdotfin * gV.ELEC_PRICE / qdot

    wdot_interpol = interpolate.interp1d(qdot, wdot_range, kind = "linear")
    #wdot_required = Q_therm_interpol(Q_therm_request)
    Q_used_prim_interpol = interpolate.interp1d(qdot, Q_used_prim, kind = "linear")
    cost_per_Wh_th_incl_el_interpol = interpolate.interp1d(qdot, cost_per_Wh_th_incl_el, kind = "linear")

    Q_therm_min = min(qdot)
    Q_therm_max = max(qdot)
            
    return wdot_interpol, Q_used_prim_interpol, cost_per_Wh_th_incl_el_interpol, Q_therm_min, Q_therm_max
 
