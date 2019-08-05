"""
Evaluation function of an individual

"""
from __future__ import division

import os

import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.optimization import slave_data
from cea.optimization.constants import *
from cea.optimization.master import cost_model
from cea.optimization.master import summarize_network
from cea.optimization.master.generation import individual_to_barcode
from cea.optimization.master.performance_aggregation import summarize_results_individual
from cea.optimization.slave import cooling_main
from cea.optimization.slave import electricity_main
from cea.optimization.slave import heating_main
from cea.optimization.slave import natural_gas_main
from cea.resources.geothermal import calc_ground_temperature
from cea.technologies import substation
from cea.utilities import epwreader


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

    # CREATE CLASS AND PASS KEY CHARACTERISTICS OF INDIVIDUAL
    # THIS CLASS SHOULD CONTAIN ALL VARIABLES THAT MAKE AN INDIVIDUAL CONFIGURATION
    master_to_slave_vars = export_data_to_master_to_slave_class(locator,
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
    performance_storage = {}
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
                 fuels_dispatch, performance_totals)

    # Converting costs into float64 to avoid longer values
    print ('Total TAC in USD = ' + str(TAC_sys_USD))
    print ('Total GHG emissions in tonCO2-eq = ' + str(GHG_sys_tonCO2))
    print ('Total PEN non-renewable in MJoil ' + str(PEN_sys_MJoil) + "\n")

    return TAC_sys_USD, GHG_sys_tonCO2, PEN_sys_MJoil


def save_results(master_to_slave_vars, locator, performance_heating, performance_cooling, performance_electricity,
                 performance_disconnected, storage_dispatch, heating_dispatch, cooling_dispatch, electricity_dispatch,
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
    pd.DataFrame(storage_dispatch).to_csv(locator.get_optimization_slave_storage_operation_data(
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


def export_data_to_master_to_slave_class(locator,
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
                                         district_cooling_network):
    # RECALCULATE THE NOMINAL LOADS FOR HEATING AND COOLING, INCL SOME NAMES OF FILES
    Q_cooling_nom_W, Q_heating_nom_W, \
    network_file_name_cooling, network_file_name_heating = extract_loads_individual(locator,
                                                                                    config,
                                                                                    individual_with_name_dict,
                                                                                    DCN_barcode,
                                                                                    DHN_barcode,
                                                                                    district_heating_network,
                                                                                    district_cooling_network,
                                                                                    building_names_heating,
                                                                                    building_names_cooling, )

    # CREATE MASTER TO SLAVE AND FILL-IN
    master_to_slave_vars = calc_master_to_slave_variables(locator, gen,
                                                          ind_num,
                                                          individual_with_name_dict,
                                                          building_names,
                                                          DHN_barcode,
                                                          DCN_barcode,
                                                          network_file_name_heating,
                                                          network_file_name_cooling,
                                                          Q_heating_nom_W,
                                                          Q_cooling_nom_W,
                                                          district_heating_network,
                                                          district_cooling_network,
                                                          building_names_heating,
                                                          building_names_cooling,
                                                          building_names_electricity,
                                                          )

    return master_to_slave_vars


def extract_loads_individual(locator,
                             config,
                             individual_with_name_dict,
                             DCN_barcode,
                             DHN_barcode,
                             district_heating_network,
                             district_cooling_network,
                             column_names_buildings_heating,
                             column_names_buildings_cooling):
    # local variables
    weather_file = config.weather
    network_depth_m = Z0
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    ground_temp = calc_ground_temperature(locator, T_ambient, depth_m=network_depth_m)

    # EVALUATE CASES TO CREATE A NETWORK OR NOT
    if district_heating_network:  # network exists
        if DHN_barcode.count("1") == len(column_names_buildings_heating):
            network_file_name_heating = "DH_Network_summary_result_" + hex(int(str(DHN_barcode), 2)) + ".csv"
            Q_DHNf_W = pd.read_csv(locator.get_optimization_network_results_summary('DH', DHN_barcode),
                                   usecols=["Q_DHNf_W"]).values
            Q_heating_max_W = Q_DHNf_W.max()
        elif DHN_barcode.count("1") == 0:  # no network at all
            network_file_name_heating = "DH_Network_summary_result_" + hex(int(str(DHN_barcode), 2)) + ".csv"
            Q_heating_max_W = 0
        else:
            network_file_name_heating = "DH_Network_summary_result_" + hex(int(str(DHN_barcode), 2)) + ".csv"
            if not os.path.exists(locator.get_optimization_network_results_summary('DH', DHN_barcode)):
                total_demand = createTotalNtwCsv("DH", DHN_barcode, locator, column_names_buildings_heating)
                num_total_buildings = len(column_names_buildings_heating)
                buildings_in_heating_network = total_demand.Name.values
                # Run the substation and distribution routines
                substation.substation_main_heating(locator,
                                                   total_demand,
                                                   buildings_in_heating_network,
                                                   DHN_barcode=DHN_barcode)
                summarize_network.network_main(locator,
                                               buildings_in_heating_network,
                                               ground_temp,
                                               num_total_buildings,
                                               "DH", DHN_barcode)

            Q_DHNf_W = pd.read_csv(locator.get_optimization_network_results_summary('DH', DHN_barcode),
                                   usecols=["Q_DHNf_W"]).values
            Q_heating_max_W = Q_DHNf_W.max()
    else:
        Q_heating_max_W = 0.0
        network_file_name_heating = ""

    if district_cooling_network:  # network exists
        if DCN_barcode.count("1") == len(column_names_buildings_cooling):
            network_file_name_cooling = "DC_Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"
            if individual_with_name_dict['HPServer'] == 1:
                # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
                Q_DCNf_W_no_data = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                               usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
                Q_DCNf_W_with_data = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                                 usecols=[
                                                     "Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values

                Q_DCNf_W = Q_DCNf_W_no_data + (
                        (Q_DCNf_W_with_data - Q_DCNf_W_no_data) * (individual_with_name_dict['HPShare']))

            else:
                Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                       usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
            Q_cooling_max_W = Q_DCNf_W.max()
        elif DCN_barcode.count("1") == 0:
            network_file_name_cooling = "DC_Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"
            Q_cooling_max_W = 0.0
        else:
            network_file_name_cooling = "DC_Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"

            if not os.path.exists(locator.get_optimization_network_results_summary('DC', DCN_barcode)):
                total_demand = createTotalNtwCsv("DC", DCN_barcode, locator, column_names_buildings_cooling)
                num_total_buildings = len(column_names_buildings_cooling)
                buildings_in_cooling_network = total_demand.Name.values

                # Run the substation and distribution routines
                substation.substation_main_cooling(locator, total_demand, buildings_in_cooling_network,
                                                   DCN_barcode=DCN_barcode)
                summarize_network.network_main(locator, buildings_in_cooling_network, ground_temp, num_total_buildings,
                                               'DC', DCN_barcode)

            Q_DCNf_W_no_data = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                           usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
            Q_DCNf_W_with_data = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                             usecols=[
                                                 "Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values

            # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            if district_heating_network and individual_with_name_dict['HPServer'] == 1:
                Q_DCNf_W = Q_DCNf_W_no_data + (
                        (Q_DCNf_W_with_data - Q_DCNf_W_no_data) * (individual_with_name_dict['HPShare']))
            else:
                Q_DCNf_W = Q_DCNf_W_with_data

            Q_cooling_max_W = Q_DCNf_W.max()
    else:
        Q_cooling_max_W = 0.0
        network_file_name_cooling = ""

    Q_heating_nom_W = Q_heating_max_W * (1 + Q_MARGIN_FOR_NETWORK)
    Q_cooling_nom_W = Q_cooling_max_W * (1 + Q_MARGIN_FOR_NETWORK)

    return Q_cooling_nom_W, Q_heating_nom_W, network_file_name_cooling, network_file_name_heating


def createTotalNtwCsv(network_type, DHN_barcode, locator, building_names):
    """
    Create and saves the total file for a specific DH or DC configuration
    to make the distribution routine possible
    :param indCombi: string of 0 and 1: 0 if the building is disconnected, 1 if connected
    :param locator: path to raw files
    :type indCombi: string
    :type locator: string
    :return: name of the total file
    :rtype: string
    """
    # obtain buildings which are in this network
    buildings_in_this_network_config = []
    for index, name in zip(DHN_barcode, building_names):
        if index == '1':
            buildings_in_this_network_config.append(name)

    # get total demand file fro selecte
    df = pd.read_csv(locator.get_total_demand())
    dfRes = df[df.Name.isin(buildings_in_this_network_config)]
    dfRes = dfRes.reset_index(drop=True)

    return dfRes


# +++++++++++++++++++++++++++++++++++
# Boundary conditions
# +++++++++++++++++++++++++++++
def calc_master_to_slave_variables(locator, gen,
                                   ind_num,
                                   individual_with_names_dict,
                                   building_names,
                                   DHN_barcode,
                                   DCN_barcode,
                                   network_file_name_heating,
                                   network_file_name_cooling,
                                   Q_heating_nom_W,
                                   Q_cooling_nom_W,
                                   district_heating_network,
                                   district_cooling_network,
                                   building_names_heating,
                                   building_names_cooling,
                                   building_names_electricity,
                                   ):
    """
    This function reads the list encoding a configuration and implements the corresponding
    for the slave routine's to use
    :param individual_with_names_dict: list with inidividual
    :param Q_heating_max_W:  peak heating demand
    :param locator: locator class
    :param gv: global variables class
    :type individual_with_names_dict: list
    :type Q_heating_max_W: float
    :type locator: string
    :type gv: class
    :return: master_to_slave_vars : class MasterSlaveVariables
    :rtype: class
    """

    # calculate local variables
    num_total_buildings = len(building_names)

    # initialise class storing dynamic variables transfered from master to slave optimization
    master_to_slave_vars = slave_data.SlaveData()

    # Store information aobut individual regarding the configuration of the network and curstomers connected
    if district_heating_network and DHN_barcode.count("1") > 0:
        master_to_slave_vars.DHN_exists = True
    if district_cooling_network and DCN_barcode.count("1") > 0:
        master_to_slave_vars.DCN_exists = True

    # store how many buildings are connected to district heating or cooling
    master_to_slave_vars.number_of_buildings_connected_heating = DHN_barcode.count("1")
    master_to_slave_vars.number_of_buildings_connected_cooling = DCN_barcode.count("1")

    # store the names of the buildings connected to district heating or district cooling
    master_to_slave_vars.buildings_connected_to_district_heating = calc_connected_names(building_names_heating,
                                                                                        DHN_barcode)
    master_to_slave_vars.buildings_connected_to_district_cooling = calc_connected_names(building_names_cooling,
                                                                                        DCN_barcode)

    # store the name of the file where the network configuration is stored
    master_to_slave_vars.network_data_file_heating = network_file_name_heating
    master_to_slave_vars.network_data_file_cooling = network_file_name_cooling

    # store the barcode which identifies which buildings are connected and disconencted
    master_to_slave_vars.DHN_barcode = DHN_barcode
    master_to_slave_vars.DCN_barcode = DCN_barcode

    # store the total number of buildings in the district (independent of district cooling or heating)
    master_to_slave_vars.num_total_buildings = num_total_buildings

    # store the name of all buildings in the district (independent of district cooling or heating)
    master_to_slave_vars.building_names_all = building_names

    # store the name used to didentified the individual (this helps to know where is inside)
    master_to_slave_vars.building_names_heating = building_names_heating
    master_to_slave_vars.building_names_cooling = building_names_cooling
    master_to_slave_vars.building_names_electricity = building_names_electricity
    master_to_slave_vars.individual_with_names_dict = individual_with_names_dict

    # Store the number of the individual and the generation to which it belongs
    master_to_slave_vars.individual_number = ind_num
    master_to_slave_vars.generation_number = gen

    # Store useful variables to know where to save the results of the individual
    master_to_slave_vars.date = pd.read_csv(locator.get_demand_results_file(building_names[0])).DATE.values

    # Store inforamtion about which units are activated
    master_to_slave_vars = master_to_slave_electrical_technologies(individual_with_names_dict, locator,
                                                                   master_to_slave_vars)

    if master_to_slave_vars.DHN_exists:
        master_to_slave_vars = master_to_slave_district_heating_technologies(Q_heating_nom_W,
                                                                             individual_with_names_dict, locator,
                                                                             master_to_slave_vars)

    if master_to_slave_vars.DCN_exists:
        master_to_slave_vars = master_to_slave_district_cooling_technologies(locator, Q_cooling_nom_W,
                                                                             individual_with_names_dict,
                                                                             master_to_slave_vars)

    return master_to_slave_vars


def master_to_slave_district_cooling_technologies(locator, Q_cooling_nom_W, individual_with_names_dict,
                                                  master_to_slave_vars):
    # COOLING SYSTEMS
    # Lake Cooling
    if individual_with_names_dict['FLake'] == 1 and LAKE_COOLING_ALLOWED is True:
        lake_potential = pd.read_csv(locator.get_lake_potential())
        Q_max_lake = (lake_potential['QLake_kW'] * 1000).max()
        master_to_slave_vars.Lake_cooling_on = 1
        master_to_slave_vars.Lake_cooling_size_W = min(individual_with_names_dict['FLake Share'] * Q_max_lake,
                                                       individual_with_names_dict['FLake Share'] * Q_cooling_nom_W)

    # VCC Cooling
    if individual_with_names_dict['VCC'] == 1 and VCC_ALLOWED is True:
        master_to_slave_vars.VCC_on = 1
        master_to_slave_vars.VCC_cooling_size_W = individual_with_names_dict['VCC Share'] * Q_cooling_nom_W
    # Absorption Chiller Cooling
    if individual_with_names_dict['ACH'] == 1 and ABSORPTION_CHILLER_ALLOWED is True:
        master_to_slave_vars.Absorption_Chiller_on = 1
        master_to_slave_vars.Absorption_chiller_size_W = individual_with_names_dict['ACH Share'] * Q_cooling_nom_W
    # Storage Cooling
    if individual_with_names_dict['Storage'] == 1 and STORAGE_COOLING_ALLOWED is True:
        if (individual_with_names_dict['VCC'] == 1 and VCC_ALLOWED is True) or \
                (individual_with_names_dict['ACH'] == 1 and ABSORPTION_CHILLER_ALLOWED is True):
            master_to_slave_vars.storage_cooling_on = 1
            master_to_slave_vars.Storage_cooling_size_W = individual_with_names_dict['Storage Share'] * Q_cooling_nom_W
            if master_to_slave_vars.Storage_cooling_size_W > STORAGE_COOLING_SHARE_RESTRICTION * Q_cooling_nom_W:
                master_to_slave_vars.Storage_cooling_size_W = STORAGE_COOLING_SHARE_RESTRICTION * Q_cooling_nom_W

    return master_to_slave_vars


def calc_connected_names(building_names, barcode):
    connected_buildings = []
    for name, index in zip(building_names, barcode):
        if index == '1':
            connected_buildings.append(name)
    return connected_buildings


def calc_available_area_solar(locator, buildings, share_allowed, technology):
    area_m2 = 0.0
    for building_name in buildings:
        solar_technology_potential = pd.read_csv(
            os.path.join(locator.get_potentials_solar_folder(), building_name + '_' + technology + '.csv'))
        area_m2 += solar_technology_potential['Area_'+technology+'_m2'][0]

    return area_m2 * share_allowed

def calc_available_area_solar_collectors(locator, buildings, share_allowed, technology):
    area_m2 = 0.0
    for building_name in buildings:
        solar_technology_potential = pd.read_csv(
            os.path.join(locator.get_potentials_solar_folder(), building_name + '_' + technology + '.csv'))
        area_m2 += solar_technology_potential['Area_SC_m2'][0]

    return area_m2 * share_allowed


def master_to_slave_district_heating_technologies(Q_heating_nom_W,
                                                  individual_with_names_dict,
                                                  locator,
                                                  master_to_slave_vars):
    if individual_with_names_dict['CHP/Furnace'] == 1 and FURNACE_ALLOWED == True:  # Wet-Biomass fired Furnace
        master_to_slave_vars.Furnace_on = 1
        master_to_slave_vars.Furnace_Q_max_W = individual_with_names_dict['CHP/Furnace Share'] * Q_heating_nom_W
        master_to_slave_vars.Furn_Moist_type = "wet"
    elif individual_with_names_dict['CHP/Furnace'] == 2 and CC_ALLOWED == True:  # NG-fired CHPFurnace
        master_to_slave_vars.CC_on = 1
        master_to_slave_vars.CC_GT_SIZE_W = individual_with_names_dict['CHP/Furnace Share'] * Q_heating_nom_W * 1.3
        # 1.3 is the conversion factor between the GT_Elec_size NG and Q_DHN
        master_to_slave_vars.gt_fuel = "NG"
    elif individual_with_names_dict['CHP/Furnace'] == 3 and FURNACE_ALLOWED == True:  # Dry-Biomass fired Furnace
        master_to_slave_vars.Furnace_on = 1
        master_to_slave_vars.Furnace_Q_max_W = individual_with_names_dict['CHP/Furnace Share'] * Q_heating_nom_W
        master_to_slave_vars.Furn_Moist_type = "dry"
    elif individual_with_names_dict['CHP/Furnace'] == 4 and CC_ALLOWED == True:  # Biogas-fired CHPFurnace
        master_to_slave_vars.CC_on = 1
        master_to_slave_vars.CC_GT_SIZE_W = individual_with_names_dict['CHP/Furnace Share'] * Q_heating_nom_W * 1.3
        # 1.3 is the conversion factor between the GT_Elec_size NG and Q_DHN
        master_to_slave_vars.gt_fuel = "BG"
    # Base boiler
    if individual_with_names_dict['BaseBoiler'] == 1:  # NG-fired boiler
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max_W = individual_with_names_dict['BaseBoiler Share'] * Q_heating_nom_W
        master_to_slave_vars.BoilerType = "NG"
    elif individual_with_names_dict['BaseBoiler'] == 2:  # BG-fired boiler
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max_W = individual_with_names_dict['BaseBoiler Share'] * Q_heating_nom_W
        master_to_slave_vars.BoilerType = "BG"
    # peak boiler
    if individual_with_names_dict['PeakBoiler'] == 1:  # BG-fired boiler
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max_W = individual_with_names_dict['PeakBoiler Share'] * Q_heating_nom_W
        master_to_slave_vars.BoilerPeakType = "NG"
    if individual_with_names_dict['PeakBoiler'] == 2:  # BG-fired boiler
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max_W = individual_with_names_dict['PeakBoiler Share'] * Q_heating_nom_W
        master_to_slave_vars.BoilerPeakType = "BG"
    # HPLake
    if individual_with_names_dict['HPLake'] == 1 and HP_LAKE_ALLOWED == True:
        lake_potential = pd.read_csv(locator.get_lake_potential())
        Q_max_lake = (lake_potential['QLake_kW'] * 1000).max()
        master_to_slave_vars.HP_Lake_on = 1
        master_to_slave_vars.HPLake_maxSize_W = min(individual_with_names_dict['HPLake Share'] * Q_max_lake,
                                                    individual_with_names_dict['HPLake Share'] * Q_heating_nom_W)
    # HPSewage
    if individual_with_names_dict['HPSewage'] == 1 and HP_SEW_ALLOWED == True:
        sewage_potential = pd.read_csv(locator.get_sewage_heat_potential())
        Q_max_sewage = (sewage_potential['Qsw_kW'] * 1000).max()
        master_to_slave_vars.HP_Sew_on = 1
        master_to_slave_vars.HPSew_maxSize_W = min(individual_with_names_dict['HPSewage Share'] * Q_max_sewage,
                                                   individual_with_names_dict['HPSewage Share'] * Q_heating_nom_W)
    # GHP
    if individual_with_names_dict['GHP'] == 1 and GHP_ALLOWED == True:
        ghp_potential = pd.read_csv(locator.get_geothermal_potential())
        Q_max_ghp = (ghp_potential['QGHP_kW'] * 1000).max()
        master_to_slave_vars.GHP_on = 1
        master_to_slave_vars.GHP_maxSize_W = min(individual_with_names_dict['GHP Share'] * Q_max_ghp,
                                                 individual_with_names_dict['GHP Share'] * Q_heating_nom_W)
    # HPServer
    if individual_with_names_dict['HPServer'] == 1 and DATACENTER_HEAT_RECOVERY_ALLOWED == True:
        master_to_slave_vars.WasteServersHeatRecovery = 1
        master_to_slave_vars.HPServer_maxSize_W = individual_with_names_dict['HPServer Share'] * Q_heating_nom_W

    # SOLAR TECHNOLOGIES
    if individual_with_names_dict['PVT'] == 1:
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = individual_with_names_dict['PVT Share']
        master_to_slave_vars.PVT_on = 1
        master_to_slave_vars.A_PVT_m2 = calc_available_area_solar(locator, buildings, share_allowed, 'PVT')
        master_to_slave_vars.PVT_share = share_allowed

    if individual_with_names_dict['SC_ET'] == 1:
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = individual_with_names_dict['SC_ET Share']
        master_to_slave_vars.SC_ET_on = 1
        master_to_slave_vars.A_SC_ET_m2 = calc_available_area_solar_collectors(locator, buildings, share_allowed, 'SC_ET')
        master_to_slave_vars.SC_ET_share = share_allowed

    if individual_with_names_dict['SC_FP'] == 1:
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = individual_with_names_dict['SC_FP Share']
        master_to_slave_vars.SC_FP_on = 1
        master_to_slave_vars.A_SC_FP_m2 = calc_available_area_solar_collectors(locator, buildings, share_allowed, "SC_FP")
        master_to_slave_vars.SC_FP_share = share_allowed

    return master_to_slave_vars


def master_to_slave_electrical_technologies(individual_with_names_dict,
                                            locator,
                                            master_to_slave_vars):
    # SOLAR TECHNOLOGIES
    if individual_with_names_dict['PV'] == 1:
        buildings = master_to_slave_vars.building_names_all
        share_allowed = individual_with_names_dict['PV Share']
        master_to_slave_vars.PV_on = 1
        master_to_slave_vars.A_PV_m2 = calc_available_area_solar(locator, buildings, share_allowed, 'PV')
        master_to_slave_vars.PV_share = share_allowed

    return master_to_slave_vars


def epsIndicator(frontOld, frontNew):
    """
    This function computes the epsilon indicator
    
    :param frontOld: Old Pareto front
    :type frontOld: list
    :param frontNew: New Pareto front
    :type frontNew: list

    :return: epsilon indicator between the old and new Pareto fronts
    :rtype: float

    """
    epsInd = 0
    firstValueAll = True

    for indNew in frontNew:
        tempEpsInd = 0
        firstValue = True

        for indOld in frontOld:
            (aOld, bOld, cOld) = indOld.fitness.values
            (aNew, bNew, cNew) = indNew.fitness.values
            compare = max(aOld - aNew, bOld - bNew, cOld - cNew)

            if firstValue:
                tempEpsInd = compare
                firstValue = False

            if compare < tempEpsInd:
                tempEpsInd = compare

        if firstValueAll:
            epsInd = tempEpsInd
            firstValueAll = False

        if tempEpsInd > epsInd:
            epsInd = tempEpsInd

    return epsInd
