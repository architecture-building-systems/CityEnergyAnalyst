"""
Evaluation function of an individual

"""
from __future__ import division

import os

import pandas as pd

from cea.optimization import slave_data
from cea.optimization.constants import *
from cea.optimization.master import summarize_network
from cea.resources.geothermal import calc_ground_temperature
from cea.technologies import substation
from cea.utilities import epwreader
from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_SHARE


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
    weather_file = locator.get_weather_file()
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
                total_demand = createTotalNtwCsv(DHN_barcode, locator, column_names_buildings_heating)
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
                Q_DCNf_W_no_server_demand = pd.read_csv(
                    locator.get_optimization_network_results_summary('DC', DCN_barcode),
                    usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
                Q_DCNf_W_with_server_demand = pd.read_csv(
                    locator.get_optimization_network_results_summary('DC', DCN_barcode),
                    usecols=[
                        "Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values

                Q_DCNf_W = Q_DCNf_W_no_server_demand + (
                        (Q_DCNf_W_with_server_demand - Q_DCNf_W_no_server_demand) * (
                    individual_with_name_dict['HPShare']))

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
                total_demand = createTotalNtwCsv(DCN_barcode, locator, column_names_buildings_cooling)
                num_total_buildings = len(column_names_buildings_cooling)
                buildings_in_cooling_network = total_demand.Name.values

                # Run the substation and distribution routines
                substation.substation_main_cooling(locator, total_demand, buildings_in_cooling_network,
                                                   DCN_barcode=DCN_barcode)
                summarize_network.network_main(locator, buildings_in_cooling_network, ground_temp, num_total_buildings,
                                               'DC', DCN_barcode)

            Q_DCNf_W_no_server_demand = pd.read_csv(locator.get_optimization_network_results_summary('DC', DCN_barcode),
                                                    usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
            Q_DCNf_W_with_server_demand = pd.read_csv(
                locator.get_optimization_network_results_summary('DC', DCN_barcode),
                usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values

            # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            if district_heating_network and individual_with_name_dict['HPServer'] == 1:
                Q_DCNf_W = Q_DCNf_W_no_server_demand + (
                        (Q_DCNf_W_with_server_demand - Q_DCNf_W_no_server_demand) * (
                    individual_with_name_dict['HPShare']))
            else:
                Q_DCNf_W = Q_DCNf_W_with_server_demand

            Q_cooling_max_W = Q_DCNf_W.max()
    else:
        Q_cooling_max_W = 0.0
        network_file_name_cooling = ""

    Q_heating_nom_W = Q_heating_max_W * (1 + Q_MARGIN_FOR_NETWORK)
    Q_cooling_nom_W = Q_cooling_max_W * (1 + Q_MARGIN_FOR_NETWORK)

    return Q_cooling_nom_W, Q_heating_nom_W, network_file_name_cooling, network_file_name_heating


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
    :type individual_with_names_dict: list
    :type Q_heating_max_W: float
    :type locator: string
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
    # NG-Fired Trigen with Absorption Chiller
    if individual_with_names_dict['NG_Trigen'] >= mimimum_valuedc('NG_Trigen')and ABSORPTION_CHILLER_ALLOWED is True:
        master_to_slave_vars.NG_Trigen_on = 1
        master_to_slave_vars.NG_Trigen_ACH_size_W = individual_with_names_dict['NG_Trigen'] * Q_cooling_nom_W
        master_to_slave_vars.NG_Trigen_CCGT_size_W = master_to_slave_vars.NG_Trigen_ACH_size_W *2
        #twice as big to allow for usage of absorption chiller

    # Water source base vapor compression chiller
    if individual_with_names_dict['WS_BaseVCC'] >= mimimum_valuedc('WS_BaseVCC') and LAKE_COOLING_ALLOWED is True:
        master_to_slave_vars.WS_BaseVCC_on = 1
        master_to_slave_vars.WS_BaseVCC_size_W = individual_with_names_dict['WS_BaseVCC'] * Q_cooling_nom_W

    # Water source peak vapor compression chiller
    if individual_with_names_dict['WS_PeakVCC'] >= mimimum_valuedc('WS_PeakVCC') and LAKE_COOLING_ALLOWED is True:
        master_to_slave_vars.WS_PeakVCC_on = 1
        master_to_slave_vars.WS_PeakVCC_size_W = individual_with_names_dict['WS_PeakVCC'] * Q_cooling_nom_W

    # Air source (Cooling Tower) base vapor compression chiller
    if individual_with_names_dict['AS_BaseVCC'] >= mimimum_valuedc('AS_BaseVCC') and LAKE_COOLING_ALLOWED is True:
        master_to_slave_vars.AS_BaseVCC_on = 1
        master_to_slave_vars.AS_BaseVCC_size_W = individual_with_names_dict['WS_BaseVCC'] * Q_cooling_nom_W

    # Air source (Cooling Tower) peak vapor compression chiller
    if individual_with_names_dict['AS_PeakVCC'] >= mimimum_valuedc('AS_PeakVCC') and LAKE_COOLING_ALLOWED is True:
        master_to_slave_vars.AS_PeakVCC_on = 1
        master_to_slave_vars.AS_PeakVCC_size_W = individual_with_names_dict['AS_PeakVCC'] * Q_cooling_nom_W

    # Storage Cooling
    if individual_with_names_dict['Storage'] >= mimimum_valuedc('Storage') and STORAGE_COOLING_ALLOWED is True:
        if (individual_with_names_dict['WS_BaseVCC'] >= mimimum_valuedc('WS_BaseVCC') and VCC_ALLOWED is True) or \
            (individual_with_names_dict['WS_PeakVCC'] >= mimimum_valuedc('WS_PeakVCC') and VCC_ALLOWED is True) or \
            (individual_with_names_dict['AS_BaseVCC'] >= mimimum_valuedc('AS_BaseVCC') and VCC_ALLOWED is True) or \
            (individual_with_names_dict['AS_PeakVCC'] >= mimimum_valuedc('AS_PeakVCC') and VCC_ALLOWED is True) or \
            (individual_with_names_dict['NG_Trigen'] >= mimimum_valuedc('NG_Trigen') and ABSORPTION_CHILLER_ALLOWED is True):
            master_to_slave_vars.Storage_cooling_on = 1
            master_to_slave_vars.Storage_cooling_size_W = individual_with_names_dict['Storage'] * Q_cooling_nom_W

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
        area_m2 += solar_technology_potential['Area_' + technology + '_m2'][0]

    return area_m2 * share_allowed


def calc_available_area_solar_collectors(locator, buildings, share_allowed, technology):
    area_m2 = 0.0
    for building_name in buildings:
        solar_technology_potential = pd.read_csv(
            os.path.join(locator.get_potentials_solar_folder(), building_name + '_' + technology + '.csv'))
        area_m2 += solar_technology_potential['Area_SC_m2'][0]

    return area_m2 * share_allowed


def mimimum_valuedh(technology):
    data = DH_CONVERSION_TECHNOLOGIES_SHARE[technology]
    minimum = data['minimum']
    return minimum

def mimimum_valuedc(technology):
    data = DC_CONVERSION_TECHNOLOGIES_SHARE[technology]
    minimum = data['minimum']
    return minimum

def master_to_slave_district_heating_technologies(Q_heating_nom_W,
                                                  individual_with_names_dict,
                                                  locator,
                                                  master_to_slave_vars):

    if individual_with_names_dict['NG_Cogen'] >= mimimum_valuedh('NG_Cogen') and CC_ALLOWED == True:  # NG-fired CHPFurnace
        master_to_slave_vars.CC_on = 1
        master_to_slave_vars.CCGT_SIZE_W = individual_with_names_dict['NG_Cogen'] * Q_heating_nom_W

    if individual_with_names_dict['WB_Cogen'] >= mimimum_valuedh('WB_Cogen') and FURNACE_ALLOWED == True:  # Wet-Biomass fired Furnace
        master_to_slave_vars.Furnace_wet_on = 1
        master_to_slave_vars.WBFurnace_Q_max_W = individual_with_names_dict['WB_Cogen'] * Q_heating_nom_W

    if individual_with_names_dict['DB_Cogen'] >= mimimum_valuedh('DB_Cogen') and FURNACE_ALLOWED == True:  # Dry-Biomass fired Furnace
        master_to_slave_vars.Furnace_dry_on = 1
        master_to_slave_vars.DBFurnace_Q_max_W = individual_with_names_dict['DB_Cogen'] * Q_heating_nom_W

    # Base boiler
    if individual_with_names_dict['NG_BaseBoiler'] >= mimimum_valuedh('NG_BaseBoiler'): # NG-fired boiler
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max_W = individual_with_names_dict['NG_BaseBoiler'] * Q_heating_nom_W

    # peak boiler
    if individual_with_names_dict['NG_PeakBoiler'] >= mimimum_valuedh('NG_PeakBoiler'):  # BG-fired boiler
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max_W = individual_with_names_dict['NG_PeakBoiler'] * Q_heating_nom_W

    # HPLake
    if individual_with_names_dict['WS_HP'] >= mimimum_valuedh('WS_HP') and HP_LAKE_ALLOWED == True:
        master_to_slave_vars.HPLake_on = 1
        master_to_slave_vars.HPLake_maxSize_W = individual_with_names_dict['WS_HP'] * Q_heating_nom_W
    # HPSewage
    if individual_with_names_dict['SS_HP'] >= mimimum_valuedh('SS_HP') and HP_SEW_ALLOWED == True:
        master_to_slave_vars.HPSew_on = 1
        master_to_slave_vars.HPSew_maxSize_W = individual_with_names_dict['SS_HP'] * Q_heating_nom_W
    # GHP
    if individual_with_names_dict['GS_HP'] >= mimimum_valuedh('GS_HP') and GHP_ALLOWED == True:
        master_to_slave_vars.GHP_on = 1
        master_to_slave_vars.GHP_maxSize_W = individual_with_names_dict['GS_HP'] * Q_heating_nom_W
    # HPServer
    if individual_with_names_dict['DS_HP'] >= mimimum_valuedh('DS_HP') and DATACENTER_HEAT_RECOVERY_ALLOWED == True:
        master_to_slave_vars.WasteServersHeatRecovery = 1
        master_to_slave_vars.HPServer_maxSize_W = individual_with_names_dict['DS_HP'] * Q_heating_nom_W

    # SOLAR TECHNOLOGIES
    if individual_with_names_dict['PVT'] > 0.0: #different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = individual_with_names_dict['PVT']
        master_to_slave_vars.PVT_on = 1
        master_to_slave_vars.A_PVT_m2 = calc_available_area_solar(locator, buildings, share_allowed, 'PVT')
        master_to_slave_vars.PVT_share = share_allowed

    if individual_with_names_dict['SC_ET'] > 0.0: #different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = individual_with_names_dict['SC_ET']
        master_to_slave_vars.SC_ET_on = 1
        master_to_slave_vars.A_SC_ET_m2 = calc_available_area_solar_collectors(locator, buildings, share_allowed,
                                                                               'SC_ET')
        master_to_slave_vars.SC_ET_share = share_allowed

    if individual_with_names_dict['SC_FP'] > 0.0: #different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.buildings_connected_to_district_heating
        share_allowed = individual_with_names_dict['SC_FP']
        master_to_slave_vars.SC_FP_on = 1
        master_to_slave_vars.A_SC_FP_m2 = calc_available_area_solar_collectors(locator, buildings, share_allowed,
                                                                               "SC_FP")
        master_to_slave_vars.SC_FP_share = share_allowed

    return master_to_slave_vars


def master_to_slave_electrical_technologies(individual_with_names_dict,
                                            locator,
                                            master_to_slave_vars):
    # SOLAR TECHNOLOGIES
    if individual_with_names_dict['PV'] > 0.0: #different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.building_names_all
        share_allowed = individual_with_names_dict['PV']
        master_to_slave_vars.PV_on = 1
        master_to_slave_vars.A_PV_m2 = calc_available_area_solar(locator, buildings, share_allowed, 'PV')
        master_to_slave_vars.PV_share = share_allowed

    return master_to_slave_vars


def createTotalNtwCsv(barcode, locator, building_names):
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
    for index, name in zip(barcode, building_names):
        if index == '1':
            buildings_in_this_network_config.append(name)

    # get total demand file fro selecte
    df = pd.read_csv(locator.get_total_demand())
    dfRes = df[df.Name.isin(buildings_in_this_network_config)]
    dfRes = dfRes.reset_index(drop=True)

    return dfRes
