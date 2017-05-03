"""
cogeneration (combined heat and power)
"""

from __future__ import division
import numpy as np
from scipy import interpolate
import scipy

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



#===========================
#Combined Cycle Gas Turbine
#===========================


def calc_Cop_CCT(GT_SIZE, T_DH_Supply, fuel, gV):
    """
    The function iterate the CCT operation between its nominal capacity and minimum load and generate linear functions of
    the GT operation.

    This generated function calculates Operation Point and associated costs of the cogeneration at given
    thermal load (Q_therm_requested).

    How to use the return functions : input Q_therm_requested into the output interpolation functions
    Conditions: not below or above boundaries Q_therm_min & Q_therm_max

    :type GT_SIZE : float
    :param GT_SIZE: Nominal capacity of Gas Turbine (only GT not cogeneration)

    :type T_DH_Supply : float
    :param T_DH_Supply: CHP plant supply temperature to DHN

    :type fuel : string
    :param fuel: type of fuel, either "NG" or "BG"

    :param gV: globalvar.py


    :rtype wdot_interpol : function
    :returns wdot_interpol: interpolation function for part load electricity requirement for given Q_therm_requested

    :rtype Q_used_prim_interpol: function
    :returns Q_used_prim_interpol: interpolation function, primary energy used for given Q_therm_requested

    :rtype cost_per_Wh_th_incl_el_interpol : function
    :returns cost_per_Wh_th_incl_el_interpol: interpolation function, operation cost per thermal energy generated at Q_therm_requested

    :rtype Q_therm_min : float
    :returns Q_therm_min: minimum thermal energy output

    :rtype Q_therm_max : float
    :returns Q_therm_max: maximum thermal energy output

    :rtype eta_elec_interpol: function
    :returns eta_elec_interpol: interpolation function, electrical efficiency at Q_therm_requested


    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """

    it_len = 50

    # create empty arrays

    wdotfin = np.zeros( it_len)
    qdot = np.zeros( it_len)
    eta_elec = np.zeros( it_len)
    eta_heat = np.zeros( it_len)
    Q_used_prim = np.zeros( it_len)
    cost_per_Wh_th_incl_el =  np.zeros( it_len)

    # create range of electricity output from the GT between the minimum and nominal load
    wdot_range = np.linspace(GT_SIZE * gV.GT_minload, GT_SIZE, it_len)

    # calculate the operation data at different electricity load
    for wdot_it in range(len(wdot_range)):
        wdot_in = wdot_range[wdot_it]

        # combine cycle operation
        CC_OpInfo = CC_Op(wdot_in, GT_SIZE, fuel, T_DH_Supply, gV)
        wdotfin[wdot_it] = CC_OpInfo[0]  # Electricity output from the combined cycle
        qdot[wdot_it] = CC_OpInfo[1]     # Thermal output from the combined cycle
        eta_elec[wdot_it] = CC_OpInfo[2] # el. efficiency
        eta_heat[wdot_it] = CC_OpInfo[3] # thermal efficiency

        Q_used_prim[wdot_it] = qdot[wdot_it] / eta_heat[wdot_it]    # primary energy input
        cost_per_Wh_th_incl_el[wdot_it] = (gV.NG_PRICE / eta_heat[wdot_it] - wdotfin[wdot_it] * gV.ELEC_PRICE) / qdot[wdot_it]

    # create interpolation functions
    wdot_interpol = interpolate.interp1d(qdot, wdot_range, kind = "linear")
    Q_used_prim_interpol = interpolate.interp1d(qdot, Q_used_prim, kind = "linear")
    cost_per_Wh_th_incl_el_interpol = interpolate.interp1d(qdot, cost_per_Wh_th_incl_el, kind = "linear")
    eta_elec_interpol = interpolate.interp1d(Q_used_prim, eta_elec, kind = "linear")

    Q_therm_min = min(qdot)
    Q_therm_max = max(qdot)

    return wdot_interpol, Q_used_prim_interpol, cost_per_Wh_th_incl_el_interpol, Q_therm_min, Q_therm_max, eta_elec_interpol

def CC_Op(wdot, gt_size, fuel, tDH, gV) :
    """
    Operation Function of Combined Cycle at given electricity Demand (wdot).
    The gas turbine (GT) exhaust gas is used by the steam turbine (ST).

    :type wdot : float
    :param wdot: Electric load that is demanded to the gas turbine (only GT output, not CC output!)
    :type gt_size : float
    :param gt_size: size of the gas turbine and (not CC)(P_el_max)
    :type fuel : string
    :param fuel: fuel used, either 'NG' (natural gas) or 'BG' (biogas)
    :type tDH : float
    :param tDH: plant supply temperature to district heating network (hot)
    :param gV: globalvar.py


    :rtype wtot : float
    :returns wtot: total electric power output from the combined cycle (both GT + ST !)
    :rtype qdot : float
    :returns qdot: thermal output from teh combined cycle
    :rtype eta_elec : float
    :returns eta_elec: total electric efficiency
    :rtype eta_heat : float
    :returns eta_heat: total thermal efficiency
    :rtype eta_all : float
    :returns eta_all: sum of total electric and thermal efficiency

    """

    (eta0, mdot0) = GT_fullLoadParam(gt_size, fuel, gV)
    (eta, mdot, texh, mdotfuel) = GT_partLoadParam(wdot, gt_size, eta0, mdot0, fuel, gV)
    (qdot, wdotfin) = ST_Op(mdot, texh, tDH, fuel, gV)

    if fuel == 'NG':
        LHV = gV.LHV_NG
    else:
        LHV = gV.LHV_BG

    eta_elec = (wdot + wdotfin) / (mdotfuel * LHV)
    eta_heat = qdot / (mdotfuel * LHV)
    eta_all = eta_elec + eta_heat
    wtot = wdotfin + wdot

    return wtot, qdot, eta_elec, eta_heat, eta_all

def GT_fullLoadParam(gt_size, fuel, gV):
    """
    Calculates gas turbine efficiency and exhaust gas mass flow rate at full load.

    :type gt_size : float
    :param gt_size: Maximum electric load that is demanded to the gas turbine
    :type fuel : string
    :param fuel: fuel used, either NG (Natural Gas) or BG (Biogas)
    :param gV: globalvar.py

    :rtype eta0 : float
    :returns eta0: efficiency at full load
    :rtype mdot0 : float
    :returns mdot0: exhaust gas mass flow rate at full load

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    assert gt_size < gV.GT_maxSize + 0.001
    if gt_size == 0:
        eta0 = 0.01
    else:
        eta0 = 0.0196 * scipy.log(gt_size * 1E-3) + 0.1317  # [C. Weber, 2008]_

    if fuel == 'NG':
        LHV = gV.LHV_NG
    else:
        LHV = gV.LHV_BG

    mdotfuel = gt_size / (eta0 * LHV)

    if fuel == 'NG':
        mdot0 = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4  * 28E-3 + 200.5 * 32E-3 * (gV.CC_airratio - 1) +
                 200.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 1.8156
    else:
        mdot0 = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (gV.CC_airratio - 1) +
                 115.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 2.754

    return eta0, mdot0

def GT_partLoadParam(wdot, gt_size, eta0, mdot0, fuel, gV):
    """
    Calculates GT operational parameters at part load

    :type wdot : float
    :param wdot: GT electric output (load)
    :type gt_size : float
    :param gt_size: Maximum electric load that is demanded to the gas turbine
    :type eta0 : float
    :param eta0: GT part-load electric efficiency
    :type mdot0 : float
    :param mdot0: GT part-load exhaust gas mass flow
    :type fuel : string
    :param fuel: fuel used, either 'NG' (natural gas) or 'BG' (biogas)


    :rtype eta : float
    :returns eta: GT part-load electric efficiency
    :rtype mdot : float
    :returns mdot: GT part-load exhaust gas mass flow rate
    :rtype texh : float
    :returns texh: exhaust gas temperature
    :rtype mdotfuel : float
    :returns mdotfuel: mass flow rate of fuel(gas) requirement


    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL

    """
    assert wdot <= gt_size

    if fuel == 'NG':
        exitT = gV.CC_exitT_NG
        LHV = gV.LHV_NG
    else:
        exitT = gV.CC_exitT_BG
        LHV = gV.LHV_BG

    pload = (wdot + 1) / gt_size # avoid calculation errors
    if pload < gV.GT_minload:
        print pload
        print wdot
        print gt_size
        raise ModelError

    eta = (0.4089 + 0.9624 * pload - 0.3726 * pload ** 2) * eta0  # [C. Weber, 2008]_
    #mdot = (0.9934 + 0.0066 * pload) * mdot0
    texh = (0.7379 + 0.2621 * pload) * exitT
    mdotfuel = wdot / (eta * LHV)

    if fuel == 'NG':
        mdot = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4  * 28E-3 + 200.5 * 32E-3 * (gV.CC_airratio - 1) +
                200.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 1.8156

    else:
        mdot = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (gV.CC_airratio - 1) + \
                115.5 * 3.773 * 28E-3 * (gV.CC_airratio - 1) ) * mdotfuel / 2.754

    return eta, mdot, texh, mdotfuel

def ST_Op(mdot, texh, tDH, fuel, gV):
    """
    Operation of a double pressure (LP,HP) steam turbine connected to a district heating network following
    [C. Weber, 2008]_

    :type mdot : float
    :param mdot: GT part-load exhaust gas mass flow rate
    :type texh : float
    :param texh: GT exhaust gas temperature
    :type tDH : float
    :param tDH: plant supply temperature to district heating network (hot)
    :param fuel: fuel used, either 'NG' (natural gas) or 'BG' (biogas)
    :type tDH : float
    :param gV: globalvar.py

    :rtype qdot : float
    :returns qdot: heat power supplied to the DHN
    :rtype wdotfin : float
    :returns wdotfin: electric power generated from the steam cycle

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL

    """

    temp_i = (0.9 * ((6/48.2) ** (0.4/1.4) - 1) + 1) * (texh - gV.ST_deltaT)
    if fuel == 'NG':
        Mexh = 103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * \
                                                               (gV.CC_airratio - 1) * 32E-3 + \
               200.5 * (gV.CC_airratio - 1) * 3.773 * 28E-3
        ncp_exh = 103.7 * 44 * 0.846 + 196.2 * 18 * 1.8723 + \
                  761.4 * 28 * 1.039 + 200.5 * (gV.CC_airratio - 1) * 32 * \
                                       0.918 + 200.5 * (gV.CC_airratio - 1) * 3.773 * 28 * 1.039
        cp_exh = ncp_exh / Mexh  # J/kgK


    else:
        Mexh = 98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * \
                                                            (gV.CC_airratio - 1) * 32E-3 + \
               115.5 * (gV.CC_airratio - 1) * 3.773 * 28E-3
        ncp_exh = 98.5 * 44 * 0.846 + 116 * 18 * 1.8723 + \
                  436.8 * 28 * 1.039 + 115.5 * (gV.CC_airratio - 1) * 32 * \
                                       0.918 + 115.5 * (gV.CC_airratio - 1) * 3.773 * 28 * 1.039
        cp_exh = ncp_exh / Mexh  # J/kgK

    a = np.array([[1653E3 + gV.cp * (texh - gV.ST_deltaT - 534.5), \
                   gV.cp * (temp_i - 534.5)], \
                  [gV.cp * (534.5 - 431.8), \
                   2085.8E3 + gV.cp * (534.5 - 431.8)]])
    b = np.array([mdot * cp_exh * (texh - (534.5 + gV.ST_deltaT)), \
                  mdot * cp_exh * (534.5 - 431.8)])
    [mdotHP, mdotLP] = np.linalg.solve(a, b)   # HP and LP mass flow of a double pressure steam turbine

    temp0 = tDH + gV.CC_deltaT_DH    # condensation temperature constrained by the DH network temperature
    pres0 = (0.0261 * (temp0-273) ** 2 -2.1394 * (temp0-273) + 52.893) * 1E3

    deltaHevap = (-2.4967 * (temp0-273) + 2507) * 1E3
    qdot = (mdotHP + mdotLP) * deltaHevap       # thermal output of ST


    # temp_c = (0.9 * ((pres0/48.2E5) ** (0.4/1.4) - 1) + 1) * (texh - gV.ST_deltaT)
    # qdot = (mdotHP + mdotLP) * (gV.cp * (temp_c - temp0) + deltaHevap)
    # presSTexit = pres0 + gV.ST_deltaP
    # wdotST = 0.9 / 18E-3 * 1.4 / 0.4 * 8.31 * \
    #         (mdotHP * 534.5 * ( (6/48.2) ** (0.4/1.4) - 1 )\
    #         + (mdotLP + mdotHP) * temp_i * ( (presSTexit/6E5) ** (0.4/1.4) - 1 ) )
    #
    # temp1 = (((6E5/pres0) ** (0.4/1.4) - 1) / 0.87 + 1) * temp0
    # wdotcomp = 0.87 / 18E-3 * 1.4 / 0.4 * 8.31 * \
    #           (mdotHP * temp1 * ( (48.2/6) ** (0.4/1.4) - 1 )\
    #           + (mdotHP + mdotLP) * temp0 * ( (6E5/pres0) ** (0.4/1.4) - 1 ))


    h_HP = (2.5081 * (texh - gV.ST_deltaT - 273) + 2122.7) * 1E3  # J/kg
    h_LP = (2.3153 * (temp_i - 273) + 2314.7) * 1E3  # J/kg
    h_cond = (1.6979 * (temp0 - 273) + 2506.6) * 1E3  # J/kg
    spec_vol = 0.0010  # m3/kg

    wdotST = mdotHP * (h_HP - h_LP) + (mdotHP + mdotLP) * (h_LP - h_cond)  # turbine electricity output
    wdotcomp = spec_vol * (mdotLP * (6E5 - pres0) + (mdotHP + mdotLP) * (48.2E5 - 6E5))  # compressor electricity use

    wdotfin = gV.STGen_eta * ( wdotST - wdotcomp )  # gross electricity production of turbine

    return qdot, wdotfin


#===========================
#Fuel Cell
#===========================

def calc_eta_FC(Q_load, Q_design, phi_threshold, approach_call):
    """
    Efficiency for operation of a SOFC (based on LHV of NG) including all auxiliary losses
    Valid for Q_load in range of 1-10 [kW_el]

    Modeled after:
        Approach A (NREL Approach):
            http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
            and
            NREL : p.5  of [M. Zolot et al., 2004]_

        Approach B (Empiric Approach): [Iain Staffell]_


    :type Q_load : float
    :param Q_load: Load at each time step

    :type Q_design : float
    :param Q_design: Design Load of FC

    :type phi_threshold : float
    :param phi_threshold: where Maximum Efficiency is reached, used for Approach A

    :type approach_call : string
    :param appraoch_call: choose "A" or "B": A = NREL-Approach, B = Empiric Approach

    :rtype eta_el : float
    :returns eta_el: electric efficiency of FC (Lower Heating Value), in abs. numbers

    :rtype Q_fuel : float
    :returns Q_fuel: Heat demand from fuel (in Watt)

    ..[M. Zolot et al., 2004] M. Zolot et al., Analysis of Fuel Cell Hybridization and Implications for Energy Storage
    Devices, NREL, 4th International Advanced Automotive Battery.
    http://www.nrel.gov/vehiclesandfuels/energystorage/pdfs/36169.pdf

    ..[Iain Staffell, 2009] Iain Staffell, For Domestic Heat and Power: Are They Worth It?, PhD Thesis, Birmingham:
    University of Birmingham. http://etheses.bham.ac.uk/641/1/Staffell10PhD.pdf
    """
    phi = 0.0

    ## Approach A - NREL Approach
    if approach_call == "A":

        phi = float( Q_load ) / float( Q_design )
        eta_max = 0.425 # from energy.gov

        if phi >= phi_threshold:  # from NREL-Shape
            eta_el = eta_max - ((1 / 6.0 * eta_max) / (1.0 - phi_threshold)) * abs(phi - phi_threshold)

        if phi < phi_threshold:
            if phi <= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3 * ( phi / ( phi_threshold * 118 / 520.0 ) )

            if phi < 0.5 * phi_threshold and phi >= 118 / 520.0 * phi_threshold:
                eta_el = eta_max * 2/3.0 + \
                         eta_max * 0.25 * ( phi-phi_threshold * 118/520.0) / ( phi_threshold * (0.5 - 118/520.0 ) )

            if phi > 0.5 * phi_threshold and phi < phi_threshold:
                eta_el = eta_max * ( 2/3.0 + 0.25 ) + \
                         1/12.0 * eta_max * ( phi - phi_threshold * 0.5) / (phi_threshold * (1-0.5))

        eta_therm_max = 0.45  # constant, after energy.gov

        if phi < phi_threshold:
            eta_therm = 0.5 * eta_therm_max * (phi / phi_threshold)

        else:
            eta_therm = 0.5 * eta_therm_max * (1 + eta_therm_max * ((phi - phi_threshold) / (1 - phi_threshold)))

    ## Approach B - Empiric Approach
    if approach_call == "B":

        if Q_design > 0:
            phi = float(Q_load) / float(Q_design)

        else:
            phi = 0

        eta_el_max = 0.39
        eta_therm_max = 0.58   #* 1.11 as this source gives eff. of HHV
        eta_el_score = -0.220 + 5.277 * phi - 9.127 * phi**2 + 7.172* phi ** 3 - 2.103* phi**4
        eta_therm_score = 0.9 - 0.07 * phi + 0.17 * phi**2

        eta_el = eta_el_max * eta_el_score
        eta_therm = eta_therm_max * eta_therm_score

        if phi < 0.2:
            eta_el = 0

    return eta_el, eta_therm


# investment and maintenance costs

def calc_Cinv_CCT(CC_size, gV):
    """
    Annualized investment costs for the Combined cycle

    :type CC_size : float
    :param CC_size: Electrical size of the CC

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in CHF

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """

    InvC = 32978 * (CC_size * 1E-3) ** 0.5967  # [C. Weber, 2008]_
    InvCa = InvC * gV.CC_i * (1+ gV.CC_i) ** gV.CC_n / ((1+gV.CC_i) ** gV.CC_n - 1)

    return InvCa


def calc_Cinv_FC(P_design, gV):
    """
    Calculates the investment cost of a Fuel Cell in CHF

    http://hexis.com/sites/default/files/media/publikationen/140623_hexis_galileo_ibb_profitpaket.pdf?utm_source=HEXIS+Mitarbeitende&utm_campaign=06d2c528a5-1_Newsletter_2014_Mitarbeitende_DE&utm_medium=email&utm_term=0_e97bc1703e-06d2c528a5-

    :type P_design : float
    :param P_design: Design thermal Load of Fuel Cell [W_th]

    :rtype InvCa: float
    :returns InvCa: annualized investment costs in CHF
    """

    InvC = (1 + gV.FC_overhead) * gV.FC_stack_cost * P_design / 1000 # FC_stack_cost = 55'000 CHF  / kW_therm, 10 % extra (overhead) cost
    InvCa = InvC * gV.FC_i * (1 + gV.FC_i) ** gV.FC_n / (( 1 + gV.FC_i) ** gV.FC_n - 1)

    return InvCa
