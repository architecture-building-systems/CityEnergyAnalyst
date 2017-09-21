# coding=utf-8
"""
Input matrix script creates matrix of input parameters for the NN out of CEA
"""
from __future__ import division
import numpy as np
import pandas as pd
from cea.demand.demand_main import properties_and_schedule
from cea.demand.calibration.nn_generator.input_matrix import get_cea_inputs
from cea.demand.calibration.nn_generator.nn_settings import nn_delay
import cea.inputlocator
import os

__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def input_prepare_main(list_building_names, locator, target_parameters):
    '''
    this function prepares the final inputs and targets to be fed into the NN
    :param list_building_names:
    :param locator:
    :param target_parameters:
    :return:
    '''
    for counter, building_name in enumerate(list_building_names):
        raw_nn_targets = get_cea_outputs(building_name, locator, target_parameters)
        raw_nn_inputs = get_cea_inputs(building_name)
        NN_input_ready, NN_target_ready = prep_NN_delay(raw_nn_inputs, raw_nn_targets, nn_delay)
        if counter == 0:
            urban_input_matrix = NN_input_ready
            urban_taget_matrix = NN_target_ready
        else:
            urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))
            urban_taget_matrix = np.concatenate((urban_taget_matrix, NN_target_ready))

        print (counter)
    return urban_input_matrix, urban_taget_matrix

def prep_NN_delay(NN_input,NN_target,NN_delays):
    '''
    :param NN_input: the inputs to be prepared and sent to NN for training
    :type   NN_input: numpy array
    :param NN_target:
    :param NN_delays:
    :return: NN_inpuy_ready , NN_target_ready
    :rtype: numpy arrays

    '''
    input1=NN_input
    target1=NN_target
    nS, nF = input1.shape
    nSS, nT = target1.shape
    nD=NN_delays-1
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
    NN_input_ready=np.concatenate([trimmed_inputn, trimmed_inputt], axis=1)
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

def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    target_parameters=['Qhsf', 'Qcsf', 'Qwwf','Ef', 'theta_a']
    input_prepare_main(list_building_names, locator, target_parameters)




if __name__ == '__main__':
    run_as_script()