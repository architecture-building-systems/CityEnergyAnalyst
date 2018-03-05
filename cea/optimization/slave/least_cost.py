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
from cea.optimization.slave.heating_resource_activation import heating_source_activator

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
    E_PV_gen_W = np.array(centralized_plant_data['E_PV_Wh'])
    E_PVT_gen_W = np.array(centralized_plant_data['E_PVT_Wh'])
    E_aux_solar_and_heat_recovery_W = np.array(centralized_plant_data['E_aux_solar_and_heat_recovery_Wh'])
    Q_SC_gen_Wh = np.array(centralized_plant_data['Q_SC_gen_Wh'])
    Q_PVT_gen_Wh = np.array(centralized_plant_data['Q_PVT_gen_Wh'])
    Q_SCandPVT_gen_Wh = Q_SC_gen_Wh + Q_PVT_gen_Wh
    E_produced_solar_W = np.array(centralized_plant_data['E_produced_from_solar_W'])

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
    tdhsup_K = network_data['T_DHNf_sup_K']
    # import Marginal Cost of PP Data :
    # os.chdir(Cost_Maps_Path)

    # FIXED ORDER ACTIVATION STARTS
    # Import Data - Sewage
    if HPSew_allowed == 1:
        HPSew_Data = pd.read_csv(locator.get_sewage_heat_potential())
        QcoldsewArray = np.array(HPSew_Data['Qsw_kW']) * 1E3
        TretsewArray_K = np.array(HPSew_Data['ts_C']) + 273



    # Initiation of the variables
    Opex_var_HP_Sewage = []
    Opex_var_HP_Lake = []
    Opex_var_GHP = []
    Opex_var_CHP = []
    Opex_var_Furnace = []
    Opex_var_BaseBoiler = []
    Opex_var_PeakBoiler = []

    source_HP_Sewage = []
    source_HP_Lake = []
    source_GHP = []
    source_CHP = []
    source_Furnace = []
    source_BaseBoiler = []
    source_PeakBoiler = []

    Q_HPSew_gen_W = []
    Q_HPLake_gen_W = []
    Q_GHP_gen_W = []
    Q_CHP_gen_W = []
    Q_Furnace_gen_W = []
    Q_BaseBoiler_gen_W = []
    Q_PeakBoiler_gen_W = []
    Q_uncovered_W = []

    E_HPSew_req_W = []
    E_HPLake_req_W = []
    E_GHP_req_W = []
    E_CHP_gen_W = []
    E_Furnace_gen_W = []
    E_BaseBoiler_req_W = []
    E_PeakBoiler_req_W = []

    E_gas_HPSew_W = []
    E_gas_HPLake_W = []
    E_gas_GHP_W = []
    E_gas_CHP_W = []
    E_gas_Furnace_W = []
    E_gas_BaseBoiler_W = []
    E_gas_PeakBoiler_W = []

    E_wood_HPSew_W = []
    E_wood_HPLake_W = []
    E_wood_GHP_W = []
    E_wood_CHP_W = []
    E_wood_Furnace_W = []
    E_wood_BaseBoiler_W = []
    E_wood_PeakBoiler_W = []

    E_coldsource_HPSew_W = []
    E_coldsource_HPLake_W = []
    E_coldsource_GHP_W = []
    E_coldsource_CHP_W = []
    E_coldsource_Furnace_W = []
    E_coldsource_BaseBoiler_W = []
    E_coldsource_PeakBoiler_W = []

    Q_excess_W = np.zeros(8760)

    for hour in range(8760):
        Q_therm_req_W = Q_missing_W[hour]
        # cost_data_centralPlant_op[hour, :], source_info[hour, :], Q_source_data_W[hour, :], E_coldsource_data_W[hour,
        #                                                                                     :], \
        # E_PP_el_data_W[hour, :], E_gas_data_W[hour, :], E_wood_data_W[hour, :], Q_excess_W[hour] = source_activator(
        #     Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_kgpers[hour], tdhsup_K,
        #     tdhret_K[hour], TretsewArray_K[hour], gv, prices)
        opex_output, source_output, Q_output, E_output, Gas_output, Wood_output, coldsource_output, Q_excess_W[hour] = heating_source_activator(
            Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_kgpers[hour], tdhsup_K[hour],
            tdhret_K[hour], TretsewArray_K[hour], gv, prices)

        Opex_var_HP_Sewage.append(opex_output['Opex_var_HP_Sewage'])
        Opex_var_HP_Lake.append(opex_output['Opex_var_HP_Lake'])
        Opex_var_GHP.append(opex_output['Opex_var_GHP'])
        Opex_var_CHP.append(opex_output['Opex_var_CHP'])
        Opex_var_Furnace.append(opex_output['Opex_var_Furnace'])
        Opex_var_BaseBoiler.append(opex_output['Opex_var_BaseBoiler'])
        Opex_var_PeakBoiler.append(opex_output['Opex_var_PeakBoiler'])

        source_HP_Sewage.append(source_output['HP_Sewage'])
        source_HP_Lake.append(source_output['HP_Lake'])
        source_GHP.append(source_output['GHP'])
        source_CHP.append(source_output['CHP'])
        source_Furnace.append(source_output['Furnace'])
        source_BaseBoiler.append(source_output['BaseBoiler'])
        source_PeakBoiler.append(source_output['PeakBoiler'])

        Q_HPSew_gen_W.append(Q_output['Q_HPSew_gen_W'])
        Q_HPLake_gen_W.append(Q_output['Q_HPLake_gen_W'])
        Q_GHP_gen_W.append(Q_output['Q_GHP_gen_W'])
        Q_CHP_gen_W.append(Q_output['Q_CHP_gen_W'])
        Q_Furnace_gen_W.append(Q_output['Q_Furnace_gen_W'])
        Q_BaseBoiler_gen_W.append(Q_output['Q_BaseBoiler_gen_W'])
        Q_PeakBoiler_gen_W.append(Q_output['Q_PeakBoiler_gen_W'])
        Q_uncovered_W.append(Q_output['Q_uncovered_W'])

        E_HPSew_req_W.append(E_output['E_HPSew_req_W'])
        E_HPLake_req_W.append(E_output['E_HPLake_req_W'])
        E_GHP_req_W.append(E_output['E_GHP_req_W'])
        E_CHP_gen_W.append(E_output['E_CHP_gen_W'])
        E_Furnace_gen_W.append(E_output['E_Furnace_gen_W'])
        E_BaseBoiler_req_W.append(E_output['E_BaseBoiler_req_W'])
        E_PeakBoiler_req_W.append(E_output['E_PeakBoiler_req_W'])

        E_gas_HPSew_W.append(Gas_output['E_gas_HPSew_W'])
        E_gas_HPLake_W.append(Gas_output['E_gas_HPLake_W'])
        E_gas_GHP_W.append(Gas_output['E_gas_GHP_W'])
        E_gas_CHP_W.append(Gas_output['E_gas_CHP_W'])
        E_gas_Furnace_W.append(Gas_output['E_gas_Furnace_W'])
        E_gas_BaseBoiler_W.append(Gas_output['E_gas_BaseBoiler_W'])
        E_gas_PeakBoiler_W.append(Gas_output['E_gas_PeakBoiler_W'])

        E_wood_HPSew_W.append(Wood_output['E_wood_HPSew_W'])
        E_wood_HPLake_W.append(Wood_output['E_wood_HPLake_W'])
        E_wood_GHP_W.append(Wood_output['E_wood_GHP_W'])
        E_wood_CHP_W.append(Wood_output['E_wood_CHP_W'])
        E_wood_Furnace_W.append(Wood_output['E_wood_Furnace_W'])
        E_wood_BaseBoiler_W.append(Wood_output['E_wood_BaseBoiler_W'])
        E_wood_PeakBoiler_W.append(Wood_output['E_wood_PeakBoiler_W'])

        E_coldsource_HPSew_W.append(coldsource_output['E_coldsource_HPSew_W'])
        E_coldsource_HPLake_W.append(coldsource_output['E_coldsource_HPLake_W'])
        E_coldsource_GHP_W.append(coldsource_output['E_coldsource_GHP_W'])
        E_coldsource_CHP_W.append(coldsource_output['E_coldsource_CHP_W'])
        E_coldsource_Furnace_W.append(coldsource_output['E_coldsource_Furnace_W'])
        E_coldsource_BaseBoiler_W.append(coldsource_output['E_coldsource_BaseBoiler_W'])
        E_coldsource_PeakBoiler_W.append(coldsource_output['E_coldsource_PeakBoiler_W'])

    # save data

    elapsed = time.time() - t
    # sum up the uncovered demand, get average and peak load
    Q_uncovered_design_W = np.amax(Q_uncovered_W)
    Q_uncovered_annual_W = np.sum(Q_uncovered_W)
    Opex_var_BackupBoiler = np.zeros(8760)
    Q_BackupBoiler_W = np.zeros(8760)
    E_aux_AddBoiler_req_W = []

    Opex_var_Furnace_wet = np.zeros(8760)
    Opex_var_Furnace_dry = np.zeros(8760)
    Opex_var_CHP_NG = np.zeros(8760)
    Opex_var_CHP_BG = np.zeros(8760)
    Opex_var_BaseBoiler_NG = np.zeros(8760)
    Opex_var_BaseBoiler_BG = np.zeros(8760)
    Opex_var_PeakBoiler_NG = np.zeros(8760)
    Opex_var_PeakBoiler_BG = np.zeros(8760)
    Opex_var_BackupBoiler_NG = np.zeros(8760)
    Opex_var_BackupBoiler_BG = np.zeros(8760)


    Opex_var_PV = np.zeros(8760)
    Opex_var_PVT = np.zeros(8760)
    Opex_var_SC = np.zeros(8760)




    if Q_uncovered_design_W != 0:
        for hour in range(8760):
            tdhret_req_K = tdhret_K[hour]
            BoilerBackup_Cost_Data = cond_boiler_op_cost(Q_uncovered_W[hour], Q_uncovered_design_W, tdhret_req_K, \
                                                         master_to_slave_vars.BoilerBackupType,
                                                         master_to_slave_vars.EL_TYPE, gv, prices)
            Opex_var_BackupBoiler[hour], C_boil_per_WhBackup, Q_BackupBoiler_W[hour], E_aux_AddBoiler_req_W_hour = BoilerBackup_Cost_Data
            E_aux_AddBoiler_req_W.append(E_aux_AddBoiler_req_W_hour)
        Q_BackupBoiler_sum_W = np.sum(Q_BackupBoiler_W)
        Opex_var_BackupBoiler_total = np.sum(Opex_var_BackupBoiler)

    else:
        for hour in range(8760):
            E_aux_AddBoiler_req_W.append(0)
        Q_BackupBoiler_sum_W = 0.0
        Opex_var_BackupBoiler_total = 0.0

    if master_to_slave_vars.Furn_Moist_type == "wet":
        Opex_var_Furnace_wet = Opex_var_Furnace
    elif master_to_slave_vars.Furn_Moist_type == "dry":
        Opex_var_Furnace_dry = Opex_var_Furnace

    if master_to_slave_vars.gt_fuel == "NG":
        Opex_var_CHP_NG = Opex_var_CHP
        Opex_var_BaseBoiler_NG = Opex_var_BaseBoiler
        Opex_var_PeakBoiler_NG = Opex_var_PeakBoiler
        Opex_var_BackupBoiler_NG = Opex_var_BackupBoiler

    elif master_to_slave_vars.gt_fuel == "BG":
        Opex_var_CHP_BG = Opex_var_CHP
        Opex_var_BaseBoiler_BG = Opex_var_BaseBoiler
        Opex_var_PeakBoiler_BG = Opex_var_PeakBoiler
        Opex_var_BackupBoiler_BG = Opex_var_BackupBoiler


    # Sum up all electricity needs
    intermediate_sum_1 = np.add(E_HPSew_req_W, E_HPLake_req_W)
    intermediate_sum_2 = np.add(E_GHP_req_W, E_BaseBoiler_req_W)
    intermediate_sum_3 = np.add(E_PeakBoiler_req_W, E_aux_AddBoiler_req_W)
    intermediate_sum_4 = np.add(intermediate_sum_1, intermediate_sum_2)
    E_aux_activation_req_W = np.add(intermediate_sum_3, intermediate_sum_4)
    E_aux_storage_solar_and_heat_recovery_req_W = np.add(np.add(E_aux_ch_W, E_aux_dech_W), E_aux_solar_and_heat_recovery_W)

    # Sum up all electricity produced by CHP (CC and Furnace)
    # cost already accounted for in System Models (selling electricity --> cheaper thermal energy)
    E_CHP_and_Furnace_gen_W = np.add(E_CHP_gen_W , E_Furnace_gen_W)
    # price from PV and PVT electricity (both are in E_PV_Wh, see Storage_Design_and..., about Line 133)
    E_solar_gen_W = np.add(E_PV_gen_W, E_PVT_gen_W)
    E_total_gen_W = np.add(E_produced_solar_W,  E_CHP_and_Furnace_gen_W)
    E_without_buildingdemand_req_W = np.add(E_aux_storage_solar_and_heat_recovery_req_W, E_aux_activation_req_W)

    E_total_req_W = np.add(np.array(network_data['Electr_netw_total_W']), E_without_buildingdemand_req_W)

    E_PV_to_grid_W = np.zeros(8760)
    E_PVT_to_grid_W = np.zeros(8760)
    E_CHP_to_grid_W = np.zeros(8760)
    E_Furnace_to_grid_W = np.zeros(8760)
    E_PV_directload_W = np.zeros(8760)
    E_PVT_directload_W = np.zeros(8760)
    E_CHP_directload_W = np.zeros(8760)
    E_Furnace_directload_W = np.zeros(8760)
    E_from_grid_W = np.zeros(8760)

    for hour in range(8760):
        E_hour_W = E_total_req_W[hour]

        if E_PV_gen_W[hour] <= E_hour_W:
            E_PV_directload_W[hour] = E_PV_gen_W[hour]
            E_hour_W = E_hour_W - E_PV_directload_W[hour]
        else:
            E_PV_directload_W[hour] = E_hour_W
            E_PV_to_grid_W[hour] = E_PV_gen_W[hour] - E_hour_W
            E_hour_W = 0

        if E_PVT_gen_W[hour] <= E_hour_W:
            E_PVT_directload_W[hour] = E_PVT_gen_W[hour]
            E_hour_W = E_hour_W - E_PVT_directload_W[hour]
        else:
            E_PVT_directload_W[hour] = E_hour_W
            E_PVT_to_grid_W[hour] = E_PVT_gen_W[hour] - E_hour_W
            E_hour_W = 0

        if E_CHP_gen_W[hour] <= E_hour_W:
            E_CHP_directload_W[hour] = E_CHP_gen_W[hour]
            E_hour_W = E_hour_W - E_CHP_directload_W[hour]
        else:
            E_CHP_directload_W[hour] = E_hour_W
            E_CHP_to_grid_W[hour] = E_CHP_gen_W[hour] - E_hour_W
            E_hour_W = 0

        if E_Furnace_gen_W[hour] <= E_hour_W:
            E_Furnace_directload_W[hour] = E_Furnace_gen_W[hour]
            E_hour_W = E_hour_W - E_Furnace_directload_W[hour]
        else:
            E_Furnace_directload_W[hour] = E_hour_W
            E_Furnace_to_grid_W[hour] = E_Furnace_gen_W[hour] - E_hour_W
            E_hour_W = 0

        E_from_grid_W[hour] = E_hour_W

    # saving pattern activation to disk
    date = network_data.DATE.values
    results = pd.DataFrame({"DATE": date,
                            "Q_Network_Demand_after_Storage_W": Q_missing_copy_W,
                            "Cost_HPSew": Opex_var_HP_Sewage,
                            "Cost_HPLake": Opex_var_HP_Lake,
                            "Cost_GHP": Opex_var_GHP,
                            "Cost_CHP_BG": Opex_var_CHP_BG,
                            "Cost_CHP_NG": Opex_var_CHP_NG,
                            "Cost_Furnace_wet": Opex_var_Furnace_wet,
                            "Cost_Furnace_dry": Opex_var_Furnace_dry,
                            "Cost_BaseBoiler_BG": Opex_var_BaseBoiler_BG,
                            "Cost_BaseBoiler_NG": Opex_var_BaseBoiler_NG,
                            "Cost_PeakBoiler_BG": Opex_var_PeakBoiler_BG,
                            "Cost_PeakBoiler_NG": Opex_var_PeakBoiler_NG,
                            "Cost_AddBoiler_BG": Opex_var_BackupBoiler_BG,
                            "Cost_AddBoiler_NG": Opex_var_BackupBoiler_NG,
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
                            "Q_coldsource_HPLake_W": E_coldsource_HPLake_W,
                            "Q_coldsource_HPSew_W": E_coldsource_HPSew_W,
                            "Q_coldsource_GHP_W": E_coldsource_GHP_W,
                            "Q_coldsource_CHP_W": E_coldsource_CHP_W,
                            "Q_coldsource_Furnace_W": E_coldsource_Furnace_W,
                            "Q_coldsource_BaseBoiler_W": E_coldsource_BaseBoiler_W,
                            "Q_coldsource_PeakBoiler_W": E_coldsource_PeakBoiler_W,
                            "Q_excess_W": Q_excess_W
                            })

    results.to_csv(locator.get_optimization_slave_heating_activation_pattern(MS_Var.configKey), index=False)

    results = pd.DataFrame({"DATE": date,
                            "E_total_req_W": E_total_req_W,
                            "E_HPSew_req_W": E_HPSew_req_W,
                            "E_HPLake_req_W": E_HPLake_req_W,
                            "E_GHP_req_W": E_GHP_req_W,
                            "E_CHP_gen_W": E_CHP_gen_W,
                            "E_Furnace_gen_W": E_Furnace_gen_W,
                            "E_BaseBoiler_req_W": E_BaseBoiler_req_W,
                            "E_PeakBoiler_req_W": E_PeakBoiler_req_W,
                            "E_AddBoiler_req_W": E_aux_AddBoiler_req_W,
                            "E_PV_gen_W": E_PV_gen_W,
                            "E_PVT_gen_W": E_PVT_gen_W,
                            "E_CHP_and_Furnace_gen_W": E_CHP_and_Furnace_gen_W,
                            "E_gen_total_W": E_total_gen_W,
                            "E_PV_directload_W": E_PV_directload_W,
                            "E_PVT_directload_W": E_PVT_directload_W,
                            "E_CHP_directload_W": E_CHP_directload_W,
                            "E_Furnace_directload_W": E_Furnace_directload_W,
                            "E_PV_to_grid_W": E_PV_to_grid_W,
                            "E_PVT_to_grid_W": E_PVT_to_grid_W,
                            "E_CHP_to_grid_W": E_CHP_to_grid_W,
                            "E_Furnace_to_grid_W": E_Furnace_to_grid_W,
                            "E_aux_storage_solar_and_heat_recovery_req_W": E_aux_storage_solar_and_heat_recovery_req_W,
                            "E_consumed_without_buildingdemand_W": E_without_buildingdemand_req_W,
                            "E_from_grid_W": E_from_grid_W
                            })

    results.to_csv(locator.get_optimization_slave_electricity_activation_pattern(MS_Var.configKey), index=False)

    E_aux_storage_operation_sum_W = np.sum(E_aux_storage_solar_and_heat_recovery_req_W)
    E_aux_solar_and_heat_recovery_W = np.sum(E_aux_solar_and_heat_recovery_W)



    CO2_emitted, Eprim_used = calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W, Q_uncovered_W,
                                                          E_coldsource_HPSew_W, E_coldsource_HPLake_W, E_coldsource_GHP_W,
                                                          E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W,
                                                          E_gas_CHP_W, E_gas_BaseBoiler_W, E_gas_PeakBoiler_W,
                                                          E_wood_Furnace_W, Q_BackupBoiler_sum_W,
                                                          np.sum(E_aux_AddBoiler_req_W),
                                                          np.sum(E_solar_gen_W), np.sum(Q_SCandPVT_gen_Wh),
                                                          Q_storage_content_W,
                                                          master_to_slave_vars, locator, E_aux_solar_and_heat_recovery_W,
                                                          E_aux_storage_operation_sum_W, gv)

    # sum up results from PP Activation
    E_consumed_sum_W = np.sum(E_aux_storage_solar_and_heat_recovery_req_W) + np.sum(E_aux_activation_req_W)

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

    KEV_total = KEV_RpPerkWhPVT / 100 * np.sum(E_PVT_gen_W) / 1000 + KEV_RpPerkWhPV / 100 * np.sum(E_PV_gen_W) / 1000
    # Units: from Rp/kWh to CHF/Wh

    price_obtained_from_KEV_for_PVandPVT = KEV_total
    cost_CHP_maintenance = np.sum(E_CHP_gen_W) * prices.CC_MAINTENANCE_PER_KWHEL / 1000.0

    # Fill up storage if end-of-season energy is lower than beginning of season
    Q_Storage_SeasonEndReheat_W = Q_storage_content_W[-1] - Q_storage_content_W[0]

    gas_price = prices.NG_PRICE

    if Q_Storage_SeasonEndReheat_W > 0:
        cost_Boiler_for_Storage_reHeat_at_seasonend = float(Q_Storage_SeasonEndReheat_W) / 0.8 * gas_price
    else:
        cost_Boiler_for_Storage_reHeat_at_seasonend = 0

    # CHANGED AS THE COST_DATA INCLUDES COST_ELECTRICITY_TOTAL ALREADY! (= double accounting)
    cost_HP_aux_uncontrollable = np.sum(E_aux_solar_and_heat_recovery_W) * ELEC_PRICE
    cost_HP_storage_operation = np.sum(E_aux_storage_solar_and_heat_recovery_req_W) * ELEC_PRICE

    cost_sum = np.sum(Opex_var_HP_Sewage) + np.sum(Opex_var_HP_Lake) + np.sum(Opex_var_GHP) + np.sum(
        Opex_var_CHP) + np.sum(Opex_var_Furnace) + np.sum(Opex_var_BaseBoiler) + np.sum(
        Opex_var_PeakBoiler) - price_obtained_from_KEV_for_PVandPVT - prices.ELEC_PRICE * np.sum(
        E_CHP_gen_W) + Opex_var_BackupBoiler_total + cost_CHP_maintenance + \
               cost_Boiler_for_Storage_reHeat_at_seasonend + cost_HP_aux_uncontrollable + cost_HP_storage_operation

    save_cost = 1

    E_oil_eq_MJ = Eprim_used
    CO2_kg_eq = CO2_emitted

    # Calculate primary energy from ressources:
    E_gas_Primary_W = Q_BackupBoiler_sum_W + np.sum(E_gas_HPSew_W) + np.sum(E_gas_HPLake_W) + np.sum(
        E_gas_GHP_W) + np.sum(E_gas_CHP_W) + np.sum(E_gas_Furnace_W) + np.sum(E_gas_BaseBoiler_W) + np.sum(
        E_gas_PeakBoiler_W)
    E_wood_Primary_W = np.sum(E_wood_HPSew_W) + np.sum(E_wood_HPLake_W) + np.sum(E_wood_GHP_W) + np.sum(
        E_wood_CHP_W) + np.sum(E_wood_Furnace_W) + np.sum(E_wood_BaseBoiler_W) + np.sum(E_wood_PeakBoiler_W)
    E_Import_Slave_req_W = E_consumed_sum_W + np.sum(E_aux_AddBoiler_req_W)
    E_Export_gen_W = np.sum(E_total_gen_W)
    E_groundheat_W = np.sum(E_coldsource_HPSew_W) + np.sum(E_coldsource_HPLake_W) + np.sum(E_coldsource_GHP_W) + np.sum(
        E_coldsource_CHP_W) + np.sum(E_coldsource_Furnace_W) + np.sum(E_coldsource_BaseBoiler_W) + np.sum(
        E_coldsource_PeakBoiler_W)
    E_solar_gen_W = np.sum(E_solar_gen_W) + np.sum(Q_SCandPVT_gen_Wh)
    intermediate_max_1 = max(np.amax(E_gas_HPSew_W), np.amax(E_gas_HPLake_W))
    intermediate_max_2 = max(intermediate_max_1, np.amax(E_gas_GHP_W))
    intermediate_max_3 = max(intermediate_max_2, np.amax(E_gas_CHP_W))
    intermediate_max_4 = max(intermediate_max_3, np.amax(E_gas_Furnace_W))
    intermediate_max_5 = max(intermediate_max_4, np.amax(E_gas_BaseBoiler_W))
    intermediate_max_6 = max(intermediate_max_5, np.amax(E_gas_PeakBoiler_W))
    E_gas_PrimaryPeakPower_W = intermediate_max_6 + np.amax(Q_BackupBoiler_W)


    if save_cost == 1:
        results = pd.DataFrame({
            "total cost": [cost_sum],
            "KEV_Remuneration": [price_obtained_from_KEV_for_PVandPVT],
            "costAddBackup_total": [Opex_var_BackupBoiler_total],
            "cost_CHP_maintenance": [cost_CHP_maintenance],
            "costHPSew_sum": np.sum(Opex_var_HP_Sewage),
            "costHPLake_sum": np.sum(Opex_var_HP_Lake),
            "costGHP_sum": np.sum(Opex_var_GHP),
            "costCHP_sum": np.sum(Opex_var_CHP),
            "costFurnace_sum": np.sum(Opex_var_Furnace),
            "costBaseBoiler_sum": np.sum(Opex_var_BaseBoiler),
            "costPeakBoiler_sum": np.sum(Opex_var_PeakBoiler),
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
            "E_solar_gen_Wh": [E_solar_gen_W]
        })
        results.to_csv(locator.get_optimization_slave_cost_prime_primary_energy_data(MS_Var.configKey), sep=',')

    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, Q_uncovered_design_W, Q_uncovered_annual_W


def calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W, Q_uncovered_W,
                                E_coldsource_HPSew_W, E_coldsource_HPLake_W, E_coldsource_GHP_W,
                                E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W,
                                E_gas_CHP_W, E_gas_BaseBoiler_W, E_gas_PeakBoiler_W,
                                E_wood_Furnace_W,
                                Q_gas_AdduncoveredBoilerSum_W, E_aux_AddBoilerSum_W,
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

    E_AuxillaryBoilerAllSum_W = np.sum(E_BaseBoiler_req_W) + np.sum(E_PeakBoiler_req_W) + E_aux_AddBoilerSum_W

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

    CO2_from_Sewage = np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * SEWAGEHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_GHP = np.sum(Q_GHP_gen_W) / COP_GHP_avg * GHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_HPLake = np.sum(Q_HPLake_gen_W) / COP_HPLake_avg * LAKEHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_HP = CO2_from_Sewage + CO2_from_GHP + CO2_from_HPLake
    CO2_from_CC_gas = 1 / eta_CC_avg * np.sum(Q_CHP_gen_W) * gas_to_co2_CC_std * gv.Wh_to_J / 1.0E6
    CO2_from_BaseBoiler_gas = 1 / eta_Boiler_avg * np.sum(
        Q_BaseBoiler_gen_W) * gas_to_co2_BoilerBase_std * gv.Wh_to_J / 1.0E6
    CO2_from_PeakBoiler_gas = 1 / eta_PeakBoiler_avg * np.sum(
        Q_PeakBoiler_gen_W) * gas_to_co2_BoilerPeak_std * gv.Wh_to_J / 1.0E6
    CO2_from_AddBoiler_gas = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_co2_BoilerBackup_std * gv.Wh_to_J / 1.0E6
    CO2_from_fictiveBoilerStorage = E_gasPrim_fictiveBoiler * NG_BOILER_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    CO2_from_gas = CO2_from_CC_gas + CO2_from_BaseBoiler_gas + CO2_from_PeakBoiler_gas + CO2_from_AddBoiler_gas \
                   + CO2_from_fictiveBoilerStorage
    CO2_from_wood = np.sum(Q_Furnace_gen_W) * FURNACE_TO_CO2_STD / eta_furnace_avg * gv.Wh_to_J / 1.0E6
    CO2_from_elec_sold = np.sum(E_Furnace_gen_W) * (- el_to_co2) * gv.Wh_to_J / 1.0E6 \
                         + np.sum(E_CHP_gen_W) * (- el_to_co2) * gv.Wh_to_J / 1.0E6 \
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

    E_prim_from_CC_gas = 1 / eta_CC_avg * np.sum(Q_CHP_gen_W) * gas_to_oil_CC_std * gv.Wh_to_J / 1.0E6
    E_prim_from_BaseBoiler_gas = 1 / eta_Boiler_avg * np.sum(
        Q_BaseBoiler_gen_W) * gas_to_oil_BoilerBase_std * gv.Wh_to_J / 1.0E6
    E_prim_from_PeakBoiler_gas = 1 / eta_PeakBoiler_avg * np.sum(
        Q_PeakBoiler_gen_W) * gas_to_oil_BoilerPeak_std * gv.Wh_to_J / 1.0E6
    E_prim_from_AddBoiler_gas = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_oil_BoilerBackup_std * gv.Wh_to_J / 1.0E6
    E_prim_from_FictiveBoiler_gas = E_gasPrim_fictiveBoiler * NG_BOILER_TO_OIL_STD * gv.Wh_to_J / 1.0E6

    E_prim_from_gas = E_prim_from_CC_gas + E_prim_from_BaseBoiler_gas + E_prim_from_PeakBoiler_gas \
                      + E_prim_from_AddBoiler_gas + E_prim_from_FictiveBoiler_gas

    E_prim_from_wood = 1 / eta_furnace_avg * np.sum(Q_Furnace_gen_W) * FURNACE_TO_OIL_STD * gv.Wh_to_J / 1.0E6

    E_primSaved_from_elec_sold_Furnace = np.sum(E_Furnace_gen_W) * (- el_to_oil_eq) * gv.Wh_to_J / 1.0E6
    E_primSaved_from_elec_sold_CHP = np.sum(E_CHP_gen_W) * (- el_to_oil_eq) * gv.Wh_to_J / 1.0E6
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
