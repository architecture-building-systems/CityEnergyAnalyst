# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
import pandas as pd
import os
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


def calc_set_point_from_predefined_file(tsd, bpr, weekday, building_name, locator):
    """
    This function is used to set the space cooling and space heating set points from a predefined hourly set points
    xlsx file. This will help in finding the building demand for a flexible building scenario.

    This script is developed as part of the CONCEPT project (an Intra-CREATE collaboration between FCL and TUM CREATE)

    The excel files with the predefined hourly temperatures are to be stored in
    `scenario\inputs\predefined-hourly-setpoints` folder. This folder in turn has two subfolders namely `space-heating`
    and `space-cooling`. Inside these folders the setpoints are to be provided in an excel file. The excel files need
    to be provided in `BuildingName_temperature.xlsx` format and the necessary columns are `time` and `temperature`

    In case the files are not present, the calculations will still carry on by taking the archetypical set points
    present in CEA databases. Though it will print a message saying `predefined set points file is not provided`


    :param tsd: a dictionary of time step data mapping variable names to ndarrays for each hour of the year.
    :type tsd: dict
    :param bpr: BuildingPropertiesRow
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :param weekday:
    :return: tsd with updated columns
    :rtype: dict
    """
    if os.path.isfile(locator.get_predefined_hourly_setpoints(building_name, type_of_district_network='space-heating')):
        predefined_set_temperatures_space_heating = pd.read_csv(locator.get_predefined_hourly_setpoints(building_name, type_of_district_network='space-heating'))
        tsd['ta_hs_set'] = predefined_set_temperatures_space_heating['temperature'].values
    else:
        print ('predefined set points file for space heating is not provided. It is running with the default archetype set points')
        tsd['ta_hs_set'] = np.vectorize(get_heating_system_set_point)(tsd['people'], range(8760), bpr, weekday)

    if os.path.isfile(locator.get_predefined_hourly_setpoints(building_name, type_of_district_network='space-cooling')):
        predefined_set_temperatures_space_cooling = pd.read_csv(locator.get_predefined_hourly_setpoints(building_name, type_of_district_network='space-cooling'))
        tsd['ta_cs_set'] = predefined_set_temperatures_space_cooling['temperature'].values
    else:
        print ('predefined set points file for space cooling is not provided. It is running with the default archetype set points')
        tsd['ta_cs_set'] = np.vectorize(get_cooling_system_set_point)(tsd['people'], range(8760), bpr, weekday)

    return tsd