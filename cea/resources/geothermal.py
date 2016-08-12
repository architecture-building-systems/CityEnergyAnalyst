


import pandas as pd
import numpy as np
import math

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_ground_temperature(T_ambient, gv):

    T_max = max(T_ambient)+273 # to K
    T_avg = np.mean(T_ambient)+273 # to K
    e = gv.Z0*math.sqrt((math.pi*gv.Csl*gv.Psl)/(8760*gv.Bsl)) # soil constant
    Tg = []

    for i in range(8760):
        Tground_t = T_avg+(T_max-T_avg)*math.exp(-e)*math.cos((2*math.pi*(i+1)/8760)-e)
        Tg.append(Tground_t)
    return Tg #in K
