"""
This tool calibrates a set of inputs from CEA to reduce the error between model outputs (predicted) and measured data (observed)
"""
from __future__ import division
from __future__ import print_function

from hyperopt.pyll import scope

import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf
from cea.datamanagement import archetypes_mapper
from cea.demand import demand_main, schedule_maker
from cea.demand.schedule_maker import schedule_maker
from cea.examples import validation
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule
from collections import OrderedDict
from hyperopt import fmin, tpe, hp, Trials
import pandas as pd
import numpy as np
from cea.constants import MONTHS_IN_YEAR_NAMES
from cea.examples.validation import get_measured_building_names
import glob2
import os

__author__ = "Luis Santos"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def modify_monthly_multiplier(locator, config, measured_building_names):
    ##create building input schedules to set monthly multiplier
    archetypes_mapper.archetypes_mapper(locator,
                      update_architecture_dbf=False,
                      update_air_conditioning_systems_dbf=False,
                      update_indoor_comfort_dbf=False,
                      update_internal_loads_dbf=False,
                      update_supply_systems_dbf=False,
                      update_schedule_operation_cea=True,
                      buildings=[])

    ##calculate monthly multiplier based on buildings real consumption
    for building_name in measured_building_names:
        monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
        fields_to_extract = ['Name'] + MONTHS_IN_YEAR_NAMES
        monthly_measured_demand = monthly_measured_data[fields_to_extract].set_index('Name')
        monthly_measured_demand = monthly_measured_demand.loc[building_name]
        monthly_measured_demand = pd.DataFrame({'Month': monthly_measured_demand.index.values,
                                                'measurements': monthly_measured_demand.values})
        monthly_measured_load = monthly_measured_demand.measurements / max(monthly_measured_demand.measurements)

        path_to_schedule = locator.get_building_weekly_schedules(building_name)
        data_schedule, data_metadata = read_cea_schedule(path_to_schedule)
        data_metadata["MONTHLY_MULTIPLIER"] = list(monthly_measured_load.round(2))

        # save cea schedule format
        save_cea_schedule(data_schedule, data_metadata, path_to_schedule)


def calc_score(static_params, dynamic_params):
    """
    This tool reduces the error between observed (real life measured data) and predicted (output of the model data) values by changing some of CEA inputs.
    Annual data is compared in terms of MBE and monthly data in terms of NMBE and CvRMSE (follwing ASHRAE Guideline 14-2002).
    A new input folder with measurements has to be created, with a csv each for monthly and annual data provided as input for this tool.
    A new output csv is generated providing the calibration results (iteration number, parameters tested and results(score metric))
    """
    ## define set of CEA inputs to be calibrated and initial guess values
    SEED = dynamic_params['SEED']
    np.random.seed (SEED)                   #initalize seed numpy randomly npy.random.seed (once call the function) - inside put the seed
     #import random (initialize) npy.random.randint(low=1, high=100, size= number of buildings)/1000 - for every parameter.
    Hs_ag = dynamic_params['Hs_ag']
    Tcs_set_C = dynamic_params['Tcs_set_C']
    Es = dynamic_params['Es']
    Ns = dynamic_params['Ns']
    Occ_m2pax = dynamic_params['Occ_m2pax']
    Vww_lpdpax = dynamic_params['Vww_lpdpax']
    Ea_Wm2 = dynamic_params['Ea_Wm2']
    El_Wm2 = dynamic_params['El_Wm2']

    ##define fixed constant parameters (to be redefined by CEA config file)
    #Hs_ag = 0.15
    #Tcs_set_C = 28
    Tcs_setb_C = 40
    void_deck = 1
    height_bg = 0
    floors_bg = 0

    scenario_list = static_params['scenario_list']
    config = static_params['config']

    locators_of_scenarios = []
    measured_building_names_of_scenarios = []
    for scenario in scenario_list:
        config.scenario = scenario
        locator = cea.inputlocator.InputLocator(config.scenario)
        measured_building_names = get_measured_building_names(locator)
        modify_monthly_multiplier(locator, config, measured_building_names)

        # store for later use
        locators_of_scenarios.append(locator)
        measured_building_names_of_scenarios.append(measured_building_names)

        ## overwrite inputs with corresponding initial values

        # Changes and saves variables related to the architecture
        df_arch = dbf_to_dataframe(locator.get_building_architecture())
        number_of_buildings = df_arch.shape[0]
        Rand_it = np.random.randint(low=-30, high=30, size=number_of_buildings) / 100
        df_arch.Es = Es*(1+Rand_it)
        df_arch.Ns = Ns*(1+Rand_it)
        df_arch.Hs_ag = Hs_ag*(1+Rand_it)
        df_arch.void_deck = void_deck
        dataframe_to_dbf(df_arch, locator.get_building_architecture())

        # Changes and saves variables related to intetnal loads
        df_intload = dbf_to_dataframe(locator.get_building_internal())
        df_intload.Occ_m2pax = Occ_m2pax*(1+Rand_it)
        df_intload.Vww_lpdpax = Vww_lpdpax*(1+Rand_it)
        df_intload.Ea_Wm2 = Ea_Wm2*(1+Rand_it)
        df_intload.El_Wm2 = El_Wm2*(1+Rand_it)
        dataframe_to_dbf(df_intload, locator.get_building_internal())

        #Changes and saves variables related to comfort
        df_comfort = dbf_to_dataframe(locator.get_building_comfort())
        df_comfort.Tcs_set_C = Tcs_set_C*(1+Rand_it)
        df_comfort.Tcs_setb_C = Tcs_setb_C
        dataframe_to_dbf(df_comfort, locator.get_building_comfort())


        # Changes and saves variables related to zone
        df_zone = dbf_to_dataframe(locator.get_zone_geometry().split('.')[0]+'.dbf')
        df_zone.height_bg = height_bg
        df_zone.floors_bg = floors_bg
        dataframe_to_dbf(df_zone, locator.get_zone_geometry().split('.')[0]+'.dbf')

        ## run building schedules and energy demand
        config.schedule_maker.buildings = measured_building_names
        schedule_maker.schedule_maker_main(locator, config)
        config.demand.buildings = measured_building_names
        demand_main.demand_calculation(locator, config)

    # calculate the score
    score = validation.validation(scenario_list=scenario_list,
                                  locators_of_scenarios=locators_of_scenarios,
                                  measured_building_names_of_scenarios=measured_building_names_of_scenarios)

    return score

    ## save the iteration number, the value of each parameter tested and the score obtained ***


def calibration(config, list_scenarios):
    max_evals = 2

    #  define a search space
    # DYNAMIC_PARAMETERS = OrderedDict([('SEED', scope.int(hp.uniform('SEED', 0.0, 100.0))),
    #                                   ('Hs_ag', hp.uniform('Hs_ag', 0.1, 0.4)),
    #                                   ('Tcs_set_C', hp.uniform('Tcs_set_C', 23, 27)),
    #                                   ('Es', hp.uniform('Es', 0.4, 0.8)),
    #                                   ('Ns', hp.uniform('Ns', 0.4, 0.8)),
    #                                   ('Occ_m2pax', hp.uniform('Occ_m2pax', 35.0, 55.0)),
    #                                   ('Vww_lpdpax', hp.uniform('Vww_lpdpax', 25.0, 35.0)),
    #                                   ('Ea_Wm2', hp.uniform('Ea_Wm2', 1.0, 4.0)),
    #                                   ('El_Wm2', hp.uniform('El_Wm2', 1.0, 4.0))
    #                                   ])

    # DYNAMIC_PARAMETERS = OrderedDict([('SEED', scope.int(hp.uniform('SEED', 0.0, 100.0))),
    #                                   ('Hs_ag', hp.uniform('Hs_ag', 0.175, 0.176)),
    #                                   ('Tcs_set_C', hp.uniform('Tcs_set_C', 24, 24.1)),
    #                                   ('Es', hp.uniform('Es', 0.5, 0.51)),
    #                                   ('Ns', hp.uniform('Ns', 0.5, 0.51)),
    #                                   ('Occ_m2pax', hp.uniform('Occ_m2pax', 40.0, 40.1)),
    #                                   ('Vww_lpdpax', hp.uniform('Vww_lpdpax', 27.5, 27.6)),
    #                                   ('Ea_Wm2', hp.uniform('Ea_Wm2', 1.75, 1.76)),
    #                                   ('El_Wm2', hp.uniform('El_Wm2', 1.75, 1.76))
    #                                   ])

    DYNAMIC_PARAMETERS = OrderedDict([('SEED', scope.int(hp.uniform('SEED', 0.0, 100.0))),
                                      ('Hs_ag', hp.uniform('Hs_ag', 0.1, 0.25)),
                                      ('Tcs_set_C', hp.uniform('Tcs_set_C', 24, 26)),
                                      ('Es', hp.uniform('Es', 0.4, 0.6)),
                                      ('Ns', hp.uniform('Ns', 0.4, 0.6)),
                                      ('Occ_m2pax', hp.uniform('Occ_m2pax', 35.0, 45.0)),
                                      ('Vww_lpdpax', hp.uniform('Vww_lpdpax', 25.0, 30.0)),
                                      ('Ea_Wm2', hp.uniform('Ea_Wm2', 1, 2.5)),
                                      ('El_Wm2', hp.uniform('El_Wm2', 1, 2.5))
                                      ])
    STATIC_PARAMS = {'scenario_list': list_scenarios, 'config': config}

    # define the objective
    def objective(dynamic_params):
        return -1.0 * calc_score(STATIC_PARAMS, dynamic_params)

    # run the algorithm
    trials = Trials()
    best = fmin(objective,
                space=DYNAMIC_PARAMETERS,
                algo=tpe.suggest,
                max_evals=max_evals,
                trials=trials)
    print(best)
    print('Best Params: {}'.format(best))
    print(trials.losses())

    import cea.examples.global_variables as global_variables
    validation_n_calib = pd.DataFrame(global_variables.global_validation_n_calibrated)
    validation_percentage = pd.DataFrame(global_variables.global_validation_percentage)

    results = pd.DataFrame()
    for counter in range(0, max_evals):
        results_it = [counter,
                      trials.trials[counter]['misc']['vals']['SEED'][0],
                      trials.trials[counter]['misc']['vals']['Hs_ag'][0],
                      trials.trials[counter]['misc']['vals']['Tcs_set_C'][0],
                      trials.trials[counter]['misc']['vals']['Ea_Wm2'][0],
                      trials.trials[counter]['misc']['vals']['El_Wm2'][0],
                      trials.trials[counter]['misc']['vals']['Es'][0],
                      trials.trials[counter]['misc']['vals']['Ns'][0],
                      trials.trials[counter]['misc']['vals']['Occ_m2pax'][0],
                      trials.trials[counter]['misc']['vals']['Vww_lpdpax'][0],
                      trials.losses()[counter]
                      ]
        results_it = pd.DataFrame([results_it])
        results = results.append(results_it)
    results.reset_index(drop=True, inplace=True)
    results = pd.concat([results, validation_n_calib, validation_percentage],  axis=1, sort=False).sort_index()

    results.columns = ['eval', 'SEED','Hs_ag','Tcs_set_C', 'Ea_Wm2', 'El_Wm2', 'Es',
                       'Ns', 'Occ_m2pax', 'Vww_lpdpax', 'score_weighted_demand', 'buildings_calibrated', 'percentage_buildings_calibrated_%']
    project_path = config.project
    output_path = (project_path + r'/output/calibration/')

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    file_name = output_path+'calibration_results.csv'
    results.to_csv(file_name, index=False)

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
    project_path = config.project
    measurement_files = sorted(glob2.glob(project_path + '/**/monthly_measurements.csv'))

    list_scenarios = []
    for f in measurement_files:
        list_scenarios.append(os.path.dirname(os.path.dirname(os.path.dirname(f))))
    print(list_scenarios[:])

    calibration(config, list_scenarios[:])

if __name__ == '__main__':
    main(cea.config.Configuration())
