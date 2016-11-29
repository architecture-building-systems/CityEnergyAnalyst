


import pandas as pd
import numpy as np
import math

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_ground_temperature(T_ambient, gv):
    '''
    SOURCE?
    This function calculates the ground temperature in an hourly basis.
    :param T_ambient: vector with outdoor temperature
    :param gv: global variables class
    :return:
        Tg: vector with ground temperatures in K
    '''

    T_max = max(T_ambient)+273 # to K
    T_avg = np.mean(T_ambient)+273 # to K
    e = gv.Z0*math.sqrt((math.pi*gv.Csl*gv.Psl)/(8760*gv.Bsl)) # soil constants
    Tg = [T_avg+(T_max-T_avg)*math.exp(-e)*math.cos((2*math.pi*(i+1)/8760)-e) for i in range(8760)]

    return Tg #in K
