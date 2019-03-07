from __future__ import division

import datetime
import os
import sqlite3
import time

from pyomo.environ import *

import cea.config
import cea.inputlocator
from cea.optimization.flexibility_model import model_building
from cea.optimization.flexibility_model.mpc_building import operation_optimization
from cea.optimization.flexibility_model.mpc_building import operation_preprocess_optimization
from cea.optimization.flexibility_model.mpc_building import operation_write_results
from cea.optimization.flexibility_model.constants import PARAMETER_SET, TIME_STEP_TS, SOLVER_NAME, TIME_LIMIT, ALPHA, BETA
from cea.optimization.flexibility_model.model_building import building_main
from cea.optimization.flexibility_model.model_building import building_utils
from cea.optimization.flexibility_model.model_building.building import Building

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def operation(locator, config):
    # local variables
    scenario_name = config.scenario_name  # scenario_name
    country = config.region
    weather_path = config.weather
    threads = config.get_number_of_processes()

    time_start = config.mpc_building.time_start
    time_end = config.mpc_building.time_end
    set_temperature_goal = config.mpc_building.set_temperature_goal
    constant_temperature = config.mpc_building.constant_temperature
    pricing_scheme = config.mpc_building.pricing_scheme
    constant_price = config.mpc_building.constant_price
    min_max_source = config.mpc_building.min_max_source
    min_constant_temperature = config.mpc_building.min_constant_temperature
    max_constant_temperature = config.mpc_building.max_constant_temperature
    delta_set = config.mpc_building.delta_set
    delta_setback = config.mpc_building.delta_setback

    # local constants
    parameter_set = PARAMETER_SET
    time_step_ts = TIME_STEP_TS
    solver_name = SOLVER_NAME
    time_limit = TIME_LIMIT
    alpha = ALPHA
    beta = BETA

    t0 = time.clock()
    date_main = datetime.datetime.now()

    (
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        buildings_dic,
        buildings_names,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index,
        heating_boolean,
        cooling_boolean,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        set_temperatures_dic,
        initial_state_dic,
        minimum_output_dic,
        maximum_output_dic,
        em_efficiency_mean_dic,
        Qcsmax_Wm2_dic,
        gross_floor_area_m2,
        price_vector
    ) = get_optimization_inputs(locator, weather_path,
                                scenario_name,
                                country,
                                parameter_set,
                                time_start,
                                time_end,
                                time_step_ts,
                                set_temperature_goal,
                                constant_temperature,
                                pricing_scheme,
                                constant_price,
                                min_max_source,
                                min_constant_temperature,
                                max_constant_temperature,
                                delta_set,
                                delta_setback
                                )
    print('Processing: Setup optimization model')
    m = operation_optimization.main(
        alpha,
        beta,
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        buildings_dic,
        buildings_names,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index,
        heating_boolean,
        cooling_boolean,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        set_temperatures_dic,
        initial_state_dic,
        minimum_output_dic,
        maximum_output_dic,
        em_efficiency_mean_dic,
        Qcsmax_Wm2_dic,
        gross_floor_area_m2,
        price_vector
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
    output_folder = "mpc-building"  # this is an identifier for the location of the output folder
    operation_write_results.main(locator, m, output_folder)
    print('Completed.')
    print('Total time: {:.2f} seconds'.format(time.clock() - t0))


def get_optimization_inputs(locator, weather_path,
                            scenario,
                            country,
                            parameter_set,
                            time_start,
                            time_end,
                            time_step_ts,
                            set_temperature_goal,
                            constant_temperature,
                            pricing_scheme,
                            constant_price,
                            min_max_source,
                            min_constant_temperature,
                            max_constant_temperature,
                            delta_set,
                            delta_setback
                            ):
    print('Processing: Load data & translate building model definitions')
    (
        prediction_horizon,
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step, year, buildings_names,
        buildings_cardinal,
        center_interval_temperatures_dic,
        set_setback_temperatures_dic,
        setback_boolean_dic,
        heating_boolean,
        cooling_boolean,
        set_temperatures_dic,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        gross_floor_area_m2,
        total_gross_floor_area_m2,
        indoor_comfort_df,
        occupancy_density_m2_p,
        occupancy_probability_df,
        em_efficiency_mean_dic,
        Qcsmax_Wm2_dic,
        electricity_prices_MWh
    ) = building_main.main(locator, weather_path,
                           scenario,
                           country,
                           parameter_set,
                           time_start,
                           time_end,
                           time_step_ts,
                           set_temperature_goal,
                           constant_temperature
                           )

    print('Processing: Create building state space models')
    buildings_dic = {}
    for building in buildings_names:
        # Update database from CSV files
        building_data_path = locator.get_mpc_results_building_definitions_folder()
        building_utils.create_database(
            sqlite_path=os.path.join(building_data_path, 'data.sqlite'),
            sql_path=os.path.abspath(os.path.join(
                os.path.dirname(model_building.__file__), 'setup_data', 'data.sqlite.schema.sql'
            )),
            csv_path=building_data_path
        )
        conn = sqlite3.connect(os.path.join(building_data_path, 'data.sqlite'))

        building_utils.calculate_irradiation_surfaces(conn, weather_type='Create-Singaproe', irradiation_model='disc')
        # TODO: Automatically take first existing weather type

        building_scenario_name = scenario + '/' + building
        buildings_dic[building] = Building(conn, building_scenario_name)
        conn.close()

    print('Processing: Generate optimization constraint definitions')
    (
        initial_state_dic,
        price_vector,
        minimum_output_dic,
        maximum_output_dic,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index
    ) = operation_preprocess_optimization.main(
        pricing_scheme,
        constant_price,
        min_max_source,
        min_constant_temperature,
        max_constant_temperature,
        prediction_horizon,
        date_and_time_prediction,
        time_start,
        delta_set,
        delta_setback,
        buildings_names,
        buildings_cardinal,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        center_interval_temperatures_dic,
        setback_boolean_dic,
        gross_floor_area_m2,
        indoor_comfort_df,
        occupancy_density_m2_p,
        occupancy_probability_df,
        buildings_dic,
        electricity_prices_MWh,
        set_temperatures_dic
    )

    return (
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        buildings_dic,
        buildings_names,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index,
        heating_boolean,
        cooling_boolean,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        set_temperatures_dic,
        initial_state_dic,
        minimum_output_dic,
        maximum_output_dic,
        em_efficiency_mean_dic,
        Qcsmax_Wm2_dic,
        gross_floor_area_m2,
        price_vector
    )


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    operation(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
