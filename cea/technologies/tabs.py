# -*- coding: utf-8 -*-
"""
Termoactivated building surfaces (TABS)
"""




import numpy as np
import scipy.optimize

__author__ = "Martin Mosteiro"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_floorheating(Qh, tm, Qh0, tsh0, trh0, Af):
    """
    Calculates the operating conditions of the TABS system based on existing radiator model, replacing the radiator
    equation with the simple calculation for TABS from SIA 2044, which in turn is based on Koschenz & Lehmann
    "Thermoaktive Bauteilsysteme (TABS)".

    :param Qh: heating demand
    :param tm: Temperature of the thermal mass
    :param Qh0: nominal heating power of the heating system
    :param tsh0: nominal supply temperature to the TABS system
    :param trh0: nominal return temperature from the TABS system
    :param Af: heated area

    :return: - ``tsh``, supply temperature to the TABS system
             - ``trh``, return temperature from the TABS system
             - ``mCw``, flow rate in the TABS system
    """

    if Qh > 0:
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        tm = tm + 273
        mCw0 = Qh0 / (tsh0 - trh0)
        # minimum
        k1 = 1 / mCw0

        R_tabs = 0.08       # m2-K/W from SIA 2044
        A_tabs = 0.8 * Af   # m2
        H_tabs = A_tabs / R_tabs

        def fh(x, mCw0, k2, tm, H_tabs):
            Eq = mCw0 * k2 - (x+k2-tm) * H_tabs
            return Eq

        k2 = Qh * k1
        result = scipy.optimize.newton(fh, trh0, args=(mCw0, k2, tsh0, H_tabs),  maxiter=1000, tol=0.1) - 273
        trh = result.real
        tsh = trh + k2
        mCw = Qh / (tsh - trh)
    else:
        mCw = 0
        tsh = np.nan
        trh = np.nan
    return tsh, trh, mCw # C,C, W/C
