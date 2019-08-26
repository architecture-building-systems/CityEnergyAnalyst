"""
Disctrict Cooling Network Calculations.

Use free cooling from Lake as long as possible ( HP Lake operation from slave)
If Lake exhausted, then use other supply technologies

"""
from __future__ import division

from math import log

import numpy as np
import pandas as pd

import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as VCCModel
import cea.technologies.cogeneration as cogeneration
import cea.technologies.cooling_tower as CTModel
import cea.technologies.storage_tank as storage_tank
import cea.technologies.thermal_storage as thermal_storage
from cea.constants import HOURS_IN_YEAR
from cea.constants import WH_TO_J
from cea.optimization.constants import SIZING_MARGIN, ACH_T_IN_FROM_CHP, ACH_TYPE_DOUBLE, T_TANK_FULLY_DISCHARGED_K, \
    PUMP_ETA
from cea.optimization.master.cost_model import calc_network_costs
from cea.optimization.slave.cooling_resource_activation import cooling_resource_activator
from cea.technologies.constants import DT_COOL
from cea.technologies.pumps import calc_Cinv_pump
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
                             master_to_slave_vars,
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

    ############# Recover the cooling needs
    # Cooling demands in a neighborhood are divided into three categories currently. They are
    # 1. Space Cooling in buildings
    # 2. Data center Cooling
    # 3. Refrigeration Needs
    # Data center cooling can also be done by recovering the heat and heating other demands during the same time
    # whereas Space cooling and refrigeration needs are to be provided by District Cooling Network or decentralized cooling
    # Currently, all the buildings are assumed to be connected to DCN
    # In the following code, the cooling demands of Space cooling and refrigeration are first satisfied by using Lake and VCC
    # This is then followed by checking of the Heat recovery from Data Centre, if it is allowed, then the corresponding
    # cooling demand is ignored. If not, the corresponding coolind demand is also satisfied by DCN.

    # local variables
    DCN_barcode = master_to_slave_vars.DCN_barcode
    building_names = master_to_slave_vars.building_names_cooling

    # THERMAL STORAGE + NETWORK
    # Import Temperatures from Network Summary:
    Q_thermal_req_W, T_district_cooling_return_K, T_district_cooling_supply_K, mdot_kgpers = calc_network_summary_DCN(
        locator, master_to_slave_vars)

    print("CALCULATING ECOLOGICAL COSTS OF DAILY COOLING STORAGE - DUE TO OPERATION (IF ANY)")
    if master_to_slave_vars.Storage_cooling_on == 1:
        T_tank_fully_charged_K = min(
            T_district_cooling_supply_K) - DT_COOL  # the lowest temperature that is able to provide cooling
        T_tank_fully_discharged_K = max(
            T_district_cooling_return_K) - DT_COOL  # the highest temperature that is able to provide cooling
        Qc_tank_charging_limit_W = master_to_slave_vars.Storage_cooling_size_W
        V_tank_m3 = storage_tank.calc_storage_tank_properties(Qc_tank_charging_limit_W,
                                                              T_tank_fully_charged_K,
                                                              T_tank_fully_discharged_K)
    else:
        Qc_tank_charging_limit_W = 0
        V_tank_m3 = 0
        T_tank_fully_charged_K = 0
        T_tank_fully_discharged_K = 0

    storage_tank_properties_previous_timestep = {
        "V_tank_m3": V_tank_m3,
        "T_tank_K": T_TANK_FULLY_DISCHARGED_K,
        "Qc_tank_charging_limit_W": Qc_tank_charging_limit_W,
        "T_tank_fully_charged_K": T_tank_fully_charged_K,
        "T_tank_fully_discharged_K": T_tank_fully_discharged_K,
    }

    # Import Data - potentials lake heat
    if master_to_slave_vars.WS_BaseVCC_on == 1 or master_to_slave_vars.WS_PeakVCC_on == 1 or:
        HPlake_Data = pd.read_csv(locator.get_lake_potential())
        Q_therm_Lake = np.array(HPlake_Data['QLake_kW']) * 1E3
        total_WS_VCC_installed = master_to_slave_vars.WS_BaseVCC_size_W + master_to_slave_vars.WS_PeakVCC_size_W
        Q_therm_Lake_W = [x if x < total_WS_VCC_installed else total_WS_VCC_installed for x in Q_therm_Lake]
        T_source_average_Lake_K = np.array(HPlake_Data['Ts_C']) + 273
    else:
        Q_therm_Lake_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_Lake_K = np.zeros(HOURS_IN_YEAR)

    T_ground_K = calculate_ground_temperature(locator, config)


    Qc_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)
    Qc_BaseVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
    Qc_PeakVCC_WS_gen_W = np.zeros(HOURS_IN_YEAR)
    Qc_BaseVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)
    Qc_PeakVCC_AS_gen_W = np.zeros(HOURS_IN_YEAR)

    Qc_from_storage_tank_W = np.zeros(HOURS_IN_YEAR)
    Qc_from_VCC_backup_W = np.zeros(HOURS_IN_YEAR)

    Qc_req_from_CT_W = np.zeros(HOURS_IN_YEAR)
    Qh_req_from_CCGT_W = np.zeros(HOURS_IN_YEAR)
    Qh_from_CCGT_W = np.zeros(HOURS_IN_YEAR)
    E_gen_CCGT_W = np.zeros(HOURS_IN_YEAR)

    opex_var_Trigen_NG_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_BaseVCC_WS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_PeakVCC_WS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_BaseVCC_AS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_PeakVCC_AS_USDhr = np.zeros(HOURS_IN_YEAR)

    opex_var_BackupVCC_AS_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_CCGT_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_CT_USDhr = np.zeros(HOURS_IN_YEAR)

    deltaPmax = np.zeros(HOURS_IN_YEAR)

    E_Trigen_NG_req_W = np.zeros(HOURS_IN_YEAR)
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

            storage_tank_properties_this_timestep, \
            opex_output, \
            activation_output, \
            thermal_output, \
            electricity_output, \
            gas_output = cooling_resource_activator(Q_thermal_req_W[hour],
                                                    mdot_kgpers[hour],
                                                    T_district_cooling_supply_K[hour],
                                                    T_district_cooling_return_K[hour],
                                                    Q_therm_Lake_W[hour],
                                                    T_source_average_Lake_K[hour],
                                                    storage_tank_properties_previous_timestep,
                                                    T_ground_K[hour],
                                                    lca,
                                                    master_to_slave_vars,
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

            Qc_Trigen_NG_gen_W[hour] = thermal_output['Qc_Trigen_NG_gen_W']
            Qc_BaseVCC_WS_gen_W[hour] = thermal_output['Qc_BaseVCC_WS_gen_W']
            Qc_PeakVCC_WS_gen_W[hour] = thermal_output['Qc_PeakVCC_WS_gen_W']
            Qc_BaseVCC_AS_gen_W[hour] = thermal_output['Qc_BaseVCC_AS_gen_W']
            Qc_PeakVCC_AS_gen_W[hour] = thermal_output['Qc_PeakVCC_AS_gen_W']

            Qc_from_storage_tank_W[hour] = thermal_output['Qc_from_Tank_W']

            Qc_from_VCC_backup_W[hour] = thermal_output['Qc_from_backup_VCC_W']

            Qc_req_from_CT_W[hour] = Qc_CT_W
            Qh_req_from_CCGT_W[hour] = Qh_CHP_ACH_W

            E_Trigen_NG_req_W[hour] = electricity_output['E_Trigen_NG_req_W']
            E_BaseVCC_WS_req_W[hour] = electricity_output['E_BaseVCC_WS_req_W']
            E_PeakVCC_WS_req_W[hour] = electricity_output['E_PeakVCC_WS_req_W']
            E_BaseVCC_AS_req_W[hour] = electricity_output['E_BaseVCC_AS_req_W']
            E_PeakVCC_AS_req_W[hour] = electricity_output['E_PeakVCC_AS_req_W']
            E_BackupVCC_AS_req_W[hour] = electricity_output['E_BackupVCC_AS_req_W']

            NG_Trigen_req_W = gas_output['NG_Trigen_req_W']

        storage_tank_properties_previous_timestep = storage_tank_properties_this_timestep

    ## Operation of the cooling tower
    # TODO: so this can be vectorized. split between costs and emissions
    if Q_CT_nom_W > 0:
        for hour in range(HOURS_IN_YEAR):
            wdot_CT_Wh = CTModel.calc_CT(Qc_req_from_CT_W[hour], Q_CT_nom_W)
            opex_var_CT_USDhr[hour] = (wdot_CT_Wh) * lca.ELEC_PRICE[hour]
            GHG_CT_tonCO2[hour] = (wdot_CT_Wh * WH_TO_J / 1E6) * (lca.EL_TO_CO2 / 1E3)
            prim_energy_CT_MJoil[hour] = (wdot_CT_Wh * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
            E_used_CT_W[hour] = wdot_CT_Wh



    # CAPEX AND FIXED OPEX GENERATION UNITS
    performance_costs = calc_generation_costs_cooling(E_BaseVCC_WS_req_W,
                                                      Q_CT_nom_W,
                                                      Q_GT_nom_W,
                                                      Qc_ACH_nom_W,
                                                      Qc_VCC_backup_nom_W,
                                                      Qc_VCC_nom_W,
                                                      V_tank_m3,
                                                      config,
                                                      locator,
                                                      master_to_slave_vars
                                                      )

    # CAPEX VAR GENERATION UNITS
    Opex_var_Lake_connected_USD = sum(opex_var_BaseVCC_WS_USDhr),
    Opex_var_VCC_connected_USD = sum(opex_var_BaseVCC_AS_USDhr),
    Opex_var_ACH_connected_USD = sum(opex_var_Trigen_NG_USDhr),
    Opex_var_VCC_backup_connected_USD = sum(opex_var_BackupVCC_AS_USDhr),
    Opex_var_CT_connected_USD = sum(opex_var_CT_USDhr),
    Opex_var_CCGT_connected_USD = sum(opex_var_CCGT_USDhr),

    # COOLING NETWORK
    Capex_DCN_USD, \
    Capex_a_DCN_USD, \
    Opex_fixed_DCN_USD, \
    Opex_var_DCN_USD, \
    E_used_district_cooling_netowrk_W = calc_network_costs(locator,
                                                           master_to_slave_vars,
                                                           network_features,
                                                           lca,
                                                           "DC")
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
        "Q_VCC_WS_W": Qc_BaseVCC_WS_gen_W,
        "Q_VCC_AS_W": Qc_BaseVCC_AS_gen_W,
        "Q_VCC_backup_AS_W": Qc_from_VCC_backup_W,
        "Q_Trigen_NG_W": Qc_Trigen_NG_gen_W,
        "Q_Storage_gen_W": Qc_from_storage_tank_W,

        # electricity
        "E_Trigen_NG_gen_W": E_gen_CCGT_W,

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


def calc_generation_costs_cooling(E_used_Lake_W,
                                  Q_CT_nom_W,
                                  Q_GT_nom_W,
                                  Qc_ACH_nom_W,
                                  Qc_VCC_backup_nom_W,
                                  Qc_VCC_nom_W,
                                  V_tank_m3,
                                  config,
                                  locator,
                                  master_to_slave_vars):
    # WATER-SOURCE VAPOR COMPRESION CHILLER
    if master_to_slave_vars.Lake_cooling_on == 1:
        mdotnMax_kgpers = df.loc[df['E_used_Lake_W'] == E_used_Lake_W.max(), 'mdot_DCN_kgpers'].iloc[0]
        deltaPmax = df.loc[df['E_used_Lake_W'] == E_used_Lake_W.max(), 'deltaPmax'].iloc[0]
        Capex_a_Lake_USD, Opex_fixed_Lake_USD, Capex_Lake_USD = calc_Cinv_pump(deltaPmax, mdotnMax_kgpers, PUMP_ETA,
                                                                               locator, 'PU1')
    # AIR_SOURCE VAPOR COMPRESSION CHILLER
    if master_to_slave_vars.VCC_on == 1:
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_nom_W, locator, config,
                                                                                    'CH3')

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Q_CT_nom_W, locator, 'CT1')
    # TRIGENERATION
    if master_to_slave_vars.Absorption_Chiller_on == 1:
        # ACH
        Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_ACH_nom_W, locator,
                                                                                              ACH_TYPE_DOUBLE)
        # CCGT
        Capex_a_CCGT_USD, Opex_fixed_CCGT_USD, Capex_CCGT_USD = cogeneration.calc_Cinv_CCGT(Q_GT_nom_W, locator, config)
    # COLD WATER STORAGE TANK
    if master_to_slave_vars.Storage_cooling_on == 1:
        Capex_a_Tank_USD, Opex_fixed_Tank_USD, Capex_Tank_USD = thermal_storage.calc_Cinv_storage(V_tank_m3, locator,
                                                                                                  config, 'TES2')
    # BACK-UP VCC
    master_to_slave_vars.VCC_backup_cooling_size_W = Qc_VCC_backup_nom_W
    Capex_a_VCC_backup_USD, \
    Opex_fixed_VCC_backup_USD, \
    Capex_VCC_backup_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_backup_nom_W, locator, config, 'CH3')

    # PLOT RESULTS
    performance = {
        # annualized capex
        "Capex_a_Lake_connected_USD": Capex_a_Lake_USD,
        "Capex_a_VCC_connected_USD": Capex_a_VCC_USD,
        "Capex_a_VCC_backup_connected_USD": Capex_a_VCC_backup_USD,
        "Capex_a_ACH_connected_USD": Capex_a_ACH_USD,
        "Capex_a_CCGT_connected_USD": Capex_a_CCGT_USD,
        "Capex_a_Tank_connected_USD": Capex_a_Tank_USD,
        "Capex_a_CT_connected_USD": Capex_a_CT_USD,

        # total capex
        "Capex_total_Lake_connected_USD": Capex_Lake_USD,
        "Capex_total_VCC_connected_USD": Capex_VCC_USD,
        "Capex_total_VCC_backup_connected_USD": Capex_VCC_backup_USD,
        "Capex_total_ACH_connected_USD": Capex_ACH_USD,
        "Capex_total_CCGT_connected_USD": Capex_CCGT_USD,
        "Capex_total_Tank_connected_USD": Capex_Tank_USD,
        "Capex_total_CT_connected_USD": Capex_CT_USD,

        # opex fixed
        "Opex_fixed_Lake_connected_USD": Opex_fixed_Lake_USD,
        "Opex_fixed_VCC_connected_USD": Opex_fixed_VCC_USD,
        "Opex_fixed_ACH_connected_USD": Opex_fixed_ACH_USD,
        "Opex_fixed_VCC_backup_connected_USD": Opex_fixed_VCC_backup_USD,
        "Opex_fixed_CCGT_connected_USD": Opex_fixed_CCGT_USD,
        "Opex_fixed_Tank_connected_USD": Opex_fixed_Tank_USD,
        "Opex_fixed_CT_connected_USD": Opex_fixed_CT_USD
    }

    return performance


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
