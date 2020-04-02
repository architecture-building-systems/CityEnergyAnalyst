"""
This tool calibrates a set of inputs from CEA to reduce the error between model outputs (predicted) and measured data (observed)
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf
from cea.datamanagement import data_helper
from cea.demand import demand_main, schedule_maker
from cea.demand.schedule_maker import schedule_maker
from cea.examples import validation
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule
import numpy as np
from scipy.optimize import minimize
from hyperopt import hp
from collections import OrderedDict
from sklearn.linear_model import LogisticRegression
import hyperopt.pyll
from hyperopt.pyll import scope
import pickle
import time
import matplotlib.pyplot as plt
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from hyperopt.plotting import main_plot_history,main_plot_histogram
import pandas as pd
from sklearn.metrics import mean_squared_error
from math import sqrt
from cea.constants import MONTHS_IN_YEAR, MONTHS_IN_YEAR_NAMES

from sklearn.externals import joblib

__author__ = "Luis Santos"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def modify_monthly_multiplier (locator, config):

    ##create building input schedules to set monthly multiplier
    data_helper.data_helper(locator, config.data_helper.region, overwrite_technology_folder=False,
                update_architecture_dbf=False, update_HVAC_systems_dbf=False, update_indoor_comfort_dbf=False,
                update_internal_loads_dbf=False, update_supply_systems_dbf=False,
                update_schedule_operation_cea=True, buildings=[])

    ##calculate monthly multiplier based on buildings real consumption
    monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
    measured_building_names = monthly_measured_data.Name.values
    measured_building_names = list(measured_building_names)

    for building_name in measured_building_names:
        monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
        fields_to_extract = ['Name'] + MONTHS_IN_YEAR_NAMES
        monthly_measured_demand = monthly_measured_data[fields_to_extract].set_index('Name')
        monthly_measured_demand = monthly_measured_demand.loc[building_name]
        monthly_measured_demand = pd.DataFrame({'Month': monthly_measured_demand.index.values,
                                                'measurements': monthly_measured_demand.values})
        monthly_measured_load = monthly_measured_demand.measurements/max(monthly_measured_demand.measurements)

        path_to_schedule = locator.get_building_weekly_schedules(building_name)
        data_schedule, data_metadata = read_cea_schedule(path_to_schedule)
        data_metadata["MONTHLY_MULTIPLIER"]=list(monthly_measured_load.round(2))

        # save cea schedule format
        save_cea_schedule(data_schedule, data_metadata, path_to_schedule)
    return measured_building_names

def calc_score(static_params, params):
    """
    This tool reduces the error between observed (real life measured data) and predicted (output of the model data) values by changing some of CEA inputs.
    Annual data is compared in terms of MBE and monthly data in terms of NMBE and CvRMSE (follwing ASHRAE Guideline 14-2002).
    A new input folder with measurements has to be created, with a csv each for monthly and annual data provided as input for this tool.
    A new output csv is generated providing the calibration results (iteration number, parameters tested and results(score metric))
    """
    locator = static_params['locator']
    config = static_params['config']
    measured_building_names = static_params['measured_building_names']

    ## define set of CEA inputs to be calibrated and initial guess values
    Es = params['Es']
    Ns = params['Ns']
    Occ_m2pax = params['Occ_m2pax']
    Vww_lpdpax = params['Vww_lpdpax']
    Ea_Wm2 = params['Ea_Wm2']
    El_Wm2 = params['El_Wm2']

    ##define fixed constant parameters (to be redefined by CEA config file)
    Hs_ag = 0
    Tcs_set_C = 40
    Tcs_setb_C = 40

    ## overwrite inputs with corresponding initial values
    df_arch = dbf_to_dataframe(locator.get_building_architecture())
    df_arch.Es = Es
    df_arch.Ns = Ns
    df_arch.Hs_ag = Hs_ag
    df_arch = dataframe_to_dbf(df_arch, locator.get_building_architecture())

    df_intload = dbf_to_dataframe(locator.get_building_internal())
    df_intload.Occ_m2pax = Occ_m2pax
    df_intload.Vww_lpdpax = Vww_lpdpax
    df_intload.Ea_Wm2 = Ea_Wm2
    df_intload.El_Wm2 = El_Wm2
    df_intload = dataframe_to_dbf(df_intload, locator.get_building_internal())

    df_comfort = dbf_to_dataframe(locator.get_building_comfort())
    df_comfort.Tcs_set_C = Tcs_set_C
    df_comfort.Tcs_setb_C = Tcs_setb_C
    df_comfort = dataframe_to_dbf(df_comfort, locator.get_building_comfort())

    ## run building schedules and energy demand
    config.schedule_maker.buildings = measured_building_names
    schedule_maker.schedule_maker_main(locator, config)
    config.demand.buildings = measured_building_names
    demand_main.demand_calculation(locator, config)

    #calculate the score
    score = validation.validation(locator, measured_building_names)

    return score

    ## save the iteration number, the value of each parameter tested and the score obtained ***


def calibration(config, locator):
    measured_building_names = modify_monthly_multiplier(locator, config)
    max_evals = 2

    #  define a search space
    SPACE = OrderedDict([('Es', hp.uniform('Es', 0.6, 1.0)),
                         ('Ns', hp.uniform('Ns', 0.7, 1.0)),
                         ('Occ_m2pax', hp.uniform('Occ_m2pax', 30.0, 60.0)),
                         ('Vww_lpdpax', hp.uniform('Vww_lpdpax', 20.0, 40.0)),
                         ('Ea_Wm2', hp.uniform('Ea_Wm2', 1.0, 5.0)),
                         ('El_Wm2', hp.uniform('El_Wm2', 1.0, 5.0))
                         ])
    STATIC_PARAMS = {'locator': locator, 'config': config, 'measured_building_names':measured_building_names}

    #define the objective
    def objective(params):
        return -1.0 * calc_score(STATIC_PARAMS, params)

    #run the algorithm
    trials = Trials()
    best = fmin(objective,
                space=SPACE,
                algo=tpe.suggest,
                max_evals=max_evals,
                trials=trials)
    print(best)
    print('Best Params: {}'.format(best))
    print (trials.losses())
    results=[]
    for counter in range(0, max_evals):

        results_it = [counter,trials.trials[counter]['misc']['vals']['Ea_Wm2'][0],trials.trials[counter]['misc']['vals']['El_Wm2'][0], trials.trials[counter]['misc']['vals']['Es'][0],trials.trials[counter]['misc']['vals']['Ns'][0],
          trials.trials[counter]['misc']['vals']['Occ_m2pax'][0],trials.trials[counter]['misc']['vals']['Vww_lpdpax'][0],trials.losses()[counter]]
        results.append(results_it)
    results=pd.DataFrame(results)
    path=locator.get_calibrationresults()
    results.to_csv(path, index=False)
        # results = pd.DataFrame(results_it)
        #
        # results.to_csv('calibration_it.csv')
        # print (results)
        # print(counter,trials.trials[counter]['misc']['vals']['Ea_Wm2'],trials.trials[counter]['misc']['vals']['El_Wm2'], trials.trials[counter]['misc']['vals']['Es'],trials.trials[counter]['misc']['vals']['Ns'],
        #   trials.trials[counter]['misc']['vals']['Occ_m2pax'],trials.trials[counter]['misc']['vals']['Vww_lpdpax'],trials.losses()[counter])

    x=1
def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """


    # assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    #
    # list_scenarios = ['C:\CEA\HDB_calibration\LCZ1_Yishun', 'C:\CEA\HDB_calibration\LCZ4_Tampines']
    # for scenario in list_scenarios:
    #     config.scenario = scenario
    #     locator = cea.inputlocator.InputLocator(config.scenario)
    # calibration(config, locator)

    list_scenarios = ['C:\CEA\HDB_calibration\LCZ1_Yishun', 'C:\CEA\HDB_calibration\LCZ4_Tampines']
    for scenario in list_scenarios:
        config.scenario = scenario
        assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
        locator = cea.inputlocator.InputLocator(config.scenario)
        calibration(config, locator)

    # monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
    # measured_building_names = monthly_measured_data.Name.values
    # measured_building_names = list(measured_building_names)
    # building_names = measured_building_names
    # return building_names

if __name__ == '__main__':
    main(cea.config.Configuration())
