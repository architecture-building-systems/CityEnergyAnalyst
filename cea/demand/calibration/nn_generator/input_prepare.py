# coding=utf-8
"""
Input matrix script creates matrix of input parameters for the NN out of CEA
"""
from __future__ import division
import numpy as np
import pandas as pd
from cea.demand.demand_main import properties_and_schedule
from cea.demand.calibration.nn_generator import input_matrix

from cea.demand.calibration.nn_generator.input_matrix import get_cea_inputs
from cea.demand.calibration.nn_generator.nn_settings import nn_delay
import cea.inputlocator
import multiprocessing as mp
import os

__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def input_prepare_main(list_building_names, locator, target_parameters, gv):
    '''
    this function prepares the final inputs and targets to be fed into the NN
    :param list_building_names:
    :param locator:
    :param target_parameters:
    :return:
    '''
    pool = mp.Pool()
    gv.log("Using %i CPU's" % mp.cpu_count())
    joblist = []
    for building_name in list_building_names:
        job = pool.apply_async(input_matrix.input_prepare_multi_processing,
                               [building_name, gv, locator, target_parameters])
        joblist.append(job)
    for i, job in enumerate(joblist):

        NN_input_ready , NN_target_ready=job.get(240)
        check_nan=1*(np.isnan(np.sum(NN_input_ready)))
        if check_nan == 0:
            if i == 0:
                urban_input_matrix = NN_input_ready
                urban_taget_matrix = NN_target_ready
            else:
                urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))
                urban_taget_matrix = np.concatenate((urban_taget_matrix, NN_target_ready))

    pool.close()
    return urban_input_matrix, urban_taget_matrix

    # from cea.demand.calibration.nn_generator.input_matrix import input_prepare_multi_processing
    # for counter, building_name in enumerate(list_building_names):
    #     NN_input_ready, NN_target_ready =input_prepare_multi_processing(building_name, gv, locator, target_parameters)
    #     check_nan = 1 * (np.isnan(np.sum(NN_input_ready)))
    #     if check_nan == 0:
    #         if counter == 0:
    #             urban_input_matrix = NN_input_ready
    #             urban_taget_matrix = NN_target_ready
    #         else:
    #             urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))
    #             urban_taget_matrix = np.concatenate((urban_taget_matrix, NN_target_ready))
    #
    #     print (counter)
    #
    #return urban_input_matrix, urban_taget_matrix


    # for counter, building_name in enumerate(list_building_names):
    #     NN_input_ready, NN_target_ready = input_prepare_multi_processing(building_name, gv, locator, target_parameters)
    #     if counter == 0:
    #         urban_input_matrix = NN_input_ready
    #         urban_taget_matrix = NN_target_ready
    #     else:
    #         urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))
    #         urban_taget_matrix = np.concatenate((urban_taget_matrix, NN_target_ready))
    #
    #     print (counter)
    # return urban_input_matrix, urban_taget_matrix




def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    target_parameters=['Qhsf_kWh', 'Qcsf_kWh', 'Qwwf_kWh','Ef_kWh', 'T_int_C']
    input_prepare_main(list_building_names, locator, target_parameters, gv)




if __name__ == '__main__':
    run_as_script()