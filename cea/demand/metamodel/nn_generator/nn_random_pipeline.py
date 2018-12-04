# coding=utf-8
"""
'nn_random_pipeline.py' script is a pipeline of the following jobs:
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

import numpy as np
from cea.demand.metamodel.nn_generator.nn_random_sampler import sampling_main
from cea.demand.metamodel.nn_generator.nn_settings import nn_passes, random_variables, target_parameters, autoencoder
from cea.demand.metamodel.nn_generator.nn_trainer import neural_trainer, nn_input_collector
from sklearn.externals import joblib
import cea.config
import cea.inputlocator
import cea.globalvar

import cea
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator.nn_trainer_resume import neural_trainer_resume, nn_model_collector
from cea.utilities import epwreader

def run_nn_pipeline(locator, random_variables, target_parameters, list_building_names, weather_path, scalerX,
                    scalerT, multiprocessing, config, nn_delay, climatic_variables, region, year,use_daysim_radiation):
    '''
    this function enables a pipeline of tasks by calling a random sampler and a neural network trainer
    :param locator: points to the variables
    :param random_variables:  a list containing the names of variables associated with uncertainty (can be accessed from 'nn_settings.py')
    :param target_parameters:  a list containing the name of desirable outputs (can be accessed from 'nn_settings.py')
    :param list_building_names: a list containing the name of desired buildings
    :param weather_path: weather path
    :return: -
    '''
    #   create n random sample of the whole dataset of buildings. n is accessible from 'nn_settings.py'
    sampling_main(locator, random_variables, target_parameters, list_building_names, weather_path,
                  multiprocessing, config, nn_delay, climatic_variables, region, year, use_daysim_radiation)
    #   reads the n random files from the previous step and creat the input and targets for the neural net
    urban_input_matrix, urban_taget_matrix = nn_input_collector(locator)
    #   train the neural net
    neural_trainer(urban_input_matrix, urban_taget_matrix, locator, scalerX, scalerT, autoencoder)
    #   do nn_passes additional training (nn_passes can be accessed from 'nn_settings.py')
    for i in range(nn_passes):
        #   fix a different seed number (for random generation) in each loop
        np.random.seed(i)
        #   create n random sample of the whole dataset of buildings. n is accessible from 'nn_settings.py'
        sampling_main(locator, random_variables, target_parameters, list_building_names, weather_path,
                      multiprocessing, config, nn_delay, climatic_variables, region, year, use_daysim_radiation)
        #   reads the n random files from the previous step and creat the input and targets for the neural net
        urban_input_matrix, urban_taget_matrix = nn_input_collector(locator)
        #   reads the saved model and the normalizer
        model, scalerT, scalerX = nn_model_collector(locator)
        #   resume training of the neural net
        neural_trainer_resume(urban_input_matrix, urban_taget_matrix, model, scalerX, scalerT, locator, autoencoder)
        print ("%d random sample passes of the city have been completed" %i)


def main(config):

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]
    region = config.region
    settings = config.demand
    use_daysim_radiation = settings.use_daysim_radiation
    weather_path = config.weather
    building_properties, schedules_dict, date = properties_and_schedule(locator, region, year, use_daysim_radiation)
    list_building_names = building_properties.list_building_names()
    scalerX_file, scalerT_file = locator.get_minmaxscalar_model()
    scalerX = joblib.load(scalerX_file)
    scalerT = joblib.load(scalerT_file)
    run_nn_pipeline(locator, random_variables, target_parameters, list_building_names, weather_path, scalerX, scalerT,
                    multiprocessing=config.multiprocessing, config=config, nn_delay=config.neural_network.nn_delay,
                    climatic_variables=config.neural_network.climatic_variables, region = config.region,
                    year=config.neural_network.year, use_daysim_radiation=settings.use_daysim_radiation)


if __name__ == '__main__':
    main(cea.config.Configuration())
