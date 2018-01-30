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

from cea.demand.metamodel.nn_generator.nn_presampled_caller import presampled_collector
from cea.demand.metamodel.nn_generator.nn_settings import number_samples_scaler, number_sweeps, autoencoder
from cea.demand.metamodel.nn_generator.nn_trainer import neural_trainer
from sklearn.externals import joblib
import cea.inputlocator
import cea.config

from cea.demand.metamodel.nn_generator.nn_trainer_resume import neural_trainer_resume, nn_model_collector


def run_nn_pipeline(locator, scalerX, scalerT):
    '''
    this function enables a pipeline of tasks by calling a random sampler and a neural network trainer
    :param locator: points to the variables
    :param random_variables:  a list containing the names of variables associated with uncertainty (can be accessed from 'nn_settings.py')
    :param target_parameters:  a list containing the name of desirable outputs (can be accessed from 'nn_settings.py')
    :param list_building_names: a list containing the name of desired buildings
    :param weather_path: weather path
    :param gv: global variables
    :return: -
    '''

    for k in range(number_sweeps):
        collect_count = 0
        #   reads the n random files from the previous step and creat the input and targets for the neural net
        urban_input_matrix, urban_taget_matrix, collect_count = presampled_collector(locator, collect_count)
        #   train the neural net
        neural_trainer(urban_input_matrix, urban_taget_matrix, locator, scalerX, scalerT, autoencoder)
        #   do nn_passes additional training (nn_passes can be accessed from 'nn_settings.py')
        while (collect_count < number_samples_scaler):
            #   fix a different seed number (for random generation) in each loop
            # np.random.seed(collect_count)
            #   reads the n random files from the previous step and creat the input and targets for the neural net
            urban_input_matrix, urban_taget_matrix, collect_count = presampled_collector(locator, collect_count)
            #   reads the saved model and the normalizer
            model, scalerT, scalerX = nn_model_collector(locator)
            #   resume training of the neural net
            neural_trainer_resume(urban_input_matrix, urban_taget_matrix, model, scalerX, scalerT, locator, autoencoder)


def main(config):

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    scalerX_file, scalerT_file = locator.get_minmaxscalar_model()
    scalerX = joblib.load(scalerX_file)
    scalerT = joblib.load(scalerT_file)
    run_nn_pipeline(locator, scalerX, scalerT)


if __name__ == '__main__':
    main(cea.config.Configuration())
