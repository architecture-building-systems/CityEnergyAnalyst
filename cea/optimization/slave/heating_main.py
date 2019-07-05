"""
FIND LEAST COST FUNCTION
USING PRESET ORDER

"""

from __future__ import division

import time
from math import log

import numpy as np
import pandas as pd

import cea.optimization.distribution.network_optimization_features as network_opt
import cea.technologies.pumps as PumpModel
from cea.constants import HOURS_IN_YEAR
from cea.constants import WH_TO_J
from cea.optimization.constants import HP_SEW_ALLOWED
from cea.optimization.master import cost_model
from cea.optimization.slave.heating_resource_activation import heating_source_activator
from cea.resources.geothermal import calc_ground_temperature
from cea.technologies.boiler import cond_boiler_op_cost
from cea.utilities import epwreader

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

def heating_calculations_of_DH_buildings(locator, master_to_slave_vars, config, prices, lca, solar_features,
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
    building_names = master_to_slave_vars.building_names

    # Import data from storage optimization
    centralized_plant_data = pd.read_csv(
        locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                              master_to_slave_vars.generation_number))
    E_aux_ch_W = np.array(centralized_plant_data['E_aux_ch_W'])
    E_aux_dech_W = np.array(centralized_plant_data['E_aux_dech_W'])
    Q_missing_W = np.array(centralized_plant_data['Q_missing_W'])
    E_aux_solar_and_heat_recovery_W = np.array(centralized_plant_data['E_aux_solar_and_heat_recovery_Wh'])
    Q_SC_ET_gen_Wh = np.array(centralized_plant_data['Q_SC_ET_gen_Wh'])
    Q_SC_FP_gen_Wh = np.array(centralized_plant_data['Q_SC_FP_gen_Wh'])
    Q_PVT_gen_Wh = np.array(centralized_plant_data['Q_PVT_gen_Wh'])
    Q_SCandPVT_gen_Wh = Q_SC_ET_gen_Wh + Q_SC_FP_gen_Wh + Q_PVT_gen_Wh
    E_PV_gen_W = np.array(centralized_plant_data['E_PV_Wh'])
    E_PVT_gen_W = np.array(centralized_plant_data['E_PVT_Wh'])
    E_produced_solar_W = np.array(centralized_plant_data['E_produced_from_solar_W'])

    E_solar_gen_W = np.add(E_PV_gen_W, E_PVT_gen_W)

    Q_missing_copy_W = Q_missing_W.copy()

    # Import Temperatures from Network Summary:
    network_data = pd.read_csv(locator.get_thermal_network_data_folder(master_to_slave_vars.network_data_file_heating))
    tdhret_K = network_data['T_DHNf_re_K']

    mdot_DH_kgpers = network_data['mdot_DH_netw_total_kgpers']
    tdhsup_K = network_data['T_DHNf_sup_K']
    # import Marginal Cost of PP Data :
    # os.chdir(Cost_Maps_Path)

    # FIXED ORDER ACTIVATION STARTS
    # Import Data - Sewage
    if HP_SEW_ALLOWED == 1:
        HPSew_Data = pd.read_csv(locator.get_sewage_heat_potential())
        QcoldsewArray = np.array(HPSew_Data['Qsw_kW']) * 1E3
        TretsewArray_K = np.array(HPSew_Data['ts_C']) + 273

    # Initiation of the variables
    Opex_var_HP_Sewage_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_HP_Lake_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_GHP_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_CHP_USD = np.zeros(HOURS_IN_YEAR)
    Opex_var_Furnace_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BaseBoiler_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_PeakBoiler_USDhr = np.zeros(HOURS_IN_YEAR)

    source_HP_Sewage = np.zeros(HOURS_IN_YEAR)
    source_HP_Lake = np.zeros(HOURS_IN_YEAR)
    source_GHP = np.zeros(HOURS_IN_YEAR)
    source_CHP = np.zeros(HOURS_IN_YEAR)
    source_Furnace = np.zeros(HOURS_IN_YEAR)
    source_BaseBoiler = np.zeros(HOURS_IN_YEAR)
    source_PeakBoiler = np.zeros(HOURS_IN_YEAR)

    Q_HPSew_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_HPLake_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_GHP_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_CHP_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_Furnace_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_BaseBoiler_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_PeakBoiler_gen_W = np.zeros(HOURS_IN_YEAR)
    Q_uncovered_W = np.zeros(HOURS_IN_YEAR)

    E_HPSew_req_W = np.zeros(HOURS_IN_YEAR)
    E_HPLake_req_W = np.zeros(HOURS_IN_YEAR)
    E_GHP_req_W = np.zeros(HOURS_IN_YEAR)
    E_CHP_gen_W = np.zeros(HOURS_IN_YEAR)
    E_Furnace_gen_W = np.zeros(HOURS_IN_YEAR)
    E_BaseBoiler_req_W = np.zeros(HOURS_IN_YEAR)
    E_PeakBoiler_req_W = np.zeros(HOURS_IN_YEAR)

    NG_used_HPSew_W = np.zeros(HOURS_IN_YEAR)
    NG_used_HPLake_W = np.zeros(HOURS_IN_YEAR)
    NG_used_GHP_W = np.zeros(HOURS_IN_YEAR)
    NG_used_CHP_W = np.zeros(HOURS_IN_YEAR)
    NG_used_Furnace_W = np.zeros(HOURS_IN_YEAR)
    NG_used_BaseBoiler_W = np.zeros(HOURS_IN_YEAR)
    NG_used_PeakBoiler_W = np.zeros(HOURS_IN_YEAR)
    NG_used_BackupBoiler_W = np.zeros(HOURS_IN_YEAR)

    BG_used_HPSew_W = np.zeros(HOURS_IN_YEAR)
    BG_used_HPLake_W = np.zeros(HOURS_IN_YEAR)
    BG_used_GHP_W = np.zeros(HOURS_IN_YEAR)
    BG_used_CHP_W = np.zeros(HOURS_IN_YEAR)
    BG_used_Furnace_W = np.zeros(HOURS_IN_YEAR)
    BG_used_BaseBoiler_W = np.zeros(HOURS_IN_YEAR)
    BG_used_PeakBoiler_W = np.zeros(HOURS_IN_YEAR)

    Wood_used_HPSew_W = np.zeros(HOURS_IN_YEAR)
    Wood_used_HPLake_W = np.zeros(HOURS_IN_YEAR)
    Wood_used_GHP_W = np.zeros(HOURS_IN_YEAR)
    Wood_used_CHP_W = np.zeros(HOURS_IN_YEAR)
    Wood_used_Furnace_W = np.zeros(HOURS_IN_YEAR)
    Wood_used_BaseBoiler_W = np.zeros(HOURS_IN_YEAR)
    Wood_used_PeakBoiler_W = np.zeros(HOURS_IN_YEAR)

    Q_coldsource_HPSew_W = np.zeros(HOURS_IN_YEAR)
    Q_coldsource_HPLake_W = np.zeros(HOURS_IN_YEAR)
    Q_coldsource_GHP_W = np.zeros(HOURS_IN_YEAR)
    Q_coldsource_CHP_W = np.zeros(HOURS_IN_YEAR)
    Q_coldsource_Furnace_W = np.zeros(HOURS_IN_YEAR)
    Q_coldsource_BaseBoiler_W = np.zeros(HOURS_IN_YEAR)
    Q_coldsource_PeakBoiler_W = np.zeros(HOURS_IN_YEAR)

    Q_excess_W = np.zeros(HOURS_IN_YEAR)
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent',
                                                         'windspd_ms', 'skytemp_C']]
    ground_temp = calc_ground_temperature(locator, config, weather_data['drybulb_C'], depth_m=10)

    for hour in range(HOURS_IN_YEAR):
        Q_therm_req_W = Q_missing_W[hour]

        opex_output, source_output, \
        Q_output, E_output, Gas_output, \
        Wood_output, coldsource_output, \
        Q_excess_W[hour] = heating_source_activator(Q_therm_req_W, hour, master_to_slave_vars,
                                                    mdot_DH_kgpers[hour], tdhsup_K[hour], tdhret_K[hour],
                                                    TretsewArray_K[hour],
                                                    prices, lca, ground_temp[hour])

        Opex_var_HP_Sewage_USDhr[hour] = opex_output['Opex_var_HP_Sewage_USDhr']
        Opex_var_HP_Lake_USDhr[hour] = opex_output['Opex_var_HP_Lake_USD']
        Opex_var_GHP_USDhr[hour] = opex_output['Opex_var_GHP_USD']
        Opex_var_CHP_USD[hour] = opex_output['Opex_var_CHP_USD']
        Opex_var_Furnace_USDhr[hour] = opex_output['Opex_var_Furnace_USD']
        Opex_var_BaseBoiler_USDhr[hour] = opex_output['Opex_var_BaseBoiler_USD']
        Opex_var_PeakBoiler_USDhr[hour] = opex_output['Opex_var_PeakBoiler_USD']

        source_HP_Sewage[hour] = source_output['HP_Sewage']
        source_HP_Lake[hour] = source_output['HP_Lake']
        source_GHP[hour] = source_output['GHP']
        source_CHP[hour] = source_output['CHP']
        source_Furnace[hour] = source_output['Furnace']
        source_BaseBoiler[hour] = source_output['BaseBoiler']
        source_PeakBoiler[hour] = source_output['PeakBoiler']

        Q_HPSew_gen_W[hour] = Q_output['Q_HPSew_gen_W']
        Q_HPLake_gen_W[hour] = Q_output['Q_HPLake_gen_W']
        Q_GHP_gen_W[hour] = Q_output['Q_GHP_gen_W']
        Q_CHP_gen_W[hour] = Q_output['Q_CHP_gen_W']
        Q_Furnace_gen_W[hour] = Q_output['Q_Furnace_gen_W']
        Q_BaseBoiler_gen_W[hour] = Q_output['Q_BaseBoiler_gen_W']
        Q_PeakBoiler_gen_W[hour] = Q_output['Q_PeakBoiler_gen_W']
        Q_uncovered_W[hour] = Q_output['Q_uncovered_W']

        E_HPSew_req_W[hour] = E_output['E_HPSew_req_W']
        E_HPLake_req_W[hour] = E_output['E_HPLake_req_W']
        E_GHP_req_W[hour] = E_output['E_GHP_req_W']
        E_CHP_gen_W[hour] = E_output['E_CHP_gen_W']
        E_Furnace_gen_W[hour] = E_output['E_Furnace_gen_W']
        E_BaseBoiler_req_W[hour] = E_output['E_BaseBoiler_req_W']
        E_PeakBoiler_req_W[hour] = E_output['E_PeakBoiler_req_W']

        if master_to_slave_vars.gt_fuel == "NG":
            NG_used_HPSew_W[hour] = Gas_output['Gas_used_HPSew_W']
            NG_used_HPLake_W[hour] = Gas_output['Gas_used_HPLake_W']
            NG_used_GHP_W[hour] = Gas_output['Gas_used_GHP_W']
            NG_used_CHP_W[hour] = Gas_output['Gas_used_CHP_W']
            NG_used_Furnace_W[hour] = Gas_output['Gas_used_Furnace_W']
            NG_used_BaseBoiler_W[hour] = Gas_output['Gas_used_BaseBoiler_W']
            NG_used_PeakBoiler_W[hour] = Gas_output['Gas_used_PeakBoiler_W']

        elif master_to_slave_vars.gt_fuel == "BG":
            BG_used_HPSew_W[hour] = Gas_output['Gas_used_HPSew_W']
            BG_used_HPLake_W[hour] = Gas_output['Gas_used_HPLake_W']
            BG_used_GHP_W[hour] = Gas_output['Gas_used_GHP_W']
            BG_used_CHP_W[hour] = Gas_output['Gas_used_CHP_W']
            BG_used_Furnace_W[hour] = Gas_output['Gas_used_Furnace_W']
            BG_used_BaseBoiler_W[hour] = Gas_output['Gas_used_BaseBoiler_W']
            BG_used_PeakBoiler_W[hour] = Gas_output['Gas_used_PeakBoiler_W']

        Wood_used_HPSew_W[hour] = Wood_output['Wood_used_HPSew_W']
        Wood_used_HPLake_W[hour] = Wood_output['Wood_used_HPLake_W']
        Wood_used_GHP_W[hour] = Wood_output['Wood_used_GHP_W']
        Wood_used_CHP_W[hour] = Wood_output['Wood_used_CHP_W']
        Wood_used_Furnace_W[hour] = Wood_output['Wood_used_Furnace_W']
        Wood_used_BaseBoiler_W[hour] = Wood_output['Wood_used_BaseBoiler_W']
        Wood_used_PeakBoiler_W[hour] = Wood_output['Wood_used_PeakBoiler_W']

        Q_coldsource_HPSew_W[hour] = coldsource_output['Q_coldsource_HPSew_W']
        Q_coldsource_HPLake_W[hour] = coldsource_output['Q_coldsource_HPLake_W']
        Q_coldsource_GHP_W[hour] = coldsource_output['Q_coldsource_GHP_W']
        Q_coldsource_CHP_W[hour] = coldsource_output['Q_coldsource_CHP_W']
        Q_coldsource_Furnace_W[hour] = coldsource_output['Q_coldsource_Furnace_W']
        Q_coldsource_BaseBoiler_W[hour] = coldsource_output['Q_coldsource_BaseBoiler_W']
        Q_coldsource_PeakBoiler_W[hour] = coldsource_output['Q_coldsource_PeakBoiler_W']

    # save data

    elapsed = time.time() - t
    # sum up the uncovered demand, get average and peak load
    Q_uncovered_design_W = np.amax(Q_uncovered_W)
    Q_uncovered_annual_W = np.sum(Q_uncovered_W)
    Opex_var_BackupBoiler_USDhr = np.zeros(HOURS_IN_YEAR)
    Q_BackupBoiler_W = np.zeros(HOURS_IN_YEAR)
    E_BackupBoiler_req_W = np.zeros(HOURS_IN_YEAR)

    Opex_var_Furnace_wet_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_Furnace_dry_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_CHP_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_CHP_BG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BaseBoiler_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BaseBoiler_BG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_PeakBoiler_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_PeakBoiler_BG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BackupBoiler_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    Opex_var_BackupBoiler_BG_USDhr = np.zeros(HOURS_IN_YEAR)

    Opex_var_PV_USD = np.zeros(HOURS_IN_YEAR)
    Opex_var_PVT_USD = np.zeros(HOURS_IN_YEAR)
    Opex_var_SC_USD = np.zeros(HOURS_IN_YEAR)

    if Q_uncovered_design_W != 0:
        for hour in range(HOURS_IN_YEAR):
            tdhret_req_K = tdhret_K[hour]
            BoilerBackup_Cost_Data = cond_boiler_op_cost(Q_uncovered_W[hour], Q_uncovered_design_W, tdhret_req_K, \
                                                         master_to_slave_vars.BoilerBackupType,
                                                         master_to_slave_vars.EL_TYPE, prices, lca, hour)
            Opex_var_BackupBoiler_USDhr[hour], Opex_var_BackupBoiler_per_Wh_USD, Q_BackupBoiler_W[
                hour], E_BackupBoiler_req_W_hour = BoilerBackup_Cost_Data
            E_BackupBoiler_req_W[hour] = E_BackupBoiler_req_W_hour
            NG_used_BackupBoiler_W[hour] = Q_BackupBoiler_W[hour]
        Q_BackupBoiler_sum_W = np.sum(Q_BackupBoiler_W)
    else:
        Q_BackupBoiler_sum_W = 0.0

    if master_to_slave_vars.Furn_Moist_type == "wet":
        Opex_var_Furnace_wet_USDhr = Opex_var_Furnace_USDhr
    elif master_to_slave_vars.Furn_Moist_type == "dry":
        Opex_var_Furnace_dry_USDhr = Opex_var_Furnace_USDhr

    if master_to_slave_vars.gt_fuel == "NG":
        Opex_var_CHP_NG_USDhr = Opex_var_CHP_USD
        Opex_var_BaseBoiler_NG_USDhr = Opex_var_BaseBoiler_USDhr
        Opex_var_PeakBoiler_NG_USDhr = Opex_var_PeakBoiler_USDhr
        Opex_var_BackupBoiler_NG_USDhr = Opex_var_BackupBoiler_USDhr

    elif master_to_slave_vars.gt_fuel == "BG":
        Opex_var_CHP_BG_USDhr = Opex_var_CHP_USD
        Opex_var_BaseBoiler_BG_USDhr = Opex_var_BaseBoiler_USDhr
        Opex_var_PeakBoiler_BG_USDhr = Opex_var_PeakBoiler_USDhr
        Opex_var_BackupBoiler_BG_USDhr = Opex_var_BackupBoiler_USDhr

    # COSTS GENERATION UNITS
    performance_costs = cost_model.addCosts(building_names, locator, master_to_slave_vars, Q_uncovered_design_W,
                                            solar_features, network_features,
                                            config, prices, lca)
    # COSTS HEATING NETWORK
    Capex_DHN_USD, \
    Capex_a_DHN_USD, \
    Opex_fixed_DHN_USD, \
    Opex_var_DHN_USD = calc_network_costs_heating(config, DHN_barcode, locator, master_to_slave_vars,
                                                  network_features, lca)

    # COSTS HEATING SUBSTATIONS
    Capex_SubstationsHeating_USD, \
    Capex_a_SubstationsHeating_USD, \
    Opex_fixed_SubstationsHeating_USD, \
    Opex_var_SubstationsHeating_USD = calc_substations_costs_heating(building_names, DHN_barcode,
                                                                     locator)

    # THIS CALCUALTES EMISSIONS
    if master_to_slave_vars.gt_fuel == "NG":
        performance_emissions_pen = calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W,
                                                                Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W,
                                                                Q_uncovered_W,
                                                                Q_coldsource_HPSew_W, Q_coldsource_HPLake_W,
                                                                Q_coldsource_GHP_W,
                                                                E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W,
                                                                E_PeakBoiler_req_W,
                                                                NG_used_CHP_W, NG_used_BaseBoiler_W,
                                                                NG_used_PeakBoiler_W,
                                                                Wood_used_Furnace_W, Q_BackupBoiler_sum_W,
                                                                np.sum(E_BackupBoiler_req_W),
                                                                master_to_slave_vars, locator, lca, fuel='NG')
        performance_emissions_pen['GHG_BaseBoiler_BG_tonCO2'] = 0.0
        performance_emissions_pen['GHG_PeakBoiler_BG_tonCO2'] = 0.0
        performance_emissions_pen['GHG_BackupBoiler_BG_tonCO2'] = 0.0
        performance_emissions_pen['GHG_CHP_BG_connected_tonCO2'] = 0.0
        performance_emissions_pen['PEN_CHP_BG_connected_MJoil'] = 0.0
        performance_emissions_pen['PEN_BaseBoiler_BG_MJoil'] = 0.0
        performance_emissions_pen['PEN_PeakBoiler_BG_MJoil'] = 0.0
        performance_emissions_pen['PEN_BackupBoiler_BG_MJoil'] = 0.0

    if master_to_slave_vars.gt_fuel == "BG":
        performance_emissions_pen = calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W,
                                                                Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W,
                                                                Q_uncovered_W,
                                                                Q_coldsource_HPSew_W, Q_coldsource_HPLake_W,
                                                                Q_coldsource_GHP_W,
                                                                E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W,
                                                                E_PeakBoiler_req_W,
                                                                BG_used_CHP_W, BG_used_BaseBoiler_W,
                                                                BG_used_PeakBoiler_W,
                                                                Wood_used_Furnace_W, Q_BackupBoiler_sum_W,
                                                                np.sum(E_BackupBoiler_req_W),
                                                                master_to_slave_vars, locator, lca, fuel='BG')
        performance_emissions_pen['GHG_BaseBoiler_NG_tonCO2'] = 0.0
        performance_emissions_pen['GHG_PeakBoiler_NG_tonCO2'] = 0.0
        performance_emissions_pen['GHG_BackupBoiler_NG_tonCO2'] = 0.0
        performance_emissions_pen['GHG_CHP_NG_connected_tonCO2'] = 0.0
        performance_emissions_pen['PEN_CHP_NG_connected_MJoil'] = 0.0
        performance_emissions_pen['PEN_BaseBoiler_NG_MJoil'] = 0.0
        performance_emissions_pen['PEN_PeakBoiler_NG_MJoil'] = 0.0
        performance_emissions_pen['PEN_BackupBoiler_NG_MJoil'] = 0.0

    # SUMMARIZE ALL DATA
    Opex_var_HP_Sewage_USD = sum(Opex_var_HP_Sewage_USDhr)
    Opex_var_HP_Lake_USD = sum(Opex_var_HP_Lake_USDhr)
    Opex_var_GHP_USD = sum(Opex_var_GHP_USDhr)
    Opex_var_CHP_BG_USD = sum(Opex_var_CHP_BG_USDhr)
    Opex_var_CHP_NG_USD = sum(Opex_var_CHP_NG_USDhr)
    Opex_var_Furnace_wet_USD = sum(Opex_var_Furnace_wet_USDhr)
    Opex_var_Furnace_dry_USD = sum(Opex_var_Furnace_dry_USDhr)
    Opex_var_BaseBoiler_BG_USD = sum(Opex_var_BaseBoiler_BG_USDhr)
    Opex_var_BaseBoiler_NG_USD = sum(Opex_var_BaseBoiler_NG_USDhr)
    Opex_var_PeakBoiler_BG_USD = sum(Opex_var_PeakBoiler_BG_USDhr)
    Opex_var_PeakBoiler_NG_USD = sum(Opex_var_PeakBoiler_NG_USDhr)
    Opex_var_BackupBoiler_BG_USD = sum(Opex_var_BackupBoiler_BG_USDhr)
    Opex_var_BackupBoiler_NG_USD = sum(Opex_var_BackupBoiler_NG_USDhr)

    # Costs
    Capex_a_connected_USD = addcosts_Capex_a_USD
    Capex_total_connected_USD = addcosts_Capex_USD
    Opex_a_connected_USD = addcosts_Opex_fixed_USD
    TAC_connected_USD = Capex_a_connected_USD + Opex_a_connected_USD

    TAC_USD = np.float64(TAC_connected_USD)
    GHG_tonCO2 = np.float64(CO2_emitted)
    PEN_MJoil = np.float64(PEN_used)

    # saving pattern activation to disk
    date = network_data.DATE.values
    results = pd.DataFrame(
        {"DATE": date,
         # annualized capex
         "Capex_a_DHN_USD": Capex_a_DHN_USD,
         "Capex_a_SubstationsHeating_USD": Capex_a_SubstationsHeating_USD,

         # total capex
         "Capex_DHN_USD": Capex_DHN_USD,
         "Capex_SubstationsHeating_USD": Capex_SubstationsHeating_USD,


         # opex fixed
         "Opex_fixed_HP_Sewage_connected_USD": performance_costs['Opex_fixed_HP_Sewage_USD'],
         "Opex_fixed_HP_Lake_connected_USD": performance_costs['Opex_fixed_HP_Lake_USD'],
         "Opex_fixed_GHP_connected_USD": performance_costs['Opex_fixed_GHP_USD'],
         "Opex_fixed_CHP_BG_connected_USD": performance_costs['Opex_fixed_CHP_BG_USD'],
         "Opex_fixed_CHP_NG_connected_USD": performance_costs['Opex_fixed_CHP_NG_USD'],
         "Opex_fixed_Furnace_wet_connected_USD": performance_costs['Opex_fixed_Furnace_wet_USD'],
         "Opex_fixed_Furnace_dry_connected_USD": performance_costs['Opex_fixed_Furnace_dry_USD'],
         "Opex_fixed_BaseBoiler_BG_connected_USD": performance_costs['Opex_fixed_BaseBoiler_BG_USD'],
         "Opex_fixed_BaseBoiler_NG_connected_USD": performance_costs['Opex_fixed_BaseBoiler_NG_USD'],
         "Opex_fixed_PeakBoiler_BG_connected_USD": performance_costs['Opex_fixed_PeakBoiler_BG_USD'],
         "Opex_fixed_PeakBoiler_NG_connected_USD": performance_costs['Opex_fixed_PeakBoiler_NG_USD'],
         "Opex_fixed_BackupBoiler_BG_connected_USD": performance_costs['Opex_fixed_BackupBoiler_USD'],
         "Opex_fixed_BackupBoiler_NG_connected_USD": performance_costs['Opex_fixed_BackupBoiler_NG_USD'],
         "Opex_fixed_Storage_connected_USD": performance_costs['Opex_fixed_Storage_USD'],
         "Opex_fixed_DHN_USD": Opex_fixed_DHN_USD,
         "Opex_fixed_SubstationsHeating_USD": Opex_fixed_SubstationsHeating_USD,

         # opex variable
         "Opex_var_HP_Sewage_connected_USD": Opex_var_HP_Sewage_USD,
         "Opex_var_HP_Lake_connected_USD": Opex_var_HP_Lake_USD,
         "Opex_var_GHP_connected_USD": Opex_var_GHP_USD,
         "Opex_var_CHP_BG_connected_USD": Opex_var_CHP_BG_USD,
         "Opex_var_CHP_NG_connected_USD": Opex_var_CHP_NG_USD,
         "Opex_var_Furnace_wet_connected_USD": Opex_var_Furnace_wet_USD,
         "Opex_var_Furnace_dry_connected_USD": Opex_var_Furnace_dry_USD,
         "Opex_var_BaseBoiler_BG_connected_USD": Opex_var_BaseBoiler_BG_USD,
         "Opex_var_BaseBoiler_NG_connected_USD": Opex_var_BaseBoiler_NG_USD,
         "Opex_var_PeakBoiler_BG_connected_USD": Opex_var_PeakBoiler_BG_USD,
         "Opex_var_PeakBoiler_NG_connected_USD": Opex_var_PeakBoiler_NG_USD,
         "Opex_var_BackupBoiler_BG_connected_USD": Opex_var_BackupBoiler_BG_USD,
         "Opex_var_BackupBoiler_NG_connected_USD": Opex_var_BackupBoiler_NG_USD,
         "Opex_var_Storage_USD": Opex_var_Storage_USD,
         "Opex_var_DHN_USD": Opex_var_DHN_USD,
         "Opex_var_SubstationsHeating_USD": Opex_var_SubstationsHeating_USD,

         # opex annual

         # totals of connected to network
         "Capex_total_connected_USD": [Capex_total_connected_USD],
         "Capex_a_connected_USD": [Capex_a_connected_USD],
         "Opex_a_connected_USD": [Opex_a_connected_USD],
         "TAC_connected_USD": [TAC_connected_USD],

         # emissions
         "GHG_HP_Sewage_connected_tonCO2": performance_emissions_pen['GHG_HP_Sewage_tonCO2'],
         "GHG_HP_Lake_connected_tonCO2": performance_emissions_pen['GHG_HP_Lake_tonCO2'],
         "GHG_GHP_connected_tonCO2": performance_emissions_pen['GHG_GHP_tonCO2'],
         "GHG_CHP_BG_connected_tonCO2": performance_emissions_pen['GHG_CHP_BG_tonCO2'],
         "GHG_CHP_NG_connected_tonCO2": performance_emissions_pen['GHG_CHP_NG_tonCO2'],
         "GHG_Furnace_wet_connected_tonCO2": performance_emissions_pen['GHG_Furnace_wet_tonCO2'],
         "GHG_Furnace_dry_connected_tonCO2": performance_emissions_pen['GHG_Furnace_dry_tonCO2'],
         "GHG_BaseBoiler_BG_connected_tonCO2": performance_emissions_pen['GHG_BaseBoiler_BG_tonCO2'],
         "GHG_BaseBoiler_NG_connected_tonCO2": performance_emissions_pen['GHG_BaseBoiler_NG_tonCO2'],
         "GHG_PeakBoiler_BG_connected_tonCO2": performance_emissions_pen['GHG_PeakBoiler_BG_tonCO2'],
         "GHG_PeakBoiler_NG_connected_tonCO2": performance_emissions_pen['GHG_PeakBoiler_NG_tonCO2'],
         "GHG_BackupBoiler_BG_connected_tonCO2": performance_emissions_pen['GHG_BackupBoiler_BG_tonCO2'],
         "GHG_BackupBoiler_NG_connected_tonCO2": performance_emissions_pen['GHG_BackupBoiler_NG_tonCO2'],

         # primary energy
         "PEN_HP_Sewage_connected_MJoil": performance_emissions_pen['PEN_HP_Sewage_MJoil'],
         "PEN_HP_Lake_connected_MJoil": performance_emissions_pen['PEN_HP_Lake_MJoil'],
         "PEN_GHP_connected_MJoil": performance_emissions_pen['PEN_GHP_MJoil'],
         "PEN_CHP_BG_connected_MJoil": performance_emissions_pen['PEN_CHP_BG_MJoil'],
         "PEN_CHP_NG_connected_MJoil": performance_emissions_pen['PEN_CHP_NG_MJoil'],
         "PEN_Furnace_wet_connected_MJoil": performance_emissions_pen['PEN_Furnace_wet_MJoil'],
         "PEN_Furnace_dry_connected_MJoil": performance_emissions_pen['PEN_Furnace_dry_MJoil'],
         "PEN_BaseBoiler_BG_connected_MJoil": performance_emissions_pen['PEN_BaseBoiler_BG_MJoil'],
         "PEN_BaseBoiler_NG_connected_MJoil": performance_emissions_pen['PEN_BaseBoiler_NG_MJoil'],
         "PEN_PeakBoiler_BG_connected_MJoil": performance_emissions_pen['PEN_PeakBoiler_BG_MJoil'],
         "PEN_PeakBoiler_NG_connected_MJoil": performance_emissions_pen['PEN_PeakBoiler_NG_MJoil'],
         "PEN_BackupBoiler_BG_connected_MJoil": performance_emissions_pen['PEN_BackupBoiler_BG_MJoil'],
         "PEN_BackupBoiler_NG_connected_MJoil": performance_emissions_pen['PEN_BackupBoiler_NG_MJoil']
         })

    results.to_csv(locator.get_optimization_slave_heating_performance(master_to_slave_vars.individual_number,
                                                                      master_to_slave_vars.generation_number),
                   index=False)

    results = pd.DataFrame({"DATE": date,
                            "Q_Network_Demand_after_Storage_W": Q_missing_copy_W,
                            "HPSew_Status": source_HP_Sewage,
                            "HPLake_Status": source_HP_Lake,
                            "GHP_Status": source_GHP,
                            "CHP_Status": source_CHP,
                            "Furnace_Status": source_Furnace,
                            "BoilerBase_Status": source_BaseBoiler,
                            "BoilerPeak_Status": source_PeakBoiler,
                            "Q_HPSew_W": Q_HPSew_gen_W,
                            "Q_HPLake_W": Q_HPLake_gen_W,
                            "Q_GHP_W": Q_GHP_gen_W,
                            "Q_CHP_W": Q_CHP_gen_W,
                            "Q_Furnace_W": Q_Furnace_gen_W,
                            "Q_BaseBoiler_W": Q_BaseBoiler_gen_W,
                            "Q_PeakBoiler_W": Q_PeakBoiler_gen_W,
                            "Q_AddBoiler_W": Q_uncovered_W,
                            "Q_coldsource_HPLake_W": Q_coldsource_HPLake_W,
                            "Q_coldsource_HPSew_W": Q_coldsource_HPSew_W,
                            "Q_coldsource_GHP_W": Q_coldsource_GHP_W,
                            "Q_coldsource_CHP_W": Q_coldsource_CHP_W,
                            "Q_coldsource_Furnace_W": Q_coldsource_Furnace_W,
                            "Q_coldsource_BaseBoiler_W": Q_coldsource_BaseBoiler_W,
                            "Q_coldsource_PeakBoiler_W": Q_coldsource_PeakBoiler_W,
                            "Q_excess_W": Q_excess_W,
                            "E_HPSew_req_W": E_HPSew_req_W,
                            "E_HPLake_req_W": E_HPLake_req_W,
                            "E_GHP_req_W": E_GHP_req_W,
                            "E_CHP_gen_W": E_CHP_gen_W,
                            "E_Furnace_gen_W": E_Furnace_gen_W,
                            "E_BaseBoiler_req_W": E_BaseBoiler_req_W,
                            "E_PeakBoiler_req_W": E_PeakBoiler_req_W,
                            "E_BackupBoiler_req_W": E_BackupBoiler_req_W,
                            "NG_used_HPSew_W": NG_used_HPSew_W,
                            "NG_used_HPLake_W": NG_used_HPLake_W,
                            "NG_used_GHP_W": NG_used_GHP_W,
                            "NG_used_CHP_W": NG_used_CHP_W,
                            "NG_used_Furnace_W": NG_used_Furnace_W,
                            "NG_used_BaseBoiler_W": NG_used_BaseBoiler_W,
                            "NG_used_PeakBoiler_W": NG_used_PeakBoiler_W,
                            "NG_used_BackupBoiler_W": NG_used_BackupBoiler_W,
                            "BG_used_HPSew_W": BG_used_HPSew_W,
                            "BG_used_HPLake_W": BG_used_HPLake_W,
                            "BG_used_GHP_W": BG_used_GHP_W,
                            "BG_used_CHP_W": BG_used_CHP_W,
                            "BG_used_Furnace_W": BG_used_Furnace_W,
                            "BG_used_BaseBoiler_W": BG_used_BaseBoiler_W,
                            "BG_used_PeakBoiler_W": BG_used_PeakBoiler_W,
                            "Wood_used_HPSew_W": Wood_used_HPSew_W,
                            "Wood_used_HPLake_W": Wood_used_HPLake_W,
                            "Wood_used_GHP_W": Wood_used_GHP_W,
                            "Wood_used_CHP_": Wood_used_CHP_W,
                            "Wood_used_Furnace_W": Wood_used_Furnace_W,
                            "Wood_used_BaseBoiler_W": Wood_used_BaseBoiler_W,
                            "Wood_used_PeakBoiler_W": Wood_used_PeakBoiler_W
                            })

    results.to_csv(locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                             master_to_slave_vars.generation_number),
                   index=False)

    return TAC_USD, GHG_tonCO2, PEN_MJoil


def calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W,
                                Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W, Q_uncovered_W,
                                E_coldsource_HPSew_W, E_coldsource_HPLake_W, E_coldsource_GHP_W,
                                E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W,
                                E_gas_CHP_W, E_gas_BaseBoiler_W, E_gas_PeakBoiler_W,
                                E_wood_Furnace_W,
                                Q_gas_AdduncoveredBoilerSum_W, E_aux_AddBoilerSum_W,
                                master_to_slave_vars, locator, lca, fuel):
    """
    This function calculates the emissions and primary energy consumption

    :param Q_source_data_W: array with loads of different units for heating
    :param Q_coldsource_data_W: array with loads of different units for cooling
    :param E_PP_el_data_W: array with data of pattern activation for electrical loads
    :param Q_gas_data_W: array with cconsumption of eergy due to gas
    :param Q_wood_data_W: array with consumption of energy with wood..
    :param Q_gas_AdduncoveredBoilerSum_W: load to be covered by auxiliary unit.
    :param E_aux_AddBoilerSum_W: electricity needed by auxiliary unit
    :param E_solar_gen_Wh: electricity produced from solar
    :param Q_SCandPVT_gen_Wh: thermal load of solar collector and pvt units.
    :param Q_storage_content_W: thermal load stored in seasonal storage
    :param master_to_slave_vars: class MastertoSlaveVars containing the value of variables to be passed to
        the slave optimization for each individual
    :param locator: path to results
    :param E_HP_SolarAndHeatRecoverySum_W: auxiliary electricity of heat pump
    :param E_aux_storage_operation_sum_W: auxiliary electricity of operation of storage
    :param gv:  global variables class
    :type Q_source_data_W: list
    :type Q_coldsource_data_W: list
    :type E_PP_el_data_W: list
    :type Q_gas_data_W: list
    :type Q_wood_data_W: list
    :type Q_gas_AdduncoveredBoilerSum_W: list
    :type E_aux_AddBoilerSum_W: list
    :type E_solar_gen_Wh: list
    :type Q_SCandPVT_gen_Wh: list
    :type Q_storage_content_W: list
    :type master_to_slave_vars: class
    :type locator: string
    :type E_HP_SolarAndHeatRecoverySum_W: list
    :type E_aux_storage_operation_sum_W: list
    :type gv: class
    :return: CO2_emitted, Eprim_used

    :rtype: float, float

    """

    # Electricity is accounted for already, no double accounting --> leave it out.
    # only CO2 / Eprim is not included in the installation part, neglected as its very small compared to operational values
    # QHPServerHeatSum, QHPpvtSum, QHPCompAirSum, QHPScSum = HP_operation_Data_sum_array

    # ask for type of fuel, then either us BG or NG 
    if master_to_slave_vars.BoilerBackupType == 'BG':
        gas_to_oil_BoilerBackup_std = lca.BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBackup_std = lca.BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerBackup_std = lca.NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBackup_std = lca.NG_BOILER_TO_CO2_STD

    if master_to_slave_vars.gt_fuel == 'BG':
        gas_to_oil_CC_std = lca.BG_CC_TO_OIL_STD
        gas_to_co2_CC_std = lca.BG_CC_TO_CO2_STD
        EL_CC_TO_CO2_STD = lca.EL_BGCC_TO_CO2_STD
        EL_CC_TO_OIL_STD = lca.EL_BGCC_TO_OIL_EQ_STD
    else:
        gas_to_oil_CC_std = lca.NG_CC_TO_OIL_STD
        gas_to_co2_CC_std = lca.NG_CC_TO_CO2_STD
        EL_CC_TO_CO2_STD = lca.EL_NGCC_TO_CO2_STD
        EL_CC_TO_OIL_STD = lca.EL_NGCC_TO_OIL_EQ_STD

    if master_to_slave_vars.BoilerType == 'BG':
        gas_to_oil_BoilerBase_std = lca.BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBase_std = lca.BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerBase_std = lca.NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBase_std = lca.NG_BOILER_TO_CO2_STD

    if master_to_slave_vars.BoilerPeakType == 'BG':
        gas_to_oil_BoilerPeak_std = lca.BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerPeak_std = lca.BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerPeak_std = lca.NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerPeak_std = lca.NG_BOILER_TO_CO2_STD

    if master_to_slave_vars.EL_TYPE == 'green':
        el_to_co2 = lca.EL_TO_CO2_GREEN
        el_to_oil_eq = lca.EL_TO_OIL_EQ_GREEN
    else:
        el_to_co2 = lca.EL_TO_CO2
        el_to_oil_eq = lca.EL_TO_OIL_EQ

    # evaluate average efficiency, recover normalized data with this efficiency, if-else is there to avoid nan's
    if np.sum(Q_Furnace_gen_W) != 0:
        eta_furnace_avg = np.sum(Q_Furnace_gen_W) / np.sum(E_wood_Furnace_W)
        eta_furnace_el = np.sum(E_Furnace_gen_W) / np.sum(E_wood_Furnace_W)

    else:
        eta_furnace_avg = 1
        eta_furnace_el = 1

    if np.sum(Q_CHP_gen_W) != 0:
        eta_CC_avg = np.sum(Q_CHP_gen_W) / np.sum(E_gas_CHP_W)
        eta_CC_el = np.sum(E_CHP_gen_W) / np.sum(E_gas_CHP_W)
    else:
        eta_CC_avg = 1
        eta_CC_el = 1

    if np.sum(Q_BaseBoiler_gen_W) != 0:
        eta_Boiler_avg = np.sum(Q_BaseBoiler_gen_W) / np.sum(E_gas_BaseBoiler_W)
    else:
        eta_Boiler_avg = 1

    if np.sum(Q_PeakBoiler_gen_W) != 0:
        eta_PeakBoiler_avg = np.sum(Q_PeakBoiler_gen_W) / np.sum(E_gas_PeakBoiler_W)
    else:
        eta_PeakBoiler_avg = 1

    if np.sum(Q_uncovered_W) != 0:
        eta_AddBackup_avg = np.sum(Q_uncovered_W) / np.sum(Q_gas_AdduncoveredBoilerSum_W)
    else:
        eta_AddBackup_avg = 1

    if np.sum(Q_HPSew_gen_W) != 0:
        COP_HPSew_avg = np.sum(Q_HPSew_gen_W) / (-np.sum(E_coldsource_HPSew_W) + np.sum(Q_HPSew_gen_W))
    else:
        COP_HPSew_avg = 100.0

    if np.sum(Q_GHP_gen_W) != 0:
        COP_GHP_avg = np.sum(Q_GHP_gen_W) / (-np.sum(E_coldsource_GHP_W) + np.sum(Q_GHP_gen_W))
    else:
        COP_GHP_avg = 100

    if np.sum(Q_HPLake_gen_W) != 0:
        COP_HPLake_avg = np.sum(Q_HPLake_gen_W) / (-np.sum(E_coldsource_HPLake_W) + np.sum(Q_HPLake_gen_W))

    else:
        COP_HPLake_avg = 100

    ######### COMPUTE THE GHG emissions
    GHG_Sewage_tonCO2 = (np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * WH_TO_J / 1.0E6) * (lca.SEWAGEHP_TO_CO2_STD / 1E3)
    GHG_GHP_tonCO2 = (np.sum(Q_GHP_gen_W) / COP_GHP_avg * WH_TO_J / 1.0E6) * (lca.GHP_TO_CO2_STD / 1E3)
    GHG_HPLake_tonCO2 = (np.sum(Q_HPLake_gen_W) / COP_HPLake_avg / 1.0E6) * (lca.LAKEHP_TO_CO2_STD / 1.0E3)
    GHG_CHP_tonCO2 = 1 / eta_CC_avg * np.sum(Q_CHP_gen_W) * gas_to_co2_CC_std * WH_TO_J / 1.0E6
    GHG_BaseBoiler_tonCO2 = (1 / eta_Boiler_avg * np.sum(Q_BaseBoiler_gen_W) * WH_TO_J / 1.0E6) * (
            gas_to_co2_BoilerBase_std / 1E3)
    GHG_PeakBoiler_tonCO2 = (1 / eta_PeakBoiler_avg * np.sum(
        Q_PeakBoiler_gen_W) * WH_TO_J / 1.0E6) * (gas_to_co2_BoilerPeak_std / 1E3)
    GHG_AddBoiler_tonCO2 = (1 / eta_AddBackup_avg * np.sum(Q_uncovered_W) * WH_TO_J / 1.0E6) * (
            gas_to_co2_BoilerBackup_std / 1.0E3)
    GHG_Furnace_tonCO2 = (1 / eta_furnace_avg * np.sum(Q_Furnace_gen_W) * WH_TO_J / 1.0E6) * (
            lca.FURNACE_TO_CO2_STD / 1E3)

    ################## Primary energy needs
    PEN_Sewage_MJoil = np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * lca.SEWAGEHP_TO_OIL_STD * WH_TO_J / 1.0E6
    PEN_GHP_MJoil = np.sum(Q_GHP_gen_W) / COP_GHP_avg * lca.GHP_TO_OIL_STD * WH_TO_J / 1.0E6
    PEN_HPLake_MJoil = np.sum(Q_HPLake_gen_W) / COP_HPLake_avg * lca.LAKEHP_TO_OIL_STD * WH_TO_J / 1.0E6
    PEN_CC_MJoil = 1 / eta_CC_avg * np.sum(Q_CHP_gen_W) * gas_to_oil_CC_std * WH_TO_J / 1.0E6
    PEN_BaseBoiler_MJoil = 1 / eta_Boiler_avg * np.sum(
        Q_BaseBoiler_gen_W) * gas_to_oil_BoilerBase_std * WH_TO_J / 1.0E6
    PEN_PeakBoiler_MJoil = 1 / eta_PeakBoiler_avg * np.sum(
        Q_PeakBoiler_gen_W) * gas_to_oil_BoilerPeak_std * WH_TO_J / 1.0E6
    PEN_AddBoiler_MJoil = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_oil_BoilerBackup_std * WH_TO_J / 1.0E6
    PEN_Furnace_MJoil = 1 / eta_furnace_avg * np.sum(Q_Furnace_gen_W) * lca.FURNACE_TO_OIL_STD * WH_TO_J / 1.0E6

    # Save data
    performance_parameters = {
        "GHG_HP_Sewage_tonCO2": [GHG_Sewage_tonCO2],
        "GHG_GHP_tonCO2": [GHG_GHP_tonCO2],
        "GHG_HP_Lake_tonCO2": [GHG_HPLake_tonCO2],
        "GHG_CHP_" + fuel + "_tonCO2": [GHG_CHP_tonCO2],
        "GHG_BaseBoiler_" + fuel + "_tonCO2": [GHG_BaseBoiler_tonCO2],
        "GHG_PeakBoiler_" + fuel + "_tonCO2": [GHG_PeakBoiler_tonCO2],
        "GHG_BackupBoiler_" + fuel + "_tonCO2": [GHG_AddBoiler_tonCO2],
        "GHG_Furnace_tonCO2": [GHG_Furnace_tonCO2],
        "PEN_HP_Sewage_MJoil": [PEN_Sewage_MJoil],
        "PEN_GHP_MJoil": [PEN_GHP_MJoil],
        "PEN_HP_Lake_MJoil": [PEN_HPLake_MJoil],
        "PEN_CHP_" + fuel + "_MJoil": [PEN_CC_MJoil],
        "PEN_BaseBoiler_" + fuel + "_MJoil": [PEN_BaseBoiler_MJoil],
        "PEN_PeakBoiler_" + fuel + "_MJoil": [PEN_PeakBoiler_MJoil],
        "PEN_BackupBoiler_" + fuel + "_MJoil": [PEN_AddBoiler_MJoil],
        "PEN_Furnace_MJoil": [PEN_Furnace_MJoil]}

    return performance_parameters


def calc_network_costs_heating(config, district_network_barcode, locator, master_to_slave_vars,
                               ntwFeat, lca):
    # costs of pumps
    Capex_a_pump_USD, Opex_fixed_pump_USD, Opex_var_pump_USD, Capex_pump_USD = PumpModel.calc_Ctot_pump(
        master_to_slave_vars, ntwFeat, locator, lca, "DC")

    # Intitialize class
    network_features = network_opt.NetworkOptimizationFeatures(config, locator)
    num_buildings_connected = district_network_barcode.count("1")
    num_all_buildings = len(district_network_barcode)
    ratio_connected = num_buildings_connected / num_all_buildings

    # Capital costs
    Inv_IR = 0.05
    Inv_LT = 20
    Inv_OM = 0.10
    Capex_Network_USD = network_features.pipesCosts_DCN_USD * ratio_connected
    Capex_a_Network_USD = (Capex_Network_USD * ((1 + Inv_IR) ** Inv_LT - 1) / (Inv_IR) * (1 + Inv_IR) ** Inv_LT)
    Opex_fixed_Network_USD = Capex_Network_USD * Inv_OM

    # summarize
    Capex_Network_USD += Capex_pump_USD
    Capex_a_Network_USD += Capex_a_pump_USD
    Opex_fixed_Network_USD += Opex_fixed_pump_USD
    Opex_var_Network_USD = Opex_var_pump_USD

    return Capex_Network_USD, Capex_a_Network_USD, Opex_fixed_Network_USD, Opex_var_Network_USD


def calc_substations_costs_heating(building_names, district_network_barcode, locator):
    Capex_Substations_USD = 0.0
    Capex_a_Substations_USD = 0.0
    Opex_fixed_Substations_USD = 0.0
    Opex_var_Substations_USD = 0.0  # it is asssumed as 0 in substations
    for (index, building_name) in zip(district_network_barcode, building_names):
        if index == "1":
            df = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DH"),
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

    return Capex_Substations_USD, Capex_a_Substations_USD, Opex_fixed_Substations_USD, Opex_var_Substations_USD
