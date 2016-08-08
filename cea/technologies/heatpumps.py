"""
==================================================
heatpumps
==================================================

"""


from __future__ import division
from math import floor, log


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


def calc_Cop_GHP(mdot, tsup, tret, tground, gV):
    """
    For the operation of a Geothermal Heat pump

    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply to the DHN (hot)
    tret : float
        temperature of return from the DHN (cold)
    tground : float
        temperature of the ground

    Returns
    -------
    wdot_el : float
        total electric power needed (compressor and auxiliary)
    qcolddot : float
        cold power needed
    qhotdot_missing : float
        heating energy which cannot be provided by the HP
    tsup2 : supply temperature after HP (to DHN)

    """
    tsup2 = tsup

    tcond = tsup + gV.HP_deltaT_cond
    if tcond > gV.HP_maxT_cond:
        #raise ModelError
        tcond = gV.HP_maxT_cond
        tsup2 = tcond - gV.HP_deltaT_cond  # lower the supply temp if necessairy


    tevap = tground - gV.HP_deltaT_evap
    COP = gV.GHP_etaex / (1- tevap/tcond)

    qhotdot = mdot * gV.cp * (tsup2 - tret)  # tsup2 = tsup, if all load can be provided by the HP
                                             #  else: tsup2 < tsup if max load is not enough

    qhotdot_missing = mdot * gV.cp * (tsup - tsup2) #calculate the missing energy if needed

    wdot = qhotdot / COP
    wdot_el = wdot / gV.GHP_Auxratio

    qcolddot =  qhotdot - wdot

    #if qcolddot > gV.GHP_CmaxSize:
    #    raise ModelError


    return wdot_el, qcolddot, qhotdot_missing, tsup2


def HPLake_op_cost(mdot, tsup, tret, tlake, gV):

    wdot, qcolddot = HPLake_Op(mdot, tsup, tret, tlake, gV)

    Q_therm = mdot * gV.cp *(tsup - tret)

    C_HPL_el = wdot * gV.ELEC_PRICE

    Q_cold_primary = qcolddot

    return C_HPL_el, wdot, Q_cold_primary, Q_therm


def HPSew_op_cost(mdot, tsup, tret, tsupsew, gV):

    COP = gV.HP_etaex*(tsup+gV.HP_deltaT_cond)/((tsup+gV.HP_deltaT_cond)-tsupsew)
    q_therm = mdot * gV.cp *(tsup - tret)
    qcoldot = q_therm*(1-(1/COP))

    wdot = q_therm/COP

    C_HPSew_el_pure = wdot * gV.ELEC_PRICE
    C_HPSew_el = C_HPSew_el_pure
    C_HPSew_per_kWh_th_pure = C_HPSew_el_pure / (q_therm)

    return C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, qcoldot, q_therm, wdot


def GHP_op_cost(mdot, tsup, tret, gV, COP):

    q_therm = mdot * gV.cp *(tsup - tret) # Thermal Energy generated
    qcoldot = q_therm*(1-(1/COP))
    wdot = q_therm/COP

    C_GHP_el = wdot * gV.ELEC_PRICE

    return C_GHP_el, wdot, qcoldot, q_therm


def HPLake_Op(mdot, tsup, tret, tlake, gV):
    """
    For the operation of a Heat pump
    between a district heating network and a lake

    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply for the DHN (hot)
    tret : float
        temperature of return for the DHN (cold)
    tlake : float
        temperature of the lake

    Returns
    -------
    wdot_el : float
        total electric power needed (compressor and auxiliary)
    qcolddot : float
        cold power needed

    """
    tcond = tsup + gV.HP_deltaT_cond
    print tcond
    if tcond > gV.HP_maxT_cond:
        raise ModelError

    tevap = tlake - gV.HP_deltaT_evap
    COP = gV.HP_etaex / (1- tevap/tcond)
    qhotdot = mdot * gV.cp * (tsup - tret)

    if qhotdot > gV.HP_maxSize:
        print "Qhot above max size on the market !"

    wdot = qhotdot / COP
    wdot_el = wdot / gV.HP_Auxratio

    qcolddot =  qhotdot - wdot

    return wdot_el, qcolddot


def GHP_Op_max(tsup, tground, nProbes, gV):

    qcoldot = nProbes*gV.GHP_Cmax_Size_th
    COP = gV.HP_etaex*(tsup+gV.HP_deltaT_cond)/((tsup+gV.HP_deltaT_cond)-tground)
    qhotdot = qcoldot /(1-(1/COP))

    return qhotdot, COP


"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_GHP(GHP_Size, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    Parameters
    ----------
    GHP_Size : float
        Design ELECTRICAL size of the heat pump in WATT ELECTRICAL

    Returns
    -------
    InvCa : float
        annualized investment costs in EUROS/a

    """
    nProbe = floor(GHP_Size / gV.GHP_WmaxSize)
    roundProbe = GHP_Size / gV.GHP_WmaxSize - nProbe

    InvC_HP = 0
    InvC_BH = 0

    InvC_HP += nProbe * 5247.5 * (gV.GHP_WmaxSize * 1E-3) ** 0.49
    InvC_BH += nProbe * 7100 * (gV.GHP_WmaxSize * 1E-3) ** 0.74

    InvC_HP += 5247.5 * (roundProbe * gV.GHP_WmaxSize * 1E-3) ** 0.49
    InvC_BH += 7100 * (roundProbe * gV.GHP_WmaxSize * 1E-3) ** 0.74

    InvCa = InvC_HP * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / \
            ((1+gV.GHP_i) ** gV.GHP_nHP - 1) + \
            InvC_BH * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nBH / \
            ((1+gV.GHP_i) ** gV.GHP_nBH - 1)

    return InvCa


def calc_Cinv_HP(HP_Size, gV):
    """
    Calculates the annualized investment costs for the heat pump

    Parameters
    ----------
    HP_Size : float
        Design THERMAL size of the heat pump in WATT THERMAL

    Returns
    -------
    InvCa : float
        annualized investment costs in CHF/a

    """
    if HP_Size > 0:
        InvC = (-493.53 * log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
        InvCa = InvC * gV.HP_i * (1+ gV.HP_i) ** gV.HP_n / \
                ((1+gV.HP_i) ** gV.HP_n - 1)

    else:
        InvCa = 0

    return InvCa


def HP_InvCost(HP_Size, gV):
    """
    Calculates the annualized investment costs for the heat pump

    Parameters
    ----------
    HP_Size : float
        Design THERMAL size of the heat pump in WATT THERMAL

    Returns
    -------
    InvCa : float
        annualized investment costs in CHF/a

    """
    InvC = (-493.53 * log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
    InvCa = InvC * gV.HP_i * (1+ gV.HP_i) ** gV.HP_n / \
            ((1+gV.HP_i) ** gV.HP_n - 1)

    return InvCa


def GHP_InvCost(GHP_Size, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    Parameters
    ----------
    GHP_Size : float
        Design ELECTRICAL size of the heat pump in WATT ELECTRICAL

    Returns
    -------
    InvCa : float
        annualized investment costs in EUROS/a

    """
    InvC_HP = 5247.5 * (GHP_Size * 1E-3) ** 0.49
    InvC_BH = 7100 * (GHP_Size * 1E-3) ** 0.74

    InvCa = InvC_HP * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / \
            ((1+gV.GHP_i) ** gV.GHP_nHP - 1) + \
            InvC_BH * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nBH / \
            ((1+gV.GHP_i) ** gV.GHP_nBH - 1)

    return InvCa


