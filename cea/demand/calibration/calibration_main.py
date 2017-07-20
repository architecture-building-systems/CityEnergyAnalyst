"""
===========================
Bayesian calibration routine

based on work of (Patil_et_al, 2010 - #http://www.map.ox.ac.uk/media/PDF/Patil_et_al_2010.pdf) in MCMC in pyMC3
and the works of bayesian calibration of (Kennedy and O'Hagan, 2001)
===========================
J. Fonseca  script development          27.10.16


"""

from __future__ import division

import pandas as pd
import pymc3 as pm
import shutil, os
from pymc3.backends import SQLite
import theano.tensor as tt
from theano import as_op
from pymc3.distributions.distribution import Continuous, draw_values, generate_samples
from pymc3.distributions.dist_math import logpow, alltrue
from geopandas import GeoDataFrame as Gdf
from scipy import stats
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import cea.globalvar
import cea.inputlocator

from cea.demand import demand_main
from cea.demand.calibration.cal
from cea.demand.calibration.settings import number_samples


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Adam Rysanek"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calibration_main(gv, locator, weather_path, building_name, variables, building_load, retrieve_results, scenario_path,
                     method, values_index, niter)


    # create demand samples
    samples = sample_demand(locator, number_samples, variables):


    # create function of demand calculation and send to theano
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def demand_calculation(phi, err, var1, var2, var3, var4, var5):

        # create an overrides file which contains changes in the input variables.
        prop_thermal = Gdf.from_file(locator.get_building_thermal()).set_index('Name')
        prop_overrides = pd.DataFrame(index=prop_thermal.index)
        samples = [var1, var2, var3, var4, var5]
        for i, key in enumerate(vars):
            prop_overrides[key] = samples[i]
        prop_overrides.to_csv(locator.get_building_overrides())

        # call CEA demand calculation
        gv.multiprocessing = False # do not use multiprocessing while calculating the demand
        gv.print_totals = False # do not print yearly totals, it saves computational time
        gv.simulate_building_list = [building_name] # just tell CEA to run only this building.
        demand_main.demand_calculation(locator, weather_path, gv)  # simulation
        result = pd.read_csv(locator.get_demand_results_file(building_name), usecols=[building_load]) * (1 + phi + err)

        # get the results for the valid range of indexes
        if method is 'cvrmse':
            out = np.empty(1)
            out[0] = calc_CVrmse(result[building_load].values[values_index], obs_data)
        else:
            out = result[building_load].values[values_index]

        print out, phi, err, var1, var2, var3, var4, var5
        return out

    # copy scenario folder to do overides only there
    simulation_path = locator.get_temporary_folder()+'//'+'test'
    if os.path.exists(simulation_path):
        shutil.rmtree(simulation_path)
    shutil.copytree(scenario_path, simulation_path)
    locator = cea.inputlocator.InputLocator(scenario_path=simulation_path)

    # import arguments of probability density functions (PDF) of variables and create priors:
    pdf = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1) for group in
                     ['THERMAL', 'ARCHITECTURE', 'INDOOR_COMFORT', 'INTERNAL_LOADS']]).set_index('name')

    # import measured data for building and building load:
    obs_data = pd.read_csv(locator.get_demand_measured_file(building_name))[building_load].values[values_index]

    # create bayesian calibration model in PYMC3
    with pm.Model() as basic_model:

        # add all priors of selected varialbles to the model and assign a triangular distribution
        # for this we create a global variable out of the strings included in the list variables
        vars = []
        for i, variable in enumerate(variables):
            lower = pdf.loc[variable, 'min']
            upper = pdf.loc[variable, 'max']
            #c = pdf.locator[variable, 'mu']
            globals()['var'+str(i+1)] = pm.Uniform('var'+str(i+1), lower=lower, upper=upper)
            vars.append('var'+str(i+1))

        # get priors for the model inaquacy and the measurement errors.
        phi = pm.Uniform('phi', lower=0, upper=0.01)
        err = pm.Uniform('err', lower=0, upper=0.02)

        # expected value of outcome
        mu = pm.Deterministic('mu', demand_calculation(phi, err, var1, var2, var3, var4, var5))

        # Likelihood (sampling distribution) of observations
        if method is 'cvrmse':
            sigma = pm.HalfNormal('sigma', sd=0.1)
            y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed = 0.0)
        else:
            y_obs = pm.ZeroInflatedPoisson('y_obs', theta=mu, psi=0.5,  observed=obs_data)

    if retrieve_results:
        with basic_model:
            # plot posteriors
            trace = pm.backends.text.load(locator.get_calibration_folder(niter))
            pm.traceplot(trace)
            plt.show()

        # plot comparison to mean values
        ppc = pm.sample_ppc(trace, samples=500, model=basic_model, size=100)
        ax = plt.subplot()
        sns.distplot([x.mean() for x in ppc['var1']], kde=False, ax=ax)
        ax.axvline(obs_data.mean())
        ax.set(title='Posterior predictive of the mean', xlabel='mean(x)', ylabel='Frequency')
        plt.show()
    else:

        with basic_model:
            step = pm.Metropolis()
            trace = pm.sample(niter, step=step)
            pm.backends.text.dump(locator.get_calibration_folder(niter), trace)
    return


def calc_CVrmse(prediction, target):
    """
    This function calculates the covariance of the root square mean error between two vectors.
    :param prediction: vector of predicted/simulated data
    :param target: vector of target/measured data
    :return:
        float (0..1)
    """
    CVrmse = np.sqrt(((prediction - target) ** 2).mean()) / prediction.mean()
    return CVrmse

def run_as_script():
    import cea.inputlocator as inputlocator
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()

    # based on the variables listed in the uncertainty database and selected
    # through a screeing process. they need to be 5.
    variables = ['U_win', 'U_wall', 'Ths_setb_C', 'Ths_set_C', 'Cm']
    building_name = 'B01'
    building_load = 'Qhsf_kWh'
    values_index = range(0,gv.seasonhours[0])+ range(gv.seasonhours[1],8760) #indexes of timeseries to consider
    retrieve_results = False # flag to retrieve and analyze results from calibration
    method = 'cvrmse' # cvrmse and normal distribution or 'poisson' with an entire timeseries
    calibration_main(gv, locator, weather_path, building_name, variables, building_load, retrieve_results, scenario_path,
                     method, values_index, niter=10000)

if __name__ == '__main__':
    run_as_script()
