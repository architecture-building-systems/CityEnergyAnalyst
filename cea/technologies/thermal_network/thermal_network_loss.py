"""
Hydraulic - thermal network
"""
from __future__ import division
from __future__ import print_function

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK


def calc_temperature_out_per_pipe(t_in, m, k, t_ground):
    """

    :param t_in: in Kelvin
    :param m: in kg/s
    :param k: in kW/K
    :param t_ground: in Kelvin
    :return:
    """
    t_out = (t_in * (k / 2 - m * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000) - k * t_ground) / (
            -m * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000 - k / 2)  # [K]

    return t_out