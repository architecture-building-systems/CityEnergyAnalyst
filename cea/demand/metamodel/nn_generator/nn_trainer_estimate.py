import os
import multiprocessing as mp
import numpy as np
import pandas as pd
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator.nn_settings import nn_delay, target_parameters, warmup_period
from cea.demand.metamodel.nn_generator.input_matrix import get_cea_inputs
from cea.demand.metamodel.nn_generator.nn_trainer_resume import nn_model_collector
import cea.inputlocator
import cea.globalvar
import cea.config


def get_nn_estimations(model, scalerT, scalerX, urban_input_matrix, locator):
    input_NN_x = urban_input_matrix
    inputs_x = scalerX.transform(input_NN_x)  # TODO: change scalerX.fit_transform to scalerX.transform

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
    overrides_path = locator.get_building_overrides()
    # TODO: try remove
    # os.remove(overrides_path)

    # file_path_inputs = os.path.join(test_sample_path, "input_predict.csv")
    # urban_input_matrix = np.asarray(pd.read_csv(file_path_inputs))
    #
    # return urban_input_matrix


def prep_NN_delay_estimate(raw_nn_inputs_D, raw_nn_inputs_S, nn_delay):
    '''
        this function adds a time-delay to the inputs
        :param raw_nn_inputs_D: hourly building properties with dynamic characteristics throughout the year,
                these parameters require delay (e.g. climatic parameters, internal gains)
        :param raw_nn_inputs_S: houtly building properties with static characteristics throughout the year,
                these parameters DO NOT require delay (e.g. geometry characteristic, thermal characteristics of the envelope)
        :param raw_nn_targets: hourly demand data (targets)
        :param nn_delay: number of intended delays (can be accessed from 'nn_settings.py')
        :return: array of hourly input and target values for a single building associated with delay (NN_input_ready, NN_target_ready)
        '''
    input1 = raw_nn_inputs_D
    #   input matrix shape
    nS, nF = input1.shape
    #   delay correction (python starts with 0 not 1), therefore, assiging 1 as the time-step delay results in two delays [0,1]
    nD = nn_delay - 1
    #   delay +1
    aD = nD + 1
    #   delay +2
    rD = aD + 1
    #   number of samples +1
    rS = nS + 1
    #   target size
    nT = len(target_parameters)
    #   create an empty matrix to be later filled with input features
    input_matrix_features = np.zeros((rS + nD, rD * nF))
    #   create an empty matrix to be later filled with input features
    input_matrix_targets = np.zeros((rS + nD, rD * nT))

    #   insert delay into the input and target matrices
    i = 1
    while i < rD + 1:
        j = i - 1
        aS = nS + j
        m1 = (i * nF) - (nF)
        m2 = (i * nF)
        input_matrix_features[j:aS, m1:m2] = input1
        i = i + 1

    # remove extra rows
    trimmed_inputn = input_matrix_features[aD:nS, :]
    trimmed_inputt = input_matrix_targets[aD:nS, nT:]
    #   extract the correct slice from the inputs
    trimmed_input_S = raw_nn_inputs_S[aD:aS, :]
    #   merge all input features
    NN_input_ready = np.concatenate([trimmed_inputn, trimmed_inputt, trimmed_input_S], axis=1)

    return NN_input_ready


def input_estimate_prepare_multi_processing(building_name, gv, locator):
    '''
    this function gathers the final inputs and targets
    :param building_name: the intended building name from the list of buildings
    :param gv: global variables
    :param locator: points to the variables
    :param target_parameters: a list containing the name of desirable outputs(can be accessed from 'nn_settings.py')
    :return: array of final hourly input and target matrices for a single building (NN_input_ready, NN_target_ready)
    '''

    #   collect inputs from the input reader function
    raw_nn_inputs_D, raw_nn_inputs_S = get_cea_inputs(locator, building_name, gv)
    #   pass the inputs and targets for delay incorporation
    NN_input_ready = prep_NN_delay_estimate(raw_nn_inputs_D, raw_nn_inputs_S, nn_delay)

    return NN_input_ready


def input_prepare_estimate(list_building_names, locator, gv):
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
        job = pool.apply_async(input_estimate_prepare_multi_processing,
                               [building_name, gv, locator])
        joblist.append(job)
    # run the input/target preperation for all buildings in the list (here called jobs)
    for i, job in enumerate(joblist):
        NN_input_ready = job.get(240)
        #   remove buildings that have "NaN" in their input (e.g. if heating/cooling is off, the indoor temperature
        #   will be returned as "NaN"). Afterwards, stack the inputs/targets of all buildings
        check_nan = 1 * (np.isnan(np.sum(NN_input_ready)))
        if check_nan == 0:
            if i == 0:
                urban_input_matrix = NN_input_ready
            else:
                urban_input_matrix = np.concatenate((urban_input_matrix, NN_input_ready))

    # close the multiprocessing
    pool.close()

    model, scalerT, scalerX = nn_model_collector(locator)

    # reshape file to get a tensor of buildings, features, time.
    num_buildings = len(list_building_names)
    num_features = len(urban_input_matrix[0])
    num_outputs = len(target_parameters)
    matrix = np.empty([num_buildings, 8759+warmup_period, num_outputs])
    reshaped_input_matrix = urban_input_matrix.reshape(num_buildings, 8759, num_features)

    # including warm up period
    warmup_period_input_matrix = reshaped_input_matrix[:,(8759-warmup_period):,:]
    concat_input_matrix = np.hstack((warmup_period_input_matrix, reshaped_input_matrix))

    for i in range(8759+warmup_period):
        one_hour_step = concat_input_matrix[:, i, :]
        inputs_x = scalerX.transform(one_hour_step)

        model_estimates = model.predict(inputs_x)
        matrix[:, i, :] = scalerT.inverse_transform(model_estimates)

    # lets save:
    for i, name in enumerate(list_building_names):
        vector = matrix[i][warmup_period-1:, :].T
        dict_to_dataframe = dict(zip(target_parameters, vector ))
        pd.DataFrame(dict_to_dataframe).to_csv(locator.get_result_building_NN(name), float_format='%.3f')

    print "done"

    return

def main(config):
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    input_prepare_estimate(list_building_names, locator, gv)


if __name__ == '__main__':
    main(cea.config.Configuration())
