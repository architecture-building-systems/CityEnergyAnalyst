from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
from keras.layers import Input, Dense
from keras.models import Model
import scipy.io
import os
from keras.models import Sequential
from keras.callbacks import EarlyStopping
import cea
from cea.demand.calibration.nn_generator.input_prepare import input_prepare_main
from cea.demand.demand_main import properties_and_schedule

def neural_trainer(inputs_x,targets_t,locator):
    '''
    This function executes the training if the NN
    :param inputs_x:
    :param targets_t:
    :param locator:
    :return:
    '''
    np.random.seed(7)
    inputs_x_rows, inputs_x_cols = inputs_x.shape
    #scaling and normalizing inputs
    scalerX = MinMaxScaler(feature_range=(0, 1))
    inputs_x=scalerX.fit_transform(inputs_x)
    scalerT = MinMaxScaler(feature_range=(0, 1))
    targets_t=scalerT.fit_transform(targets_t)
    encoding_dim = int(np.ceil(inputs_x_cols/2)+np.ceil(inputs_x_cols * 0.1))
    over_complete_dim =int(encoding_dim*2)
    AE_input_dim=int(inputs_x_cols)

    #sparsing inputs: use this if you have more than 50 input features
    # input_AEI = Input(shape=(AE_input_dim,))
    # encoded = Dense(over_complete_dim, activation='relu')(input_AEI)
    # encoded = Dense(encoding_dim, activation='softplus')(encoded)
    #
    # decoded = Dense(over_complete_dim, activation='softplus')(encoded)
    # decoded = Dense(inputs_x_cols, activation='relu')(decoded)
    #
    # autoencoder = Model(input_AEI, decoded)
    # autoencoder.compile(optimizer='Adamax', loss='mse')
    # autoencoder.fit(inputs_x,inputs_x,epochs=1000, batch_size= 100000, shuffle=True)
    # encoder = Model(input_AEI, encoded)
    # encoded_input=Input(shape=(encoding_dim,))
    # encoded_x=encoder.predict(inputs_x)
    #print encoded_x

    encoded_x_rows, encoded_x_cols = inputs_x.shape
    targets_t_rows, targets_t_cols = targets_t.shape
    hidden_units_L1=int(encoded_x_cols*1.1)
    hidden_units_L2=int(encoded_x_cols+1)
    validation_split = 0.5
    e_stop_limit=100000

    # multi-layer perceptron
    model = Sequential()
    model.add(Dense(hidden_units_L1, input_dim=encoded_x_cols, activation='relu')) #logistic layer

    model.add(Dense(hidden_units_L2, activation='relu')) #logistic layer

    model.add(Dense(targets_t_cols, activation='linear')) #output layer

    model.compile(loss='mean_squared_error', optimizer='Adamax') # compile the network

    # define early stopping to avoid overfitting
    estop = EarlyStopping(monitor='val_loss', min_delta=0, patience=e_stop_limit, verbose=1, mode='auto')

    # Fit the model
    model.fit(inputs_x, targets_t, validation_split=validation_split, epochs=1500, shuffle=True, batch_size=100000,callbacks=[estop])

    json_NN_path , weight_NN_path = locator.get_neural_network_model()
    model_json = model.to_json()
    with open(json_NN_path, "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights(weight_NN_path)
    print("neural network model saved")

def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    target_parameters = ['Qhsf', 'Qcsf', 'Qwwf', 'Ef', 'T_int']
    urban_input_matrix, urban_taget_matrix=input_prepare_main(list_building_names, locator, target_parameters)
    save_inputs=pd.DataFrame(urban_input_matrix)
    save_targets=pd.DataFrame(urban_taget_matrix)
    temp_file = r'C:\reference-case-open\baseline\outputs\data\calibration\inputs.csv'
    save_inputs.to_csv(temp_file)
    temp_file = r'C:\reference-case-open\baseline\outputs\data\calibration\targets.csv'
    save_targets.to_csv(temp_file)
    neural_trainer(urban_input_matrix, urban_taget_matrix, locator)

if __name__ == '__main__':
    run_as_script()