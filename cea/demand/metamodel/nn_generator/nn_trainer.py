# coding=utf-8
"""
'nn_trainer.py' script fits a neural net on inputs and targets
"""

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from sklearn.externals import joblib
import numpy as np
import pandas as pd
from keras.layers import Input, Dense
from keras.models import Model
import os
from keras.models import Sequential
from keras.callbacks import EarlyStopping
import cea
from cea.demand.metamodel.nn_generator.nn_settings import number_samples
from cea.demand.metamodel.nn_generator.nn_settings import autoencoder
import cea.inputlocator
import cea.config


def neural_trainer(inputs_x, targets_t, locator, scalerX, scalerT, autoencoder):
    '''
    This function executes the training if the NN
    :param inputs_x:
    :param targets_t:
    :param locator:
    :return:
    '''

    inputs_x_rows, inputs_x_cols = inputs_x.shape
    # scaling and normalizing inputs
    inputs_x = scalerX.transform(inputs_x)
    targets_t = scalerT.transform(targets_t)

    encoding_dim = int(np.ceil(inputs_x_cols / 2) + np.ceil(inputs_x_cols * 0.1))
    over_complete_dim = int(encoding_dim * 2)
    AE_input_dim = int(inputs_x_cols)

    if autoencoder:
        # sparsing inputs: this option is recommended if you have more than 50 input features
        input_AEI = Input(shape=(AE_input_dim,))
        encoded = Dense(over_complete_dim, activation='relu')(input_AEI)
        encoded = Dense(encoding_dim, activation='softplus')(encoded)

        decoded = Dense(over_complete_dim, activation='softplus')(encoded)
        decoded = Dense(inputs_x_cols, activation='relu')(decoded)

        autoencoder = Model(input_AEI, decoded)
        autoencoder.compile(optimizer='Adamax', loss='mse')
        autoencoder.fit(inputs_x,inputs_x,epochs=1000, batch_size= 100000, shuffle=True)
        encoder = Model(input_AEI, encoded)
        encoded_x=encoder.predict(inputs_x)
        inputs_x=encoded_x

    encoded_x_rows, encoded_x_cols = inputs_x.shape
    targets_t_rows, targets_t_cols = targets_t.shape
    hidden_units_L1 = int(encoded_x_cols * 1.1)
    hidden_units_L2 = int(encoded_x_cols + 1)
    validation_split = 0.5
    e_stop_limit = 10

    # multi-layer perceptron: here we start the training for the first time
    model = Sequential()

    model.add(Dense(hidden_units_L1, input_dim=encoded_x_cols, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L2, activation='relu'))  # logistic layer

    model.add(Dense(targets_t_cols, activation='linear'))  # output layer

    model.compile(loss='mean_squared_error', optimizer='Adamax')  # compile the network

    #   define early stopping to avoid overfitting
    estop = EarlyStopping(monitor='val_loss', min_delta=0, patience=e_stop_limit, verbose=1, mode='auto')

    #   Fit the model
    model.fit(inputs_x, targets_t, validation_split=validation_split, epochs=10, shuffle=True, batch_size=100000,
              callbacks=[estop])
    #   save model structure
    json_NN_path, weight_NN_path = locator.get_neural_network_model()
    model_json = model.to_json()
    with open(json_NN_path, "w") as json_file:
        json_file.write(model_json)
    # serialize weights based on model structure
    model.save_weights(weight_NN_path)
    print("neural network properties saved")
    #   save resume-enables model
    model_resume = locator.get_neural_network_resume()
    model.save(model_resume)  # creates a HDF5 file 'model_resume.h5'
    print("neural network model saved")

    del inputs_x
    del targets_t
    del model


def nn_input_collector(locator):
    nn_inout_path = locator.get_nn_inout_folder()
    for i in range(number_samples):
        file_path_inputs = os.path.join(nn_inout_path, "input%(i)s.csv" % locals())
        file_path_targets = os.path.join(nn_inout_path, "target%(i)s.csv" % locals())
        batch_input_matrix = np.asarray(pd.read_csv(file_path_inputs))
        batch_taget_matrix = np.asarray(pd.read_csv(file_path_targets))
        if i < 1:
            urban_input_matrix = batch_input_matrix
            urban_taget_matrix = batch_taget_matrix
        else:
            urban_input_matrix = np.concatenate((urban_input_matrix, batch_input_matrix), axis=0)
            urban_taget_matrix = np.concatenate((urban_taget_matrix, batch_taget_matrix), axis=0)

        print(i)

    return urban_input_matrix, urban_taget_matrix


def main(config):

    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)

    urban_input_matrix, urban_taget_matrix = nn_input_collector(locator)
    scalerX_file, scalerT_file = locator.get_minmaxscalar_model()
    scalerX = joblib.load(scalerX_file)
    scalerT = joblib.load(scalerT_file)
    neural_trainer(urban_input_matrix, urban_taget_matrix, locator, scalerX, scalerT, autoencoder)


if __name__ == '__main__':
    main(cea.config.Configuration())
