# coding=utf-8
"""
'nn_pipeline.py" script is a pipeline of the following jobs:
    (1) calls "sampling_main" function for random generation of features
    (2) calls "neural_trainer" function for training a first neural network and saving the model
    (3) executes a loop in which "sampling_main" and "neural_training" are iteratively called for
        sequential training of the neural network.
"""

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.demand_main import properties_and_schedule
from cea.demand.calibration.bayesian_calibrator.calibration_sampling import apply_sample_parameters
from cea.demand import demand_main
import pickle
import cea
import json
#import h5py
import os
import numpy as np
import pandas as pd
from cea.demand.calibration.nn_generator.nn_settings import number_samples_scaler, random_variables,\
    target_parameters, boolean_vars
from cea.demand.calibration.nn_generator.input_prepare import input_prepare_main


def sampling_scaler(locator, random_variables, target_parameters, list_building_names, weather_path, gv):
    '''
    this function creates a number of random samples for the entire district (city)
    :param locator: points to the variables
    :param random_variables: a list containing the names of variables associated with uncertainty (can be accessed from 'nn_settings.py')
    :param target_parameters: a list containing the name of desirable outputs (can be accessed from 'nn_settings.py')
    :param list_building_names: a list containing the name of desired buildings
    :param weather_path: weather path
    :param gv: global variables
    :return: -
    '''

    #   get number of buildings
    size_city = np.shape(list_building_names)
    size_city=size_city[0]
    #   create random samples of the entire district
    for i in range(number_samples_scaler): #the parameter "number_samples" is accessible from 'nn_settings.py'
        bld_counter=0
        # create list of samples with a LHC sampler and save to disk
        samples, pdf_list = latin_sampler(locator, size_city, random_variables)
        for building_name in (list_building_names):
            np.save(locator.get_calibration_samples(building_name), samples)
            problem = {'variables': random_variables,
                       'building_load': target_parameters, 'probabiltiy_vars': pdf_list}
            pickle.dump(problem, file(locator.get_calibration_problem(building_name), 'w'))
            sample = np.asarray(zip(random_variables, samples[bld_counter, :]))
            apply_sample_parameters(locator, sample)
            bld_counter = bld_counter + 1
        # read the saved *.csv file and replace Boolean with logical (True/False)
        overwritten = pd.read_csv(locator.get_building_overrides())
        bld_counter = 0
        for building_name in (list_building_names):
            sample = np.asarray(zip(random_variables, samples[bld_counter, :]))
            for boolean_mask in (boolean_vars):
                indices=np.where(sample == boolean_mask)

                if  sample[indices[0], 1] == '0.0':
                    sample[indices[0], 1] = 'False'
                else:
                    sample[indices[0], 1] = 'True'

            overwritten.loc[overwritten.Name == building_name, random_variables] = sample[:,1]
            bld_counter = bld_counter + 1

        # for boolean_mask in (boolean_vars):
        #     fazel1=overwritten.replace([0],'False')
        #     overwritten[boolean_mask] = fazel1
        #     overwritten[boolean_mask] = overwritten[boolean_mask].replace(1, 'True')
        overwritten.to_csv(locator.get_building_overrides())

        # run cea demand

        demand_main.demand_calculation(locator, weather_path, gv)
        urban_input_matrix, urban_taget_matrix=input_prepare_main(list_building_names, locator, target_parameters, gv)

        scaler_inout_path = locator.get_minmaxscaler_folder()
        file_path_inputs=os.path.join(scaler_inout_path,"input%(i)s.csv" % locals())
        data_file_inputs = pd.DataFrame(urban_input_matrix)
        data_file_inputs.to_csv(file_path_inputs,header=False,index=False)

        file_path_targets = os.path.join(scaler_inout_path, "target%(i)s.csv" % locals())
        data_file_targets = pd.DataFrame(urban_taget_matrix)
        data_file_targets.to_csv(file_path_targets,header=False,index=False)

    #return urban_input_matrix, urban_taget_matrix


def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    sampling_scaler(locator, random_variables, target_parameters, list_building_names, weather_path, gv)




if __name__ == '__main__':
    run_as_script()
