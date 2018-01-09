import os
import cea.config
import cea.inputlocator
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.layers import Input, Dense
from keras.models import Model
import os
from keras.models import Sequential
from keras.callbacks import EarlyStopping
from sklearn.externals import joblib

def normalized_inputs(locator):

    # importing the input and output features from the saved folder using locator
    file_path_inputs = os.path.join(locator.get_optimization_nn_inout_folder(), "input_data_total.csv")
    inputs = pd.DataFrame.from_csv(file_path_inputs)
    # filtering the inputs to remove the inputs with negative costs, CO2 and prim values
    inputs = inputs[inputs.CO2 >= 0]
    inputs = inputs[inputs.costs >= 0]
    inputs = inputs[inputs.prim >= 0]
    # reindexing to avoid missing indices due to the above step
    inputs.index = range(len(inputs))
    # splitting the inputs under 'individual' which is a big string, into individual components
    # split_individual = inputs['individual'][0]
    # split_individual = split_individual.split(',')
    # initiating the dataframe with column names as feature_0, feature_1 and so on
    # column_names = []
    # for i in range(len(split_individual)):
    #     column_names.append('feature_' + str(i))
    # input_features = pd.DataFrame(columns=column_names)

    input_features = inputs[['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5', 'feature_6',
                             'feature_7', 'feature_8', 'feature_9', 'feature_10', 'feature_11', 'feature_12', 'feature_13',
                             'feature_14', 'feature_15', 'feature_16', 'feature_17', 'feature_18', 'feature_19', 'feature_20',
                             'feature_21', 'feature_22', 'feature_23', 'feature_24', 'feature_25', 'feature_26',
                             'feature_27', 'feature_28', 'feature_29', 'feature_30', 'feature_31', 'feature_32',
                             'feature_33', 'feature_34', 'feature_35', 'feature_36', 'feature_37', 'feature_38',
                             'feature_39', 'feature_40', 'feature_41', 'feature_42', 'feature_43', 'feature_44']]

    # # updating the dataframe with the individuals from the inputs
    # for i in range(len(inputs)):
    #     split_individual = inputs['individual'][i]
    #     print (split_individual)
    #
    #     # a
    #     # b = a.replace(" ", "")
    #     # c = b.split()
    #     # d = c[0]
    #     # e = d.replace("[", "")
    #     # f = e.replace("]", "")
    #     # g = f.split("#")
    #     # h = g[0].split(',')
    #
    #     for i in range(len(split_individual)):
    #         split_individual[i] = float(split_individual[i])
    #     print (split_individual)
    #     input_features.loc[i] = float(split_individual)

    # creating target features dataframe
    target_features = inputs[['costs', 'CO2', 'prim']]

    # calculating min and max of each feature of the dataframe corresponding to inputs and targets
    inputs_max = np.amax(input_features, axis=0)
    inputs_min = np.amin(input_features, axis=0)

    targets_max = np.amax(target_features, axis=0)
    targets_min = np.amin(target_features, axis=0)

    print (inputs_max)
    print (inputs_min)
    print (targets_max)
    print (targets_min)
    # input_scaled = []
    # # for feature_name in input_features.columns:
    # #     max_value = input_features[feature_name].max()
    # #     min_value = input_features[feature_name].min()
    # #     print (input_features[feature_name].values)
    # #     input_scaled[feature_name] = (input_features[feature_name].values - min_value) / (max_value - min_value)
    # #     print (input_scaled)
    #
    # print (input_scaled)
    input_scaled = input_features.values
    target_scaled = target_features.values  # returns a numpy array
    min_max_scaler = MinMaxScaler()
    input_scaled = min_max_scaler.fit_transform(input_scaled)
    input_scaled = pd.DataFrame(input_scaled)
    target_scaled = min_max_scaler.fit_transform(target_scaled)
    target_scaled = pd.DataFrame(target_scaled)
    print (target_scaled)
    print (input_scaled)
    print (1)

    encoded_x_rows, encoded_x_cols = input_scaled.shape
    targets_t_rows, targets_t_cols = target_scaled.shape
    hidden_units_L1 = int(encoded_x_cols * 1.1)
    hidden_units_L2 = int(encoded_x_cols * 1.1)
    hidden_units_L3 = int(encoded_x_cols * 1.1)
    hidden_units_L4 = int(encoded_x_cols * 1.1)
    hidden_units_L5 = int(encoded_x_cols * 1.1)
    hidden_units_L6 = int(encoded_x_cols * 1.1)
    hidden_units_L7 = int(encoded_x_cols + 1)
    validation_split = 0.5
    e_stop_limit = 10

    # multi-layer perceptron: here we start the training for the first time
    model = Sequential()

    model.add(Dense(hidden_units_L1, input_dim=encoded_x_cols, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L2, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L3, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L4, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L5, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L6, activation='relu'))  # logistic layer

    model.add(Dense(hidden_units_L7, activation='relu'))  # logistic layer

    model.add(Dense(targets_t_cols, activation='linear'))  # output layer

    model.compile(loss='mean_squared_error', optimizer='Adamax')  # compile the network

    #   define early stopping to avoid overfitting
    estop = EarlyStopping(monitor='val_loss', min_delta=0, patience=e_stop_limit, verbose=1, mode='auto')

    #   Fit the model
    model.fit(input_scaled, target_scaled, validation_split=validation_split, epochs=5000, shuffle=True, batch_size=100000,
              callbacks=[estop])

    json_NN_path, weight_NN_path = locator.get_optimization_neural_network_model()
    model_json = model.to_json()
    with open(json_NN_path, "w") as json_file:
        json_file.write(model_json)
    # serialize weights based on model structure
    model.save_weights(weight_NN_path)
    print("neural network properties saved")
    #   save resume-enables model
    print("neural network model saved")

def main(config):

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    normalized_inputs(locator)

if __name__ == '__main__':
    main(cea.config.Configuration())