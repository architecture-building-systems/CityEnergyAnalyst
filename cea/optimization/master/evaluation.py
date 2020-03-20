"""
Evaluation function of an individual

"""
from __future__ import division

import cea.inputlocator
from cea.optimization.master import cost_model
from cea.optimization.master import master_to_slave as master
from cea.optimization.master.generation import individual_to_barcode
from cea.optimization.master.performance_aggregation import summarize_results_individual
from cea.optimization.slave import cooling_main
from cea.optimization.slave import electricity_main
from cea.optimization.slave import heating_main


# +++++++++++++++++++++++++++++++++++++
# Main objective function evaluation
# ++++++++++++++++++++++++++++++++++++++

def evaluation_main(individual,
                    building_names_all,
                    locator,
                    network_features,
                    weather_features,
                    config,
                    prices,
                    lca,
                    individual_number,
                    generation_number,
                    column_names_individual,
                    column_names_buildings_heating,
                    column_names_buildings_cooling,
                    building_names_heating,
                    building_names_cooling,
                    building_names_electricity,
                    district_heating_network,
                    district_cooling_network,
                    technologies_heating_allowed,
                    technologies_cooling_allowed
                    ):
    """
    This function evaluates an individual

    :param individual: list with values of the individual
    :param column_names_buildings_all: list with names of buildings
    :param cea.inputlocator.InputLocator locator: locator class
    :param solar_features: solar features call to class
    :param network_features: network features call to class
    :param optimization_constants: class containing constants used in optimization
    :param config: configuration file
    :param prices: class of prices used in optimization
    :type individual: list
    :type column_names_buildings_all: list
    :type solar_features: class
    :type network_features: class
    :type optimization_constants: class
    :type config: class
    :type prices: class
    :return: Resulting values of the objective function. costs, CO2, prim
    :rtype: tuple

    """

    # CREATE THE INDIVIDUAL BARCODE AND INDIVIDUAL WITH HER COLUMN NAME AS A DICT
    DHN_barcode, DCN_barcode, individual_with_name_dict, building_connectivity_dict = individual_to_barcode(individual,
                                                                                                            building_names_all,
                                                                                                            building_names_heating,
                                                                                                            building_names_cooling,
                                                                                                            column_names_individual,
                                                                                                            column_names_buildings_heating,
                                                                                                            column_names_buildings_cooling)

    print("EVALUATING THE NEXT SYSTEM OPTION/INDIVIDUAL")
    print(individual_with_name_dict)
    # CREATE CLASS AND PASS KEY CHARACTERISTICS OF INDIVIDUAL
    # THIS CLASS SHOULD CONTAIN ALL VARIABLES THAT MAKE AN INDIVIDUAL CONFIGURATION
    master_to_slave_vars = master.export_data_to_master_to_slave_class(locator,
                                                                       generation_number,
                                                                       individual_number,
                                                                       individual_with_name_dict,
                                                                       building_names_all,
                                                                       building_names_heating,
                                                                       building_names_cooling,
                                                                       building_names_electricity,
                                                                       DHN_barcode,
                                                                       DCN_barcode,
                                                                       district_heating_network,
                                                                       district_cooling_network,
                                                                       technologies_heating_allowed,
                                                                       technologies_cooling_allowed,
                                                                       weather_features,
                                                                       )

    # DISTRICT HEATING NETWORK
    print("DISTRICT HEATING OPERATION")
    district_heating_fixed_costs, \
    district_heating_generation_dispatch, \
    district_heating_electricity_requirements_dispatch, \
    district_heating_fuel_requirements_dispatch, \
    district_heating_capacity_installed = heating_main.district_heating_network(locator,
                                                                                master_to_slave_vars,
                                                                                config,
                                                                                network_features,
                                                                                )

    # DISTRICT COOLING NETWORK:
    print("DISTRICT COOLING OPERATION")
    district_cooling_fixed_costs, \
    district_cooling_generation_dispatch, \
    district_cooling_electricity_requirements_dispatch, \
    district_cooling_fuel_requirements_dispatch, \
    district_cooling_capacity_installed = cooling_main.district_cooling_network(locator,
                                                                                master_to_slave_vars,
                                                                                config,
                                                                                prices,
                                                                                network_features)

    # ELECTRICITY CONSUMPTION CALCULATIONS
    print("DISTRICT ELECTRICITY GRID OPERATION")
    district_electricity_fixed_costs, \
    district_electricity_dispatch, \
    district_electricity_demands, \
    district_electricity_capacity_installed = electricity_main.electricity_calculations_of_all_buildings(locator,
                                                                                                         master_to_slave_vars,
                                                                                                         district_heating_generation_dispatch,
                                                                                                         district_heating_electricity_requirements_dispatch,
                                                                                                         district_cooling_generation_dispatch,
                                                                                                         district_cooling_electricity_requirements_dispatch)

    # electricity_main.extract_fuels_demand_buildings(master_to_slave_vars, building_names_all, locator)
    print("DISTRICT ENERGY SYSTEM - COSTS, PRIMARY ENERGY AND EMISSIONS OF CONNECTED BUILDINGS")
    buildings_connected_costs, \
    buildings_connected_emissions = cost_model.buildings_connected_costs_and_emissions(district_heating_fixed_costs,
                                                                                       district_cooling_fixed_costs,
                                                                                       district_electricity_fixed_costs,
                                                                                       district_electricity_dispatch,
                                                                                       district_heating_fuel_requirements_dispatch,
                                                                                       district_cooling_fuel_requirements_dispatch,
                                                                                       district_electricity_demands,
                                                                                       prices,
                                                                                       lca)

    print("DISTRICT ENERGY SYSTEM - COSTS, PRIMARY ENERGY AND EMISSIONS OF DISCONNECTED BUILDINGS")
    buildings_disconnected_costs, \
    buildings_disconnected_emissions, \
    buildings_disconnected_heating_capacities, \
    buildings_disconnected_cooling_capacities = cost_model.buildings_disconnected_costs_and_emissions(
        building_names_heating,
        building_names_cooling,
        locator,
        master_to_slave_vars)

    print("AGGREGATING RESULTS")
    TAC_sys_USD, GHG_sys_tonCO2, performance_totals = summarize_results_individual(buildings_connected_costs,
                                                                                   buildings_connected_emissions,
                                                                                   buildings_disconnected_costs,
                                                                                   buildings_disconnected_emissions)


    print ('Total TAC in USD = ' + str(TAC_sys_USD))
    print ('Total GHG emissions in tonCO2-eq = ' + str(GHG_sys_tonCO2))

    return TAC_sys_USD, \
           GHG_sys_tonCO2, \
           buildings_connected_costs, \
           buildings_connected_emissions, \
           buildings_disconnected_costs, \
           buildings_disconnected_emissions, \
           district_heating_generation_dispatch, \
           district_cooling_generation_dispatch, \
           district_electricity_dispatch, \
           district_electricity_demands, \
           performance_totals, \
           building_connectivity_dict, \
           district_heating_capacity_installed, \
           district_cooling_capacity_installed, \
           district_electricity_capacity_installed, \
           buildings_disconnected_heating_capacities, \
           buildings_disconnected_cooling_capacities

