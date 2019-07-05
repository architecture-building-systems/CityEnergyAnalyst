"""
Evaluation function of an individual

"""
from __future__ import division

import os

import numpy as np
import pandas as pd

import check
from cea.optimization import slave_data
from cea.optimization import supportFn
from cea.optimization.constants import *
from cea.optimization.master import cost_model
from cea.optimization.master import generation
from cea.optimization.master import summarize_network
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load
from cea.optimization.slave import cooling_main
from cea.optimization.slave import electricity_main
from cea.optimization.slave import heating_main
from cea.optimization.slave import natural_gas_main
from cea.optimization.slave.seasonal_storage import storage_main
from cea.resources.geothermal import calc_ground_temperature
from cea.technologies import substation
from cea.utilities import epwreader


# +++++++++++++++++++++++++++++++++++++
# Main objective function evaluation
# ++++++++++++++++++++++++++++++++++++++

def evaluation_main(individual, building_names, locator, solar_features, network_features, config, prices, lca,
                    ind_num, gen):
    """
    This function evaluates an individual

    :param individual: list with values of the individual
    :param building_names: list with names of buildings
    :param locator: locator class
    :param solar_features: solar features call to class
    :param network_features: network features call to class
    :param gv: global variables class
    :param optimization_constants: class containing constants used in optimization
    :param config: configuration file
    :param prices: class of prices used in optimization
    :type individual: list
    :type building_names: list
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

    # local variables
    district_heating_network = config.optimization.district_heating_network
    district_cooling_network = config.optimization.district_cooling_network
    num_total_buildings = len(building_names)

    # EVALUATE CONSTRAINTS = CHECK CONSISTENCY OF INDIVIDUAL
    individual = evaluate_constrains(individual, num_total_buildings, config, district_heating_network,
                                     district_cooling_network)

    # CREATE THE INDIVIDUAL BARCODE
    DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                     building_names)

    # CREATE CLASS AND PASS KEY CHACTERISTICS OF INDIVIDUAL
    # THIS CLASS SHOULD CONTAIN ALL VARIABLES THAT MAKE AN INDIVIDUAL CONFIGURATION
    master_to_slave_vars = export_data_to_master_to_slave_class(locator, gen, individual, ind_num, building_names,
                                                                num_total_buildings,
                                                                DHN_barcode, DCN_barcode, DHN_configuration,
                                                                DCN_configuration, config)

    # INTITIALIZE OBJECTIVE FUNCTIONS =  costs, CO2 and primary energy
    total_costs_df = {}
    total_emissions_df = {}
    total_energy_df = {}
    costs_USD = 0
    GHG_tonCO2 = 0
    PEN_MJoil = 0

    # THERMAL STORAGE
    print("CALCULATING ECOLOGICAL COSTS OF SEASONAL STORAGE - DUE TO OPERATION (IF ANY)")
    costs_storage_USD, GHG_storage_tonCO2, PEN_storage_MJoil = storage_main.storage_optimization(locator,
                                                                                                 master_to_slave_vars,
                                                                                                 lca, prices, config)

    costs_USD += costs_storage_USD
    GHG_tonCO2 += GHG_storage_tonCO2
    PEN_MJoil += PEN_storage_MJoil

    # DISTRICT HEATING NETWORK
    costs_heating_USD = 0.0
    PEN_heating_MJoil = 0.0
    GHG_heating_tonCO2 = 0.0
    if district_heating_network:
        print("CALCULATING PERFROMANCE OF HEATING NETWORK - CONNECTED BUILDINGS")
        if DHN_barcode.count("1") > 0:
            (costs_heating_USD, GHG_tonCO2, PEN_heating_MJoil, Q_heating_uncovered_design_W,
             Q_heating_uncovered_annual_W) = heating_main.heating_calculations_of_DH_buildings(locator,
                                                                                               master_to_slave_vars,
                                                                                               config, prices, lca,
                                                                                               solar_features,
                                                                                               network_features)
        costs_USD += costs_heating_USD
        GHG_tonCO2 += GHG_heating_tonCO2
        PEN_MJoil += PEN_heating_MJoil

    # DISTRICT COOLING NETWORK
    costs_cooling_USD = 0.0
    GHG_cooling_tonCO2 = 0.0
    PEN_cooling_MJoil = 0.0
    if district_cooling_network:
        print("CALCULATING PERFORMANCE OF COOLING NETWORK - CONNECTED BUILDINGS")
        if DCN_barcode.count("1") > 0:
            reduced_timesteps_flag = False
            (costs_cooling_USD, GHG_cooling_tonCO2, PEN_cooling_MJoil) \
                = cooling_main.cooling_calculations_of_DC_buildings(locator,
                                                                    master_to_slave_vars,
                                                                    network_features,
                                                                    prices,
                                                                    lca,
                                                                    config,
                                                                    reduced_timesteps_flag, district_cooling_network,
                                                                    district_cooling_network)
        costs_USD += costs_cooling_USD
        GHG_tonCO2 += GHG_cooling_tonCO2
        PEN_MJoil += PEN_cooling_MJoil

    # ELECTRICITY CONSUMPTION CALCULATIONS
    print("CALCULATING PERFORMANCE OF ELECTRICITY CONSUMPTION")
    (costs_electricity_USD, GHG_electricity_tonCO2,
     PEN_electricity_MJoil) = electricity_main.electricity_calculations_of_all_buildings(DHN_barcode,
                                                                                         DCN_barcode,
                                                                                         locator,
                                                                                         master_to_slave_vars,
                                                                                         lca,
                                                                                         district_heating_network,
                                                                                         district_cooling_network)
    costs_USD += costs_electricity_USD
    GHG_tonCO2 += GHG_electricity_tonCO2
    PEN_MJoil += PEN_electricity_MJoil

    # Natural Gas Import Calculations. Prices, GHG and PEN are already included in the various sections.
    # This is to save the files for further processing and plots
    natural_gas_main.natural_gas_imports(master_to_slave_vars, locator, district_cooling_network,
                                         district_cooling_network)

    # DISCONNECTED BUILDINGS
    print("CALCULATING PERFORMANCE OF DISCONNECTED BUILDNGS")
    (costs_additional_USD, GHG_additional_tonCO2,
     PEN_additional_MJoil) = cost_model.add_disconnected_costs(building_names, locator, master_to_slave_vars)

    costs_USD += costs_additional_USD
    GHG_tonCO2 += GHG_additional_tonCO2
    PEN_MJoil += PEN_additional_MJoil

    # Converting costs into float64 to avoid longer values
    costs_USD = np.float64(costs_USD)
    GHG_tonCO2 = np.float64(GHG_tonCO2)
    PEN_MJoil = np.float64(PEN_MJoil)

    print ('Total TAC in USD = ' + str(costs_USD))
    print ('Total GHG emissions in tonCO2-eq = ' + str(GHG_tonCO2))
    print ('Total PEN emissions in MJoil ' + str(PEN_MJoil) + "\n")

    # TODO:CALCULATE CAPEX TOTAL, OPEX TOTAL and RENEWABLE ERNGY SHARE (to be used in multicriteria.

    return costs_USD, GHG_tonCO2, PEN_MJoil, master_to_slave_vars, individual


def export_data_to_master_to_slave_class(locator, gen, individual, ind_num, building_names, num_total_buildings,
                                         DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration, config):
    # RECALCULATE THE NOMINAL LOADS FOR HEATING AND COOLING, INCL SOME NAMES OF FILES
    Q_cooling_nom_W, Q_heating_nom_W, \
    network_file_name_cooling, network_file_name_heating = extract_capacities_from_individual(locator, individual,
                                                                                              DCN_barcode,
                                                                                              DCN_configuration,
                                                                                              DHN_barcode,
                                                                                              DHN_configuration,
                                                                                              config,
                                                                                              num_total_buildings)

    # MODIFY EXTRA CONSTRAINT
    try:
        check.GHPCheck(individual, locator, Q_heating_nom_W, building_names)
    except:
        print "No GHP constraint check possible \n"

    # CREATE MASTER TO SLAVE AND FILL-IN
    master_to_slave_vars = calc_master_to_slave_variables(gen,
                                                          ind_num,
                                                          individual,
                                                          building_names,
                                                          num_total_buildings,
                                                          DHN_barcode,
                                                          DCN_barcode,
                                                          DHN_configuration,
                                                          DCN_configuration,
                                                          network_file_name_heating,
                                                          network_file_name_cooling,
                                                          Q_heating_nom_W,
                                                          Q_cooling_nom_W)

    return master_to_slave_vars


def extract_capacities_from_individual(locator, individual, DCN_barcode, DCN_configuration, DHN_barcode,
                                       DHN_configuration, config, num_total_buildings):
    # local variables
    weather_file = config.weather
    network_depth_m = Z0
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    ground_temp = calc_ground_temperature(locator, config, T_ambient, depth_m=network_depth_m)

    # EVALUATE CASES TO CREATE A NETWORK OR NOT
    if DHN_barcode.count("1") == num_total_buildings:
        network_file_name_heating = "DH_Network_summary_result_all.csv"
        Q_DHNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('DH', 'all'),
                               usecols=["Q_DHNf_W"]).values
        Q_heating_max_W = Q_DHNf_W.max()
    elif DHN_barcode.count("1") == 0:  # no network at all
        network_file_name_heating = "DH_Network_summary_result_all.csv"
        Q_heating_max_W = 0
    else:
        network_file_name_heating = "DH_Network_summary_result_" + hex(int(str(DHN_barcode), 2)) + ".csv"
        if not os.path.exists(locator.get_optimization_network_results_summary('DH', DHN_barcode)):
            total_demand = supportFn.createTotalNtwCsv("DH", DHN_barcode, locator)
            buildings_in_heating_network = total_demand.Name.values
            # Run the substation and distribution routines
            substation.substation_main_heating(locator, total_demand, buildings_in_heating_network, DHN_configuration,
                                               Flag=True)
            summarize_network.network_main(locator, buildings_in_heating_network, ground_temp, num_total_buildings,
                                           "DH", DHN_barcode)

        Q_DHNf_W = pd.read_csv(locator.get_optimization_network_results_summary('DH', DHN_barcode),
                               usecols=["Q_DHNf_W"]).values
        Q_heating_max_W = Q_DHNf_W.max()

    if DCN_barcode.count("1") == num_total_buildings:
        network_file_name_cooling = "DC_Network_summary_result_all.csv"
        if individual[
            N_HEAT * 2] == 1:  # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('DC', 'all'),
                                   usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
        else:
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('DC', 'all'),
                                   usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
        Q_cooling_max_W = Q_DCNf_W.max()
    elif DCN_barcode.count("1") == 0:
        network_file_name_cooling = "DC_Network_summary_result_all.csv"
        Q_cooling_max_W = 0
    else:
        network_file_name_cooling = "DC_Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"

        if not os.path.exists(locator.get_optimization_network_results_summary('DC', DCN_barcode)):
            total_demand = supportFn.createTotalNtwCsv("DC", DCN_barcode, locator)
            buildings_in_cooling_network = total_demand.Name.values

            # Run the substation and distribution routines
            substation.substation_main_cooling(locator, total_demand, buildings_in_cooling_network, DCN_configuration,
                                               Flag=True)
            summarize_network.network_main(locator, buildings_in_cooling_network, ground_temp, num_total_buildings,
                                           'DC', DCN_barcode)

        if individual[
            N_HEAT * 2] == 1:  # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                   usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
        else:
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                   usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
        Q_cooling_max_W = Q_DCNf_W.max()
    Q_heating_nom_W = Q_heating_max_W * (1 + Q_MARGIN_FOR_NETWORK)
    Q_cooling_nom_W = Q_cooling_max_W * (1 + Q_MARGIN_FOR_NETWORK)
    return Q_cooling_nom_W, Q_heating_nom_W, network_file_name_cooling, network_file_name_heating


# +++++++++++++++++++++++++++++++++++
# Boundary conditions
# +++++++++++++++++++++++++++++


def evaluate_constrains(individual, nBuildings, config, district_heating_network, district_cooling_network):
    """
    This function rejects individuals out of the bounds of the problem
    It can also generate a new individual, to replace the rejected individual
    :param individual: individual sent for checking
    :param nBuildings: number of buildings
    :type individual: list
    :type nBuildings: int
    :type gv: class
    :return: new individual if necessary
    :rtype: list
    """
    valid = True

    for i in range(N_HEAT):
        if individual[2 * i] > 0 and individual[2 * i + 1] < 0.01:
            oldValue = individual[2 * i + 1]
            shareGain = oldValue - 0.01
            individual[2 * i + 1] = 0.01

            for rank in range(N_HEAT):
                if individual[2 * rank] > 0 and i != rank:
                    individual[2 * rank + 1] += individual[2 * rank + 1] / (1 - oldValue) * shareGain

        elif individual[2 * i] == 0:
            individual[2 * i + 1] = 0

    frank = N_HEAT * 2 + N_HR
    for i in range(N_SOLAR):
        if individual[frank + 2 * i + 1] < 0:
            individual[frank + 2 * i + 1] = 0

    # CHECK DISTRICT HEATING PLANTS
    sharePlants = 0
    for i in range(N_HEAT):
        sharePlants += individual[2 * i + 1]
    if sharePlants > 1.0 and district_heating_network:
        valid = False

    # CHECK RANGE OF SOLAR
    shareSolar = 0
    nSol = 0
    for i in range(N_SOLAR):
        nSol += individual[frank + 2 * i]
        shareSolar += individual[frank + 2 * i + 1]
    if nSol > 0.0 and shareSolar > 1.0:
        valid = False

    # CHECK COOLING NETWORK
    if district_cooling_network:  # This is a temporary fix, need to change it in an elaborate method
        for i in range(N_SOLAR - 1):
            solar = i + 1
            individual[2 * N_HEAT + N_HR + 2 * solar] = 0
            individual[2 * N_HEAT + N_HR + 2 * solar + 1] = 0

    heating_part = 2 * N_HEAT + N_HR + 2 * N_SOLAR + INDICES_CORRESPONDING_TO_DHN
    for i in range(N_COOL):
        if individual[heating_part + 2 * i] > 0 and individual[heating_part + 2 * i + 1] < 0.01:
            oldValue = individual[heating_part + 2 * i + 1]
            shareGain = oldValue - 0.01
            individual[heating_part + 2 * i + 1] = 0.01

            for rank in range(N_COOL):
                if individual[heating_part + 2 * rank] > 0 and i != rank:
                    individual[heating_part + 2 * rank + 1] += individual[heating_part + 2 * rank + 1] / (
                            1 - oldValue) * shareGain
        elif individual[heating_part + 2 * i] == 0:
            individual[heating_part + 2 * i + 1] = 0

    # CHECK COOLING PLANTS
    sharePlants = 0
    for i in range(N_COOL):
        sharePlants += individual[heating_part + 2 * i + 1]
    if sharePlants > 1.0 and district_cooling_network:
        valid = False

    # CHECK IF AT THE END OF THE PROBLEM THE FLAG TURNED INTO NOT VALID
    if not valid:
        newInd = generation.generate_main(nBuildings, config)
        L = (N_HEAT + N_SOLAR) * 2 + N_HR
        for i in range(L):
            individual[i] = newInd[i]

    return individual


def calc_master_to_slave_variables(gen,
                                   ind_num,
                                   individual,
                                   building_names,
                                   num_total_buildings,
                                   DHN_barcode,
                                   DCN_barcode,
                                   DHN_configuration,
                                   DCN_configuration,
                                   network_file_name_heating,
                                   network_file_name_cooling,
                                   Q_heating_nom_W,
                                   Q_cooling_nom_W):
    """
    This function reads the list encoding a configuration and implements the corresponding
    for the slave routine's to use
    :param individual: list with inidividual
    :param Q_heating_max_W:  peak heating demand
    :param locator: locator class
    :param gv: global variables class
    :type individual: list
    :type Q_heating_max_W: float
    :type locator: string
    :type gv: class
    :return: master_to_slave_vars : class MasterSlaveVariables
    :rtype: class
    """
    # initialise class storing dynamic variables transfered from master to slave optimization
    master_to_slave_vars = slave_data.SlaveData()
    configkey = "".join(str(e)[0:4] for e in individual)
    configkey = configkey[:-2 * len(DHN_barcode)] + hex(int(str(DHN_barcode), 2)) + hex(int(str(DCN_barcode), 2))

    master_to_slave_vars.configKey = configkey
    master_to_slave_vars.number_of_buildings_connected_heating = DHN_barcode.count("1")
    master_to_slave_vars.number_of_buildings_connected_cooling = DCN_barcode.count("1")
    master_to_slave_vars.individual_number = ind_num
    master_to_slave_vars.generation_number = gen
    master_to_slave_vars.num_total_buildings = num_total_buildings
    master_to_slave_vars.building_names = building_names
    master_to_slave_vars.network_data_file_heating = network_file_name_heating
    master_to_slave_vars.network_data_file_cooling = network_file_name_cooling
    master_to_slave_vars.DHN_barcode = DHN_barcode
    master_to_slave_vars.DCN_barcode = DCN_barcode
    master_to_slave_vars.DHN_supplyunits = DHN_configuration
    master_to_slave_vars.DCN_supplyunits = DCN_configuration

    # Heating systems
    # CHP units with NG & furnace with biomass wet
    if individual[0] == 1 or individual[0] == 3:
        if FURNACE_ALLOWED == True:
            master_to_slave_vars.Furnace_on = 1
            master_to_slave_vars.Furnace_Q_max_W = max(individual[1] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
            master_to_slave_vars.Furn_Moist_type = "wet"
        elif CC_ALLOWED == True:
            master_to_slave_vars.CC_on = 1
            master_to_slave_vars.CC_GT_SIZE_W = max(individual[1] * Q_heating_nom_W * 1.3,
                                                    Q_MIN_SHARE * Q_heating_nom_W * 1.3)
            # 1.3 is the conversion factor between the GT_Elec_size NG and Q_DHN
            master_to_slave_vars.gt_fuel = "NG"

    # CHP units with BG& furnace with biomass dry
    if individual[0] == 2 or individual[0] == 4:
        if FURNACE_ALLOWED == True:
            master_to_slave_vars.Furnace_on = 1
            master_to_slave_vars.Furnace_Q_max_W = max(individual[1] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
            master_to_slave_vars.Furn_Moist_type = "dry"
        elif CC_ALLOWED == True:
            master_to_slave_vars.CC_on = 1
            master_to_slave_vars.CC_GT_SIZE_W = max(individual[1] * Q_heating_nom_W * 1.5,
                                                    Q_MIN_SHARE * Q_heating_nom_W * 1.5)
            # 1.5 is the conversion factor between the GT_Elec_size BG and Q_DHN
            master_to_slave_vars.gt_fuel = "BG"

    # Base boiler NG
    if individual[2] == 1:
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max_W = max(individual[3] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
        master_to_slave_vars.BoilerType = "NG"

    # Base boiler BG
    if individual[2] == 2:
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max_W = max(individual[3] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
        master_to_slave_vars.BoilerType = "BG"

    # peak boiler NG         
    if individual[4] == 1:
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max_W = max(individual[5] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
        master_to_slave_vars.BoilerPeakType = "NG"

    # peak boiler BG   
    if individual[4] == 2:
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max_W = max(individual[5] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
        master_to_slave_vars.BoilerPeakType = "BG"

    # lake - heat pump
    if individual[6] == 1 and HP_LAKE_ALLOWED == True:
        master_to_slave_vars.HP_Lake_on = 1
        master_to_slave_vars.HPLake_maxSize_W = max(individual[7] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)

    # sewage - heatpump    
    if individual[8] == 1 and HP_SEW_ALLOWED == True:
        master_to_slave_vars.HP_Sew_on = 1
        master_to_slave_vars.HPSew_maxSize_W = max(individual[9] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)

    # Gwound source- heatpump
    if individual[10] == 1 and GHP_ALLOWED == True:
        master_to_slave_vars.GHP_on = 1
        GHP_Qmax = max(individual[11] * Q_heating_nom_W, Q_MIN_SHARE * Q_heating_nom_W)
        master_to_slave_vars.GHP_number = GHP_Qmax / GHP_HMAX_SIZE

    # heat recovery servers and compresor
    irank = N_HEAT * 2
    master_to_slave_vars.WasteServersHeatRecovery = individual[irank]
    master_to_slave_vars.WasteCompressorHeatRecovery = 0

    # SOLAR SYSTEMS
    shareAvail = 1  # all buildings in the neighborhood are connected to the solar potential
    irank = N_HEAT * 2 + N_HR
    master_to_slave_vars.SOLAR_PART_PV = max(individual[irank] * individual[irank + 1] * shareAvail, 0)
    master_to_slave_vars.SOLAR_PART_PVT = max(individual[irank + 2] * individual[irank + 3] * shareAvail, 0)
    master_to_slave_vars.SOLAR_PART_SC_ET = max(individual[irank + 4] * individual[irank + 5] * shareAvail, 0)
    master_to_slave_vars.SOLAR_PART_SC_FP = max(individual[irank + 6] * individual[irank + 7] * shareAvail, 0)

    heating_block = N_HEAT * 2 + N_HR + N_SOLAR * 2 + INDICES_CORRESPONDING_TO_DHN
    # COOLING SYSTEMS
    # Lake Cooling
    if individual[heating_block] == 1 and LAKE_COOLING_ALLOWED is True:
        master_to_slave_vars.Lake_cooling_on = 1
        master_to_slave_vars.Lake_cooling_size_W = max(individual[heating_block + 1] * Q_cooling_nom_W,
                                                       Q_MIN_SHARE * Q_cooling_nom_W)

    # VCC Cooling
    if individual[heating_block + 2] == 1 and VCC_ALLOWED is True:
        master_to_slave_vars.VCC_on = 1
        master_to_slave_vars.VCC_cooling_size_W = max(individual[heating_block + 3] * Q_cooling_nom_W,
                                                      Q_MIN_SHARE * Q_cooling_nom_W)

    # Absorption Chiller Cooling
    if individual[heating_block + 4] == 1 and ABSORPTION_CHILLER_ALLOWED is True:
        master_to_slave_vars.Absorption_Chiller_on = 1
        master_to_slave_vars.Absorption_chiller_size_W = max(individual[heating_block + 5] * Q_cooling_nom_W,
                                                             Q_MIN_SHARE * Q_cooling_nom_W)

    # Storage Cooling
    if individual[heating_block + 6] == 1 and STORAGE_COOLING_ALLOWED is True:
        if (individual[heating_block + 2] == 1 and VCC_ALLOWED is True) or (
                individual[heating_block + 4] == 1 and ABSORPTION_CHILLER_ALLOWED is True):
            master_to_slave_vars.storage_cooling_on = 1
            master_to_slave_vars.Storage_cooling_size_W = max(individual[heating_block + 7] * Q_cooling_nom_W,
                                                              Q_MIN_SHARE * Q_cooling_nom_W)
            if master_to_slave_vars.Storage_cooling_size_W > STORAGE_COOLING_SHARE_RESTRICTION * Q_cooling_nom_W:
                master_to_slave_vars.Storage_cooling_size_W = STORAGE_COOLING_SHARE_RESTRICTION * Q_cooling_nom_W

    return master_to_slave_vars


def checkNtw(individual, DHN_barcode_list, DCN_barcode_list, locator, config, building_names):
    """
    This function adds new DH/DC networks to lists and run network simulations for new networks.
    
    :param individual: network configuration considered
    :param DHN_barcode_list: list of DHN configurations previously encountered in the master
    :param DCN_barcode_list: list of DCN configurations previously encountered in the master
    :param locator: path to the folder
    :type individual: list
    :type DHN_barcode_list: list
    :type DCN_barcode_list: list
    :type locator: string
    :return: None
    files changes: DHN_network_list, DCN_network_list
    :rtype: Nonetype
    """

    # decode an individual
    DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                     building_names)
    # local variables
    weather_file = config.weather
    network_depth_m = Z0
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    ground_temp = calc_ground_temperature(locator, config, T_ambient, depth_m=network_depth_m)
    total_demand = pd.read_csv(locator.get_total_demand())

    ## add network barcodes to lists and run network simulation
    if not (DHN_barcode in DHN_barcode_list) and DHN_barcode.count("1") > 0:
        DHN_barcode_list.append(DHN_barcode)
        demand_this_network = supportFn.createTotalNtwCsv("DH", DHN_barcode, locator)
        buildings_in_heating_network = demand_this_network.Name.values

        # Run the substation and distribution routines
        substation.substation_main_heating(locator, demand_this_network, buildings_in_heating_network,
                                           DHN_configuration,
                                           Flag=True)
        # Run thermal network simulation
        num_tot_buildings = len(get_building_names_with_load(total_demand, load_name='QH_sys_MWhyr'))
        summarize_network.network_main(locator, buildings_in_heating_network, ground_temp, num_tot_buildings, "DH",
                                       DHN_barcode)

    if not (DCN_barcode in DCN_barcode_list) and DCN_barcode.count("1") > 0:
        DCN_barcode_list.append(DCN_barcode)
        demand_this_network = supportFn.createTotalNtwCsv("DC", DCN_barcode, locator)
        buildings_in_cooling_network = demand_this_network.Name.values

        # Run the substation and distribution routines
        substation.substation_main_cooling(locator, demand_this_network, buildings_in_cooling_network,
                                           DCN_configuration,
                                           Flag=True)
        # Run thermal network simulation
        num_tot_buildings = len(get_building_names_with_load(total_demand, load_name='QC_sys_MWhyr'))
        summarize_network.network_main(locator, buildings_in_cooling_network, ground_temp, num_tot_buildings, "DC",
                                       DCN_barcode)

    return np.nan


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
