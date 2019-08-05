# -*- coding: utf-8 -*-
"""
Extra costs to an individual

"""
from __future__ import division

import pandas as pd

import cea.technologies.boiler as boiler
import cea.technologies.cogeneration as chp
import cea.technologies.furnace as furnace
import cea.technologies.heat_exchangers as hex
import cea.technologies.heatpumps as hp
import cea.technologies.solar.photovoltaic_thermal as pvt
import cea.technologies.solar.solar_collector as stc
from cea.optimization.constants import N_PVT
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def add_disconnected_costs(column_names_buildings_heating,
                           column_names_buildings_cooling, locator, master_to_slave_vars):
    DHN_barcode = master_to_slave_vars.DHN_barcode
    DCN_barcode = master_to_slave_vars.DCN_barcode

    # DISCONNECTED BUILDINGS  - HEATING LOADS
    GHG_heating_disconnected_tonCO2, Capex_a_heating_disconnected_USD, \
    TAC_heating_disconnected_USD, Opex_a_heating_disconnected_USD, \
    PEN_heating_disconnected_MJoil, Capex_total_heating_disconnected_USD = calc_costs_emissions_decentralized_DH(
        DHN_barcode,
        column_names_buildings_heating, locator)

    # DISCONNECTED BUILDINGS - COOLING LOADS
    GHG_cooling_disconnected_tonCO2, Capex_a_cooling_disconnected_USD, \
    TAC_cooling_disconnected_USD, Opex_a_cooling_disconnected_USD, \
    PEN_cooling_disconnected_MJoil, Capex_total_cooling_disconnected_USD = calc_costs_emissions_decentralized_DC(
        DCN_barcode,
        column_names_buildings_cooling, locator)

    Capex_a_disconnected_USD = Capex_a_cooling_disconnected_USD + Capex_a_heating_disconnected_USD
    Capex_total_disconnected_USD = Capex_total_cooling_disconnected_USD + Capex_total_heating_disconnected_USD
    Opex_a_disconnected_USD = Opex_a_cooling_disconnected_USD + Opex_a_heating_disconnected_USD
    TAC_disconnected_USD = TAC_heating_disconnected_USD + TAC_cooling_disconnected_USD
    GHG_disconnected_tonCO2 = (GHG_heating_disconnected_tonCO2 + GHG_cooling_disconnected_tonCO2)
    PEN_disconnected_MJoil = PEN_heating_disconnected_MJoil + PEN_cooling_disconnected_MJoil

    performance = {
        "Capex_a_heating_disconnected_USD": Capex_a_heating_disconnected_USD,
        "Capex_total_heating_disconnected_USD": Capex_total_heating_disconnected_USD,
        "Opex_a_heating_disconnected_USD": Opex_a_heating_disconnected_USD,
        "TAC_heating_disconnected_USD": TAC_heating_disconnected_USD,
        "GHG_heating_disconnected_tonCO2": GHG_heating_disconnected_tonCO2,
        "PEN_heating_disconnected_MJoil": PEN_heating_disconnected_MJoil,
        "Capex_a_cooling_disconnected_USD": Capex_a_cooling_disconnected_USD,
        "Capex_total_cooling_disconnected_USD": Capex_total_cooling_disconnected_USD,
        "Opex_a_cooling_disconnected_USD": Opex_a_cooling_disconnected_USD,
        "TAC_cooling_disconnected_USD": TAC_cooling_disconnected_USD,
        "GHG_cooling_disconnected_tonCO2": GHG_cooling_disconnected_tonCO2,
        "PEN_cooling_disconnected_MJoil": PEN_cooling_disconnected_MJoil,
        "Capex_a_disconnected_USD": Capex_a_disconnected_USD,
        "Capex_total_disconnected_USD": Capex_total_disconnected_USD,
        "Opex_a_disconnected_USD": Opex_a_disconnected_USD,
        "TAC_disconnected_USD": TAC_disconnected_USD,
        "GHG_disconnected_tonCO2": GHG_disconnected_tonCO2,
        "PEN_disconnected_MJoil": PEN_disconnected_MJoil}

    return performance


def calc_generation_costs_heating(locator,
                                  master_to_slave_vars,
                                  Q_uncovered_design_W,
                                  config,
                                  storage_activation_data,
                                  solar_features,
                                  heating_dispatch,
                                  ):
    """
    Computes costs / GHG emisions / primary energy needs
    for the individual
    addCosts = additional costs
    addCO2 = GHG emissions
    addPrm = primary energy needs
    :param DHN_barcode: parameter indicating if the building is connected or not
    :param buildList: list of buildings in the district
    :param locator: input locator set to scenario
    :param master_to_slave_vars: class containing the features of a specific individual
    :param Q_uncovered_design_W: hourly max of the heating uncovered demand
    :param Q_uncovered_annual_W: total heating uncovered
    :param solar_features: solar features
    :param thermal_network: network features
    :param gv: global variables
    :type indCombi: string
    :type buildList: list
    :type locator: string
    :type master_to_slave_vars: class
    :type Q_uncovered_design_W: float
    :type Q_uncovered_annual_W: float
    :type solar_features: class
    :type thermal_network: class
    :type gv: class

    :return: returns the objectives addCosts, addCO2, addPrim
    :rtype: tuple
    """

    thermal_network = pd.read_csv(
        locator.get_thermal_network_data_folder(master_to_slave_vars.network_data_file_heating))

    # START VVALUES
    Capex_a_HEX_SC_ET_USD = 0.0
    Capex_a_HEX_SC_FP_USD = 0.0
    Capex_a_HEX_PVT_USD = 0.0
    Capex_a_wasteserver_HP_USD = 0.0
    Capex_a_wasteserver_HEX_USD = 0.0
    Capex_a_Sewage_USD = 0.0
    Capex_a_Lake_USD = 0.0
    Capex_a_GHP_USD = 0.0
    Capex_a_CHP_BG_USD = 0.0
    Capex_a_CHP_NG_USD = 0.0
    Capex_a_furnace_wet_USD = 0.0
    Capex_a_furnace_dry_USD = 0.0
    Capex_a_BaseBoiler_BG_USD = 0.0
    Capex_a_BaseBoiler_NG_USD = 0.0
    Capex_a_PeakBoiler_BG_USD = 0.0
    Capex_a_PeakBoiler_NG_USD = 0.0
    Capex_a_BackupBoiler_BG_USD = 0.0
    Capex_a_BackupBoiler_NG_USD = 0.0
    Capex_HEX_SC_ET_USD = 0.0
    Capex_HEX_SC_FP_USD = 0.0
    Capex_HEX_PVT_USD = 0.0
    Capex_wasteserver_HEX_USD = 0.0
    Capex_wasteserver_HP_USD = 0.0
    Capex_Sewage_USD = 0.0
    Capex_Lake_USD = 0.0
    Capex_GHP_USD = 0.0
    Capex_CHP_BG_USD = 0.0
    Capex_CHP_NG_USD = 0.0
    Capex_furnace_wet_USD = 0.0
    Capex_furnace_dry_USD = 0.0
    Capex_BaseBoiler_BG_USD = 0.0
    Capex_BaseBoiler_NG_USD = 0.0
    Capex_PeakBoiler_BG_USD = 0.0
    Capex_PeakBoiler_NG_USD = 0.0
    Capex_BackupBoiler_BG_USD = 0.0
    Capex_BackupBoiler_NG_USD = 0.0
    Opex_fixed_wasteserver_HP_USD = 0.0
    Opex_fixed_wasteserver_HEX_USD = 0.0
    Opex_fixed_Sewage_USD = 0.0
    Opex_fixed_Lake_USD = 0.0
    Opex_fixed_GHP_USD = 0.0
    Opex_fixed_CHP_BG_USD = 0.0
    Opex_fixed_CHP_NG_USD = 0.0
    Opex_fixed_furnace_wet_USD = 0.0
    Opex_fixed_furnace_dry_USD = 0.0
    Opex_fixed_BaseBoiler_BG_USD = 0.0
    Opex_fixed_BaseBoiler_NG_USD = 0.0
    Opex_fixed_PeakBoiler_BG_USD = 0.0
    Opex_fixed_PeakBoiler_NG_USD = 0.0
    Opex_fixed_BackupBoiler_BG_USD = 0.0
    Opex_fixed_BackupBoiler_NG_USD = 0.0

    # FURNACE
    if master_to_slave_vars.Furnace_on == 1:
        P_design_W = heating_dispatch['E_Furnace_gen_W'].max()
        Q_annual_W = heating_dispatch["Q_Furnace_gen_directload_W"].sum()
        Capex_a_furnace_USD, Opex_fixed_furnace_USD, Capex_furnace_USD = furnace.calc_Cinv_furnace(P_design_W,
                                                                                                   Q_annual_W,
                                                                                                   config, locator,
                                                                                                   'FU1')
        if master_to_slave_vars.Furn_Moist_type == "wet":
            Capex_furnace_wet_USD = Capex_furnace_USD
            Capex_a_furnace_wet_USD = Capex_a_furnace_USD
            Opex_fixed_furnace_wet_USD = Opex_fixed_furnace_USD
            Capex_furnace_dry_USD = 0.0
            Capex_a_furnace_dry_USD = 0.0
            Opex_fixed_furnace_dry_USD = 0.0
        elif master_to_slave_vars.Furn_Moist_type == "dry":
            Capex_furnace_dry_USD = Capex_furnace_USD
            Capex_a_furnace_dry_USD = Capex_a_furnace_USD
            Opex_fixed_furnace_dry_USD = Opex_fixed_furnace_USD
            Capex_furnace_wet_USD = 0.0
            Capex_a_furnace_wet_USD = 0.0
            Opex_fixed_furnace_wet_USD = 0.0

    # CCGT
    if master_to_slave_vars.CC_on == 1:
        CC_size_W = master_to_slave_vars.CC_GT_SIZE_W
        Capex_a_CHP_USD, Opex_fixed_CHP_USD, Capex_CHP_USD = chp.calc_Cinv_CCGT(CC_size_W, locator, config)
        if master_to_slave_vars.gt_fuel == "BG":
            Capex_a_CHP_BG_USD = Capex_a_CHP_USD
            Opex_fixed_CHP_BG_USD = Opex_fixed_CHP_USD
            Capex_CHP_BG_USD = Capex_CHP_USD
            Capex_a_CHP_NG_USD = 0.0
            Opex_fixed_CHP_NG_USD = 0.0
            Capex_CHP_NG_USD = 0.0
        elif master_to_slave_vars.gt_fuel == "NG":
            Capex_a_CHP_BG_USD = 0.0
            Opex_fixed_CHP_BG_USD = 0.0
            Capex_CHP_BG_USD = 0.0
            Capex_a_CHP_NG_USD = Capex_a_CHP_USD
            Opex_fixed_CHP_NG_USD = Opex_fixed_CHP_USD
            Capex_CHP_NG_USD = Capex_CHP_USD

        # BOILER BASE LOAD
    if master_to_slave_vars.Boiler_on == 1:
        Q_design_W = master_to_slave_vars.Boiler_Q_max_W
        Capex_a_Boiler_USD, Opex_fixed_Boiler_USD, Capex_Boiler_USD = boiler.calc_Cinv_boiler(Q_design_W, locator,
                                                                                              config, 'BO1')
        if master_to_slave_vars.gt_fuel == "BG":
            Capex_a_BaseBoiler_BG_USD = Capex_a_Boiler_USD
            Opex_fixed_BaseBoiler_BG_USD = Opex_fixed_Boiler_USD
            Capex_BaseBoiler_BG_USD = Capex_Boiler_USD
            Capex_a_BaseBoiler_NG_USD = 0.0
            Opex_fixed_BaseBoiler_NG_USD = 0.0
            Capex_BaseBoiler_NG_USD = 0.0
        elif master_to_slave_vars.gt_fuel == "NG":
            Capex_a_BaseBoiler_BG_USD = 0.0
            Opex_fixed_BaseBoiler_BG_USD = 0.0
            Capex_BaseBoiler_BG_USD = 00.0
            Capex_a_BaseBoiler_NG_USD = Capex_a_Boiler_USD
            Opex_fixed_BaseBoiler_NG_USD = Opex_fixed_Boiler_USD
            Capex_BaseBoiler_NG_USD = Capex_a_Boiler_USD

    # BOILER PEAK LOAD
    if master_to_slave_vars.BoilerPeak_on == 1:
        Q_design_W = master_to_slave_vars.BoilerPeak_Q_max_W
        Capex_a_Boiler_peak_USD, Opex_fixed_Boiler_peak_USD, Capex_Boiler_peak_USD = boiler.calc_Cinv_boiler(
            Q_design_W, locator, config, 'BO1')

        if master_to_slave_vars.gt_fuel == "BG":
            Capex_a_PeakBoiler_BG_USD = Capex_a_Boiler_peak_USD
            Opex_fixed_PeakBoiler_BG_USD = Opex_fixed_Boiler_peak_USD
            Capex_PeakBoiler_BG_USD = Capex_Boiler_peak_USD
            Capex_a_PeakBoiler_NG_USD = 0.0
            Opex_fixed_PeakBoiler_NG_USD = 0.0
            Capex_PeakBoiler_NG_USD = 0.0
        elif master_to_slave_vars.gt_fuel == "NG":
            Capex_a_PeakBoiler_BG_USD = Capex_a_Boiler_peak_USD
            Opex_fixed_PeakBoiler_BG_USD = Opex_fixed_Boiler_peak_USD
            Capex_PeakBoiler_BG_USD = Capex_Boiler_peak_USD
            Capex_a_PeakBoiler_NG_USD = Capex_a_Boiler_peak_USD
            Opex_fixed_PeakBoiler_NG_USD = Opex_fixed_Boiler_peak_USD
            Capex_PeakBoiler_NG_USD = Capex_Boiler_peak_USD

    # HEATPUMP LAKE
    if master_to_slave_vars.HP_Lake_on == 1:
        HP_Size_W = heating_dispatch['Q_HP_Lake_gen_directload_W'].max()
        Capex_a_Lake_USD, Opex_fixed_Lake_USD, Capex_Lake_USD = hp.calc_Cinv_HP(HP_Size_W, locator, config, 'HP2')

    # HEATPUMP_SEWAGE
    if master_to_slave_vars.HP_Sew_on == 1:
        HP_Size_W = heating_dispatch['Q_HP_Sew_gen_directload_W'].max()
        Capex_a_Sewage_USD, Opex_fixed_Sewage_USD, Capex_Sewage_USD = hp.calc_Cinv_HP(HP_Size_W, locator, config,
                                                                                      'HP2')

    # GROUND HEAT PUMP
    if master_to_slave_vars.GHP_on == 1:
        GHP_Enom_W = heating_dispatch['Q_GHP_gen_directload_W'].max()
        Capex_a_GHP_USD, Opex_fixed_GHP_USD, Capex_GHP_USD = hp.calc_Cinv_GHP(GHP_Enom_W, locator, config)

    # BACK-UP BOILER
    Capex_a_Boiler_backup_USD, Opex_fixed_Boiler_backup_USD, Capex_Boiler_backup_USD = boiler.calc_Cinv_boiler(
        Q_uncovered_design_W, locator, config, 'BO1')

    master_to_slave_vars.BoilerBackup_Q_max_W = Q_uncovered_design_W

    if master_to_slave_vars.gt_fuel == "BG":
        Capex_a_BackupBoiler_BG_USD = Capex_a_Boiler_backup_USD
        Opex_fixed_BackupBoiler_BG_USD = Opex_fixed_Boiler_backup_USD
        Capex_BackupBoiler_BG_USD = Capex_Boiler_backup_USD
        Capex_a_BackupBoiler_NG_USD = 0.0
        Opex_fixed_BackupBoiler_NG_USD = 0.0
        Capex_BackupBoiler_NG_USD = 0.0
    elif master_to_slave_vars.gt_fuel == "NG":
        Capex_a_BackupBoiler_BG_USD = 0.0
        Opex_fixed_BackupBoiler_BG_USD = 0.0
        Capex_BackupBoiler_BG_USD = 0.0
        Capex_a_BackupBoiler_NG_USD = Capex_a_Boiler_backup_USD
        Opex_fixed_BackupBoiler_NG_USD = Opex_fixed_Boiler_backup_USD
        Capex_BackupBoiler_NG_USD = Capex_a_Boiler_backup_USD

    # HEATPUMP AND HEX FOR HEAT RECOVERY (DATA CENTRE)
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        Q_HEX_max_Wh = thermal_network["Qcdata_netw_total_kWh"].max() * 1000  # convert to Wh
        Capex_a_wasteserver_HEX_USD, Opex_fixed_wasteserver_HEX_USD, Capex_wasteserver_HEX_USD = hex.calc_Cinv_HEX(
            Q_HEX_max_Wh, locator, config, 'HEX1')

        Q_HP_max_Wh = storage_activation_data["Q_HP_Server_W"].max()
        Capex_a_wasteserver_HP_USD, Opex_fixed_wasteserver_HP_USD, Capex_wasteserver_HP_USD = hp.calc_Cinv_HP(
            Q_HP_max_Wh, locator, config, 'HP2')

    # SOLAR TECHNOLOGIES
    # ADD COSTS AND EMISSIONS DUE TO SOLAR TECHNOLOGIES
    SC_ET_area_m2 = master_to_slave_vars.SOLAR_PART_SC_ET * solar_features.A_SC_ET_m2
    Capex_a_SC_ET_USD, Opex_fixed_SC_ET_USD, Capex_SC_ET_USD = stc.calc_Cinv_SC(SC_ET_area_m2, locator,
                                                                                'ET')

    SC_FP_area_m2 = master_to_slave_vars.SOLAR_PART_SC_FP * solar_features.A_SC_FP_m2
    Capex_a_SC_FP_USD, Opex_fixed_SC_FP_USD, Capex_SC_FP_USD = stc.calc_Cinv_SC(SC_FP_area_m2, locator,
                                                                                'FP')

    PVT_peak_kW = master_to_slave_vars.SOLAR_PART_PVT * solar_features.A_PVT_m2 * N_PVT  # kW
    Capex_a_PVT_USD, Opex_fixed_PVT_USD, Capex_PVT_USD = pvt.calc_Cinv_PVT(PVT_peak_kW, locator, config)

    # HEATPUMP FOR SOLAR UPGRADE TO DISTRICT HEATING
    Q_HP_max_PVT_wh = storage_activation_data["Q_HP_PVT_W"].max()
    Capex_a_HP_PVT_USD, Opex_fixed_HP_PVT_USD, Capex_HP_PVT_USD = hp.calc_Cinv_HP(Q_HP_max_PVT_wh, locator, config,
                                                                                  'HP2')
    # hack split into two technologies
    Q_HP_max_SC_ET_Wh = storage_activation_data["Q_HP_SC_ET_W"].max()
    Capex_a_HP_SC_ET_USD, Opex_fixed_HP_SC_ET_USD, Capex_HP_SC_ET_USD = hp.calc_Cinv_HP(Q_HP_max_SC_ET_Wh, locator,
                                                                                        config,
                                                                                        'HP2')
    Q_HP_max_SC_FP_Wh = storage_activation_data["Q_HP_SC_FP_W"].max()
    Capex_a_HP_SC_FP_USD, Opex_fixed_HP_SC_FP_USD, Capex_HP_SC_FP_USD = hp.calc_Cinv_HP(Q_HP_max_SC_FP_Wh, locator,
                                                                                        config,
                                                                                        'HP2')

    # HEAT EXCHANGER FOR SOLAR COLLECTORS
    Q_max_SC_ET_Wh = (storage_activation_data["Q_SC_ET_gen_directload_W"] + storage_activation_data[
        "Q_SC_ET_gen_storage_W"]).max()
    Capex_a_HEX_SC_ET_USD, Opex_fixed_HEX_SC_ET_USD, Capex_HEX_SC_ET_USD = hex.calc_Cinv_HEX(Q_max_SC_ET_Wh,
                                                                                             locator,
                                                                                             config, 'HEX1')

    Q_max_SC_FP_Wh = (storage_activation_data["Q_SC_FP_gen_directload_W"] + storage_activation_data[
        "Q_SC_FP_gen_storage_W"]).max()
    Capex_a_HEX_SC_FP_USD, Opex_fixed_HEX_SC_FP_USD, Capex_HEX_SC_FP_USD = hex.calc_Cinv_HEX(Q_max_SC_FP_Wh,
                                                                                             locator,
                                                                                             config, 'HEX1')

    Q_max_PVT_Wh = (storage_activation_data["Q_PVT_gen_directload_W"] + storage_activation_data[
        "Q_PVT_gen_storage_W"]).max()
    Capex_a_HEX_PVT_USD, Opex_fixed_HEX_PVT_USD, Capex_HEX_PVT_USD = hex.calc_Cinv_HEX(Q_max_PVT_Wh,
                                                                                       locator, config,
                                                                                       'HEX1')

    performance_costs = {
        # annualized capex
        "Capex_a_SC_ET_connected_USD": Capex_a_SC_ET_USD + Capex_a_HP_SC_ET_USD + Capex_a_HEX_SC_ET_USD,
        "Capex_a_SC_FP_connected_USD": Capex_a_SC_FP_USD + Capex_a_HP_SC_FP_USD + Capex_a_HEX_SC_FP_USD,
        "Capex_a_PVT_connected_USD": Capex_a_PVT_USD + Capex_a_HP_PVT_USD + Capex_a_HEX_PVT_USD,
        "Capex_a_HP_Server_connected_USD": Capex_a_wasteserver_HP_USD + Capex_a_wasteserver_HEX_USD,
        "Capex_a_HP_Sewage_connected_USD": Capex_a_Sewage_USD,
        "Capex_a_HP_Lake_connected_USD": Capex_a_Lake_USD,
        "Capex_a_GHP_connected_USD": Capex_a_GHP_USD,
        "Capex_a_CHP_BG_connected_USD": Capex_a_CHP_BG_USD,
        "Capex_a_CHP_NG_connected_USD": Capex_a_CHP_NG_USD,
        "Capex_a_Furnace_wet_connected_USD": Capex_a_furnace_wet_USD,
        "Capex_a_Furnace_dry_connected_USD": Capex_a_furnace_dry_USD,
        "Capex_a_BaseBoiler_BG_connected_USD": Capex_a_BaseBoiler_BG_USD,
        "Capex_a_BaseBoiler_NG_connected_USD": Capex_a_BaseBoiler_NG_USD,
        "Capex_a_PeakBoiler_BG_connected_USD": Capex_a_PeakBoiler_BG_USD,
        "Capex_a_PeakBoiler_NG_connected_USD": Capex_a_PeakBoiler_NG_USD,
        "Capex_a_BackupBoiler_BG_connected_USD": Capex_a_BackupBoiler_BG_USD,
        "Capex_a_BackupBoiler_NG_connected_USD": Capex_a_BackupBoiler_NG_USD,

        # total_capex
        "Capex_total_SC_ET_connected_USD": Capex_SC_ET_USD + Capex_HP_SC_ET_USD + Capex_HEX_SC_ET_USD,
        "Capex_total_SC_FP_connected_USD": Capex_SC_FP_USD + Capex_HP_SC_FP_USD + Capex_HEX_SC_FP_USD,
        "Capex_total_PVT_connected_USD": Capex_PVT_USD + Capex_HP_PVT_USD + Capex_HEX_PVT_USD,
        "Capex_total_HP_Server_connected_USD": Capex_wasteserver_HP_USD + Capex_wasteserver_HEX_USD,
        "Capex_total_HP_Sewage_connected_USD": Capex_Sewage_USD,
        "Capex_total_HP_Lake_connected_USD": Capex_Lake_USD,
        "Capex_total_GHP_connected_USD": Capex_GHP_USD,
        "Capex_total_CHP_BG_connected_USD": Capex_CHP_BG_USD,
        "Capex_total_CHP_NG_connected_USD": Capex_CHP_NG_USD,
        "Capex_total_Furnace_wet_connected_USD": Capex_furnace_wet_USD,
        "Capex_total_Furnace_dry_connected_USD": Capex_furnace_dry_USD,
        "Capex_total_BaseBoiler_BG_connected_USD": Capex_BaseBoiler_BG_USD,
        "Capex_total_BaseBoiler_NG_connected_USD": Capex_BaseBoiler_NG_USD,
        "Capex_total_PeakBoiler_BG_connected_USD": Capex_PeakBoiler_BG_USD,
        "Capex_total_PeakBoiler_NG_connected_USD": Capex_PeakBoiler_NG_USD,
        "Capex_total_BackupBoiler_BG_connected_USD": Capex_BackupBoiler_BG_USD,
        "Capex_total_BackupBoiler_NG_connected_USD": Capex_BackupBoiler_NG_USD,

        # opex fixed costs
        "Opex_fixed_SC_ET_connected_USD": Opex_fixed_SC_ET_USD,
        "Opex_fixed_SC_FP_connected_USD": Opex_fixed_SC_FP_USD,
        "Opex_fixed_PVT_connected_USD": Opex_fixed_PVT_USD,
        "Opex_fixed_HP_Server_connected_USD": Opex_fixed_wasteserver_HP_USD + Opex_fixed_wasteserver_HEX_USD,
        "Opex_fixed_HP_Sewage_connected_USD": Opex_fixed_Sewage_USD,
        "Opex_fixed_HP_Lake_connected_USD": Opex_fixed_Lake_USD,
        "Opex_fixed_GHP_connected_USD": Opex_fixed_GHP_USD,
        "Opex_fixed_CHP_BG_connected_USD": Opex_fixed_CHP_BG_USD,
        "Opex_fixed_CHP_NG_connected_USD": Opex_fixed_CHP_NG_USD,
        "Opex_fixed_Furnace_wet_connected_USD": Opex_fixed_furnace_wet_USD,
        "Opex_fixed_Furnace_dry_connected_USD": Opex_fixed_furnace_dry_USD,
        "Opex_fixed_BaseBoiler_BG_connected_USD": Opex_fixed_BaseBoiler_BG_USD,
        "Opex_fixed_BaseBoiler_NG_connected_USD": Opex_fixed_BaseBoiler_NG_USD,
        "Opex_fixed_PeakBoiler_BG_connected_USD": Opex_fixed_PeakBoiler_BG_USD,
        "Opex_fixed_PeakBoiler_NG_connected_USD": Opex_fixed_PeakBoiler_NG_USD,
        "Opex_fixed_BackupBoiler_BG_connected_USD": Opex_fixed_BackupBoiler_BG_USD,
        "Opex_fixed_BackupBoiler_NG_connected_USD": Opex_fixed_BackupBoiler_NG_USD
    }

    return performance_costs


def calc_costs_emissions_decentralized_DC(DCN_barcode, buildings_names_with_cooling_load, locator,
                                          ):
    CO2DiscBuild = 0.0
    Capex_Disconnected = 0.0
    CostDiscBuild = 0.0
    Opex_Disconnected = 0.0
    PrimDiscBuild = 0.0
    Capex_total_Disconnected = 0.0
    total_demand = pd.read_csv(locator.get_total_demand())
    for (index, building_name) in zip(DCN_barcode, buildings_names_with_cooling_load):
        if index == "0":  # choose the best decentralized configuration
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_name, configuration='AHU_ARU_SCU'))
            dfBest = df[df["Best configuration"] == 1]
            CostDiscBuild += dfBest["TAC_USD"].iloc[0]  # [CHF]
            CO2DiscBuild += dfBest["GHG_tonCO2"].iloc[0]  # [ton CO2]
            PrimDiscBuild += dfBest["PEN_MJoil"].iloc[0]  # [MJ-oil-eq]
            Capex_Disconnected += dfBest["Capex_a_USD"].iloc[0]
            Capex_total_Disconnected += dfBest["Capex_total_USD"].iloc[0]
            Opex_Disconnected += dfBest["Opex_a_USD"].iloc[0]
    return CO2DiscBuild, Capex_Disconnected, CostDiscBuild, Opex_Disconnected, PrimDiscBuild, Capex_total_Disconnected


def calc_costs_emissions_decentralized_DH(DHN_barcode, buildings_names_with_heating_load, locator):
    CO2DiscBuild = 0.0
    Capex_Disconnected = 0.0
    CostDiscBuild = 0.0
    Opex_Disconnected = 0.0
    PrimDiscBuild = 0.0
    Capex_total_Disconnected = 0.0
    for (index, building_name) in zip(DHN_barcode, buildings_names_with_heating_load):
        if index == "0":
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_heating(building_name))
            dfBest = df[df["Best configuration"] == 1]
            CostDiscBuild += dfBest["TAC_USD"].iloc[0]  # [USD]
            CO2DiscBuild += dfBest["GHG_tonCO2"].iloc[0]  # [ton CO2]
            PrimDiscBuild += dfBest["PEN_MJoil"].iloc[0]  # [MJ-oil-eq]
            Capex_total_Disconnected += dfBest["Capex_total_USD"].iloc[0]
            Capex_Disconnected += dfBest["Capex_a_USD"].iloc[0]
            Opex_Disconnected += dfBest["Opex_a_USD"].iloc[0]
    return CO2DiscBuild, Capex_Disconnected, CostDiscBuild, Opex_Disconnected, PrimDiscBuild, Capex_total_Disconnected
