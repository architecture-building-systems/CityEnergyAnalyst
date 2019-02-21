# -*- coding: utf-8 -*-
"""
Heating and cooling coils of Air handling units
"""
from __future__ import division
import scipy.optimize as sopt
import scipy
import numpy as np
from cea.technologies import substation
from cea.demand import constants

# import from GV
C_A = constants.C_A

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_heating_coil(Qhsf, Qhsf_0, Ta_sup_hs, Ta_re_hs, Ths_sup_0, Ths_re_0, ma_sup_hs, ma_sup_0, Ta_sup_0, Ta_re_0):
    '''
    this function calculates the state of the heat exchanger at the substation of every customer with heating needs in
    an analogous way to the cooling coil calculation

    :param Q: cooling load
    :param thi: in temperature of primary side
    :param tho: out temperature of primary side
    :param tci: in temperature of secondary side
    :param ch: capacity mass flow rate primary side
    :param ch_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of primary side
    :param tci_0: nominal in temperature of secondary side
    :param tho_0: nominal out temperature of primary side
    :param gv: path to global variables class

    :return:
        - tci = inlet temperature of secondary side (district heating network)
        - tco = out temperature of secondary side (district heating network)
        - cc = capacity mass flow rate secondary side
    '''

    Q = abs(Qhsf)
    Qnom = abs(Qhsf_0)
    tci = Ta_re_hs + 273
    tco = Ta_sup_hs + 273
    thi = Ths_sup_0 + 273
    tci_0 = Ta_re_0
    tco_0 = Ta_sup_0
    thi_0 = Ths_sup_0 + 273
    tho_0 = Ths_re_0 + 273
    cc = ma_sup_hs * C_A # WperC

    if Q > 0 and ma_sup_hs > 0:
        U_HEAT = 450.0  # W/m2K for air-based heat exchanger
        # nominal conditions network side
        dTm_0 = substation.calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0)
        # Area heat exchange and UA_heating
        Area_HEX_heating, UA_heating = substation.calc_area_HEX(Qnom, dTm_0, U_HEAT)
        tho, ch = np.vectorize(substation.calc_HEX_heating)(Q, UA_heating, thi, tco, tci, cc)

    else:
        thi = np.nan
        tho = np.nan
        ch = 0.0

    return np.float(thi-273), np.float(tho), np.float(ch)

    # tasup = Ta_sup_hs + 273
    # tare = Ta_re_hs + 273
    # tsh0 = Ths_sup_0 + 273
    # trh0 = Ths_re_0 + 273
    # mCw0 = Qhsf_0 / (tsh0 - trh0)
    #
    # # log mean temperature at nominal conditions
    # # https: // en.wikipedia.org / wiki / Logarithmic_mean_temperature_difference
    # TD10 = tsh0 - Ta_sup_0  # nominal temperature difference at hot end of heat exchanger
    # TD20 = trh0 - Ta_re_0  # nominal temperature difference at cold end of heat exchanger
    # LMRT0 = (TD10 - TD20) / scipy.log(TD10 / TD20)
    # UA0 = Qhsf_0 / LMRT0
    #
    # NTU_0 = UA0 / (ma_sup_0 * C_A)
    # ec_0 = 1 - scipy.exp(-NTU_0)
    #
    # if Qhsf > 0 and ma_sup_hs > 0:
    #     AUa = UA0 * (ma_sup_hs / ma_sup_0) ** 0.77
    #     NTUc = AUa / (ma_sup_hs * C_A)  # we removed a wrong unit conversion,
    #     #  according to HEX graphs NTU should be in the range of 3-5 (-), see e.g.
    #     #  http://kb.eng-software.com/display/ESKB/Difference+Between+the+Effectiveness-NTU+and+LMTD+Methods
    #     ec = 1 - scipy.exp(-NTUc)  # this is a very strong assumption. it is only valid for boilers and condensers.
    #     tc = (tasup - tare + tare * ec) / ec  # (contact temperature of coil)
    #     # We think tc calculated here is the minimum required hot water supply temperature
    #
    #     # minimum
    #     LMRT = abs((tsh0 - trh0) / scipy.log((tsh0 - tc) / (trh0 - tc)))  # we don't understand what is happening here
    #     k1 = 1 / mCw0
    #
    #     def fh(x):
    #         Eq = mCw0 * k2 - Qhsf_0 * (k2 / (scipy.log((x + k2 - tc) / (x - tc)) * LMRT))
    #         return Eq
    #
    #     k2 = Qhsf * k1
    #     try:
    #         result = sopt.newton(fh, trh0, maxiter=1000, tol=0.01).real - 273
    #     except RuntimeError:
    #         result = sopt.bisect(fh, 0, 350, xtol=0.01, maxiter=500).real - 273
    #
    #     tsh = result  # we swap the result to be the water supply temperature in accordance with `tc` above
    #     trh = tsh - k2  # the return temperature of the water, assuming some delta_T of k2
    #     mcphs = Qhsf / (tsh - trh)
    # else:
    #     tsh = np.nan
    #     trh = np.nan
    #     mcphs = 0
    # # return floats with numpy function. Needed when np.vectorize is use to call this function
    # return np.float(tsh), np.float(trh), np.float(mcphs) # C,C, W/C


# tci = DCN_supply['T_DC_supply_to_cs_ref_data_C'] + 273  # fixme: change according to cs_ref or ce_ref_data
# Qcs_sys_W = abs(Qcs_sys_kWh_dict[cs_configuration]) * 1000  # in W
# # only include space cooling and refrigeration
# Qnom_W = max(Qcs_sys_W)  # in W
# if Qnom_W > 0:
#     tho = cs_temperatures['Tcs_supply_C'] + 273  # in K
#     thi = cs_temperatures['Tcs_return_C'] + 273  # in K
#     ch = (mcpcs_sys_kWperC_dict[cs_configuration]) * 1000  # in W/K #fixme: recalculated with the Tsupply/return
#     index = np.where(Qcs_sys_W == Qnom_W)[0][0]
#     tci_0 = tci[index]  # in K
#     thi_0 = thi[index]
#     tho_0 = tho[index]
#     ch_0 = ch[index]
#     t_DC_return_cs, mcp_DC_cs, A_hex_cs = \
#         calc_substation_cooling(Qcs_sys_W, thi, tho, tci, ch, ch_0, Qnom_W, thi_0, tci_0,
#                                 tho_0)
# else:
#     t_DC_return_cs = tci
#     mcp_DC_cs = 0
#     A_hex_cs = 0

def calc_cooling_coil(Qcsf, Qcsf_0, Ta_sup_cs, Ta_re_cs, Tcs_sup_0, Tcs_re_0, ma_sup_cs, ma_sup_0, Ta_sup_0, Ta_re_0):
    '''
    this function calculates the state of the heat exchanger at the substation of every customer with cooling needs

    :param Q: cooling load
    :param thi: inlet temperature of primary side
    :param tho: outlet temperature of primary side
    :param tci: inlet temperature of secondary side
    :param ch: capacity mass flow rate primary side
    :param ch_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of primary side
    :param tci_0: nominal in temperature of secondary side
    :param tho_0: nominal out temperature of primary side
    :param gv: path to global variables class

    :return:
        - tci = inlet temperature of secondary side (district cooling network)
        - tco = outlet temperature of secondary side (district cooling network)
        - cc = capacity mass flow rate secondary side
    '''

    Q = abs(Qcsf)
    Qnom = abs(Qcsf_0)
    thi = Ta_re_cs + 273
    tho =  Ta_sup_cs + 273
    tci = Tcs_sup_0 + 273
    ch = ma_sup_cs * C_A # WperC
    ch_0 = ma_sup_0 * C_A # WperC
    thi_0 = Ta_re_0
    tho_0 = Ta_sup_0
    tci_0 = Tcs_sup_0 + 273
    tco_0 = Tcs_re_0 + 273

    if Q > 0 and ma_sup_cs > 0:
        U_COOL = 450.0  # W/m2K for air cooled heat exchanger
        # nominal conditions network side
        dTm_0 = substation.calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0)
        # Area heat exchange and UA_heating
        Area_HEX_cooling, UA_cooling = substation.calc_area_HEX(Qnom, dTm_0, U_COOL)
        tco, cc = np.vectorize(substation.calc_HEX_cooling)(Q, UA_cooling, thi, tho, tci, ch)
    else:
        tco = np.nan
        tci = np.nan
        cc = 0.0

    return np.float(tci-273), np.float(tco), np.float(cc)


# def calc_cooling_coil(Qcsf, Qcsf_0, Ta_sup_cs, Ta_re_cs, Tcs_sup_0, Tcs_re_0, ma_sup_cs, ma_sup_0, Ta_sup_0, Ta_re_0):
#     # Initialize temperatures
#     tasup = Ta_sup_cs + 273
#     tare = Ta_re_cs + 273
#     tsc0 = Tcs_sup_0 + 273
#     trc0 = Tcs_re_0 + 273
#     mCw0 = Qcsf_0 / (tsc0 - trc0)
#
#     # log mean temperature at nominal conditions
#     TD10 = Ta_sup_0 - trc0
#     TD20 = Ta_re_0 - tsc0
#     LMRT0 = (TD20 - TD10) / scipy.log(TD20 / TD10)
#     UA0 = Qcsf_0 / LMRT0
#
#     if Qcsf < -0 and ma_sup_cs > 0:
#         AUa = UA0 * (ma_sup_cs / ma_sup_0) ** 0.77
#         NTUc = AUa / (ma_sup_cs * C_A * 1000)
#         ec = 1 - scipy.exp(-NTUc)
#         tc = (tare - tasup + tasup * ec) / ec  # contact temperature of coil
#
#         def fh(x):
#             TD1 = tc - (k2 + x)
#             TD2 = tc - x
#             LMRT = (TD2 - TD1) / scipy.log(TD2 / TD1)
#             Eq = mCw0 * k2 - Qcsf_0 * (LMRT / LMRT0)
#             return Eq
#
#         k2 = -Qcsf / mCw0
#         try:
#             result = sopt.newton(fh, trc0, maxiter=1000, tol=0.01) - 273
#         except RuntimeError:
#             print('Newton optimization failed in cooling coil, using slower bisect algorithm...')
#             try:
#                 result = sopt.bisect(fh, 0, 350, xtol=0.01, maxiter=500) - 273
#             except RuntimeError:
#                 print ('Bisect optimization also failed in cooing coil, using sample:')
#
#
#         #if Ta_sup_cs == Ta_re_cs:
#         #    print 'Ta_sup_cs == Ta_re_cs:', Ta_sup_cs
#         tsc = result.real
#         trc = tsc + k2
#
#         #Control system check - close to optimal flow
#         min_AT = 5  # Its equal to 10% of the mass flowrate
#         tsc_min = Tcs_sup_0  # to consider coolest source possible
#         trc_max = Tcs_re_0
#         tsc_max = 12
#         AT = tsc - trc
#         if AT < min_AT:
#             if tsc < tsc_min:
#                 tsc = tsc_min
#                 trc = tsc_min + min_AT
#             if tsc > tsc_max:
#                 tsc = tsc_max
#                 trc = tsc_max + min_AT
#             else:
#                 trc = tsc + min_AT
#         elif tsc > tsc_max or trc > trc_max or tsc < tsc_min:
#             trc = trc_max
#             tsc = tsc_max
#
#         mcpcs = Qcsf / (tsc - trc)
#     else:
#         tsc = np.nan
#         trc = np.nan
#         mcpcs = 0
#     # return floats with numpy function. Needed when np.vectorize is use to call this function
#     return np.float(tsc), np.float(trc), np.float(mcpcs)  # C,C, W/C
