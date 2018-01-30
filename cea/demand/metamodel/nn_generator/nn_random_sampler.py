# coding=utf-8
"""
'nn_random_sampler.py' script is a generator of random properties for the entire case-study
"""

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# import h5py
import os
import pickle

import numpy as np
import pandas as pd

import cea.inputlocator
import cea.globalvar
import cea.config
from cea.demand import demand_main
from cea.demand.calibration.bayesian_calibrator.calibration_sampling import apply_sample_parameters
from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator.nn_settings import number_samples, random_variables, \
    target_parameters, boolean_vars
from cea.demand.metamodel.nn_generator.input_prepare import input_prepare_main


def input_dropout(urban_input_matrix, urban_taget_matrix):
    rows, cols = urban_input_matrix.shape
    drop_random_array = np.random.rand(rows)
    drop_idx_filter = drop_random_array > 0.5
    drop_idx = np.where(drop_idx_filter)
    urban_input_matrix = np.delete(urban_input_matrix, drop_idx, 0)
    urban_taget_matrix = np.delete(urban_taget_matrix, drop_idx, 0)

    return urban_input_matrix, urban_taget_matrix


def sampling_main(locator, random_variables, target_parameters, list_building_names, weather_path, gv, multiprocessing):
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
    size_city = size_city[0]
    #   create random samples of the entire district
    for i in range(number_samples):  # the parameter "number_samples" is accessible from 'nn_settings.py'
        bld_counter = 0
        # create list of samples with a LHC sampler and save to disk
        samples, pdf_list = latin_sampler(locator, size_city, random_variables)
        samples = samples[0]  # extract the non-normalized samples

        # create a file of overides with the samples
        dictionary = dict(zip(random_variables, samples.transpose()))
        overides_dataframe = pd.DataFrame(dictionary)
        overides_dataframe['Name'] = list_building_names

        # replace the 1, 0 with True and False
        for var in boolean_vars:
            overides_dataframe[var].replace(1, "True", inplace=True)
            overides_dataframe[var].replace(0, "False", inplace=True)
            overides_dataframe[var].replace(0.0, "False", inplace=True)

        # save file so the demand calculation can know about it.
        overides_dataframe.to_csv(locator.get_building_overrides())

        #   run cea demand
        demand_main.demand_calculation(locator, weather_path, gv, multiprocessing=multiprocessing)
        #   prepare the inputs for feeding into the neural network
        urban_input_matrix, urban_taget_matrix = input_prepare_main(list_building_names, locator, target_parameters, gv)
        #   drop half the inputs and targets to avoid overfitting and save RAM / Disk space
        urban_input_matrix, urban_taget_matrix = input_dropout(urban_input_matrix, urban_taget_matrix)
        #   get the pathfor saving the files
        nn_inout_path = locator.get_nn_inout_folder()
        #   save inputs with sequential naming
        file_path_inputs = os.path.join(nn_inout_path, "input%(i)s.csv" % locals())
        data_file_inputs = pd.DataFrame(urban_input_matrix)
        data_file_inputs.to_csv(file_path_inputs, header=False, index=False)
        #   save inputs with sequential naming
        file_path_targets = os.path.join(nn_inout_path, "target%(i)s.csv" % locals())
        data_file_targets = pd.DataFrame(urban_taget_matrix)
        data_file_targets.to_csv(file_path_targets, header=False, index=False)

        # return urban_input_matrix, urban_taget_matrix


def main(config):
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)

    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    sampling_main(locator, random_variables, target_parameters, list_building_names, config.weather, gv,
                  multiprocessing=config.multiprocessing)


if __name__ == '__main__':
    main(cea.config.Configuration())
