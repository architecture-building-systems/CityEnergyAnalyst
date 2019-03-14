"""
FIND LEAST COST FUNCTION
USING PRESET ORDER

"""

from __future__ import division
import time
import numpy as np
import pandas as pd
from cea.optimization.constants import ETA_AREA_TO_PEAK, HP_SEW_ALLOWED
from cea.constants import WH_TO_J
from cea.technologies.boiler import cond_boiler_op_cost
from cea.optimization.slave.heating_resource_activation import heating_source_activator
from cea.resources.geothermal import calc_ground_temperature
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

def heating_calculations_of_DH_buildings(locator, master_to_slave_vars, gv, config, prices, lca):
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
    network_data = pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_heating))
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
    Opex_var_HP_Sewage_USD = np.zeros(8760)
    Opex_var_HP_Lake_USD = np.zeros(8760)
    Opex_var_GHP_USD = np.zeros(8760)
    Opex_var_CHP_USD = np.zeros(8760)
    Opex_var_Furnace_USD = np.zeros(8760)
    Opex_var_BaseBoiler_USD = np.zeros(8760)
    Opex_var_PeakBoiler_USD = np.zeros(8760)

    source_HP_Sewage = np.zeros(8760)
    source_HP_Lake = np.zeros(8760)
    source_GHP = np.zeros(8760)
    source_CHP = np.zeros(8760)
    source_Furnace = np.zeros(8760)
    source_BaseBoiler = np.zeros(8760)
    source_PeakBoiler = np.zeros(8760)

    Q_HPSew_gen_W = np.zeros(8760)
    Q_HPLake_gen_W = np.zeros(8760)
    Q_GHP_gen_W = np.zeros(8760)
    Q_CHP_gen_W = np.zeros(8760)
    Q_Furnace_gen_W = np.zeros(8760)
    Q_BaseBoiler_gen_W = np.zeros(8760)
    Q_PeakBoiler_gen_W = np.zeros(8760)
    Q_uncovered_W = np.zeros(8760)

    E_HPSew_req_W = np.zeros(8760)
    E_HPLake_req_W = np.zeros(8760)
    E_GHP_req_W = np.zeros(8760)
    E_CHP_gen_W = np.zeros(8760)
    E_Furnace_gen_W = np.zeros(8760)
    E_BaseBoiler_req_W = np.zeros(8760)
    E_PeakBoiler_req_W = np.zeros(8760)

    NG_used_HPSew_W = np.zeros(8760)
    NG_used_HPLake_W = np.zeros(8760)
    NG_used_GHP_W = np.zeros(8760)
    NG_used_CHP_W = np.zeros(8760)
    NG_used_Furnace_W = np.zeros(8760)
    NG_used_BaseBoiler_W = np.zeros(8760)
    NG_used_PeakBoiler_W = np.zeros(8760)
    NG_used_BackupBoiler_W = np.zeros(8760)


    BG_used_HPSew_W = np.zeros(8760)
    BG_used_HPLake_W = np.zeros(8760)
    BG_used_GHP_W = np.zeros(8760)
    BG_used_CHP_W = np.zeros(8760)
    BG_used_Furnace_W = np.zeros(8760)
    BG_used_BaseBoiler_W = np.zeros(8760)
    BG_used_PeakBoiler_W = np.zeros(8760)

    Wood_used_HPSew_W = np.zeros(8760)
    Wood_used_HPLake_W = np.zeros(8760)
    Wood_used_GHP_W = np.zeros(8760)
    Wood_used_CHP_W = np.zeros(8760)
    Wood_used_Furnace_W = np.zeros(8760)
    Wood_used_BaseBoiler_W = np.zeros(8760)
    Wood_used_PeakBoiler_W = np.zeros(8760)

    Q_coldsource_HPSew_W = np.zeros(8760)
    Q_coldsource_HPLake_W = np.zeros(8760)
    Q_coldsource_GHP_W = np.zeros(8760)
    Q_coldsource_CHP_W = np.zeros(8760)
    Q_coldsource_Furnace_W = np.zeros(8760)
    Q_coldsource_BaseBoiler_W = np.zeros(8760)
    Q_coldsource_PeakBoiler_W = np.zeros(8760)

    Q_excess_W = np.zeros(8760)
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent',
                                                         'windspd_ms', 'skytemp_C']]
    ground_temp = calc_ground_temperature(locator, config, weather_data['drybulb_C'], depth_m=10)

    for hour in range(8760):
        Q_therm_req_W = Q_missing_W[hour]
        # cost_data_centralPlant_op[hour, :], source_info[hour, :], Q_source_data_W[hour, :], E_coldsource_data_W[hour,
        #                                                                                     :], \
        # E_PP_el_data_W[hour, :], E_gas_data_W[hour, :], E_wood_data_W[hour, :], Q_excess_W[hour] = source_activator(
        #     Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_kgpers[hour], tdhsup_K,
        #     tdhret_K[hour], TretsewArray_K[hour], gv, prices)
        opex_output, source_output, Q_output, E_output, Gas_output, Wood_output, coldsource_output, Q_excess_W[
            hour] = heating_source_activator(
            Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_kgpers[hour], tdhsup_K[hour],
            tdhret_K[hour], TretsewArray_K[hour], gv, prices, lca, ground_temp[hour], config)

        Opex_var_HP_Sewage_USD[hour] = opex_output['Opex_var_HP_Sewage_USD']
        Opex_var_HP_Lake_USD[hour] = opex_output['Opex_var_HP_Lake_USD']
        Opex_var_GHP_USD[hour] = opex_output['Opex_var_GHP_USD']
        Opex_var_CHP_USD[hour] = opex_output['Opex_var_CHP_USD']
        Opex_var_Furnace_USD[hour] = opex_output['Opex_var_Furnace_USD']
        Opex_var_BaseBoiler_USD[hour] = opex_output['Opex_var_BaseBoiler_USD']
        Opex_var_PeakBoiler_USD[hour] = opex_output['Opex_var_PeakBoiler_USD']

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
    Opex_var_BackupBoiler_USD = np.zeros(8760)
    Q_BackupBoiler_W = np.zeros(8760)
    E_BackupBoiler_req_W = np.zeros(8760)

    Opex_var_Furnace_wet_USD = np.zeros(8760)
    Opex_var_Furnace_dry_USD = np.zeros(8760)
    Opex_var_CHP_NG_USD = np.zeros(8760)
    Opex_var_CHP_BG_USD = np.zeros(8760)
    Opex_var_BaseBoiler_NG_USD = np.zeros(8760)
    Opex_var_BaseBoiler_BG_USD = np.zeros(8760)
    Opex_var_PeakBoiler_NG_USD = np.zeros(8760)
    Opex_var_PeakBoiler_BG_USD = np.zeros(8760)
    Opex_var_BackupBoiler_NG_USD = np.zeros(8760)
    Opex_var_BackupBoiler_BG_USD = np.zeros(8760)

    Opex_var_PV_USD = np.zeros(8760)
    Opex_var_PVT_USD = np.zeros(8760)
    Opex_var_SC_USD = np.zeros(8760)

    if Q_uncovered_design_W != 0:
        for hour in range(8760):
            tdhret_req_K = tdhret_K[hour]
            BoilerBackup_Cost_Data = cond_boiler_op_cost(Q_uncovered_W[hour], Q_uncovered_design_W, tdhret_req_K, \
                                                         master_to_slave_vars.BoilerBackupType,
                                                         master_to_slave_vars.EL_TYPE, prices, lca, hour)
            Opex_var_BackupBoiler_USD[hour], Opex_var_BackupBoiler_per_Wh_USD, Q_BackupBoiler_W[
                hour], E_BackupBoiler_req_W_hour = BoilerBackup_Cost_Data
            E_BackupBoiler_req_W[hour] = E_BackupBoiler_req_W_hour
            NG_used_BackupBoiler_W[hour] = Q_BackupBoiler_W[hour]
        Q_BackupBoiler_sum_W = np.sum(Q_BackupBoiler_W)
        Opex_t_var_BackupBoiler_USD = np.sum(Opex_var_BackupBoiler_USD)

    else:
        Q_BackupBoiler_sum_W = 0.0
        Opex_t_var_BackupBoiler_USD = 0.0

    if master_to_slave_vars.Furn_Moist_type == "wet":
        Opex_var_Furnace_wet_USD = Opex_var_Furnace_USD
    elif master_to_slave_vars.Furn_Moist_type == "dry":
        Opex_var_Furnace_dry_USD = Opex_var_Furnace_USD

    if master_to_slave_vars.gt_fuel == "NG":
        Opex_var_CHP_NG_USD = Opex_var_CHP_USD
        Opex_var_BaseBoiler_NG_USD = Opex_var_BaseBoiler_USD
        Opex_var_PeakBoiler_NG_USD = Opex_var_PeakBoiler_USD
        Opex_var_BackupBoiler_NG_USD = Opex_var_BackupBoiler_USD

    elif master_to_slave_vars.gt_fuel == "BG":
        Opex_var_CHP_BG_USD = Opex_var_CHP_USD
        Opex_var_BaseBoiler_BG_USD = Opex_var_BaseBoiler_USD
        Opex_var_PeakBoiler_BG_USD = Opex_var_PeakBoiler_USD
        Opex_var_BackupBoiler_BG_USD = Opex_var_BackupBoiler_USD

    # saving pattern activation to disk
    date = network_data.DATE.values
    results = pd.DataFrame({"DATE": date,
                            "Q_Network_Demand_after_Storage_W": Q_missing_copy_W,
                            "Opex_var_HP_Sewage": Opex_var_HP_Sewage_USD,
                            "Opex_var_HP_Lake": Opex_var_HP_Lake_USD,
                            "Opex_var_GHP": Opex_var_GHP_USD,
                            "Opex_var_CHP_BG": Opex_var_CHP_BG_USD,
                            "Opex_var_CHP_NG": Opex_var_CHP_NG_USD,
                            "Opex_var_Furnace_wet": Opex_var_Furnace_wet_USD,
                            "Opex_var_Furnace_dry": Opex_var_Furnace_dry_USD,
                            "Opex_var_BaseBoiler_BG": Opex_var_BaseBoiler_BG_USD,
                            "Opex_var_BaseBoiler_NG": Opex_var_BaseBoiler_NG_USD,
                            "Opex_var_PeakBoiler_BG": Opex_var_PeakBoiler_BG_USD,
                            "Opex_var_PeakBoiler_NG": Opex_var_PeakBoiler_NG_USD,
                            "Opex_var_BackupBoiler_BG": Opex_var_BackupBoiler_BG_USD,
                            "Opex_var_BackupBoiler_NG": Opex_var_BackupBoiler_NG_USD,
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
                                                                             master_to_slave_vars.generation_number), index=False)

    if master_to_slave_vars.gt_fuel == "NG":

        CO2_emitted, PEN_used = calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W,
                                                              Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W,
                                                              Q_uncovered_W,
                                                              Q_coldsource_HPSew_W, Q_coldsource_HPLake_W,
                                                              Q_coldsource_GHP_W,
                                                              E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W,
                                                              E_PeakBoiler_req_W,
                                                              NG_used_CHP_W, NG_used_BaseBoiler_W, NG_used_PeakBoiler_W,
                                                              Wood_used_Furnace_W, Q_BackupBoiler_sum_W,
                                                              np.sum(E_BackupBoiler_req_W),
                                                              master_to_slave_vars, locator, lca)
    elif master_to_slave_vars.gt_fuel == "BG":

        CO2_emitted, PEN_used = calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W,
                                                              Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W,
                                                              Q_uncovered_W,
                                                              Q_coldsource_HPSew_W, Q_coldsource_HPLake_W,
                                                              Q_coldsource_GHP_W,
                                                              E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W,
                                                              E_PeakBoiler_req_W,
                                                              BG_used_CHP_W, BG_used_BaseBoiler_W, BG_used_PeakBoiler_W,
                                                              Wood_used_Furnace_W, Q_BackupBoiler_sum_W,
                                                              np.sum(E_BackupBoiler_req_W),
                                                              master_to_slave_vars, locator, lca)




    cost_sum = np.sum(Opex_var_HP_Sewage_USD) + np.sum(Opex_var_HP_Lake_USD) + np.sum(Opex_var_GHP_USD) + np.sum(
        Opex_var_CHP_USD) + np.sum(Opex_var_Furnace_USD) + np.sum(Opex_var_BaseBoiler_USD) + np.sum(
        Opex_var_PeakBoiler_USD) + Opex_t_var_BackupBoiler_USD

    E_oil_eq_MJ = PEN_used
    CO2_kg_eq = CO2_emitted

    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, Q_uncovered_design_W, Q_uncovered_annual_W


def calc_primary_energy_and_CO2(Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W,
                                Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W, Q_uncovered_W,
                                E_coldsource_HPSew_W, E_coldsource_HPLake_W, E_coldsource_GHP_W,
                                E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W,
                                E_gas_CHP_W, E_gas_BaseBoiler_W, E_gas_PeakBoiler_W,
                                E_wood_Furnace_W,
                                Q_gas_AdduncoveredBoilerSum_W, E_aux_AddBoilerSum_W,
                                master_to_slave_vars, locator, lca):
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

    GHG_Sewage_tonCO2 = np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * lca.SEWAGEHP_TO_CO2_STD * WH_TO_J / 1.0E6
    GHG_GHP_tonCO2 = np.sum(Q_GHP_gen_W) / COP_GHP_avg * lca.GHP_TO_CO2_STD * WH_TO_J / 1.0E6
    GHG_HPLake_tonCO2 = np.sum(Q_HPLake_gen_W) / COP_HPLake_avg * lca.LAKEHP_TO_CO2_STD * WH_TO_J / 1.0E6
    GHG_HP_tonCO2 = GHG_Sewage_tonCO2 + GHG_GHP_tonCO2 + GHG_HPLake_tonCO2
    GHG_CC_tonCO2 = 1 / eta_CC_avg * np.sum(Q_CHP_gen_W) * gas_to_co2_CC_std * WH_TO_J / 1.0E6
    GHG_BaseBoiler_tonCO2 = 1 / eta_Boiler_avg * np.sum(
        Q_BaseBoiler_gen_W) * gas_to_co2_BoilerBase_std * WH_TO_J / 1.0E6
    GHG_PeakBoiler_tonCO2 = 1 / eta_PeakBoiler_avg * np.sum(
        Q_PeakBoiler_gen_W) * gas_to_co2_BoilerPeak_std * WH_TO_J / 1.0E6
    GHG_AddBoiler_tonCO2 = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_co2_BoilerBackup_std * WH_TO_J / 1.0E6
    GHG_gas_tonCO2 = GHG_CC_tonCO2 + GHG_BaseBoiler_tonCO2 + GHG_PeakBoiler_tonCO2 + GHG_AddBoiler_tonCO2
    GHG_wood_tonCO2 = np.sum(Q_Furnace_gen_W) * lca.FURNACE_TO_CO2_STD / eta_furnace_avg * WH_TO_J / 1.0E6

    ################## Primary energy needs

    PEN_Sewage_MJoil = np.sum(Q_HPSew_gen_W) / COP_HPSew_avg * lca.SEWAGEHP_TO_OIL_STD * WH_TO_J / 1.0E6
    PEN_GHP_MJoil = np.sum(Q_GHP_gen_W) / COP_GHP_avg * lca.GHP_TO_OIL_STD * WH_TO_J / 1.0E6
    PEN_HPLake_MJoil = np.sum(Q_HPLake_gen_W) / COP_HPLake_avg * lca.LAKEHP_TO_OIL_STD * WH_TO_J / 1.0E6
    PEN_HP_MJoil = PEN_Sewage_MJoil + PEN_GHP_MJoil + PEN_HPLake_MJoil

    PEN_CC_MJoil = 1 / eta_CC_avg * np.sum(Q_CHP_gen_W) * gas_to_oil_CC_std * WH_TO_J / 1.0E6
    PEN_BaseBoiler_MJoil = 1 / eta_Boiler_avg * np.sum(
        Q_BaseBoiler_gen_W) * gas_to_oil_BoilerBase_std * WH_TO_J / 1.0E6
    PEN_PeakBoiler_MJoil = 1 / eta_PeakBoiler_avg * np.sum(
        Q_PeakBoiler_gen_W) * gas_to_oil_BoilerPeak_std * WH_TO_J / 1.0E6
    PEN_AddBoiler_MJoil = 1 / eta_AddBackup_avg * np.sum(
        Q_uncovered_W) * gas_to_oil_BoilerBackup_std * WH_TO_J / 1.0E6

    PEN_gas_MJoil = PEN_CC_MJoil + PEN_BaseBoiler_MJoil + PEN_PeakBoiler_MJoil \
                      + PEN_AddBoiler_MJoil

    PEN_wood_MJoil = 1 / eta_furnace_avg * np.sum(Q_Furnace_gen_W) * lca.FURNACE_TO_OIL_STD * WH_TO_J / 1.0E6


    # Save data
    results = pd.DataFrame({
        "GHG_Sewage_tonCO2": [GHG_Sewage_tonCO2],
        "GHG_GHP_tonCO2": [GHG_GHP_tonCO2],
        "GHG_HPLake_tonCO2": [GHG_HPLake_tonCO2],
        "GHG_CC_tonCO2": [GHG_CC_tonCO2],
        "GHG_BaseBoiler_tonCO2": [GHG_BaseBoiler_tonCO2],
        "GHG_PeakBoiler_tonCO2": [GHG_PeakBoiler_tonCO2],
        "GHG_AddBoiler_tonCO2": [GHG_AddBoiler_tonCO2],
        "GHG_wood_tonCO2": [GHG_wood_tonCO2],
        "PEN_Sewage_MJoil": [PEN_Sewage_MJoil],
        "PEN_GHP_MJoil": [PEN_GHP_MJoil],
        "PEN_HPLake_MJoil": [PEN_HPLake_MJoil],
        "PEN_CC_MJoil": [PEN_CC_MJoil],
        "PEN_BaseBoiler_MJoil": [PEN_BaseBoiler_MJoil],
        "PEN_PeakBoiler_MJoil": [PEN_PeakBoiler_MJoil],
        "PEN_AddBoiler_MJoil": [PEN_AddBoiler_MJoil],
        "PEN_wood_MJoil": [PEN_wood_MJoil]
    })
    results.to_csv(locator.get_optimization_slave_slave_detailed_emission_and_eprim_data(master_to_slave_vars.individual_number,
                                                                                         master_to_slave_vars.generation_number),
                   sep=',')

    ######### Summed up results
    GHG_emitted_tonCO2 = (
            GHG_HP_tonCO2 + GHG_gas_tonCO2 + GHG_wood_tonCO2 )

    PEN_used_MJoil = (PEN_HP_MJoil + PEN_gas_MJoil + PEN_wood_MJoil)

    return GHG_emitted_tonCO2, PEN_used_MJoil