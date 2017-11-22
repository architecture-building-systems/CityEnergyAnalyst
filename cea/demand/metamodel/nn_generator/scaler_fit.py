import os
import cea
import numpy as np
import pandas as pd
from cea.demand.metamodel.nn_generator.nn_settings import number_samples_scaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.externals import joblib

def range_collector(locator,counter):
    '''
    This function finds the right file and sends it back to the range_finder function.
    :param locator:
    :param counter:
    :return:
    '''
    nn_inout_path = locator.get_nn_inout_folder()
    i=counter
    scaler_inout_path = locator.get_minmaxscaler_folder()
    file_path_inputs = os.path.join(scaler_inout_path, "input%(i)s.csv" % locals())
    file_path_targets = os.path.join(scaler_inout_path, "target%(i)s.csv" % locals())
    urban_input_matrix = np.asarray(pd.read_csv(file_path_inputs))
    urban_taget_matrix = np.asarray(pd.read_csv(file_path_targets))

    inputs_max=np.amax(urban_input_matrix,axis=0)
    targets_max=np.amax(urban_taget_matrix,axis=0)

    inputs_min = np.amin(urban_input_matrix, axis=0)
    targets_min = np.amin(urban_taget_matrix, axis=0)

    return inputs_max, targets_max, inputs_min, targets_min


def range_finder(locator):
    '''
    This function collects the randomly sampled inputs and targets and finds the maximum and minimum value
    for each colum of the inputs and targets.
    :param locator:
    :return:
    '''
    counter=0
    inputs_max, targets_max, inputs_min, targets_min = range_collector(locator, counter)
    columns_input_max=inputs_max.shape
    columns_target_max=targets_max.shape

    columns=int(columns_input_max[0])+int(columns_target_max[0])
    range_matrix_max = np.empty([number_samples_scaler,columns])
    range_matrix_min = np.empty([number_samples_scaler, columns])
    inputs_scaler_max = np.empty([number_samples_scaler,columns_input_max[0]])
    inputs_scaler_min = np.empty([number_samples_scaler,columns_input_max[0]])
    targets_scaler_max = np.empty([number_samples_scaler,columns_target_max[0]])
    targets_scaler_min = np.empty([number_samples_scaler,columns_target_max[0]])


    for counter in range(number_samples_scaler):
        inputs_max, targets_max, inputs_min, targets_min=range_collector(locator,counter)
        all_params=np.concatenate((inputs_max, targets_max))
        range_matrix_max[counter,:] = all_params
        all_params = np.concatenate((inputs_min, targets_min))
        range_matrix_min[counter,:] = all_params
        range_matrix_min = np.empty([number_samples_scaler, columns])
        inputs_scaler_max[counter,:] = inputs_max
        inputs_scaler_min[counter,:] = inputs_min
        targets_scaler_max[counter,:] = targets_max
        targets_scaler_min[counter,:] = targets_min
        print(counter)

    nn_inout_path = locator.get_nn_inout_folder()
    file_path_inputs = os.path.join(nn_inout_path, "ranges_max.csv")
    range_matrix=pd.DataFrame(range_matrix_max)
    range_matrix.to_csv(file_path_inputs,header=False,index=False)

    file_path_inputs = os.path.join(nn_inout_path, "ranges_min.csv")
    range_matrix = pd.DataFrame(range_matrix_min)
    range_matrix.to_csv(file_path_inputs, header=False, index=False)

    xscaler_max = np.amin(inputs_scaler_max, axis=0)
    xscaler_min = np.amin(inputs_scaler_min, axis=0)
    tscaler_max = np.amin(targets_scaler_max, axis=0)
    tscaler_min = np.amin(targets_scaler_min, axis=0)

    xscaler_array = np.stack((xscaler_max,xscaler_min))
    tscaler_array = np.stack((tscaler_max, tscaler_min))

    # scaling and normalizing inputs
    scalerX = MinMaxScaler(feature_range=(0, 1))
    scalerX.fit(xscaler_array)
    scalerT = MinMaxScaler(feature_range=(0, 1))
    scalerT.fit(tscaler_array)


    scalerX_file, scalerT_file = locator.get_minmaxscalar_model()
    joblib.dump(scalerX, scalerX_file)
    joblib.dump(scalerT, scalerT_file)
    print("scalers saved")

def run_as_script():
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    range_finder(locator)

if __name__ == '__main__':
    run_as_script()