from __future__ import division

import datetime
import errno
import os
import time

from pyomo.environ import *

from cea.concept_project import config
from cea.concept_project.algorithm_operation import operation_write_results
from cea.concept_project.algorithm_planning_and_operation import planning_and_operation_optimization
from cea.concept_project.algorithm_planning_and_operation import planning_and_operation_plots
from cea.concept_project.algorithm_planning_and_operation import planning_and_operation_write_results

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def main(
        scenario_data_path=config.scenario_data_path,
        scenario=config.scenario,
        country=config.country,
        parameter_set=config.parameter_set,
        time_start=config.time_start,
        time_end=config.time_end,
        time_step_ts=config.time_step_ts,
        set_temperature_goal=config.set_temperature_goal,
        constant_temperature=config.constant_temperature,
        alpha=config.alpha,
        beta=config.beta,
        pricing_scheme=config.pricing_scheme,
        constant_price=config.constant_price,
        min_max_source=config.min_max_source,
        min_constant_temperature=config.min_constant_temperature,
        max_constant_temperature=config.max_constant_temperature,
        delta_set=config.delta_set,
        delta_setback=config.delta_setback,
        power_factor=config.power_factor,
        approx_loss_hours=config.approx_loss_hours,
        voltage_nominal=config.voltage_nominal,
        load_factor=config.load_factor,
        interest_rate=config.interest_rate,
        solver_name=config.solver_name,
        time_limit=config.time_limit,
        threads=config.threads
):
    t0 = time.clock()
    time_main = time.time()
    date_main = datetime.datetime.now()

    print('Running scenario: ' + scenario)

    print('Processing: Setup models and optimization')
    m = planning_and_operation_optimization.main(
        scenario_data_path,
        scenario,
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
    output_folder = "mpc_district"
    planning_and_operation_write_results.print_res(m)
    planning_and_operation_write_results.write_results(
        m,
        results_path,
        time_main,
        scenario_data_path,
        scenario,
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
    planning_and_operation_plots.save_plots(m, scenario_data_path, scenario, results_path)
    operation_write_results.main(locator, m, output_folder)

    print('Completed.')
    print('Total time: {:.2f} seconds'.format(time.clock() - t0))


if __name__ == '__main__':
    main()
