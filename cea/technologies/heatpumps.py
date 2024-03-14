"""
heatpumps
"""





from math import log, ceil
import pandas as pd
from cea.optimization.constants import HP_DELTA_T_COND, HP_DELTA_T_EVAP, HP_ETA_EX, HP_ETA_EX_COOL, HP_AUXRATIO, \
    GHP_AUXRATIO, HP_MAX_T_COND, GHP_ETA_EX, HP_MAX_SIZE, HP_COP_MAX, HP_COP_MIN
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
import numpy as np
from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ============================
# technical model
# ============================

def calc_HP_const(q_load_Wh, COP):
    """
    Calculate heat pump operation for a fixed COP. Return required power supply and thermal energy drawn from
    the environment for a given heating load.

    :param q_load_Wh: Heating load in Watt-hours (single value or time series).
    :type q_load_Wh: int, float, list or pd.Series
    :param COP: Characteristic coefficient of performance of the heat pump
    :type COP: int, float

    :return q_env_in_Wh: Thermal energy drawn from the environment, i.e. earth, water or air (single value or time series)
    :rtype q_env_in_Wh: int, float, list or pd.Series
    :return p_supply_Wh: Electrical power supply required to provide the given heating load (single value or time series)
    :rtype p_supply_Wh: int, float, list or pd.Series
    """
    p_supply_Wh = q_load_Wh / COP
    q_env_in_Wh = q_load_Wh - p_supply_Wh
    return q_env_in_Wh, p_supply_Wh


def HP_air_air(mdot_cp_WC, t_sup_K, t_re_K, tsource_K):
    """
    For the operation of a heat pump (direct expansion unit) connected to minisplit units

    :type mdot_cp_WC : float
    :param mdot_cp_WC: capacity mass flow rate.
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the minisplit unit (cold)
    :type t_re_K : float
    :param t_re_K: return temperature from the minisplit unit (hot)
    :type tsource_K : float
    :param tsource_K: temperature of the source
    :rtype wdot_el : float
    :returns wdot_el: total electric power requirement for compressor and auxiliary el.
    :rtype qcolddot : float
    :returns qcolddot: cold power requirement

    ..[C. Montagud et al., 2014] C. Montagud, J.M. Corberan, A. Montero (2014). In situ optimization methodology for
    the water circulation pump frequency of ground source heat pump systems. Energy and Buildings

    + reverse cycle
    """
    if mdot_cp_WC > 0.0:
        # calculate condenser temperature
        tcond_K = tsource_K
        # calculate evaporator temperature
        tevap_K = t_sup_K # approximate evaporator temperature with air-side supply temperature
        # calculate COP
        if np.isclose(tcond_K, tevap_K):
            print('condenser temperature is equal to evaporator temperature, COP set to the maximum')
            COP = HP_COP_MAX
        else:
            COP = HP_ETA_EX_COOL * tevap_K / (tcond_K - tevap_K)

        # in order to work in the limits of the equation
        if COP > HP_COP_MAX:
            COP = HP_COP_MAX
        elif COP < 1.0:
            COP = HP_COP_MIN

        qcolddot_W = mdot_cp_WC * (t_re_K - t_sup_K)

        wdot_W = qcolddot_W / COP
        E_req_W = wdot_W / HP_AUXRATIO     # compressor power [C. Montagud et al., 2014]_

    else:
        E_req_W = 0.0

    return E_req_W


def calc_Cop_GHP(ground_temp_K, mdot_kgpers, T_DH_sup_K, T_re_K):
    """
    For the operation of a Geothermal heat pump (GSHP) supplying DHN.

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type T_DH_sup_K : float
    :param T_DH_sup_K: supply temperature to the DHN (hot)
    :type T_re_K : float
    :param T_re_K: return temperature from the DHN (cold)

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
    tcond_K = T_DH_sup_K + HP_DELTA_T_COND
    if tcond_K > HP_MAX_T_COND:
        #raise ModelError
        tcond_K = HP_MAX_T_COND
        tsup2_K = tcond_K - HP_DELTA_T_COND  # lower the supply temp if necessary, tsup2 < tsup if max load is not enough

    # calculate evaporator temperature
    tevap_K = ground_temp_K - HP_DELTA_T_EVAP
    COP = GHP_ETA_EX / (1 - tevap_K / tcond_K)     # [O. Ozgener et al., 2005]_

    qhotdot_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (tsup2_K - T_re_K)
    qhotdot_missing_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_DH_sup_K - tsup2_K) #calculate the missing energy if tsup2 < tsup

    wdot_W = qhotdot_W / COP
    wdot_el_W = wdot_W / GHP_AUXRATIO     # compressor power [C. Montagud et al., 2014]_

    qcolddot_W =  qhotdot_W - wdot_W

    return wdot_el_W, qcolddot_W, qhotdot_missing_W, tsup2_K

# ============================
# operation cost
# ============================

def GHP_op_cost(mdot_kgpers, t_sup_K, t_re_K, t_sup_GHP_K, Q_therm_GHP_W):
    """
    Operation cost of sewage water HP supplying DHN

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the DHN (hot)
    :type t_re_K : float
    :param t_re_K: return temperature from the DHN (cold)
    :type t_sup_GHP_K : float
    :param t_sup_GHP_K: sewage supply temperature
    :rtype C_HPSew_el_pure: float
    :returns C_HPSew_el_pure: electricity cost of sewage water HP operation

    :rtype C_HPSew_per_kWh_th_pure: float
    :returns C_HPSew_per_kWh_th_pure: electricity cost per kWh thermal energy produced from sewage water HP

    :rtype qcoldot: float
    :returns qcoldot: cold power requirement

    :rtype q_therm: float
    :returns q_therm: thermal energy supplied to DHN

    :rtype wdot: float
    :returns wdot: electricity required for sewage water HP operation

    ..[L. Girardin et al., 2010] L. Girardin, F. Marechal, M. Dubuis, N. Calame-Darbellay, D. Favrat (2010). EnerGis:
    a geographical information based system for the evaluation of integrated energy conversion systems in urban areas,
    Energy.

    """

    if (t_sup_K + HP_DELTA_T_COND) == t_sup_GHP_K:
        COP = 1
    else:
        COP = HP_ETA_EX * (t_sup_K + HP_DELTA_T_COND) / ((t_sup_K + HP_DELTA_T_COND) - t_sup_GHP_K)

    if t_sup_K == t_re_K:
        q_therm_W = 0
        qcoldot_W = 0
        E_GHP_req_W = 0
    else:
        q_therm_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (t_sup_K - t_re_K)
        if q_therm_W > Q_therm_GHP_W:
            q_therm_W = Q_therm_GHP_W
        qcoldot_W = q_therm_W * (1 - (1 / COP))
        E_GHP_req_W = q_therm_W / COP

    return E_GHP_req_W, qcoldot_W, q_therm_W


def GHP_Op_max(Q_max_GHP_W, tsup_K, tground_K):
    """
    For the operation of a Geothermal heat pump (GSHP) at maximum capacity supplying DHN.

    :type tsup_K : float
    :param tsup_K: supply temperature to the DHN (hot)
    :type tground_K : float
    :param tground_K: ground temperature
    :type nProbes: float
    :param nProbes: number of probes
    :rtype qhotdot: float
    :returns qhotdot: heating energy provided from GHSP
    :rtype COP: float
    :returns COP: coefficient of performance of GSHP

    """

    COP = HP_ETA_EX * (tsup_K + HP_DELTA_T_COND) / ((tsup_K + HP_DELTA_T_COND) - tground_K)
    qhotdot_Wh = Q_max_GHP_W /( 1 - ( 1 / COP ) )

    return qhotdot_Wh, COP

def HPLake_op_cost(Q_gen_W, tsup_K, tret_K, tlake):
    """
    For the operation of lake heat pump supplying DHN

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type tsup_K : float
    :param tsup_K: supply temperature to the DHN (hot)
    :type tret_K : float
    :param tret_K: return temperature from the DHN (cold)
    :type tlake : float
    :param tlake: lake temperature
    :rtype C_HPL_el: float
    :returns C_HPL_el: electricity cost of Lake HP operation

    :rtype wdot: float
    :returns wdot: electricity required for Lake HP operation

    :rtype Q_cold_primary: float
    :returns Q_cold_primary: cold power requirement

    :rtype Q_therm: float
    :returns Q_therm: thermal energy supplied to DHN

    """
    mdot_kgpers = Q_gen_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tsup_K - tret_K))

    E_HPLake_req_W, qcolddot_W = HPLake_Op(mdot_kgpers, tsup_K, tret_K, tlake)

    Q_therm_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (tsup_K - tret_K)

    Q_cold_primary_W = qcolddot_W

    return E_HPLake_req_W, Q_cold_primary_W, Q_therm_W

def HPLake_Op(mdot_kgpers, t_sup_K, t_re_K, t_lake_K):
    """
    For the operation of a Heat pump between a district heating network and a lake

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the DHN (hot)
    :type t_re_K : float
    :param t_re_K: return temperature from the DHN (cold)
    :type t_lake_K : float
    :param t_lake_K: lake temperature
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
    tcond = t_sup_K + HP_DELTA_T_COND
    if tcond > HP_MAX_T_COND:
        tcond = HP_MAX_T_COND

    # calculate evaporator temperature
    tevap_K = t_lake_K - HP_DELTA_T_EVAP
    COP = HP_ETA_EX / (1 - tevap_K / tcond)   # [L. Girardin et al., 2010]_
    q_hotdot_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (t_sup_K - t_re_K)

    if q_hotdot_W > HP_MAX_SIZE:
        print("Qhot above max size on the market !")

    wdot_W = q_hotdot_W / COP
    E_HPLake_req_W = wdot_W / HP_AUXRATIO     # compressor power [C. Montagud et al., 2014]_

    q_colddot_W =  q_hotdot_W - wdot_W

    return E_HPLake_req_W, q_colddot_W

def HPSew_op_cost(mdot_kgpers, t_sup_K, t_re_K, t_sup_sew_K, Q_therm_Sew_W):
    """
    Operation cost of sewage water HP supplying DHN

    :type mdot_kgpers : float
    :param mdot_kgpers: supply mass flow rate to the DHN
    :type t_sup_K : float
    :param t_sup_K: supply temperature to the DHN (hot)
    :type t_re_K : float
    :param t_re_K: return temperature from the DHN (cold)
    :type t_sup_sew_K : float
    :param t_sup_sew_K: sewage supply temperature
    :rtype C_HPSew_el_pure: float
    :returns C_HPSew_el_pure: electricity cost of sewage water HP operation

    :rtype C_HPSew_per_kWh_th_pure: float
    :returns C_HPSew_per_kWh_th_pure: electricity cost per kWh thermal energy produced from sewage water HP

    :rtype qcoldot: float
    :returns qcoldot: cold power requirement

    :rtype q_therm: float
    :returns q_therm: thermal energy supplied to DHN

    :rtype wdot: float
    :returns wdot: electricity required for sewage water HP operation

    ..[L. Girardin et al., 2010] L. Girardin, F. Marechal, M. Dubuis, N. Calame-Darbellay, D. Favrat (2010). EnerGis:
    a geographical information based system for the evaluation of integrated energy conversion systems in urban areas,
    Energy.

    """

    if (t_sup_K + HP_DELTA_T_COND) == t_sup_sew_K:
        COP = 1
    else:
        COP = HP_ETA_EX * (t_sup_K + HP_DELTA_T_COND) / ((t_sup_K + HP_DELTA_T_COND) - t_sup_sew_K)

    if t_sup_sew_K >= t_sup_K + HP_DELTA_T_COND:
        q_therm_W = Q_therm_Sew_W
        qcoldot_W = Q_therm_Sew_W
        E_HPSew_req_W = 0.0
    else:
        q_therm_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (t_sup_K - t_re_K)
        if q_therm_W > Q_therm_Sew_W:
            q_therm_W = Q_therm_Sew_W
        qcoldot_W = q_therm_W * (1 - (1 / COP))
        E_HPSew_req_W = q_therm_W / COP

    return qcoldot_W, q_therm_W, E_HPSew_req_W


def calc_Cinv_HP(HP_Size, locator, technology_type):
    """
    Calculates the annualized investment costs for a water to water heat pump.

    :type HP_Size : float
    :param HP_Size: Design thermal size of the heat pump in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF/a]

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    Capex_a_HP_USD = 0.0
    Opex_fixed_HP_USD = 0.0
    Capex_HP_USD = 0.0

    if HP_Size > 0.0:
        HP_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="HP")
        HP_cost_data = HP_cost_data[HP_cost_data['code'] == technology_type]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if HP_Size < HP_cost_data.iloc[0]['cap_min']:
            HP_Size = HP_cost_data.iloc[0]['cap_min']

        max_HP_size = max(HP_cost_data['cap_max'].values)

        if HP_Size <= max_HP_size:

            HP_cost_data = HP_cost_data[
                (HP_cost_data['cap_min'] <= HP_Size) & (HP_cost_data['cap_max'] > HP_Size)]

            Inv_a = HP_cost_data.iloc[0]['a']
            Inv_b = HP_cost_data.iloc[0]['b']
            Inv_c = HP_cost_data.iloc[0]['c']
            Inv_d = HP_cost_data.iloc[0]['d']
            Inv_e = HP_cost_data.iloc[0]['e']
            Inv_IR = HP_cost_data.iloc[0]['IR_%']
            Inv_LT = HP_cost_data.iloc[0]['LT_yr']
            Inv_OM = HP_cost_data.iloc[0]['O&M_%'] / 100

            InvC = Inv_a + Inv_b * (HP_Size) ** Inv_c + (Inv_d + Inv_e * HP_Size) * log(HP_Size)

            Capex_a_HP_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
            Opex_fixed_HP_USD = InvC * Inv_OM
            Capex_HP_USD = InvC

        else:
            number_of_chillers = int(ceil(HP_Size / max_HP_size))
            Q_nom_each_chiller = HP_Size / number_of_chillers
            HP_cost_data = HP_cost_data[
                (HP_cost_data['cap_min'] <= Q_nom_each_chiller) & (HP_cost_data['cap_max'] > Q_nom_each_chiller)]

            for i in range(number_of_chillers):

                Inv_a = HP_cost_data.iloc[0]['a']
                Inv_b = HP_cost_data.iloc[0]['b']
                Inv_c = HP_cost_data.iloc[0]['c']
                Inv_d = HP_cost_data.iloc[0]['d']
                Inv_e = HP_cost_data.iloc[0]['e']
                Inv_IR = HP_cost_data.iloc[0]['IR_%']
                Inv_LT = HP_cost_data.iloc[0]['LT_yr']
                Inv_OM = HP_cost_data.iloc[0]['O&M_%'] / 100

                InvC = Inv_a + Inv_b * (Q_nom_each_chiller) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_chiller) * log(Q_nom_each_chiller)

                Capex_a_HP_USD += calc_capex_annualized(InvC, Inv_IR, Inv_LT)
                Opex_fixed_HP_USD += InvC * Inv_OM
                Capex_HP_USD += InvC
    else:
        Capex_a_HP_USD = Opex_fixed_HP_USD = Capex_HP_USD = 0.0

    return Capex_a_HP_USD, Opex_fixed_HP_USD, Capex_HP_USD


def calc_Cinv_GHP(GHP_Size_W, GHP_cost_data, BH_cost_data):
    """
    Calculates the annualized investment costs for the geothermal heat pump

    :type GHP_Size_W : float
    :param GHP_Size_W: Design electrical size of the heat pump in [Wel]

    InvCa : float
        annualized investment costs in EUROS/a
    """
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if GHP_Size_W < GHP_cost_data['cap_min'][0]:
        GHP_Size_W = GHP_cost_data['cap_min'][0]
    GHP_cost_data = GHP_cost_data[
        (GHP_cost_data['cap_min'] <= GHP_Size_W) & (GHP_cost_data['cap_max'] > GHP_Size_W)]

    Inv_a = GHP_cost_data.iloc[0]['a']
    Inv_b = GHP_cost_data.iloc[0]['b']
    Inv_c = GHP_cost_data.iloc[0]['c']
    Inv_d = GHP_cost_data.iloc[0]['d']
    Inv_e = GHP_cost_data.iloc[0]['e']
    Inv_IR = GHP_cost_data.iloc[0]['IR_%']
    Inv_LT = GHP_cost_data.iloc[0]['LT_yr']
    Inv_OM = GHP_cost_data.iloc[0]['O&M_%'] / 100

    InvC_GHP = Inv_a + Inv_b * (GHP_Size_W) ** Inv_c + (Inv_d + Inv_e * GHP_Size_W) * log(GHP_Size_W)

    Capex_a_GHP_USD = calc_capex_annualized(InvC_GHP, Inv_IR, Inv_LT)
    Opex_fixed_GHP_USD = InvC_GHP * Inv_OM

    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if GHP_Size_W < BH_cost_data['cap_min'][0]:
        GHP_Size_W = BH_cost_data['cap_min'][0]
    BH_cost_data = BH_cost_data[
        (BH_cost_data['cap_min'] <= GHP_Size_W) & (BH_cost_data['cap_max'] > GHP_Size_W)]

    Inv_a = BH_cost_data.iloc[0]['a']
    Inv_b = BH_cost_data.iloc[0]['b']
    Inv_c = BH_cost_data.iloc[0]['c']
    Inv_d = BH_cost_data.iloc[0]['d']
    Inv_e = BH_cost_data.iloc[0]['e']
    Inv_IR = BH_cost_data.iloc[0]['IR_%']
    Inv_LT = BH_cost_data.iloc[0]['LT_yr']
    Inv_OM = BH_cost_data.iloc[0]['O&M_%'] / 100

    InvC_BH = Inv_a + Inv_b * (GHP_Size_W) ** Inv_c + (Inv_d + Inv_e * GHP_Size_W) * log(GHP_Size_W)

    Capex_a_BH_USD = calc_capex_annualized(InvC_BH, Inv_IR, Inv_LT)
    Opex_fixed_BH_USD = InvC_BH * Inv_OM

    Capex_a_GHP_total_USD = Capex_a_BH_USD + Capex_a_GHP_USD
    Opex_fixed_GHP_total_USD = Opex_fixed_BH_USD + Opex_fixed_GHP_USD
    Capex_GHP_total_USD = InvC_BH + InvC_GHP

    return Capex_a_GHP_total_USD, Opex_fixed_GHP_total_USD, Capex_GHP_total_USD