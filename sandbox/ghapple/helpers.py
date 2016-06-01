
"""
Some helper functions that could be useful


"""

from __future__ import division
import datetime
import math
import numpy as np


def hoy_2_doy(hoy):

    return int(math.floor(hoy/24))


def hoy_2_woy(hoy):

    return int(math.floor(hoy_2_doy(hoy)/7))


def hoy_2_moy(hoy):

    months_of_year = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    days_in_month = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    return months_of_year.where(np.cumsum(days_in_month) > hoy_2_doy(hoy))



