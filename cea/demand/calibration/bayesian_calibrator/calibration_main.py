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
import seaborn as sns
import theano.tensor as tt
from theano import as_op
from sklearn.externals import joblib
from sklearn import preprocessing

import numpy as np
import pickle
import time
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

    with pm.Model() as basic_model:

        # DECLARE PRIORS
        for i, variable in enumerate(variables):
            arguments = np.array([distributions.loc[variable, 'min'], distributions.loc[variable, 'max'],
                                  distributions.loc[variable, 'mu']]).reshape(-1, 1)
            min_max_scaler = preprocessing.MinMaxScaler(copy=True, feature_range=(0, 1))
            arguments_norm = min_max_scaler.fit_transform(arguments)
            globals()['var' + str(i + 1)] = pm.Triangular('var' + str(i + 1), lower=arguments_norm[0][0],
                                                          c=arguments_norm[1][0],
                                                          upper=arguments_norm[2][0])

        # DECLARE OBJECTIVE FUNCTION
        mu = pm.Deterministic('mu', predict_y(var1, var2, var3, var4, var5, var6))
        sigma = pm.HalfNormal('sigma', 0.15)
        # sigma = pm.Deterministic('sigma', predict_sigma(var1, var2, var3, var4, var5, var6))
        y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed=0)

        # RUN MODEL, SAVE TO DISC AND PLOT RESULTS
        with basic_model:
            # Running
            step = pm.Metropolis()
            trace = pm.sample(10000, tune=1000, step=step)
            # Saving
            df_trace = pm.trace_to_dataframe(trace)

            #CREATE GRAPHS AND SAVE TO DISC
            df_trace.to_csv(locator.get_calibration_posteriors(building_name, building_load))
            pm.traceplot(trace)

            columns = ["var1", "var2", "var3", "var4", "var5", "var6"]
            sns.pairplot(df_trace[columns])

            if config.single_calibration.show_plots:
                plt.show()


    #SAVING POSTERIORS IN PROBLEM
    problem['posterior_norm'] = df_trace.as_matrix(columns=columns)
    pickle.dump(problem, open(locator.get_calibration_problem(building_name, building_load), 'w'))

    return

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    calibration_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
