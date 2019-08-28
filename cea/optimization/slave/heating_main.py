"""
FIND LEAST COST FUNCTION
USING PRESET ORDER

"""

from __future__ import division

import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.optimization.master import cost_model
from cea.optimization.master.emissions_model import calc_emissions_Whyr_to_tonCO2yr, calc_pen_Whyr_to_MJoilyr
from cea.optimization.slave.heating_resource_activation import heating_source_activator
from cea.optimization.slave.seasonal_storage import storage_main
from cea.technologies.boiler import cond_boiler_op_cost

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Tim Vollrath", "Thuy-An Nguyen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# ==============================
# least_cost main optimization
# ==============================

def district_heating_network(locator,
                             master_to_slave_variables,
                             config,
                             prices,
                             lca,
                             network_features):
    """
    Computes the parameters for the heating of the complete DHN

    :param locator: locator class
    :param master_to_slave_variables: class MastertoSlaveVars containing the value of variables to be passed to the
        slave optimization for each individual
    :param solar_features: solar features class
    :param gv: global variables class
    :type locator: class
    :type master_to_slave_variables: class
    :type solar_features: class
    :type gv: class
    :return:
        - E_oil_eq_MJ: MJ oil Equivalent used during operation
        - CO2_kg_eq: kg of CO2-Equivalent emitted during operation
        - cost_sum: total cost in CHF used for operation
        - Q_source_data[:,7]: uncovered demand

    :rtype: float, float, float, array

    """
    # THERMAL STORAGE + NETWORK
    print("CALCULATING ECOLOGICAL COSTS OF SEASONAL STORAGE - DUE TO OPERATION (IF ANY)")
    performance_storage, storage_dispatch = storage_main.storage_optimization(locator,
                                                                              master_to_slave_variables,
                                                                              lca, prices,
                                                                              config)
    # Import data from storage optimization
    Q_DH_networkload_W = np.array(storage_dispatch['Q_DH_networkload_W'])
    Q_thermal_req_W = np.array(storage_dispatch['Q_req_after_storage_W'])

    E_PVT_gen_W = storage_dispatch['E_PVT_gen_W']

    Q_PVT_to_directload_W = storage_dispatch["Q_PVT_gen_directload_W"]
    Q_PVT_to_storage_W = storage_dispatch["Q_PVT_gen_storage_W"]

    Q_SC_ET_to_directload_W = storage_dispatch["Q_SC_ET_gen_directload_W"]
    Q_SC_ET_to_storage_W = storage_dispatch["Q_SC_ET_gen_storage_W"]

    Q_SC_FP_to_directload_W = storage_dispatch["Q_SC_FP_gen_directload_W"]
    Q_SC_FP_to_storage_W = storage_dispatch["Q_SC_FP_gen_storage_W"]

    Q_HP_Server_to_directload_W = storage_dispatch["Q_HP_Server_gen_directload_W"]
    Q_HP_Server_to_storage_W = storage_dispatch["Q_HP_Server_gen_storage_W"]

    E_Storage_req_charging_W = storage_dispatch["E_Storage_charging_req_W"]
    E_Storage_req_discharging_W = storage_dispatch["E_Storage_discharging_req_W"]
    E_HP_SC_FP_req_W = storage_dispatch["E_HP_SC_FP_req_W"]
    E_HP_SC_ET_req_W = storage_dispatch["E_HP_SC_ET_req_W"]
    E_HP_PVT_req_W = storage_dispatch["E_HP_PVT_req_W"]
    E_HP_Server_req_W = storage_dispatch["E_HP_Server_req_W"]

    Q_SC_ET_gen_W = storage_dispatch["Q_SC_ET_gen_W"]
    Q_SC_FP_gen_W = storage_dispatch["Q_SC_FP_gen_W"]
    Q_PVT_gen_W = storage_dispatch["Q_PVT_gen_W"]
    Q_Server_gen_W = storage_dispatch["Q_HP_Server_gen_W"]

    Q_Storage_gen_W = storage_dispatch["Q_Storage_gen_W"]

    # HEATING PLANT
    # Import Temperatures from Network Summary:
    mdot_DH_kgpers, T_district_heating_return_K, T_district_heating_supply_K = calc_network_summary_DHN(locator,
                                                                                                        master_to_slave_variables)

    # FIXED ORDER ACTIVATION STARTS
    # Import Data - Sewage heat
    if master_to_slave_variables.HPSew_on == 1:
        HPSew_Data = pd.read_csv(locator.get_sewage_heat_potential())
        Q_therm_Sew = np.array(HPSew_Data['Qsw_kW']) * 1E3
        Q_therm_Sew_W = [
            x if x < master_to_slave_variables.HPSew_maxSize_W else master_to_slave_variables.HPSew_maxSize_W for x in
            Q_therm_Sew]
        T_source_average_sewage_K = np.array(HPSew_Data['Ts_C']) + 273
    else:
        Q_therm_Sew_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_sewage_K = np.zeros(HOURS_IN_YEAR)

    # Import Data - lake heat
    if master_to_slave_variables.HPLake_on == 1:
        HPlake_Data = pd.read_csv(locator.get_lake_potential())
        Q_therm_Lake = np.array(HPlake_Data['QLake_kW']) * 1E3
        Q_therm_Lake_W = [
            x if x < master_to_slave_variables.HPLake_maxSize_W else master_to_slave_variables.HPLake_maxSize_W for x in
            Q_therm_Lake]
        T_source_average_Lake_K = np.array(HPlake_Data['Ts_C']) + 273
    else:
        Q_therm_Lake_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_Lake_K = np.zeros(HOURS_IN_YEAR)

    # Import Data - geothermal (shallow)
    if master_to_slave_variables.GHP_on == 1:
        GHP_Data = pd.read_csv(locator.get_geothermal_potential())
        Q_therm_GHP = np.array(GHP_Data['QGHP_kW']) * 1E3
        Q_therm_GHP_W = [x if x < master_to_slave_variables.GHP_maxSize_W else master_to_slave_variables.GHP_maxSize_W
                         for x in Q_therm_GHP]
        T_source_average_GHP_W = np.array(GHP_Data['Ts_C']) + 273
    else:
        Q_therm_GHP_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_GHP_W = np.zeros(HOURS_IN_YEAR)

    # Initiation of the variables

    source_HP_Sewage = np.zeros(HOURS_IN_YEAR)
    source_HP_Lake = np.zeros(HOURS_IN_YEAR)
    source_GHP = np.zeros(HOURS_IN_YEAR)
    source_CHP = np.zeros(HOURS_IN_YEAR)
    source_Furnace_dry = np.zeros(HOURS_IN_YEAR)
    source_Furnace_wet = np.zeros(HOURS_IN_YEAR)
    source_BaseBoiler = np.zeros(HOURS_IN_YEAR)
    source_PeakBoiler = np.zeros(HOURS_IN_YEAR)

    Q_HPSew_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_HPLake_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_GHP_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_CHP_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_Furnace_dry_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_Furnace_wet_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseBoiler_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakBoiler_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_AddBoiler_gen_W = np.zeros(HOURS_IN_YEAR)

    E_HPSew_req_W = np.zeros(HOURS_IN_YEAR)
    E_HPLake_req_W = np.zeros(HOURS_IN_YEAR)
    E_GHP_req_W = np.zeros(HOURS_IN_YEAR)
    E_CHP_gen_W = np.zeros(HOURS_IN_YEAR)
    E_Furnace_dry_gen_W = np.zeros(HOURS_IN_YEAR)
    E_Furnace_wet_gen_W = np.zeros(HOURS_IN_YEAR)
    E_BaseBoiler_req_W = np.zeros(HOURS_IN_YEAR)
    E_PeakBoiler_req_W = np.zeros(HOURS_IN_YEAR)
    E_BackupBoiler_req_W = np.zeros(HOURS_IN_YEAR)

    NG_CHP_req_W = np.zeros(HOURS_IN_YEAR)
    NG_BaseBoiler_req_W = np.zeros(HOURS_IN_YEAR)
    NG_PeakBoiler_req_W = np.zeros(HOURS_IN_YEAR)
    NG_BackupBoiler_req_W = np.zeros(HOURS_IN_YEAR)

    WetBiomass_Furnace_req_W = np.zeros(HOURS_IN_YEAR)
    DryBiomass_Furnace_req_W = np.zeros(HOURS_IN_YEAR)

    for hour in range(HOURS_IN_YEAR):
        if Q_thermal_req_W[hour] > 0.0:
            activation_output, \
            thermal_output, \
            electricity_output, \
            gas_output, \
            biomass_output = heating_source_activator(Q_thermal_req_W[hour],
                                                      hour,
                                                      master_to_slave_variables,
                                                      Q_therm_GHP_W[hour],
                                                      T_source_average_GHP_W[hour],
                                                      T_source_average_Lake_K[hour],
                                                      Q_therm_Lake_W[hour],
                                                      Q_therm_Sew_W[hour],
                                                      T_source_average_sewage_K[hour],
                                                      T_district_heating_supply_K[hour],
                                                      T_district_heating_return_K[hour],
                                                      prices,
                                                      lca)

            source_HP_Sewage[hour] = activation_output['Source_HP_Sewage']
            source_HP_Lake[hour] = activation_output['Source_HP_Lake']
            source_GHP[hour] = activation_output['Source_GHP']
            source_CHP[hour] = activation_output['Source_CHP']
            source_Furnace_dry[hour] = activation_output['Source_Furnace_dry']
            source_Furnace_wet[hour] = activation_output['Source_Furnace_wet']
            source_BaseBoiler[hour] = activation_output['Source_BaseBoiler']
            source_PeakBoiler[hour] = activation_output['Source_PeakBoiler']

            Q_HPSew_gen_W[hour] = thermal_output['Q_HPSew_gen_W']
            Q_HPLake_gen_W[hour] = thermal_output['Q_HPLake_gen_W']
            Q_GHP_gen_W[hour] = thermal_output['Q_GHP_gen_W']
            Q_CHP_gen_W[hour] = thermal_output['Q_CHP_gen_W']
            Q_Furnace_dry_gen_W[hour] = thermal_output['Q_Furnace_dry_gen_W']
            Q_Furnace_wet_gen_W[hour] = thermal_output['Q_Furnace_wet_gen_W']
            Q_BaseBoiler_gen_W[hour] = thermal_output['Q_BaseBoiler_gen_W']
            Q_PeakBoiler_gen_W[hour] = thermal_output['Q_PeakBoiler_gen_W']
            Q_AddBoiler_gen_W[hour] = thermal_output['Q_AddBoiler_gen_W']

            E_HPSew_req_W[hour] = electricity_output['E_HPSew_req_W']
            E_HPLake_req_W[hour] = electricity_output['E_HPLake_req_W']
            E_GHP_req_W[hour] = electricity_output['E_GHP_req_W']
            E_CHP_gen_W[hour] = electricity_output['E_CHP_gen_W']
            E_BaseBoiler_req_W[hour] = electricity_output['E_BaseBoiler_req_W']
            E_PeakBoiler_req_W[hour] = electricity_output['E_PeakBoiler_req_W']

            E_Furnace_dry_gen_W[hour] = electricity_output['E_Furnace_dry_gen_W']
            E_Furnace_wet_gen_W[hour] = electricity_output['E_Furnace_wet_gen_W']

            NG_CHP_req_W[hour] = gas_output['Gas_CHP_req_W']
            NG_BaseBoiler_req_W[hour] = gas_output['Gas_BaseBoiler_req_W']
            NG_PeakBoiler_req_W[hour] = gas_output['Gas_PeakBoiler_req_W']
            WetBiomass_Furnace_req_W[hour] = biomass_output['Biomass_Furnace_dry_req_W']
            DryBiomass_Furnace_req_W[hour] = biomass_output['Biomass_Furnace_wet_req_W']

    # BACK-UP BOILER
    master_to_slave_variables.BackupBoiler_size_W = np.amax(Q_AddBoiler_gen_W)
    if master_to_slave_variables.BackupBoiler_size_W != 0:
        master_to_slave_variables.BackupBoiler_on = 1
        for hour in range(HOURS_IN_YEAR):
            tdhret_req_K = T_district_heating_return_K[hour]
            _, \
            _, \
            NG_BackupBoiler_req_W[hour], \
            E_BackupBoiler_req_W[hour] = cond_boiler_op_cost(Q_AddBoiler_gen_W[hour],
                                                             master_to_slave_variables.BackupBoiler_size_W,
                                                             tdhret_req_K,
                                                             "NG",
                                                             prices, lca, hour)

    # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR) GENERATION UNITS
    performance_costs_generation = cost_model.calc_generation_costs_heating(locator,
                                                                            master_to_slave_variables,
                                                                            config,
                                                                            storage_dispatch,
                                                                            )

    # CAPEX (ANNUAL, TOTAL) AND OPEX (FIXED, VAR) NETWORK
    performance_costs_network, \
    E_used_district_heating_network_W = cost_model.calc_network_costs_heating(locator,
                                                                              master_to_slave_variables,
                                                                              network_features,
                                                                              lca,
                                                                              "DH")


    # MERGE COSTS AND EMISSIONS IN ONE FILE
    district_heating_costs = dict(performance_costs_generation, **performance_costs_network)

    # save data
    district_heating_generation_dispatch = {

        # demand of the network:
        "Q_districtheating_sys_req_W": Q_DH_networkload_W,

        # Status of each technology 1 = on, 0 = off in every hour
        "HPSew_Status": source_HP_Sewage,
        "HPLake_Status": source_HP_Lake,
        "GHP_Status": source_GHP,
        "CHP_Status": source_CHP,
        "Furnace_dry_Status": source_Furnace_dry,
        "Furnace_wet_Status": source_Furnace_wet,
        "BoilerBase_Status": source_BaseBoiler,
        "BoilerPeak_Status": source_PeakBoiler,

        # ENERGY GENERATION
        # heating
        "Q_PVT_gen_storage_W": Q_PVT_to_storage_W,
        "Q_SC_ET_gen_storage_W": Q_SC_ET_to_storage_W,
        "Q_SC_FP_gen_storage_W": Q_SC_FP_to_storage_W,
        "Q_HP_Server_storage_W": Q_HP_Server_to_storage_W,

        # this is what is generated out of all the technologies sent to the storage
        "Q_Storage_gen_directload_W": Q_Storage_gen_W,
        # heating
        "Q_PVT_gen_directload_W": Q_PVT_to_directload_W,
        "Q_SC_ET_gen_directload_W": Q_SC_ET_to_directload_W,
        "Q_SC_FP_gen_directload_W": Q_SC_FP_to_directload_W,
        "Q_HP_Server_gen_directload_W": Q_HP_Server_to_directload_W,
        "Q_HP_Sew_gen_directload_W": Q_HPSew_gen_W,
        "Q_HP_Lake_gen_directload_W": Q_HPLake_gen_W,
        "Q_GHP_gen_directload_W": Q_GHP_gen_W,
        "Q_CHP_gen_directload_W": Q_CHP_gen_W,
        "Q_Furnace_dry_gen_directload_W": Q_Furnace_dry_gen_W,
        "Q_Furnace_wet_gen_directload_W": Q_Furnace_wet_gen_W,
        "Q_BaseBoiler_gen_directload_W": Q_BaseBoiler_gen_W,
        "Q_PeakBoiler_gen_directload_W": Q_PeakBoiler_gen_W,
        "Q_BackupBoiler_gen_directload_W": Q_AddBoiler_gen_W,

        # electricity
        "E_CHP_gen_W": E_CHP_gen_W,
        "E_PVT_gen_W": E_PVT_gen_W,
        "E_Furnace_dry_gen_W": E_Furnace_dry_gen_W,
        "E_Furnace_wet_gen_W": E_Furnace_wet_gen_W,
    }

    district_heating_electricity_requirements_dispatch = {
        # ENERGY REQUIREMENTS
        # Electricity
        "E_Storage_charging_req_W": E_Storage_req_charging_W,
        "E_Storage_discharging_req_W": E_Storage_req_discharging_W,
        "E_DHN_req_W": E_used_district_heating_network_W,
        "E_HP_SC_FP_req_W": E_HP_SC_FP_req_W,
        "E_HP_SC_ET_req_W": E_HP_SC_ET_req_W,
        "E_HP_PVT_req_W": E_HP_PVT_req_W,
        "E_HP_Server_req_W": E_HP_Server_req_W,
        "E_HP_Sew_req_W": E_HPSew_req_W,
        "E_HP_Lake_req_W": E_HPLake_req_W,
        "E_GHP_req_W": E_GHP_req_W,
        "E_BaseBoiler_req_W": E_BaseBoiler_req_W,
        "E_PeakBoiler_req_W": E_PeakBoiler_req_W,
        "E_BackupBoiler_req_W": E_BackupBoiler_req_W,
    }
    district_heating_fuel_requirements_dispatch = {
        # FUEL REQUIREMENTS
        "NG_CHP_req_W": NG_CHP_req_W,
        "NG_BaseBoiler_req_W": NG_BaseBoiler_req_W,
        "NG_PeakBoiler_req_W": NG_PeakBoiler_req_W,
        "NG_BackupBoiler_req_W": NG_BackupBoiler_req_W,
        "WB_Furnace_req_W": WetBiomass_Furnace_req_W,
        "DB_Furnace_req_W": DryBiomass_Furnace_req_W,
    }

    return district_heating_costs, \
           district_heating_generation_dispatch, \
           district_heating_electricity_requirements_dispatch,\
           district_heating_fuel_requirements_dispatch


def calc_network_summary_DHN(locator, master_to_slave_vars):
    network_data = pd.read_csv(
        locator.get_optimization_thermal_network_data_file(master_to_slave_vars.network_data_file_heating))
    tdhret_K = network_data['T_DHNf_re_K']
    mdot_DH_kgpers = network_data['mdot_DH_netw_total_kgpers']
    tdhsup_K = network_data['T_DHNf_sup_K']
    return mdot_DH_kgpers, tdhret_K, tdhsup_K