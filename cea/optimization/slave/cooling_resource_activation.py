from __future__ import division
import copy
import numpy as np
from cea.optimization.constants import *
from cea.optimization import prices
import pandas as pd

def cooling_resource_activator(dataArray, el, Q_availIni_W, TempSup=0):
    """
    :param dataArray:
    :param el:
    :param Q_availIni_W:
    :param TempSup:
    :type dataArray: list
    :type el:
    :type Q_availIni_W: float?
    :type TempSup:
    :return: toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni
    :rtype: float, float, float, float, float, float, float
    """
    Q_cooling_total = 0
    calfactor_total = 0
    opex_total = 0
    co2_total = 0
    prim_total = 0

    Q_availCopy_W = Q_availIni_W
    VCC_nom_Ini_W = 0

    for i in range(8760):

        if TempSup > 0:
            T_sup_K = TempSup
            T_re_K = dataArray[i][-2]
            mdot_kgpers = abs(dataArray[i][-1])
        else:
            T_sup_K = dataArray[i][-3] + 273
            T_re_K = dataArray[i][-2] + 273
            mdot_kgpers = abs(dataArray[i][-1] * 1E3 / gv.cp)

        Q_need_W = abs(mdot_kgpers * gv.cp * (T_re_K - T_sup_K))
        Q_cooling_total += Q_need_W

        if Q_availCopy_W - Q_need_W >= 0:  # Free cooling possible from the lake
            Q_availCopy_W -= Q_need_W

            # Delta P from linearization after distribution optimization
            deltaP = 2 * (DeltaP_Coeff * mdot_kgpers + DeltaP_Origin)

            calfactor_total += deltaP * mdot_kgpers / 1000 / etaPump
            opex_total += deltaP * mdot_kgpers / 1000 * prices.ELEC_PRICE / etaPump
            co2_total += deltaP * mdot_kgpers / 1000 * EL_TO_CO2 / etaPump * 0.0036
            prim_total += deltaP * mdot_kgpers / 1000 * EL_TO_OIL_EQ / etaPump * 0.0036

        else:
            wdot_W, qhotdot_W = VCCModel.calc_VCC(mdot_kgpers, T_sup_K, T_re_K, gv)
            if Q_need_W > VCC_nom_Ini_W:
                VCC_nom_Ini_W = Q_need_W * (1 + Qmargin_Disc)

            opex_total += wdot_W * prices.ELEC_PRICE
            co2_total += wdot_W * EL_TO_CO2 * 3600E-6
            prim_total += wdot_W * EL_TO_OIL_EQ * 3600E-6

            CT_Load_W[i] += qhotdot_W

    return opex_total, co2_total, prim_total, calfactor_total, Q_cooling_total, Q_availCopy_W, VCC_nom_Ini_W