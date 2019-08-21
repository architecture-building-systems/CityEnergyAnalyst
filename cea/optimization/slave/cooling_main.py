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
    PUMP_ETA, ACH_TYPE_SINGLE, VCC_CODE_CENTRALIZED
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
    Qc_VCC_nom_W = master_to_slave_vars.VCC_cooling_size_W
    Qc_ACH_nom_W = master_to_slave_vars.Absorption_chiller_size_W

    # Import Temperatures from Network Summary:
    Q_cooling_req_W, T_re_K, T_sup_K, mdot_kgpers = calc_network_summary_DCN(locator, master_to_slave_vars)

    # Import Data - potentials lake heat
    if master_to_slave_vars.Lake_cooling_on == 1:
        HPlake_Data = pd.read_csv(locator.get_lake_potential())
        Q_therm_Lake = np.array(HPlake_Data['QLake_kW']) * 1E3
        Q_therm_Lake_W = [
            x if x < master_to_slave_vars.Lake_cooling_size_W else master_to_slave_vars.Lake_cooling_size_W for x in
            Q_therm_Lake]
        T_source_average_Lake_K = np.array(HPlake_Data['Ts_C']) + 273
    else:
        Q_therm_Lake_W = np.zeros(HOURS_IN_YEAR)
        T_source_average_Lake_K = np.zeros(HOURS_IN_YEAR)

    T_ground_K = calculate_ground_temperature(locator, config)

    # SIZE THE COLD STORAGE TANK
    # calculate the highest/lowest tank temperatures for sizing 
    T_tank_fully_charged_K = min(T_sup_K) - DT_COOL  # the lowest temperature that is able to provide cooling to DC
    T_tank_fully_discharged_K = max(T_sup_K) - DT_COOL  # the highest temperature that is able to provide cooling to DC
    if master_to_slave_vars.Storage_cooling_size_W > 0.0:
        Qc_tank_discharging_limit_W = master_to_slave_vars.Storage_cooling_size_W  # FIXME: change to Qc_tank_capacity_Wh, and use this to sizing
        # FIXME: Qc_tank_capacity_Wh could be a portion of the Qc required in the peak day (yesterday's discussion)
        Qc_tank_charging_limit_W = (Qc_VCC_nom_W + Qc_ACH_nom_W) * 0.8  # assume reduced capacity when Tsup is lower
        V_tank_m3 = storage_tank.calc_storage_tank_properties(Qc_tank_discharging_limit_W,
                                                              T_tank_fully_charged_K,
                                                              T_tank_fully_discharged_K)
    else:
        Qc_tank_discharging_limit_W = 0
        Qc_tank_charging_limit_W = 0
        V_tank_m3 = 0

    storage_tank_properties = {'V_tank_m3': V_tank_m3,
                               'T_tank_fully_charged_K': T_tank_fully_charged_K,
                               'T_tank_fully_discharged_K': T_tank_fully_discharged_K,
                               'Qc_tank_discharging_limit_W': Qc_tank_discharging_limit_W,
                               # TODO: redundant, because this should be calculated hourly
                               'Qc_tank_charging_limit_W': Qc_tank_charging_limit_W}

    # SIZE CHILLERS (VCC, ACH, backup VCC)
    Qc_peak_load_W = Q_cooling_req_W.max()
    Qc_VCC_backup_nom_W = (Qc_peak_load_W - Qc_ACH_nom_W - Qc_VCC_nom_W - Qc_tank_discharging_limit_W)

    min_ACH_unit_size_W, \
    max_ACH_unit_size_W = chiller_absorption.get_min_max_ACH_unit_size(locator, ACH_TYPE_SINGLE)

    technology_capacities = {'Qc_VCC_nom_W': Qc_VCC_nom_W,
                             'Qc_ACH_nom_W': Qc_ACH_nom_W,
                             'Qc_VCC_backup_nom_W': Qc_VCC_backup_nom_W,
                             'max_ACH_unit_size_W': max_ACH_unit_size_W,
                             'min_ACH_unit_size_W': min_ACH_unit_size_W}

    ### input variables
    cooling_resource_potentials = {'T_tank_K': T_TANK_FULLY_DISCHARGED_K}

    calfactor_buildings = np.zeros(HOURS_IN_YEAR)
    TotalCool = 0
    Qc_from_Lake_W = np.zeros(HOURS_IN_YEAR)
    Qc_from_VCC_W = np.zeros(HOURS_IN_YEAR)
    Qc_from_ACH_W = np.zeros(HOURS_IN_YEAR)
    Qc_from_storage_tank_W = np.zeros(HOURS_IN_YEAR)
    Qc_from_VCC_backup_W = np.zeros(HOURS_IN_YEAR)

    Qc_req_from_CT_W = np.zeros(HOURS_IN_YEAR)
    Qh_req_from_CCGT_W = np.zeros(HOURS_IN_YEAR)
    Qh_from_CCGT_W = np.zeros(HOURS_IN_YEAR)
    E_gen_CCGT_W = np.zeros(HOURS_IN_YEAR)

    opex_var_Lake_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_VCC_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_ACH_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_VCC_backup_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_CCGT_USDhr = np.zeros(HOURS_IN_YEAR)
    opex_var_CT_USDhr = np.zeros(HOURS_IN_YEAR)
    E_used_Lake_W = np.zeros(HOURS_IN_YEAR)
    deltaPmax = np.zeros(HOURS_IN_YEAR)
    E_used_VCC_W = np.zeros(HOURS_IN_YEAR)
    E_used_VCC_backup_W = np.zeros(HOURS_IN_YEAR)
    E_used_ACH_W = np.zeros(HOURS_IN_YEAR)
    E_used_CT_W = np.zeros(HOURS_IN_YEAR)
    GHG_Lake_tonCO2 = np.zeros(HOURS_IN_YEAR)
    GHG_VCC_tonCO2 = np.zeros(HOURS_IN_YEAR)
    GHG_ACH_tonCO2 = np.zeros(HOURS_IN_YEAR)
    GHG_VCC_backup_tonCO2 = np.zeros(HOURS_IN_YEAR)
    GHG_CCGT_tonCO2 = np.zeros(HOURS_IN_YEAR)
    GHG_CT_tonCO2 = np.zeros(HOURS_IN_YEAR)
    prim_energy_Lake_MJoil = np.zeros(HOURS_IN_YEAR)
    prim_energy_VCC_MJoil = np.zeros(HOURS_IN_YEAR)
    prim_energy_ACH_MJoil = np.zeros(HOURS_IN_YEAR)
    prim_energy_VCC_backup_MJoil = np.zeros(HOURS_IN_YEAR)
    prim_energy_CCGT_MJoil = np.zeros(HOURS_IN_YEAR)
    prim_energy_CT_MJoil = np.zeros(HOURS_IN_YEAR)
    NG_used_CCGT_W = np.zeros(HOURS_IN_YEAR)
    Lake_Status = np.zeros(HOURS_IN_YEAR)
    ACH_Status = np.zeros(HOURS_IN_YEAR)
    VCC_Status = np.zeros(HOURS_IN_YEAR)
    VCC_Backup_Status = np.zeros(HOURS_IN_YEAR)
    calfactor_total = 0

    for hour in range(HOURS_IN_YEAR):  # cooling supply for all buildings excluding cooling loads from data centers
        if Q_cooling_req_W[hour] > 0.0:  # only if there is a cooling load!
            performance_indicators_output, \
            Qc_supply_to_DCN, \
            Qc_CT_W, Qh_CHP_ACH_W, \
            cooling_resource_potentials, \
            source_output = cooling_resource_activator(mdot_kgpers[hour],
                                                       T_sup_K[hour],
                                                       T_re_K[hour],
                                                       Q_therm_Lake_W[hour],
                                                       T_source_average_Lake_K[hour],
                                                       storage_tank_properties,
                                                       cooling_resource_potentials,
                                                       T_ground_K[hour],
                                                       technology_capacities,
                                                       lca,
                                                       master_to_slave_vars,
                                                       Q_cooling_req_W[hour],
                                                       hour,
                                                       locator)

            # print (hour)
            # save results for each time-step
            opex_var_Lake_USDhr[hour] = performance_indicators_output['Opex_var_Lake_USD']
            opex_var_VCC_USDhr[hour] = performance_indicators_output['Opex_var_VCC_USD']
            opex_var_ACH_USDhr[hour] = performance_indicators_output['Opex_var_ACH_USD']
            opex_var_VCC_backup_USDhr[hour] = performance_indicators_output['Opex_var_VCC_backup_USD']
            E_used_Lake_W[hour] = performance_indicators_output['E_used_Lake_W']
            E_used_VCC_W[hour] = performance_indicators_output['E_used_VCC_W']
            E_used_VCC_backup_W[hour] = performance_indicators_output['E_used_VCC_backup_W']
            E_used_ACH_W[hour] = performance_indicators_output['E_used_ACH_W']
            GHG_Lake_tonCO2[hour] = performance_indicators_output['GHG_Lake_tonCO2']
            GHG_VCC_tonCO2[hour] = performance_indicators_output['GHG_VCC_tonCO2']
            GHG_ACH_tonCO2[hour] = performance_indicators_output['GHG_ACH_tonCO2']
            GHG_VCC_backup_tonCO2[hour] = performance_indicators_output['GHG_VCC_backup_tonCO2']
            prim_energy_Lake_MJoil[hour] = performance_indicators_output['PEN_Lake_MJoil']
            prim_energy_VCC_MJoil[hour] = performance_indicators_output['PEN_VCC_MJoil']
            prim_energy_ACH_MJoil[hour] = performance_indicators_output['PEN_ACH_MJoil']
            prim_energy_VCC_backup_MJoil[hour] = performance_indicators_output['PEN_VCC_backup_MJoil']
            Qc_from_Lake_W[hour] = Qc_supply_to_DCN['Qc_from_Lake_W']
            Qc_from_storage_tank_W[hour] = Qc_supply_to_DCN['Qc_from_Tank_W']
            Qc_from_VCC_W[hour] = Qc_supply_to_DCN['Qc_from_VCC_W']
            Qc_from_ACH_W[hour] = Qc_supply_to_DCN['Qc_from_ACH_W']
            Qc_from_VCC_backup_W[hour] = Qc_supply_to_DCN['Qc_from_backup_VCC_W']
            Lake_Status[hour] = source_output["Lake_Status"]
            ACH_Status[hour] = source_output["ACH_Status"]
            VCC_Status[hour] = source_output["VCC_Status"]
            VCC_Backup_Status[hour] = source_output["VCC_Backup_Status"]
            deltaPmax[hour] = performance_indicators_output['deltaPmax']

            Qc_req_from_CT_W[hour] = Qc_CT_W
            Qh_req_from_CCGT_W[hour] = Qh_CHP_ACH_W

    calfactor_total += np.sum(calfactor_buildings)
    TotalCool += np.sum(Qc_from_Lake_W) + \
                 np.sum(Qc_from_VCC_W) + \
                 np.sum(Qc_from_ACH_W) + \
                 np.sum(Qc_from_VCC_backup_W) + \
                 np.sum(Qc_from_storage_tank_W)
    Q_CT_nom_W = np.amax(Qc_req_from_CT_W)
    Qh_req_from_CCGT_max_W = np.amax(Qh_req_from_CCGT_W)  # the required heat output from CCGT at peak

    mdot_Max_kgpers = np.amax(mdot_kgpers)  # sizing of DCN network pumps
    Q_GT_nom_W = 0

    ## Operation of the cooling tower
    # TODO: so this can be vectorized. split between costs and emissions
    max_CT_unit_size_W = CTModel.get_CT_max_size(locator)
    if Q_CT_nom_W > 0:
        for hour in range(HOURS_IN_YEAR):
            wdot_CT_Wh = CTModel.calc_CT(Qc_req_from_CT_W[hour], Q_CT_nom_W, max_CT_unit_size_W)
            opex_var_CT_USDhr[hour] = (wdot_CT_Wh) * lca.ELEC_PRICE[hour]
            GHG_CT_tonCO2[hour] = (wdot_CT_Wh * WH_TO_J / 1E6) * (lca.EL_TO_CO2 / 1E3)
            prim_energy_CT_MJoil[hour] = (wdot_CT_Wh * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
            E_used_CT_W[hour] = wdot_CT_Wh

    ########## Operation of the CCGT
    if Qh_req_from_CCGT_max_W > 0:
        # Sizing of CCGT
        GT_fuel_type = 'NG'  # assumption for scenarios in SG
        Q_GT_nom_sizing_W = Qh_req_from_CCGT_max_W  # starting guess for the size of GT
        Qh_output_CCGT_max_W = 0  # the heat output of CCGT at currently installed size (Q_GT_nom_sizing_W)
        while (Qh_output_CCGT_max_W - Qh_req_from_CCGT_max_W) <= 0:
            Q_GT_nom_sizing_W += 1000  # update GT size
            # get CCGT performance limits and functions at Q_GT_nom_sizing_W
            CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_sizing_W, ACH_T_IN_FROM_CHP,
                                                           GT_fuel_type, prices, lca.ELEC_PRICE[hour])
            Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']

        # unpack CCGT performance functions
        Q_GT_nom_W = Q_GT_nom_sizing_W * (1 + SIZING_MARGIN)  # installed CCGT capacity
        CCGT_performances = cogeneration.calc_cop_CCGT(Q_GT_nom_W, ACH_T_IN_FROM_CHP,
                                                       GT_fuel_type, prices, lca.ELEC_PRICE[hour])
        Q_used_prim_W_CCGT_fn = CCGT_performances['q_input_fn_q_output_W']
        cost_per_Wh_th_CCGT_fn = CCGT_performances['fuel_cost_per_Wh_th_fn_q_output_W']  # interpolated cost function
        Qh_output_CCGT_min_W = CCGT_performances['q_output_min_W']
        Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']
        eta_elec_interpol = CCGT_performances['eta_el_fn_q_input']

        for hour in range(HOURS_IN_YEAR):
            if Qh_req_from_CCGT_W[hour] > Qh_output_CCGT_min_W:  # operate above minimal load
                if Qh_req_from_CCGT_W[hour] < Qh_output_CCGT_max_W:  # Normal operation Possible within partload regime
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_req_from_CCGT_W[hour])
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_req_from_CCGT_W[hour])
                    Qh_from_CCGT_W[hour] = Qh_req_from_CCGT_W[hour].copy()
                    E_gen_CCGT_W[hour] = np.float(eta_elec_interpol(Q_used_prim_CCGT_W)) * Q_used_prim_CCGT_W
                else:
                    raise ValueError('Incorrect CCGT sizing!')
            else:  # operate at minimum load
                cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_output_CCGT_min_W)
                Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_output_CCGT_min_W)
                Qh_from_CCGT_W[hour] = Qh_output_CCGT_min_W
                E_gen_CCGT_W[hour] = np.float(eta_elec_interpol(Qh_output_CCGT_max_W)) * Q_used_prim_CCGT_W

            # ASSUME THAT ALL ELECTRICITY IS SOLD
            opex_var_CCGT_USDhr[hour] = (cost_per_Wh_th * Qh_from_CCGT_W[hour]) - \
                                        (E_gen_CCGT_W[hour] * lca.ELEC_PRICE[hour])
            GHG_CCGT_tonCO2[hour] = ((Q_used_prim_CCGT_W * WH_TO_J / 1E6) * lca.NG_CC_TO_CO2_STD / 1E3) - \
                                    ((E_gen_CCGT_W[hour] * WH_TO_J / 1E6) * lca.EL_TO_CO2 / 1E3)
            prim_energy_CCGT_MJoil[hour] = ((Q_used_prim_CCGT_W * WH_TO_J / 1.E6) * lca.NG_CC_TO_OIL_STD) - \
                                           ((E_gen_CCGT_W[hour] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ)
            NG_used_CCGT_W[hour] = Q_used_prim_CCGT_W

    # CAPEX AND FIXED OPEX GENERATION UNITS
    performance_costs = calc_generation_costs_cooling(E_used_Lake_W,
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
    Opex_var_Lake_connected_USD = sum(opex_var_Lake_USDhr),
    Opex_var_VCC_connected_USD = sum(opex_var_VCC_USDhr),
    Opex_var_ACH_connected_USD = sum(opex_var_ACH_USDhr),
    Opex_var_VCC_backup_connected_USD = sum(opex_var_VCC_backup_USDhr),
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
        "Q_districtcooling_sys_req_W": Q_cooling_req_W,

        # Status of each technology 1 = on, 0 = off in every hour
        "VCC_WS_Status": Lake_Status,
        "Trigen_NG_Status": ACH_Status,
        "VCC_AS_Status": VCC_Status,
        "VCC_Backup_AS_Status": VCC_Backup_Status,

        # ENERGY GENERATION
        # cooling
        "Q_VCC_WS_W": Qc_from_Lake_W,
        "Q_VCC_AS_W": Qc_from_VCC_W,
        "Q_VCC_backup_AS_W": Qc_from_VCC_backup_W,
        "Q_Trigen_NG_W": Qc_from_ACH_W,
        "Q_Storage_gen_W": Qc_from_storage_tank_W,

        # electricity
        "E_Trigen_NG_gen_W": E_gen_CCGT_W,

        # ENERGY REQUIREMENTS
        # Electricity
        "E_VCC_WS_req_W": E_used_Lake_W,
        "E_VCC_AS_req_W": E_used_VCC_W + E_used_CT_W,
        "E_VCC_backup_AS_req_W": E_used_VCC_backup_W,
        "E_Trigen_NG_req_W": E_used_ACH_W,

        # fuels
        "NG_Trigen_req_W": NG_used_CCGT_W
    }

    # PLOT RESULTS
    performance = {
        # annualized capex
        "Capex_a_VCC_WS_connected_USD": performance_costs['Capex_a_Lake_connected_USD'],
        "Capex_a_VCC_AS_connected_USD": performance_costs['Capex_a_VCC_connected_USD']+
                                        performance_costs['Capex_a_CT_connected_USD'],
        "Capex_a_VCC_backup_AS_connected_USD": performance_costs['Capex_a_VCC_backup_connected_USD'],
        "Capex_a_Trigen_NG_connected_USD": performance_costs['Capex_a_CCGT_connected_USD'] +
                                           performance_costs['Capex_a_ACH_connected_USD'],
        "Capex_a_Storage_connected_USD": performance_costs['Capex_a_Tank_connected_USD'],
        "Capex_a_DCN_connected_USD": Capex_a_DCN_USD,
        "Capex_a_SubstationsCooling_connected_USD": Capex_a_Substations_USD,

        # total capex
        "Capex_total_VCC_WS_connected_USD": performance_costs['Capex_total_Lake_connected_USD'],
        "Capex_total_VCC_AS_connected_USD": performance_costs['Capex_total_VCC_connected_USD']+
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
        "Opex_fixed_Trigen_NG_connected_USD": performance_costs['Opex_fixed_CCGT_connected_USD']+
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
                                       performance_costs['Opex_fixed_VCC_connected_USD']+
                                       Opex_var_CT_connected_USD +
                                       performance_costs['Opex_fixed_CT_connected_USD'],
        "Opex_a_Trigen_NG_connected_USD": Opex_var_ACH_connected_USD +
                                       performance_costs['Opex_fixed_ACH_connected_USD']+
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
    if master_to_slave_vars.storage_cooling_on == 1:
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
