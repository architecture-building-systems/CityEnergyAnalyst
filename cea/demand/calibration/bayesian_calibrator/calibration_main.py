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
# import seaborn as sns
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
    with open(locator.get_calibration_problem(building_name, building_load), 'r') as input_file:
        problem = pickle.load(input_file)
    emulator = joblib.load(locator.get_calibration_gaussian_emulator(building_name, building_load))
    distributions = problem['probabiltiy_vars']
    variables = problem['variables']

    # Create function to call predictions (mu)
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def predict_y(var1, var2, var3, var4, var5, var6):
        input_sample = np.array([var1, var2, var3, var4, var5, var6]).reshape(1, -1)
        prediction = emulator.predict(input_sample)
        return prediction

    # Create function to call predictions (sigma)
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def predict_sigma(var1, var2, var3, var4, var5, var6):
        input_sample = np.array([var1, var2, var3, var4, var5, var6]).reshape(1, -1)
        _, sigma = emulator.predict(input_sample, return_std=True)
        return sigma

    # crete function to retrieve distributions
    for i, variable in enumerate(variables):
        # normalization [0,1]
        arguments = np.array([distributions.loc[variable, 'min'], distributions.loc[variable, 'max'],
                              distributions.loc[variable, 'mu']]).reshape(-1, 1)
        min_max_scaler = preprocessing.MinMaxScaler(copy=True, feature_range=(0, 1))
        arguments_norm = min_max_scaler.fit_transform(arguments)
        globals()['var' + str(i + 1) + '_min'] = arguments_norm[0]
        globals()['var' + str(i + 1) + '_max'] = arguments_norm[1]
        globals()['var' + str(i + 1) + '_mu'] = arguments_norm[2]

    # create observed data (to comply with limit of 0.30 of ashrae or less)
    observed = np.random.uniform(0, 0.30, 100)

    with pm.Model() as basic_model:
        # DECLARE PRIORS
        var1 = pm.Triangular('var1', lower=var1_min[0], c=var1_mu[0], upper=var1_max[0])
        var2 = pm.Triangular('var2', lower=var2_min[0], c=var2_mu[0], upper=var2_max[0])
        var3 = pm.Triangular('var3', lower=var3_min[0], c=var3_mu[0], upper=var3_max[0])
        var4 = pm.Triangular('var4', lower=var4_min[0], c=var4_mu[0], upper=var4_max[0])
        var5 = pm.Triangular('var5', lower=var5_min[0], c=var5_mu[0], upper=var5_max[0])
        var6 = pm.Triangular('var6', lower=var6_min[0], c=var6_mu[0], upper=var6_max[0])

        # DECLARE OBJECTIVE FUNCTION
        mu = pm.Deterministic('mu', predict_y(var1, var2, var3, var4, var5, var6))
        sigma = pm.Deterministic('sigma', predict_sigma(var1, var2, var3, var4, var5, var6))
        y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed=observed)

        # RUN MODEL, SAVE TO DISC AND PLOT RESULTS
        with basic_model:
            # Running
            step = pm.Metropolis()
            trace = pm.sample(10000, tune=500, step=step)
            # Saving
            pm.backends.text.dump(locator.get_calibration_folder(), trace)
            # tracing plots
            pm.traceplot(trace)
            pm.plots.plot_posterior(trace)
            plt.show()
    return


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    calibration_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
