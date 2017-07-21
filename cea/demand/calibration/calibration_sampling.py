import pandas as pd
from scipy.stats import triang
from scipy.stats import norm
from scipy.stats import uniform
from pyDOE import lhs
import cea
import numpy as np
from cea.demand import demand_main
from geopandas import GeoDataFrame as Gdf
import json

from cea.demand.calibration.settings import number_samples
import cea.inputlocator as inputlocator

def simulate_demand_sample(locator, building_name, output_parameters):
    """
    Run a demand simulation for a single sample. This function expects a locator that is already initialized to the
    simulation folder, that has already been prepared with `apply_sample_parameters`.

    :param locator: The InputLocator to use for the simulation
    :type locator: InputLocator

    :param weather: The path to the weather file (``*.epw``) to use for simulation. See the `weather_path` parameter in
                    `cea.demand.demand_main.demand_calculation` for more information.
    :type weather: str

    :param output_parameters: The list of output parameters to save to disk. This is a column-wise subset of the
                              output of `cea.demand.demand_main.demand_calculation`.
    :type output_parameters: list of str

    :return: Returns the columns of the results of `cea.demand.demand_main.demand_calculation` as defined in
            `output_parameters`.
    :rtype: pandas.DataFrame
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
    cv_rmse = calc_cv_rmse(time_series_simulation[output_parameters].values, time_series_measured[output_parameters].values)

    return cv_rmse

def calc_cv_rmse(prediction, target):
    """
    This function calculates the covariance of the root square mean error between two vectors.
    :param prediction: vector of predicted/simulated data
    :param target: vector of target/measured data
    :return:
        float (0..1)
    """
    delta = (prediction - target)**2
    mean = target.mean()
    sum_delta = delta.sum()
    n = len(prediction)
    CVrmse = np.sqrt((sum_delta/n))/mean
    return CVrmse


def latin_sampler(locator, num_samples, variables, variable_groups = ('ENVELOPE', 'INDOOR_COMFORT', 'INTERNAL_LOADS')):


    # get probability density function PDF of variables of interest
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

    return design

def sampling_main(locator, variables, building_name, building_load):

    # create list of samples with a LHC sampler and save to disk
    samples = latin_sampler(locator, number_samples, variables)
    np.save(locator.get_calibration_samples(building_name), samples)

    # create problem and save to disk as json
    problem = {'variables':variables, 'building_name':building_name,
               'building_load':building_load}
    json.dump(problem, file(locator.get_calibration_problem(building_name),'w'))

    cv_rmse_list = []
    for i in range(number_samples):

        #create list of tubles with variables and sample
        sample = zip(variables,samples[i,:])

        #create overrides and return pointer to files
        apply_sample_parameters(locator, sample)

        # run cea demand and calculate cv_rmse
        cv_rmse = simulate_demand_sample(locator, building_name, building_load)
        cv_rmse_list.append(cv_rmse)
        print "The cv_rmse for this iteration is:", cv_rmse

    json.dump({'cv_rmse':cv_rmse_list}, file(locator.get_calibration_cvrmse_file(building_name), 'w'))


def apply_sample_parameters(locator, sample):
    """
    Copy the scenario from the `scenario_path` to the `simulation_path`. Patch the parameters from
    the problem statement. Return an `InputLocator` implementation that can be used to simulate the demand
    of the resulting scenario.

    The `simulation_path` is modified by the demand calculation. For the purposes of the sensitivity analysis, these
    changes can be viewed as temporary and deleted / overwritten after each simulation.

    :param sample_index: zero-based index into the samples list, which is read from the file `$samples_path/samples.npy`
    :type sample_index: int

    :param samples_path: path to the pre-calculated samples and problem statement (created by
                        `sensitivity_demand_samples.py`)
    :type samples_path: str

    :param scenario_path: path to the scenario template
    :type scenario_path: str

    :param simulation_path: a (temporary) path for simulating a scenario that has been patched with a sample
                            NOTE: When simulating in parallel, special care must be taken that each process has
                            a unique `simulation_path` value. For the Euler cluster, this is solved by ensuring the
                            simulation is done with `gv.multiprocessing = False` and setting the `simulation_path` to
                            the special folder `$TMPDIR` that is set to a local scratch folder for each job by the
                            job scheduler of the Euler cluster. Other setups will need to adopt an equivalent strategy.
    :type simulation_path: str

    :return: InputLocator that can be used to simulate the demand in the `simulation_path`
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
    building_load = 'Ef_kWh'
    sampling_main(locator, variables, building_name, building_load)

if __name__ == '__main__':
    run_as_script()