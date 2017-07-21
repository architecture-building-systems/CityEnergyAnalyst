from __future__ import division
from sklearn import preprocessing
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, RationalQuadratic,WhiteKernel, ExpSineSquared
import pickle
from sklearn.externals import joblib # this is like the python pickle package

__author__ = "Adam Rysanek"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Adam Rysanek, Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def gaussian_emulator(input_samples, sampling_results, output_path):

    # this normalizes all the input variables independently 0 - 1. so this might not be neccesary
    min_max_scaler = preprocessing.MinMaxScaler()
    Xnorm = min_max_scaler.fit_transform(input_samples)

    # Kernel with parameters given in GPML book for the gaussian surrogate models. The hyperparameters are optimized so you can get anything here.
    k1 = 5**2 * RBF(length_scale=1e-5)  # long term smooth rising trend RBF: radio basis functions (you can have many, this is one).
    k2 = 5**2 * RBF(length_scale=0.000415) * ExpSineSquared(length_scale=3.51e-5, periodicity=0.000199)  # seasonal component
    # medium term irregularity
    k3 = 316**2 * RationalQuadratic(length_scale=3.54, alpha=1e+05)
    k4 = 316**2 * RBF(length_scale=4.82) + WhiteKernel(noise_level=0.43)  # noise terms
    kernel = k1 + k2 + k3 + k4

    # give the data to the regressor.
    gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-7, normalize_y=True, n_restarts_optimizer=2)
    gp.fit(Xnorm, sampling_results) # then fit the gp to your observations and the minmax. It takes 30 min - 1 h.

    # this is the result
    joblib.dump(gp, output_path)