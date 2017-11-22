# coding=utf-8
"""
'input_prepare.py' script does the following:
    (1) activates multiprocessing for parallel computation
    (2) stacks the results into a single matrix
"""
from __future__ import division
import multiprocessing as mp
import numpy as np
import cea.inputlocator
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator import input_matrix

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def input_prepare_main(list_building_names, locator, target_parameters, gv):
    '''
    this function prepares the inputs and targets for the neural net by splitting the jobs between different processors
    :param list_building_names: a list of building names
    :param locator: points to the variables
    :param target_parameters: (imported from 'nn_settings.py') a list containing the name of desirable outputs
    :param gv: global variables
    :return: inputs and targets for the whole dataset (urban_input_matrix, urban_taget_matrix)
    '''

    #   open multiprocessing pool
    pool = mp.Pool()
    #   count number of CPUs
    gv.log("Using %i CPU's" % mp.cpu_count())
    #   creat an empty job list to be filled later
    joblist = []
    #   create one job for each data preparation task i.e. each building
    for building_name in list_building_names:
        job = pool.apply_async(input_matrix.input_prepare_multi_processing,
                               [building_name, gv, locator, target_parameters])
        joblist.append(job)
    #   run the input/target preperation for all buildings in the list (here called jobs)
    for i, job in enumerate(joblist):
        NN_input_ready , NN_target_ready=job.get(240)
        #   remove buildings that have "NaN" in their input (e.g. if heating/cooling is off, the indoor temperature
        #   will be returned as "NaN"). Afterwards, stack the inputs/targets of all buildings
        check_nan=1*(np.isnan(np.sum(NN_input_ready)))
        if check_nan == 0:
            if i == 0:
                urban_input_matrix = NN_input_ready
                urban_taget_matrix = NN_target_ready
            else:
                urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))
                urban_taget_matrix = np.concatenate((urban_taget_matrix, NN_target_ready))

    #   close the multiprocessing
    pool.close()

    return urban_input_matrix, urban_taget_matrix


    # #***untag the following section of you do not want multiprocessing***
    # from cea.demand.metamodel.nn_generator.input_matrix import input_prepare_multi_processing
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
    # return urban_input_matrix, urban_taget_matrix


def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario=scenario_path)
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    target_parameters=['Qhsf_kWh', 'Qcsf_kWh', 'Qwwf_kWh','Ef_kWh', 'T_int_C']
    input_prepare_main(list_building_names, locator, target_parameters, gv)




if __name__ == '__main__':
    run_as_script()