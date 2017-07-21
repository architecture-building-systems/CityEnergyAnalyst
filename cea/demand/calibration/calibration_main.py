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
from geopandas import GeoDataFrame as Gdf
from scipy import stats
import numpy as np
#import seaborn as sns
import matplotlib.pyplot as plt
import cea.globalvar
import cea.inputlocator
import json

from cea.demand import demand_main
from cea.demand.calibration.settings import max_iter_MCMC



__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Adam Rysanek"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calibration_main(locator, problem, building_name):

    # get variables from problem
    variables = problem.variables
    building_load = problem.building_load

    # create function of cea demand and send to theano
    @as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar, tt.dscalar], otypes=[tt.dvector])

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
        mu = pm.Deterministic('mu', cea_demand(phi, err, var1, var2, var3, var4, var5))

        # Likelihood (sampling distribution) of observations
        if method is 'cvrmse':
            sigma = pm.HalfNormal('sigma', sd=0.1)
            y_obs = pm.Normal('y_obs', mu=mu, sd=sigma, observed = 0.0)
        else:
            y_obs = pm.ZeroInflatedPoisson('y_obs', theta=mu, psi=0.5,  observed=obs_data)

    if retrieve_results:
        with basic_model:
            # plot posteriors
            trace = pm.backends.text.load(locator.get_calibration_folder(max_iter_MCMC))
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
            trace = pm.sample(max_iter_MCMC, step=step)
            pm.backends.text.dump(locator.get_calibration_folder(niter), trace)
    return




def run_as_script():
    import cea.inputlocator as inputlocator
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)

    # based on the variables listed in the uncertainty database and selected
    # through a screeing process. they need to be 5.
    building_name = 'B01'
    problem = json.load(locator.get_calibration_problem(building_name))
    calibration_main(locator, problem, building_name)

if __name__ == '__main__':
    run_as_script()
