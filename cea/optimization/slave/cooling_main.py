"""
Disctrict Cooling Network Calculations.

Use free cooling from Lake as long as possible ( HP Lake operation from slave)
If Lake exhausted, then use other supply technologies

"""




import numpy as np
import pandas as pd
import cea.inputlocator

from cea.constants import HOURS_IN_YEAR
from cea.optimization.constants import T_TANK_FULLY_DISCHARGED_K, DT_COOL, VCC_T_COOL_IN, ACH_T_IN_FROM_CHP_K, VCC_CODE_CENTRALIZED
from cea.optimization.master import cost_model
from cea.optimization.slave.cooling_resource_activation import calc_vcc_CT_operation, cooling_resource_activator
from cea.technologies.storage_tank_pcm import Storage_tank_PCM
from cea.technologies.chiller_vapor_compression import VaporCompressionChiller
from cea.technologies.cogeneration import calc_cop_CCGT
from cea.technologies.thermal_network.thermal_network import calculate_ground_temperature
from cea.technologies.chiller_absorption import AbsorptionChiller
from cea.technologies.supply_systems_database import SupplySystemsDatabase

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2021, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def district_cooling_network(locator,
                             master_to_slave_variables,
                             network_features,
                             weather_features):
    """
    Computes the parameters for the cooling of the complete DCN

    :param cea.inputlocator.InputLocator locator: path to res folder
    :param network_features: network features
    :param prices: Prices imported from the database
    :type network_features: class
    :type prices: class
    :return: costs, co2, prim
    :rtype: tuple
    """

    if master_to_slave_variables.DCN_exists:
        # THERMAL STORAGE + NETWORK
        # Import Temperatures from Network Summary:
        Q_thermal_req_W, \
        T_district_cooling_return_K, \
        T_district_cooling_supply_K, \
        mdot_kgpers = calc_network_summary_DCN(master_to_slave_variables)

        # Initialize daily storage calss
        T_ground_K = weather_features.ground_temp_K
        daily_storage = Storage_tank_PCM(activation=master_to_slave_variables.Storage_cooling_on,
                                         size_Wh=master_to_slave_variables.Storage_cooling_size_W,
                                         database_model_parameters= pd.read_excel(locator.get_database_conversion_systems(), sheet_name="TES"),
                                         T_ambient_K = np.average(T_ground_K),
                                         type_storage = config.optimization.cold_storage_type,
                                         debug = master_to_slave_variables.debug
                                         )

        # Import Data - potentials lake heat
        if master_to_slave_variables.WS_BaseVCC_on == 1 or master_to_slave_variables.WS_PeakVCC_on == 1:
            HPlake_Data = pd.read_csv(locator.get_water_body_potential())
            Q_therm_Lake = np.array(HPlake_Data['QLake_kW']) * 1E3
            total_WS_VCC_installed = master_to_slave_variables.WS_BaseVCC_size_W + master_to_slave_variables.WS_PeakVCC_size_W
            Q_therm_Lake_W = [x if x < total_WS_VCC_installed else total_WS_VCC_installed for x in Q_therm_Lake]
            T_source_average_Lake_K = np.array(HPlake_Data['Ts_C']) + 273
        else:
            Q_therm_Lake_W = np.zeros(HOURS_IN_YEAR)
            T_source_average_Lake_K = np.zeros(HOURS_IN_YEAR)

        # get properties of technology used in this script
        absorption_chiller = AbsorptionChiller(pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Absorption_chiller"), 'double')
        CCGT_prop = calc_cop_CCGT(master_to_slave_variables.NG_Trigen_ACH_size_W, ACH_T_IN_FROM_CHP_K, "NG")
        VCC_chiller = VaporCompressionChiller(locator, scale='DISTRICT')

        # initialize variables
        Q_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_DailyStorage_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_DailyStorage_content_W = np.zeros(HOURS_IN_YEAR)
        Q_DailyStorage_to_storage_W = np.zeros(HOURS_IN_YEAR)

        E_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
        E_BaseVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
        E_PeakVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
        E_BaseVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
        E_PeakVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
        NG_Trigen_req_W = np.zeros(HOURS_IN_YEAR)
        Q_BackupVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)

        Q_Trigen_NG_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_WS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_WS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_AS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_AS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_BackupVCC_AS_directload_W = np.zeros(HOURS_IN_YEAR)

        for hour in range(HOURS_IN_YEAR):  # cooling supply for all buildings excluding cooling loads from data centers
            daily_storage.hour = hour
            if Q_thermal_req_W[hour] > 0.0:
                # only if there is a cooling load!
                daily_storage, \
                thermal_output, \
                electricity_output, \
                gas_output = cooling_resource_activator(Q_thermal_req_W[hour],
                                                        T_district_cooling_supply_K[hour],
                                                        T_district_cooling_return_K[hour],
                                                        Q_therm_Lake_W[hour],
                                                        T_source_average_Lake_K[hour],
                                                        daily_storage,
                                                        T_ground_K[hour],
                                                        master_to_slave_variables,
                                                        absorption_chiller,
                                                        CCGT_prop,
                                                        VCC_chiller)

                Q_DailyStorage_gen_directload_W[hour] = thermal_output['Q_DailyStorage_gen_directload_W']
                Q_DailyStorage_content_W[hour] = thermal_output['Q_DailyStorage_content_W']
                Q_DailyStorage_to_storage_W[hour] = thermal_output['Q_DailyStorage_to_storage_W']
                Q_Trigen_NG_gen_directload_W[hour] = thermal_output['Q_Trigen_NG_gen_directload_W']
                Q_BaseVCC_WS_gen_directload_W[hour] = thermal_output['Q_BaseVCC_WS_gen_directload_W']
                Q_PeakVCC_WS_gen_directload_W[hour] = thermal_output['Q_PeakVCC_WS_gen_directload_W']
                Q_BaseVCC_AS_gen_directload_W[hour] = thermal_output['Q_BaseVCC_AS_gen_directload_W']
                Q_PeakVCC_AS_gen_directload_W[hour] = thermal_output['Q_PeakVCC_AS_gen_directload_W']
                Q_BackupVCC_AS_directload_W[hour] = thermal_output['Q_BackupVCC_AS_directload_W']

                Q_Trigen_NG_gen_W[hour] = thermal_output['Q_Trigen_NG_gen_W']
                Q_BaseVCC_WS_gen_W[hour] = thermal_output['Q_BaseVCC_WS_gen_W']
                Q_PeakVCC_WS_gen_W[hour] = thermal_output['Q_PeakVCC_WS_gen_W']
                Q_BaseVCC_AS_gen_W[hour] = thermal_output['Q_BaseVCC_AS_gen_W']
                Q_PeakVCC_AS_gen_W[hour] = thermal_output['Q_PeakVCC_AS_gen_W']
                Q_BackupVCC_AS_gen_W[hour] = thermal_output['Q_BackupVCC_AS_gen_W']

                E_BaseVCC_WS_req_W[hour] = electricity_output['E_BaseVCC_WS_req_W']
                E_PeakVCC_WS_req_W[hour] = electricity_output['E_PeakVCC_WS_req_W']
                E_BaseVCC_AS_req_W[hour] = electricity_output['E_BaseVCC_AS_req_W']
                E_PeakVCC_AS_req_W[hour] = electricity_output['E_PeakVCC_AS_req_W']
                E_Trigen_NG_gen_W[hour] = electricity_output['E_Trigen_NG_gen_W']

                NG_Trigen_req_W[hour] = gas_output['NG_Trigen_req_W']

        #calculate the electrical capacity as a function of the peak produced by the turbine
        master_to_slave_variables.NG_Trigen_CCGT_size_electrical_W = E_Trigen_NG_gen_W.max()

        # BACK-UPP VCC - AIR SOURCE
        master_to_slave_variables.AS_BackupVCC_size_W = np.amax(Q_BackupVCC_AS_gen_W)
        size_chiller_CT = master_to_slave_variables.AS_BackupVCC_size_W
        if master_to_slave_variables.AS_BackupVCC_size_W != 0.0:
            master_to_slave_variables.AS_BackupVCC_on = 1
            Q_BackupVCC_AS_gen_W, E_BackupVCC_AS_req_W = np.vectorize(calc_vcc_CT_operation)(Q_BackupVCC_AS_gen_W,
                                                                                             T_district_cooling_return_K,
                                                                                             T_district_cooling_supply_K,
                                                                                             VCC_T_COOL_IN,
                                                                                             size_chiller_CT,
                                                                                             VCC_chiller)
        else:
            E_BackupVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)

        # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR, ANNUAL) GENERATION UNITS
        supply_systems = SupplySystemsDatabase(locator)
        mdotnMax_kgpers = np.amax(mdot_kgpers)
        performance_costs_generation, \
        district_cooling_capacity_installed = cost_model.calc_generation_costs_capacity_installed_cooling(locator,
                                                                                                          master_to_slave_variables,
                                                                                                          supply_systems,
                                                                                                          mdotnMax_kgpers
                                                                                                          )
        # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR, ANNUAL) STORAGE UNITS
        performance_costs_storage = cost_model.calc_generation_costs_cooling_storage(master_to_slave_variables,
                                                                                     daily_storage
                                                                                     )

        # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR, ANNUAL) NETWORK
        performance_costs_network, \
        E_used_district_cooling_network_W = cost_model.calc_network_costs_cooling(locator,
                                                                                  master_to_slave_variables,
                                                                                  network_features,
                                                                                  "DC")

        # MERGE COSTS AND EMISSIONS IN ONE FILE
        performance = dict(performance_costs_generation, **performance_costs_storage)
        district_cooling_costs = dict(performance, **performance_costs_network)
    else:
        Q_thermal_req_W = np.zeros(HOURS_IN_YEAR)
        Q_DailyStorage_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_DailyStorage_content_W = np.zeros(HOURS_IN_YEAR)
        Q_DailyStorage_to_storage_W = np.zeros(HOURS_IN_YEAR)
        Q_Trigen_NG_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_WS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_WS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_AS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_AS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_BackupVCC_AS_directload_W = np.zeros(HOURS_IN_YEAR)
        Q_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_BaseVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_PeakVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
        Q_BackupVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
        E_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
        E_used_district_cooling_network_W = np.zeros(HOURS_IN_YEAR)
        E_BaseVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
        E_PeakVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
        E_BaseVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
        E_PeakVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
        E_BackupVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
        NG_Trigen_req_W = np.zeros(HOURS_IN_YEAR)
        district_cooling_costs = {}
        district_cooling_capacity_installed = {}

    # SAVE
    district_cooling_generation_dispatch = {
        # demand of the network
        "Q_districtcooling_sys_req_W": Q_thermal_req_W,

        # ENERGY GENERATION TO DIRECT LOAD
        # from storage
        "Q_DailyStorage_gen_directload_W": Q_DailyStorage_gen_directload_W,
        "Q_DailyStorage_content_W": Q_DailyStorage_content_W,
        "Q_DailyStorage_to_storage_W": Q_DailyStorage_to_storage_W,

        # cooling
        "Q_Trigen_NG_gen_directload_W": Q_Trigen_NG_gen_directload_W,
        "Q_BaseVCC_WS_gen_directload_W": Q_BaseVCC_WS_gen_directload_W,
        "Q_PeakVCC_WS_gen_directload_W": Q_PeakVCC_WS_gen_directload_W,
        "Q_BaseVCC_AS_gen_directload_W": Q_BaseVCC_AS_gen_directload_W,
        "Q_PeakVCC_AS_gen_directload_W": Q_PeakVCC_AS_gen_directload_W,
        "Q_BackupVCC_AS_directload_W": Q_BackupVCC_AS_directload_W,

        # ENERGY GENERATION TOTAL
        # cooling
        "Q_Trigen_NG_gen_W": Q_Trigen_NG_gen_W,
        "Q_BaseVCC_WS_gen_W": Q_BaseVCC_WS_gen_W,
        "Q_PeakVCC_WS_gen_W": Q_PeakVCC_WS_gen_W,
        "Q_BaseVCC_AS_gen_W": Q_BaseVCC_AS_gen_W,
        "Q_PeakVCC_AS_gen_W": Q_PeakVCC_AS_gen_W,
        "Q_BackupVCC_AS_W": Q_BackupVCC_AS_gen_W,

        # electricity
        "E_Trigen_NG_gen_W": E_Trigen_NG_gen_W
    }

    district_cooling_electricity_requirements_dispatch = {
        # ENERGY REQUIREMENTS
        # Electricity
        "E_DCN_req_W": E_used_district_cooling_network_W,
        "E_BaseVCC_WS_req_W": E_BaseVCC_WS_req_W,
        "E_PeakVCC_WS_req_W": E_PeakVCC_WS_req_W,
        "E_BaseVCC_AS_req_W": E_BaseVCC_AS_req_W,
        "E_PeakVCC_AS_req_W": E_PeakVCC_AS_req_W,
        "E_BackupVCC_AS_req_W": E_BackupVCC_AS_req_W,
    }

    district_cooling_fuel_requirements_dispatch = {
        # fuels
        "NG_Trigen_req_W": NG_Trigen_req_W
    }

    # PLOT RESULTS

    return district_cooling_costs, \
           district_cooling_generation_dispatch, \
           district_cooling_electricity_requirements_dispatch, \
           district_cooling_fuel_requirements_dispatch, \
           district_cooling_capacity_installed



def calc_network_summary_DCN(master_to_slave_vars):

    # if there is a district heating network on site and there is server_heating
    district_heating_network = master_to_slave_vars.DHN_exists
    df = master_to_slave_vars.DC_network_summary_individual
    df = df.fillna(0)
    if district_heating_network and master_to_slave_vars.WasteServersHeatRecovery == 1:
        T_sup_K = df['T_DCNf_space_cooling_and_refrigeration_sup_K'].values
        T_re_K = df['T_DCNf_space_cooling_and_refrigeration_re_K'].values
        mdot_kgpers = df['mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers'].values
        Q_cooling_req_W = df['Q_DCNf_space_cooling_and_refrigeration_W'].values
    else:
        T_sup_K = df['T_DCNf_space_cooling_data_center_and_refrigeration_sup_K'].values
        T_re_K = df['T_DCNf_space_cooling_data_center_and_refrigeration_re_K'].values
        mdot_kgpers = df['mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers'].values
        Q_cooling_req_W = df['Q_DCNf_space_cooling_data_center_and_refrigeration_W'].values

    return Q_cooling_req_W, T_re_K, T_sup_K, mdot_kgpers
