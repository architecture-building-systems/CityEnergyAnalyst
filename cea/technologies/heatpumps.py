"""
heatpumps
"""


from __future__ import division
from math import floor, log
import pandas as pd


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


def calc_Cinv_HP(HP_Size, gV, locator, technology=1):
    """
    Calculates the annualized investment costs for a water to water heat pump.

    :type HP_Size : float
    :param HP_Size: Design thermal size of the heat pump in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF/a]

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    if HP_Size > 0:
        HP_cost_data = pd.read_excel(locator.get_supply_systems_cost(), sheetname="HP")
        technology_code = list(set(HP_cost_data['code']))
        HP_cost_data[HP_cost_data['code'] == technology_code[technology]]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if HP_Size < HP_cost_data['cap_min'][0]:
            HP_Size = HP_cost_data['cap_min'][0]
        HP_cost_data = HP_cost_data[
            (HP_cost_data['cap_min'] <= HP_Size) & (HP_cost_data['cap_max'] > HP_Size)]

        Inv_a = HP_cost_data.iloc[0]['a']
        Inv_b = HP_cost_data.iloc[0]['b']
        Inv_c = HP_cost_data.iloc[0]['c']
        Inv_d = HP_cost_data.iloc[0]['d']
        Inv_e = HP_cost_data.iloc[0]['e']
        Inv_IR = (HP_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = HP_cost_data.iloc[0]['LT_yr']
        Inv_OM = HP_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (HP_Size) ** Inv_c + (Inv_d + Inv_e * HP_Size) * log(HP_Size)

        Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
        Opex_fixed = Capex_a * Inv_OM

    else:
        Capex_a = 0
        Opex_fixed = 0

    return Capex_a, Opex_fixed


def calc_Cinv_GHP(GHP_Size, gV, locator, technology=0):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    :type GHP_Size : float
    :param GHP_Size: Design electrical size of the heat pump in [Wel]

    InvCa : float
        annualized investment costs in EUROS/a
    """

    GHP_cost_data = pd.read_excel(locator.get_supply_systems_cost(), sheetname="HP")
    technology_code = list(set(GHP_cost_data['code']))
    GHP_cost_data[GHP_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if GHP_Size < GHP_cost_data['cap_min'][0]:
        GHP_Size = GHP_cost_data['cap_min'][0]
    GHP_cost_data = GHP_cost_data[
        (GHP_cost_data['cap_min'] <= GHP_Size) & (GHP_cost_data['cap_max'] > GHP_Size)]

    Inv_a = GHP_cost_data.iloc[0]['a']
    Inv_b = GHP_cost_data.iloc[0]['b']
    Inv_c = GHP_cost_data.iloc[0]['c']
    Inv_d = GHP_cost_data.iloc[0]['d']
    Inv_e = GHP_cost_data.iloc[0]['e']
    Inv_IR = (GHP_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = GHP_cost_data.iloc[0]['LT_yr']
    Inv_OM = GHP_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (GHP_Size) ** Inv_c + (Inv_d + Inv_e * GHP_Size) * log(GHP_Size)

    Capex_a_GHP = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_GHP = Capex_a_GHP * Inv_OM

    BH_cost_data = pd.read_excel(locator.get_supply_systems_cost(), sheetname="BH")
    technology_code = list(set(BH_cost_data['code']))
    BH_cost_data[BH_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if GHP_Size < BH_cost_data['cap_min'][0]:
        GHP_Size = BH_cost_data['cap_min'][0]
    BH_cost_data = BH_cost_data[
        (BH_cost_data['cap_min'] <= GHP_Size) & (BH_cost_data['cap_max'] > GHP_Size)]

    Inv_a = BH_cost_data.iloc[0]['a']
    Inv_b = BH_cost_data.iloc[0]['b']
    Inv_c = BH_cost_data.iloc[0]['c']
    Inv_d = BH_cost_data.iloc[0]['d']
    Inv_e = BH_cost_data.iloc[0]['e']
    Inv_IR = (BH_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = BH_cost_data.iloc[0]['LT_yr']
    Inv_OM = BH_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (GHP_Size) ** Inv_c + (Inv_d + Inv_e * GHP_Size) * log(GHP_Size)

    Capex_a_BH = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_BH = Capex_a_BH * Inv_OM

    Capex_a = Capex_a_BH + Capex_a_GHP
    Opex_fixed = Opex_fixed_BH + Opex_fixed_GHP

    return Capex_a, Opex_fixed


