import os
from math import sqrt

import numpy as np
import pandas as pd
from cea.demand.calibration.nn_generator.nn_settings import random_variables, target_parameters
from cea.demand.calibration.nn_generator.nn_trainer_resume import nn_model_collector
from sklearn.metrics import mean_squared_error, mean_absolute_error

import cea
from cea.demand.demand_main import properties_and_schedule


def get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, urban_taget_matrix, locator):
    input_NN_x=urban_input_matrix
    target_NN_t=urban_taget_matrix
    inputs_x = scalerX.transform(input_NN_x)

    model_estimates = model.predict(inputs_x)
    filtered_predict = scalerT.inverse_transform(model_estimates)

    # filter_logic = np.isin(targets_t, 0)
    # target_anomalies = np.asarray(np.where(filter_logic), dtype=np.int)
    # t_anomalies_rows, t_anomalies_cols = target_anomalies.shape
    # anomalies_replacements = np.zeros(t_anomalies_cols)
    # filtered_predict[target_anomalies, 0] = anomalies_replacements

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



    print (rmse_Qhsf,mbe_Qhsf)
    print (rmse_Qcsf,mbe_Qcsf)
    print (rmse_Qwwf,mbe_Qwwf)
    print (rmse_Ef,mbe_Ef)
    print (rmse_T_int,mbe_T_int)

    model_estimates = locator.get_neural_network_estimates()
    filtered_predict=pd.DataFrame(filtered_predict)
    filtered_predict.to_csv(model_estimates, index=False, header=False, float_format='%.3f', decimal='.')


def test_sample_collector(locator):
    test_sample_path = locator.get_nn_inout_folder()
    file_path_inputs = os.path.join(test_sample_path, "input_test.csv")
    file_path_targets = os.path.join(test_sample_path, "target_test.csv")
    urban_input_matrix = np.asarray(pd.read_csv(file_path_inputs))
    urban_taget_matrix = np.asarray(pd.read_csv(file_path_targets))

    return urban_input_matrix, urban_taget_matrix

def test_nn_performance(locator, random_variables, target_parameters, list_building_names, weather_path, gv):
    urban_input_matrix, urban_taget_matrix = test_sample_collector(locator)
    model, scalerT, scalerX = nn_model_collector(locator)
    get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, urban_taget_matrix, locator)



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
