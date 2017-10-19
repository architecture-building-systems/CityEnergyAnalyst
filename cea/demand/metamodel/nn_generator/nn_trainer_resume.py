

from sklearn.externals import joblib
import numpy as np
from keras.layers import Input, Dense

from keras.models import Model

from keras.models import load_model
from keras.callbacks import EarlyStopping
import cea

import theano
import multiprocessing
from cea.demand.metamodel.nn_generator.nn_trainer import nn_input_collector
from cea.demand.metamodel.nn_generator.nn_settings import autoencoder


def neural_trainer_resume(inputs_x, targets_t, model, scalerX, scalerT, locator, autoencoder):
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
    encoding_dim = int(np.ceil(inputs_x_cols/2)+np.ceil(inputs_x_cols * 0.1))
    over_complete_dim =int(encoding_dim*2)
    AE_input_dim=int(inputs_x_cols)

    if autoencoder:
        # sparsing inputs: use this if you have more than 50 input features
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

    validation_split = 0.3
    e_stop_limit = 10

    # define early stopping to avoid overfitting
    estop = EarlyStopping(monitor='val_loss', min_delta=0, patience=e_stop_limit, verbose=1, mode='auto')

    # Fit the model
    model.fit(inputs_x, targets_t, validation_split=validation_split, epochs=10, shuffle=True, batch_size=100000,
              callbacks=[estop])

    json_NN_path, weight_NN_path = locator.get_neural_network_model()
    model_json = model.to_json()
    with open(json_NN_path, "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights(weight_NN_path)
    print("neural network properties saved")

    model_resume = locator.get_neural_network_resume()
    model.save(model_resume)  # creates a HDF5 file 'model_resume.h5'
    print("neural network model saved")

    del inputs_x
    del targets_t
    del model


def nn_model_collector(locator):
    # locate the saved neural network
    model_resume = locator.get_neural_network_resume()
    # load the model
    model = load_model(model_resume)
    # locate the saved scaler
    scalerX_file, scalerT_file = locator.get_minmaxscalar_model()
    # load scalers
    scalerX = joblib.load(scalerX_file)
    scalerT = joblib.load(scalerT_file)
    return model, scalerT, scalerX


def run_as_script():
    num_cpu_threads = multiprocessing.cpu_count()
    theano.config.openmp = True
    OMP_NUM_THREADS = num_cpu_threads
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    model, scalerT, scalerX = nn_model_collector(locator)

    urban_input_matrix, urban_taget_matrix = nn_input_collector(locator)

    neural_trainer_resume(urban_input_matrix, urban_taget_matrix, model, scalerX, scalerT, locator, autoencoder)


if __name__ == '__main__':
    run_as_script()
