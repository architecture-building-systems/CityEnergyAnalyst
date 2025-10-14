"""
Evaluation function of an individual

"""

import os

import pandas as pd

from cea.optimization import slave_data
from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_SHARE, \
    Q_MARGIN_FOR_NETWORK
from cea.optimization.master import summarize_network
from cea.technologies import substation


def export_data_to_master_to_slave_class(locator,
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
                                         district_cooling_network,
                                         technologies_heating_allowed,
                                         technologies_cooling_allowed,
                                         weather_features,
                                         config
                                         ):
    """
    This function ...

    :param locator: paths to cea input files
    :param gen: counter for generation of genetic optimization algorithm
    :param ind_num: counter to identify individual within current generation of genetic optimization algorithm
    :param individual_with_name_dict: individual's chromosome (including description of each parameter)
    :param building_names: names of buildings in the analysed district
    :param building_names_heating: names of all buildings that have a heating load (space heat, hot water etc.)
    :param building_names_cooling: names of all buildings that have a cooling load
    :param building_names_electricity: names of all buildings that have an electricity load
    :param DHN_barcode: barcode identifying buildings are connected to the district heating network ('0' not connected,
                        '1' connected)
    :param DCN_barcode: barcode identifying buildings are connected to the district cooling network ('0' not connected,
                        '1' connected)
    :param district_heating_network: indicator defining if district heating networks should be analyzed
    :param district_cooling_network: indicator defining if district heating networks should be analyzed
    :param technologies_heating_allowed: district heating technologies to be considered in the optimization
    :param technologies_cooling_allowed: district cooling technologies to be considered in the optimization
    :param weather_features: weather data for the selected location (ambient temperature, ground temperature etc.)

    :type locator: cea.inputlocator.InputLocator class object
    :type gen: int
    :type ind_num: int
    :type individual_with_name_dict: dict
    :type building_names: list of str
    :type building_names_heating: list of str
    :type building_names_cooling: list of str
    :type building_names_electricity: list of str
    :type DHN_barcode: str
    :type DCN_barcode: str
    :type district_heating_network: bool
    :type district_cooling_network: bool
    :type technologies_heating_allowed: list of str
    :type technologies_cooling_allowed: list of str
    :type weather_features: cea.optimization.preprocessing.preprocessing_main.WeatherFeatures class object

    :return: object containing all the important information on the energy system configuration of an individual
            (buildings [connected, non-connected], heating technologies, cooling technologies, storage etc.)
    :rtype: cea.optimization.slave_data.SlaveData class object
    """
    # get thermal network for this individual
    # RECALCULATE THE NOMINAL LOADS FOR HEATING AND COOLING, INCL SOME NAMES OF FILES
    DH_network_summary_individual, \
    DC_network_summary_individual = thermal_networks_in_individual(locator,
                                                                   weather_features,
                                                                   DCN_barcode,
                                                                   DHN_barcode,
                                                                   district_heating_network,
                                                                   district_cooling_network,
                                                                   building_names_heating,
                                                                   building_names_cooling)

    # CALCULATE PEAK LOADS
    Q_cooling_nom_W, \
    Q_heating_nom_W, \
    Q_wasteheat_datacentre_nom_W = extract_peak_loads(district_heating_network,
                                                      district_cooling_network,
                                                      DH_network_summary_individual,
                                                      DC_network_summary_individual,
                                                      )

    # CREATE MASTER TO SLAVE AND FILL-IN
    master_to_slave_vars = calc_master_to_slave_variables(locator, gen,
                                                          ind_num,
                                                          individual_with_name_dict,
                                                          building_names,
                                                          DHN_barcode,
                                                          DCN_barcode,
                                                          Q_heating_nom_W,
                                                          Q_cooling_nom_W,
                                                          Q_wasteheat_datacentre_nom_W,
                                                          district_heating_network,
                                                          district_cooling_network,
                                                          technologies_heating_allowed,
                                                          technologies_cooling_allowed,
                                                          building_names_heating,
                                                          building_names_cooling,
                                                          building_names_electricity,
                                                          DH_network_summary_individual,
                                                          DC_network_summary_individual,
                                                          config
                                                          )
    return master_to_slave_vars


def extract_peak_loads(district_heating_network,
                       district_cooling_network,
                       DH_network_summary_individual,
                       DC_network_summary_individual,
                       ):
    """
    This functions extracts peak loads of the district heating/cooling networks as well as the maximum waste heat
    generated in data centers. These values are used to define nominal heating/cooling capacities required in the
    thermal network.

    :return Q_cooling_nom_W: Nominal cooling capacity required by the district cooling network
    :return Q_heating_nom_W: Nominal heating capacity required by the district heating network
    :return Q_wasteheat_datacentre_max_W: Maximum waste heat from data centers to be used in district cooling networks
    :rtype Q_cooling_nom_W, Q_heating_nom_W, Q_wasteheat_datacentre_max_W: float
    """

    if district_heating_network:
        Q_DHNf_W = DH_network_summary_individual['Q_DHNf_W'].values
        Q_heating_max_W = Q_DHNf_W.max()
        Qcdata_netw_total_kWh = DH_network_summary_individual['Qcdata_netw_total_kWh'].values
        Q_wasteheat_datacentre_max_W = Qcdata_netw_total_kWh.max()

    else:
        Q_heating_max_W = 0.0
        Q_wasteheat_datacentre_max_W = 0.0

    if district_cooling_network:
        # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
        Q_DCNf_W = DC_network_summary_individual["Q_DCNf_space_cooling_data_center_and_refrigeration_W"].values
        Q_cooling_max_W = Q_DCNf_W.max()
    else:
        Q_cooling_max_W = 0.0

    Q_heating_nom_W = Q_heating_max_W * (1 + Q_MARGIN_FOR_NETWORK)
    Q_cooling_nom_W = Q_cooling_max_W * (1 + Q_MARGIN_FOR_NETWORK)

    return Q_cooling_nom_W, Q_heating_nom_W, Q_wasteheat_datacentre_max_W


def thermal_networks_in_individual(locator,
                                   weather_features,
                                   DCN_barcode,
                                   DHN_barcode,
                                   district_heating_network,
                                   district_cooling_network,
                                   column_names_buildings_heating,
                                   column_names_buildings_cooling
                                   ):
    """
    This function gets the district heating/cooling network properties for networks corresponding to the combination of
    connected buildings as specified by DHN_barcode/DHN_barcode.
    If the thermal network properties for this combination of buildings have not previously been calculated, this
    function calls the substation_main and network_main functions to calculate these properties and saves them for
    future individuals with the same combination of thermally connected buildings.

    :return: Thermal network operation properties (mass flow rate, heating/cooling energy provided, supply & return
             temperatures,  network losses) for each hour of the year.
    :rtype: DataFrame
    """

    # local variables
    ground_temp = weather_features.ground_temp

    # EVALUATE CASES TO CREATE A NETWORK OR NOT
    if district_heating_network:  # network exists
        if not os.path.exists(locator.get_optimization_network_results_summary('DH', DHN_barcode)):
            total_demand = createTotalNtwCsv(DHN_barcode, locator, column_names_buildings_heating)
            num_total_buildings = len(column_names_buildings_heating)
            buildings_in_heating_network = total_demand.Name.values
            # Run the substation and distribution routines
            substation.substation_main_heating(locator,
                                               total_demand,
                                               buildings_in_heating_network,
                                               DHN_barcode=DHN_barcode)
            DH_network_summary_individual = summarize_network.network_main(locator,
                                                                           buildings_in_heating_network,
                                                                           ground_temp,
                                                                           num_total_buildings,
                                                                           "DH", DHN_barcode)
        else:
            DH_network_summary_individual = pd.read_csv(
                locator.get_optimization_network_results_summary('DH', DHN_barcode))
    else:
        DH_network_summary_individual = None

    if district_cooling_network:  # network exists
        if not os.path.exists(locator.get_optimization_network_results_summary('DC', DCN_barcode)):
            total_demand = createTotalNtwCsv(DCN_barcode, locator, column_names_buildings_cooling)
            num_total_buildings = len(column_names_buildings_cooling)
            buildings_in_cooling_network = total_demand.Name.values

            # Run the substation and distribution routines
            substation.substation_main_cooling(locator, total_demand, buildings_in_cooling_network,
                                               DCN_barcode=DCN_barcode)
            DC_network_summary_individual = summarize_network.network_main(locator, buildings_in_cooling_network,
                                                                           ground_temp,
                                                                           num_total_buildings,
                                                                           'DC', DCN_barcode)
        else:
            DC_network_summary_individual = pd.read_csv(
                locator.get_optimization_network_results_summary('DC', DCN_barcode))
    else:
        DC_network_summary_individual = None

    return DH_network_summary_individual, DC_network_summary_individual


# +++++++++++++++++++++++++++++++++++
# Boundary conditions
# +++++++++++++++++++++++++++++
def calc_master_to_slave_variables(locator, gen,
                                   ind_num,
                                   individual_with_names_dict,
                                   building_names,
                                   DHN_barcode,
                                   DCN_barcode,
                                   Q_heating_nom_W,
                                   Q_cooling_nom_W,
                                   Q_wasteheat_datacentre_nom_W,
                                   district_heating_network,
                                   district_cooling_network,
                                   technologies_heating_allowed,
                                   technologies_cooling_allowed,
                                   building_names_heating,
                                   building_names_cooling,
                                   building_names_electricity,
                                   DH_network_summary_individual,
                                   DC_network_summary_individual,
                                   config
                                   ):
    """
    This function stores all the information on an individual and the corresponding thermal network in a class object.

    :return: master_to_slave_vars : class MasterSlaveVariables
    :rtype: class
    """

    # initialise class storing dynamic variables transferred from master to slave optimization
    master_to_slave_vars = slave_data.SlaveData()
    master_to_slave_vars.debug = config.general.debug

    # Store information about individual regarding the configuration of the network and customers connected
    if district_heating_network and DHN_barcode.count("1") > 0:
        master_to_slave_vars.DHN_exists = True
    if district_cooling_network and DCN_barcode.count("1") > 0:
        master_to_slave_vars.DCN_exists = True

    # store how many buildings are connected to district heating or cooling
    master_to_slave_vars.number_of_buildings_district_scale_heating = DHN_barcode.count("1")
    master_to_slave_vars.number_of_buildings_district_scale_cooling = DCN_barcode.count("1")

    # store the names of the buildings connected to district heating or district cooling
    master_to_slave_vars.buildings_district_scale_to_district_heating = calc_district_scale_names(
        building_names_heating,
        DHN_barcode)
    master_to_slave_vars.buildings_district_scale_to_district_cooling = calc_district_scale_names(
        building_names_cooling,
        DCN_barcode)

    # these are dataframes describing the operation of the thermal networks in the individual
    master_to_slave_vars.DH_network_summary_individual = DH_network_summary_individual
    master_to_slave_vars.DC_network_summary_individual = DC_network_summary_individual

    # store the name of the file where the network configuration is stored
    master_to_slave_vars.technologies_heating_allowed = technologies_heating_allowed
    master_to_slave_vars.technologies_cooling_allowed = technologies_cooling_allowed

    # store the barcode which identifies which buildings are connected and disconnected
    master_to_slave_vars.DHN_barcode = DHN_barcode
    master_to_slave_vars.DCN_barcode = DCN_barcode

    # store the total number of buildings in the district (independent of district cooling or heating)
    master_to_slave_vars.num_total_buildings = len(building_names)

    # store the name of all buildings in the district (independent of district cooling or heating)
    master_to_slave_vars.building_names_all = building_names

    # store the name used to identify the individual (this helps to know where is inside)
    master_to_slave_vars.building_names_heating = building_names_heating
    master_to_slave_vars.building_names_cooling = building_names_cooling
    master_to_slave_vars.building_names_electricity = building_names_electricity
    master_to_slave_vars.individual_with_names_dict = individual_with_names_dict

    # Store the number of the individual and the generation to which it belongs
    master_to_slave_vars.individual_number = ind_num
    master_to_slave_vars.generation_number = gen

    # Store information about which units are activated
    master_to_slave_vars = master_to_slave_electrical_technologies(individual_with_names_dict, locator,
                                                                   master_to_slave_vars,
                                                                   district_heating_network,
                                                                   district_cooling_network,
                                                                   )

    if master_to_slave_vars.DHN_exists:
        master_to_slave_vars.Q_heating_nom_W = Q_heating_nom_W
        master_to_slave_vars = master_to_slave_district_heating_technologies(Q_heating_nom_W,
                                                                             Q_wasteheat_datacentre_nom_W,
                                                                             individual_with_names_dict, locator,
                                                                             master_to_slave_vars)

    if master_to_slave_vars.DCN_exists:
        storage_type = config.optimization.cold_storage_type
        master_to_slave_vars.Q_cooling_nom_W = Q_cooling_nom_W
        master_to_slave_vars = master_to_slave_district_cooling_technologies(Q_cooling_nom_W,
                                                                             individual_with_names_dict,
                                                                             master_to_slave_vars,
                                                                             storage_type)

    return master_to_slave_vars


def master_to_slave_district_cooling_technologies(Q_cooling_nom_W,
                                                  individual_with_names_dict,
                                                  master_to_slave_vars,
                                                  storage_type):
    # COOLING SYSTEMS
    technologies_cooling_allowed = master_to_slave_vars.technologies_cooling_allowed
    # NG-Fired Trigen with Absorption Chiller
    if 'NG_Trigen' in technologies_cooling_allowed and individual_with_names_dict['NG_Trigen'] >= mimimum_valuedc(
            'NG_Trigen'):
        master_to_slave_vars.NG_Trigen_on = 1
        master_to_slave_vars.NG_Trigen_ACH_size_W = individual_with_names_dict['NG_Trigen'] * Q_cooling_nom_W
        master_to_slave_vars.NG_Trigen_CCGT_size_thermal_W = master_to_slave_vars.NG_Trigen_ACH_size_W * 1.2
        # twice as big to allow for usage of absorption chiller

    # Water source base vapor compression chiller
    if 'WS_BaseVCC' in technologies_cooling_allowed and individual_with_names_dict['WS_BaseVCC'] >= mimimum_valuedc(
            'WS_BaseVCC'):
        master_to_slave_vars.WS_BaseVCC_on = 1
        master_to_slave_vars.WS_BaseVCC_size_W = individual_with_names_dict['WS_BaseVCC'] * Q_cooling_nom_W

    # Water source peak vapor compression chiller
    if 'WS_PeakVCC' in technologies_cooling_allowed and individual_with_names_dict['WS_PeakVCC'] >= mimimum_valuedc(
            'WS_PeakVCC'):
        master_to_slave_vars.WS_PeakVCC_on = 1
        master_to_slave_vars.WS_PeakVCC_size_W = individual_with_names_dict['WS_PeakVCC'] * Q_cooling_nom_W

    # Air source (Cooling Tower) base vapor compression chiller
    if 'AS_BaseVCC' in technologies_cooling_allowed and individual_with_names_dict['AS_BaseVCC'] >= mimimum_valuedc(
            'AS_BaseVCC'):
        master_to_slave_vars.AS_BaseVCC_on = 1
        master_to_slave_vars.AS_BaseVCC_size_W = individual_with_names_dict['AS_BaseVCC'] * Q_cooling_nom_W

    # Air source (Cooling Tower) peak vapor compression chiller
    if 'AS_PeakVCC' in technologies_cooling_allowed and individual_with_names_dict['AS_PeakVCC'] >= mimimum_valuedc(
            'AS_PeakVCC'):
        master_to_slave_vars.AS_PeakVCC_on = 1
        master_to_slave_vars.AS_PeakVCC_size_W = individual_with_names_dict['AS_PeakVCC'] * Q_cooling_nom_W

    # Storage Cooling
    flag = False
    if 'WS_BaseVCC' in technologies_cooling_allowed and individual_with_names_dict['WS_BaseVCC'] >= mimimum_valuedc(
            'WS_BaseVCC'):
        flag = True
    elif 'WS_PeakVCC' in technologies_cooling_allowed and individual_with_names_dict['WS_PeakVCC'] >= mimimum_valuedc(
            'WS_PeakVCC'):
        flag = True
    elif 'AS_BaseVCC' in technologies_cooling_allowed and individual_with_names_dict['AS_BaseVCC'] >= mimimum_valuedc(
            'AS_BaseVCC'):
        flag = True
    elif 'AS_PeakVCC' in technologies_cooling_allowed and individual_with_names_dict['AS_PeakVCC'] >= mimimum_valuedc(
            'AS_PeakVCC'):
        flag = True
    elif 'NG_Trigen' in technologies_cooling_allowed and individual_with_names_dict['NG_Trigen'] >= mimimum_valuedc(
            'NG_Trigen'):
        flag = True
    if 'Storage' in technologies_cooling_allowed and individual_with_names_dict['Storage'] >= mimimum_valuedc(
            'Storage') and flag:
        master_to_slave_vars.Storage_cooling_on = 1
        master_to_slave_vars.Storage_cooling_size_W = individual_with_names_dict['Storage'] * Q_cooling_nom_W
        master_to_slave_vars.Storage_type = storage_type

    return master_to_slave_vars


def calc_district_scale_names(building_names, barcode):
    connected_buildings = []
    for name, index in zip(building_names, barcode):
        if index == '1':
            connected_buildings.append(name)
    return connected_buildings


def calc_available_area_solar(locator, buildings, share_allowed, technology):
    """
    :param cea.inputlocator.InputLocator locator:
    :param buildings:
    :param share_allowed:
    :param technology:
    :return:
    """
    area_m2 = 0.0
    locator_methods = {"PVT": locator.PVT_results, "PV": locator.PV_results}
    for building in buildings:
        solar_technology_potential = pd.read_csv(locator_methods[technology](building))
        area_m2 += solar_technology_potential['Area_' + technology + '_m2'][0]

    return area_m2 * share_allowed


def calc_available_area_solar_collectors(locator, buildings, share_allowed, panel_type):
    """

    :param cea.inputlocator.InputLocator locator:
    :param buildings:
    :param share_allowed:
    :param str panel_type:
    :return:
    """
    area_m2 = 0.0
    for building in buildings:
        solar_technology_potential = pd.read_csv(locator.SC_results(building, panel_type))
        area_m2 += solar_technology_potential['area_SC_m2'][0]

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
                                                  Q_wasteheat_datacentre_nom_W,
                                                  individual_with_names_dict,
                                                  locator,
                                                  master_to_slave_vars):
    technologies_heating_allowed = master_to_slave_vars.technologies_heating_allowed
    if 'NG_Trigen' in technologies_heating_allowed and individual_with_names_dict['NG_Cogen'] >= mimimum_valuedh(
            'NG_Cogen'):  # NG-fired CHPFurnace
        master_to_slave_vars.CC_on = 1
        master_to_slave_vars.CCGT_SIZE_W = individual_with_names_dict['NG_Cogen'] * Q_heating_nom_W

    if 'WB_Cogen' in technologies_heating_allowed and individual_with_names_dict['WB_Cogen'] >= mimimum_valuedh(
            'WB_Cogen'):  # Wet-Biomass fired Furnace
        master_to_slave_vars.Furnace_wet_on = 1
        master_to_slave_vars.WBFurnace_Q_max_W = individual_with_names_dict['WB_Cogen'] * Q_heating_nom_W

    if 'DB_Cogen' in technologies_heating_allowed and individual_with_names_dict['DB_Cogen'] >= mimimum_valuedh(
            'DB_Cogen'):  # Dry-Biomass fired Furnace
        master_to_slave_vars.Furnace_dry_on = 1
        master_to_slave_vars.DBFurnace_Q_max_W = individual_with_names_dict['DB_Cogen'] * Q_heating_nom_W

    # Base boiler
    if 'NG_BaseBoiler' in technologies_heating_allowed and individual_with_names_dict[
        'NG_BaseBoiler'] >= mimimum_valuedh('NG_BaseBoiler'):  # NG-fired boiler
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max_W = individual_with_names_dict['NG_BaseBoiler'] * Q_heating_nom_W

    # peak boiler
    if 'NG_PeakBoiler' in technologies_heating_allowed and individual_with_names_dict[
        'NG_PeakBoiler'] >= mimimum_valuedh('NG_PeakBoiler'):  # BG-fired boiler
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max_W = individual_with_names_dict['NG_PeakBoiler'] * Q_heating_nom_W

    # HPLake
    if 'WS_HP' in technologies_heating_allowed and individual_with_names_dict['WS_HP'] >= mimimum_valuedh('WS_HP'):
        master_to_slave_vars.HPLake_on = 1
        master_to_slave_vars.HPLake_maxSize_W = individual_with_names_dict['WS_HP'] * Q_heating_nom_W
    # HPSewage
    if 'SS_HP' in technologies_heating_allowed and individual_with_names_dict['SS_HP'] >= mimimum_valuedh('SS_HP'):
        master_to_slave_vars.HPSew_on = 1
        master_to_slave_vars.HPSew_maxSize_W = individual_with_names_dict['SS_HP'] * Q_heating_nom_W
    # GHP
    if 'GS_HP' in technologies_heating_allowed and individual_with_names_dict['GS_HP'] >= mimimum_valuedh('GS_HP'):
        master_to_slave_vars.GHP_on = 1
        master_to_slave_vars.GHP_maxSize_W = individual_with_names_dict['GS_HP'] * Q_heating_nom_W
    # HPServer
    if 'DS_HP' in technologies_heating_allowed and individual_with_names_dict['DS_HP'] >= mimimum_valuedh('DS_HP'):
        master_to_slave_vars.WasteServersHeatRecovery = 1
        master_to_slave_vars.HPServer_maxSize_W = Q_wasteheat_datacentre_nom_W

    # SOLAR TECHNOLOGIES
    if 'PVT' in technologies_heating_allowed and individual_with_names_dict[
        'PVT'] > 0.0:  # different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.buildings_district_scale_to_district_heating
        share_allowed = individual_with_names_dict['PVT']
        master_to_slave_vars.PVT_on = 1
        master_to_slave_vars.A_PVT_m2 = calc_available_area_solar(locator, buildings, share_allowed, 'PVT')
        master_to_slave_vars.PVT_share = share_allowed

    if 'SC_ET' in technologies_heating_allowed and individual_with_names_dict[
        'SC_ET'] > 0.0:  # different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.buildings_district_scale_to_district_heating
        share_allowed = individual_with_names_dict['SC_ET']
        master_to_slave_vars.SC_ET_on = 1
        master_to_slave_vars.A_SC_ET_m2 = calc_available_area_solar_collectors(locator, buildings, share_allowed, "ET")
        master_to_slave_vars.SC_ET_share = share_allowed

    if 'SC_FP' in technologies_heating_allowed and individual_with_names_dict[
        'SC_FP'] > 0.0:  # different in this case, because solar technologies can have shares close to 0.0
        buildings = master_to_slave_vars.buildings_district_scale_to_district_heating
        share_allowed = individual_with_names_dict['SC_FP']
        master_to_slave_vars.SC_FP_on = 1
        master_to_slave_vars.A_SC_FP_m2 = calc_available_area_solar_collectors(locator, buildings, share_allowed, "FP")
        master_to_slave_vars.SC_FP_share = share_allowed

    return master_to_slave_vars


def master_to_slave_electrical_technologies(individual_with_names_dict,
                                            locator,
                                            master_to_slave_vars,
                                            district_heating_network,
                                            district_cooling_network,
                                            ):
    # SOLAR TECHNOLOGIES
    if district_heating_network:
        technologies_allowed = master_to_slave_vars.technologies_heating_allowed
    elif district_cooling_network:
        technologies_allowed = master_to_slave_vars.technologies_cooling_allowed
    else:
        raise Exception("option not available")

    if 'PV' in technologies_allowed and individual_with_names_dict['PV'] > 0.0:
        # different in this case, because solar technologies can have shares close to 0.0
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
    :param barcode: string of 0 and 1: 0 if the building is disconnected, 1 if connected
    :param locator: path to raw files
    :param building_names: list of all buildings in the selected district
    :type barcode: string
    :type locator: string
    :type building_names: list
    :return: name of the total file
    :rtype: string
    """
    # obtain buildings which are in this network
    buildings_in_this_network_config = []
    for index, name in zip(barcode, building_names):
        if index == '1':
            buildings_in_this_network_config.append(name)

    # get total demand file for buildings in the network
    df = pd.read_csv(locator.get_total_demand())
    dfRes = df[df.Name.isin(buildings_in_this_network_config)]
    dfRes = dfRes.reset_index(drop=True)

    return dfRes
