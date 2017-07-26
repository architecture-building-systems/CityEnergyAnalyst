from __future__ import division
from sklearn import preprocessing
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, RationalQuadratic,WhiteKernel, ExpSineSquared
import json
import numpy as np
import cea.globalvar
import cea.inputlocator
from sklearn.externals import joblib # this is like the python pickle package
import pandas as pd

gv = cea.globalvar.GlobalVariables()
scenario_path = gv.scenario_reference
locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

# based on the variables listed in the uncertainty database and selected
# through a screening process. they need to be 5.
building_name = 'B01'
samples = np.load(locator.get_calibration_samples(building_name))
cv_rmse = json.load(file(locator.get_calibration_cvrmse_file(building_name)))['rmse']

pd.DataFrame({'cv':cv_rmse}).to_csv(r'C:\reference-case-open\baseline\outputs\data\calibration/test2.csv')