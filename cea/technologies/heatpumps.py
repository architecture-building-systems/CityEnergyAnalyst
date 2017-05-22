"""
heatpumps
"""


from __future__ import division
from math import floor, log


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


#============================
#operation costs
#============================

def calc_Cop_GHP(mdot, tsup, tret, tground, gV):
    """
    For the operation of a Geothermal heat pump (GSHP) supplying DHN.

    :type mdot : float
    :param mdot: supply mass flow rate to the DHN
    :type tsup : float
    :param tsup: supply temperature to the DHN (hot)
    :type tret : float
    :param tret: return temeprature from the DHN (cold)
    :type tground : float
    :param tground: ground temperature
    :param gV: globalvar.py

    :rtype wdot_el : float
    :returns wdot_el: total electric power requirement for compressor and auxiliary el.
    :rtype qcolddot : float
    :returns qcolddot: cold power requirement
    :rtype qhotdot_missing : float
    :returns qhotdot_missing: deficit heating energy from GSHP
    :rtype tsup2 :
    :returns tsup2: supply temperature after HP (to DHN)

    ..[O. Ozgener et al., 2005] O. Ozgener, A. Hepbasli (2005). Experimental performance analysis of a solar assisted
    ground-source heat pump greenhouse heating system, Energy Build.
    ..[C. Montagud et al., 2014] C. Montagud, J.M. Corberan, A. Montero (2014). In situ optimization methodology for
    the water circulation pump frequency of ground source heat pump systems. Energy and Buildings
    """
    tsup2 = tsup      # tsup2 = tsup, if all load can be provided by the HP

    # calculate condenser temperature
    tcond = tsup + gV.HP_deltaT_cond
    if tcond > gV.HP_maxT_cond:
        #raise ModelError
        tcond = gV.HP_maxT_cond
        tsup2 = tcond - gV.HP_deltaT_cond  # lower the supply temp if necessary, tsup2 < tsup if max load is not enough

    # calculate evaporator temperature
    tevap = tground - gV.HP_deltaT_evap
    COP = gV.GHP_etaex / (1- tevap/tcond)     # [O. Ozgener et al., 2005]_

    qhotdot = mdot * gV.cp * (tsup2 - tret)
    qhotdot_missing = mdot * gV.cp * (tsup - tsup2) #calculate the missing energy if tsup2 < tsup

    wdot = qhotdot / COP
    wdot_el = wdot / gV.GHP_Auxratio     # compressor power [C. Montagud et al., 2014]_

    qcolddot =  qhotdot - wdot

    #if qcolddot > gV.GHP_CmaxSize:
    #    raise ModelError

    return wdot_el, qcolddot, qhotdot_missing, tsup2

def GHP_op_cost(mdot, tsup, tret, gV, COP):
    """
    Operation cost of GSHP supplying DHN

    :type mdot : float
    :param mdot: supply mass flow rate to the DHN
    :type tsup : float
    :param tsup: supply temperature to the DHN (hot)
    :type tret : float
    :param tret: return temeprature from the DHN (cold)
    :type COP: float
    :param COP: coefficient of performance of GSHP
    :param gV: globalvar.py

    :rtype C_GHP_el: float
    :returns C_GHP_el: electricity cost of GSHP operation

    :rtype wdot: float
    :returns wdot: electricty required for GSHP operation

    :rtype qcoldot: float
    :returns qcoldot: cold power requirement

    :rtype q_therm: float
    :returns q_therm: thermal energy supplied to DHN

    """

    q_therm = mdot * gV.cp *( tsup - tret) # Thermal Energy generated
    qcoldot = q_therm * ( 1 - ( 1 / COP ) )
    wdot = q_therm / COP

    C_GHP_el = wdot * gV.ELEC_PRICE

    return C_GHP_el, wdot, qcoldot, q_therm

def GHP_Op_max(tsup, tground, nProbes, gV):
    """
    For the operation of a Geothermal heat pump (GSHP) at maximum capacity supplying DHN.

    :type tsup : float
    :param tsup: supply temperature to the DHN (hot)
    :type tground : float
    :param tground: ground temperature
    :type nProbes: float
    :param nProbes: bumber of probes
    :param gV: globalvar.py

    :rtype qhotdot: float
    :returns qhotdot: heating energy provided from GHSP
    :rtype COP: float
    :returns COP: coefficient of performance of GSHP

    """

    qcoldot = nProbes * gV.GHP_Cmax_Size_th   # maximum capacity from all probes
    COP = gV.HP_etaex * ( tsup + gV.HP_deltaT_cond ) / ( ( tsup + gV.HP_deltaT_cond ) - tground)
    qhotdot = qcoldot /( 1 - ( 1 / COP ) )

    return qhotdot, COP

def HPLake_op_cost(mdot, tsup, tret, tlake, gV):
    """
    For the operation of lake heat pump supplying DHN

    :type mdot : float
    :param mdot: supply mass flow rate to the DHN
    :type tsup : float
    :param tsup: supply temperature to the DHN (hot)
    :type tret : float
    :param tret: return temeprature from the DHN (cold)
    :type tlake : float
    :param tlake: lake temperature
    :param gV: globalvar.py

    :rtype C_HPL_el: float
    :returns C_HPL_el: electricity cost of Lake HP operation

    :rtype wdot: float
    :returns wdot: electricty required for Lake HP operation

    :rtype Q_cold_primary: float
    :returns Q_cold_primary: cold power requirement

    :rtype Q_therm: float
    :returns Q_therm: thermal energy supplied to DHN

    """

    wdot, qcolddot = HPLake_Op(mdot, tsup, tret, tlake, gV)

    Q_therm = mdot * gV.cp *(tsup - tret)

    C_HPL_el = wdot * gV.ELEC_PRICE

    Q_cold_primary = qcolddot

    return C_HPL_el, wdot, Q_cold_primary, Q_therm

def HPLake_Op(mdot, tsup, tret, tlake, gV):
    """
    For the operation of a Heat pump between a district heating network and a lake

    :type mdot : float
    :param mdot: supply mass flow rate to the DHN
    :type tsup : float
    :param tsup: supply temperature to the DHN (hot)
    :type tret : float
    :param tret: return temeprature from the DHN (cold)
    :type tlake : float
    :param tlake: lake temperature
    :param gV: globalvar.py

    :rtype wdot_el : float
    :returns wdot_el: total electric power requirement for compressor and auxiliary el.
    :rtype qcolddot : float
    :returns qcolddot: cold power requirement

    ..[L. Girardin et al., 2010] L. Girardin, F. Marechal, M. Dubuis, N. Calame-Darbellay, D. Favrat (2010). EnerGis:
    a geographical information based system for the evaluation of integrated energy conversion systems in urban areas,
    Energy.

    ..[C. Montagud et al., 2014] C. Montagud, J.M. Corberan, A. Montero (2014). In situ optimization methodology for
    the water circulation pump frequency of ground source heat pump systems. Energy and Buildings
    """

    # calculate condenser temperature
    tcond = tsup + gV.HP_deltaT_cond
    print tcond
    if tcond > gV.HP_maxT_cond:
        raise ModelError

    # calculate evaporator temperature
    tevap = tlake - gV.HP_deltaT_evap
    COP = gV.HP_etaex / (1- tevap/tcond)   # [L. Girardin et al., 2010]_
    qhotdot = mdot * gV.cp * (tsup - tret)

    if qhotdot > gV.HP_maxSize:
        print "Qhot above max size on the market !"

    wdot = qhotdot / COP
    wdot_el = wdot / gV.HP_Auxratio     # compressor power [C. Montagud et al., 2014]_

    qcolddot =  qhotdot - wdot

    return wdot_el, qcolddot

def HPSew_op_cost(mdot, tsup, tret, tsupsew, gV):
    """
    Operation cost of sewage water HP supplying DHN

    :type mdot : float
    :param mdot: supply mass flow rate to the DHN
    :type tsup : float
    :param tsup: supply temperature to the DHN (hot)
    :type tret : float
    :param tret: return temeprature from the DHN (cold)
    :type tsupsew : float
    :param tsupsew: sewage supply temperature
    :param gV: globalvar.py

    :rtype C_HPSew_el_pure: float
    :returns C_HPSew_el_pure: electricity cost of sewage water HP operation

    :rtype C_HPSew_per_kWh_th_pure: float
    :returns C_HPSew_per_kWh_th_pure: electricity cost per kWh thermal energy produced from sewage water HP

    :rtype qcoldot: float
    :returns qcoldot: cold power requirement

    :rtype q_therm: float
    :returns q_therm: thermal energy supplied to DHN

    :rtype wdot: float
    :returns wdot: electricty required for sewage water HP operation

    ..[L. Girardin et al., 2010] L. Girardin, F. Marechal, M. Dubuis, N. Calame-Darbellay, D. Favrat (2010). EnerGis:
    a geographical information based system for the evaluation of integrated energy conversion systems in urban areas,
    Energy.

    """

    COP = gV.HP_etaex * ( tsup + gV.HP_deltaT_cond) / ( ( tsup + gV.HP_deltaT_cond ) - tsupsew )
    q_therm = mdot * gV.cp *(tsup - tret)
    qcoldot = q_therm*( 1 - ( 1 / COP ) )

    wdot = q_therm / COP

    C_HPSew_el_pure = wdot * gV.ELEC_PRICE
    C_HPSew_per_kWh_th_pure = C_HPSew_el_pure / (q_therm)

    return C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, qcoldot, q_therm, wdot




# investment and maintenance costs

def calc_Cinv_GHP(GHP_Size, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    :type GHP_Size : float
    :param GHP_Size: Design electrical size of the heat pump in [Wel]

    :type InvCa : float
    :returns InvCa: annualized investment costs in [EUROS/a]

    ..[D. Bochatay et al., 2005] D. Bochatay, I. Blanc, O. Jolliet, F. Marechal, T. Manasse-Ratmandresy (2005). Project
    PACOGEN Evaluation economique et environmentale de systemes energetiques a usage residentiel., EPFL.
    """
    nProbe = floor(GHP_Size / gV.GHP_WmaxSize)
    roundProbe = GHP_Size / gV.GHP_WmaxSize - nProbe

    # calculate investment cost of GSHP and Boreholes
    InvC_HP = 0
    InvC_BH = 0

    InvC_HP += nProbe * 6297 * (gV.GHP_WmaxSize * 1E-3) ** 0.49
    InvC_BH += nProbe * 8520 * (gV.GHP_WmaxSize * 1E-3) ** 0.74

    InvC_HP += 6297 * (roundProbe * gV.GHP_WmaxSize * 1E-3) ** 0.49
    InvC_BH += 8520 * (roundProbe * gV.GHP_WmaxSize * 1E-3) ** 0.74

    InvCa = InvC_HP * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / \
            ((1+gV.GHP_i) ** gV.GHP_nHP - 1) + \
            InvC_BH * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nBH / \
            ((1+gV.GHP_i) ** gV.GHP_nBH - 1)

    return InvCa


def calc_Cinv_HP(HP_Size, gV):
    """
    Calculates the annualized investment costs for the heat pump

    :type HP_Size : float
    :param HP_Size: Design thermal size of the heat pump in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF/a]

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    if HP_Size > 0:
        InvC = (-493.53 * log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
        InvCa = InvC * gV.HP_i * (1+ gV.HP_i) ** gV.HP_n / \
                ((1+gV.HP_i) ** gV.HP_n - 1)

    else:
        InvCa = 0

    return InvCa


def GHP_InvCost(GHP_Size, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    :type GHP_Size : float
    :param GHP_Size: Design electrical size of the heat pump in [Wel]

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


