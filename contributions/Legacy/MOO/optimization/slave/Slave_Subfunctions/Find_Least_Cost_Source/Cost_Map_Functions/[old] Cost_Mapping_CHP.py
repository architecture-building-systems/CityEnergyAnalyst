"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant
"""


# Mapping Furnace Cost

import os
#import numpy as np
#os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models")
import EnergySystem_Models.Model_Furnace as MF
import globalVar as gV
#reload (gV)
reload (MF)


def CC_op_cost(Q_therm, Q_design, T_return_to_boiler, MOIST_TYPE):
    """ 
    Calculates the operation cost of a CC plant (only operation, no annualized cost!)
    
    
    
    Parameters
    ----------
    P_design : float
        Design Power of Furnace Plant (Boiler Thermal power!!)
        
    Q_annual : float
        annual thermal Power output
    
    Returns
    -------
    C_furn : float
        Total generation cost for required load (per hour) in CHF
    
    c_furn_per_kWh : float
        cost per kWh in Rp / kWh
     
    Q_primary : float
        required thermal energy per hour (in Wh of wood chips) 
    """
    
    #if Q_load / Q_design < 0.3:
    #    raise ModelError
    """ Iterating for efficiency as Q_thermal_required is given as input """
    eta_therm_in = 0.5
    eta_therm_real = 1.0
    i = 0
    
    while 0.999 >= abs(eta_therm_in/eta_therm_real): # Iterating for thermal efficiency and required load
        if i != 0:
            eta_therm_in = eta_therm_real 
        i += 1
        Q_load = Q_therm / eta_therm_real # primary energy needed
        if Q_design < Q_load:
            Q_load = Q_design - 1
        
        Furnace_eff = MF.Furnace_eff(Q_load, Q_design, T_return_to_boiler)
        eta_therm_real, eta_el, Q_aux = Furnace_eff
        if eta_therm_real == 0:
            print "error found"
            break

        
    if MOIST_TYPE == "dry":
        C_furn_therm = Q_load / eta_therm_real * gV.Furn_FuelCost_dry #  CHF / Wh - cost of thermal energy
        C_furn_el_sold = Q_load * eta_el * gV.ELEC_PRICE #  CHF / Wh  - directly sold to the grid, as a cost gain
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_kWh = C_furn / Q_therm

        
    else:
        C_furn_therm = Q_therm * 1 / eta_therm_real * gV.Furn_FuelCost_wet 
        C_furn_el_sold = (Q_load * eta_el - Q_aux) * gV.ELEC_PRICE
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_kWh = C_furn / Q_therm * 100 * 1000.0 # in Rp / kWh
    
    Q_primary = Q_load
    
    return C_furn, C_furn_per_kWh, Q_primary


    