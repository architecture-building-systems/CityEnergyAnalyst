# -*- coding: utf-8 -*-
"""
=========================================
Termoactivated building surfaces (TABS)
=========================================

"""

from __future__ import division
import scipy
import scipy.optimize as sopt

def calc_floorheating(Qh, tair, Qh0, tair0, tsh0, trh0):

    nh =0.2
    if Qh > 0:
        tair0 = tair0 + 273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0 / (tsh0 - trh0)
        # minimum
        LMRT = (tsh0 - trh0) / scipy.log((tsh0 - tair0) / (trh0 - tair0))
        k1 = 1 / mCw0

        def fh(x):
            Eq = mCw0 * k2 - Qh0 * (k2 / (scipy.log((x + k2 - tair) / (x - tair)) * LMRT)) ** (nh + 1)
            return Eq

        k2 = Qh * k1
        tair = tair + 273
        result = sopt.newton(fh, trh0, maxiter=1000, tol=0.1) - 273
        trh = result.real
        tsh = trh + k2
        mCw = Qh / (tsh - trh)
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh, trh, mCw # C,C, W/C