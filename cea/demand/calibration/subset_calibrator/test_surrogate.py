from keras.models import model_from_json
import os
import cea.inputlocator as inputlocator
import cea.globalvar
import cea
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from math import sqrt
from sklearn.preprocessing import MinMaxScaler


def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    json_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.json" % locals())
    weight_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.h5" % locals())

    # load json and create model
    json_file = open(json_NN_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    perceptron_ht = model_from_json(loaded_model_json)

    # load weights into new model
    perceptron_ht.load_weights(weight_NN_path)

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


    final_target = pd.DataFrame(target_NN_t)
    final_output = pd.DataFrame(filtered_predict)
    save_target_path = os.path.join(locator.get_calibration_folder(), "saved_targets.csv" % locals())
    save_output_path = os.path.join(locator.get_calibration_folder(), "saved_outputs.csv" % locals())
    final_target.to_csv(save_target_path, index=False, header=False, float_format='%.3f', decimal='.')
    final_output.to_csv(save_output_path, index=False, header=False, float_format='%.3f', decimal='.')

    rmse = sqrt(mean_squared_error(target_NN_t[:,0], filtered_predict[:,0]))
    mean_target=np.mean(target_NN_t[:,0])
    cv_rmse=np.divide(rmse,mean_target)

    print (rmse , cv_rmse)

if __name__ == '__main__':
    run_as_script()