"""
Building model main function definitions
"""

import os, sys, inspect, time
from concept.algorithm_planning_and_operation.lp_op_config import *

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


from cea.concept_project.model_building_cleaned_up.building_model.building import Building  # Unresolved reference warnings can be ignored
from cea.concept_project.model_building_cleaned_up.building_model.utils import *  # Unresolved reference warnings can be ignored
from concept.model_building.get_process_write_data import main_get_process_write_data
from concept.algorithm_operation.preliminary_setup_optimisation \
    import main_preliminary_setup_optimisation
from concept.algorithm_operation.optimisation_district import main_optimisation_district

# User parameters --> to be changed if needed
# TODO: Move case files to local folder and make local user config file to define path
# Keeping it in the data folder for now, so I don't need to change the path after each commit
scenario_data_path = 'C:\Users\Bhargava\Documents\GitHub\CityEnergyAnalyst\cea\concept_project\data'
results_path = os.path.join(scenario_data_path, 'output_operation')

# Case parameters --> to be changed if needed
# scenario = 'reference-case-WTP/MIX_high_density'
# scenario = 'reference-case-WTP-reduced/WTP_MIX_m'
# scenario = 'IBPSA/Office'
# scenario = 'IBPSA/Office_Residential'
# scenario = 'IBPSA/Office_Retail_Residential'
# scenario = 'IBPSA/Residential'
# scenario = 'IBPSA/Retail'
# scenario = 'IBPSA/Retail_Office'
# scenario = 'IBPSA/Retail_Residential'
scenario = SCENARIO  # Use SCENARIO from lp_op_config
scenario = os.path.normpath(scenario)  # Convert to proper path name

country = 'SIN'  # If changing this, supply appropriate data in scenario files
parameter_set = 'parameters_default'

# Time parameters --> to be changed if needed
# time_start = '2005-03-02 00:00:00'
time_start = '2005-01-01 00:00:00'
# time_end = '2005-12-31 23:30:00'
time_end = '2005-01-01 23:30:00'
time_step_ts = '01:00:00'
# time_step_ts = '00:30:00'

# Goal parameters --> to be changed if needed
# case_goal = 'set_temperature_tracking'
# case_goal = 'price_based_flexibility'
if BETA > 0:
    case_goal = 'set_temperature_tracking'
else:
    case_goal = 'price_based_flexibility'

pricing_scheme = 'constant_prices'  # Uses constant_price for all time steps
# pricing_scheme = 'dynamic_prices'  # Loads prices from file (Check implementation in main_get_process_write_data)
constant_price = 255.2  # SGD/MWh from https://www.spgroup.com.sg/what-we-do/billing

# Make sure that the set temperature respects the constraints, especially for the initial temperature
# set_temperature_goal = 'set_setback_temperature'
# set_temperature_goal = 'follow_cea'
set_temperature_goal = 'constant_temperature'
constant_temperature = 25  # For 'constant_temperature'

# min_max_source == 'from building.py'
# min_max_source = 'from occupancy variations'
delta_set = 3
delta_setback = 5
min_max_source = 'constants'
min_constant_temperature = 20  # For 'constants'
max_constant_temperature = 25  # For 'constants'


def connect_database(
        data_path=os.path.join(scenario_data_path, scenario, 'concept', 'building-definition')
):
    # Update database from CSV files
    create_database(
        sqlite_path=os.path.join(data_path, 'data.sqlite'),
        sql_path=os.path.abspath(os.path.join(
            data_path, '..', '..', '..', '..', '..', 'external', 'building_model', 'data', 'data.sqlite.schema.sql'
        )),
        csv_path=data_path
    )

    conn = sqlite3.connect(os.path.join(data_path, 'data.sqlite'))
    return conn


def get_building_model(scenario_name, conn):
    building = Building(conn, scenario_name)
    return building


def get_optimisation_inputs():
    # Non-building-specific data
    print('Processing: Load data')
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
        electricity_prices_MWh,
        T_int_cea_dic,
        thermal_room_load_cea_dic,
        thermal_between_generation_emission_cea_dic
    ) = main_get_process_write_data(
        scenario_data_path,
        scenario,
        country,
        parameter_set,
        time_start,
        time_end,
        time_step_ts,
        set_temperature_goal,
        constant_temperature
    )

    # Building-specific data
    print('Processing: Building models')
    buildings_dic = {}
    for building in buildings_names:
        scenario_name = scenario + '/' + building
        conn = connect_database()
        calculate_irradiation_surfaces(conn, weather_type='Create-Singaproe', irradiation_model='disc')
        # TODO: Automatically take first existing weather type

        print('Processing: Building model ' + building)
        buildings_dic[building] = get_building_model(scenario_name, conn)

        # # For debugging
        # print('Building model ' + building + ' :')
        # if building == 'B001':
        #     print('-----------------------------------------------------------------------------------------')
        #     print('buildings_dic[building].state_matrix=')
        #     print(buildings_dic[building].state_matrix)
        #     print('-----------------------------------------------------------------------------------------')
        #     print('buildings_dic[building].control_matrix=')
        #     print(buildings_dic[building].control_matrix)
        #     print('-----------------------------------------------------------------------------------------')
        #     print('buildings_dic[building].disturbance_matrix=')
        #     print(buildings_dic[building].disturbance_matrix)
        #     print('-----------------------------------------------------------------------------------------')
        #     print('buildings_dic[building].state_output_matrix=')
        #     print(buildings_dic[building].state_output_matrix)
        #     print('-----------------------------------------------------------------------------------------')
        #     print('buildings_dic[building].control_output_matrix=')
        #     print(buildings_dic[building].control_output_matrix)
        #     print('-----------------------------------------------------------------------------------------')
        #     print('buildings_dic[building].disturbance_output_matrix=')
        #     print(buildings_dic[building].disturbance_output_matrix)
        #     print('-----------------------------------------------------------------------------------------')

        conn.close()

    (
        initial_state_dic,
        price_vector,
        alpha,
        beta,
        minimum_output_dic,
        maximum_output_dic,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index
    ) = main_preliminary_setup_optimisation(
        case_goal,
        pricing_scheme,
        constant_price,
        min_max_source,
        min_constant_temperature,
        max_constant_temperature,
        prediction_horizon,
        date_and_time_prediction,
        time_start, delta_set,
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
        results_path,
        alpha,
        beta,
        prediction_horizon,
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        buildings_dic,
        buildings_names,
        buildings_cardinal,
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
        price_vector,
        electricity_prices_MWh,
        T_int_cea_dic,
        thermal_room_load_cea_dic,
        thermal_between_generation_emission_cea_dic
    )


def run_optimisation(return_peak_loads=False):
    m = main_optimisation_district(
        *get_optimisation_inputs()
    )

    if return_peak_loads:
        return m.peak_loads_per_building_df


if __name__ == "__main__":
    t0 = time.clock()
    run_optimisation()
    t1 = time.clock()
    print('Computation time: {} seconds'.format(t1 - t0))
