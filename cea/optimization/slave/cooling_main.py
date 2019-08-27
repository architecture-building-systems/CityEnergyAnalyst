"""
Disctrict Cooling Network Calculations.

Use free cooling from Lake as long as possible ( HP Lake operation from slave)
If Lake exhausted, then use other supply technologies

"""
from __future__ import division

from math import log

import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.optimization.constants import T_TANK_FULLY_DISCHARGED_K
from cea.optimization.constants import VCC_T_COOL_IN
from cea.optimization.master import cost_model
from cea.optimization.master.cost_model import calc_network_costs
from cea.optimization.slave.cooling_resource_activation import calc_vcc_CT_operation
from cea.optimization.slave.cooling_resource_activation import cooling_resource_activator
from cea.optimization.slave.daily_storage.load_leveling import LoadLevelingDailyStorage
from cea.technologies.constants import DT_COOL
from cea.technologies.thermal_network.thermal_network import calculate_ground_temperature

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def district_cooling_network(locator,
                             master_to_slave_variables,
                             config,
                             prices,
                             lca,
                             network_features):
    """
    Computes the parameters for the cooling of the complete DCN

    :param locator: path to res folder
    :param network_features: network features
    :param prices: Prices imported from the database
    :type locator: string
    :type network_features: class
    :type prices: class
    :return: costs, co2, prim
    :rtype: tuple
    """

    # local variables
    DCN_barcode = master_to_slave_variables.DCN_barcode
    building_names = master_to_slave_variables.building_names_cooling

    # THERMAL STORAGE + NETWORK
    # Import Temperatures from Network Summary:
    Q_thermal_req_W, T_district_cooling_return_K, T_district_cooling_supply_K, mdot_kgpers = calc_network_summary_DCN(
        locator, master_to_slave_variables)

    print("CALCULATING ECOLOGICAL COSTS OF DAILY COOLING STORAGE - DUE TO OPERATION (IF ANY)")
    # Initialize daily storage calss
    T_ground_K = calculate_ground_temperature(locator, config)
    daily_storage = LoadLevelingDailyStorage(master_to_slave_variables.Storage_cooling_on,
                                             master_to_slave_variables.Storage_cooling_size_W,
                                             min(T_district_cooling_supply_K) - DT_COOL,
                                             max(T_district_cooling_return_K) - DT_COOL,
                                             T_TANK_FULLY_DISCHARGED_K,
                                             np.mean(T_ground_K)
                                             )

    # Import Data - potentials lake heat
    if master_to_slave_variables.WS_BaseVCC_on == 1 or master_to_slave_variables.WS_PeakVCC_on == 1 or:
        HPlake_Data = pd.read_csv(locator.get_lake_potential())
        Q_therm_Lake = np.array(HPlake_Data['QLake_kW']) * 1E3
        total_WS_VCC_installed = master_to_slave_variables.WS_BaseVCC_size_W + master_to_slave_variables.WS_PeakVCC_size_W
        Q_therm_Lake_W = [x if x < total_WS_VCC_installed else total_WS_VCC_installed for x in Q_therm_Lake]
        T_source_average_Lake_K = np.array(HPlake_Data['Ts_C']) + 273
    else:
        Q_therm_Lake_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_Lake_K = np.zeros(HOURS_IN_YEAR)

    Q_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BackupVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_DailyStorage_gen_W = np.zeros(HOURS_IN_YEAR)

    Qc_from_storage_tank_W = np.zeros(HOURS_IN_YEAR)

    opex_var_Trigen_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_BaseVCC_WS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_PeakVCC_WS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_BaseVCC_AS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_PeakVCC_AS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_BackupVCC_AS_USDhr = np.zeros(HOURS_IN_YEAR)

    E_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
    E_BaseVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
    E_PeakVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
    E_BaseVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
    E_PeakVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
    E_BackupVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)

    NG_Trigen_req_W = np.zeros(HOURS_IN_YEAR)

    source_Trigen_NG = np.zeros(HOURS_IN_YEAR)
    source_BaseVCC_WS = np.zeros(HOURS_IN_YEAR)
    source_PeakVCC_WS = np.zeros(HOURS_IN_YEAR)
    source_BaseVCC_AS = np.zeros(HOURS_IN_YEAR)
    source_PeakVCC_AS = np.zeros(HOURS_IN_YEAR)

    VCC_Backup_Status = np.zeros(HOURS_IN_YEAR)

    for hour in range(HOURS_IN_YEAR):  # cooling supply for all buildings excluding cooling loads from data centers
        if Q_thermal_req_W[hour] > 0.0:  # only if there is a cooling load!
            daily_storage, \
            opex_output, \
            activation_output, \
            thermal_output, \
            electricity_output, \
            gas_output = cooling_resource_activator(Q_thermal_req_W[hour],
                                                    T_district_cooling_supply_K[hour],
                                                    T_district_cooling_return_K[hour],
                                                    Q_therm_Lake_W[hour],
                                                    T_source_average_Lake_K[hour],
                                                    daily_storage,
                                                    T_ground_K[hour],
                                                    lca,
                                                    master_to_slave_variables,
                                                    hour,
                                                    prices,
                                                    locator)

            opex_var_Trigen_NG_USDhr[hour] = opex_output['opex_var_Trigen_NG_USDhr']
            opex_var_BaseVCC_WS_USDhr[hour] = opex_output['opex_var_BaseVCC_WS_USDhr']
            opex_var_PeakVCC_WS_USDhr[hour] = opex_output['opex_var_PeakVCC_WS_USDhr']
            opex_var_BaseVCC_AS_USDhr[hour] = opex_output['opex_var_BaseVCC_AS_USDhr']
            opex_var_PeakVCC_AS_USDhr[hour] = opex_output['opex_var_PeakVCC_AS_USDhr']
            opex_var_BackupVCC_AS_USDhr[hour] = opex_output['opex_var_BackupVCC_AS_USDhr']

            source_Trigen_NG[hour] = activation_output["source_Trigen_NG"]
            source_BaseVCC_WS[hour] = activation_output["source_BaseVCC_WS"]
            source_PeakVCC_WS[hour] = activation_output["source_PeakVCC_WS"]
            source_BaseVCC_AS[hour] = activation_output["source_BaseVCC_AS"]
            source_PeakVCC_AS[hour] = activation_output["source_PeakVCC_AS"]

            Q_Trigen_NG_gen_W[hour] = thermal_output['Q_Trigen_NG_gen_W']
            Q_BaseVCC_WS_gen_W[hour] = thermal_output['Q_BaseVCC_WS_gen_W']
            Q_PeakVCC_WS_gen_W[hour] = thermal_output['Q_PeakVCC_WS_gen_W']
            Q_BaseVCC_AS_gen_W[hour] = thermal_output['Q_BaseVCC_AS_gen_W']
            Q_PeakVCC_AS_gen_W[hour] = thermal_output['Q_PeakVCC_AS_gen_W']
            Q_BackupVCC_AS_gen_W[hour] = thermal_output['Q_BackupVCC_AS_gen_W']
            Q_DailyStorage_gen_W[hour] = thermal_output['Q_DailyStorage_WS_gen_W']

            E_BaseVCC_WS_req_W[hour] = electricity_output['E_BaseVCC_WS_req_W']
            E_PeakVCC_WS_req_W[hour] = electricity_output['E_PeakVCC_WS_req_W']
            E_BaseVCC_AS_req_W[hour] = electricity_output['E_BaseVCC_AS_req_W']
            E_PeakVCC_AS_req_W[hour] = electricity_output['E_PeakVCC_AS_req_W']
            E_BackupVCC_AS_req_W[hour] = electricity_output['E_BackupVCC_AS_req_W']
            E_Trigen_NG_gen_W[hour] = electricity_output['E_Trigen_NG_gen_W']

            NG_Trigen_req_W = gas_output['NG_Trigen_req_W']

    # BACK-UPP VCC - AIR SOURCE
    master_to_slave_variables.AS_BackupVCC_size_W = np.amax(Q_BackupVCC_AS_gen_W)
    if master_to_slave_variables.AS_BackupVCC_size_W != 0:
        master_to_slave_variables.AS_BackupVCC_on = 1
        for hour in range(HOURS_IN_YEAR):
            opex_var_BackupVCC_AS_USDhr[hour], \
            Q_BackupVCC_AS_gen_W[hour], \
            E_BackupVCC_AS_req_W[hour] = calc_vcc_CT_operation(Q_BackupVCC_AS_gen_W[hour],
                                                               T_district_cooling_return_K[hour],
                                                               T_district_cooling_supply_K[hour],
                                                               VCC_T_COOL_IN,
                                                               lca)

    # CAPEX AND OPEX OF COOLING NETWORK
    Capex_DCN_USD, \
    Capex_a_DCN_USD, \
    Opex_fixed_DCN_USD, \
    Opex_var_DCN_USD, \
    E_used_district_cooling_network_W = calc_network_costs(locator,
                                                           master_to_slave_variables,
                                                           network_features,
                                                           lca,
                                                           "DC")
    # CAPEX AND FIXED OPEX GENERATION UNITS
    performance_costs = cost_model.calc_generation_costs_cooling(locator,
                                                                 master_to_slave_variables,
                                                                 config,
                                                                 daily_storage
                                                                 )

    # CAPEX VAR GENERATION UNITS
    opex_var_Trigen_NG_USD = sum(opex_var_Trigen_NG_USDhr)
    opex_var_BaseVCC_WS_USD = sum(opex_var_BaseVCC_WS_USDhr)
    opex_var_PeakVCC_WS_USD = sum(opex_var_PeakVCC_WS_USDhr)
    opex_var_BaseVCC_AS_USD = sum(opex_var_BaseVCC_AS_USDhr)
    opex_var_PeakVCC_AS_USD = sum(opex_var_PeakVCC_AS_USDhr)
    opex_var_BackupVCC_AS_USD = sum(opex_var_BackupVCC_AS_USDhr)

    # COOLING SUBSTATIONS
    Capex_Substations_USD, \
    Capex_a_Substations_USD, \
    Opex_fixed_Substations_USD, \
    Opex_var_Substations_USD = calc_substations_costs_cooling(building_names, df_current_individual, DCN_barcode,
                                                              locator)

    # SAVE
    cooling_dispatch = {
        # demand of the network
        "Q_districtcooling_sys_req_W": Q_thermal_req_W,

        # Status of each technology 1 = on, 0 = off in every hour
        "VCC_WS_Status": source_BaseVCC_WS,
        "Trigen_NG_Status": source_Trigen_NG,
        "VCC_AS_Status": source_BaseVCC_AS,
        "VCC_Backup_AS_Status": VCC_Backup_Status,

        # ENERGY GENERATION
        # cooling
        "Q_VCC_WS_W": Q_BaseVCC_WS_gen_W,
        "Q_VCC_AS_W": Q_BaseVCC_AS_gen_W,
        "Q_VCC_backup_AS_W": Q_BackupVCC_AS_gen_W,
        "Q_Trigen_NG_W": Q_Trigen_NG_gen_W,
        "Q_DailyStorage_gen_W": Q_DailyStorage_gen_W,

        # electricity
        "E_Trigen_NG_gen_W": E_Trigen_NG_gen_W,

        # ENERGY REQUIREMENTS
        # Electricity
        "E_VCC_WS_req_W": E_BaseVCC_WS_req_W,
        "E_VCC_AS_req_W": E_BaseVCC_AS_req_W + E_used_CT_W,
        "E_VCC_backup_AS_req_W": E_BackupVCC_AS_req_W,
        "E_Trigen_NG_req_W": E_Trigen_NG_req_W,

        # fuels
        "NG_Trigen_req_W": NG_Trigen_req_W
    }

    # PLOT RESULTS
    performance = {
        # annualized capex
        "Capex_a_VCC_WS_connected_USD": performance_costs['Capex_a_Lake_connected_USD'],
        "Capex_a_VCC_AS_connected_USD": performance_costs['Capex_a_VCC_connected_USD'] +
                                        performance_costs['Capex_a_CT_connected_USD'],
        "Capex_a_VCC_backup_AS_connected_USD": performance_costs['Capex_a_VCC_backup_connected_USD'],
        "Capex_a_Trigen_NG_connected_USD": performance_costs['Capex_a_CCGT_connected_USD'] +
                                           performance_costs['Capex_a_ACH_connected_USD'],
        "Capex_a_Storage_connected_USD": performance_costs['Capex_a_Tank_connected_USD'],
        "Capex_a_DCN_connected_USD": Capex_a_DCN_USD,
        "Capex_a_SubstationsCooling_connected_USD": Capex_a_Substations_USD,

        # total capex
        "Capex_total_VCC_WS_connected_USD": performance_costs['Capex_total_Lake_connected_USD'],
        "Capex_total_VCC_AS_connected_USD": performance_costs['Capex_total_VCC_connected_USD'] +
                                            performance_costs['Capex_total_CT_connected_USD'],
        "Capex_total_VCC_backup_AS_connected_USD": performance_costs['Capex_total_VCC_backup_connected_USD'],
        "Capex_total_Trigen_NG_connected_USD": performance_costs['Capex_total_ACH_connected_USD'] +
                                               performance_costs['Capex_total_CCGT_connected_USD'],
        "Capex_total_Storage_connected_USD": performance_costs['Capex_total_Tank_connected_USD'],
        "Capex_total_DCN_connected_USD": Capex_DCN_USD,
        "Capex_total_SubstationsCooling_connected_USD": Capex_Substations_USD,

        # opex fixed
        "Opex_fixed_VCC_WS_connected_USD": performance_costs['Opex_fixed_Lake_connected_USD'],
        "Opex_fixed_VCC_AS_connected_USD": performance_costs['Opex_fixed_VCC_connected_USD'] +
                                           performance_costs['Opex_fixed_CT_connected_USD'],
        "Opex_fixed_VCC_backup_connected_USD": performance_costs['Opex_fixed_VCC_backup_connected_USD'],
        "Opex_fixed_Trigen_NG_connected_USD": performance_costs['Opex_fixed_CCGT_connected_USD'] +
                                              performance_costs['Opex_fixed_ACH_connected_USD'],
        "Opex_fixed_Storage_connected_USD": performance_costs['Opex_fixed_Tank_connected_USD'],
        "Opex_fixed_DCN_connected_USD": Opex_fixed_DCN_USD,
        "Opex_fixed_SubstationsCooling_connected_USD": Opex_fixed_Substations_USD,

        # opex variable
        "Opex_var_VCC_WS_connected_USD": Opex_var_Lake_connected_USD,
        "Opex_var_VCC_AS_connected_USD": Opex_var_VCC_connected_USD + Opex_var_CT_connected_USD,
        "Opex_var_VCC_backup_AS_connected_USD": Opex_var_VCC_backup_connected_USD,
        "Opex_var_Trigen_NG_connected_USD": Opex_var_CCGT_connected_USD + Opex_var_ACH_connected_USD,
        "Opex_var_Storage_connected_USD": 0.0,  # no variable costs
        "Opex_var_DCN_connected_USD": Opex_var_DCN_USD,
        "Opex_var_SubstationsCooling_connected_USD": Opex_var_Substations_USD,

        # opex annual
        "Opex_a_VCC_WS_connected_USD": Opex_var_Lake_connected_USD +
                                       performance_costs['Opex_fixed_Lake_connected_USD'],
        "Opex_a_VCC_AS_connected_USD": Opex_var_VCC_connected_USD +
                                       performance_costs['Opex_fixed_VCC_connected_USD'] +
                                       Opex_var_CT_connected_USD +
                                       performance_costs['Opex_fixed_CT_connected_USD'],
        "Opex_a_Trigen_NG_connected_USD": Opex_var_ACH_connected_USD +
                                          performance_costs['Opex_fixed_ACH_connected_USD'] +
                                          Opex_var_CCGT_connected_USD +
                                          performance_costs['Opex_fixed_CCGT_connected_USD'],
        "Opex_a_VCC_backup_AS_connected_USD": Opex_var_VCC_backup_connected_USD +
                                              performance_costs['Opex_fixed_VCC_backup_connected_USD'],
        "Opex_a_Storage_connected_USD": 0.0 + performance_costs['Opex_fixed_Tank_connected_USD'],
        "Opex_a_DCN_connected_USD": Opex_var_DCN_USD + Opex_fixed_DCN_USD,
        "Opex_a_SubstationsCooling_connected_USD": Opex_fixed_Substations_USD + Opex_var_Substations_USD,

        # emissions
        "GHG_VCC_WS_connected_tonCO2": GHG_Lake_tonCO2,
        "GHG_VCC_AS_connected_tonCO2": GHG_VCC_tonCO2 + GHG_CT_tonCO2,
        "GHG_VCC_backup_AS_connected_tonCO2": GHG_VCC_backup_tonCO2,
        "GHG_Trigen_NG_connected_tonCO2": GHG_ACH_tonCO2 + GHG_CCGT_tonCO2,

        # primary energy
        "PEN_VCC_WS_connected_MJoil": prim_energy_Lake_MJoil,
        "PEN_VCC_AS_connected_MJoil": prim_energy_VCC_MJoil + prim_energy_CT_MJoil,
        "PEN_VCC_backup_AS_connected_MJoil": prim_energy_VCC_backup_MJoil,
        "PEN_Trigen_NG_connected_MJoil": prim_energy_ACH_MJoil + prim_energy_CCGT_MJoil,
    }

    return performance, cooling_dispatch


def calc_network_summary_DCN(locator, master_to_slave_vars):
    # if there is a district heating network on site and there is server_heating
    district_heating_network = master_to_slave_vars.DHN_exists
    if district_heating_network and master_to_slave_vars.WasteServersHeatRecovery == 1:
        df = pd.read_csv(locator.get_optimization_network_results_summary('DC',
                                                                          master_to_slave_vars.network_data_file_cooling))
        df = df.fillna(0)
        T_sup_K = df['T_DCNf_space_cooling_and_refrigeration_sup_K'].values
        T_re_K = df['T_DCNf_space_cooling_and_refrigeration_re_K'].values
        mdot_kgpers = df['mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers'].values
        Q_cooling_req_W = df['Q_DCNf_space_cooling_and_refrigeration_W'].values
    else:
        df = pd.read_csv(locator.get_optimization_network_results_summary('DC',
                                                                          master_to_slave_vars.network_data_file_cooling))
        df = df.fillna(0)
        T_sup_K = df['T_DCNf_space_cooling_data_center_and_refrigeration_sup_K'].values
        T_re_K = df['T_DCNf_space_cooling_data_center_and_refrigeration_re_K'].values
        mdot_kgpers = df['mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers'].values
        Q_cooling_req_W = df['Q_DCNf_space_cooling_data_center_and_refrigeration_W'].values
    return Q_cooling_req_W, T_re_K, T_sup_K, mdot_kgpers


def calc_substations_costs_cooling(building_names, df_current_individual, district_network_barcode, locator):
    Capex_Substations_USD = 0.0
    Capex_a_Substations_USD = 0.0
    Opex_fixed_Substations_USD = 0.0
    Opex_var_Substations_USD = 0.0  # it is asssumed as 0 in substations
    for (index, building_name) in zip(district_network_barcode, building_names):
        if index == "1":
            if df_current_individual['Data Centre'][0] == 1:
                df = pd.read_csv(
                    locator.get_optimization_substations_results_file(building_name, "DC", district_network_barcode),
                    usecols=["Q_space_cooling_and_refrigeration_W"])
            else:
                df = pd.read_csv(
                    locator.get_optimization_substations_results_file(building_name, "DC", district_network_barcode),
                    usecols=["Q_space_cooling_data_center_and_refrigeration_W"])

            subsArray = np.array(df)
            Q_max_W = np.amax(subsArray)
            HEX_cost_data = pd.read_excel(locator.get_supply_systems(), sheet_name="HEX")
            HEX_cost_data = HEX_cost_data[HEX_cost_data['code'] == 'HEX1']
            # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
            # capacity for the corresponding technology from the database
            if Q_max_W < HEX_cost_data.iloc[0]['cap_min']:
                Q_max_W = HEX_cost_data.iloc[0]['cap_min']
            HEX_cost_data = HEX_cost_data[
                (HEX_cost_data['cap_min'] <= Q_max_W) & (HEX_cost_data['cap_max'] > Q_max_W)]

            Inv_a = HEX_cost_data.iloc[0]['a']
            Inv_b = HEX_cost_data.iloc[0]['b']
            Inv_c = HEX_cost_data.iloc[0]['c']
            Inv_d = HEX_cost_data.iloc[0]['d']
            Inv_e = HEX_cost_data.iloc[0]['e']
            Inv_IR = (HEX_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = HEX_cost_data.iloc[0]['LT_yr']
            Inv_OM = HEX_cost_data.iloc[0]['O&M_%'] / 100

            InvC_USD = Inv_a + Inv_b * (Q_max_W) ** Inv_c + (Inv_d + Inv_e * Q_max_W) * log(Q_max_W)
            Capex_a_USD = InvC_USD * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
            Opex_fixed_USD = InvC_USD * Inv_OM

            Capex_Substations_USD += InvC_USD
            Capex_a_Substations_USD += Capex_a_USD
            Opex_fixed_Substations_USD += Opex_fixed_USD

    return Capex_Substations_USD, Capex_a_Substations_USD, Opex_fixed_Substations_USD, Opex_var_Substations_USD
