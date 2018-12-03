# coding=utf-8
"""
'input_matrix.py' script hosts the following functions:
    (1) collect CEA inputs
    (2) collect CEA outputs (demands)
    (3) add delay to time-sensitive inputs
    (4) return the input and target matrices
"""

from math import sqrt

import pandas as pd
from cea.demand.metamodel.nn_generator.nn_settings import random_variables, target_parameters
from cea.demand.metamodel.nn_generator.nn_trainer_resume import nn_model_collector
from cea.demand.metamodel.nn_generator.nn_test_sampler import sampling_single
from sklearn.metrics import mean_squared_error, mean_absolute_error
import cea.inputlocator
import cea.config
import cea.globalvar
from cea.demand.demand_main import properties_and_schedule
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca","Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def get_nn_performance(model, scalerT, scalerX, urban_input_matrix, urban_taget_matrix, locator):
    input_NN_x = urban_input_matrix
    target_NN_t = urban_taget_matrix
    inputs_x = scalerX.transform(input_NN_x)

    model_estimates = model.predict(inputs_x)
    filtered_predict = scalerT.inverse_transform(model_estimates)

    rmse_Qhsf = sqrt(mean_squared_error(target_NN_t[:, 0], filtered_predict[:, 0]))
    rmse_Qcsf = sqrt(mean_squared_error(target_NN_t[:, 1], filtered_predict[:, 1]))
    rmse_Qwwf = sqrt(mean_squared_error(target_NN_t[:, 2], filtered_predict[:, 2]))
    rmse_Ef = sqrt(mean_squared_error(target_NN_t[:, 3], filtered_predict[:, 3]))
    rmse_T_int = sqrt(mean_squared_error(target_NN_t[:, 4], filtered_predict[:, 4]))

    mbe_Qhsf = mean_absolute_error(target_NN_t[:, 0], filtered_predict[:, 0])
    mbe_Qcsf = mean_absolute_error(target_NN_t[:, 1], filtered_predict[:, 1])
    mbe_Qwwf = mean_absolute_error(target_NN_t[:, 2], filtered_predict[:, 2])
    mbe_Ef = mean_absolute_error(target_NN_t[:, 3], filtered_predict[:, 3])
    mbe_T_int = mean_absolute_error(target_NN_t[:, 4], filtered_predict[:, 4])

    print ("the rmse of Qhsf is %d and the mbe is %d" %(rmse_Qhsf, mbe_Qhsf))
    print (rmse_Qcsf, mbe_Qcsf)
    print (rmse_Qwwf, mbe_Qwwf)
    print (rmse_Ef, mbe_Ef)
    print (rmse_T_int, mbe_T_int)

    model_estimates = locator.get_neural_network_estimates()
    filtered_predict = pd.DataFrame(filtered_predict)
    filtered_predict.to_csv(model_estimates, index=False, header=False, float_format='%.3f', decimal='.')

    return urban_input_matrix, urban_taget_matrix


def eval_nn_performance(locator, random_variables, target_parameters, list_building_names,
                        config, nn_delay, climatic_variables, region, year, use_daysim_radiation,
                        use_stochastic_occupancy):
    urban_input_matrix, urban_taget_matrix = sampling_single(locator, random_variables, target_parameters,
                                                             list_building_names, config,
                                                             nn_delay, climatic_variables, region, year,
                                                             use_daysim_radiation,use_stochastic_occupancy)
    model, scalerT, scalerX = nn_model_collector(locator)
    get_nn_performance(model, scalerT, scalerX, urban_input_matrix, urban_taget_matrix, locator)


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]
    region = config.region
    settings = config.demand
    use_daysim_radiation = settings.use_daysim_radiation
    building_properties, schedules_dict, date = properties_and_schedule(locator, region, year, use_daysim_radiation)
    list_building_names = building_properties.list_building_names()
    eval_nn_performance(locator, random_variables, target_parameters, list_building_names,
                        config=config, nn_delay=config.neural_network.nn_delay,
                        climatic_variables=config.neural_network.climatic_variables, region=config.region,
                        year=config.neural_network.year, use_daysim_radiation=settings.use_daysim_radiation,
                        use_stochastic_occupancy=config.demand.use_stochastic_occupancy)


if __name__ == '__main__':
    main(cea.config.Configuration())
