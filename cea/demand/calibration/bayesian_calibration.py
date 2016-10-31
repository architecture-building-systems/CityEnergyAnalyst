"""
===========================
Bayesian calibration routine
##check this for timeseries calculation https://arxiv.org/abs/1206.5015
##https: // www.ncbi.nlm.nih.gov / pubmed / 10985202
#http://www.map.ox.ac.uk/media/PDF/Patil_et_al_2010.pdf
===========================
J. Fonseca  script development          27.10.16


"""
from __future__ import division

import pandas as pd
import pymc3 as pm
import numpy as np
import scipy.stats as stats
import scipy.optimize as opt

from cea.demand import demand_main

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calibration_main(locator, gv, group_var, building_name, building_load, weather_path):

    #import arguments of probability density functions (PDF) of variables and create priors:
    pdf_arg = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1) for group in group_var]).set_index('name')
    var_names = pdf_arg.index

    #import measured data for building and building load:
    obs_data = pd.read_csv(locator.get_demand_results_file(building_name))[building_load]

    with pm.Model() as building_demand_model:

        # get priors for the input variables of the model assuming they are all uniform
        priors = [pm.Uniform(name, lower=a, upper=b) for name, a, b in zip(var_names, pdf_arg['min'].values, pdf_arg['max'].values)]
        print priors

        # get priors for the model inaquacy and the measurement errors.
        phi = pm.Uniform('phi', lower=0, upper=10)
        err = pm.Uniform('err', lower=0, upper=10)

        print phi
        # expected value of outcome
        mu = pm.Deterministic(demand_calculation(gv, locator, weather_path, building_load, phi, err, var_names, priors)

        # Likelihood (sampling distribution) of observations
        y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed=obs_data)


    with building_demand_model:
        #call NUTS - MCMC process:
        mu, sds, elbo = pm.variational.advi(n=100000)
        step = pm.NUTS(scaling = building_demand_model.dict_to_array(sds)**2,is_cov=True)
        trace = pm.sample(2000, step, start = mu, progressbar=True)

    return

def demand_calculation(gv, locator, weather_path, building_load, phi, err, var_names, priors):
    gv.samples = dict((x, y) for x, y in zip(var_names, priors))
    print gv.samples
    result = demand_main.demand_calculation(locator, weather_path, gv)[building_load]*(1+ phi + err)  # simulation
    return result

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    group_var = ['THERMAL']
    building_name = 'B01'
    building_load = 'Qhsf_kWh'
    weather_path = locator.get_default_weather()
    calibration_main(locator, gv, group_var, building_name, building_load,weather_path )

if __name__ == '__main__':
    run_as_script()