from __future__ import division
import copy
import numpy as np
from cea.optimization.constants import *
from cea.optimization import prices
import pandas as pd
import cea.technologies.cooling_tower as CTModel
import cea.technologies.chillers as VCCModel
import cea.technologies.pumps as PumpModel

def cooling_resource_activator(cool_array, hour, Q_avail_W, gv, Q_from_Lake_cumulative_W, prices, TempSup):
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

    # if TempSup > 0:
    # print (cool_array[hour])
    T_sup_K = TempSup
    T_re_K = cool_array[hour][-2]
    mdot_kgpers = abs(cool_array[hour][-1])
    # else:
    #     T_sup_K = cool_array[hour][-3] + 273
    #     T_re_K = cool_array[hour][-2] + 273
    #     mdot_kgpers = abs(cool_array[hour][-1] * 1E3 / gv.cp)

    Q_need_W = abs(mdot_kgpers * gv.cp * (T_re_K - T_sup_K))

    if Q_from_Lake_cumulative_W + Q_need_W <= Q_avail_W:  # Free cooling possible from the lake
        Q_from_Lake_W = Q_need_W
        Q_from_VCC_W = 0
        CT_Load_W = 0
        # Delta P from linearization after distribution optimization
        deltaP = 2 * (DeltaP_Coeff * mdot_kgpers + DeltaP_Origin)
        calfactor_output = deltaP * mdot_kgpers / 1000 / etaPump
        opex_output = deltaP * mdot_kgpers / 1000 * prices.ELEC_PRICE / etaPump
        co2_output = deltaP * mdot_kgpers / 1000 * EL_TO_CO2 / etaPump * 0.0036
        prim_output = deltaP * mdot_kgpers / 1000 * EL_TO_OIL_EQ / etaPump * 0.0036
    else:
        Q_from_Lake_W = 0
        Q_from_VCC_W = Q_need_W
        wdot_W, qhotdot_W = VCCModel.calc_VCC(mdot_kgpers, T_sup_K, T_re_K, gv)
        calfactor_output = 0
        opex_output = wdot_W * prices.ELEC_PRICE
        co2_output = wdot_W * EL_TO_CO2 * 3600E-6
        prim_output = wdot_W * EL_TO_OIL_EQ * 3600E-6
        CT_Load_W = qhotdot_W

    return opex_output, co2_output, prim_output, calfactor_output, Q_from_Lake_W, Q_from_VCC_W, CT_Load_W