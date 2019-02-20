# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
import pandas as pd
from cea.demand.control_heating_cooling_systems import get_heating_system_set_point
from cea.demand.control_heating_cooling_systems import get_cooling_system_set_point

import datetime

__author__ = "Bhargava Krishna Sreepathi"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Krishna Sreepathi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_set_point_from_predefined_file(tsd, bpr, weekday, building_name):
    """

    :param tsd: a dictionary of time step data mapping variable names to ndarrays for each hour of the year.
    :type tsd: dict
    :param bpr: BuildingPropertiesRow
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :param weekday:
    :return: tsd with updated columns
    :rtype: dict
    """

    tsd['ta_hs_set'] = np.vectorize(get_heating_system_set_point)(tsd['people'], range(8760), bpr, weekday)
    # compare_a = np.vectorize(get_cooling_system_set_point)(tsd['people'], range(8760), bpr, weekday)

    predefined_set_temperatures = pd.read_excel('D:\demand_code\WTP_MIX_m_flexible\data/Temperature ' + str(building_name) + '.xlsx')
    # compare_b = predefined_set_temperatures['temperature'].values

    tsd['ta_cs_set'] = predefined_set_temperatures['temperature'].values

    return tsd