import cea
import numpy as np
import pandas as pd
from math import sqrt
from cea.demand.calibration.nn_generator.nn_test_sampler import sampling_single
from cea.demand.calibration.nn_generator.nn_trainer_resume import nn_model_collector
from cea.demand.calibration.nn_generator.nn_settings import random_variables, target_parameters
from cea.demand.demand_main import properties_and_schedule
from sklearn.metrics import mean_squared_error

def get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, urban_taget_matrix, locator):
    input_NN_x=urban_input_matrix
    target_NN_t=urban_taget_matrix
    inputs_x = scalerX.fit_transform(input_NN_x)

    model_estimates = model.predict(inputs_x)
    filtered_predict = scalerT.inverse_transform(model_estimates)

    # filter_logic = np.isin(targets_t, 0)
    # target_anomalies = np.asarray(np.where(filter_logic), dtype=np.int)
    # t_anomalies_rows, t_anomalies_cols = target_anomalies.shape
    # anomalies_replacements = np.zeros(t_anomalies_cols)
    # filtered_predict[target_anomalies, 0] = anomalies_replacements

    rmse_Qhsf = sqrt(mean_squared_error(target_NN_t[:, 0], filtered_predict[:, 0]))
    rmse_Qcsf = sqrt(mean_squared_error(target_NN_t[:, 1], filtered_predict[:, 1]))
    # rmse_Qwwf = sqrt(mean_squared_error(target_NN_t[:, 2], filtered_predict[:, 2]))
    # rmse_Ef = sqrt(mean_squared_error(target_NN_t[:, 3], filtered_predict[:, 3]))
    # rmse_T_int = sqrt(mean_squared_error(target_NN_t[:, 4], filtered_predict[:, 4]))

    mean_target_Qhsf = np.mean(target_NN_t[:, 0])
    mean_target_Qcsf = np.mean(target_NN_t[:, 1])
    # mean_target_Qwwf = np.mean(target_NN_t[:, 2])
    # mean_target_Ef = np.mean(target_NN_t[:, 3])
    # mean_target_T_int = np.mean(target_NN_t[:, 4])

    cv_rmse_Qhsf = np.divide(rmse_Qhsf, mean_target_Qhsf)
    cv_rmse_Qcsf = np.divide(rmse_Qcsf, mean_target_Qcsf)
    # cv_rmse_Qwwf = np.divide(rmse_Qwwf, mean_target_Qwwf)
    # cv_rmse_Ef = np.divide(rmse_Ef, mean_target_Ef)
    # cv_rmse_T_int = np.divide(rmse_T_int, mean_target_T_int)

    print (rmse_Qhsf,cv_rmse_Qhsf)
    print (rmse_Qcsf,cv_rmse_Qcsf)
    # print (rmse_Qwwf,cv_rmse_Qwwf)
    # print (rmse_Ef,cv_rmse_Ef)
    # print (rmse_T_int,cv_rmse_T_int)

    model_estimates = locator.get_neural_network_estimates()
    filtered_predict=pd.DataFrame(filtered_predict)
    filtered_predict.to_csv(model_estimates, index=False, header=False, float_format='%.3f', decimal='.')


def test_nn_performance(locator, random_variables, target_parameters, list_building_names, weather_path, gv):
    urban_input_matrix, urban_taget_matrix=sampling_single(locator, random_variables, target_parameters, list_building_names, weather_path, gv)
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
