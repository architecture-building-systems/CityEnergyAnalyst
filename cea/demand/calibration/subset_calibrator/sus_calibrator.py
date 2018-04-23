# coding=utf-8
"""
'sus_calibrator.py' script hosts the following functions:
    (1) calls
    (2) collect CEA outputs (demands)
    (3) add delay to time-sensitive inputs
    (4) return the input and target matrices
"""

import os
import multiprocessing as mp
import numpy as np
import pandas as pd
from cea.demand.metamodel.nn_generator.nn_trainer_estimate import input_prepare_estimate
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator.nn_settings import nn_delay, target_parameters, warmup_period
from cea.demand.metamodel.nn_generator.input_matrix import get_cea_inputs
from cea.demand.metamodel.nn_generator.nn_trainer_resume import nn_model_collector
import cea.inputlocator
import cea.globalvar
import cea.config
from cea.utilities import epwreader

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian","Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def ss_calibrator(list_building_names, locator, gv, climatic_variables, region, year,
                           use_daysim_radiation, use_stochastic_occupancy):
    input_prepare_estimate(list_building_names, locator, gv, climatic_variables, region, year,
                           use_daysim_radiation, use_stochastic_occupancy)

def main(config):
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]
    region = config.region
    settings = config.demand
    use_daysim_radiation = settings.use_daysim_radiation
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator, region, year, use_daysim_radiation)
    list_building_names = building_properties.list_building_names()
    ss_calibrator(list_building_names, locator, gv, climatic_variables=config.neural_network.climatic_variables,
                  region=config.region, year=config.neural_network.year,
                  use_daysim_radiation=settings.use_daysim_radiation,
                  use_stochastic_occupancy=config.demand.use_stochastic_occupancy)


if __name__ == '__main__':
    main(cea.config.Configuration())