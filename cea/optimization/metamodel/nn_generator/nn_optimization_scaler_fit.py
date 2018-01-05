import os
import cea.config
import cea.inputlocator
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.externals import joblib

def normalized_inputs(locator):

    # importing the input and output features from the saved folder using locator
    file_path_inputs = os.path.join(locator.get_optimization_nn_inout_folder(), "input_data_home_1_2000.csv")
    inputs = pd.DataFrame.from_csv(file_path_inputs)
    # filtering the inputs to remove the inputs with negative costs, CO2 and prim values
    inputs = inputs[inputs.CO2 >= 0]
    inputs = inputs[inputs.costs >= 0]
    inputs = inputs[inputs.prim >= 0]
    # reindexing to avoid missing indices due to the above step
    inputs.index = range(len(inputs))
    # splitting the inputs under 'individual' which is a big string, into individual components
    split_individual = inputs['individual'][0]
    split_individual = split_individual.split(',')
    # initiating the dataframe with column names as feature_0, feature_1 and so on
    column_names = []
    for i in range(len(split_individual)):
        column_names.append('feature_' + str(i))
    input_features = pd.DataFrame(columns=column_names)

    # updating the dataframe with the individuals from the inputs
    for i in range(len(inputs)):
        split_individual = inputs['individual'][i]
        print (split_individual)

        # a
        # b = a.replace(" ", "")
        # c = b.split()
        # d = c[0]
        # e = d.replace("[", "")
        # f = e.replace("]", "")
        # g = f.split("#")
        # h = g[0].split(',')

        for i in range(len(split_individual)):
            split_individual[i] = float(split_individual[i])
        print (split_individual)
        input_features.loc[i] = float(split_individual)

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
    input_scaled = []
    for feature_name in input_features.columns:
        max_value = input_features[feature_name].max()
        min_value = input_features[feature_name].min()
        input_scaled[feature_name] = (input_features[feature_name] - min_value) / (max_value - min_value)

    print (input_scaled)
    target_scaled = target_features.values  # returns a numpy array
    min_max_scaler = MinMaxScaler()
    target_scaled = min_max_scaler.fit_transform(target_scaled)
    target_scaled = pd.DataFrame(target_scaled)
    print (target_scaled)


def main(config):

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    normalized_inputs(locator)

if __name__ == '__main__':
    main(cea.config.Configuration())