from __future__ import division
from sklearn import preprocessing
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, RationalQuadratic,WhiteKernel, ExpSineSquared
import json
import numpy as np
import cea.globalvar
import cea.inputlocator
from sklearn.externals import joblib # this is like the python pickle package

__author__ = "Adam Rysanek"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Adam Rysanek, Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def gaussian_emulator(locator, samples, cv_rmse, building_name):
    """
    Thi is a Gaussian process linear emulator. It is used to create a surrogate model of CEA whose
    output is either rmse or cvrmse

    for more details on the work behind this please check:
    Rysanek A., Fonseca A., Schlueter, A. Bayesian calibration of Dyanmic building Energy Models. Applied Energy 2017.

    :param locator: pointer to location of CEA files
    :param samples: matrix m x n with samples simulated from CEA. m are the number of input variables [0,1]
    :param cv_rmse: array with results of cv_rmse after running n samples.
    :param building_name: name of building whose calibration process is being acted upon
    :return:
           file with database of emulator stored in locator.get_calibration_cvrmse_file(building_name)

    """

    # Kernel with parameters given in GPML book for the gaussian surrogate models. The hyperparameters are optimized so you can get anything here.
    k1 = 5**2 * RBF(length_scale=1e-5)  # long term smooth rising trend RBF: radio basis functions (you can have many, this is one).
    k2 = 5**2 * RBF(length_scale=0.000415) * ExpSineSquared(length_scale=3.51e-5, periodicity=0.000199)  # seasonal component
    # medium term irregularity
    k3 = 316**2 * RationalQuadratic(length_scale=3.54, alpha=1e+05)
    k4 = 316**2 * RBF(length_scale=4.82) + WhiteKernel(noise_level=0.43)  # noise terms
    kernel = k1 + k2 + k3 + k4

    # give the data to the regressor.
    gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-7, normalize_y=True, n_restarts_optimizer=2)
    gp.fit(samples, cv_rmse) # then fit the gp to your observations and the minmax. It takes 30 min - 1 h.

    # this is the result
    joblib.dump(gp, locator.get_calibration_gaussian_emulator(building_name))

def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario=scenario_path)

    # based on the variables listed in the uncertainty database and selected
    # through a screening process. they need to be 5.
    building_name = 'B01'
    samples = np.load(locator.get_calibration_samples(building_name))
    samples_norm = samples[1]
    cv_rmse = json.load(open(locator.get_calibration_cvrmse_file(building_name)))['cv_rmse']
    gaussian_emulator(locator, samples_norm, cv_rmse, building_name)

if __name__ == '__main__':
    run_as_script()