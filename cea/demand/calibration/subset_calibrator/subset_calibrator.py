import os
from math import sqrt

import numpy as np
import pandas as pd
from keras.models import model_from_json
from pyDOE import lhs
from scipy.stats.distributions import uniform
from sklearn.metrics import mean_squared_error
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import MinMaxScaler

import cea
import cea.globalvar
import cea.inputlocator as inputlocator

__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Testing"


def gmm_random_sampler(filtered_samples,lhs_samples):

    gmm = GaussianMixture(1, covariance_type='full')
    gmm.fit(filtered_samples)
    design = gmm.sample(n_samples=lhs_samples)
    return design

def neural_output_generator(nn_X_ht,scalerX,perceptron_ht,scalerT,nn_T_ht,avg_cluster_measured):
    rows_X_ht, cols_X_ht = nn_X_ht.shape
    nn_X_ht_h = nn_X_ht
    predictor_counter=0
    while predictor_counter < rows_X_ht:
        inputs_x = scalerX.transform(nn_X_ht_h)
        predict_NN_ht = perceptron_ht.predict(inputs_x)
        filtered_predict = scalerT.inverse_transform(predict_NN_ht)
        target_filter_node = nn_T_ht[:, 0]
        filter_logic = np.isin(target_filter_node, 0)
        target_anomalies = np.asarray(np.where(filter_logic), dtype=np.int)
        t_anomalies_rows, t_anomalies_cols = target_anomalies.shape
        anomalies_replacements = np.zeros(t_anomalies_cols)
        anomalies_replacements = np.transpose(anomalies_replacements)
        filtered_predict[target_anomalies, 0] = anomalies_replacements
        replace_temp_vect=filtered_predict[predictor_counter, :]
        if predictor_counter < rows_X_ht-1:
            nn_X_ht_h[predictor_counter+1,18:20]=replace_temp_vect
        avg_cluster_single = np.average(avg_cluster_measured)
        trim_avg_cluster = avg_cluster_measured[1:24]
        main_filtered_predict = filtered_predict[:, 0]
        predictor_counter=predictor_counter+1

    second_anomalies=np.asarray(np.where(main_filtered_predict<0), dtype=np.int)
    sec_anomalies_rows, sec_anomalies_cols = second_anomalies.shape
    if sec_anomalies_cols > 0:
        sec_anomalies_replacements = np.zeros(sec_anomalies_cols)
        sec_anomalies_replacements = np.transpose(sec_anomalies_replacements)
        #second_anomalies = pd.DataFrame(second_anomalies)
        #second_anomalies = np.array(second_anomalies.ix[:,:])
        second_anomalies=np.squeeze(second_anomalies)
        main_filtered_predict[second_anomalies] = sec_anomalies_replacements
    CV_RMSE = np.divide((sqrt(mean_squared_error(trim_avg_cluster, main_filtered_predict))), avg_cluster_single)

    return CV_RMSE


def ss_loop(design, lhs_samples, NN_input_ready_ht,scalerX,perceptron_ht,scalerT,nn_T_ht,avg_cluster_measured):
    CV_RMSE_mat=np.empty([lhs_samples,1])
    for loop_count in range(lhs_samples):
        test_vector=design[loop_count,:]
        test_vector=np.repeat(test_vector,23)
        test_vector=np.reshape(test_vector,(5,23))
        test_vector=np.transpose(test_vector)
        old_replace_Ths=max(NN_input_ready_ht[:,7])
        new_replace_Ths=test_vector[0,3]
        find_replace1=np.where(NN_input_ready_ht[:,7] == old_replace_Ths)[0]
        find_replace2 = np.where(NN_input_ready_ht[:, 16] == old_replace_Ths)[0]
        NN_input_ready_ht[find_replace1,7]=new_replace_Ths
        NN_input_ready_ht[find_replace2, 16] = new_replace_Ths
        random_combined_inputs = np.concatenate((NN_input_ready_ht, test_vector), axis=1)
        nn_X_ht = random_combined_inputs
        CV_RMSE=neural_output_generator(nn_X_ht,scalerX,perceptron_ht,scalerT,nn_T_ht,avg_cluster_measured)
        CV_RMSE_mat[loop_count,0]=CV_RMSE
    return  CV_RMSE_mat

def ss_calibrator(building_name):

    from cea.analysis.clustering.kmeans.k_means_partitioner import partitioner
    list_median, cluster_labels = partitioner(building_name)
    intended_parameters = ['people', 'Eaf', 'Elf', 'Qwwf', 'I_rad', 'I_sol', 'T_ext', 'rh_ext',
                           'ta_hs_set', 'ta_cs_set', 'theta_a', 'Qhsf', 'Qcsf']
    # collect the simulation results
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    metered_path=r'C:\reference-case-open\baseline\inputs\building-metering'
    metered_building=os.path.join(metered_path, '%s.csv' % building_name)
    ht_cl_el = ['Qhsf']
    measured_data_pd = pd.read_csv(metered_building,usecols=ht_cl_el)
    measured_data = np.array(measured_data_pd)
    test_NN_input_path = os.path.join(locator.get_calibration_folder(), "test_NN_input.csv" % locals())
    test_NN_target_path = os.path.join(locator.get_calibration_folder(), "test_NN_target.csv" % locals())
    input_NN_x = np.array(pd.read_csv(test_NN_input_path))
    target_NN_t = np.array(pd.read_csv(test_NN_target_path))
    json_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.json" % locals())
    weight_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.h5" % locals())

    json_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.json" % locals())
    weight_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.h5" % locals())

    scalerX = MinMaxScaler(feature_range=(0, 1))
    inputs_x=scalerX.fit_transform(input_NN_x)
    scalerT = MinMaxScaler(feature_range=(0, 1))
    targets_t=scalerT.fit_transform(target_NN_t)

    # load json and create model
    json_file = open(json_NN_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    perceptron_ht = model_from_json(loaded_model_json)

    # load weights into new model
    perceptron_ht.load_weights(weight_NN_path)
    perceptron_ht.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    file_path = os.path.join(locator.get_demand_results_folder(), "%(building_name)s.xls" % locals())
    calcs_outputs_xls = pd.read_excel(file_path)
    temp_file = os.path.join(locator.get_temporary_folder(), "%(building_name)s.csv" % locals())
    calcs_outputs_xls.to_csv(temp_file, index=False, header=True, float_format='%.3f', decimal='.')
    calcs_trimmed_csv = pd.read_csv(temp_file, usecols=intended_parameters)
    calcs_trimmed_csv['I_real'] = calcs_trimmed_csv['I_rad'] + calcs_trimmed_csv['I_sol']
    calcs_trimmed_csv['ta_hs_set'].fillna(0, inplace=True)
    calcs_trimmed_csv['ta_cs_set'].fillna(50, inplace=True)
    NN_input = calcs_trimmed_csv
    input_drops = ['I_rad', 'I_sol', 'theta_a', 'Qhsf', 'Qcsf']
    NN_input = NN_input.drop(input_drops, 1)

    NN_input = np.array(NN_input)
    target1 = calcs_trimmed_csv['Qhsf']
    target2 = calcs_trimmed_csv['Qcsf']
    target3 = calcs_trimmed_csv['theta_a']
    NN_target_ht = pd.concat([target1, target3], axis=1)
    NN_target_cl = pd.concat([target2, target3], axis=1)
    NN_target_ht = np.array(NN_target_ht)
    NN_target_cl = np.array(NN_target_cl)

    # return NN_input, NN_target_ht, NN_target_cl
    from cea.demand.calibration.subset_calibrator.surrogate_4_calibration import prep_NN_inputs
    NN_delays = 1
    NN_input_ready_ht, NN_target_ready_ht = prep_NN_inputs(NN_input, NN_target_ht, NN_delays)
    NN_input_ready_cl, NN_target_ready_cl = prep_NN_inputs(NN_input, NN_target_cl, NN_delays)

    one_array_override = np.array(pd.read_csv(locator.get_building_overrides(), skiprows=1, nrows=1))
    one_array_override1 = np.delete(one_array_override, 0, 1)
    rows_override, cols_override = one_array_override1.shape
    rows_NN_input, cols_NN_input = NN_input_ready_ht.shape
    random_variables_matrix = []
    random_variables_matrix = np.array(random_variables_matrix)
    vector_of_ones = np.ones((rows_NN_input, 1))

    for k in range(0, cols_override):
        random_variable_call = one_array_override1[0, k]
        random_variable_col = np.multiply(random_variable_call, vector_of_ones)
        if k < 1:
            random_variables_matrix = random_variable_col
        else:
            random_variables_matrix = np.append(random_variables_matrix, random_variable_col, axis=1)

    combined_inputs_ht = np.concatenate((NN_input_ready_ht, random_variables_matrix), axis=1)
    combined_inputs_cl = np.concatenate((NN_input_ready_cl, random_variables_matrix), axis=1)
    nn_X_ht = combined_inputs_ht
    nn_X_cl = combined_inputs_cl
    nn_T_ht = NN_target_ready_ht
    nn_T_cl = NN_target_ready_cl

    nn_input_rows, nn_input_cols, = NN_input.shape
    reshaped_nn_input=np.reshape(NN_input,(365,24,nn_input_cols))
    reshape_measured_data = np.reshape(measured_data,(365,24))
    reshape_target1 = np.reshape(target1, (365, 24))
    reshape_target2 = np.reshape(target2, (365, 24))
    reshape_target3 = np.reshape(target3, (365, 24))

    first_cluster=cluster_labels[0]

    first_group = np.where(cluster_labels == first_cluster)[0]
    first_mat = reshaped_nn_input[first_group, : , :]
    measured_data_trim = reshape_measured_data [first_group, : ]
    avg_cluster_measured=np.average(measured_data_trim,axis=0)
    target1 = reshape_target1[first_group, :]
    target2 = reshape_target2[first_group, :]
    target3 = reshape_target3[first_group, :]

    nn_input_rows, nn_input_cols, nn_input_tens = first_mat.shape
    #nn_input_rows=list(int(nn_input_rows))
    #second_mat=np.reshape(first_mat,(nn_input_rows*nn_input_cols,nn_input_tens))
    for number_samples in range(nn_input_rows):

        NN_input=first_mat[number_samples]
        NN_input=np.array(NN_input)
        target1a=target1[number_samples]
        target2a=target2[number_samples]
        target3a=target3[number_samples]
        NN_target_ht = np.vstack((target1a, target3a))
        #NN_target_cl = pd.concat([target2, target3], axis=1)
        NN_target_ht=np.array(NN_target_ht)
        NN_target_ht=np.transpose(NN_target_ht)
        #NN_target_cl=np.array(NN_target_cl)
        NN_delays = 1
        NN_input_ready_ht, NN_target_ready_ht = prep_NN_inputs(NN_input, NN_target_ht, NN_delays)
        #NN_input_ready_cl, NN_target_ready_cl = prep_NN_inputs(NN_input, NN_target_cl, NN_delays)
        random_variables_matrix2=random_variables_matrix[0:23,:]
        combined_inputs_ht = np.concatenate((NN_input_ready_ht, random_variables_matrix2), axis=1)
        #combined_inputs_cl = np.concatenate((NN_input_ready_cl, random_variables_matrix), axis=1)
        nn_X_ht = combined_inputs_ht
        #nn_X_cl = combined_inputs_cl
        nn_T_ht = NN_target_ready_ht
        #nn_T_cl = NN_target_ready_cl

        inputs_x = scalerX.transform(nn_X_ht)
        predict_NN_ht = perceptron_ht.predict(inputs_x)
        filtered_predict = scalerT.inverse_transform(predict_NN_ht)
        target_filter_node=NN_target_ready_ht[:,0]
        filter_logic = np.isin(target_filter_node, 0)
        target_anomalies = np.asarray(np.where(filter_logic), dtype=np.int)
        t_anomalies_rows, t_anomalies_cols = target_anomalies.shape
        anomalies_replacements = np.zeros(t_anomalies_cols)
        anomalies_replacements=np.transpose(anomalies_replacements)
        filtered_predict[target_anomalies, 0] = anomalies_replacements
        avg_cluster_single=np.average(avg_cluster_measured)
        trim_avg_cluster=avg_cluster_measured[1:24]
        main_filtered_predict=filtered_predict[:,0]
        CV_RMSE = np.divide((sqrt(mean_squared_error(trim_avg_cluster,main_filtered_predict))),avg_cluster_single)


        ####LHS#
        lhs_samples_num=1000
        #design = gmm_random_sampler(random_variables_matrix2, lhs_samples_num)
        design = lhs(5, samples=lhs_samples_num)
        lower = [0.5*random_variables_matrix2[0,0],0.5 * random_variables_matrix2[0, 1],0.5 * random_variables_matrix2[0, 2],
                 0.5 * random_variables_matrix2[0, 3],0.5 * random_variables_matrix2[0, 4]]
        upper = [1.5*random_variables_matrix2[0,0],1.5 * random_variables_matrix2[0, 1],1.5 * random_variables_matrix2[0, 2],
                 1.5 * random_variables_matrix2[0, 3],1.5 * random_variables_matrix2[0, 4]]
        for i in xrange(4):
            design[:, i] = uniform(loc=lower[i], scale=upper[i]).ppf(design[:, i])

        CV_RMSE_mat = ss_loop(design, lhs_samples_num, NN_input_ready_ht, scalerX, perceptron_ht, scalerT, nn_T_ht, avg_cluster_measured)
        min_CV_RMSE=np.ndarray.min(CV_RMSE_mat)

        counter_while=0
        counter_max=100

        while min_CV_RMSE<0.15 and counter_while<counter_max:
            # momentum_low= 0.9 + ((float(counter_while)/float(counter_max))/float(10))
            # momentum_up = 1.1 - ((float(counter_while) / float(counter_max)) / float(10))
            jumbo_outputs=np.concatenate((CV_RMSE_mat,design),axis=1)
            jumbo_outputs = jumbo_outputs[np.argsort(jumbo_outputs[:, 0])]
            filtered_samples=jumbo_outputs[0:10,:]
            # lower = [momentum_low*np.ndarray.min(filtered_samples[:,1]), momentum_low*np.ndarray.min(filtered_samples[:,2]),
            #          momentum_low*np.ndarray.min(filtered_samples[:,3]),momentum_low *np.ndarray.min(filtered_samples[:, 4]),
            #          momentum_low*np.ndarray.min(filtered_samples[:,5])]
            # upper = [momentum_up*np.ndarray.max(filtered_samples[:,1]),momentum_up*np.ndarray.max(filtered_samples[:,2]),
            #          momentum_up*np.ndarray.max(filtered_samples[:,3]),momentum_up*np.ndarray.max(filtered_samples[:, 4]),
            #          momentum_up*np.ndarray.max(filtered_samples[:,5])]
            # for i in xrange(4):
            #     design = lhs(5, samples=lhs_samples_num)
            #     design[:, i] = uniform(loc=lower[i], scale=upper[i]).ppf(design[:, i])
            gmm_samples_num=100
            gmm_input=filtered_samples[:,1:6]
            design=gmm_random_sampler(gmm_input,gmm_samples_num)
            #design = list(design)
            design = np.array(design[0])
            CV_RMSE_mat = ss_loop(design, gmm_samples_num, NN_input_ready_ht, scalerX, perceptron_ht, scalerT, nn_T_ht,
                                  avg_cluster_measured)
            min_CV_RMSE = np.ndarray.min(CV_RMSE_mat)
            counter_while = counter_while+1

            print (min_CV_RMSE, counter_while)



def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)


    building_name = 'B155066' # intended building
    cluster_labels=ss_calibrator(building_name)


if __name__ == '__main__':
    run_as_script()