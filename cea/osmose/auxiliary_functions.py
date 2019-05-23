import math


def calc_h_from_T_w(T_C, w_gperkg):
    """
    h_OA1 = {unit='kJ/kg', job = function() return (c_air*T_OA1() - 0.026) + w_OA1()*(h_fg + c_vapor*T_OA1()) end},
    :return:
    """
    c_air = 1.007  # kJ/kg/K
    c_vapor = 1.84 / 1000  # kJ/kg/K
    h_fg = 2501 / 1000  # kJ/kg

    h_kJperkg = (c_air * T_C - 0.026) + w_gperkg * (h_fg + c_vapor * T_C)

    return h_kJperkg


def calc_w_ss_from_T(T_C):
    """
    LCU_P_ss_SA = {unit='kPa', job= function() return 10^(A-B/(C+LCU_T_SA()))*0.1333224 end},
    LCU_w_SA = {unit='g/kg', job=function() return 0.622*LCU_P_ss_SA()/(P_atm-LCU_P_ss_SA())*1000 end},
    :return:
    """
    A = 8.07131
    B = 1730.63
    C = 233.426
    P_atm = 101.325  # kPa
    P_ss = 10 ** (A - B / (C + T_C)) * 0.1333224
    w_ss_gperkg = 0.622 * P_ss / (P_atm - P_ss) * 1000
    return w_ss_gperkg


def p_ws_from_t(t_celsius):
    # convert temperature
    t = t_celsius + 273.15

    # constants
    C8 = -5.8002206E+03
    C9 = 1.3914993E+00
    C10 = -4.8640239E-02
    C11 = 4.1764768E-05
    C12 = -1.4452093E-08
    C13 = 6.5459673E+00

    return math.exp(C8 / t + C9 + C10 * t + C11 * t ** 2 + C12 * t ** 3 + C13 * math.log1p(t))


def calc_RH_from_w(w_gperkg, T_C):
    T_K = 273.15 + T_C
    C_gKperJ = 2.16679
    P_ws_Pa = p_ws_from_t(T_C)  # T in Celcius
    rho_air_kgperm3 = 1.19  # kg/m3
    rh = w_gperkg * rho_air_kgperm3 * T_K / (C_gKperJ * P_ws_Pa)
    return rh