from __future__ import division
from cea.optimization.constants import DELTA_P_COEFF, DELTA_P_ORIGIN, PUMP_ETA, EL_TO_OIL_EQ, EL_TO_CO2
import cea.technologies.chillers as VCCModel
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK

def cooling_resource_activator(cool_array, hour, Q_avail_W, gv, Q_from_Lake_cumulative_W, prices):
    """
    :param dataArray:
    :param el:
    :param Q_avail_W:
    :param TempSup:
    :type dataArray: list
    :type el:
    :type Q_avail_W: float?
    :type TempSup:
    :return: toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni
    :rtype: float, float, float, float, float, float, float
    """

    T_sup_K = cool_array[hour][0]
    T_re_K = cool_array[hour][1]
    mdot_kgpers = abs(cool_array[hour][2])

    Q_need_W = abs(mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_re_K - T_sup_K))

    opex_var_Lake = 0
    opex_var_VCC = 0
    co2_output_Lake = 0
    co2_output_VCC = 0
    prim_output_Lake = 0
    prim_output_VCC = 0
    calfactor_output = 0

    Q_from_Lake_W = 0
    Q_from_VCC_W = 0

    CT_Load_W = 0

    if Q_from_Lake_cumulative_W + Q_need_W <= Q_avail_W:  # Free cooling possible from the lake
        Q_from_Lake_W = Q_need_W

        # Delta P from linearization after distribution optimization
        deltaP = 2 * (DELTA_P_COEFF * mdot_kgpers + DELTA_P_ORIGIN)
        calfactor_output = deltaP * mdot_kgpers / 1000 / PUMP_ETA
        opex_var_Lake = deltaP * mdot_kgpers / 1000 * prices.ELEC_PRICE / PUMP_ETA
        co2_output_Lake = deltaP * mdot_kgpers / 1000 * EL_TO_CO2 / PUMP_ETA * 0.0036
        prim_output_Lake = deltaP * mdot_kgpers / 1000 * EL_TO_OIL_EQ / PUMP_ETA * 0.0036
    else:
        Q_from_VCC_W = Q_need_W
        wdot_W, qhotdot_W = VCCModel.calc_VCC(mdot_kgpers, T_sup_K, T_re_K, gv)
        opex_var_VCC = wdot_W * prices.ELEC_PRICE
        co2_output_VCC = wdot_W * EL_TO_CO2 * 3600E-6
        prim_output_VCC = wdot_W * EL_TO_OIL_EQ * 3600E-6
        CT_Load_W = qhotdot_W

    opex_output = {'Opex_var_Lake':opex_var_Lake,
                   'Opex_var_VCC': opex_var_VCC}

    co2_output = {'CO2_Lake': co2_output_Lake,
                  'CO2_VCC': co2_output_VCC}

    prim_output = {'Primary_Energy_Lake': prim_output_Lake,
                   'Primary_Energy_VCC': prim_output_VCC}

    Q_output = {'Q_from_Lake_W': Q_from_Lake_W,
                'Q_from_VCC_W': Q_from_VCC_W}

    return opex_output, co2_output, prim_output, Q_output, calfactor_output, CT_Load_W