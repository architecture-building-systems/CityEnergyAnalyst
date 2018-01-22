# -*- coding: utf-8 -*-
"""
Physical functions
"""
from __future__ import division
import scipy.optimize as sopt
import scipy
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# stefan-boltzmann constant
BOLTZMANN = 0.0000000567  # W/m2K4


def calc_w(t, RH):
    """
    Moisture content in kg/kg of dry air

    t : temperature of air in (°C)
    RH : relative humidity of air in (%)

    w : moisture content of air in (kg/kg dry air)
    """
    Pa = 100000  # Pa
    Ps = 610.78 * scipy.exp(t / (t + 238.3) * 17.2694)
    Pv = RH / 100 * Ps
    w = 0.62 * Pv / (Pa - Pv)

    # TODO: source?

    return w


def calc_h(t, w):
    """
    calculates enthalpy of moist air in kJ/kg

    t : air temperature in (°C)
    w : moisture content of air in (kg/kg dry air)

    h : enthalpy of moist air in (kJ/kg)
    """

    if 0 < t < 60:  # temperature above zero
        h = (1.007 * t - 0.026) + w * (2501 + 1.84 * t)
    elif -100 < t <= 0:  # temperature below zero
        h = (1.005 * t) + w * (2501 + 1.84 * t)
    else:
        raise Exception('temperature out of bounds!' + str(t))
        h = np.nan
        print('Warning: Temperature out of bounds (>60°C or <-100°C)')
        print(t)

    # TODO: source?

    return h


def calc_t_from_h(h, w):
    """
    calculates temperature in (°C) from enthalpy (kJ/kg) of moist air with know moisture content
    inverse equation of calc_h(t,w)

    :param h: enthalpy of moist air in (kJ/kg)
    :param w: moisture content of air in (kg/kg dry air)
    :return: temperature in (°C)
    """

    t1 = (-1359.24 * (w - 3.998e-4 * (h + 0.026))) / (w + 0.547283)

    t2 = (-1359.24 * (w - 3.998e-4 * h)) / (w + 0.546196)

    # choose appropriate result based on temperature range
    if 0 < t1 < 60:
        t = t1
    elif -100 < t2 <= 0:
        t = t2
    else:
        raise
        t = np.nan
        #    print('Warning: Temperature out of bounds (>60°C or <-100°C)')
        #   print(t1,t2)

    return t


def calc_RH(w, t):  # Moisture content in kg/kg of dry air
    Pa = 100000  # Pa

    def Ps(x):
        Eq = w * (Pa / (x / 100 * 610.78 * scipy.exp(t / (t + 238.3 * 17.2694))) - 1) - 0.62
        return Eq

    result = sopt.newton(Ps, 50, maxiter=100, tol=0.01)
    RH = result.real
    return RH


def calc_t(w, RH):  # tempeature in C
    Pa = 100000  # Pa

    def Ps(x):
        Eq = w * (Pa / (RH / 100 * 610.78 * scipy.exp(x / (x + 238.3 * 17.2694))) - 1) - 0.62
        return Eq

    result = sopt.newton(Ps, 19, maxiter=100, tol=0.01)
    t = result.real
    return t


def calc_rho_air(temp_air):
    """
    Calculation of density of air according to 6.4.2.1 in [1]

    temp_air : air temperature in (°C)

    rho_air : air density in (kg/m3)

    """
    # constants from Table 12 in [1]
    # TODO import from global variables
    # TODO implement dynamic air density in other functions
    rho_air_ref = 1.23  # (kg/m3)
    temp_air_ref_K = 283  # (K)
    temp_air_K = temp_air + 273  # conversion to (K)

    # Equation (1) in [1]
    rho_air = temp_air_ref_K / temp_air_K * rho_air_ref

    return rho_air


def calc_wet_bulb_temperature(dry_bulb_temperature, relative_humidity):
    '''
    calc wet bulb temperature from empirical formula in R. Stull, "Wet-Bulb Temperature from Relative Humidity and Air
    Temperature" (2011)
    '''

    return dry_bulb_temperature * np.arctan(0.151977 * (relative_humidity + 8.313659) ** 0.5) + \
           np.arctan(dry_bulb_temperature + relative_humidity) - np.arctan(relative_humidity - 1.676331) + \
           0.00391838 * (relative_humidity) ** 1.5 * np.arctan(0.23101 * relative_humidity) - 4.686035
