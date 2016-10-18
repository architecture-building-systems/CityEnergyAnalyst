# -*- coding: utf-8 -*-
"""
=========================================
Termoactivated building surfaces (TABS)
=========================================

"""

from __future__ import division
import scipy
import scipy.optimize as sopt

def calc_floorheating(Qh, tm, Qh0, tsh0, trh0, Af):
    nh =0.2
    if Qh > 0:
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        tm = tm + 273
        mCw0 = Qh0 / (tsh0 - trh0)
        # minimum
        k1 = 1 / mCw0

        # simple calculation based on SIA 2044, which in turn is based on EMPA's book on TABS
        R_tabs = 0.08       # m2-K/W from SIA 2044
        A_tabs = 0.8 * Af   # m2
        H_tabs = A_tabs / R_tabs

        def fh(x):
            Eq = mCw0 * k2 - (x+k2-tm) * H_tabs
            return Eq

        k2 = Qh * k1
        result = sopt.newton(fh, trh0, maxiter=1000, tol=0.1) - 273
        trh = result.real
        tsh = trh + k2
        mCw = Qh / (tsh - trh)
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh, trh, mCw # C,C, W/C