"""
===============================
System Modeling: Combined cycle
===============================


"""
from __future__ import division
from math import log

import globalVar as gV
import numpy as np

reload (gV)

	
class ModelError(Exception):
    pass


def GT_fullLoadParam(gt_size, fuel):
    """
    Calculates parameters at full load
    
    Parameters
    ----------
    gt_size : float
        Maximum electric load that is demanded to the gas turbine
    fuel : string
        'NG' (natural gas) or 'BG' (biogas)
    
    Returns
    -------
    eta0 : float
        efficiency at full load
    mdot0 : float
        mass flow rate at full load of exhaust gas 
        
    """
    assert gt_size < gV.GT_maxSize + 0.001
    
    eta0 = 0.0196 * log(gt_size * 1E-3) + 0.1317
    
    if fuel == 'NG':
        LHV = gV.LHV_NG
    else:
        LHV = gV.LHV_BG
    
    mdotfuel = gt_size / (eta0 * LHV)
    
    if fuel == 'NG':
        mdot0 = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4  * 28E-3 + 200.5 * 32E-3 * (gV.CC_airratio - 1) + \
        200.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 1.8156
        
    else:
	mdot0 = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (gV.CC_airratio - 1) + \
	115.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 2.754
    
    return eta0, mdot0


def GT_partLoadParam(wdot, gt_size, eta0, mdot0, fuel):
    """
    Calculates parameters at part load
    
    Parameters
    ----------
    wdot : float
        Electric load that is demanded to the gas turbine
    gt_size : float
        size of the GAS turbine and NOT entire CC (P_el_max)
    eta0 : float
        efficiency at full load (electric)
    mdot0 : float
        mass flow rate of gas at full load
    fuel : string
        'NG' (natural gas) or 'BG' (biogas)
            
    Returns
    -------
    eta : float
        efficiency at part load (electr)
    mdot : float
        mass flow rate of exhaust at part load
    texh : float
        exhaust temperature
    mdotgas : float
        mass flow rate of gas needed (fuel)
        
    """
    assert wdot <= gt_size

    if fuel == 'NG':
        exitT = gV.CC_exitT_NG
        LHV = gV.LHV_NG
    else:
        exitT = gV.CC_exitT_BG
        LHV = gV.LHV_BG
    
    pload = wdot / gt_size
    if pload < gV.GT_minload:
        print pload
        print wdot
        print gt_size
        raise ModelError
    
    eta = (0.4089 + 0.9624 * pload - 0.3726 * pload ** 2) * eta0
    #mdot = (0.9934 + 0.0066 * pload) * mdot0
    texh = (0.7379 + 0.2621 * pload) * exitT
    mdotfuel = wdot / (eta * LHV)
    
    if fuel == 'NG':
        mdot = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4  * 28E-3 + 200.5 * 32E-3 * (gV.CC_airratio - 1) + \
        200.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 1.8156
        
    else:
	mdot = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (gV.CC_airratio - 1) + \
	115.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 2.754
    


    return eta, mdot, texh, mdotfuel


def ST_Op(mdot, texh, tDH, fuel):
    """
    Operation of a steam turbine connected to a district heating network
    
    Parameters
    ----------
    mdot : float
        mass flow rate of gas at the exit of the gas turbine
    texh : float
        temperature of the exhaust gas at the exit of the gas turbine
    tDH : float
        temperature of supply of the district heating network (hot)
    fuel : string
        'NG' (natural gas) or 'BG' (biogas)
        
    Returns
    -------
    qdot : float
        heat power transfered to the DHN
    wdotfin : float
        electric power from the steam cycle
    
    """
    temp_i = (0.9 * ((6/48.2) ** (0.4/1.4) - 1) + 1) * (texh - gV.ST_deltaT)
    
    if fuel == 'NG':
        Mexh = 103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * \
                (gV.CC_airratio -1) * 32E-3 + \
                200.5 * (gV.CC_airratio -1) * 3.773 * 28E-3
        ncp_exh = 103.7 * 44 * 0.846 + 196.2 * 18 * 1.8723 + \
                   761.4 * 28 * 1.039 + 200.5 * (gV.CC_airratio -1) * 32 * \
                   0.918 + 200.5 * (gV.CC_airratio -1) * 3.773 * 28 * 1.039 
        cp_exh = ncp_exh / Mexh # J/kgK
        
        
    else:
        Mexh = 98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * \
                (gV.CC_airratio -1) * 32E-3 + \
                115.5 * (gV.CC_airratio -1) * 3.773 * 28E-3
        ncp_exh = 98.5 * 44 * 0.846 + 116 * 18 * 1.8723 + \
                   436.8 * 28 * 1.039 + 115.5 * (gV.CC_airratio -1) * 32 * \
                   0.918 + 115.5 * (gV.CC_airratio -1) * 3.773 * 28 * 1.039 
        cp_exh = ncp_exh / Mexh # J/kgK
    
   
    a = np.array([[1653E3 + gV.cp * (texh - gV.ST_deltaT - 534.5), \
                gV.cp * (temp_i-534.5)], \
                [gV.cp * (534.5 - 431.8), \
                2085.8E3 + gV.cp * (534.5 - 431.8)]])
    b = np.array([mdot * cp_exh * (texh - (534.5 + gV.ST_deltaT)), \
                  mdot * cp_exh * (534.5 - 431.8)])
    [mdotHP, mdotLP] = np.linalg.solve(a,b)

    temp0 = tDH + gV.CC_deltaT_DH
    pres0 = (0.0261 * (temp0-273) ** 2 -2.1394 * (temp0-273) + 52.893) * 1E3
    
    deltaHevap = (-2.4967 * (temp0-273) + 2507) * 1E3
    qdot = (mdotHP + mdotLP) * deltaHevap
    
    #temp_c = (0.9 * ((pres0/48.2E5) ** (0.4/1.4) - 1) + 1) * (texh - gV.ST_deltaT)
    #qdot = (mdotHP + mdotLP) * (gV.cp * (temp_c - temp0) + deltaHevap)
    #presSTexit = pres0 + gV.ST_deltaP
    #wdotST = 0.9 / 18E-3 * 1.4 / 0.4 * 8.31 * \
    #         (mdotHP * 534.5 * ( (6/48.2) ** (0.4/1.4) - 1 )\
    #         + (mdotLP + mdotHP) * temp_i * ( (presSTexit/6E5) ** (0.4/1.4) - 1 ) )
    #
    #temp1 = (((6E5/pres0) ** (0.4/1.4) - 1) / 0.87 + 1) * temp0
    #wdotcomp = 0.87 / 18E-3 * 1.4 / 0.4 * 8.31 * \
    #           (mdotHP * temp1 * ( (48.2/6) ** (0.4/1.4) - 1 )\
    #           + (mdotHP + mdotLP) * temp0 * ( (6E5/pres0) ** (0.4/1.4) - 1 ))
    
    
    h_HP = (2.5081 * (texh - gV.ST_deltaT - 273) + 2122.7) * 1E3 #J/kg
    h_LP = (2.3153 * (temp_i - 273) + 2314.7) * 1E3 #J/kg
    h_cond = (1.6979 * (temp0 - 273) + 2506.6) * 1E3 #J/kg
    spec_vol = 0.0010 #m3/kg
    
    wdotST = mdotHP * (h_HP - h_LP) + (mdotHP + mdotLP) * (h_LP - h_cond)
    wdotcomp = spec_vol * (mdotLP * (6E5 - pres0) + (mdotHP + mdotLP) * (48.2E5 - 6E5))

    wdotfin = gV.STGen_eta * (wdotST-wdotcomp)

    return qdot, wdotfin


def CC_Op(wdot, gt_size, fuel, tDH) :
    """
    Operation Function of Combined Cycle, asking for electricity Demand.
    
    Parameters
    ----------
    wdot : float
        Electric load that is demanded to the gas turbine (only GT output, not CC output!)
    gt_size : float
        size of the GAS turbine and NOT CC (P_el_max)
    fuel : string
        'NG' (natural gas) or 'BG' (biogas)
    tDH : float
        temperature of supply of the district heating network (hot)

        
    Returns
    -------
    wdotfin : float
        electric power from the steam cycle
    qdot : float
        heat power transfered to the DHN
    eta_elec : float
        total electric efficiency
    eta_heat : float
        total thermal efficiency
    eta_all : float
        sum of total electric and thermal efficiency
    
    """
    
    (eta0, mdot0) = GT_fullLoadParam(gt_size, fuel)
    (eta, mdot, texh, mdotgas) = GT_partLoadParam(wdot, gt_size, eta0, mdot0, fuel)
    (qdot, wdotfin) = ST_Op(mdot, texh, tDH, fuel)
    
    if fuel == 'NG':
        LHV = gV.LHV_NG
    else:
        LHV = gV.LHV_BG
        
    eta_elec = (wdot + wdotfin) / (mdotgas * LHV)
    eta_heat = qdot / (mdotgas * LHV)
    eta_all = eta_elec + eta_heat
    wtot = wdotfin + wdot 
    return wtot, qdot, eta_elec, eta_heat, eta_all
    

def CC_InvC(CC_size):
    """
    Annualized investment costs for the Combined cycle
    
    Parameters
    ----------
    CC_size : float
        Electrical size of the CC
        
    Returns
    -------
    InvCa : float
        annualized investment costs in CHF
    
    """
    InvC = 32978 * (CC_size * 1E-3) ** 0.5946
    InvCa = InvC * gV.CC_i * (1+ gV.CC_i) ** gV.CC_n / \
            ((1+gV.CC_i) ** gV.CC_n - 1)

    return InvCa










