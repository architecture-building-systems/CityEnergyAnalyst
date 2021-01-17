# -*- coding: utf-8 -*-
"""
heating radiators
"""



from scipy.optimize import newton
import math
import numpy as np


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_radiator(Qh, tair, Qh0, tair0, tsh0, trh0):
    """
    Calculates the supply and return temperature as well as the flow rate of water in radiators similar to the model
    implemented by Holst (1996) using a Newton-Raphson solver.

    :param Qh: Space heating demand in the building
    :param tair: environment temperature in the building
    :param Qh0: nominal radiator power
    :param tair0:
    :param tsh0:
    :param trh0:
    :return:

    [Holst} S. Holst (1996) "TRNSYS-Models for Radiator Heating Systems"
    """
    # TODO: add documentation and sources

    nh = 0.3  # radiator constant
    if Qh > 0 or Qh < 0:  # use radiator function also for sensible cooling panels (ceiling cooling, chilled beam,...)
        tair = tair + 273
        tair0 = tair0 + 273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0 / (tsh0 - trh0)
        # minimum
        LMRT0 = lmrt(tair0, trh0, tsh0)
        delta_t = Qh / mCw0
        result = newton(fh, trh0, args=(delta_t, Qh0, Qh, tair, LMRT0, nh), maxiter=100, tol=0.01) - 273
        trh = result.real
        tsh = trh + Qh / mCw0
        mCw = Qh / (tsh - trh)
    else:
        mCw = 0
        tsh = np.nan
        trh = np.nan
    # return floats with numpy function. Needed when np.vectorize is use to call this function
    return np.float(tsh), np.float(trh), np.float(mCw) # C, C, W/C

def fh(x, delta_t, Qh0, Qh, tair, LMRT0, nh):
    '''
    Static radiator heat balance equation from Holst (1996), eq. 6.

    :param x: radiator exhaust temperature
    :param mCw0: nominal radiator mass flow rate
    :param Qh: space heating demand
    :param Qh0: nominal space heating power
    :param tair: air temperature in the building
    :param LMRT0: nominal logarithmic temperature difference
    :param nh: radiator constant
    :return:
    '''
    LMRT = lmrt(tair, x, x+delta_t)
    # Eq. 6
    Eq = Qh - Qh0 * (LMRT / LMRT0) ** (nh + 1)
    return Eq

def lmrt(tair, trh, tsh):
    '''
    Logarithmic temperature difference (Eq. 3 in Holst, 1996)
    :param tair: environment temperature in the room
    :param trh: radiator exhaust temperature
    :param tsh: radiator supply temperature
    :return:
    '''
    LMRT = (tsh - trh) / math.log((tsh - tair) / (trh - tair))
    return LMRT



try:
    # import Numba AOT versions of the functions above, overwriting them
    from calc_radiator import fh, lmrt
except ImportError:
    # fall back to using the python version
    # print('failed to import from calc_radiator.pyd, falling back to pure python functions')
    pass
