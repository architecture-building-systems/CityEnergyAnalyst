# coding=utf-8
"""
Input matrix script creates matrix of input parameters for the NN out of CEA
"""
from __future__ import division

import os

import pandas as pd
import time
import cea.globalvar
import math
import cea.inputlocator
from cea.demand.demand_main import properties_and_schedule
from cea.demand.thermal_loads import initialize_inputs
from cea.utilities.dbfreader import dbf_to_dataframe
from cea.technologies import controllers
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
data_architecture.set_index('Name', inplace=True)
weather_data = epwreader.epw_reader(locator.get_default_weather())[['drybulb_C', 'relhum_percent', 'glohorrad_Whm2',
                                                                    'dirnorrad_Whm2', 'difhorrad_Whm2', 'skytemp_C',
                                                                    'windspd_ms']]

building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
list_building_names = building_properties.list_building_names()

for name in list_building_names:
    building = building_properties[name]

    # Geometry properties
    ## aconditioned floor area
    array_Af = np.empty(8760)
    array_Af.fill(building.rc_model['Af'])
    ## surface to volume ratio
    array_sv = np.empty(8760)
    array_sv.fill(building.rc_model['surface_volume'])

    # Architecture
    ##Window to wall ratio
    array_wwr = np.empty(8760)
    average_wwr = np.mean([data_architecture.ix[name, 'wwr_south'], data_architecture.ix[name, 'wwr_north'],
                          data_architecture.ix[name, 'wwr_west'], data_architecture.ix[name, 'wwr_east']])
    array_wwr.fill(average_wwr)
    ##Type of construction
    array_cm = np.empty(8760)
    ##Type of leakage
    array_n50 = np.empty(8760)
    array_n50.fill(building.architecture.n50)
    ##Type of roof
    array_Uroof = np.empty(8760)
    array_Uroof.fill(building.architecture.U_roof)
    array_aroof = np.empty(8760)
    array_aroof.fill(building.architecture.a_roof)
    ##Type of walls
    array_Uwall = np.empty(8760)
    array_Uwall.fill(building.architecture.U_wall)
    array_Ubase = np.empty(8760)
    array_Ubase.fill(building.architecture.U_base)
    array_awall = np.empty(8760)
    array_awall.fill(building.architecture.a_wall)
    ##type of windows
    array_Uwin = np.empty(8760)
    array_Uwin.fill(building.architecture.U_win)
    array_Gwin = np.empty(8760)
    array_Gwin.fill(building.architecture.G_win)
    ##type_shade
    array_rfsh = np.empty(8760)
    array_rfsh.fill(building.architecture.rf_sh)

    # indoor comfort
    schedules, tsd = initialize_inputs(building, gv, schedules_dict, weather_data)
    tsd = controllers.calc_simple_temp_control(tsd, building.comfort, gv.seasonhours[0] + 1, gv.seasonhours[1],
                                               date.dayofweek)

    np.place(tsd['ta_hs_set'], np.isnan(tsd['ta_hs_set']),-100)
    np.place(tsd['ta_cs_set'], np.isnan(tsd['ta_cs_set']), 100)
    array_Thset = tsd['ta_hs_set']
    array_Tcset = tsd['ta_cs_set']

    # internal loads
    array_electricity = tsd['Eaf']+ tsd['Edataf'] + tsd ['Elf'] + tsd ['Eprof'] + tsd['Eref']
    array_sensible_gain = tsd['Qs'] + tsd['Qhp']
    array_X = tsd['X']
    array_ve = tsd['ve']
    array_Vww = np.empty(8760)
    array_Vww.fill(building.internal_loads['Vww'])

    # HVAC systems
    ##heating system
    array_dThs_C = np.empty(8760)
    array_dThs_C.fill(building.hvac['dThs_C'])
    ##cooling system
    array_dTcs_C = np.empty(8760)
    array_dTcs_C.fill(building.hvac['dTcs_C'])
    ## ventilation
    array_economizer = np.empty(8760)
    array_economizer.fill(int(building.hvac['ECONOMIZER'] == 'true'))
    ##todo for heat recovery, mech vent, night flush, win_vent
    ##controller
    ##todo for the controller out of dT_Qhs, and dT_Qcs







    # for building in buildings:
