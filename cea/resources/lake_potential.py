# -*- coding: utf-8 -*-
"""
Sewage source heat exchanger
"""
from __future__ import division
import pandas as pd
import numpy as np
import scipy
from cea.constants import HEX_WIDTH_M,VEL_FLOW_MPERS, HEAT_CAPACITY_OF_WATER_JPERKGK, H0_KWPERM2K, MIN_FLOW_LPERS, T_MIN, AT_MIN_K
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_lake_potential(locator, config):
    """
    Calaculate the heat extracted from the sewage HEX.

    :param locator: an InputLocator instance set to the scenario to work on
    :param Length_HEX_available: HEX length available
    :type Length_HEX_available: float
    :param gv: globalvar.py

    Save the results to `SWP.csv`
    """

    lake_potential = np.zeros(HOURS_IN_YEAR)
    hour = range(HOURS_IN_YEAR)

    if config.lake.available:
        lake_size = config.lake.size
        lake_size_per_hour = float(lake_size) / HOURS_IN_YEAR
        for i in range(HOURS_IN_YEAR):
            lake_potential[i] = lake_size_per_hour


    lake_gen = locator.get_lake_potential()
    pd.DataFrame( { "hour" : hour, "lake_potential" : lake_potential}).to_csv( lake_gen, index=False, float_format='%.3f')


def main(config):

    locator = cea.inputlocator.InputLocator(config.scenario)

    calc_lake_potential(locator=locator, config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())