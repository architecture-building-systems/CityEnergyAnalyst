# -*- coding: utf-8 -*-
"""
    Physiscal properties
    ===========
"""
def calc_w(t, RH):
    """
    Moisture content in kg/kg of dry air

    Parameters
    ----------
    t : temperature of air in (°C)
    RH : relative humidity of air in (%)

    Returns
    -------
    w : moisture content of air in (kg/kg dry air)
    """
    Pa = 100000  # Pa
    Ps = 610.78 * math.exp(t / (t + 238.3) * 17.2694)
    Pv = RH / 100 * Ps
    w = 0.62 * Pv / (Pa - Pv)

    return w


def calc_h(t, w):
    """
    calculates enthalpy of moist air in kJ/kg

    source: thesis Kaempf Eq.(4.30) extended to temperatures below -10°

    Parameters
    ----------
    t : air temperature in (°C)
    w : moisture content of air in (kg/kg dry air)

    Returns
    -------
    h : enthalpy of moist air in (kJ/kg)
    """

    if 0 < t < 60:  # temperature above zero
        h = (1.007 * t - 0.026) + w * (2501 + 1.84 * t)
    elif -100 < t <= 0: # temperature below zero
        h = (1.005 * t) + w * (2501 + 1.84 * t)
    else:
        h = np.nan
        print('Warning: Temperature out of bounds (>60°C or <-100°C)')
        print(t)

    return h