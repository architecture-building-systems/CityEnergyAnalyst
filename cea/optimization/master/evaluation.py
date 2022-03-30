"""
Evaluation function of an individual

"""

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

    :param individual: Input individual
    :param building_names_all: names of buildings in the analysed district
    :param locator: paths to cea input files
    :param network_features: characteristic parameters (pumping energy, mass flow rate, thermal losses & piping cost)
                             of the district cooling/heating network
    :param weather_features: weather data for the selected location (ambient temperature, ground temperature etc.)
    :param config: configurations of cea
    :param prices: catalogue of energy prices (e.g. for natural gas, electricity, biomass etc.)
    :param lca: catalogue of emission intensities of energy carriers
    :param individual_number: unique identifier of the individual in that generation
    :param generation_number: unique identifier of the generation in this optimization run
    :param column_names_individual: description of the parameter list in the individual
    :param column_names_buildings_heating: names of all buildings that are connected to a district heating system
    :param column_names_buildings_cooling: names of all buildings that are connected to a district cooling system
    :param building_names_heating: names of all buildings that have a heating load (space heat, hot water etc.)
    :param building_names_cooling: names of all buildings that have a cooling load
    :param building_names_electricity: names of all buildings that have an electricity load
    :param district_heating_network: indicator defining if district heating networks should be analyzed
    :param district_cooling_network: indicator defining if district heating networks should be analyzed
    :param technologies_heating_allowed: district heating technologies to be considered in the optimization
    :param technologies_cooling_allowed: district cooling technologies to be considered in the optimization

    :type individual: list
    :type individual_number: int
    :type generation_number: int
    :type building_names_all: list of str
    :type column_names_buildings_heating: list of str
    :type column_names_buildings_cooling: list of str
    :type building_names_heating: list of str
    :type building_names_cooling: list of str
    :type building_names_electricity: list of str
    :type locator: cea.inputlocator.InputLocator class object
    :type network_features: cea.optimization.distribution.network_optimization_features.NetworkOptimizationFeatures
                            class object
    :type weather_features: cea.optimization.preprocessing.preprocessing_main.WeatherFeatures class object
    :type config: cea.config.Configuration class object
    :type prices: cea.optimization.prices.Prices class object
    :type lca: cea.optimization.lca_calculations.LcaCalculations class object
    :type district_heating_network: bool
    :type district_cooling_network: bool
    :type technologies_heating_allowed: list of str
    :type technologies_cooling_allowed: list of str
    :type column_names_individual: list of str

    :return: Resulting values of the objective function. costs, CO2, prim
    :rtype: tuple
    """

    # CREATE THE INDIVIDUAL BARCODE AND INDIVIDUAL WITH HER COLUMN NAME AS A DICT
    DHN_barcode, DCN_barcode,\
    individual_with_name_dict, building_connectivity_dict = individual_to_barcode(individual,
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
                                                                                network_features)

    # ELECTRICITY CONSUMPTION CALCULATIONS
    print("DISTRICT ELECTRICITY GRID OPERATION")
    district_electricity_fixed_costs, \
    district_electricity_dispatch, \
    district_electricity_demands, \
    district_electricity_capacity_installed = electricity_main.electricity_calculations_of_all_buildings(
        locator,
        master_to_slave_vars,
        district_heating_generation_dispatch,
        district_heating_electricity_requirements_dispatch,
        district_cooling_generation_dispatch,
        district_cooling_electricity_requirements_dispatch)

    # electricity_main.extract_fuels_demand_buildings(master_to_slave_vars, building_names_all, locator)
    print("DISTRICT ENERGY SYSTEM - COSTS, PRIMARY ENERGY AND EMISSIONS OF CONNECTED BUILDINGS")
    buildings_district_scale_costs, \
    buildings_district_scale_emissions = cost_model.buildings_district_scale_costs_and_emissions(
        district_heating_fixed_costs,
        district_cooling_fixed_costs,
        district_electricity_fixed_costs,
        district_electricity_dispatch,
        district_heating_fuel_requirements_dispatch,
        district_cooling_fuel_requirements_dispatch,
        district_electricity_demands,
        prices,
        lca)

    print("DISTRICT ENERGY SYSTEM - COSTS, PRIMARY ENERGY AND EMISSIONS OF DISCONNECTED BUILDINGS")
    buildings_building_scale_costs, \
    buildings_building_scale_emissions, \
    buildings_building_scale_heating_capacities, \
    buildings_building_scale_cooling_capacities = cost_model.buildings_building_scale_costs_and_emissions(
        building_names_heating,
        building_names_cooling,
        locator,
        master_to_slave_vars)

    print("AGGREGATING RESULTS")
    TAC_sys_USD, GHG_sys_tonCO2, performance_totals = summarize_results_individual(buildings_district_scale_costs,
                                                                                   buildings_district_scale_emissions,
                                                                                   buildings_building_scale_costs,
                                                                                   buildings_building_scale_emissions)

    print('Total TAC in USD = ' + str(TAC_sys_USD))
    print('Total GHG emissions in tonCO2-eq = ' + str(GHG_sys_tonCO2))

    return TAC_sys_USD, \
           GHG_sys_tonCO2, \
           buildings_district_scale_costs, \
           buildings_district_scale_emissions, \
           buildings_building_scale_costs, \
           buildings_building_scale_emissions, \
           district_heating_generation_dispatch, \
           district_cooling_generation_dispatch, \
           district_electricity_dispatch, \
           district_electricity_demands, \
           performance_totals, \
           building_connectivity_dict, \
           district_heating_capacity_installed, \
           district_cooling_capacity_installed, \
           district_electricity_capacity_installed, \
           buildings_building_scale_heating_capacities, \
           buildings_building_scale_cooling_capacities
