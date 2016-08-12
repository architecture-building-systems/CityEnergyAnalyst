"""
==================================================
cogeneration (combined heat and power)
==================================================

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
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

"""
============================
operation costs
============================

"""


def calc_Cop_CCT(GT_SIZE, T_DH_Supply, fuel, gV):
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

        CC_OpInfo = CC_Op(wdot_in, GT_SIZE, fuel, T_DH_Supply, gV)

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
    eta_elec_interpol = interpolate.interp1d(Q_used_prim, eta_elec, kind = "linear")

    #print eta_elec_interpol, Q_used_prim_interpol, " eta_elec, Q_used_prim_interpol"
    #E_CC_produced = eta_elec_interpol * Q_used_prim_interpol
    Q_therm_min = min(qdot)
    Q_therm_max = max(qdot)

    return wdot_interpol, Q_used_prim_interpol, cost_per_Wh_th_incl_el_interpol, Q_therm_min, Q_therm_max, eta_elec_interpol


def GT_fullLoadParam(gt_size, fuel, gV):
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
    if gt_size == 0:
        eta0 = 0.01
    else:
        eta0 = 0.0196 * scipy.log(gt_size * 1E-3) + 0.1317

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


def ST_Op(mdot, texh, tDH, fuel, gV):
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


def CC_Op(wdot, gt_size, fuel, tDH, gV) :
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
    wtot : float
        electric power OUTPUT from the combined cycle (both GT + ST !)
    qdot : float
        heat power transfered to the DHN
    eta_elec : float
        total electric efficiency
    eta_heat : float
        total thermal efficiency
    eta_all : float
        sum of total electric and thermal efficiency

    """

    (eta0, mdot0) = GT_fullLoadParam(gt_size, fuel, gV)
    (eta, mdot, texh, mdotgas) = GT_partLoadParam(wdot, gt_size, eta0, mdot0, fuel, gV)
    (qdot, wdotfin) = ST_Op(mdot, texh, tDH, fuel, gV)

    if fuel == 'NG':
        LHV = gV.LHV_NG
    else:
        LHV = gV.LHV_BG

    eta_elec = (wdot + wdotfin) / (mdotgas * LHV)
    eta_heat = qdot / (mdotgas * LHV)
    eta_all = eta_elec + eta_heat
    wtot = wdotfin + wdot

    return wtot, qdot, eta_elec, eta_heat, eta_all


def GT_partLoadParam(wdot, gt_size, eta0, mdot0, fuel, gV):
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

    pload = (wdot + 1) / gt_size # avoid calculation errors
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


def calc_eta_FC(Q_load, Q_design, phi_threshold, approach_call):

    """
    VALID FOR Q in range of 1-10kW_el !
    Compared to LHV of NG

    Efficiency for operation of a SOFC (based on LHV of nat. gas)

    Includes all auxillary losses

    Fuel = Natural Gas

    Modeled after:
        Approach A:
            http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
            and
            NREL : p.5  of http://www.nrel.gov/vehiclesandfuels/energystorage/pdfs/36169.pdf

        Approach B:
            http://etheses.bham.ac.uk/641/1/Staffell10PhD.pdf

    Parameters
    ----------
    Q_load : float
        Load of time step

    Q_design : float
        Design Load of FC

    phi_threshold : float
        where Maximum Efficiency is reached, used for Approach A

    approach_call : string
        choose "A" or "B": A = NREL-Approach, B = Empiric Approach

    Returns
    -------
    eta_el : float
        electric efficiency of FC (Lower Heating Value), in abs. numbers

    Q_fuel : float
        Heat demand from fuel (in Watt)



    """
    phi = 0.0


    """ APPROACH A - AFTER NREL """
    if approach_call == "A":

        phi = float (Q_load) / float(Q_design)
        eta_max = 0.425 # from energy.gov

        if phi >= phi_threshold: # from NREL-Shape
            eta_el = eta_max - ((1/6.0 * eta_max)/ (1.0-phi_threshold) )* abs(phi-phi_threshold)


        if phi < phi_threshold:
            if phi <= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3 * (phi / (phi_threshold*118/520.0))


            if phi < 0.5 * phi_threshold and phi >= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3.0 + eta_max * 0.25 * (phi-phi_threshold*118/520.0) / (phi_threshold * (0.5 - 118/520.0))

            if phi > 0.5 * phi_threshold and phi < phi_threshold:
                eta_el = eta_max * (2/3.0 + 0.25)  +  1/12.0 * eta_max * (phi - phi_threshold * 0.5) / (phi_threshold * (1-0.5))

        eta_therm_max = 0.45 # constant, after energy.gov

        if phi < phi_threshold:
            eta_therm = 0.5 * eta_therm_max * (phi / phi_threshold)

        else:
            eta_therm = 0.5 * eta_therm_max * (1 + eta_therm_max * ((phi - phi_threshold) / (1 - phi_threshold)))


    """ SECOND APPROACH  after http://etheses.bham.ac.uk/641/"""
    if approach_call == "B":

        if Q_design > 0:
            phi = float(Q_load) / float(Q_design)

        else:
            phi = 0

        eta_el_max = 0.39  # after http://etheses.bham.ac.uk/641/
        eta_therm_max = 0.58   # http://etheses.bham.ac.uk/641/     * 1.11 as this source gives eff. of HHV
        eta_el_score = -0.220 + 5.277 * phi - 9.127 * phi**2 + 7.172* phi ** 3 - 2.103* phi**4
        eta_therm_score = 0.9 - 0.07 * phi + 0.17 * phi**2

        eta_el = eta_el_max * eta_el_score
        eta_therm = eta_therm_max * eta_therm_score

        if phi < 0.2:
            eta_el = 0


    return eta_el, eta_therm


"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_CCT(CC_size, gV):
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


def calc_Cinv_FC(P_design, gV):
    """
    Calculates the cost of a Fuel Cell in CHF

    http://hexis.com/sites/default/files/media/publikationen/140623_hexis_galileo_ibb_profitpaket.pdf?utm_source=HEXIS+Mitarbeitende&utm_campaign=06d2c528a5-1_Newsletter_2014_Mitarbeitende_DE&utm_medium=email&utm_term=0_e97bc1703e-06d2c528a5-

    Parameters
    ----------
    P_design : float
        Design THERMAL Load of Fuel Cell [W_th]

    Returns
    -------
    InvC_return : float
        total investment Cost

    InvCa : float
        annualized investment costs in CHF

    """

    InvC = (1+gV.FC_overhead) * gV.FC_stack_cost * P_design / 1000 # FC_stack_cost = 55'000 CHF  / kW_therm, 10 % extra (overhead) cost

    InvCa =  InvC * gV.FC_i * (1+ gV.FC_i) ** gV.FC_n / ((1+gV.FC_i) ** gV.FC_n - 1)


    return InvCa
