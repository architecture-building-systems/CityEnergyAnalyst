from __future__ import division
import numpy as np
import pandas as pd
import math

# REF: D.Peng et al., 2017
Ra = 0.287  # kJ / kgK, ideal air constant for air
c_air = 1.006  # kJ / kgK
c_vapor = 1.84  # kJ / kgK


def calc_exergy_moist_air(T_air_C, w_air_gperkg, T_ref_C, w_ref_gperkg):
    """
    Calculates exergy of moist air.
    :param T_air_C:
    :param w_air_gperkg:
    :param T_ref_C:
    :param w_ref_gperkg:
    :return:

    ..[Bejan,A.2016] Exergy Analysis. In Advanced Engineering Thermodynamics (pp.195-212).
    """
    T_ref_K = T_ref_C + 273.15
    T_air_K = T_air_C + 273.15
    w_air_kgperkg = w_air_gperkg / 1000
    w_ref_kgperkg = w_ref_gperkg / 1000

    # physical exergy
    ph_1 = c_air + w_air_kgperkg * c_vapor
    ph_2 = T_air_K / T_ref_K - 1 - math.log(T_air_K / T_ref_K)
    ex_ph = ph_1 * T_ref_K * ph_2  # eq.(5.49) first part
    # print('thermal exergy: ',ex_ph)

    # chemical exergy
    ch_1 = (1 + 1.608 * w_air_kgperkg)
    ch_2 = (1 + 1.608 * w_ref_kgperkg)
    ex_ch = Ra * T_ref_K * (
            ch_1 * math.log(ch_2 / ch_1) + 1.608 * w_air_kgperkg * math.log(
        w_air_kgperkg / w_ref_kgperkg))  # eq.(5.49) third part
    # print('chemical exergy: ', ex_ch)
    ex_air_kJperkg = ex_ph + ex_ch
    return ex_air_kJperkg


def calc_exergy_liquid_water(T_ref_C, w_ref_gperkg):
    """
    Calculates exergy of liquid water as a single component substance.
    Equations assume the liquid water is in thermal equilibrium with the ambient.
    :param T_ref_C:
    :param w_ref_gperkg:
    :return:

    ..[Bejan,A.2016] Exergy Analysis. In Advanced Engineering Thermodynamics (pp.195-212).
    """
    T_ref_K = T_ref_C + 273.15
    w_ref_kgperkg = w_ref_gperkg / 1000
    w_sat_kgperkg = calc_w_sat(T_ref_C)
    RH = w_ref_kgperkg / w_sat_kgperkg
    Rv = 0.4615  # kJ/kgK
    ex_liquid_water_kJperkg = -Rv * T_ref_K * math.log(RH)  # eq.(5.59) _[Bejan,A.2016]
    return ex_liquid_water_kJperkg


def calc_w_sat(T):
    # Antoine Equation
    A = 8.07131
    B = 1730.63
    C = 233.426
    P_sat = (10 ** (A - B / (C + T))) * 0.1333224
    P_atm = 101.325  # kPa
    w_sat_kgperkg = 0.622 * P_sat / (P_atm - P_sat)
    return w_sat_kgperkg


def calc_Ex_Qc(Qc, T_RA_C, T_ref_C):
    T_ref_K = T_ref_C + 273.15
    T_RA_K = T_RA_C + 273.15
    Ex_Qc = Qc * (T_ref_K/T_RA_K-1)
    return Ex_Qc


if __name__ == '__main__':
    # indoor air set points
    T_air_C = 24
    w_air_gperkg = 11.237  # 40% RH
    T_0_C = 30
    w_0_gperkg = 21.663  # 80% RH

    ex_moist_air = calc_exergy_moist_air(T_air_C, w_air_gperkg, T_0_C, w_0_gperkg)
    print ('ex_moist_air: ', ex_moist_air, ' [kJ/kg]')  #

    ex_water = calc_exergy_liquid_water(T_0_C, w_0_gperkg)
    print ('ex_water: ', ex_water, ' [kJ/kg]')  #