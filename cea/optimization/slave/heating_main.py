"""
FIND LEAST COST FUNCTION
USING PRESET ORDER

"""

from __future__ import division

import time
from math import log

import numpy as np
import pandas as pd

from cea.optimization.master.cost_model import calc_network_costs
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
                             master_to_slave_vars,
                             config,
                             prices,
                             lca,
                             network_features):
    """
    Computes the parameters for the heating of the complete DHN

    :param locator: locator class
    :param master_to_slave_vars: class MastertoSlaveVars containing the value of variables to be passed to the
        slave optimization for each individual
    :param solar_features: solar features class
    :param gv: global variables class
    :type locator: class
    :type master_to_slave_vars: class
    :type solar_features: class
    :type gv: class
    :return:
        - E_oil_eq_MJ: MJ oil Equivalent used during operation
        - CO2_kg_eq: kg of CO2-Equivalent emitted during operation
        - cost_sum: total cost in CHF used for operation
        - Q_source_data[:,7]: uncovered demand

    :rtype: float, float, float, array

    """
    t = time.time()

    # local variables:
    DHN_barcode = master_to_slave_vars.DHN_barcode
    building_names = master_to_slave_vars.building_names_heating

    # THERMAL STORAGE + NETWORK
    print("CALCULATING ECOLOGICAL COSTS OF SEASONAL STORAGE - DUE TO OPERATION (IF ANY)")
    performance_storage, storage_dispatch = storage_main.storage_optimization(locator,
                                                                              master_to_slave_vars,
                                                                              lca, prices,
                                                                              config)
    # Import data from storage optimization
    Q_DH_networkload_W = np.array(storage_dispatch['Q_DH_networkload_W'])
    Q_thermal_req_W = np.array(storage_dispatch['Q_thermal_req_W'])

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
    mdot_DH_kgpers, T_district_heating_return_K, T_district_heating_supply_K = calc_network_summary_DHN(locator, master_to_slave_vars)

    # FIXED ORDER ACTIVATION STARTS
    # Import Data - Sewage heat
    if master_to_slave_vars.HPSew_on == 1:
        HPSew_Data = pd.read_csv(locator.get_sewage_heat_potential())
        Q_therm_Sew = np.array(HPSew_Data['Qsw_kW']) * 1E3
        Q_therm_Sew_W = [x if x < master_to_slave_vars.HPSew_maxSize_W else master_to_slave_vars.HPSew_maxSize_W for x in Q_therm_Sew]
        T_source_average_sewage_K = np.array(HPSew_Data['Ts_C']) + 273
    else:
        Q_therm_Sew_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_sewage_K = np.zeros(HOURS_IN_YEAR)

    # Import Data - lake heat
    if master_to_slave_vars.HPLake_on == 1:
        HPlake_Data = pd.read_csv(locator.get_lake_potential())
        Q_therm_Lake = np.array(HPlake_Data['QLake_kW']) * 1E3
        Q_therm_Lake_W = [x if x < master_to_slave_vars.HPLake_maxSize_W else master_to_slave_vars.HPLake_maxSize_W for x in Q_therm_Lake]
        T_source_average_Lake_K = np.array(HPlake_Data['Ts_C']) + 273
    else:
        Q_therm_Lake_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_Lake_K = np.zeros(HOURS_IN_YEAR)

    # Import Data - geothermal (shallow)
    if master_to_slave_vars.GHP_on == 1:
        GHP_Data = pd.read_csv(locator.get_geothermal_potential())
        Q_therm_GHP = np.array(GHP_Data['QGHP_kW']) * 1E3
        Q_therm_GHP_W = [x if x < master_to_slave_vars.GHP_maxSize_W else master_to_slave_vars.GHP_maxSize_W for x in Q_therm_GHP]
        T_source_average_GHP_W = np.array(GHP_Data['Ts_C']) + 273
    else:
        Q_therm_GHP_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_GHP_W = np.zeros(HOURS_IN_YEAR)

    # Initiation of the variables
    Opex_var_HP_Sewage_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_HP_Server_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_HP_Lake_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_GHP_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_CHP_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_Furnace_dry_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_Furnace_wet_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BaseBoiler_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_PeakBoiler_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BackupBoiler_NG_USDhr = np.zeros(HOURS_IN_YEAR)

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
            opex_output, \
            activation_output, \
            thermal_output, \
            electricity_output, \
            gas_output, \
            biomass_output = heating_source_activator(Q_thermal_req_W[hour],
                                                      hour,
                                                      master_to_slave_vars,
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

            Opex_var_HP_Sewage_USDhr[hour] = opex_output['Opex_var_HP_Sewage_USDhr']
            Opex_var_HP_Lake_USDhr[hour] = opex_output['Opex_var_HP_Lake_USDhr']
            Opex_var_GHP_USDhr[hour] = opex_output['Opex_var_GHP_USDhr']
            Opex_var_CHP_NG_USDhr[hour] = opex_output['Opex_var_CHP_USDhr']
            Opex_var_Furnace_dry_USDhr[hour] = opex_output['Opex_var_Furnace_dry_USDhr']
            Opex_var_Furnace_wet_USDhr[hour] = opex_output['Opex_var_Furnace_wet_USDhr']
            Opex_var_BaseBoiler_NG_USDhr[hour] = opex_output['Opex_var_BaseBoiler_USDhr']
            Opex_var_PeakBoiler_NG_USDhr[hour] = opex_output['Opex_var_PeakBoiler_USDhr']

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
            E_Furnace_dry_gen_W[hour] = electricity_output['E_Furnace_dry_gen_W']
            E_Furnace_wet_gen_W[hour] = electricity_output['E_Furnace_wet_gen_W']
            E_BaseBoiler_req_W[hour] = electricity_output['E_BaseBoiler_req_W']
            E_PeakBoiler_req_W[hour] = electricity_output['E_PeakBoiler_req_W']

            NG_CHP_req_W[hour] = gas_output['Gas_CHP_req_W']
            NG_BaseBoiler_req_W[hour] = gas_output['Gas_BaseBoiler_req_W']
            NG_PeakBoiler_req_W[hour] = gas_output['Gas_PeakBoiler_req_W']
            WetBiomass_Furnace_req_W[hour] = biomass_output['Biomass_Furnace_dry_req_W']
            DryBiomass_Furnace_req_W[hour] = biomass_output['Biomass_Furnace_wet_req_W']

    #BACK-UP BOILER
    Q_uncovered_design_W = np.amax(Q_AddBoiler_gen_W)
    if Q_uncovered_design_W != 0:
        for hour in range(HOURS_IN_YEAR):
            tdhret_req_K = T_district_heating_return_K[hour]
            Opex_var_BackupBoiler_NG_USDhr[hour], \
            Opex_var_BackupBoiler_per_Wh_USD, \
            NG_BackupBoiler_req_W[hour], \
            E_BackupBoiler_req_W[hour] = cond_boiler_op_cost(Q_AddBoiler_gen_W[hour],
                                                             Q_uncovered_design_W,
                                                             tdhret_req_K,
                                                             "NG",
                                                             prices, lca, hour)

    # CAPEX AND OPEX OF HEATING NETWORK
    Capex_DHN_USD, \
    Capex_a_DHN_USD, \
    Opex_fixed_DHN_USD, \
    Opex_var_DHN_USD, \
    E_used_district_heating_network_W = calc_network_costs(locator, master_to_slave_vars,
                                                           network_features, lca, "DH")

    # CAPEX AND OPEX OF HEATING SUBSTATIONS
    Capex_SubstationsHeating_USD, \
    Capex_a_SubstationsHeating_USD, \
    Opex_fixed_SubstationsHeating_USD = calc_substations_costs_heating(building_names, DHN_barcode,
                                                                       locator)

    # CAPEX AND FIXED OPEX GENERATION UNITS
    performance_costs = cost_model.calc_generation_costs_heating(locator, master_to_slave_vars, Q_uncovered_design_W,
                                                                 config, storage_dispatch,
                                                                 )

    # OPEX VAR GENERATION UNITS
    Opex_var_CHP_NG_USD = sum(Opex_var_CHP_NG_USDhr)
    Opex_var_Furnace_wet_USD = sum(Opex_var_Furnace_wet_USDhr)
    Opex_var_Furnace_dry_USD = sum(Opex_var_Furnace_dry_USDhr)
    Opex_var_BaseBoiler_NG_USD = sum(Opex_var_BaseBoiler_NG_USDhr)
    Opex_var_PeakBoiler_NG_USD = sum(Opex_var_PeakBoiler_NG_USDhr)
    Opex_var_BackupBoiler_NG_USD = sum(Opex_var_BackupBoiler_NG_USDhr)

    # EMISSIONS OF RENEWABLES AND FUELS
    performance_emissions_pen = calc_primary_energy_and_CO2(Q_SC_ET_gen_W,
                                                            Q_SC_FP_gen_W,
                                                            Q_PVT_gen_W,
                                                            Q_Server_gen_W,
                                                            NG_CHP_req_W,
                                                            NG_BaseBoiler_req_W,
                                                            NG_PeakBoiler_req_W,
                                                            NG_BackupBoiler_req_W,
                                                            WetBiomass_Furnace_req_W,
                                                            DryBiomass_Furnace_req_W,
                                                            lca,
                                                            )
    # save data
    heating_dispatch = {

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

        #ENERGY GENERATION
        #heating
        "Q_PVT_gen_storage_W": Q_PVT_to_storage_W,
        "Q_SC_ET_gen_storage_W": Q_SC_ET_to_storage_W,
        "Q_SC_FP_gen_storage_W": Q_SC_FP_to_storage_W,
        "Q_HP_Server_storage_W": Q_HP_Server_to_storage_W,

        # this is what is generated out of all the technologies sent to the storage
        "Q_Storage_gen_W": Q_Storage_gen_W,

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
        "Q_AddBoiler_gen_directload_W": Q_AddBoiler_gen_W,

        #electricity
        "E_CHP_gen_W": E_CHP_gen_W,
        "E_PVT_gen_W": E_PVT_gen_W,
        "E_Furnace_dry_gen_W": E_Furnace_dry_gen_W,
        "E_Furnace_wet_gen_W": E_Furnace_wet_gen_W,

        # ENERGY REQUIREMENTS
        # Electricity
        "E_Storage_charging_req_W": E_Storage_req_charging_W,
        "E_Storage_discharging_req_W": E_Storage_req_discharging_W,
        "E_Pump_DHN_req_W": E_used_district_heating_network_W,
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

        # FUEL REQUIREMENTS
        "NG_CHP_req_W": NG_CHP_req_W,
        "NG_BaseBoiler_req_W": NG_BaseBoiler_req_W,
        "NG_PeakBoiler_req_W": NG_PeakBoiler_req_W,
        "NG_BackupBoiler_req_W": NG_BackupBoiler_req_W,
        "WetBiomass_Furnace_req_W": WetBiomass_Furnace_req_W,
        "DryBiomass_Furnace_req_W": DryBiomass_Furnace_req_W,
    }

    # SAVE PERFORMANCE METRICS TO DISK
    performance = {
        # annualized capex
        "Capex_a_SC_ET_connected_USD": performance_costs['Capex_a_SC_ET_connected_USD'],
        "Capex_a_SC_FP_connected_USD": performance_costs['Capex_a_SC_FP_connected_USD'],
        "Capex_a_PVT_connected_USD": performance_costs['Capex_a_PVT_connected_USD'],
        "Capex_a_HP_Server_connected_USD": performance_costs['Capex_a_HP_Server_connected_USD'],
        "Capex_a_HP_Sewage_connected_USD": performance_costs['Capex_a_HP_Sewage_connected_USD'],
        "Capex_a_HP_Lake_connected_USD": performance_costs['Capex_a_HP_Lake_connected_USD'],
        "Capex_a_GHP_connected_USD": performance_costs['Capex_a_GHP_connected_USD'],
        "Capex_a_CHP_NG_connected_USD": performance_costs['Capex_a_CHP_NG_connected_USD'],
        "Capex_a_Furnace_wet_connected_USD": performance_costs['Capex_a_Furnace_wet_connected_USD'],
        "Capex_a_Furnace_dry_connected_USD": performance_costs['Capex_a_Furnace_dry_connected_USD'],
        "Capex_a_BaseBoiler_NG_connected_USD": performance_costs['Capex_a_BaseBoiler_NG_connected_USD'],
        "Capex_a_PeakBoiler_NG_connected_USD": performance_costs['Capex_a_PeakBoiler_NG_connected_USD'],
        "Capex_a_BackupBoiler_NG_connected_USD": performance_costs['Capex_a_BackupBoiler_NG_connected_USD'],
        "Capex_a_DHN_connected_USD": Capex_a_DHN_USD,
        "Capex_a_SubstationsHeating_connected_USD": Capex_a_SubstationsHeating_USD,

        # total capex
        "Capex_total_SC_ET_connected_USD": performance_costs['Capex_total_SC_ET_connected_USD'],
        "Capex_total_SC_FP_connected_USD": performance_costs['Capex_total_SC_FP_connected_USD'],
        "Capex_total_PVT_connected_USD": performance_costs['Capex_total_PVT_connected_USD'],
        "Capex_total_HP_Server_connected_USD": performance_costs['Capex_total_HP_Server_connected_USD'],
        "Capex_total_HP_Sewage_connected_USD": performance_costs['Capex_total_HP_Sewage_connected_USD'],
        "Capex_total_HP_Lake_connected_USD": performance_costs['Capex_total_HP_Lake_connected_USD'],
        "Capex_total_GHP_connected_USD": performance_costs['Capex_total_GHP_connected_USD'],
        "Capex_total_CHP_NG_connected_USD": performance_costs['Capex_total_CHP_NG_connected_USD'],
        "Capex_total_Furnace_wet_connected_USD": performance_costs['Capex_total_Furnace_wet_connected_USD'],
        "Capex_total_Furnace_dry_connected_USD": performance_costs['Capex_total_Furnace_dry_connected_USD'],
        "Capex_total_BaseBoiler_NG_connected_USD": performance_costs['Capex_total_BaseBoiler_NG_connected_USD'],
        "Capex_total_PeakBoiler_NG_connected_USD": performance_costs['Capex_total_PeakBoiler_NG_connected_USD'],
        "Capex_total_BackupBoiler_NG_connected_USD": performance_costs['Capex_total_BackupBoiler_NG_connected_USD'],
        "Capex_total_DHN_connected_USD": Capex_DHN_USD,
        "Capex_total_SubstationsHeating_connected_USD": Capex_SubstationsHeating_USD,

        # opex fixed
        "Opex_fixed_SC_ET_connected_USD": performance_costs['Opex_fixed_SC_ET_connected_USD'],
        "Opex_fixed_SC_FP_connected_USD": performance_costs['Opex_fixed_SC_FP_connected_USD'],
        "Opex_fixed_PVT_connected_USD": performance_costs['Opex_fixed_PVT_connected_USD'],
        "Opex_fixed_HP_Server_connected_USD": performance_costs['Opex_fixed_HP_Server_connected_USD'],
        "Opex_fixed_HP_Sewage_connected_USD": performance_costs['Opex_fixed_HP_Sewage_connected_USD'],
        "Opex_fixed_HP_Lake_connected_USD": performance_costs['Opex_fixed_HP_Lake_connected_USD'],
        "Opex_fixed_GHP_connected_USD": performance_costs['Opex_fixed_GHP_connected_USD'],
        "Opex_fixed_CHP_NG_connected_USD": performance_costs['Opex_fixed_CHP_NG_connected_USD'],
        "Opex_fixed_Furnace_wet_connected_USD": performance_costs['Opex_fixed_Furnace_wet_connected_USD'],
        "Opex_fixed_Furnace_dry_connected_USD": performance_costs['Opex_fixed_Furnace_dry_connected_USD'],
        "Opex_fixed_BaseBoiler_NG_connected_USD": performance_costs['Opex_fixed_BaseBoiler_NG_connected_USD'],
        "Opex_fixed_PeakBoiler_NG_connected_USD": performance_costs['Opex_fixed_PeakBoiler_NG_connected_USD'],
        "Opex_fixed_BackupBoiler_NG_connected_USD": performance_costs['Opex_fixed_BackupBoiler_NG_connected_USD'],
        "Opex_fixed_DHN_connected_USD": Opex_fixed_DHN_USD,
        "Opex_fixed_SubstationsHeating_USD": Opex_fixed_SubstationsHeating_USD,

        # opex variable
        # opex variable of soalar technologies is allocated to charging and discharging of storage
        # opex variable of technologies using electricity is calculated in electricity network eg. HP_sewage, HP_Lake
        "Opex_var_SC_ET_connected_USD": 0.0,  # costs are allocated the charging and decharging of the storage
        "Opex_var_SC_FP_connected_USD": 0.0,  # costs are allocated the charging and decharging of the storage
        "Opex_var_PVT_connected_USD": 0.0,  # costs are allocated the charging and decharging of the storage
        "Opex_var_HP_Server_connected_USD": 0.0,  # costs taken into account in the electricity network
        "Opex_var_HP_Sewage_connected_USD": 0.0, # costs taken into account in the electricity network
        "Opex_var_HP_Lake_connected_USD": 0.0,# costs taken into account in the electricity network
        "Opex_var_GHP_connected_USD": 0.0 ,# costs taken into account in the electricity network
        "Opex_var_CHP_NG_connected_USD": Opex_var_CHP_NG_USD,
        "Opex_var_Furnace_wet_connected_USD": Opex_var_Furnace_wet_USD,
        "Opex_var_Furnace_dry_connected_USD": Opex_var_Furnace_dry_USD,
        "Opex_var_BaseBoiler_NG_connected_USD": Opex_var_BaseBoiler_NG_USD,
        "Opex_var_PeakBoiler_NG_connected_USD": Opex_var_PeakBoiler_NG_USD,
        "Opex_var_BackupBoiler_NG_connected_USD": Opex_var_BackupBoiler_NG_USD,

        # opex annual
        # opex variable of soalr technologies is allocated to charging and discharging of storage
        # opex variable of technologies using electricity is calculated in electricity network eg. HP_sewage, HP_Lake
        "Opex_a_SC_ET_connected_USD": performance_costs['Opex_fixed_SC_ET_connected_USD'],
        "Opex_a_SC_FP_connected_USD": performance_costs['Opex_fixed_SC_FP_connected_USD'],
        "Opex_a_PVT_connected_USD": performance_costs['Opex_fixed_PVT_connected_USD'],
        "Opex_a_HP_Server_connected_USD":  performance_costs['Opex_fixed_HP_Server_connected_USD'],
        "Opex_a_HP_Sewage_connected_USD":  performance_costs['Opex_fixed_HP_Sewage_connected_USD'],
        "Opex_a_HP_Lake_connected_USD": performance_costs['Opex_fixed_HP_Lake_connected_USD'],
        "Opex_a_GHP_connected_USD":  performance_costs['Opex_fixed_GHP_connected_USD'],
        "Opex_a_CHP_NG_connected_USD": Opex_var_CHP_NG_USD + performance_costs['Opex_fixed_CHP_NG_connected_USD'],
        "Opex_a_Furnace_wet_connected_USD": Opex_var_Furnace_wet_USD + performance_costs[
            'Opex_fixed_Furnace_wet_connected_USD'],
        "Opex_a_Furnace_dry_connected_USD": Opex_var_Furnace_dry_USD + performance_costs[
            'Opex_fixed_Furnace_dry_connected_USD'],
        "Opex_a_BaseBoiler_NG_connected_USD": Opex_var_BaseBoiler_NG_USD + performance_costs[
            'Opex_fixed_BaseBoiler_NG_connected_USD'],
        "Opex_a_PeakBoiler_NG_connected_USD": Opex_var_PeakBoiler_NG_USD + performance_costs[
            'Opex_fixed_PeakBoiler_NG_connected_USD'],
        "Opex_a_BackupBoiler_NG_connected_USD": Opex_var_BackupBoiler_NG_USD + performance_costs[
            'Opex_fixed_BackupBoiler_NG_connected_USD'],
        "Opex_a_DHN_connected_USD": Opex_fixed_DHN_USD,
        "Opex_a_SubstationsHeating_USD": Opex_fixed_SubstationsHeating_USD,

        # emissions
        # emissions of technologies depending on electricity are calculated in electricity main e.g., HP_sewage
        "GHG_SC_ET_connected_tonCO2": performance_emissions_pen['GHG_SC_ET_connected_tonCO2'],
        "GHG_SC_FP_connected_tonCO2": performance_emissions_pen['GHG_SC_FP_connected_tonCO2'],
        "GHG_PVT_connected_tonCO2": performance_emissions_pen['GHG_PVT_connected_tonCO2'],
        "GHG_CHP_NG_connected_tonCO2": performance_emissions_pen['GHG_CHP_NG_connected_tonCO2'],
        "GHG_Furnace_wet_connected_tonCO2": performance_emissions_pen['GHG_Furnace_wet_connected_tonCO2'],
        "GHG_Furnace_dry_connected_tonCO2": performance_emissions_pen['GHG_Furnace_dry_connected_tonCO2'],
        "GHG_BaseBoiler_NG_connected_tonCO2": performance_emissions_pen['GHG_BaseBoiler_NG_connected_tonCO2'],
        "GHG_PeakBoiler_NG_connected_tonCO2": performance_emissions_pen['GHG_PeakBoiler_NG_connected_tonCO2'],
        "GHG_BackupBoiler_NG_connected_tonCO2": performance_emissions_pen['GHG_BackupBoiler_NG_connected_tonCO2'],

        # primary energy
        # emissions of technologies depending on electricity are accounted in electricity main e.g., HP_sewage
        "PEN_SC_ET_connected_MJoil": performance_emissions_pen['PEN_SC_ET_connected_MJoil'],
        "PEN_SC_FP_connected_MJoil": performance_emissions_pen['PEN_SC_FP_connected_MJoil'],
        "PEN_PVT_connected_MJoil": performance_emissions_pen['PEN_PVT_connected_MJoil'],
        "PEN_CHP_NG_connected_MJoil": performance_emissions_pen['PEN_CHP_NG_connected_MJoil'],
        "PEN_Furnace_wet_connected_MJoil": performance_emissions_pen['PEN_Furnace_wet_connected_MJoil'],
        "PEN_Furnace_dry_connected_MJoil": performance_emissions_pen['PEN_Furnace_dry_connected_MJoil'],
        "PEN_BaseBoiler_NG_connected_MJoil": performance_emissions_pen['PEN_BaseBoiler_NG_connected_MJoil'],
        "PEN_PeakBoiler_NG_connected_MJoil": performance_emissions_pen['PEN_PeakBoiler_NG_connected_MJoil'],
        "PEN_BackupBoiler_NG_connected_MJoil": performance_emissions_pen['PEN_BackupBoiler_NG_connected_MJoil'],
    }

    return performance, heating_dispatch


def calc_network_summary_DHN(locator, master_to_slave_vars):
    network_data = pd.read_csv(
        locator.get_optimization_thermal_network_data_file(master_to_slave_vars.network_data_file_heating))
    tdhret_K = network_data['T_DHNf_re_K']
    mdot_DH_kgpers = network_data['mdot_DH_netw_total_kgpers']
    tdhsup_K = network_data['T_DHNf_sup_K']
    return mdot_DH_kgpers, tdhret_K, tdhsup_K


def calc_primary_energy_and_CO2(Q_SC_ET_gen_W,
                                Q_SC_FP_gen_W,
                                Q_PVT_gen_W,
                                Q_Server_gen_W,
                                NG_CHP_req_W,
                                NG_BaseBoiler_req_W,
                                NG_PeakBoiler_req_W,
                                NG_BackupBoiler_req_W,
                                WetBiomass_Furnace_req_W,
                                DryBiomass_Furnace_req_W,
                                lca,
                                ):
    """
    This function calculates the emissions and primary energy consumption

    """

    # CALCULATE YEARLY LOADS
    Q_SC_ET_gen_Whyr = sum(Q_SC_ET_gen_W)
    Q_SC_FP_gen_Whyr = sum(Q_SC_FP_gen_W)
    Q_PVT_gen_Whyr = sum(Q_PVT_gen_W)
    Q_Server_gen_Wyr = sum(Q_Server_gen_W)
    NG_CHP_req_Wyr = sum(NG_CHP_req_W)
    NG_BaseBoiler_req_Wyr = sum(NG_BaseBoiler_req_W)
    NG_PeakBoiler_req_Wyr = sum(NG_PeakBoiler_req_W)
    NG_BackupBoiler_req_Wyr = sum(NG_BackupBoiler_req_W)
    WetBiomass_Furnace_req_Wyr = sum(WetBiomass_Furnace_req_W)
    DryBiomass_Furnace_req_Wyr = sum(DryBiomass_Furnace_req_W)

    # calculate emissions hourly (to discount for exports and imports)
    GHG_SC_ET_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(Q_SC_ET_gen_Whyr, lca.SOLARCOLLECTORS_TO_CO2)
    GHG_SC_FP_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(Q_SC_FP_gen_Whyr, lca.SOLARCOLLECTORS_TO_CO2)
    GHG_PVT_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(Q_PVT_gen_Whyr, lca.SOLARCOLLECTORS_TO_CO2)
    GHG_Server_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(Q_Server_gen_Wyr, 0.0)

    PEN_SC_ET_connected_MJoil = calc_pen_Whyr_to_MJoilyr(Q_SC_ET_gen_Whyr, lca.SOLARCOLLECTORS_TO_OIL)
    PEN_SC_FP_connected_MJoil = calc_pen_Whyr_to_MJoilyr(Q_SC_FP_gen_Whyr, lca.SOLARCOLLECTORS_TO_OIL)
    PEN_PVT_connected_MJoil = calc_pen_Whyr_to_MJoilyr(Q_PVT_gen_Whyr, lca.SOLARCOLLECTORS_TO_OIL)
    PEN_Server_connected_MJoil = calc_pen_Whyr_to_MJoilyr(Q_Server_gen_Wyr, 0.0)

    ######### COMPUTE THE GHG emissions
    GHG_CHP_NG_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(NG_CHP_req_Wyr, lca.NG_CC_TO_CO2_STD)
    GHG_BaseBoiler_NG_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(NG_BaseBoiler_req_Wyr,
                                                                         lca.NG_BOILER_TO_CO2_STD)
    GHG_PeakBoiler_NG_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(NG_PeakBoiler_req_Wyr,
                                                                         lca.NG_BOILER_TO_CO2_STD)
    GHG_BackupBoiler_NG_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(NG_BackupBoiler_req_Wyr,
                                                                           lca.NG_BOILER_TO_CO2_STD)

    GHG_Furnace_wet_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(WetBiomass_Furnace_req_Wyr,
                                                                       lca.FURNACE_TO_CO2_STD)
    GHG_Furnace_dry_connected_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(DryBiomass_Furnace_req_Wyr,
                                                                       lca.FURNACE_TO_CO2_STD)

    ######## COMPUTE PRIMARY ENERGY
    PEN_CHP_NG_connected_MJoil = calc_pen_Whyr_to_MJoilyr(NG_CHP_req_Wyr, lca.NG_CC_TO_OIL_STD)
    PEN_BaseBoiler_NG_connected_MJoil = calc_pen_Whyr_to_MJoilyr(NG_BaseBoiler_req_Wyr, lca.NG_BOILER_TO_OIL_STD)
    PEN_PeakBoiler_NG_connected_MJoil = calc_pen_Whyr_to_MJoilyr(NG_PeakBoiler_req_Wyr, lca.NG_BOILER_TO_OIL_STD)
    PEN_BackupBoiler_NG_connected_MJoil = calc_pen_Whyr_to_MJoilyr(NG_BackupBoiler_req_Wyr, lca.NG_BOILER_TO_OIL_STD)

    PEN_Furnace_wet_connected_MJoil = calc_pen_Whyr_to_MJoilyr(WetBiomass_Furnace_req_Wyr, lca.FURNACE_TO_OIL_STD)
    PEN_Furnace_dry_connected_MJoil = calc_pen_Whyr_to_MJoilyr(DryBiomass_Furnace_req_Wyr, lca.FURNACE_TO_OIL_STD)

    performance_parameters = {
        # CO2 EMISSIONS)
        "GHG_SC_ET_connected_tonCO2": GHG_SC_ET_connected_tonCO2,
        "GHG_SC_FP_connected_tonCO2": GHG_SC_FP_connected_tonCO2,
        "GHG_PVT_connected_tonCO2": GHG_PVT_connected_tonCO2,
        "GHG_Server_connected_tonCO2": GHG_Server_connected_tonCO2,
        "GHG_BaseBoiler_NG_connected_tonCO2": GHG_BaseBoiler_NG_connected_tonCO2,
        "GHG_PeakBoiler_NG_connected_tonCO2": GHG_PeakBoiler_NG_connected_tonCO2,
        "GHG_BackupBoiler_NG_connected_tonCO2": GHG_BackupBoiler_NG_connected_tonCO2,
        "GHG_CHP_NG_connected_tonCO2": GHG_CHP_NG_connected_tonCO2,
        "GHG_Furnace_wet_connected_tonCO2": GHG_Furnace_wet_connected_tonCO2,
        "GHG_Furnace_dry_connected_tonCO2": GHG_Furnace_dry_connected_tonCO2,
        "GHG_SubstationsHeating_tonCO2": 0.0,  # we neglect them

        # PRIMARY ENERGY (NON-RENEWABLE)
        "PEN_SC_ET_connected_MJoil": PEN_SC_ET_connected_MJoil,
        "PEN_SC_FP_connected_MJoil": PEN_SC_FP_connected_MJoil,
        "PEN_PVT_connected_MJoil": PEN_PVT_connected_MJoil,
        "PEN_Server_connected_MJoil": PEN_Server_connected_MJoil,
        "PEN_CHP_NG_connected_MJoil": PEN_CHP_NG_connected_MJoil,
        "PEN_BaseBoiler_NG_connected_MJoil": PEN_BaseBoiler_NG_connected_MJoil,
        "PEN_PeakBoiler_NG_connected_MJoil": PEN_PeakBoiler_NG_connected_MJoil,
        "PEN_BackupBoiler_NG_connected_MJoil": PEN_BackupBoiler_NG_connected_MJoil,
        "PEN_Furnace_wet_connected_MJoil": PEN_Furnace_wet_connected_MJoil,
        "PEN_Furnace_dry_connected_MJoil": PEN_Furnace_dry_connected_MJoil,
        "PEN_SubstationsHeating_MJoil": 0.0,  # we neglect them
    }

    return performance_parameters


def calc_substations_costs_heating(building_names, district_network_barcode, locator):
    Capex_Substations_USD = 0.0
    Capex_a_Substations_USD = 0.0
    Opex_fixed_Substations_USD = 0.0
    Opex_var_Substations_USD = 0.0  # it is asssumed as 0 in substations
    for (index, building_name) in zip(district_network_barcode, building_names):
        if index == "1":
            df = pd.read_csv(
                locator.get_optimization_substations_results_file(building_name, "DH", district_network_barcode),
                usecols=["Q_dhw_W", "Q_heating_W"])

            subsArray = np.array(df)
            Q_max_W = np.amax(subsArray[:, 0] + subsArray[:, 1])
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

    return Capex_Substations_USD, Capex_a_Substations_USD, Opex_fixed_Substations_USD
