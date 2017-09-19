# coding=utf-8
"""
Input matrix script creates matrix of input parameters for the NN out of CEA
"""
from __future__ import division

import os

import pandas as pd
import time
import cea.globalvar
import cea.inputlocator
from cea.demand.demand_main import properties_and_schedule
from cea.utilities.dbfreader import dbf_to_dataframe
from cea.utilities import epwreader
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

gv = cea.globalvar.GlobalVariables()
scenario_path = gv.scenario_reference
locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

# Geometry properties
data_architecture = dbf_to_dataframe(locator.get_building_architecture())
data_indoor_comfort = dbf_to_dataframe(locator.get_building_comfort())
data_internal_loads = dbf_to_dataframe(locator.get_building_internal())
data_hvac_systems = dbf_to_dataframe((locator.get_building_hvac()))
weather_data = epwreader.epw_reader(locator.get_default_weather())[['drybulb_C', 'relhum_percent', 'glohorrad_Whm2',
                                                            'dirnorrad_Whm2', 'difhorrad_Whm2']]


building_properties, schedules_dict, date = properties_and_schedule(gv, locator)

for building in building_properties:

    # for the geometry properties Af and surface / volumne
    array_Af = np.empty(8760)
    array_Af.fill(building.rc_model['Af'])

    array_sv = np.empty(8760)
    array_sv.fill(building.rc_model['surface_volume'])
    a=3


# for building in buildings:
