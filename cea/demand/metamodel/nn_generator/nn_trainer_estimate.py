import os
from math import sqrt

import numpy as np
import pandas as pd
from cea.demand.metamodel.nn_generator.nn_settings import random_variables, target_parameters
from cea.demand.metamodel.nn_generator.nn_trainer_resume import nn_model_collector
from sklearn.metrics import mean_squared_error, mean_absolute_error

import cea
from cea.demand.demand_main import properties_and_schedule


def get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, locator):
    input_NN_x=urban_input_matrix
    inputs_x = scalerX.transform(input_NN_x)

    model_estimates = model.predict(inputs_x)
    filtered_predict = scalerT.inverse_transform(model_estimates)

    # filter_logic = np.isin(targets_t, 0)
    # target_anomalies = np.asarray(np.where(filter_logic), dtype=np.int)
    # t_anomalies_rows, t_anomalies_cols = target_anomalies.shape
    # anomalies_replacements = np.zeros(t_anomalies_cols)
    # filtered_predict[target_anomalies, 0] = anomalies_replacements

    model_estimates = locator.get_neural_network_estimates()
    filtered_predict=pd.DataFrame(filtered_predict)
    filtered_predict.to_csv(model_estimates, index=False, header=False, float_format='%.3f', decimal='.')


def test_sample_collector(locator):
    test_sample_path = locator.get_nn_inout_folder()
    file_path_inputs = os.path.join(test_sample_path, "input_predict.csv")
    urban_input_matrix = np.asarray(pd.read_csv(file_path_inputs))

    return urban_input_matrix


def test_nn_performance(locator, random_variables, target_parameters, list_building_names, weather_path, gv):
    urban_input_matrix = test_sample_collector(locator)
    model, scalerT, scalerX = nn_model_collector(locator)
    get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, locator)



def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    test_nn_performance(locator, random_variables, target_parameters, list_building_names, weather_path, gv)

if __name__ == '__main__':
    run_as_script()
