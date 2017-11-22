import cea
import os
import pandas as pd
import numpy as np
import pickle
from scipy.stats import triang
from scipy.stats import norm
from scipy.stats import uniform
from pyDOE import lhs
from cea.demand import demand_main
from geopandas import GeoDataFrame as Gdf
import cea.inputlocator as inputlocator
from cea.demand.calibration.settings import number_samples
from keras.layers import Input, Dense
from keras.models import Model
import scipy.io
from keras.models import Sequential
from keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler


__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Testing"

all_results=[]
def simulate_demand_sample(locator, building_name, output_parameters):
    """
    This script runs the cea demand tool in series and returns a single value of cvrmse and rmse.

    :param locator: pointer to location of files in CEA
    :param building_name: name of building
    :param output_parameters: building load to consider in the anlysis
    :return:
    """

    # force simulation to be sequential and to only do one building
    gv = cea.globalvar.GlobalVariables()
    gv.multiprocessing = False
    gv.print_totals = False
    gv.simulate_building_list = [building_name]
    gv.testing = True

    #import weather and measured data
    weather_path = locator.get_default_weather()
    #weather_path = 'C:\CEAforArcGIS\cea\databases\weather\Zurich.epw'

    #calculate demand timeseries for buidling an calculate cvrms
    demand_main.demand_calculation(locator, weather_path, gv)
    output_folder=locator.get_demand_results_folder()
    file_path=os.path.join(output_folder, "%(building_name)s.xls" % locals())
    #file_path=locator.get_demand_results_file(building_name)

    new_calcs = pd.read_excel(file_path)

    #cv_rmse, rmse = calc_cv_rmse(time_series_simulation[output_parameters].values, time_series_measured[output_parameters].values)

    return  new_calcs #cv_rmse, rmse

def latin_sampler(locator, num_samples, variables):
    """
    This script creates a matrix of m x n samples using the latin hypercube sampler.
    for this, it uses the database of probability distribtutions stored in locator.get_uncertainty_db()

    :param locator: pointer to locator of files of CEA
    :param num_samples: number of samples to do
    :param variables: list of variables to sample
    :return:
        1. design: a matrix m x n with the samples
        2. pdf_list: a dataframe with properties of the probability density functions used in the excercise.
    """


    # get probability density function PDF of variables of interest
    variable_groups = ('ENVELOPE', 'INDOOR_COMFORT', 'INTERNAL_LOADS')
    database = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1)
                                                for group in variable_groups])
    pdf_list = database[database['name'].isin(variables)].set_index('name')

    # get number of variables
    num_vars = pdf_list.shape[0] #alternatively use len(variables)

    # get design of experiments
    design = lhs(num_vars, samples=num_samples)
    for i, variable in enumerate(variables):
        distribution = pdf_list.loc[variable, 'distribution']
        min = pdf_list.loc[variable,'min']
        max = pdf_list.loc[variable,'max']
        mu = pdf_list.loc[variable,'mu']
        stdv = pdf_list.loc[variable,'stdv']
        if distribution == 'triangular':
            loc = min
            scale = max - min
            c = (mu - min) / (max - min)
            design[:, i] = triang(loc=loc, c=c, scale=scale).ppf(design[:, i])
        elif distribution == 'normal':
            design[:, i] = norm(loc=mu, scale=stdv).ppf(design[:, i])
        else: # assume it is uniform
            design[:, i] = uniform(loc=min, scale=max).ppf(design[:, i])

    return design, pdf_list

def prep_NN_inputs(NN_input,NN_target,NN_delays):
    #NN_input.to_csv('TEMP.csv', index=False, header=False, float_format='%.3f', decimal='.')
    #file_path_temp = 'C:\CEAforArcGIS\cea\surrogate\Temp.csv'
    #input1 = pd.read_csv(file_path_temp)
    input1=NN_input
    target1=NN_target
    nS, nF = input1.shape
    nSS, nT = target1.shape
    nD=NN_delays
    aD=nD+1
    input_matrix_features=np.zeros((nS+nD, aD*nF))
    rowsF, colsF=input_matrix_features.shape
    input_matrix_targets=np.zeros((nS+nD, aD*nT))
    rowsFF, ColsFF = input_matrix_targets.shape

    i=1
    while i<aD+1:
        j=i-1
        aS=nS+j
        m1=(i*nF)-(nF)
        m2=(i*nF)
        n1=(i*nT)-(nT)
        n2=(i*nT)
        input_matrix_features[j:aS, m1:m2]=input1
        input_matrix_targets[j:aS, n1:n2]=target1
        i=i+1

    trimmed_inputn = input_matrix_features[nD:nS,:]
    trimmed_inputt = input_matrix_targets[nD:nS, 2:]
    NN_input_ready=np.concatenate([trimmed_inputn, trimmed_inputt], axis=1)
    NN_target_ready=target1[nD:nS,:]

    return NN_input_ready, NN_target_ready

def sampling_main(locator, variables, building_name, building_load):
    """
    This script creates samples using a lating Hypercube sample of 5 variables of interest.
    then runs the demand calculation of CEA for all the samples. It delivers a json file storing
    the results of cv_rmse and rmse for each sample.

    for more details on the work behind this please check:
    Rysanek A., Fonseca A., Schlueter, A. Bayesian calibration of Dyanmic building Energy Models. Applied Energy 2017.

    :param locator: pointer to location of CEA files
    :param variables: input variables of CEA to sample. They must be 5!
    :param building_name: name of building to calibrate
    :param building_load: name of building load to calibrate
    :return:
        1. a file storing values of cv_rmse and rmse for all samples. the file is sotred in
        file(locator.get_calibration_cvrmse_file(building_name)

        2 a file storing information about variables, the building_load and the probability distribtuions used in the
          excercise. the file is stored in locator.get_calibration_problem(building_name)
    :rtype: .json and .pkl
    """

    # create list of samples with a LHC sampler and save to disk
    samples, pdf_list = latin_sampler(locator, number_samples, variables)
    np.save(locator.get_calibration_samples(building_name), samples)

    # create problem and save to disk as json
    problem = {'variables':variables,
               'building_load':building_load, 'probabiltiy_vars':pdf_list}
    pickle.dump(problem, file(locator.get_calibration_problem(building_name), 'w'))

    nn_X_ht = []
    nn_X_cl = []
    nn_T_ht = []
    nn_T_cl = []
    nn_X_ht = np.array(nn_X_ht)
    nn_X_cl = np.array(nn_X_cl)
    nn_T_ht = np.array(nn_T_ht)
    nn_T_cl = np.array(nn_T_cl)

    for i in range(number_samples):

        #create list of tubles with variables and sample
        sample = zip(variables,samples[i,:])

        #create overrides and return pointer to files
        apply_sample_parameters(locator, sample)
        simulate_demand_sample(locator, building_name, building_load)
        # define the inputs
        intended_parameters=['people','Eaf','Elf','Qwwf','I_rad','I_sol','T_ext','rh_ext',
        'ta_hs_set','ta_cs_set','theta_a','Qhsf', 'Qcsf']
        # collect the simulation results
        file_path = os.path.join(locator.get_demand_results_folder(), "%(building_name)s.xls" % locals())
        calcs_outputs_xls = pd.read_excel(file_path)
        temp_file=os.path.join(locator.get_temporary_folder(), "%(building_name)s.csv" % locals())
        calcs_outputs_xls.to_csv(temp_file, index=False, header=True, float_format='%.3f', decimal='.')
        calcs_trimmed_csv=pd.read_csv(temp_file, usecols=intended_parameters)
        calcs_trimmed_csv['I_real'] = calcs_trimmed_csv['I_rad'] + calcs_trimmed_csv['I_sol']
        calcs_trimmed_csv['ta_hs_set'].fillna(0, inplace=True)
        calcs_trimmed_csv['ta_cs_set'].fillna(50, inplace=True)
        NN_input=calcs_trimmed_csv
        input_drops = ['I_rad', 'I_sol', 'theta_a', 'Qhsf', 'Qcsf']
        NN_input = NN_input.drop(input_drops, 1)



        NN_input=np.array(NN_input)
        target1=calcs_trimmed_csv['Qhsf']
        target2=calcs_trimmed_csv['Qcsf']
        target3=calcs_trimmed_csv['theta_a']
        NN_target_ht = pd.concat([target1, target3], axis=1)
        NN_target_cl = pd.concat([target2, target3], axis=1)
        NN_target_ht=np.array(NN_target_ht)
        NN_target_cl=np.array(NN_target_cl)


        #return NN_input, NN_target_ht, NN_target_cl

        NN_delays=1
        NN_input_ready_ht, NN_target_ready_ht=prep_NN_inputs(NN_input, NN_target_ht, NN_delays)
        NN_input_ready_cl, NN_target_ready_cl = prep_NN_inputs(NN_input, NN_target_cl, NN_delays)

        one_array_override=np.array(pd.read_csv(locator.get_building_overrides(),skiprows=1,nrows=1))
        one_array_override1=np.delete(one_array_override,0,1)
        rows_override, cols_override=one_array_override1.shape
        rows_NN_input, cols_NN_input=NN_input_ready_ht.shape
        random_variables_matrix=[]
        random_variables_matrix=np.array(random_variables_matrix)
        vector_of_ones = np.ones((rows_NN_input, 1))


        for k in range (0,cols_override):
            random_variable_call=one_array_override1[0,k]
            random_variable_col=np.multiply(random_variable_call,vector_of_ones)
            if k<1:
                random_variables_matrix=random_variable_col
            else:
                random_variables_matrix=np.append(random_variables_matrix,random_variable_col,axis=1)


        combined_inputs_ht=np.concatenate((NN_input_ready_ht,random_variables_matrix),axis=1)
        combined_inputs_cl=np.concatenate((NN_input_ready_cl, random_variables_matrix), axis=1)

        if i<1:
            nn_X_ht=combined_inputs_ht
            nn_X_cl=combined_inputs_cl
            nn_T_ht=NN_target_ready_ht
            nn_T_cl=NN_target_ready_cl
        else:
            nn_X_ht = np.concatenate((nn_X_ht,combined_inputs_ht), axis=0)
            nn_X_cl = np.concatenate((nn_X_cl,combined_inputs_cl), axis=0)
            nn_T_ht = np.concatenate((nn_T_ht, NN_target_ready_ht), axis=0)
            nn_T_cl = np.concatenate((nn_T_cl, NN_target_ready_cl), axis=0)





    sampled_input_ht = pd.DataFrame(nn_X_ht)
    #sampled_input_cl = pd.DataFrame(nn_X_cl)
    sampled_target_ht = pd.DataFrame(nn_T_ht)
    #sampled_target_cl = pd.DataFrame(nn_T_cl)

    test_NN_input_path = os.path.join(locator.get_calibration_folder(), "test_NN_input.csv" % locals())
    sampled_input_ht.to_csv(test_NN_input_path, index=False, header=False, float_format='%.3f', decimal='.')
    test_NN_target_path = os.path.join(locator.get_calibration_folder(), "test_NN_target.csv" % locals())
    sampled_target_ht.to_csv(test_NN_target_path, index=False, header=False, float_format='%.3f', decimal='.')

    #sampled_input_ht.to_csv('in_ht.csv', index=False, header=False, float_format='%.3f', decimal='.')
    #sampled_input_cl.to_csv('in_cl.csv', index=False, header=False, float_format='%.3f', decimal='.')
    #sampled_target_ht.to_csv('tar_ht.csv', index=False, header=False, float_format='%.3f', decimal='.')
    #sampled_target_cl.to_csv('tar_cl.csv', index=False, header=False, float_format='%.3f', decimal='.')

    # heating perceptron
    model=neural_trainer(nn_X_ht, nn_T_ht,locator)
    # serialize model to JSON
    json_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.json" % locals())
    weight_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_ht.h5" % locals())
    model_json = model.to_json()
    with open(json_NN_path, "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights(weight_NN_path)
    print(r"Saved model to ~reference-case-open\baseline\outputs\data\calibration")
    #out_NN = pd.DataFrame(filtered_outputs_t)
    #out_NN_path = os.path.join(locator.get_calibration_folder(), "%(building_name)s-netout_ht.csv" % locals())
    #out_NN.to_csv(out_NN_path, index=False, header=False, float_format='%.3f', decimal='.')

    # cooling perceptron
    model = neural_trainer(nn_X_cl, nn_T_cl,locator)
    # serialize model to JSON
    json_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_cl.json" % locals())
    weight_NN_path = os.path.join(locator.get_calibration_folder(), "trained_network_cl.h5" % locals())
    model_json = model.to_json()
    with open(json_NN_path, "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights(weight_NN_path)
    print(r"Saved model to ~reference-case-open\baseline\outputs\data\calibration")
    #out_NN = pd.DataFrame(filtered_outputs_t)
    #out_NN_path = os.path.join(locator.get_calibration_folder(), "%(building_name)s-netout_cl.csv" % locals())
    #out_NN.to_csv(out_NN_path, index=False, header=False, float_format='%.3f', decimal='.')

def neural_trainer(inputs_x,targets_t,locator):
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

    ## predict ourputs
    #outputs_t = model.predict(inputs_x)
    #filtered_outputs_t = scalerT.inverse_transform(outputs_t)

    #filter_logic=np.isin(targets_t, 0)
    #target_anomalies=np.asarray(np.where(filter_logic),dtype=np.int)
    #t_anomalies_rows, t_anomalies_cols=target_anomalies.shape
    #anomalies_replacements=np.zeros(t_anomalies_cols)
    #filtered_outputs_t[target_anomalies,0]=anomalies_replacements

    return model

def apply_sample_parameters(locator, sample):
    """
    This script structures samples in a format that can be read by a case study in cea.

    :param locator: pointer to location of CEA files
    :param sample: array with values of m variables to modify in the input databases of CEA
    :return: file with variables to overwrite in cea and stored in locator.get_building_overrides()
    """

    # make overides
    prop = Gdf.from_file(locator.get_zone_geometry()).set_index('Name')
    prop_overrides = pd.DataFrame(index=prop.index)
    for (variable, value) in sample:
        print("Setting prop_overrides['%s'] to %s" % (variable, value))
        prop_overrides[variable] = value
    prop_overrides.to_csv(locator.get_building_overrides())

def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario=scenario_path)

    # based on the variables listed in the uncertainty database and selected
    # through a screening process. they need to be 5.
    variables = ['U_win', 'U_wall', 'n50', 'Ths_set_C', 'Cm_Af'] #uncertain variables
    building_name = 'B155066' # intended building
    building_load = 'Qhsf_kWh' # target of prediction
    sampling_main(locator, variables, building_name, building_load)


if __name__ == '__main__':
    run_as_script()