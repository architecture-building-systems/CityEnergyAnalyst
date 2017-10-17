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

import cea
from sklearn.externals import joblib
from cea.demand.calibration.nn_generator.nn_trainer_resume import neural_trainer_resume, nn_model_collector
from cea.demand.calibration.nn_generator.nn_settings import number_sweeps, number_samples_scaler, random_variables, target_parameters
from cea.demand.demand_main import properties_and_schedule
from cea.demand.calibration.nn_generator.nn_presampled_caller import presampled_collector

def run_nn_continue(locator, random_variables, target_parameters, list_building_names, weather_path, gv, scalerX, scalerT):
    '''
    this function continues a pipeline of tasks by calling a random sampler and a neural network trainer
    :param locator: points to the variables
    :param random_variables:  a list containing the names of variables associated with uncertainty (can be accessed from 'nn_settings.py')
    :param target_parameters:  a list containing the name of desirable outputs (can be accessed from 'nn_settings.py')
    :param list_building_names: a list containing the name of desired buildings
    :param weather_path: weather path
    :param gv: global variables
    :return: -
    '''

    for k in range(number_sweeps):
        collect_count=0
        while (collect_count<number_samples_scaler):
            #   fix a different seed number (for random generation) in each loop
            #np.random.seed(collect_count)
            #   reads the n random files from the previous step and creat the input and targets for the neural net
            urban_input_matrix, urban_taget_matrix, collect_count = presampled_collector(locator,collect_count)
            #   reads the saved model and the normalizer
            model, scalerT, scalerX = nn_model_collector(locator)
            #   resume training of the neural net
            neural_trainer_resume(urban_input_matrix, urban_taget_matrix, model, scalerX, scalerT, locator)

def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    scalerX_file, scalerT_file = locator.get_minmaxscalar_model()
    scalerX = joblib.load(scalerX_file)
    scalerT = joblib.load(scalerT_file)
    run_nn_continue(locator, random_variables, target_parameters, list_building_names, weather_path, gv, scalerX, scalerT)

if __name__ == '__main__':
    run_as_script()
