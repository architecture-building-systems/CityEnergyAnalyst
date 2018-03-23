# coding=utf-8
"""
'nn_random_pipeline.py" script is a pipeline of the following jobs:
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

# import h5py
import os

import cea.globalvar
import cea.inputlocator
import cea.config
import numpy as np
import pandas as pd
from cea.utilities import epwreader
from cea.demand import demand_main
from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator.input_prepare import input_prepare_main
from cea.utilities import epwreader


def sampling_scaler(locator, random_variables, target_parameters, boolean_vars, list_building_names,
                    number_samples_scaler,nn_delay,  gv, config,climatic_variables,year,use_daysim_radiation):
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
    for i in range(number_samples_scaler):  # the parameter "number_samples" is accessible from 'nn_settings.py'
        bld_counter = 0
        # create list of samples with a LHC sampler and save to disk
        samples, samples_norm, pdf_list = latin_sampler(locator, size_city, random_variables)

        # create a file of overides with the samples
        dictionary = dict(zip(random_variables, samples.transpose()))
        overides_dataframe = pd.DataFrame(dictionary)
        overides_dataframe['Name'] = list_building_names

        # replace the 1, 0 with True and False
        for var in boolean_vars:
            somthing=overides_dataframe['ECONOMIZER']
            overides_dataframe[var].replace(1, 'True', inplace=True)
            overides_dataframe[var].replace(0, 'False', inplace=True)
            overides_dataframe[var].replace(0.0, 'False', inplace=True)

        # save file so the demand calculation can know about it.
        overides_dataframe.to_csv(locator.get_building_overrides())

        # run cea demand
        config.demand.override_variables=True
        demand_main.demand_calculation(locator, gv, config )
        urban_input_matrix, urban_taget_matrix = input_prepare_main(list_building_names, locator, target_parameters,
                                                                    gv, nn_delay, climatic_variables, config.region, year,use_daysim_radiation)

        scaler_inout_path = locator.get_minmaxscaler_folder()
        file_path_inputs = os.path.join(scaler_inout_path, "input%(i)s.csv" % locals())
        data_file_inputs = pd.DataFrame(urban_input_matrix)
        data_file_inputs.to_csv(file_path_inputs, header=False, index=False)

        file_path_targets = os.path.join(scaler_inout_path, "target%(i)s.csv" % locals())
        data_file_targets = pd.DataFrame(urban_taget_matrix)
        data_file_targets.to_csv(file_path_targets, header=False, index=False)

        # return urban_input_matrix, urban_taget_matrix


def run_as_script(config):
    gv = cea.globalvar.GlobalVariables()
    settings = config.demand
    use_daysim_radiation = settings.use_daysim_radiation
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]
    region = config.region
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator, region, year, use_daysim_radiation)
    list_building_names = building_properties.list_building_names()
    sampling_scaler(locator=locator, random_variables=config.neural_network.random_variables,
                    target_parameters=config.neural_network.target_parameters,
                    boolean_vars=config.neural_network.boolean_vars, list_building_names=list_building_names,
                    number_samples_scaler=config.neural_network.number_samples_scaler,nn_delay=config.neural_network.nn_delay,
                     gv=gv, config = config,
                    climatic_variables=config.neural_network.climatic_variables,year=config.neural_network.year,use_daysim_radiation=settings.use_daysim_radiation)

if __name__ == '__main__':
    run_as_script(cea.config.Configuration())
