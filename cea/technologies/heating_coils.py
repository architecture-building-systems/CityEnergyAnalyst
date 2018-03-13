# -*- coding: utf-8 -*-
"""
Heating and cooling coils of Air handling units
"""
from __future__ import division
import scipy.optimize as sopt
import scipy
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_heating_coil(Qhsf, Qhsf_0, Ta_sup_hs, Ta_re_hs, Ths_sup_0, Ths_re_0, ma_sup_hs, ma_sup_0,Ta_sup_0, Ta_re_0,
                      Cpa):

    tasup = Ta_sup_hs + 273
    tare = Ta_re_hs + 273
    tsh0 = Ths_sup_0 + 273
    trh0 = Ths_re_0 + 273
    mCw0 = Qhsf_0 / (tsh0 - trh0)

    # log mean temperature at nominal conditions
    TD10 = Ta_sup_0 - trh0
    TD20 = Ta_re_0 - tsh0
    LMRT0 = (TD10 - TD20) / scipy.log(TD20 / TD10)
    UA0 = Qhsf_0 / LMRT0

    if Qhsf > 0 and ma_sup_hs > 0:
        AUa = UA0 * (ma_sup_hs / ma_sup_0) ** 0.77
        NTUc = AUa / (ma_sup_hs * Cpa * 1000)
        ec = 1 - scipy.exp(-NTUc)
        tc = (tare - tasup + tasup * ec) / ec  # contact temperature of coil

        # minimum
        LMRT = abs((tsh0 - trh0) / scipy.log((tsh0 - tc) / (trh0 - tc)))
        k1 = 1 / mCw0

        def fh(x):
            Eq = mCw0 * k2 - Qhsf_0 * (k2 / (scipy.log((x + k2 - tc) / (x - tc)) * LMRT))
            return Eq

        k2 = Qhsf * k1
        try:
            result = sopt.newton(fh, trh0, maxiter=1000, tol=0.01).real - 273
        except RuntimeError:
            # print (Qhsf, Qhsf_0, Ta_sup_hs, Ta_re_hs, Ths_sup_0, Ths_re_0, ma_sup_hs, ma_sup_0,Ta_sup_0, Ta_re_0)
            result = sopt.bisect(fh, 0, 350, xtol=0.01, maxiter=500).real - 273

        trh = result
        tsh = trh + k2
        mcphs = Qhsf / (tsh - trh)
    else:
        tsh = np.nan
        trh = np.nan
        mcphs = 0
    # return floats with numpy function. Needed when np.vectorize is use to call this function
    return np.float(tsh), np.float(trh), np.float(mcphs) # C,C, W/C


def calc_cooling_coil(Qcsf, Qcsf_0, Ta_sup_cs, Ta_re_cs, Tcs_sup_0, Tcs_re_0, ma_sup_cs, ma_sup_0, Ta_sup_0, Ta_re_0,Cpa):
    # Initialize temperatures
    tasup = Ta_sup_cs + 273
    tare = Ta_re_cs + 273
    tsc0 = Tcs_sup_0 + 273
    trc0 = Tcs_re_0 + 273
    mCw0 = Qcsf_0 / (tsc0 - trc0)

    # log mean temperature at nominal conditions
    TD10 = Ta_sup_0 - trc0
    TD20 = Ta_re_0 - tsc0
    LMRT0 = (TD20 - TD10) / scipy.log(TD20 / TD10)
    UA0 = Qcsf_0 / LMRT0

    if Qcsf < -0 and ma_sup_cs > 0:
        AUa = UA0 * (ma_sup_cs / ma_sup_0) ** 0.77
        NTUc = AUa / (ma_sup_cs * Cpa * 1000)
        ec = 1 - scipy.exp(-NTUc)
        tc = (tare - tasup + tasup * ec) / ec  # contact temperature of coil

        def fh(x):
            TD1 = tc - (k2 + x)
            TD2 = tc - x
            LMRT = (TD2 - TD1) / scipy.log(TD2 / TD1)
            Eq = mCw0 * k2 - Qcsf_0 * (LMRT / LMRT0)
            return Eq

        k2 = -Qcsf / mCw0
        try:
            result = sopt.newton(fh, trc0, maxiter=1000, tol=0.01) - 273
        except RuntimeError:
            print('Newton optimization failed in cooling coil, using slower bisect algorithm...')
            try:
                result = sopt.bisect(fh, 0, 350, xtol=0.01, maxiter=500) - 273
            except RuntimeError:
                print ('Bisect optimization also failed in cooing coil, using sample:')


        #if Ta_sup_cs == Ta_re_cs:
        #    print 'Ta_sup_cs == Ta_re_cs:', Ta_sup_cs
        tsc = result.real
        trc = tsc + k2

        #Control system check - close to optimal flow
        min_AT = 5  # Its equal to 10% of the mass flowrate
        tsc_min = Tcs_sup_0  # to consider coolest source possible
        trc_max = Tcs_re_0
        tsc_max = 12
        AT = tsc - trc
        if AT < min_AT:
            if tsc < tsc_min:
                tsc = tsc_min
                trc = tsc_min + min_AT
            if tsc > tsc_max:
                tsc = tsc_max
                trc = tsc_max + min_AT
            else:
                trc = tsc + min_AT
        elif tsc > tsc_max or trc > trc_max or tsc < tsc_min:
            trc = trc_max
            tsc = tsc_max

        mcpcs = Qcsf / (tsc - trc)
    else:
        tsc = np.nan
        trc = np.nan
        mcpcs = 0
    # return floats with numpy function. Needed when np.vectorize is use to call this function
    return np.float(tsc), np.float(trc), np.float(mcpcs)  # C,C, W/C
