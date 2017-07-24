from __future__ import division
import pandas as pd
from scipy.stats import triang
from scipy.stats import norm
from scipy.stats import uniform
from pyDOE import lhs
import cea
import numpy as np
from cea.demand import demand_main
from geopandas import GeoDataFrame as Gdf
import pickle
import json

from cea.demand.calibration.settings import number_samples
import cea.inputlocator as inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

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

    #import weather and measured data
    weather_path = locator.get_default_weather()
    time_series_measured = pd.read_csv(locator.get_demand_measured_file(building_name), usecols=[output_parameters])

    #calculate demand timeseries for buidling an calculate cvrms
    demand_main.demand_calculation(locator, weather_path, gv)
    time_series_simulation = pd.read_csv(locator.get_demand_results_file(building_name), usecols=[output_parameters])
    cv_rmse, rmse = calc_cv_rmse(time_series_simulation[output_parameters].values, time_series_measured[output_parameters].values)

    return cv_rmse, rmse

def calc_cv_rmse(prediction, target):
    """
    This function calculates the covariance of the root square mean error between two vectors.
    :param prediction: vector of predicted/simulated data
    :param target: vector of target/measured data
    :return:
        CVrmse: float
        rmse: float
    """
    delta = (prediction - target)**2
    mean = target.mean()
    sum_delta = delta.sum()
    n = len(prediction)
    rmse = np.sqrt((sum_delta/n))
    CVrmse = rmse/mean
    return round(CVrmse,3), round(rmse,3) #keep only 3 significant digits


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

    cv_rmse_list = []
    rmse_list = []
    for i in range(number_samples):

        #create list of tubles with variables and sample
        sample = zip(variables,samples[i,:])

        #create overrides and return pointer to files
        apply_sample_parameters(locator, sample)

        # run cea demand and calculate cv_rmse
        cv_rmse, rmse = simulate_demand_sample(locator, building_name, building_load)
        cv_rmse_list.append(cv_rmse)
        rmse_list.append(rmse)
        print "The cv_rmse for this iteration is:", cv_rmse

    json.dump({'cv_rmse':cv_rmse_list, 'rmse':rmse_list}, file(locator.get_calibration_cvrmse_file(building_name), 'w'))


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
    locator = inputlocator.InputLocator(scenario_path=scenario_path)

    # based on the variables listed in the uncertainty database and selected
    # through a screening process. they need to be 5.
    variables = ['U_win', 'U_wall', 'Ths_setb_C', 'Ths_set_C', 'Cm_Af']
    building_name = 'B01'
    building_load = 'Qhsf_kWh'
    sampling_main(locator, variables, building_name, building_load)

if __name__ == '__main__':
    run_as_script()