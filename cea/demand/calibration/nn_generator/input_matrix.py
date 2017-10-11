# coding=utf-8
"""
Input matrix script creates matrix of input parameters for the NN out of CEA
"""
from __future__ import division
import pandas as pd
import cea.globalvar
import cea.inputlocator
from cea.demand.demand_main import properties_and_schedule
from cea.demand.thermal_loads import initialize_inputs
from cea.utilities.dbfreader import dbf_to_dataframe
from cea.technologies import controllers
from cea.utilities import epwreader
from cea.demand.sensible_loads import calc_I_sol
import numpy as np
from cea.demand.calibration.nn_generator.nn_settings import nn_delay

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def input_prepare_multi_processing(building_name, gv, locator, target_parameters):
    raw_nn_targets = get_cea_outputs(building_name, locator, target_parameters)
    raw_nn_inputs_D, raw_nn_inputs_S = get_cea_inputs(locator, building_name, gv)
    NN_input_ready, NN_target_ready = prep_NN_delay(raw_nn_inputs_D, raw_nn_inputs_S, raw_nn_targets, nn_delay)
    return NN_input_ready, NN_target_ready


def prep_NN_delay(raw_nn_inputs_D, raw_nn_inputs_S, raw_nn_targets, nn_delay):
    '''
    :param raw_nn_inputs_D: the inputs to be prepared and sent to NN for training
    :type   raw_nn_inputs_D: numpy array
    :param raw_nn_targets:
    :param nn_delay:
    :return: NN_inpuy_ready , NN_target_ready
    :rtype: numpy arrays

    '''
    input1=raw_nn_inputs_D
    target1=raw_nn_targets
    nS, nF = input1.shape
    nSS, nT = target1.shape
    nD= nn_delay - 1
    aD=nD+1
    rD=aD+1
    rS=nS+1
    input_matrix_features=np.zeros((rS+nD, rD*nF))
    rowsF, colsF=input_matrix_features.shape
    input_matrix_targets=np.zeros((rS+nD, rD*nT))
    rowsFF, ColsFF = input_matrix_targets.shape

    i=1
    while i<rD+1:
        j=i-1
        aS=nS+j
        m1=(i*nF)-(nF)
        m2=(i*nF)
        n1=(i*nT)-(nT)
        n2=(i*nT)
        input_matrix_features[j:aS, m1:m2]=input1
        input_matrix_targets[j:aS, n1:n2]=target1
        i=i+1

    trimmed_inputn = input_matrix_features[aD:nS,:]
    trimmed_inputt = input_matrix_targets[aD:nS, nT:]
    trimmed_input_S = raw_nn_inputs_S [aD:aS,:]
    NN_input_ready=np.concatenate([trimmed_inputn, trimmed_inputt, trimmed_input_S], axis=1)
    NN_target_ready=target1[aD:aS,:]

    return NN_input_ready , NN_target_ready


def get_cea_outputs(building_name,locator, target_parameters):
    '''
    This function reads the CEA outputs
    :param building_name:
    :param locator:
    :param target_parameters:
    :return:
    '''
    raw_nn_targets = pd.read_csv(locator.get_demand_results_file(building_name), usecols=target_parameters)
    raw_nn_targets = np.array(raw_nn_targets)
    return raw_nn_targets

def get_cea_inputs(locator, building_name, gv):

    # TODO: make comments in line
    weather_array, weather_data = get_array_weather_variables(locator)

    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)

    building = building_properties[building_name]

    array_geom = get_array_geometry_variables(building)

    array_arch = get_array_architecture_variables(building, building_name, locator)

    array_cmfrts, schedules, tsd = get_array_comfort_variables(building, date, gv, schedules_dict, weather_data)

    array_int_load = get_array_internal_loads_variables(schedules, tsd, building, gv)

    array_hvac = get_array_HVAC_variables(building)

    weather_array=np.transpose(weather_array)
    array_cmfrts=np.transpose(array_cmfrts)

    building_array_D=np.concatenate((weather_array, array_cmfrts,array_int_load), axis=1)
    building_array_S = np.concatenate((array_geom, array_arch, array_hvac),axis=1)

    raw_nn_inputs_D = building_array_D
    raw_nn_inputs_S = building_array_S
    return raw_nn_inputs_D , raw_nn_inputs_S


def get_array_weather_variables(locator):
    weather_data = epwreader.epw_reader(locator.get_default_weather())[['drybulb_C', 'relhum_percent', 'glohorrad_Whm2',
                                                                        'dirnorrad_Whm2', 'difhorrad_Whm2', 'skytemp_C',
                                                                        'windspd_ms']]
    weather_array = np.transpose(np.asarray(weather_data))
    return weather_array, weather_data


def get_array_geometry_variables(building):
    # Geometry properties
    ## aconditioned floor area
    array_Af = np.empty(8760)
    array_Af.fill(building.rc_model['Af'])
    ## walls area
    array_OPwall = np.empty(8760)
    array_OPwall.fill(building.rc_model['Aop_sup'])
    ## Basement walls area
    array_OPwallB = np.empty(8760)
    array_OPwallB.fill(building.rc_model['Aop_bel'])
    ## window area
    array_GLwin = np.empty(8760)
    array_GLwin.fill(building.rc_model['Aw'])
    ## roof/floor area
    array_OProof = np.empty(8760)
    array_OProof.fill(building.rc_model['footprint'])
    ## surface to volume ratio
    array_sv = np.empty(8760)
    array_sv.fill(building.rc_model['surface_volume'])
    ### final array of geometry properties
    array_geom = np.column_stack((array_Af, array_OPwall, array_OPwallB, array_GLwin, array_OProof, array_sv))
    return array_geom


def get_array_architecture_variables(building, building_name, locator):

    data_architecture = dbf_to_dataframe(locator.get_building_architecture())
    data_architecture.set_index('Name', inplace=True)
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
    array_arch = np.column_stack(
        (array_wwr, array_cm, array_n50, array_Uroof, array_aroof, array_Uwall, array_awall, array_Ubase,
         array_Uwin, array_Gwin, array_rfsh))
    return array_arch


def get_array_comfort_variables(building, date, gv, schedules_dict, weather_data):
    # indoor comfort
    schedules, tsd = initialize_inputs(building, gv, schedules_dict, weather_data)
    tsd = controllers.calc_simple_temp_control(tsd, building.comfort, gv.seasonhours[0] + 1, gv.seasonhours[1],
                                               date.dayofweek)
    np.place(tsd['ta_hs_set'], np.isnan(tsd['ta_hs_set']), -100)
    np.place(tsd['ta_cs_set'], np.isnan(tsd['ta_cs_set']), 100)
    array_Thset = tsd['ta_hs_set']
    array_Tcset = tsd['ta_cs_set']
    ### final array of indoor comfor
    array_cmfrt = np.empty((1, 8760))
    array_cmfrt[0, :] = array_Thset
    array_cmfrt[0, gv.seasonhours[0] + 1:gv.seasonhours[1]] = array_Tcset[gv.seasonhours[0] + 1:gv.seasonhours[1]]

    array_HVAC_status=np.where(array_cmfrt > 99, 0,
             (np.where(array_cmfrt < -99, 0, 1)))

    array_HVAC_heating = np.empty((1, 8760))
    array_HVAC_heating[0,:] = np.where(array_Thset < -99, 0,1)
    array_HVAC_cooling = np.empty((1, 8760))
    array_HVAC_cooling[0,:] = np.where(array_Tcset > 99, 0, 1)

    array_cmfrts=np.concatenate((array_cmfrt,array_HVAC_status),axis=0)
    array_cmfrts=np.concatenate((array_cmfrts,array_HVAC_heating),axis=0)
    array_cmfrts=np.concatenate((array_cmfrts,array_HVAC_cooling),axis=0)

    return array_cmfrts, schedules, tsd


def get_array_internal_loads_variables(schedules, tsd, building, gv):

    # internal loads
    array_electricity = tsd['Eaf'] + tsd['Edataf'] + tsd['Elf'] + tsd['Eprof'] + tsd['Eref']
    np.place(tsd['Qhprof'], np.isnan(tsd['Qhprof']), 0)
    array_sensible_gain = tsd['Qs'] + tsd['Qhprof']
    array_latent_gain = tsd['w_int']
    for t in range(8760):
        tsd['I_sol'][t], tsd['I_rad'][t]=calc_I_sol(t, building, tsd, gv)

    array_solar_gain=tsd['I_sol']+tsd['I_rad']
        
    array_ve = tsd['ve']
    array_Vww = schedules['Vww']
    ### final array of internal loads
    array_int_load = np.column_stack((array_electricity, array_sensible_gain, array_latent_gain, array_solar_gain, array_ve, array_Vww))
    return array_int_load


def get_array_HVAC_variables(building):
    # HVAC systems
    ##heating system
    array_dThs_C = np.empty(8760)
    array_dThs_C.fill(building.hvac['dThs_C'])
    ##cooling system
    array_dTcs_C = np.empty(8760)
    array_dTcs_C.fill(building.hvac['dTcs_C'])
    ## ventilation
    array_economizer = np.empty(8760)
    array_economizer.fill(int((building.hvac['ECONOMIZER'])=='True'))
    array_win_vent = np.empty(8760)
    array_win_vent.fill(int((building.hvac['WIN_VENT'])=='True'))
    array_mech_vent = np.empty(8760)
    array_mech_vent.fill(int((building.hvac['MECH_VENT'])=='True'))
    array_heat_rec = np.empty(8760)
    array_heat_rec.fill(int((building.hvac['HEAT_REC'])=='True'))
    array_night_flsh = np.empty(8760)
    array_night_flsh.fill(int((building.hvac['NIGHT_FLSH'])=='True'))
    ##controller
    array_ctrl_Qhs = np.empty(8760)
    array_ctrl_Qhs.fill(1 * (building.hvac['dT_Qhs']))
    array_ctrl_Qcs = np.empty(8760)
    array_ctrl_Qcs.fill(1 * (building.hvac['dT_Qcs']))
    ### final array of HVAC systems
    array_hvac = np.column_stack((array_dThs_C, array_dTcs_C, array_economizer, array_win_vent, array_mech_vent,
                           array_heat_rec, array_night_flsh, array_ctrl_Qhs, array_ctrl_Qcs))
    return array_hvac


def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    building_name = 'B155066'
    get_cea_inputs(locator=locator, building_name=building_name, gv=gv)

if __name__ == '__main__':
    run_as_script()

## todo change the structure of run as script: add global variables and locator
## todo write documentation on te script