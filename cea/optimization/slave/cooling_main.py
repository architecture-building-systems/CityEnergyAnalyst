"""
Disctrict Cooling Network Calculations.

Calculate which technologies need to be activated to meet the cooling energy demand and determine the cost and emissions
that result from the activation of these cooling technologies.
"""

import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.optimization.constants import VCC_T_COOL_IN, ACH_T_IN_FROM_CHP_K
from cea.optimization.master import objective_function_calculator
from cea.optimization.slave.cooling_resource_activation import calc_vcc_CT_operation, cooling_resource_activator
from cea.technologies.storage_tank_pcm import Storage_tank_PCM
from cea.technologies.chiller_vapor_compression import VaporCompressionChiller
from cea.technologies.cogeneration import calc_cop_CCGT
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
                             config,
                             master_to_slave_variables,
                             network_features,
                             weather_features):
    """
    Computes the parameters for the cooling of the complete DCN, including:
     - cost for cooling energy supply
     - hourly cooling energy supply
     - hourly electricity generation (from trigen) and demand (for VCCs)
     - hourly combustion fuel demand (for trigen)
     - hourly heat release of the cooling generation
     - installed capacity of each cooling technology

    :param locator: paths to cea input files and results folders
    :param master_to_slave_variables: all the important information on the energy system configuration of an individual
                                      (buildings [connected, non-connected], heating technologies, cooling technologies,
                                      storage etc.)
    :param config: configurations of cea
    :param network_features: characteristic parameters (pumping energy, mass flow rate, thermal losses & piping cost)
                             of the district cooling/heating network
    :param weather_features: important environmental parameters (e.g. ambient & ground temperature)

    :type locator: cea.inputlocator.InputLocator class object
    :type master_to_slave_variables: cea.optimization.slave_data.SlaveData class object
    :type config: cea.config.Configuration class object
    :type network_features: cea.optimization.distribution.network_optimization_features.NetworkOptimizationFeatures
                            class object
    :type weather_features: cea.optimization.preprocessing.preprocessing_main.WeatherFeatures class object

    :return district_cooling_costs: costs of all district cooling energy technologies (investment and operational costs
                                    of generation, storage and network)
    :return district_cooling_generation_dispatch: hourly thermal energy supply by each component of the district
                                                  cooling energy system.
    :return district_cooling_electricity_requirements_dispatch: hourly electricity demand of each component of the
                                                                district cooling energy generation system.
    :return district_cooling_fuel_requirements_dispatch: hourly combustion fuel demand of each component of the
                                                         district cooling energy system (i.e. in the current setup only
                                                         natural gas demand of the CCGT of the trigeneration system)
    :return district_cooling_capacity_installed: capacity of each district-scale cooling technology installed
                                                 (corresponding to the given individual)

    :rtype district_cooling_costs: dict (27 x float)
    :rtype district_cooling_generation_dispatch: dict (15 x 8760-ndarray)
    :rtype district_cooling_electricity_requirements_dispatch: dict (6 x 8760-ndarray)
    :rtype district_cooling_fuel_requirements_dispatch: dict (1 x 8760-ndarray)
    :rtype district_cooling_capacity_installed: dict (9 x float)
    """

    Q_thermal_req_W = np.zeros(HOURS_IN_YEAR)
    Q_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BackupVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)

    Q_DailyStorage_content_W = np.zeros(HOURS_IN_YEAR)
    Q_DailyStorage_to_storage_W = np.zeros(HOURS_IN_YEAR)
    Q_DailyStorage_from_storage_W = np.zeros(HOURS_IN_YEAR)

    E_used_district_cooling_network_W = np.zeros(HOURS_IN_YEAR)
    E_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
    E_ACH_req_W = np.zeros(HOURS_IN_YEAR)
    E_BaseVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
    E_PeakVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
    E_BaseVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
    E_PeakVCC_WS_req_W = np.zeros(HOURS_IN_YEAR)
    E_BackupVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)

    NG_Trigen_req_W = np.zeros(HOURS_IN_YEAR)

    Q_Trigen_NG_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseVCC_WS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakVCC_WS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseVCC_AS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakVCC_AS_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    Q_BackupVCC_AS_directload_W = np.zeros(HOURS_IN_YEAR)

    Q_release_Trigen_NG_W = np.zeros(HOURS_IN_YEAR)
    Q_release_BaseVCC_WS_W = np.zeros(HOURS_IN_YEAR)
    Q_release_PeakVCC_WS_W = np.zeros(HOURS_IN_YEAR)
    Q_release_FreeCooling_W = np.zeros(HOURS_IN_YEAR)
    Q_release_BaseVCC_AS_W = np.zeros(HOURS_IN_YEAR)
    Q_release_PeakVCC_AS_W = np.zeros(HOURS_IN_YEAR)
    Q_release_BackupVCC_AS_W = np.zeros(HOURS_IN_YEAR)

    district_cooling_costs = {}
    district_cooling_capacity_installed = {}

    if master_to_slave_variables.DCN_exists:
        print("DISTRICT COOLING OPERATION")
        # THERMAL STORAGE + NETWORK
        # Import Temperatures from Network Summary:
        Q_thermal_req_W, \
        T_district_cooling_return_K, \
        T_district_cooling_supply_K, \
        mdot_kgpers = calc_network_summary_DCN(master_to_slave_variables)

        # Initialize daily storage class
        T_ground_K = weather_features.ground_temp
        daily_storage = Storage_tank_PCM(activation=master_to_slave_variables.Storage_cooling_on,
                                         size_Wh=master_to_slave_variables.Storage_cooling_size_W,
                                         database_model_parameters= pd.read_excel(locator.get_database_conversion_systems(), sheet_name="TES"),
                                         T_ambient_K = np.average(T_ground_K),
                                         type_storage = config.optimization.cold_storage_type,
                                         debug = master_to_slave_variables.debug
                                         )


        # Import Data - cooling energy potential from water bodies
        if master_to_slave_variables.WS_BaseVCC_on == 1 or master_to_slave_variables.WS_PeakVCC_on == 1:
            water_body_potential = pd.read_csv(locator.get_water_body_potential())
            Q_therm_water_body = np.array(water_body_potential['QLake_kW']) * 1E3
            total_WS_VCC_installed = master_to_slave_variables.WS_BaseVCC_size_W + \
                                     master_to_slave_variables.WS_PeakVCC_size_W
            # TODO: the following line assumes that the thermal energy from the water body is used 1:1 by the VCC.
            #  i.e. thermal_energy_in = thermal_energy_out for the VCC. Check if this assumption is correct.
            Q_therm_water_body_W = [x if x < total_WS_VCC_installed else total_WS_VCC_installed for x in
                                    Q_therm_water_body]
            T_source_average_water_body_K = np.array(water_body_potential['Ts_C']) + 273
        else:
            Q_therm_water_body_W = np.zeros(HOURS_IN_YEAR)
            T_source_average_water_body_K = np.zeros(HOURS_IN_YEAR)

        # get properties of technology used in this script
        absorption_chiller = AbsorptionChiller(
            pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Absorption_chiller"), 'double')
        CCGT_prop = calc_cop_CCGT(master_to_slave_variables.NG_Trigen_ACH_size_W, ACH_T_IN_FROM_CHP_K, "NG")
        VC_chiller = VaporCompressionChiller(locator, scale='DISTRICT')

        for hour in range(HOURS_IN_YEAR):  # cooling supply for all buildings excluding cooling loads from data centers
            daily_storage.hour = hour
            if master_to_slave_variables.debug is True:
                print("\nHour {:.0f}".format(hour))
            if Q_thermal_req_W[hour] > 0.0:
                # only if there is a cooling load!
                daily_storage, \
                thermal_output, \
                electricity_output, \
                gas_output = cooling_resource_activator(Q_thermal_req_W[hour],
                                                        T_district_cooling_supply_K[hour],
                                                        T_district_cooling_return_K[hour],
                                                        Q_therm_water_body_W[hour],
                                                        T_source_average_water_body_K[hour],
                                                        T_ground_K[hour],
                                                        daily_storage,
                                                        absorption_chiller,
                                                        VC_chiller,
                                                        CCGT_prop,
                                                        master_to_slave_variables)

                Q_DailyStorage_content_W[hour] = thermal_output['Qc_DailyStorage_content_W']
                Q_DailyStorage_to_storage_W[hour] = thermal_output['Qc_DailyStorage_to_storage_W']
                Q_DailyStorage_from_storage_W[hour] = thermal_output['Qc_DailyStorage_from_storage_W']

                Q_Trigen_NG_gen_directload_W[hour] = thermal_output['Qc_Trigen_NG_gen_directload_W']
                Q_BaseVCC_WS_gen_directload_W[hour] = thermal_output['Qc_BaseVCC_WS_gen_directload_W']
                Q_PeakVCC_WS_gen_directload_W[hour] = thermal_output['Qc_PeakVCC_WS_gen_directload_W']
                Q_BaseVCC_AS_gen_directload_W[hour] = thermal_output['Qc_BaseVCC_AS_gen_directload_W']
                Q_PeakVCC_AS_gen_directload_W[hour] = thermal_output['Qc_PeakVCC_AS_gen_directload_W']
                Q_BackupVCC_AS_directload_W[hour] = thermal_output['Qc_BackupVCC_AS_directload_W']

                Q_Trigen_NG_gen_W[hour] = thermal_output['Qc_Trigen_NG_gen_W']
                Q_BaseVCC_WS_gen_W[hour] = thermal_output['Qc_BaseVCC_WS_gen_W']
                Q_PeakVCC_WS_gen_W[hour] = thermal_output['Qc_PeakVCC_WS_gen_W']
                Q_BaseVCC_AS_gen_W[hour] = thermal_output['Qc_BaseVCC_AS_gen_W']
                Q_PeakVCC_AS_gen_W[hour] = thermal_output['Qc_PeakVCC_AS_gen_W']
                Q_BackupVCC_AS_gen_W[hour] = thermal_output['Qc_BackupVCC_AS_gen_W']

                E_ACH_req_W[hour] = electricity_output['E_ACH_req_W']
                E_BaseVCC_WS_req_W[hour] = electricity_output['E_BaseVCC_WS_req_W']
                E_PeakVCC_WS_req_W[hour] = electricity_output['E_PeakVCC_WS_req_W']
                E_BaseVCC_AS_req_W[hour] = electricity_output['E_BaseVCC_AS_req_W']
                E_PeakVCC_AS_req_W[hour] = electricity_output['E_PeakVCC_AS_req_W']
                E_Trigen_NG_gen_W[hour] = electricity_output['E_Trigen_NG_gen_W']

                NG_Trigen_req_W[hour] = gas_output['NG_Trigen_req_W']

                Q_release_Trigen_NG_W[hour] = thermal_output["Q_release_Trigen_W"]
                Q_release_BaseVCC_WS_W[hour] = thermal_output["Q_release_BaseVCC_WS_W"]
                Q_release_PeakVCC_WS_W[hour] = thermal_output["Q_release_PeakVCC_WS_W"]
                Q_release_FreeCooling_W[hour] = thermal_output["Q_release_FreeCooling_W"]
                Q_release_BaseVCC_AS_W[hour] = thermal_output["Q_release_BaseVCC_CT_W"]
                Q_release_PeakVCC_AS_W[hour] = thermal_output["Q_release_PeakVCC_CT_W"]

        # calculate the electrical capacity as a function of the peak produced by the turbine
        master_to_slave_variables.NG_Trigen_CCGT_size_electrical_W = E_Trigen_NG_gen_W.max()

        # BACK-UPP VCC - AIR SOURCE
        master_to_slave_variables.AS_BackupVCC_size_W = np.amax(Q_BackupVCC_AS_gen_W)
        size_chiller_CT = master_to_slave_variables.AS_BackupVCC_size_W
        if master_to_slave_variables.AS_BackupVCC_size_W != 0.0:
            master_to_slave_variables.AS_BackupVCC_on = 1
            Q_BackupVCC_AS_gen_W, \
            E_BackupVCC_AS_req_W = np.vectorize(calc_vcc_CT_operation)(Q_BackupVCC_AS_gen_W,
                                                                       T_district_cooling_return_K,
                                                                       T_district_cooling_supply_K,
                                                                       VCC_T_COOL_IN,
                                                                       size_chiller_CT,
                                                                       VC_chiller)
            Q_release_BackupVCC_AS_W = Q_BackupVCC_AS_gen_W + E_BackupVCC_AS_req_W
        else:
            E_BackupVCC_AS_req_W = np.zeros(HOURS_IN_YEAR)
            Q_release_BackupVCC_AS_W = np.zeros(HOURS_IN_YEAR)

        # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR, ANNUAL) GENERATION UNITS
        supply_systems = SupplySystemsDatabase(locator)
        mdotnMax_kgpers = np.amax(mdot_kgpers)
        performance_costs_generation, \
        district_cooling_capacity_installed \
            = objective_function_calculator.calc_generation_costs_capacity_installed_cooling(locator,
                                                                                             master_to_slave_variables,
                                                                                             supply_systems,
                                                                                             mdotnMax_kgpers
                                                                                             )
        # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR, ANNUAL) STORAGE UNITS
        performance_costs_storage = \
            objective_function_calculator.calc_generation_costs_cooling_storage(master_to_slave_variables,
                                                                                daily_storage
                                                                                )

        # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR, ANNUAL) NETWORK
        performance_costs_network, \
        E_used_district_cooling_network_W = \
            objective_function_calculator.calc_network_costs_cooling(locator,
                                                                     master_to_slave_variables,
                                                                     network_features,
                                                                     "DC")

        # MERGE COSTS AND EMISSIONS IN ONE FILE
        performance = dict(performance_costs_generation, **performance_costs_storage)
        district_cooling_costs = dict(performance, **performance_costs_network)

    # SAVE
    district_cooling_generation_dispatch = {
        # demand of the network
        "Q_districtcooling_sys_req_W": Q_thermal_req_W,

        # ENERGY GENERATION TO DIRECT LOAD
        # from storage
        "Q_DailyStorage_content_W": Q_DailyStorage_content_W,
        "Q_DailyStorage_to_storage_W": Q_DailyStorage_to_storage_W,
        "Q_DailyStorage_gen_directload_W": Q_DailyStorage_from_storage_W,

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
        "E_ACH_req_W": E_ACH_req_W,
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

    district_cooling_heat_release = {
        # (anthropogenic) heat release from district cooling activation
        "Q_release_Trigen_NG_W": Q_release_Trigen_NG_W,
        "Q_release_BaseVCC_WS_W": Q_release_BaseVCC_WS_W,
        "Q_release_PeakVCC_WS_W": Q_release_PeakVCC_WS_W,
        "Q_release_FreeCooling_W": Q_release_FreeCooling_W,
        "Q_release_BaseVCC_AS_W": Q_release_BaseVCC_AS_W,
        "Q_release_PeakVCC_AS_W": Q_release_PeakVCC_AS_W,
        "Q_release_BackupVCC_AS_W": Q_release_BackupVCC_AS_W,
    }

    # PLOT RESULTS

    return district_cooling_costs, \
           district_cooling_generation_dispatch, \
           district_cooling_electricity_requirements_dispatch, \
           district_cooling_fuel_requirements_dispatch, \
           district_cooling_heat_release, \
           district_cooling_capacity_installed


def calc_network_summary_DCN(master_to_slave_vars):
    # if there is a district cooling network on site and there is server_heating
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
