import os

import numpy as np
import pandas as pd
from cea.demand.metamodel.nn_generator.nn_trainer_resume import nn_model_collector


def get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, locator):
    input_NN_x = urban_input_matrix
    inputs_x = scalerX.transform(input_NN_x)

    model_estimates = model.predict(inputs_x)
    filtered_predict = scalerT.inverse_transform(model_estimates)

    # filter_logic = np.isin(targets_t, 0)
    # target_anomalies = np.asarray(np.where(filter_logic), dtype=np.int)
    # t_anomalies_rows, t_anomalies_cols = target_anomalies.shape
    # anomalies_replacements = np.zeros(t_anomalies_cols)
    # filtered_predict[target_anomalies, 0] = anomalies_replacements

    model_estimates = locator.get_neural_network_estimates()
    filtered_predict = pd.DataFrame(filtered_predict)
    filtered_predict.to_csv(model_estimates, index=False, header=False, float_format='%.3f', decimal='.')


def test_sample_collector(locator):
    test_sample_path = locator.get_nn_inout_folder()
    overrides_path=locator.get_building_overrides()
    os.remove(overrides_path)

    file_path_inputs = os.path.join(test_sample_path, "input_predict.csv")
    urban_input_matrix = np.asarray(pd.read_csv(file_path_inputs))

    return urban_input_matrix

def input_prepare_estimate(list_building_names, locator, target_parameters, gv):
    '''
    this function prepares the inputs and targets for the neural net by splitting the jobs between different processors
    :param list_building_names: a list of building names
    :param locator: points to the variables
    :param target_parameters: (imported from 'nn_settings.py') a list containing the name of desirable outputs
    :param gv: global variables
    :return: inputs and targets for the whole dataset (urban_input_matrix, urban_taget_matrix)
    '''

    #   open multiprocessing pool
    pool = mp.Pool()
    #   count number of CPUs
    gv.log("Using %i CPU's" % mp.cpu_count())
    #   creat an empty job list to be filled later
    joblist = []
    #   create one job for each data preparation task i.e. each building
    for building_name in list_building_names:
        job = pool.apply_async(input_matrix.input_prepare_multi_processing,
                               [building_name, gv, locator, target_parameters])
        joblist.append(job)
    #   run the input/target preperation for all buildings in the list (here called jobs)
    for i, job in enumerate(joblist):
        NN_input_ready , NN_target_ready=job.get(240)
        #   remove buildings that have "NaN" in their input (e.g. if heating/cooling is off, the indoor temperature
        #   will be returned as "NaN"). Afterwards, stack the inputs/targets of all buildings
        check_nan=1*(np.isnan(np.sum(NN_input_ready)))
        if check_nan == 0:
            if i == 0:
                urban_input_matrix = NN_input_ready
                urban_taget_matrix = NN_target_ready
            else:
                urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))
                urban_taget_matrix = np.concatenate((urban_taget_matrix, NN_target_ready))

    #   close the multiprocessing
    pool.close()

    return urban_input_matrix, urban_taget_matrix


def test_nn_performance(locator):
    urban_input_matrix = test_sample_collector(locator)
    model, scalerT, scalerX = nn_model_collector(locator)
    get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, locator)


def run_as_script():
    import cea.config
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)

    test_nn_performance(locator)


if __name__ == '__main__':
    run_as_script()
