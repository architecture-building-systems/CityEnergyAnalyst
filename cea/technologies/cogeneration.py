"""
cogeneration (combined heat and power)
"""

from __future__ import division
import numpy as np
from scipy import interpolate
import scipy
import pandas as pd
from math import log
from cea.optimization.constants import *


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


def calc_Cop_CCT(GT_SIZE_W, T_DH_Supply_K, fuel, gV, prices):
    """
    This function calcualates the COP of a combined cycle, the gas turbine (GT) exhaust gas is used by
    the steam turbine (ST) to generate electricity and heat.
    This function iterates the combined cycle operation between its nominal capacity and minimum load and generate
    linear functions of the GT operation.

    The generated function calculates operation points and associated costs of the cogeneration at given
    thermal load (Q_therm_requested).

    How to use the return functions : input Q_therm_requested into the output interpolation functions
    Conditions: not below or above boundaries Q_therm_min & Q_therm_max

    :type GT_SIZE_W : float
    :param GT_SIZE_W: Nominal capacity of Gas Turbine (only GT not cogeneration)

    :type T_DH_Supply_K : float
    :param T_DH_Supply_K: CHP plant supply temperature to DHN

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

    wdotfin_W = np.zeros( it_len)
    qdot_W = np.zeros( it_len)
    eta_elec = np.zeros( it_len)
    eta_heat = np.zeros( it_len)
    Q_used_prim_W = np.zeros( it_len)
    cost_per_Wh_th_incl_el =  np.zeros( it_len)

    # create range of electricity output from the GT between the minimum and nominal load
    wdot_range_W = np.linspace(GT_SIZE_W * GT_minload, GT_SIZE_W, it_len)

    # calculate the operation data at different electricity load
    for wdot_it in range(len(wdot_range_W)):
        wdot_in_W = wdot_range_W[wdot_it]

        # combine cycle operation
        CC_OpInfo = CC_Op(wdot_in_W, GT_SIZE_W, fuel, T_DH_Supply_K, gV)
        wdotfin_W[wdot_it] = CC_OpInfo[0]  # Electricity output from the combined cycle
        qdot_W[wdot_it] = CC_OpInfo[1]     # Thermal output from the combined cycle
        eta_elec[wdot_it] = CC_OpInfo[2] # el. efficiency
        eta_heat[wdot_it] = CC_OpInfo[3] # thermal efficiency

        Q_used_prim_W[wdot_it] = qdot_W[wdot_it] / eta_heat[wdot_it]    # primary energy input
        cost_per_Wh_th_incl_el[wdot_it] = (prices.NG_PRICE / eta_heat[wdot_it] - wdotfin_W[wdot_it] * prices.ELEC_PRICE) / qdot_W[wdot_it]

    # create interpolation functions
    wdot_interpol_W = interpolate.interp1d(qdot_W, wdot_range_W, kind = "linear")
    Q_used_prim_interpol_W = interpolate.interp1d(qdot_W, Q_used_prim_W, kind = "linear")
    cost_per_Wh_th_incl_el_interpol = interpolate.interp1d(qdot_W, cost_per_Wh_th_incl_el, kind = "linear")
    eta_elec_interpol = interpolate.interp1d(Q_used_prim_W, eta_elec, kind = "linear")

    Q_therm_min_W = min(qdot_W)
    Q_therm_max_W = max(qdot_W)

    return wdot_interpol_W, Q_used_prim_interpol_W, cost_per_Wh_th_incl_el_interpol, Q_therm_min_W, Q_therm_max_W, eta_elec_interpol

def CC_Op(wdot_W, gt_size_W, fuel, tDH_K, gV) :
    """
    Operation Function of Combined Cycle at given electricity Demand (wdot).
    The gas turbine (GT) exhaust gas is used by the steam turbine (ST).

    :type wdot_W : float
    :param wdot_W: Electric load that is demanded to the gas turbine (only GT output, not CC output!)
    :type gt_size_W : float
    :param gt_size_W: size of the gas turbine and (not CC)(P_el_max)
    :type fuel : string
    :param fuel: fuel used, either 'NG' (natural gas) or 'BG' (biogas)
    :type tDH_K : float
    :param tDH_K: plant supply temperature to district heating network (hot)
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

    (eta0, mdot0_kgpers) = GT_fullLoadParam(gt_size_W, fuel)
    (eta, mdot_kgpers, texh_K, mdotfuel_kgpers) = GT_partLoadParam(wdot_W, gt_size_W, eta0, mdot0_kgpers, fuel)
    (qdot_W, wdotfin_W) = ST_Op(mdot_kgpers, texh_K, tDH_K, fuel, gV)

    if fuel == 'NG':
        LHV = LHV_NG
    else:
        LHV = LHV_BG

    eta_elec = (wdot_W + wdotfin_W) / (mdotfuel_kgpers * LHV)
    eta_heat = qdot_W / (mdotfuel_kgpers * LHV)
    eta_all = eta_elec + eta_heat
    wtot_W = wdotfin_W + wdot_W

    return wtot_W, qdot_W, eta_elec, eta_heat, eta_all

def GT_fullLoadParam(gt_size_W, fuel):
    """
    Calculates gas turbine efficiency and exhaust gas mass flow rate at full load.

    :type gt_size_W : float
    :param gt_size_W: Maximum electric load that is demanded to the gas turbine
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
    assert gt_size_W < GT_maxSize + 0.001
    if gt_size_W == 0:
        eta0 = 0.01
    else:
        eta0 = 0.0196 * scipy.log(gt_size_W * 1E-3) + 0.1317  # [C. Weber, 2008]_

    if fuel == 'NG':
        LHV = LHV_NG
    else:
        LHV = LHV_BG

    mdotfuel_kgpers = gt_size_W / (eta0 * LHV)

    if fuel == 'NG':
        mdot0_kgpers = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4  * 28E-3 + 200.5 * 32E-3 * (CC_airratio - 1) +
                 200.5 * 3.773 * 28E-3 * (CC_airratio - 1) ) * mdotfuel_kgpers / 1.8156
    else:
        mdot0_kgpers = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (CC_airratio - 1) +
                 115.5 * 3.773 * 28E-3 * (CC_airratio - 1) ) * mdotfuel_kgpers / 2.754

    return eta0, mdot0_kgpers

def GT_partLoadParam(wdot_W, gt_size_W, eta0, mdot0, fuel, ):
    """
    Calculates GT operational parameters at part load

    :type wdot_W : float
    :param wdot_W: GT electric output (load)
    :type gt_size_W : float
    :param gt_size_W: Maximum electric load that is demanded to the gas turbine
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
    assert wdot_W <= gt_size_W

    if fuel == 'NG':
        exitT = CC_exitT_NG
        LHV = LHV_NG
    else:
        exitT = CC_exitT_BG
        LHV = LHV_BG

    pload = (wdot_W + 1) / gt_size_W # avoid calculation errors
    if pload < GT_minload:
        # print pload
        # print wdot
        # print gt_size
        raise ModelError

    eta = (0.4089 + 0.9624 * pload - 0.3726 * pload ** 2) * eta0  # [C. Weber, 2008]_
    #mdot = (0.9934 + 0.0066 * pload) * mdot0
    texh_K = (0.7379 + 0.2621 * pload) * exitT
    mdotfuel_kgpers = wdot_W / (eta * LHV)

    if fuel == 'NG':
        mdot_kgpers = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4  * 28E-3 + 200.5 * 32E-3 * (CC_airratio - 1) +
                200.5 * 3.773 * 28E-3 * (CC_airratio - 1) ) * mdotfuel_kgpers / 1.8156

    else:
        mdot_kgpers = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (CC_airratio - 1) + \
                115.5 * 3.773 * 28E-3 * (CC_airratio - 1) ) * mdotfuel_kgpers / 2.754

    return eta, mdot_kgpers, texh_K, mdotfuel_kgpers

def ST_Op(mdot_kgpers, texh_K, tDH_K, fuel, gV):
    """
    Operation of a double pressure (LP,HP) steam turbine connected to a district heating network following
    [C. Weber, 2008]_

    :type mdot_kgpers : float
    :param mdot_kgpers: GT part-load exhaust gas mass flow rate
    :type texh_K : float
    :param texh_K: GT exhaust gas temperature
    :type tDH_K : float
    :param tDH_K: plant supply temperature to district heating network (hot)
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

    temp_i_K = (0.9 * ((6/48.2) ** (0.4/1.4) - 1) + 1) * (texh_K - ST_deltaT)
    if fuel == 'NG':
        Mexh = 103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * \
                                                               (CC_airratio - 1) * 32E-3 + \
               200.5 * (CC_airratio - 1) * 3.773 * 28E-3
        ncp_exh = 103.7 * 44 * 0.846 + 196.2 * 18 * 1.8723 + \
                  761.4 * 28 * 1.039 + 200.5 * (CC_airratio - 1) * 32 * \
                                       0.918 + 200.5 * (CC_airratio - 1) * 3.773 * 28 * 1.039
        cp_exh = ncp_exh / Mexh  # J/kgK


    else:
        Mexh = 98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * \
                                                            (CC_airratio - 1) * 32E-3 + \
               115.5 * (CC_airratio - 1) * 3.773 * 28E-3
        ncp_exh = 98.5 * 44 * 0.846 + 116 * 18 * 1.8723 + \
                  436.8 * 28 * 1.039 + 115.5 * (CC_airratio - 1) * 32 * \
                                       0.918 + 115.5 * (CC_airratio - 1) * 3.773 * 28 * 1.039
        cp_exh = ncp_exh / Mexh  # J/kgK

    a = np.array([[1653E3 + gV.cp * (texh_K - ST_deltaT - 534.5), \
                   gV.cp * (temp_i_K - 534.5)], \
                  [gV.cp * (534.5 - 431.8), \
                   2085.8E3 + gV.cp * (534.5 - 431.8)]])
    b = np.array([mdot_kgpers * cp_exh * (texh_K - (534.5 + ST_deltaT)), \
                  mdot_kgpers * cp_exh * (534.5 - 431.8)])
    [mdotHP_kgpers, mdotLP_kgpers] = np.linalg.solve(a, b)   # HP and LP mass flow of a double pressure steam turbine

    temp0 = tDH_K + CC_deltaT_DH    # condensation temperature constrained by the DH network temperature
    pres0 = (0.0261 * (temp0-273) ** 2 -2.1394 * (temp0-273) + 52.893) * 1E3

    deltaHevap = (-2.4967 * (temp0-273) + 2507) * 1E3
    qdot_W = (mdotHP_kgpers + mdotLP_kgpers) * deltaHevap       # thermal output of ST


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


    h_HP_Jperkg = (2.5081 * (texh_K - ST_deltaT - 273) + 2122.7) * 1E3  # J/kg
    h_LP_Jperkg = (2.3153 * (temp_i_K - 273) + 2314.7) * 1E3  # J/kg
    h_cond_Jperkg = (1.6979 * (temp0 - 273) + 2506.6) * 1E3  # J/kg
    spec_vol_m3perkg = 0.0010  # m3/kg

    wdotST_W = mdotHP_kgpers * (h_HP_Jperkg - h_LP_Jperkg) + (mdotHP_kgpers + mdotLP_kgpers) * (h_LP_Jperkg - h_cond_Jperkg)  # turbine electricity output
    wdotcomp_W = spec_vol_m3perkg * (mdotLP_kgpers * (6E5 - pres0) + (mdotHP_kgpers + mdotLP_kgpers) * (48.2E5 - 6E5))  # compressor electricity use

    wdotfin_W = STGen_eta * ( wdotST_W - wdotcomp_W )  # gross electricity production of turbine

    return qdot_W, wdotfin_W


#===========================
#Fuel Cell
#===========================

def calc_eta_FC(Q_load_W, Q_design_W, phi_threshold, approach_call):
    """
    Efficiency for operation of a SOFC (based on LHV of NG) including all auxiliary losses
    Valid for Q_load in range of 1-10 [kW_el]

    Modeled after:
        Approach A (NREL Approach):
            http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
            and
            NREL : p.5  of [M. Zolot et al., 2004]_

        Approach B (Empiric Approach): [Iain Staffell]_


    :type Q_load_W : float
    :param Q_load_W: Load at each time step

    :type Q_design_W : float
    :param Q_design_W: Design Load of FC

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

        phi = float(Q_load_W) / float(Q_design_W)
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

        if Q_design_W > 0:
            phi = float(Q_load_W) / float(Q_design_W)

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

def calc_Cinv_CCT(CC_size_W, locator, config, technology=0):
    """
    Annualized investment costs for the Combined cycle

    :type CC_size_W : float
    :param CC_size_W: Electrical size of the CC

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in CHF

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    CCGT_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="CCGT")
    technology_code = list(set(CCGT_cost_data['code']))
    CCGT_cost_data[CCGT_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if CC_size_W < CCGT_cost_data['cap_min'][0]:
        CC_size_W = CCGT_cost_data['cap_min'][0]
    CCGT_cost_data = CCGT_cost_data[
        (CCGT_cost_data['cap_min'] <= CC_size_W) & (CCGT_cost_data['cap_max'] > CC_size_W)]

    Inv_a = CCGT_cost_data.iloc[0]['a']
    Inv_b = CCGT_cost_data.iloc[0]['b']
    Inv_c = CCGT_cost_data.iloc[0]['c']
    Inv_d = CCGT_cost_data.iloc[0]['d']
    Inv_e = CCGT_cost_data.iloc[0]['e']
    Inv_IR = (CCGT_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = CCGT_cost_data.iloc[0]['LT_yr']
    Inv_OM = CCGT_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (CC_size_W) ** Inv_c + (Inv_d + Inv_e * CC_size_W) * log(CC_size_W)

    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    return Capex_a, Opex_fixed


def calc_Cinv_FC(P_design_W, locator, config, technology=0):
    """
    Calculates the investment cost of a Fuel Cell in CHF

    http://hexis.com/sites/default/files/media/publikationen/140623_hexis_galileo_ibb_profitpaket.pdf?utm_source=HEXIS+Mitarbeitende&utm_campaign=06d2c528a5-1_Newsletter_2014_Mitarbeitende_DE&utm_medium=email&utm_term=0_e97bc1703e-06d2c528a5-

    :type P_design_W : float
    :param P_design_W: Design thermal Load of Fuel Cell [W_th]

    :rtype InvCa: float
    :returns InvCa: annualized investment costs in CHF
    """
    FC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="FC")
    technology_code = list(set(FC_cost_data['code']))
    FC_cost_data[FC_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if P_design_W < FC_cost_data['cap_min'][0]:
        P_design_W = FC_cost_data['cap_min'][0]
    FC_cost_data = FC_cost_data[
        (FC_cost_data['cap_min'] <= P_design_W) & (FC_cost_data['cap_max'] > P_design_W)]

    Inv_a = FC_cost_data.iloc[0]['a']
    Inv_b = FC_cost_data.iloc[0]['b']
    Inv_c = FC_cost_data.iloc[0]['c']
    Inv_d = FC_cost_data.iloc[0]['d']
    Inv_e = FC_cost_data.iloc[0]['e']
    Inv_IR = (FC_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = FC_cost_data.iloc[0]['LT_yr']
    Inv_OM = FC_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (P_design_W) ** Inv_c + (Inv_d + Inv_e * P_design_W) * log(P_design_W)

    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    return Capex_a, Opex_fixed
