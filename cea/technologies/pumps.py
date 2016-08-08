# -*- coding: utf-8 -*-
"""
============================
pumps
============================

"""
from __future__ import division
import os
import pandas as pd
from scipy.interpolate import interp1d
import numpy as np


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""
============================
operation and total costs
============================

"""

def Pump_operation(P_design):

    """
    Modeled after:
        05_merkblatt_wirtschaftlichkeit_14.pdf
        23_merkblatt_pumpen_web.pdf
        ER_2010_11_Heizungspumpen.pdf
        MerkblattPreiseFU2010_2011.pdf
        MerkblattPreiseMotoren2010_2011.pdf

    Parameters
    ----------
    P_design : float
        Load of time step

    Returns
    -------
    eta_el : float
        electric efficiency of Pumping operation in abs. numbers (e.g. 0.93)




    """

    x = [0.5, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220] # Nominal load in kW
    y = [83, 83.5, 84, 85.2, 86.8, 87.8, 88.8, 89.5, 90.5, 91.5, 92.2, 92.6, 93, 93.6, 93.9, 94.3, 94.6, 95, 95.2, 95.4, 95.6, 95.9, 96,96] # efficiency in %
        # do the interpolation
    eff_of_Pmax = interp1d(x, y, kind='cubic')
    eta_motor = eff_of_Pmax(float(P_design) / float(100))
    eta_pump_fluid = 0.8
    eta_pumping = eta_pump_fluid * eta_motor
    return eta_pumping, eta_pump_fluid, eta_motor


def calc_Ctot_pump(dicoSupply, buildList, pathNtwRes, ntwFeat, gV):
    """
    Computes the pumping costs
    
    Parameters
    ----------
    dicoSupply : class context
    buildList : list
        list of buildings in the district
    pathNtwRes : string
        path to ntw results folder
    ntwFeat : class ntwFeatures
    
    Returns
    -------
    pumpCosts : float
    
    """    
    pumpCosts = 0
    #nBuild = dicoSupply.nBuildingsConnected
    #ntot = len(buildList)
    
    os.chdir(pathNtwRes)
    if 1:
        pumpCosts = 0
        #nBuild = dicoSupply.nBuildingsConnected
        #ntot = len(buildList)
        
        os.chdir(pathNtwRes)
        df = pd.read_csv(dicoSupply.NETWORK_DATA_FILE, usecols=["mdot_DH_netw_total"])
        mdotA = np.array(df)
        mdotnMax = np.amax(mdotA)
        
        #mdot0Max = np.amax( np.array( pd.read_csv("Network_summary_result_all.csv", usecols=["mdot_heat_netw_total"]) ) )
        
        for i in range(int(np.shape(mdotA)[0])):
            deltaP = 2* (104.81 * mdotA[i][0] + 59016)
            pumpCosts += deltaP * mdotA[i][0] / 1000 * gV.ELEC_PRICE / gV.etaPump
            deltaPmax = ntwFeat.DeltaP_DHN
            
        investCosts = calc_Cinv_pump(deltaPmax, mdotnMax, gV.etaPump, gV) # investment of Machinery
        pumpCosts += investCosts
        
    print pumpCosts, " CHF - pump costs in pumps.py"
    
    return pumpCosts


def Pump_Cost(deltaP, mdot, eta_pumping, gV):
    """
    calculates the cost of a pumping device.
    if the nominal load (electric) is above 375kW, a second pump is assumed
    if the nominal load (electric) is below 500W, a pump with Pel_design = 500W is assumed

    Investement costs are calculated upon the life time of a GHP ( 20y) and a GHP- related interest rate of 6%

    Parameters
    ----------
    deltaP : float
        Pressure drop that has to be overcome with the pump (nominal)

    mdot : float
        mass flow (nominal)

    eta_pumping : float
        pump efficiency (set 0.8 as standard value, eta = E_pumping / E_elec)

    Returns
    -------
    InvC_return : float
        total investment Cost in CHF

    InvCa : float
        annualized investment costs in CHF/year

    """

    E_pumping_required = mdot * deltaP /gV.rho_60
    P_motor_tot = E_pumping_required / eta_pumping

    PmaxPumpkW = 375.0
    PpumpMinkW = 0.5

    nPumps = int(np.ceil(P_motor_tot / 1000.0 / PmaxPumpkW))

    PpumpArray = np.zeros((nPumps))
    PpumpRemain = P_motor_tot

    #if PpumpRemain < PpumpMinkW * 1000:
     #   PpumpRemain = PpumpMinkW * 1000


    x = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
    y = [630, 580, 500, 420, 350, 315, 285, 260, 240, 220, 210, 205, 195, 190, 185, 182, 180, 176, 175, 174, 173, 170, 169, 168, 167, 165, 162, 161.9] # efficiency in %
        # do the interpolation
    x1 = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
    y1 = [720, 680, 585, 425, 330, 275, 220, 195, 180, 150, 145, 143, 135, 120, 115, 114, 110, 100, 90, 88, 85, 80, 75, 74, 74, 73, 72, 71.9] # efficiency in %
    InvC_mot= interp1d(x, y, kind='cubic')
    InvC_VFC = interp1d(x1, y1, kind='cubic')

    InvC = 0.0
    InvCa = 0.0

    for pump_i in range(nPumps):
        # calculate pump nominal capacity

        PpumpArray[pump_i] =  min(PpumpRemain, PmaxPumpkW*1000)
        if PpumpArray[pump_i] < PpumpMinkW * 1000:
            PpumpArray[pump_i] = PpumpMinkW * 1000
        PpumpRemain -= PpumpArray[pump_i]

        # Calculate cost
        InvC += InvC_mot(PpumpArray[pump_i]/1000.0) + InvC_VFC(PpumpArray[pump_i]/1000.0)
        InvCa +=  InvC * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / ((1+gV.GHP_i) ** gV.GHP_nHP - 1)

    return InvCa

"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_pump(deltaP, mdot, eta_pumping, gV):
    """
    calculates the cost of a pumping device.
    if the nominal load (electric) is above 375kW, a second pump is assumed
    if the nominal load (electric) is below 500W, a pump with Pel_design = 500W is assumed

    Investement costs are calculated upon the life time of a GHP ( 20y) and a GHP- related interest rate of 6%

    ParametersF
    ----------
    deltaP : float
        Pressure drop that has to be overcome with the pump (nominal)

    mdot : float
        mass flow (nominal)

    eta_pumping : float
        pump efficiency (set 0.8 as standard value, eta = E_pumping / E_elec)

    Returns
    -------
    InvC_return : float
        total investment Cost in CHF

    InvCa : float
        annualized investment costs in CHF/year

    """

    E_pumping_required = mdot * deltaP /gV.rho_60
    P_motor_tot = E_pumping_required / eta_pumping

    PmaxPumpkW = 375.0
    PpumpMinkW = 0.5
    print P_motor_tot
    print PmaxPumpkW
    nPumps = int(np.ceil(P_motor_tot / 1000.0 / PmaxPumpkW))

    print nPumps," nPumps"

    PpumpArray = np.zeros((nPumps))
    PpumpRemain = P_motor_tot

    #if PpumpRemain < PpumpMinkW * 1000:
     #   PpumpRemain = PpumpMinkW * 1000


    x = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
    y = [630, 580, 500, 420, 350, 315, 285, 260, 240, 220, 210, 205, 195, 190, 185, 182, 180, 176, 175, 174, 173, 170, 169, 168, 167, 165, 162, 161.9] # efficiency in %
        # do the interpolation
    x1 = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
    y1 = [720, 680, 585, 425, 330, 275, 220, 195, 180, 150, 145, 143, 135, 120, 115, 114, 110, 100, 90, 88, 85, 80, 75, 74, 74, 73, 72, 71.9] # efficiency in %
    InvC_mot= interp1d(x, y, kind='cubic')
    InvC_VFC = interp1d(x1, y1, kind='cubic')

    InvC = 0.0
    InvCa = 0.0

    for pump_i in range(nPumps):
        # calculate pump nominal capacity

        PpumpArray[pump_i] =  min(PpumpRemain, PmaxPumpkW*1000)
        if PpumpArray[pump_i] < PpumpMinkW * 1000:
            PpumpArray[pump_i] = PpumpMinkW * 1000
        PpumpRemain -= PpumpArray[pump_i]

        # Calculate cost
        InvC += InvC_mot(PpumpArray[pump_i]/1000.0) + InvC_VFC(PpumpArray[pump_i]/1000.0)
        InvCa +=  InvC * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / ((1+gV.GHP_i) ** gV.GHP_nHP - 1)

    return InvCa

