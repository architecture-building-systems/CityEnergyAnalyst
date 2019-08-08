"""
Evaluation function of an individual

"""
from __future__ import division

import pandas as pd

from cea.optimization.master import cost_model
from cea.optimization.master import master_to_slave as master
from cea.optimization.master.generation import individual_to_barcode
from cea.optimization.master.performance_aggregation import summarize_results_individual
from cea.optimization.slave import cooling_main
from cea.optimization.slave import electricity_main
from cea.optimization.slave import heating_main
from cea.optimization.slave import natural_gas_main


# +++++++++++++++++++++++++++++++++++++
# Main objective function evaluation
# ++++++++++++++++++++++++++++++++++++++

def evaluation_main(individual, building_names, locator, network_features, config, prices, lca,
                    ind_num, gen, column_names_individual,
                    column_names_buildings_heating,
                    column_names_buildings_cooling,
                    building_names_heating,
                    building_names_cooling,
                    building_names_electricity,
                    district_heating_network,
                    district_cooling_network,
                    ):
    """
    This function evaluates an individual

    :param individual: list with values of the individual
    :param column_names_buildings_all: list with names of buildings
    :param locator: locator class
    :param solar_features: solar features call to class
    :param network_features: network features call to class
    :param gv: global variables class
    :param optimization_constants: class containing constants used in optimization
    :param config: configuration file
    :param prices: class of prices used in optimization
    :type individual: list
    :type column_names_buildings_all: list
    :type locator: string
    :type solar_features: class
    :type network_features: class
    :type gv: class
    :type optimization_constants: class
    :type config: class
    :type prices: class
    :return: Resulting values of the objective function. costs, CO2, prim
    :rtype: tuple

    """

    # CREATE THE INDIVIDUAL BARCODE AND INDIVIDUAL WITH HER COLUMN NAME AS A DICT
    DHN_barcode, DCN_barcode, individual_with_name_dict = individual_to_barcode(individual,
                                                                                column_names_individual,
                                                                                column_names_buildings_heating,
                                                                                column_names_buildings_cooling)

    print("EVALUATING THE NEXT SYSTEM OPTION/INDIVIDUAL")
    print(individual_with_name_dict)

    # CREATE CLASS AND PASS KEY CHARACTERISTICS OF INDIVIDUAL
    # THIS CLASS SHOULD CONTAIN ALL VARIABLES THAT MAKE AN INDIVIDUAL CONFIGURATION
    master_to_slave_vars = master.export_data_to_master_to_slave_class(locator,
                                                                       config,
                                                                       gen,
                                                                       ind_num,
                                                                       individual_with_name_dict,
                                                                       building_names,
                                                                       building_names_heating,
                                                                       building_names_cooling,
                                                                       building_names_electricity,
                                                                       DHN_barcode,
                                                                       DCN_barcode,
                                                                       district_heating_network,
                                                                       district_cooling_network)
    # INITIALIZE DICTS STORING PERFORMANCE DATA
    performance_heating = {}
    performance_cooling = {}
    storage_dispatch = {}
    heating_dispatch = {}
    cooling_dispatch = {}

    # DISTRICT HEATING NETWORK
    if master_to_slave_vars.DHN_exists:
        print("CALCULATING PERFORMANCE OF HEATING NETWORK CONNECTED BUILDINGS")
        performance_heating, heating_dispatch = heating_main.district_heating_network(locator,
                                                                                      master_to_slave_vars,
                                                                                      config, prices,
                                                                                      lca,
                                                                                      network_features,
                                                                                      )

    # DISTRICT COOLING NETWORK:
    if master_to_slave_vars.DCN_exists:
        print("CALCULATING PERFORMANCE OF COOLING NETWORK CONNECTED BUILDINGS")
        reduced_timesteps_flag = False
        performance_cooling, cooling_dispatch = cooling_main.district_cooling_network(locator,
                                                                                      master_to_slave_vars,
                                                                                      network_features,
                                                                                      prices,
                                                                                      lca,
                                                                                      config,
                                                                                      reduced_timesteps_flag,
                                                                                      district_heating_network)

    # DISCONNECTED BUILDINGS
    print("CALCULATING PERFORMANCE OF DISCONNECTED BUILDNGS")
    performance_disconnected = cost_model.add_disconnected_costs(building_names_heating,
                                                                 building_names_cooling,
                                                                 locator,
                                                                 master_to_slave_vars)

    # ELECTRICITY CONSUMPTION CALCULATIONS
    print("CALCULATING PERFORMANCE OF ELECTRICITY CONSUMPTION")
    performance_electricity, \
    electricity_dispatch, \
    electricity_requirements, \
    performance_heating, \
    performance_cooling, = electricity_main.electricity_calculations_of_all_buildings(locator,
                                                                                      master_to_slave_vars,
                                                                                      lca,
                                                                                      performance_heating,
                                                                                      performance_cooling,
                                                                                      heating_dispatch,
                                                                                      cooling_dispatch)

    # NATURAL GAS
    print("CALCULATING PERFORMANCE OF NATURAL GAS CONSUMPTION")
    fuels_dispatch = natural_gas_main.fuel_imports(master_to_slave_vars, heating_dispatch,
                                                   cooling_dispatch)

    print("AGGREGATING RESULTS")
    TAC_sys_USD, GHG_sys_tonCO2, PEN_sys_MJoil, performance_totals = summarize_results_individual(master_to_slave_vars,
                                                                                                  performance_heating,
                                                                                                  performance_cooling,
                                                                                                  performance_disconnected,
                                                                                                  performance_electricity)

    print("SAVING RESULTS TO DISK")
    save_results(master_to_slave_vars, locator, performance_heating, performance_cooling, performance_electricity,
                 performance_disconnected, storage_dispatch, heating_dispatch, cooling_dispatch, electricity_dispatch,
                 electricity_requirements, fuels_dispatch, performance_totals)

    # Converting costs into float64 to avoid longer values
    print ('Total TAC in USD = ' + str(TAC_sys_USD))
    print ('Total GHG emissions in tonCO2-eq = ' + str(GHG_sys_tonCO2))
    print ('Total PEN non-renewable in MJoil ' + str(PEN_sys_MJoil) + "\n")

    return TAC_sys_USD, GHG_sys_tonCO2, PEN_sys_MJoil


def save_results(master_to_slave_vars, locator, performance_heating, performance_cooling, performance_electricity,
                 performance_disconnected, storage_dispatch, heating_dispatch, cooling_dispatch, electricity_dispatch,
                 electricity_requirements,
                 fuels_dispatch, performance_totals):
    # put data inside a list, otherwise pandas cannot save it
    for column in performance_disconnected.keys():
        performance_disconnected[column] = [performance_disconnected[column]]
    for column in performance_cooling.keys():
        performance_cooling[column] = [performance_cooling[column]]
    for column in performance_heating.keys():
        performance_heating[column] = [performance_heating[column]]
    for column in performance_electricity.keys():
        performance_electricity[column] = [performance_electricity[column]]
    for column in performance_totals.keys():
        performance_totals[column] = [performance_totals[column]]

    # export all including performance heating and performance cooling since we changed them
    pd.DataFrame(performance_disconnected).to_csv(
        locator.get_optimization_slave_disconnected_performance(master_to_slave_vars.individual_number,
                                                                master_to_slave_vars.generation_number),
        index=False)

    pd.DataFrame(performance_cooling).to_csv(
        locator.get_optimization_slave_cooling_performance(master_to_slave_vars.individual_number,
                                                           master_to_slave_vars.generation_number),
        index=False)

    pd.DataFrame(performance_heating).to_csv(
        locator.get_optimization_slave_heating_performance(master_to_slave_vars.individual_number,
                                                           master_to_slave_vars.generation_number),
        index=False)

    pd.DataFrame(performance_electricity).to_csv(
        locator.get_optimization_slave_electricity_performance(master_to_slave_vars.individual_number,
                                                               master_to_slave_vars.generation_number),
        index=False)

    pd.DataFrame(performance_totals).to_csv(
        locator.get_optimization_slave_total_performance(master_to_slave_vars.individual_number,
                                                         master_to_slave_vars.generation_number),
        index=False)

    # add date and plot
    DATE = master_to_slave_vars.date
    storage_dispatch['DATE'] = DATE
    electricity_dispatch['DATE'] = DATE
    cooling_dispatch['DATE'] = DATE
    heating_dispatch['DATE'] = DATE
    fuels_dispatch['DATE'] = DATE
    electricity_requirements['DATE'] = DATE

    pd.DataFrame(storage_dispatch).to_csv(locator.get_optimization_slave_storage_operation_data(
        master_to_slave_vars.individual_number,
        master_to_slave_vars.generation_number), index=False)

    pd.DataFrame(electricity_requirements).to_csv(locator.get_optimization_slave_electricity_requirements_data(
        master_to_slave_vars.individual_number,
        master_to_slave_vars.generation_number), index=False)

    pd.DataFrame(electricity_dispatch).to_csv(locator.get_optimization_slave_electricity_activation_pattern(
        master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)

    pd.DataFrame(cooling_dispatch).to_csv(
        locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number),
        index=False)

    pd.DataFrame(heating_dispatch).to_csv(
        locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number),
        index=False)

    pd.DataFrame(fuels_dispatch).to_csv(
        locator.get_optimization_slave_natural_gas_imports(master_to_slave_vars.individual_number,
                                                           master_to_slave_vars.generation_number), index=False)
