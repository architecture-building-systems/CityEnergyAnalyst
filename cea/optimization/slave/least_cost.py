"""
===========================
FIND LEAST COST FUNCTION
USING PRESET ORDER
===========================

"""

from __future__ import division
import os
import time

import numpy as np
import pandas as pd
from cea.optimization.constants import *
from cea.technologies.boilers import cond_boiler_op_cost
from cea.technologies.solar.photovoltaic import calc_Crem_pv
from cea.optimization.slave.resource_activation import source_activator

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

def least_cost_main(locator, master_to_slave_vars, solar_features, gv, prices):
    """
    This function runs the least cost optimization code and returns cost, co2 and primary energy required. \
    On the go, it saves the operation pattern

    :param locator: locator class
    :param master_to_slave_vars: class MastertoSlaveVars containing the value of variables to be passed to the
    slave optimization for each individual
    :param solar_features: solar features class
    :param gv: global variables class
    :type locator: class
    :type master_to_slave_vars: class
    :type solar_features: class
    :type gv: class
    :return: E_oil_eq_MJ: MJ oil Equivalent used during operation
        CO2_kg_eq: kg of CO2-Equivalent emitted during operation
        cost_sum: total cost in CHF used for operation
        Q_source_data[:,7]: uncovered demand
    :rtype: float, float, float, array
    """

    MS_Var = master_to_slave_vars

    t = time.time()

    # Import data from storage optimization
    centralized_plant_data = pd.read_csv(locator.get_optimization_slave_storage_operation_data(MS_Var.configKey))
    Q_DH_networkload_W = np.array(centralized_plant_data['Q_DH_networkload_W'])
    E_aux_ch_W = np.array(centralized_plant_data['E_aux_ch_W'])
    E_aux_dech_W = np.array(centralized_plant_data['E_aux_dech_W'])
    Q_missing_W = np.array(centralized_plant_data['Q_missing_W'])
    Q_storage_content_W = np.array(centralized_plant_data['Q_storage_content_W'])
    Q_to_storage_W = np.array(centralized_plant_data['Q_to_storage_W'])
    Q_from_storage_W = np.array(centralized_plant_data['Q_from_storage_used_W'])
    Q_uncontrollable_W = np.array(centralized_plant_data['Q_uncontrollable_hot_W'])
    E_PV_Wh = np.array(centralized_plant_data['E_PV_Wh'])
    E_PVT_Wh = np.array(centralized_plant_data['E_PVT_Wh'])
    E_aux_HP_uncontrollable_Wh = np.array(centralized_plant_data['E_aux_HP_uncontrollable_Wh'])
    Q_SCandPVT_gen_Wh = np.array(centralized_plant_data['Q_SCandPVT_gen_Wh'])
    HPServerHeatDesignArray_kWh = np.array(centralized_plant_data['HPServerHeatDesignArray_kWh'])
    HPpvt_designArray_Wh = np.array(centralized_plant_data['HPpvt_designArray_Wh'])
    HPCompAirDesignArray_kWh = np.array(centralized_plant_data['HPCompAirDesignArray_kWh'])
    HPScDesignArray_Wh = np.array(centralized_plant_data['HPScDesignArray_Wh'])
    E_produced_solar_W = np.array(centralized_plant_data['E_produced_from_solar_W'])
    E_consumed_for_storage_and_solarHP_W = np.array(
        centralized_plant_data['E_consumed_for_storage_and_solarHP_W'])

    # Q_StorageToDHNpipe_sum = np.sum(E_aux_dech_W) + np.sum(Q_from_storage_W)
    #
    # HP_operation_Data_sum_array = np.sum(HPServerHeatDesignArray_kWh), \
    #                               np.sum(HPpvt_designArray_Wh), \
    #                               np.sum(HPCompAirDesignArray_kWh), \
    #                               np.sum(HPScDesignArray_Wh)

    Q_missing_copy_W = Q_missing_W.copy()

    network_data_file = MS_Var.NETWORK_DATA_FILE

    # Import Temperatures from Network Summary:
    network_storage_file = locator.get_optimization_network_data_folder(network_data_file)
    network_data = pd.read_csv(network_storage_file)
    tdhret_K = network_data['T_DHNf_re_K']

    mdot_DH_kgpers = network_data['mdot_DH_netw_total_kgpers']
    tdhsup_K = network_data['T_DHNf_sup_K'][0]
    # import Marginal Cost of PP Data :
    # os.chdir(Cost_Maps_Path)

    # FIXED ORDER ACTIVATION STARTS
    # Import Data - Sewage
    if HPSew_allowed == 1:
        HPSew_Data = pd.read_csv(locator.get_sewage_heat_potential())
        QcoldsewArray = np.array(HPSew_Data['Qsw_kW']) * 1E3
        TretsewArray_K = np.array(HPSew_Data['ts_C']) + 273

    cost_data_centralPlant_op = np.zeros((8760, 7))
    source_info = np.zeros((8760, 7))
    Q_source_data_W = np.zeros((8760, 8))
    E_coldsource_data_W = np.zeros((8760, 7))
    E_PP_el_data_W = np.zeros((8760, 7))
    E_gas_data_W = np.zeros((8760, 7))
    E_wood_data_W = np.zeros((8760, 7))
    Q_excess_W = np.zeros(8760)

    for hour in range(8760):
        Q_therm_req_W = Q_missing_W[hour]
        cost_data_centralPlant_op[hour, :], source_info[hour, :], Q_source_data_W[hour, :], E_coldsource_data_W[hour,
                                                                                            :], \
        E_PP_el_data_W[hour, :], E_gas_data_W[hour, :], E_wood_data_W[hour, :], Q_excess_W[hour] = source_activator(
            Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_kgpers, tdhsup_K,
            tdhret_K, TretsewArray_K, gv)

    # save data

    elapsed = time.time() - t
    # sum up the uncovered demand, get average and peak load
    Q_uncovered_W = Q_source_data_W[:, 7]
    Q_uncovered_design_W = np.amax(Q_uncovered_W)
    Q_uncovered_annual_W = np.sum(Q_uncovered_W)
    C_boil_thermAddBackup = np.zeros(8760)
    Q_primary_AddBackup_W = np.zeros(8760)
    E_aux_AddBoiler_req_W = np.zeros(8760)

    cost_details = {'cost_HP_Sewage': cost_data_centralPlant_op[:, 0],
                    'cost_HP_Lake': cost_data_centralPlant_op[:, 1],
                    'cost_GHP': cost_data_centralPlant_op[:, 2],
                    'cost_CC': cost_data_centralPlant_op[:, 3],
                    'cost_Furnace': cost_data_centralPlant_op[:, 4],
                    'cost_Boiler': cost_data_centralPlant_op[:, 5],
                    'cost_Backup_Boiler': cost_data_centralPlant_op[:, 6]}
    cost_sum_HP_Sewage, cost_sum_HP_Lake, cost_sum_GHP, cost_sum_CC, cost_sum_Furnace, cost_sum_Boiler, cost_sum_Backup_Boiler = \
        np.sum(cost_details['cost_HP_Sewage']), np.sum(cost_details['cost_HP_Lake']), np.sum(cost_details['cost_GHP']), \
        np.sum(cost_details['cost_CC']), np.sum(cost_details['cost_Furnace']), np.sum(cost_details['cost_Boiler']),\
        np.sum(cost_details['cost_Backup_Boiler'])

    source_details = {"HPSew_Status": source_info[:, 0],
                      "HPLake_Status": source_info[:, 1],
                      "GHP_Status": source_info[:, 2],
                      "CC_Status": source_info[:, 3],
                      "Furnace_Status": source_info[:, 4],
                      "BoilerBase_Status": source_info[:, 5],
                      "BoilerPeak_Status": source_info[:, 6]}

    Q_details = {"Q_HPSew_W": Q_source_data_W[:, 0],
                 "Q_HPLake_W": Q_source_data_W[:, 1],
                 "Q_GHP_W": Q_source_data_W[:, 2],
                 "Q_CC_W": Q_source_data_W[:, 3],
                 "Q_Furnace_W": Q_source_data_W[:, 4],
                 "Q_BoilerBase_W": Q_source_data_W[:, 5],
                 "Q_BoilerPeak_W": Q_source_data_W[:, 6],
                 "Q_uncovered_W": Q_source_data_W[:, 7]}

    if Q_uncovered_design_W != 0:
        for hour in range(8760):
            tdhret_req_K = tdhret_K[hour]
            BoilerBackup_Cost_Data = cond_boiler_op_cost(Q_uncovered_W[hour], Q_uncovered_design_W, tdhret_req_K, \
                                                         master_to_slave_vars.BoilerBackupType,
                                                         master_to_slave_vars.EL_TYPE, gv, prices)
            C_boil_thermAddBackup[hour], C_boil_per_WhBackup, Q_primary_AddBackup_W[hour], E_aux_AddBoiler_req_W[
                hour] = BoilerBackup_Cost_Data
        Q_primary_AddBackup_sum_W = np.sum(Q_primary_AddBackup_W)
        costAddBackup_total = np.sum(C_boil_thermAddBackup)

    else:
        Q_primary_AddBackup_sum_W = 0.0
        costAddBackup_total = 0.0

    # Sum up all electricity needs
    electricity_details = {'E_HPSew_req_W': E_PP_el_data_W[:, 0],
                           'E_HPLake_req_W': E_PP_el_data_W[:, 1],
                           'E_GHP_req_W': E_PP_el_data_W[:, 2],
                           'E_CC_gen_W': E_PP_el_data_W[:, 3],
                           'E_Furnace_gen_W': E_PP_el_data_W[:, 4],
                           'E_BaseBoiler_req_W': E_PP_el_data_W[:, 5],
                           'E_BackupBoiler_req_W': E_PP_el_data_W[:, 6]}

    E_PP_req_W = electricity_details['E_HPSew_req_W'] + electricity_details['E_HPLake_req_W'] + electricity_details['E_GHP_req_W'] + \
                 electricity_details['E_BaseBoiler_req_W'] + electricity_details['E_BackupBoiler_req_W'] + E_aux_AddBoiler_req_W
    E_aux_storage_req_W = E_aux_ch_W + E_aux_dech_W
    E_aux_storage_operation_sum_W = np.sum(E_aux_storage_req_W)
    E_PP_and_storage_req_W = E_PP_req_W + E_aux_storage_req_W
    E_HP_SolarAndHeatRecoverySum_W = np.sum(E_aux_HP_uncontrollable_Wh)
    # Sum up all electricity produced by CHP (CC and Furnace)
    # cost already accounted for in System Models (selling electricity --> cheaper thermal energy)
    E_CC_tot_gen_W = electricity_details['E_CC_gen_W'] + electricity_details['E_Furnace_gen_W']
    # price from PV and PVT electricity (both are in E_PV_Wh, see Storage_Design_and..., about Line 133)
    E_solar_gen_Wh = E_PV_Wh + E_PVT_Wh
    E_total_gen_W = E_produced_solar_W + E_CC_tot_gen_W
    E_without_buildingdemand_req_W = E_consumed_for_storage_and_solarHP_W + E_PP_and_storage_req_W

    # saving pattern activation to disk
    date = network_data.DATE.values
    results = pd.DataFrame({"DATE": date,
                            "Q_Network_Demand_after_Storage_W": Q_missing_copy_W,
                            "Cost_HPSew": cost_details['cost_HP_Sewage'],
                            "Cost_HPLake": cost_details['cost_HP_Lake'],
                            "Cost_GHP": cost_details['cost_GHP'],
                            "Cost_CC": cost_details['cost_CC'],
                            "Cost_Furnace": cost_details['cost_Furnace'],
                            "Cost_BoilerBase": cost_details['cost_Boiler'],
                            "Cost_BoilerPeak": cost_details['cost_Backup_Boiler'],
                            "Cost_AddBoiler": C_boil_thermAddBackup,
                            "HPSew_Status": source_details['HPSew_Status'],
                            "HPLake_Status": source_details['HPLake_Status'],
                            "GHP_Status": source_details['GHP_Status'],
                            "CC_Status": source_details['CC_Status'],
                            "Furnace_Status": source_details['Furnace_Status'],
                            "BoilerBase_Status": source_details['BoilerBase_Status'],
                            "BoilerPeak_Status": source_details['BoilerPeak_Status'],
                            "Q_HPSew_W": Q_details['Q_HPSew_W'],
                            "Q_HPLake_W": Q_details['Q_HPLake_W'],
                            "Q_GHP_W": Q_details['Q_GHP_W'],
                            "Q_CC_W": Q_details['Q_CC_W'],
                            "Q_Furnace_W": Q_details['Q_Furnace_W'],
                            "Q_BoilerBase_W": Q_details['Q_BoilerBase_W'],
                            "Q_BoilerPeak_W": Q_details['Q_BoilerPeak_W'],
                            "Q_uncontrollable_W": Q_uncontrollable_W,
                            "Q_primaryAddBackupSum_W": Q_primary_AddBackup_sum_W,
                            "E_PP_and_storage_W": E_PP_and_storage_req_W,
                            "Q_uncovered_W": Q_details['Q_uncovered_W'],
                            "Q_AddBoiler_W": Q_uncovered_W,
                            "E_aux_HP_uncontrollable_W": E_aux_HP_uncontrollable_Wh,
                            "E_solar_gen_W": E_solar_gen_Wh,
                            "E_CC_gen_W": E_CC_tot_gen_W,
                            "E_GHP_req_W": electricity_details['E_GHP_req_W'],
                            "Qcold_HPLake_W": E_coldsource_data_W[:, 1],
                            "E_produced_total_W": E_total_gen_W,
                            "E_consumed_without_buildingdemand_W": E_without_buildingdemand_req_W,
                            "Q_excess_W": Q_excess_W
                            })

    results.to_csv(locator.get_optimization_slave_pp_activation_pattern(MS_Var.configKey), index=False)

    CO2_emitted, Eprim_used = calc_primary_energy_and_CO2(Q_source_data_W, E_coldsource_data_W, E_PP_el_data_W,
                                                          E_gas_data_W, E_wood_data_W, Q_primary_AddBackup_sum_W,
                                                          np.sum(E_aux_AddBoiler_req_W),
                                                          np.sum(E_solar_gen_Wh), np.sum(Q_SCandPVT_gen_Wh),
                                                          Q_storage_content_W,
                                                          master_to_slave_vars, locator, E_HP_SolarAndHeatRecoverySum_W,
                                                          E_aux_storage_operation_sum_W, gv)

    # sum up results from PP Activation
    E_consumed_sum_W = np.sum(E_PP_and_storage_req_W) + np.sum(E_aux_HP_uncontrollable_Wh)  # (excl. AddBoiler)

    # Differenciate between Normal and green electricity for
    if MS_Var.EL_TYPE == 'green':
        ELEC_PRICE = gv.ELEC_PRICE_GREEN

    else:
        ELEC_PRICE = prices.ELEC_PRICE

    # Area available in NEtwork
    Area_AvailablePV_m2 = solar_features.A_PV_m2 * MS_Var.SOLAR_PART_PV
    Area_AvailablePVT_m2 = solar_features.A_PVT_m2 * MS_Var.SOLAR_PART_PVT
    #    import from master
    eta_m2_to_kW = eta_area_to_peak  # Data from Jimeno
    Q_PowerPeakAvailablePV_kW = Area_AvailablePV_m2 * eta_m2_to_kW
    Q_PowerPeakAvailablePVT_kW = Area_AvailablePVT_m2 * eta_m2_to_kW
    # calculate with conversion factor m'2-kWPeak

    KEV_RpPerkWhPVT = calc_Crem_pv(Q_PowerPeakAvailablePVT_kW * 1000.0)
    KEV_RpPerkWhPV = calc_Crem_pv(Q_PowerPeakAvailablePV_kW * 1000.0)

    KEV_total = KEV_RpPerkWhPVT / 100 * np.sum(E_PVT_Wh) / 1000 + KEV_RpPerkWhPV / 100 * np.sum(E_PV_Wh) / 1000
    # Units: from Rp/kWh to CHF/Wh

    price_obtained_from_KEV_for_PVandPVT = KEV_total
    cost_CC_maintenance = np.sum(E_PP_el_data_W[:, 3]) * prices.CC_MAINTENANCE_PER_KWHEL / 1000.0

    # Fill up storage if end-of-season energy is lower than beginning of season
    Q_Storage_SeasonEndReheat_W = Q_storage_content_W[-1] - Q_storage_content_W[0]

    gas_price = prices.NG_PRICE

    if Q_Storage_SeasonEndReheat_W > 0:
        cost_Boiler_for_Storage_reHeat_at_seasonend = float(Q_Storage_SeasonEndReheat_W) / 0.8 * gas_price
    else:
        cost_Boiler_for_Storage_reHeat_at_seasonend = 0

    # CHANGED AS THE COST_DATA INCLUDES COST_ELECTRICITY_TOTAL ALREADY! (= double accounting)
    cost_HP_aux_uncontrollable = np.sum(E_aux_HP_uncontrollable_Wh) * ELEC_PRICE
    cost_HP_storage_operation = np.sum(E_aux_storage_req_W) * ELEC_PRICE

    cost_sum = np.sum(
        cost_data_centralPlant_op) - price_obtained_from_KEV_for_PVandPVT + costAddBackup_total + cost_CC_maintenance + \
               cost_Boiler_for_Storage_reHeat_at_seasonend + cost_HP_aux_uncontrollable + cost_HP_storage_operation

    save_cost = 1

    E_oil_eq_MJ = Eprim_used
    CO2_kg_eq = CO2_emitted

    # Calculate primary energy from ressources:
    E_gas_Primary_W = Q_primary_AddBackup_sum_W + np.sum(E_gas_data_W)
    E_wood_Primary_W = np.sum(E_wood_data_W)
    E_Import_Slave_req_W = E_consumed_sum_W + np.sum(E_aux_AddBoiler_req_W)
    E_Export_gen_W = np.sum(E_total_gen_W)
    E_groundheat_W = np.sum(E_coldsource_data_W)
    E_solar_gen_Wh = np.sum(E_solar_gen_Wh) + np.sum(Q_SCandPVT_gen_Wh)
    E_gas_PrimaryPeakPower_W = np.amax(E_gas_data_W) + np.amax(Q_primary_AddBackup_W)


    if save_cost == 1:
        results = pd.DataFrame({
            "total cost": [cost_sum],
            "PPoperation_exclAddBackup": [np.sum(cost_data_centralPlant_op)],
            "KEV_Remuneration": [price_obtained_from_KEV_for_PVandPVT],
            "costAddBackup_total": [costAddBackup_total],
            "cost_CC_maintenance": [cost_CC_maintenance],
            "costHPSew_sum": [cost_sum_HP_Sewage],
            "costHPLake_sum": [cost_sum_HP_Lake],
            "costGHP_sum": [cost_sum_GHP],
            "costCC_sum": [cost_sum_CC],
            "costFurnace_sum": [cost_sum_Furnace],
            "costBoiler_sum": [cost_sum_Boiler],
            "costBackup_sum": [cost_sum_Backup_Boiler],
            "cost_Boiler_for_Storage_reHeat_at_seasonend": [cost_Boiler_for_Storage_reHeat_at_seasonend],
            "cost_HP_aux_uncontrollable": [cost_HP_aux_uncontrollable],
            "cost_HP_storage_operation": [cost_HP_storage_operation],
            "E_oil_eq_MJ": [E_oil_eq_MJ],
            "CO2_kg_eq": [CO2_kg_eq],
            "cost_sum": [cost_sum],
            "E_gas_Primary_W": [E_gas_Primary_W],
            "E_gas_PrimaryPeakPower_W": [E_gas_PrimaryPeakPower_W],
            "E_wood_Primary_W": [E_wood_Primary_W],
            "E_Import_Slave_req_W": [E_Import_Slave_req_W],
            "E_Export_gen_W": [E_Export_gen_W],
            "E_groundheat_W": [E_groundheat_W],
            "E_solar_gen_Wh": [E_solar_gen_Wh]
        })
        results.to_csv(locator.get_optimization_slave_cost_prime_primary_energy_data(MS_Var.configKey), sep=',')

    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, Q_uncovered_design_W, Q_uncovered_annual_W


def calc_primary_energy_and_CO2(Q_source_data_W, Q_coldsource_data_W, E_PP_el_data_W,
                                Q_gas_data_W, Q_wood_data_W, Q_gas_AdduncoveredBoilerSum_W, E_aux_AddBoilerSum_W,
                                E_solar_gen_Wh, Q_SCandPVT_gen_Wh, Q_storage_content_W,
                                master_to_slave_vars, locator, E_HP_SolarAndHeatRecoverySum_W,
                                E_aux_storage_operation_sum_W, gv):
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
    :rtype float, float
    """

    MS_Var = master_to_slave_vars
    StorageContentEndOfYear = Q_storage_content_W[-1]
    StorageContentStartOfYear = Q_storage_content_W[0]

    if StorageContentEndOfYear < StorageContentStartOfYear:
        QToCoverByStorageBoiler = float(StorageContentEndOfYear - StorageContentStartOfYear)
        eta_fictive_Boiler = 0.8  # add rather low efficiency as a penalty
        E_gasPrim_fictiveBoiler = QToCoverByStorageBoiler / eta_fictive_Boiler

    else:
        E_gasPrim_fictiveBoiler = 0

        # copy data
    Q_HPSew_gen_W = Q_source_data_W[:, 0]
    Q_HPLake_gen_W = Q_source_data_W[:, 1]
    Q_GHP_gen_W = Q_source_data_W[:, 2]
    Q_CC_gen_W = Q_source_data_W[:, 3]
    Q_Furnace_gen_W = Q_source_data_W[:, 4]
    Q_Boiler_gen_W = Q_source_data_W[:, 5]
    Q_BoilerPeak_gen_W = Q_source_data_W[:, 6]
    Q_uncovered_W = Q_source_data_W[:, 7]
    Q_coldsource_HPSew_W = Q_coldsource_data_W[:, 0]
    Q_coldsource_HPLake_W = Q_coldsource_data_W[:, 1]
    Q_coldsource_GHP_W = Q_coldsource_data_W[:, 2]
    Q_gas_CC_W = Q_gas_data_W[:, 3]
    Q_gas_Boiler_W = Q_gas_data_W[:, 5]
    Q_gas_Backup_W = Q_gas_data_W[:, 6]
    Q_wood_Furnace_W = Q_wood_data_W[:, 4]
    E_CC_gen_W = E_PP_el_data_W[:, 3]
    E_Furnace_gen_W = E_PP_el_data_W[:, 4]
    E_AuxillaryBoilerAllSum_W = np.sum(E_PP_el_data_W[:, 5]) + np.sum(E_PP_el_data_W[:, 6]) + E_aux_AddBoilerSum_W

    # Electricity is accounted for already, no double accounting --> leave it out. 
    # only CO2 / Eprim is not included in the installation part, neglected as its very small compared to operational values
    # QHPServerHeatSum, QHPpvtSum, QHPCompAirSum, QHPScSum = HP_operation_Data_sum_array

    # ask for type of fuel, then either us BG or NG 
    if MS_Var.BoilerBackupType == 'BG':
        gas_to_oil_BoilerBackup_std = BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBackup_std = BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerBackup_std = NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBackup_std = NG_BOILER_TO_CO2_STD

    if MS_Var.gt_fuel == 'BG':
        gas_to_oil_CC_std = BG_CC_TO_OIL_STD
        gas_to_co2_CC_std = BG_CC_TO_CO2_STD
        EL_CC_TO_CO2_STD = EL_BGCC_TO_CO2_STD
        EL_CC_TO_OIL_STD = EL_BGCC_TO_OIL_EQ_STD
    else:
        gas_to_oil_CC_std = NG_CC_TO_OIL_STD
        gas_to_co2_CC_std = NG_CC_TO_CO2_STD
        EL_CC_TO_CO2_STD = EL_NGCC_TO_CO2_STD
        EL_CC_TO_OIL_STD = EL_NGCC_TO_OIL_EQ_STD

    if MS_Var.BoilerType == 'BG':
        gas_to_oil_BoilerBase_std = BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBase_std = BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerBase_std = NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBase_std = NG_BOILER_TO_CO2_STD

    if MS_Var.BoilerPeakType == 'BG':
        gas_to_oil_BoilerPeak_std = BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerPeak_std = BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerPeak_std = NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerPeak_std = NG_BOILER_TO_CO2_STD

    if MS_Var.EL_TYPE == 'green':
        el_to_co2 = EL_TO_CO2_GREEN
        el_to_oil_eq = EL_TO_OIL_EQ_GREEN
    else:
        el_to_co2 = EL_TO_CO2
        el_to_oil_eq = EL_TO_OIL_EQ

    # evaluate average efficiency, recover normalized data with this efficiency, if-else is there to avoid nan's
    if np.sum(Q_Furnace_gen_W) != 0:
        eta_furnace_avg = np.sum(Q_Furnace_gen_W) / np.sum(Q_wood_Furnace_W)
        eta_furnace_el = np.sum(E_Furnace_gen_W) / np.sum(Q_wood_Furnace_W)

    else:
        eta_furnace_avg = 1
        eta_furnace_el = 1

    if np.sum(Q_CC_gen_W) != 0:
        eta_CC_avg = np.sum(Q_CC_gen_W) / np.sum(Q_gas_CC_W)
        eta_CC_el = np.sum(E_CC_gen_W) / np.sum(Q_gas_CC_W)
    else:
        eta_CC_avg = 1
        eta_CC_el = 1

    if np.sum(Q_Boiler_gen_W) != 0:
        eta_Boiler_avg = np.sum(Q_Boiler_gen_W) / np.sum(Q_gas_Boiler_W)
    else:
        eta_Boiler_avg = 1

    if np.sum(Q_BoilerPeak_gen_W) != 0:
        eta_PeakBoiler_avg = np.sum(Q_BoilerPeak_gen_W) / np.sum(Q_gas_Backup_W)
    else:
        eta_PeakBoiler_avg = 1

    if np.sum(Q_uncovered_W) != 0:
        eta_AddBackup_avg = np.sum(Q_uncovered_W) / np.sum(Q_gas_AdduncoveredBoilerSum_W)
    else:
        eta_AddBackup_avg = 1

    if np.sum(Q_HPSew_gen_W) != 0:
        COP_HPSew_avg = np.sum(Q_HPSew_gen_W) / (-np.sum(Q_coldsource_HPSew_W) + np.sum(Q_HPSew_gen_W))
    else:
        COP_HPSew_avg = 100.0

    if np.sum(Q_GHP_gen_W) != 0:
        COP_GHP_avg = np.sum(Q_GHP_gen_W) / (-np.sum(Q_coldsource_GHP_W) + np.sum(Q_GHP_gen_W))
    else:
        COP_GHP_avg = 100

    if np.sum(Q_HPLake_gen_W) != 0:
        COP_HPLake_avg = np.sum(Q_HPLake_gen_W) / (-np.sum(Q_coldsource_HPLake_W) + np.sum(Q_HPLake_gen_W))

    else:
        COP_HPLake_avg = 100

    ######### COMPUTE THE GHG emissions

    CO2_from_Sewage = np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * SEWAGEHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_GHP = np.sum(Q_GHP_gen_W) / COP_GHP_avg * GHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_HPLake = np.sum(Q_HPLake_gen_W) / COP_HPLake_avg * LAKEHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_HP = CO2_from_Sewage + CO2_from_GHP + CO2_from_HPLake
    CO2_from_CC_gas = 1 / eta_CC_avg * np.sum(Q_CC_gen_W) * gas_to_co2_CC_std * gv.Wh_to_J / 1.0E6
    CO2_from_BaseBoiler_gas = 1 / eta_Boiler_avg * np.sum(
        Q_Boiler_gen_W) * gas_to_co2_BoilerBase_std * gv.Wh_to_J / 1.0E6
    CO2_from_PeakBoiler_gas = 1 / eta_PeakBoiler_avg * np.sum(
        Q_BoilerPeak_gen_W) * gas_to_co2_BoilerPeak_std * gv.Wh_to_J / 1.0E6
    CO2_from_AddBoiler_gas = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_co2_BoilerBackup_std * gv.Wh_to_J / 1.0E6
    CO2_from_fictiveBoilerStorage = E_gasPrim_fictiveBoiler * NG_BOILER_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_gas = CO2_from_CC_gas + CO2_from_BaseBoiler_gas + CO2_from_PeakBoiler_gas + CO2_from_AddBoiler_gas \
                   + CO2_from_fictiveBoilerStorage
    CO2_from_wood = np.sum(Q_Furnace_gen_W) * FURNACE_TO_CO2_STD / eta_furnace_avg * gv.Wh_to_J / 1.0E6
    CO2_from_elec_sold = np.sum(E_Furnace_gen_W) * (- el_to_co2) * gv.Wh_to_J / 1.0E6 \
                         + np.sum(E_CC_gen_W) * (- el_to_co2) * gv.Wh_to_J / 1.0E6 \
                         + E_solar_gen_Wh * (
                                 EL_PV_TO_CO2 - el_to_co2) * gv.Wh_to_J / 1.0E6  # ESolarProduced contains PV and PVT values

    CO2_from_elec_usedAuxBoilersAll = E_AuxillaryBoilerAllSum_W * el_to_co2 * gv.Wh_to_J / 1E6
    CO2_from_SCandPVT = Q_SCandPVT_gen_Wh * SOLARCOLLECTORS_TO_CO2 * gv.Wh_to_J / 1.0E6
    CO2_from_HP_SolarandHeatRecovery = E_HP_SolarAndHeatRecoverySum_W * el_to_co2 * gv.Wh_to_J / 1E6
    CO2_from_HP_StorageOperationChDeCh = E_aux_storage_operation_sum_W * el_to_co2 * gv.Wh_to_J / 1E6

    ################## Primary energy needs

    E_prim_from_Sewage = np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * SEWAGEHP_TO_OIL_STD * gv.Wh_to_J / 1.0E6
    E_prim_from_GHP = np.sum(Q_GHP_gen_W) / COP_GHP_avg * GHP_TO_OIL_STD * gv.Wh_to_J / 1.0E6
    E_prim_from_HPLake = np.sum(Q_HPLake_gen_W) / COP_HPLake_avg * LAKEHP_TO_OIL_STD * gv.Wh_to_J / 1.0E6
    E_prim_from_HP = E_prim_from_Sewage + E_prim_from_GHP + E_prim_from_HPLake

    E_prim_from_CC_gas = 1 / eta_CC_avg * np.sum(Q_CC_gen_W) * gas_to_oil_CC_std * gv.Wh_to_J / 1.0E6
    E_prim_from_BaseBoiler_gas = 1 / eta_Boiler_avg * np.sum(
        Q_Boiler_gen_W) * gas_to_oil_BoilerBase_std * gv.Wh_to_J / 1.0E6
    E_prim_from_PeakBoiler_gas = 1 / eta_PeakBoiler_avg * np.sum(
        Q_BoilerPeak_gen_W) * gas_to_oil_BoilerPeak_std * gv.Wh_to_J / 1.0E6
    E_prim_from_AddBoiler_gas = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_oil_BoilerBackup_std * gv.Wh_to_J / 1.0E6
    E_prim_from_FictiveBoiler_gas = E_gasPrim_fictiveBoiler * NG_BOILER_TO_OIL_STD * gv.Wh_to_J / 1.0E6

    E_prim_from_gas = E_prim_from_CC_gas + E_prim_from_BaseBoiler_gas + E_prim_from_PeakBoiler_gas \
                      + E_prim_from_AddBoiler_gas + E_prim_from_FictiveBoiler_gas

    E_prim_from_wood = 1 / eta_furnace_avg * np.sum(Q_Furnace_gen_W) * FURNACE_TO_OIL_STD * gv.Wh_to_J / 1.0E6

    E_primSaved_from_elec_sold_Furnace = np.sum(E_Furnace_gen_W) * (- el_to_oil_eq) * gv.Wh_to_J / 1.0E6
    E_primSaved_from_elec_sold_CHP = np.sum(E_CC_gen_W) * (- el_to_oil_eq) * gv.Wh_to_J / 1.0E6
    E_primSaved_from_elec_sold_Solar = E_solar_gen_Wh * (EL_PV_TO_OIL_EQ - el_to_oil_eq) * gv.Wh_to_J / 1.0E6

    E_prim_Saved_from_elec_sold = E_primSaved_from_elec_sold_Furnace + E_primSaved_from_elec_sold_CHP + E_primSaved_from_elec_sold_Solar

    E_prim_from_elec_usedAuxBoilersAll = E_AuxillaryBoilerAllSum_W * el_to_oil_eq * gv.Wh_to_J / 1.0E6
    E_prim_from_SCandPVT = Q_SCandPVT_gen_Wh * SOLARCOLLECTORS_TO_OIL * gv.Wh_to_J / 1.0E6

    E_prim_from_HPSolarandHeatRecovery = E_HP_SolarAndHeatRecoverySum_W * el_to_oil_eq * gv.Wh_to_J / 1.0E6
    E_prim_from_HP_StorageOperationChDeCh = E_aux_storage_operation_sum_W * el_to_co2 * gv.Wh_to_J / 1E6

    # Save data
    results = pd.DataFrame({
        "CO2_from_Sewage": [CO2_from_Sewage],
        "CO2_from_GHP": [CO2_from_GHP],
        "CO2_from_HPLake": [CO2_from_HPLake],
        "CO2_from_CC_gas": [CO2_from_CC_gas],
        "CO2_from_BaseBoiler_gas": [CO2_from_BaseBoiler_gas],
        "CO2_from_PeakBoiler_gas": [CO2_from_PeakBoiler_gas],
        "CO2_from_AddBoiler_gas": [CO2_from_AddBoiler_gas],
        "CO2_from_fictiveBoilerStorage": [CO2_from_fictiveBoilerStorage],
        "CO2_from_wood": [CO2_from_wood],
        "CO2_from_elec_sold": [CO2_from_elec_sold],
        "CO2_from_SCandPVT": [CO2_from_SCandPVT],
        "CO2_from_elec_usedAuxBoilersAll": [CO2_from_elec_usedAuxBoilersAll],
        "CO2_from_HPSolarandHearRecovery": [CO2_from_HP_SolarandHeatRecovery],
        "CO2_from_HP_StorageOperationChDeCh": [CO2_from_HP_StorageOperationChDeCh],
        "E_prim_from_Sewage": [E_prim_from_Sewage],
        "E_prim_from_GHP": [E_prim_from_GHP],
        "E_prim_from_HPLake": [E_prim_from_HPLake],
        "E_prim_from_CC_gas": [E_prim_from_CC_gas],
        "E_prim_from_BaseBoiler_gas": [E_prim_from_BaseBoiler_gas],
        "E_prim_from_PeakBoiler_gas": [E_prim_from_PeakBoiler_gas],
        "E_prim_from_AddBoiler_gas": [E_prim_from_AddBoiler_gas],
        "E_prim_from_FictiveBoiler_gas": [E_prim_from_FictiveBoiler_gas],
        "E_prim_from_wood": [E_prim_from_wood],
        "E_primSaved_from_elec_sold_Furnace": [E_primSaved_from_elec_sold_Furnace],
        "E_primSaved_from_elec_sold_CC": [E_primSaved_from_elec_sold_CHP],
        "E_primSaved_from_elec_sold_Solar": [E_primSaved_from_elec_sold_Solar],
        "E_prim_from_elec_usedAuxBoilersAll": [E_prim_from_elec_usedAuxBoilersAll],
        "E_prim_from_HPSolarandHearRecovery": [E_prim_from_HPSolarandHeatRecovery],
        "E_prim_from_HP_StorageOperationChDeCh": [E_prim_from_HP_StorageOperationChDeCh]
    })
    results.to_csv(locator.get_optimization_slave_slave_detailed_emission_and_eprim_data(MS_Var.configKey), sep=',')

    ######### Summed up results
    CO2_emitted = (
            CO2_from_HP + CO2_from_gas + CO2_from_wood + CO2_from_elec_sold + CO2_from_SCandPVT + CO2_from_elec_usedAuxBoilersAll \
            + CO2_from_HP_SolarandHeatRecovery + CO2_from_HP_StorageOperationChDeCh)

    E_prim_used = (E_prim_from_HP + E_prim_from_gas + E_prim_from_wood + E_prim_Saved_from_elec_sold \
                   + E_prim_from_SCandPVT + E_prim_from_elec_usedAuxBoilersAll + E_prim_from_HPSolarandHeatRecovery \
                   + E_prim_from_HP_StorageOperationChDeCh)
    return CO2_emitted, E_prim_used


def import_solar_PeakPower(fNameTotalCSV, nBuildingsConnected, gv):
    """
    This function estimates the amount of solar installed for a certain configuration
    based on the number of buildings connected to the grid.

    :param fNameTotalCSV: name of the csv file
    :param nBuildingsConnected: number of the buildings connected to the grid
    :param gv: global variables
    :type fNameTotalCSV: string
    :type nBuildingsConnected: int
    :type gv: class
    :return: PeakPowerAvgkW
    :rtype: float
    """
    solar_results = pd.read_csv(fNameTotalCSV, nBuildingsConnected)
    AreaAllowed = np.array(solar_results['Af'])
    nFloors = np.array(solar_results['Floors'])

    AreaRoof = np.zeros(nBuildingsConnected)

    for building in range(nBuildingsConnected):
        AreaRoof[building] = AreaAllowed[building] / (nFloors[building] * 0.9)

    PeakPowerAvgkW = np.sum(AreaRoof) * gv.eta_area_to_peak / nBuildingsConnected

    if nBuildingsConnected == 0:
        PeakPowerAvgkW = 0

    return PeakPowerAvgkW
