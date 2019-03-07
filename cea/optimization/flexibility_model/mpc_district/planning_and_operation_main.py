from __future__ import division

import datetime
import os
import time

from pyomo.environ import *

import cea.config
import cea.inputlocator
from cea.optimization.flexibility_model.mpc_building import operation_write_results
from cea.optimization.flexibility_model.mpc_district import planning_and_operation_plots
from cea.optimization.flexibility_model.mpc_district import planning_and_operation_write_results, \
    planning_and_operation_optimization
from cea.optimization.flexibility_model.constants import PARAMETER_SET, TIME_STEP_TS, SOLVER_NAME, TIME_LIMIT, ALPHA, BETA, \
    POWER_FACTOR, VOLTAGE_NOMINAL, INTEREST_RATE, LOAD_FACTOR, APPROX_LOSS_HOURS

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def planning_and_operation(locator, config):
    # Local vars
    scenario_name = config.scenario_name  # scenario_name
    country = config.region
    weather_path = config.weather
    threads = config.get_number_of_processes()

    time_start = config.mpc_district.time_start
    time_end = config.mpc_district.time_end
    set_temperature_goal = config.mpc_district.set_temperature_goal
    constant_temperature = config.mpc_district.constant_temperature
    pricing_scheme = config.mpc_district.pricing_scheme
    constant_price = config.mpc_district.constant_price
    min_max_source = config.mpc_district.min_max_source
    min_constant_temperature = config.mpc_district.min_constant_temperature
    max_constant_temperature = config.mpc_district.max_constant_temperature
    delta_set = config.mpc_district.delta_set
    delta_setback = config.mpc_district.delta_setback

    # local constants
    parameter_set = PARAMETER_SET
    time_step_ts = TIME_STEP_TS
    solver_name = SOLVER_NAME
    time_limit = TIME_LIMIT
    alpha = ALPHA
    beta = BETA
    power_factor = POWER_FACTOR
    approx_loss_hours = APPROX_LOSS_HOURS
    voltage_nominal = VOLTAGE_NOMINAL
    load_factor = LOAD_FACTOR
    interest_rate = INTEREST_RATE

    t0 = time.clock()
    time_main = time.time()
    date_main = datetime.datetime.now()

    print('Running scenario: ' + scenario_name)

    print('Processing: Setup models and optimization')
    m = planning_and_operation_optimization.main(locator, weather_path,
                                                 scenario_name,
                                                 country,
                                                 parameter_set,
                                                 time_start,
                                                 time_end,
                                                 time_step_ts,
                                                 set_temperature_goal,
                                                 constant_temperature,
                                                 alpha,
                                                 beta,
                                                 pricing_scheme,
                                                 constant_price,
                                                 min_max_source,
                                                 min_constant_temperature,
                                                 max_constant_temperature,
                                                 delta_set,
                                                 delta_setback,
                                                 power_factor,
                                                 approx_loss_hours,
                                                 voltage_nominal,
                                                 load_factor,
                                                 interest_rate
                                                 )

    print('Processing: Solve optimization')
    opt = SolverFactory(solver_name)  # Create a solver
    if time_limit > 0:
        if solver_name == 'cplex':
            opt.options['timelimit'] = time_limit
        elif solver_name == 'gurobi':
            opt.options['TimeLimit'] = time_limit
    opt.options['threads'] = threads
    opt.solve(
        m,
        tee=True
    )

    print('Processing: Write results')
    output_folder = "mpc-district"
    planning_and_operation_write_results.print_res(m)
    planning_and_operation_write_results.write_results(locator, output_folder, scenario_name,
                                                       m,
                                                       time_main,
                                                       solver_name,
                                                       threads,
                                                       time_limit,
                                                       interest_rate,
                                                       voltage_nominal,
                                                       approx_loss_hours,
                                                       alpha,
                                                       beta,
                                                       load_factor
                                                       )
    planning_and_operation_plots.save_plots(locator, m)
    operation_write_results.main(locator, m, output_folder)

    print('Completed.')
    print('Total time: {:.2f} seconds'.format(time.clock() - t0))


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    planning_and_operation(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
