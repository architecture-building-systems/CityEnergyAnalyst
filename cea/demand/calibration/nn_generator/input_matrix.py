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


def get_cea_inputs(building_name):
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    # Geometry properties
    data_architecture = dbf_to_dataframe(locator.get_building_architecture())
    data_architecture.set_index('Name', inplace=True)
    weather_data = epwreader.epw_reader(locator.get_default_weather())[['drybulb_C', 'relhum_percent', 'glohorrad_Whm2',
                                                                        'dirnorrad_Whm2', 'difhorrad_Whm2', 'skytemp_C',
                                                                        'windspd_ms']]
    weather_array=np.transpose(np.asarray(weather_data))

    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)

    building = building_properties[building_name]

    # Geometry properties
    ## aconditioned floor area
    array_Af = np.empty(8760)
    array_Af.fill(building.rc_model['Af'])
    ## surface to volume ratio
    array_sv = np.empty(8760)
    array_sv.fill(building.rc_model['surface_volume'])
    ### final array of geometry properties
    array_geom=np.stack((array_Af,array_sv))

    # Architecture
    ##Window to wall ratio
    array_wwr = np.empty(8760)
    average_wwr = np.mean([data_architecture.ix[building_name, 'wwr_south'],
                           data_architecture.ix[building_name, 'wwr_north'],
                          data_architecture.ix[building_name, 'wwr_west'],
                           data_architecture.ix[building_name, 'wwr_east']])
    array_wwr.fill(average_wwr)
    ##Type of construction
    array_cm = np.empty(8760)
    array_cm.fill(building.architecture.Cm_Af)
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
    array_awall = np.empty(8760)
    array_awall.fill(building.architecture.a_wall)
    ##type of basement
    array_Ubase = np.empty(8760)
    array_Ubase.fill(building.architecture.U_base)
    ##type of windows
    array_Uwin = np.empty(8760)
    array_Uwin.fill(building.architecture.U_win)
    array_Gwin = np.empty(8760)
    array_Gwin.fill(building.architecture.G_win)
    ##type_shade
    array_rfsh = np.empty(8760)
    array_rfsh.fill(building.architecture.rf_sh)
    ### final array of architecture properties
    array_arch=np.stack((array_wwr,array_cm,array_n50,array_Uroof,array_aroof,array_Uwall,array_awall,array_Ubase,
                array_Uwin,array_Gwin,array_rfsh))

    # indoor comfort
    schedules, tsd = initialize_inputs(building, gv, schedules_dict, weather_data)
    tsd = controllers.calc_simple_temp_control(tsd, building.comfort, gv.seasonhours[0] + 1, gv.seasonhours[1],
                                               date.dayofweek)

    np.place(tsd['ta_hs_set'], np.isnan(tsd['ta_hs_set']),-100)
    np.place(tsd['ta_cs_set'], np.isnan(tsd['ta_cs_set']), 100)
    array_Thset = tsd['ta_hs_set']
    array_Tcset = tsd['ta_cs_set']
    ### final array of indoor comfor
    array_cmfrt=np.empty((1,8760))
    array_cmfrt [0,:] = array_Thset
    array_cmfrt[0,gv.seasonhours[0] + 1:gv.seasonhours[1]]= array_Tcset[gv.seasonhours[0] + 1:gv.seasonhours[1]]
    #array_cmfrt=np.squeeze((array_cmfrt))

    # internal loads
    array_electricity = tsd['Eaf']+ tsd['Edataf'] + tsd ['Elf'] + tsd ['Eprof'] + tsd['Eref']
    np.place(tsd['Qhprof'], np.isnan(tsd['Qhprof']), 0)
    array_sensible_gain = tsd['Qs'] + tsd['Qhprof']
    array_latent_gain = tsd['w_int']
    array_ve = tsd['ve']
    array_Vww=schedules['Vww']
    ### final array of internal loads
    array_int_load=np.stack((array_electricity,array_sensible_gain,array_latent_gain,array_ve,array_Vww))

    # HVAC systems
    ##heating system
    array_dThs_C = np.empty(8760)
    array_dThs_C.fill(building.hvac['dThs_C'])
    ##cooling system
    array_dTcs_C = np.empty(8760)
    array_dTcs_C.fill(building.hvac['dTcs_C'])
    ## ventilation
    array_economizer = np.empty(8760)
    array_economizer.fill(1*(building.hvac['ECONOMIZER']))
    array_win_vent = np.empty(8760)
    array_win_vent.fill(1*(building.hvac['WIN_VENT']))
    array_mech_vent = np.empty(8760)
    array_mech_vent.fill(1*(building.hvac['MECH_VENT']))
    array_heat_rec = np.empty(8760)
    array_heat_rec.fill(1 * (building.hvac['HEAT_REC']))
    array_night_flsh = np.empty(8760)
    array_night_flsh.fill(1 * (building.hvac['NIGHT_FLSH']))
    ##controller
    array_ctrl_Qhs = np.empty(8760)
    array_ctrl_Qhs.fill(1 * (building.hvac['dT_Qhs']))
    array_ctrl_Qcs = np.empty(8760)
    array_ctrl_Qcs.fill(1 * (building.hvac['dT_Qcs']))
    ### final array of HVAC systems
    array_hvac=np.stack((array_dThs_C,array_dTcs_C,array_economizer,array_win_vent,array_mech_vent,
                         array_heat_rec,array_night_flsh,array_ctrl_Qhs,array_ctrl_Qcs))

    building_array=np.concatenate((weather_array,array_geom, array_arch, array_cmfrt,
                                   array_int_load, array_hvac))
    raw_nn_inputs=np.transpose(building_array)
    return raw_nn_inputs


def run_as_script(building_name):
    raw_nn_inputs = get_cea_inputs(building_name)
    return raw_nn_inputs

if __name__ == '__main__':
    run_as_script()

## todo change the structure of run as script: add global variables and locator
## todo write documentation on te script