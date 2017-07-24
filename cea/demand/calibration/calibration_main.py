"""
===========================
Bayesian calibration routine

based on work of (Patil_et_al, 2010 - #http://www.map.ox.ac.uk/media/PDF/Patil_et_al_2010.pdf) in MCMC in pyMC3
and the works of bayesian calibration of (Kennedy and O'Hagan, 2001)
===========================
J. Fonseca  script development          27.10.16


"""

from __future__ import division

import pymc3 as pm
import os
from pymc3.backends import SQLite
import theano.tensor as tt
from theano import as_op
from sklearn.externals import joblib

import numpy as np
import pickle
#import seaborn as sns
import matplotlib.pyplot as plt
import cea.globalvar
import cea.inputlocator


from cea.demand.calibration.settings import max_iter_MCMC, generate_plots, burn_in


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Adam Rysanek"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calibration_main(locator, problem, emulator, building_name):

    # get variables from problem
    pdf_list = problem['probabiltiy_vars']
    variables = problem['variables']
    building_load = problem['building_load']

    # create function of cea demand and send to theano
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def calc_result_emulator_and_bias(var1, var2, var3, var4, var5):
        prediction = np.empty(1000)
        prediction[0] = emulator.predict([[var1,var2,var3, var4, var5]])
        calc_result_emulator_and_bias.grad = lambda *x: x[0]
        return prediction

    def calc_observed_synthetic():
        observed_synthetic = np.random.uniform(0,0.30,1000)
        return observed_synthetic

    # create bayesian calibration model in PYMC3
    with pm.Model() as basic_model:
        # add all priors of selected varialbles to the model and assign a triangular distribution
        # for this we create a global variable out of the strings included in the list variables
        vars = []
        for i, variable in enumerate(variables):
            distribution = pdf_list.loc[variable, 'distribution']
            min = pdf_list.loc[variable, 'min']
            max = pdf_list.loc[variable, 'max']
            mu = pdf_list.loc[variable, 'mu']
            if distribution == 'triangular':
                loc = min
                scale = max - min
                c = (mu - min) / (max - min)
                globals()['var' + str(i + 1)] = pm.Triangular('var' + str(i + 1), lower=loc, c=c, upper=scale)
            vars.append('var'+str(i+1))

        # expected value of outcome
        mu = pm.Deterministic('mu', calc_result_emulator_and_bias(var1, var2, var3, var4, var5))

        # Likelihood (sampling distribution) of observations
        sigma = pm.HalfNormal('sigma', sd=0.05)
        observed = calc_observed_synthetic()
        y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed = observed)

    if generate_plots:
        with basic_model:
            # plot posteriors
            trace = pm.backends.text.load(os.path.join(locator.get_calibration_folder()))
            pm.traceplot(trace)
            plt.show()
    else:
        with basic_model:
            step = pm.Metropolis()
            trace = pm.sample(max_iter_MCMC, tune=burn_in, step=step)
            pm.backends.text.dump(locator.get_calibration_folder(), trace)
    return

def run_as_script():
    import cea.inputlocator as inputlocator
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)

    # based on the variables listed in the uncertainty database and selected
    # through a screeing process. they need to be 5.
    building_name = 'B01'
    problem = pickle.load(file(locator.get_calibration_problem(building_name)))
    emulator = joblib.load(locator.get_calibration_gaussian_emulator(building_name))
    calibration_main(locator, problem, emulator, building_name)

if __name__ == '__main__':
    run_as_script()
