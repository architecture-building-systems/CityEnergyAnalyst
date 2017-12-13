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
from sklearn import preprocessing

import numpy as np
import pickle
import time
#import seaborn as sns
import matplotlib.pyplot as plt
import cea.globalvar
import cea.inputlocator

import cea.demand.calibration.settings

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Adam Rysanek"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calibration_main(locator, config):

    # INITIALIZE TIMER
    t0 = time.clock()

    # Local variables
    building_name = config.single_calibration.building
    building_load = config.single_calibration.load
    with open(locator.get_calibration_problem(building_name, building_load),'r') as input_file:
        problem = pickle.load(input_file)
    emulator = joblib.load(locator.get_calibration_gaussian_emulator(building_name, building_load))
    distributions = problem['probabiltiy_vars']
    variables = problem['variables']

    # Create function to call predictions
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def predict_y(var1, var2, var3, var4, var5):
        input_sample = np.array([var1,var2,var3, var4, var5]).reshape(1, -1)
        prediction = emulator.predict(input_sample)
        return prediction

    # Create function to call predictions
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def predict_sigma(var1, var2, var3, var4, var5):
        input_sample = np.array([var1,var2,var3, var4, var5]).reshape(1, -1)
        _, sigma = emulator.predict(input_sample, return_std=True)
        return sigma

    with pm.Model() as basic_model:

        # DECLARE PRIORS
        var1 = pm.Uniform('var1', lower=0, upper=1)
        var2 = pm.Uniform('var2', lower=0, upper=1)
        var3 = pm.Uniform('var3', lower=0, upper=1)
        var4 = pm.Uniform('var4', lower=0, upper=1)
        var5 = pm.Uniform('var5', lower=0, upper=1)

        # DECLARE OBJECTIVE FUNCTION
        mu = pm.Deterministic('mu', predict_y(var1, var2, var3, var4, var5))
        sigma = pm.Deterministic('sigma', predict_sigma(var1, var2, var3, var4, var5))
        y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed = 0)

        # SAVE TO DISC AND SHOW GRAPH
        with basic_model:
            step = pm.Metropolis()
            trace = pm.sample(10000, tune=1000, step=step)
            pm.backends.text.dump(locator.get_calibration_folder(), trace)
            pm.traceplot(trace)
            plt.show()
    return

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    calibration_main(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
