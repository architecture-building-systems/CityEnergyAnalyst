from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.calibration.settings import subset_generations
from cea.demand.calibration.settings import subset_threshold
import cea.inputlocator as inputlocator
import cea
import os
import cea.globalvar
from keras.models import model_from_json
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np


__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Testing"


def subset_engine (locator, variables, building_name, building_load,
                   subset_threshold,subset_generations) :
    estimated_loads=nn_estimator(subset_generations)

def nn_estimator(subset_generations) :
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    json_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.json" % locals())
    weight_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_cl.h5" % locals())

    # load json and create model
    json_file = open(json_NN_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    perceptron_ht = model_from_json(loaded_model_json)

    # load weights into new model
    perceptron_ht.load_weights(weight_NN_path)
    print("model loaded")

    # predict new outputs and estimate the error
    test_NN_input_path = os.path.join(locator.get_calibration_folder(), "test_NN_input.csv" % locals())
    test_NN_target_path = os.path.join(locator.get_calibration_folder(), "test_NN_target.csv" % locals())
    input_NN_x=np.array(pd.read_csv(test_NN_input_path))
    target_NN_t=np.array(pd.read_csv(test_NN_target_path))
    perceptron_ht.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

    scalerX = MinMaxScaler(feature_range=(0, 1))
    inputs_x=scalerX.fit_transform(input_NN_x)
    scalerT = MinMaxScaler(feature_range=(0, 1))
    targets_t=scalerT.fit_transform(target_NN_t)

    predict_NN_ht = perceptron_ht.predict(inputs_x)
    filtered_predict = scalerT.inverse_transform(predict_NN_ht)

    filter_logic=np.isin(targets_t, 0)
    target_anomalies=np.asarray(np.where(filter_logic),dtype=np.int)
    t_anomalies_rows, t_anomalies_cols=target_anomalies.shape
    anomalies_replacements=np.zeros(t_anomalies_cols)
    filtered_predict[target_anomalies,0]=anomalies_replacements
    estimated_loads=filtered_predict

    return estimated_loads

def subset_sampler(design):
    rows_design, cols_design = design.shape
    i=0
    while i<rows_design:
        temp_sample=design[i,:]
        



    huy=1
    min_cv_rmse = 1
    while min_cv_rmse < subset_threshold:
        simon_and_garfunkel=1

    return list_of_samples

def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    variables = ['U_win', 'U_wall', 'n50', 'Ths_set_C', 'Cm_Af']
    variables = ['U_win', 'U_wall', 'n50', 'Ths_set_C', 'Cm_Af']
    building_name = 'B155066'
    building_load = 'Qhsf_kWh'
    res_mbe, res_cvRMSE = subset_engine(locator, variables, building_name, building_load)



    return res_mbe, res_cvRMSE

if __name__ == '__main__':
    run_as_script()