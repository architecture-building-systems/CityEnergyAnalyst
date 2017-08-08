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

def calc_Cop_GHP(mdot_kgpers, T_DH_sup_K, T_re_K, tground_K, gV):
    """
    For the operation of a Geothermal heat pump (GSHP) supplying DHN.

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type T_DH_sup_K : float
    :param T_DH_sup_K: supply temperature to the DHN (hot)
    :type T_re_K : float
    :param T_re_K: return temeprature from the DHN (cold)
    :type tground_K : float
    :param tground_K: ground temperature
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
    tsup2_K = T_DH_sup_K      # tsup2 = tsup, if all load can be provided by the HP

    # calculate condenser temperature
    tcond_K = T_DH_sup_K + gV.HP_deltaT_cond
    if tcond_K > gV.HP_maxT_cond:
        #raise ModelError
        tcond_K = gV.HP_maxT_cond
        tsup2_K = tcond_K - gV.HP_deltaT_cond  # lower the supply temp if necessary, tsup2 < tsup if max load is not enough

    # calculate evaporator temperature
    tevap_K = tground_K - gV.HP_deltaT_evap
    COP = gV.GHP_etaex / (1- tevap_K/tcond_K)     # [O. Ozgener et al., 2005]_

    qhotdot_W = mdot_kgpers * gV.cp * (tsup2_K - T_re_K)
    qhotdot_missing_W = mdot_kgpers * gV.cp * (T_DH_sup_K - tsup2_K) #calculate the missing energy if tsup2 < tsup

    wdot_W = qhotdot_W / COP
    wdot_el_W = wdot_W / gV.GHP_Auxratio     # compressor power [C. Montagud et al., 2014]_

    qcolddot_W =  qhotdot_W - wdot_W

    #if qcolddot > gV.GHP_CmaxSize:
    #    raise ModelError

    return wdot_el_W, qcolddot_W, qhotdot_missing_W, tsup2_K

def GHP_op_cost(mdot_kgpers, t_sup_K, t_ret_K, gV, COP):
    """
    Operation cost of GSHP supplying DHN

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the DHN (hot)
    :type t_ret_K : float
    :param t_ret_K: return temeprature from the DHN (cold)
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

    q_therm_W = mdot_kgpers * gV.cp * (t_sup_K - t_ret_K) # Thermal Energy generated
    qcoldot_W = q_therm_W * ( 1 - ( 1 / COP ) )
    E_GHP_req_W = q_therm_W / COP

    C_GHP_el = E_GHP_req_W * gV.ELEC_PRICE

    return C_GHP_el, E_GHP_req_W, qcoldot_W, q_therm_W

def GHP_Op_max(tsup_K, tground_K, nProbes, gV):
    """
    For the operation of a Geothermal heat pump (GSHP) at maximum capacity supplying DHN.

    :type tsup_K : float
    :param tsup_K: supply temperature to the DHN (hot)
    :type tground_K : float
    :param tground_K: ground temperature
    :type nProbes: float
    :param nProbes: bumber of probes
    :param gV: globalvar.py

    :rtype qhotdot: float
    :returns qhotdot: heating energy provided from GHSP
    :rtype COP: float
    :returns COP: coefficient of performance of GSHP

    """

    qcoldot_Wh = nProbes * gV.GHP_Cmax_Size_th   # maximum capacity from all probes
    COP = gV.HP_etaex * (tsup_K + gV.HP_deltaT_cond) / ((tsup_K + gV.HP_deltaT_cond) - tground_K)
    qhotdot_Wh = qcoldot_Wh /( 1 - ( 1 / COP ) )

    return qhotdot_Wh, COP

def HPLake_op_cost(mdot_kgpers, t_sup_K, t_ret_K, tlake, gV):
    """
    For the operation of lake heat pump supplying DHN

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the DHN (hot)
    :type t_ret_K : float
    :param t_ret_K: return temeprature from the DHN (cold)
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

    E_HPLake_req_W, qcolddot_W = HPLake_Op(mdot_kgpers, t_sup_K, t_ret_K, tlake, gV)

    Q_therm_W = mdot_kgpers * gV.cp * (t_sup_K - t_ret_K)

    C_HPL_el = E_HPLake_req_W * gV.ELEC_PRICE

    Q_cold_primary_W = qcolddot_W

    return C_HPL_el, E_HPLake_req_W, Q_cold_primary_W, Q_therm_W

def HPLake_Op(mdot_kgpers, t_sup_K, t_ret_K, tlake_K, gV):
    """
    For the operation of a Heat pump between a district heating network and a lake

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the DHN (hot)
    :type t_ret_K : float
    :param t_ret_K: return temeprature from the DHN (cold)
    :type tlake_K : float
    :param tlake_K: lake temperature
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
    tcond_K = t_sup_K + gV.HP_deltaT_cond
    print tcond_K
    if tcond_K > gV.HP_maxT_cond:
        raise ModelError

    # calculate evaporator temperature
    tevap_K = tlake_K - gV.HP_deltaT_evap
    COP = gV.HP_etaex / (1- tevap_K/tcond_K)   # [L. Girardin et al., 2010]_
    qhotdot_W = mdot_kgpers * gV.cp * (t_sup_K - t_ret_K)

    if qhotdot_W > gV.HP_maxSize:
        print "Qhot above max size on the market !"

    wdot_W = qhotdot_W / COP
    E_HPLake_req_W = wdot_W / gV.HP_Auxratio     # compressor power [C. Montagud et al., 2014]_

    qcolddot_W =  qhotdot_W - wdot_W

    return E_HPLake_req_W, qcolddot_W

def HPSew_op_cost(mdot_kgpers, tsup_K, tret_K, tsupsew_K, gV):
    """
    Operation cost of sewage water HP supplying DHN

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type tsup_K : float
    :param tsup_K: supply temperature to the DHN (hot)
    :type tret_K : float
    :param tret_K: return temeprature from the DHN (cold)
    :type tsupsew_K : float
    :param tsupsew_K: sewage supply temperature
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

    COP = gV.HP_etaex * (tsup_K + gV.HP_deltaT_cond) / ((tsup_K + gV.HP_deltaT_cond) - tsupsew_K)
    q_therm_W = mdot_kgpers * gV.cp * (tsup_K - tret_K)
    qcoldot_W = q_therm_W*( 1 - ( 1 / COP ) )

    E_HPSew_req_W = q_therm_W / COP

    C_HPSew_el_pure = E_HPSew_req_W * gV.ELEC_PRICE
    C_HPSew_per_kWh_th_pure = C_HPSew_el_pure / (q_therm_W)

    return C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, qcoldot_W, q_therm_W, E_HPSew_req_W




# investment and maintenance costs

def calc_Cinv_GHP(GHP_Size_W, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    :type GHP_Size_W : float
    :param GHP_Size_W: Design electrical size of the heat pump in [Wel]

    :type InvCa : float
    :returns InvCa: annualized investment costs in [EUROS/a]

    ..[D. Bochatay et al., 2005] D. Bochatay, I. Blanc, O. Jolliet, F. Marechal, T. Manasse-Ratmandresy (2005). Project
    PACOGEN Evaluation economique et environmentale de systemes energetiques a usage residentiel., EPFL.
    """
    nProbe = floor(GHP_Size_W / gV.GHP_WmaxSize)
    roundProbe = GHP_Size_W / gV.GHP_WmaxSize - nProbe

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


def calc_Cinv_HP(HP_Size_W, gV):
    """
    Calculates the annualized investment costs for the heat pump

    :type HP_Size_W : float
    :param HP_Size_W: Design thermal size of the heat pump in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF/a]

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    if HP_Size_W > 0:
        InvC = (-493.53 * log(HP_Size_W * 1E-3) + 5484) * (HP_Size_W * 1E-3)
        InvCa = InvC * gV.HP_i * (1+ gV.HP_i) ** gV.HP_n / \
                ((1+gV.HP_i) ** gV.HP_n - 1)

    else:
        InvCa = 0

    return InvCa


def GHP_InvCost(GHP_Size_W, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    :type GHP_Size_W : float
    :param GHP_Size_W: Design electrical size of the heat pump in [Wel]

    InvCa : float
        annualized investment costs in EUROS/a
    """
    InvC_HP = 5247.5 * (GHP_Size_W * 1E-3) ** 0.49
    InvC_BH = 7100 * (GHP_Size_W * 1E-3) ** 0.74

    InvCa = InvC_HP * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / \
            ((1+gV.GHP_i) ** gV.GHP_nHP - 1) + \
            InvC_BH * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nBH / \
            ((1+gV.GHP_i) ** gV.GHP_nBH - 1)

    return InvCa


