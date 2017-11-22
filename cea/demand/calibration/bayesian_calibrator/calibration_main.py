"""
===========================
Bayesian calibration routine

based on work of (Patil_et_al, 2010 - #http://www.map.ox.ac.uk/media/PDF/Patil_et_al_2010.pdf) in MCMC in pyMC3
and the works of bayesian calibration of (Kennedy and O'Hagan, 2001)
===========================
J. Fonseca  script development          27.10.16


"""

from __future__ import division

import pymc3
import os
from pymc3.backends import SQLite
import theano.tensor as tt
from theano import as_op
from sklearn.externals import joblib
from sklearn import preprocessing

import numpy as np
import pickle
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

def calibration_main(locator, problem, emulator):

    # get variables from problem
    pdf_list = problem['probabiltiy_vars']
    variables = problem['variables']

    # introduce the scaler used in the gaussian process and applied in the new variables

    # create function of cea demand and send to theano
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])
    def calc_result_emulator_and_bias(var1, var2, var3, var4, var5):

        # now witdhdraw the results from the emulator
        prediction = emulator.predict([var1,var2,var3, var4, var5])
        #calc_result_emulator_and_bias.grad = lambda *x: x[0]
        return prediction

    def calc_observed_synthetic():
        observed_synthetic = np.random.uniform(0,0.30,100)
        return observed_synthetic

    # create bayesian calibration model in PYMC3
    with pymc3.Model() as basic_model:
        # add all priors of selected varialbles to the model and assign a triangular distribution
        # for this we create a global variable out of the strings included in the list variables
        vars = []
        for i, variable in enumerate(variables):
            distribution = pdf_list.loc[variable, 'distribution']
            min = pdf_list.loc[variable, 'min']
            max = pdf_list.loc[variable, 'max']
            mu = pdf_list.loc[variable, 'mu']
            stdv = pdf_list.loc[variable, 'stdv']

            # normalization [0,1]
            arguments = [min, max, mu, stdv]
            min_max_scaler = preprocessing.MinMaxScaler(copy=True, feature_range=(0, 1))
            arguments_norm = min_max_scaler.fit_transform(arguments)
            min = arguments_norm[0]
            max = arguments_norm[1]
            mu = arguments_norm[2]
            stdv = arguments_norm[3]
            if distribution == 'triangular':
                loc = min
                scale = max - min
                c = (mu - min) / (max - min)
                globals()['var' + str(i + 1)] = pymc3.Triangular('var' + str(i + 1), lower=loc, c=c, upper=max)
            elif distribution == 'normal':
                globals()['var' + str(i + 1)] = pymc3.Normal('var' + str(i + 1), mu=mu, sd=stdv)
            else:  # assume it is uniform
                globals()['var' + str(i + 1)] = pymc3.Uniform('var' + str(i + 1), lower=min, upper=max)

            vars.append('var'+str(i+1))

        # expected value of outcome
        mu = pymc3.Deterministic('mu', calc_result_emulator_and_bias(var1, var2, var3, var4, var5))

        # Likelihood (sampling distribution) of observations
        sigma = pymc3.HalfNormal('sigma', sd=0.10)
        observed = calc_observed_synthetic()
        y_obs = pymc3.Normal('y_obs', mu=mu, sd=sigma, observed = 0)

    if cea.demand.calibration.settings.generate_plots:
        with basic_model:
            # plot posteriors
            trace = pymc3.backends.text.load(os.path.join(locator.get_calibration_folder()))
            pymc3.traceplot(trace)
            plt.show()
    else:
        with basic_model:
            step = pymc3.Metropolis()
            trace = pymc3.sample(cea.demand.calibration.settings.max_iter_MCMC,
                              tune=cea.demand.calibration.settings.burn_in, step=step)
            pymc3.backends.text.dump(locator.get_calibration_folder(), trace)
            pymc3.traceplot(trace)
            plt.show()
    return

def run_as_script():
    import cea.inputlocator as inputlocator
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario=scenario_path)

    # based on the variables listed in the uncertainty database and selected
    # through a screeing process. they need to be 5.
    building_name = 'B01'
    problem = pickle.load(open(locator.get_calibration_problem(building_name)))
    emulator = joblib.load(locator.get_calibration_gaussian_emulator(building_name))
    calibration_main(locator, problem, emulator)

if __name__ == '__main__':
    run_as_script()
