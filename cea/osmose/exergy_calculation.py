from __future__ import division
import numpy as np
import pandas as pd
import math
import pyromat as pm
import cea.osmose.auxiliary_functions as aux

# REF: D.Peng et al., 2017
Ra = 0.287  # kJ / kgK, ideal air constant for air
c_air_kJperkgK = 1.003  # kJ / kgK
c_vapor_kJperkgK = 1.872  # kJ / kgK


def calc_exergy_moist_air_1(T_air_C, w_air_gperkg, T_ref_C, w_ref_gperkg):
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
    ph_1 = c_air_kJperkgK + w_air_kgperkg * c_vapor_kJperkgK
    ph_2 = T_air_K / T_ref_K - 1 - math.log(T_air_K / T_ref_K)
    ex_ph = ph_1 * T_ref_K * ph_2  # eq.(5.49) first part
    # print('thermal exergy: ',ex_ph)

    # chemical exergy
    ch_1 = (1 + 1.608 * w_air_kgperkg)
    ch_2 = (1 + 1.608 * w_ref_kgperkg)
    ex_ch = Ra * T_ref_K * (math.log(ch_2 / ch_1) + 1.608 * w_air_kgperkg * math.log(w_air_kgperkg / w_ref_kgperkg) * (
            ch_2 / ch_1))  # eq.(5.49) third part
    # print('chemical exergy: ', ex_ch)
    ex_air_kJperkg = ex_ph + ex_ch
    return ex_air_kJperkg


def calc_exergy_moist_air_2(T_air_C, w_air_gperkg, T_ref_C, w_ref_gperkg):
    """
    Calculates exergy of moist air.
    :param T_air_C:
    :param w_air_gperkg:
    :param T_ref_C:
    :param w_ref_gperkg:
    :return:

    ..[Ren,C. et al.2002] Discussion Regarding the Principles of Exergy Analysis Applied to HVAC Systems. Journal of
    Asian Architecture and Building Engineering, 137-141.
    """
    if T_air_C > 0:
        T_ref_K = T_ref_C + 273.15
        T_air_K = T_air_C + 273.15
        w_air_kgperkg = w_air_gperkg / 1000
        w_ref_kgperkg = w_ref_gperkg / 1000

        # physical exergy
        ph_1 = c_air_kJperkgK + w_air_kgperkg * c_vapor_kJperkgK
        ph_2 = T_air_K - T_ref_K - T_ref_K * math.log(T_air_K / T_ref_K)
        ex_ph = ph_1 * ph_2  # eq.(2') first part
        # print('thermal exergy: ',ex_ph)

        # chemical exergy
        ch_1 = (1 + 1.608 * w_air_kgperkg)
        ch_2 = (1 + 1.608 * w_ref_kgperkg)
        ex_ch = Ra * T_ref_K * (ch_1 * math.log(ch_2 / ch_1)
                                + 1.608 * w_air_kgperkg * math.log(w_air_kgperkg / w_ref_kgperkg))  # eq.(2') third part
        # print('chemical exergy: ', ex_ch)
        ex_air_kJperkg = ex_ph + ex_ch
    else:
        ex_air_kJperkg = np.nan
    return ex_air_kJperkg


def calc_exergy_liquid_water(T_water_C, T_ref_C, RH):
    """
    Calculates exergy of liquid water as a single component substance.
    Equations assume the liquid water is in thermal equilibrium with the ambient.
    :param T_ref_C:
    :param w_ref_gperkg:
    :return:

    ..[Bejan,A.2016] Exergy Analysis. In Advanced Engineering Thermodynamics (pp.195-212).
    """
    T_ref_K = T_ref_C + 273.15
    T_water_K = T_water_C + 273.15
    # w_ref_kgperkg = w_ref_gperkg / 1000
    # w_sat_kgperkg = calc_w_sat(T_ref_C)
    # RH = w_ref_kgperkg / w_sat_kgperkg
    Rv = 0.4615  # kJ/kgK
    cp_water_kJperkgK = 4.187
    dT_water = T_water_K - T_ref_K
    ex_liquid_water_kJperkg = cp_water_kJperkgK * (dT_water) - T_ref_K * cp_water_kJperkgK * math.log(
        T_water_K / T_ref_K) - Rv * T_ref_K * math.log(RH)  # eq.(5.59) _[Bejan,A.2016]
    # print 'exergy_water at T_ref_C:', T_ref_C,'RH:',RH*100, ':', -Rv * T_ref_K * math.log(RH)
    return ex_liquid_water_kJperkg

def water_exergy_pyromat(T_water_C, T_ref_C):
    T_water_K = T_water_C + 273.15
    T_ref_K = T_ref_C + 273.15
    water = pm.get('mp.H2O')
    h_water_kJperkg = water.h(T_water_K)[0]
    s_water_kJperkgK = water.s(T_water_K)[0]
    ex_water = h_water_kJperkg - T_ref_K*s_water_kJperkgK
    ex_water_0 = water.h(T_ref_K)[0] - T_ref_K*water.s(T_ref_K)[0]
    return ex_water





def calc_Ex_Qc(Qc, T_RA_C, T_ref_C):
    T_ref_K = T_ref_C + 273.15
    T_RA_K = T_RA_C + 273.15
    Ex_Qc = Qc * (T_ref_K / T_RA_K - 1)
    return Ex_Qc

def calc_Ex_Qh(Qh, T_h_C, T_ref_C):
    T_ref_K = T_ref_C + 273.15
    T_h_K = T_h_C + 273.15
    Ex_Qc = Qh * (T_ref_K / T_h_K - 1)
    return Ex_Qc


def calc_ex_latent(T_ref_C, w_ref_gperkg):
    T_ref_K = T_ref_C + 273.15
    w_ref_kgperkg = w_ref_gperkg / 1000
    w_sat_kgperkg = aux.calc_w_ss_from_T(T_ref_C)
    a1 = (1 + 1.608 * w_ref_kgperkg) / (1 + 1.608 * w_sat_kgperkg)
    a2 = w_ref_kgperkg / w_sat_kgperkg
    ex_latent_kJperkg = 1.608 * Ra * T_ref_K * math.log(a1 * a2)
    return ex_latent_kJperkg


def calc_water_liquid_entropy(T_water_C):
    A = -203.6060
    B = 1523.290
    C = -3196.413
    D = 2474.455
    E = 3.855326
    F = -256.5478
    G = -488.7163
    H = -285.8304

    t = (T_water_C + 273.15) / 1000
    entropy = A * math.log(t) + B * t + (C * t ** 2) / 2 + (D * t ** 3) / 3 - E / (2 * t ** 2) + G
    return entropy


def calc_water_liquid_enthalpy(T_water_C):
    A, B, C, D, E, F, G, H = get_constant_shomate_eq('water liquid')
    t = (T_water_C + 273.15) / 1000
    entropy = A * t + (B * t ** 2) / 2 + (C * t ** 3) / 3 + (D * t ** 4) / 4 - E / t + F - H
    return entropy


def get_constant_shomate_eq(substance):
    if substance == 'water liquid':
        A = -203.6060
        B = 1523.290
        C = -3196.413
        D = 2474.455
        E = 3.855326
        F = -256.5478
        G = -488.7163
        H = -285.8304
    elif substance == 'water vapor':
        A = -203.6060
        B = 1523.290
        C = -3196.413
        D = 2474.455
        E = 3.855326
        F = -256.5478
        G = -488.7163
        H = -285.8304

    return A, B, C, D, E, F, G, H


def calc_water_entropy(T_water_C):
    T_ref_C = 30
    s_ref_kJperkgK = 0.43675
    cp_water_kJperkgK = 4.187
    delta_s = cp_water_kJperkgK * math.log((T_water_C + 273.15) / (T_ref_C + 273.15))
    s_kJperkgK = s_ref_kJperkgK + delta_s
    return s_kJperkgK


def calc_water_enthalpy(T_water_C):
    T_ref_C = 30
    h_ref_kJperkg = 125.73
    cp_water_kJperkgK = 4.187
    delta_h = cp_water_kJperkgK * (T_water_C - T_ref_C)
    h_kJperkg = h_ref_kJperkg + delta_h
    return h_kJperkg


def calc_exergy_condensation(T_ref_K, T_vapor_K, T_cond_K, h_fg_water):
    h_fg_water_kJperkg = 2450  # at Tcond
    part1 = c_vapor_kJperkgK * ((T_vapor_K - T_cond_K) - T_ref_K * math.log(T_vapor_K / T_cond_K))
    part2 = h_fg_water_kJperkg - T_ref_K * h_fg_water_kJperkg / T_cond_K
    ex_kJperkg = part1 + part2
    return ex_kJperkg


if __name__ == '__main__':
    # indoor air set points
    # T_air_C = 24
    # w_air_gperkg = 11.237  # 40% RH
    # T_0_C = 30
    # w_0_gperkg = 21.663  # 80% RH

    # Table 1, Beijing, Ren et al., 2001
    T_air_C = 33.2
    w_air_gperkg = 19.075  # Tw 26.4 C
    T_0_C = 33.2
    w_0s_gperkg = 33.042
    ex_moist_air_2 = calc_exergy_moist_air_2(T_air_C, w_air_gperkg, T_0_C, w_0s_gperkg)
    print 'ex outdoor air in Beijing: ', ex_moist_air_2, ' [kJ/kg]'  # 0.473 [kJ/kg]
    ##################################################################################
    # p.865 Marletta,2010
    T_air_C = 17
    w_air_gperkg = 9.5
    T_0_C = 32
    w_0_gperkg = 21.4
    w_0s_gperkg = aux.calc_w_ss_from_T(T_0_C) * 1000
    ex_moist_air_A = calc_exergy_moist_air_2(T_air_C, w_air_gperkg, T_0_C, w_0_gperkg)
    print 'ex A (Marletta,2010): ', ex_moist_air_A, ' [kJ/kg]'  #
    ####################################################################
    T_water_C = 12
    T_ref_C = 35.8
    T_ref_K = T_ref_C + 273.15
    w_0_gperkg = 19.746
    RH = 0.8
    ex_water = calc_exergy_liquid_water(T_water_C, T_ref_C, RH)
    print 'Ex,water: ', ex_water, ' [kJ/kg]'  #
    print "exergy water form pyromat: ", water_exergy_pyromat(T_water_C, T_ref_C)
    ex_latent = calc_ex_latent(T_ref_C, w_0_gperkg)
    print 'ex latent: ', ex_latent * (-0.7)
    T_room_K = 25 + 273.15
    T_water_K = T_water_C + 273.15
    ex_condensation = calc_exergy_condensation(T_ref_K, T_room_K, T_water_K, h_fg_water=2450)
    print 'ex condensation: ', ex_condensation

    s_water = calc_water_entropy(T_water_C)
    h_water = calc_water_enthalpy(T_water_C)
    print s_water, h_water
    ###############################################################
    water_liquid = pm.get('mp.H2O')
    water_gas = pm.get('ig.H2O')
    T = 20 + 273.15
    print "entropy of water(l): ", water_liquid.s(T=T, p=1.013)
    print "enthalpy of water: ", water_liquid.h(T=T)
    print "isobaric specific heat water(l): ", water_liquid.cp()
    print "cp (vapor): ", water_gas.cp(T=T)

    # print pm.config
