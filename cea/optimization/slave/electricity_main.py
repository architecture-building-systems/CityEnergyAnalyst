"""
Electricity imports and exports script

This file takes in the values of the electricity activation pattern (which is only considering buildings present in
network and corresponding district energy systems) and adds in the electricity requirement of decentralized buildings
and recalculates the imports from grid and exports to the grid
"""
from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR
from cea.constants import WH_TO_J

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def electricity_calculations_of_all_buildings(DHN_barcode, DCN_barcode, locator, master_to_slave_vars, lca):
    # local variables
    building_names = master_to_slave_vars.building_names
    storage_activation_data = pd.read_csv(
        locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                              master_to_slave_vars.generation_number))
    heating_activation_data = pd.read_csv(
        locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number))
    cooling_activation_data = pd.read_csv(
        locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number))

    cooling_performance = pd.read_csv(
        locator.get_optimization_slave_cooling_performance(master_to_slave_vars.individual_number,
                                                           master_to_slave_vars.generation_number))

    heating_performance = pd.read_csv(
        locator.get_optimization_slave_cooling_performance(master_to_slave_vars.individual_number,
                                                           master_to_slave_vars.generation_number))
    date = storage_activation_data.DATE.values

    # GET ENERGY GENERATION
    E_CHP_gen_W, \
    E_Furnace_gen_W, \
    E_CCGT_gen_W, \
    E_PV_gen_W, \
    E_PVT_gen_W, \
    E_sys_gen_W = calc_district_system_electricity_generated(cooling_activation_data,
                                                                         heating_activation_data,
                                                                         storage_activation_data)

    # GET ENERGY REQUIREMENTS
    E_sys_req_W = calc_district_system_electricity_requirements(DCN_barcode, DHN_barcode,
                                                                                    building_names,
                                                                                    cooling_activation_data,
                                                                                    heating_activation_data, locator,
                                                                                    storage_activation_data)



    #GET ACTIVATION CURVE
    activation_curve_variables = electricity_activation_curve(E_CCGT_gen_W, E_CHP_gen_W, E_Furnace_gen_W, E_PVT_gen_W,
                                                       E_PV_gen_W, E_sys_req_W, master_to_slave_vars, locator, date)

    E_CHP_gen_directload_W = activation_curve_variables['E_CHP_gen_directload_W']
    E_CHP_gen_export_W = activation_curve_variables['E_CHP_gen_export_W']
    E_CCGT_gen_directload_W = activation_curve_variables['E_CCGT_gen_directload_W']
    E_CCGT_gen_export_W = activation_curve_variables['E_CCGT_gen_export_W']
    E_Furnace_gen_directload_W = activation_curve_variables['E_Furnace_gen_directload_W']
    E_Furnace_gen_export_W = activation_curve_variables['E_Furnace_gen_export_W']
    E_GRID_directload_W = activation_curve_variables['E_GRID_directload_W']


    #PARAMETERS TO CHANGE COSTS AND EMISSIONS (NET)
    # CCGT for cooling
    cooling_performance['Opex_var_CCGT_connected_USD']
    cooling_performance['Opex_a_CCGT_connected_USD']

    cooling_performance['GHG_CCGT_connected_tonCO2']
    cooling_performance['PEN_CCGT_connected_MJoil']

    # System totals
    cooling_performance['GHG_Cooling_sys_connected_tonCO2']
    cooling_performance['PEN_Cooling_sys_connected_MJoil']

    # CHP for heating
    fuel = master_to_slave_vars.gt_fuel
    type = master_to_slave_vars.Furn_Moist_type
    heating_performance['Opex_var_CHP_'+fuel+'_connected_USD']
    heating_performance['Opex_a_CHP_'+fuel+'_connected_USD']
    heating_performance['GHG_CHP_'+fuel+'_connected_tonCO2']
    heating_performance['PEN_CHP_'+fuel+'_connected_MJoil']

    heating_performance['Opex_var_Furnace_'+type+'_connected_USD']
    heating_performance['Opex_a_Furnace_'+type+'_connected_USD']
    heating_performance['GHG_Furnace_'+type+'_connected_tonCO2']
    heating_performance['PEN_Furnace_'+type+'_connected_MJoil']

    heating_performance['GHG_Cooling_sys_connected_tonCO2']
    heating_performance['PEN_Cooling_sys_connected_MJoil']



    #calculate emissions of generation units BUT solar (the last will be calculated in the next STEP)



    PEN_from_heat_used_SC_and_PVT_MJoil = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_OIL * WH_TO_J / 1.0E6
    PEN_saved_from_electricity_sold_CHP_MJoil = E_from_CHP_W * (- lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
    PEN_saved_from_electricity_sold_Solar_MJoil = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (
            lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
    PEN_HPSolarandHeatRecovery_MJoil = E_aux_solar_and_heat_recovery_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
    PEN_Lake_MJoil = E_used_Lake_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
    PEN_VCC_MJoil = E_used_VCC_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
    PEN_VCC_backup_MJoil = E_used_VCC_backup_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
    PEN_ACH_MJoil = E_used_ACH_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
    PEN_CT_MJoil = E_used_CT_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6

    GHG_from_heat_used_SC_and_PVT_tonCO2 = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_CO2 * WH_TO_J / 1.0E6
    GHG_saved_from_electricity_sold_CHP_tonCO2 = E_from_CHP_W * (- lca.EL_TO_CO2) * WH_TO_J / 1.0E6
    GHG_saved_from_electricity_sold_Solar_tonCO2 = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (
            lca.EL_PV_TO_CO2 - lca.EL_TO_CO2) * WH_TO_J / 1.0E6
    GHG_HPSolarandHeatRecovery_tonCO2 = E_aux_solar_and_heat_recovery_W * lca.EL_TO_CO2 * WH_TO_J / 1E6
    GHG_Lake_MJoil = E_used_Lake_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
    GHG_VCC_MJoil = E_used_VCC_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
    GHG_VCC_backup_MJoil = E_used_VCC_backup_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
    GHG_ACH_MJoil = E_used_ACH_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
    GHG_CT_MJoil = E_used_CT_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6


    results = pd.DataFrame({"DATE": date,
                            "E_total_req_W": total_electricity_demand_W,
                            "E_used_Lake_W": E_used_Lake_W,
                            "E_used_VCC_W": E_used_VCC_W,
                            "E_used_VCC_backup_W": E_used_VCC_backup_W,
                            "E_used_ACH_W": E_used_ACH_W,
                            "E_used_CT_W": E_used_CT_W,
                            "E_from_CHP_W": E_from_CHP_W,
                            "E_from_PV_W": E_from_PV_W,
                            "E_from_PVT_W": E_from_PVT_W,
                            "E_CHP_directload_W": E_CHP_directload_W,
                            "E_CHP_grid_W": E_CHP_grid_W,
                            "E_PV_directload_W": E_PV_directload_W,
                            "E_PV_grid_W": E_PV_grid_W,
                            "E_PVT_directload_W": E_PVT_directload_W,
                            "E_PVT_grid_W": E_PVT_grid_W,
                            "E_GRID_directload_W": E_GRID_directload_W,
                            "E_appliances_total_W": E_appliances_total_W,
                            "E_data_center_total_W": E_data_center_total_W,
                            "E_industrial_processes_total_W": E_industrial_processes_total_W,
                            "E_auxiliary_units_total_W": E_auxiliary_units_total_W,
                            "E_hotwater_total_W": E_hotwater_total_W,
                            "E_space_heating_total_W": E_space_heating_total_W,
                            "E_space_cooling_total_W": E_space_cooling_total_W,
                            "E_total_to_grid_W_negative": - E_PV_grid_W - E_CHP_grid_W - E_PVT_grid_W,
                            "PEN_from_heat_used_SC_and_PVT_MJoil": PEN_from_heat_used_SC_and_PVT_MJoil,
                            "PEN_saved_from_electricity_sold_CHP_MJoil": PEN_saved_from_electricity_sold_CHP_MJoil,
                            "PEN_saved_from_electricity_sold_Solar_MJoil": PEN_saved_from_electricity_sold_Solar_MJoil,
                            "PEN_HPSolarandHeatRecovery_MJoil": PEN_HPSolarandHeatRecovery_MJoil,
                            "PEN_Lake_MJoil": PEN_Lake_MJoil,
                            "PEN_VCC_MJoil": PEN_VCC_MJoil,
                            "PEN_VCC_backup_MJoil": PEN_VCC_backup_MJoil,
                            "PEN_ACH_MJoil": PEN_ACH_MJoil,
                            "PEN_CT_MJoil": PEN_CT_MJoil,
                            "GHG_from_heat_used_SC_and_PVT_tonCO2": GHG_from_heat_used_SC_and_PVT_tonCO2,
                            "GHG_saved_from_electricity_sold_CHP_tonCO2": GHG_saved_from_electricity_sold_CHP_tonCO2,
                            "GHG_saved_from_electricity_sold_Solar_tonCO2": GHG_saved_from_electricity_sold_Solar_tonCO2,
                            "GHG_HPSolarandHeatRecovery_tonCO2": GHG_HPSolarandHeatRecovery_tonCO2,
                            "GHG_Lake_MJoil": GHG_Lake_MJoil,
                            "GHG_VCC_backup_MJoil": GHG_VCC_backup_MJoil,
                            "GHG_ACH_MJoil": GHG_ACH_MJoil,
                            "GHG_CT_MJoil": GHG_CT_MJoil
                            })  # let's keep this negative so it is something exported, we can use it in the graphs of likelihood

    results.to_csv(
        locator.get_optimization_slave_electricity_activation_pattern_cooling(
            master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)

    GHG_electricity_tonCO2 += np.sum(GHG_from_heat_used_SC_and_PVT_tonCO2) + np.sum(
        GHG_saved_from_electricity_sold_CHP_tonCO2) + np.sum(GHG_saved_from_electricity_sold_Solar_tonCO2) + np.sum(
        GHG_HPSolarandHeatRecovery_tonCO2) + np.sum(GHG_Lake_MJoil) + np.sum(GHG_VCC_MJoil) + np.sum(
        GHG_VCC_backup_MJoil) + np.sum(GHG_ACH_MJoil) + np.sum(GHG_CT_MJoil)

    PEN_electricity_MJoil += np.sum(PEN_from_heat_used_SC_and_PVT_MJoil) + np.sum(
        PEN_saved_from_electricity_sold_CHP_MJoil) + np.sum(PEN_saved_from_electricity_sold_Solar_MJoil) + np.sum(
        PEN_HPSolarandHeatRecovery_MJoil) + np.sum(PEN_Lake_MJoil) + np.sum(PEN_VCC_MJoil) + np.sum(
        PEN_VCC_backup_MJoil) + np.sum(PEN_ACH_MJoil) + np.sum(PEN_CT_MJoil)

    for hour in range(len(total_electricity_demand_W)):
        costs_electricity_USD += total_electricity_demand_W[hour] * lca.ELEC_PRICE[hour] - (
                E_from_CHP_W[hour] + E_from_PV_W[hour] + E_from_PVT_W[hour]) * lca.ELEC_PRICE[hour]

    return


def electricity_activation_curve(E_CCGT_gen_W, E_CHP_gen_W, E_Furnace_gen_W, E_PVT_gen_W, E_PV_gen_W, E_sys_req_W,
                                 master_to_slave_vars, locator, date):
    # ACTIVATION PATTERN OF ELECTRICITY
    E_CHP_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    E_CHP_gen_export_W = np.zeros(HOURS_IN_YEAR)
    E_CCGT_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    E_CCGT_gen_export_W = np.zeros(HOURS_IN_YEAR)
    E_Furnace_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    E_Furnace_gen_export_W = np.zeros(HOURS_IN_YEAR)
    E_PV_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    E_PV_gen_export_W = np.zeros(HOURS_IN_YEAR)
    E_PVT_gen_directload_W = np.zeros(HOURS_IN_YEAR)
    E_PVT_gen_export_W = np.zeros(HOURS_IN_YEAR)
    E_GRID_directload_W = np.zeros(HOURS_IN_YEAR)
    for hour in range(HOURS_IN_YEAR):
        E_req_hour_W = E_sys_req_W[hour]

        # CHP
        if E_req_hour_W > 0.0:
            delta_E = E_CHP_gen_W[hour] - E_req_hour_W
            if delta_E >= 0.0:
                E_CHP_gen_export_W[hour] = delta_E
                E_CHP_gen_directload_W[hour] = E_req_hour_W
                E_req_hour_W = 0.0
            else:
                E_CHP_gen_export_W[hour] = 0.0
                E_CHP_gen_directload_W[hour] = abs(delta_E)
                E_req_hour_W = E_req_hour_W - E_CHP_gen_directload_W[hour]
        else:
            # since we cannot store it is then exported
            E_CHP_gen_export_W[hour] = E_CHP_gen_W[hour]
            E_CHP_gen_directload_W[hour] = 0.0

        # FURNACE
        if E_req_hour_W > 0.0:
            delta_E = E_Furnace_gen_W[hour] - E_req_hour_W
            if delta_E >= 0.0:
                E_Furnace_gen_export_W[hour] = delta_E
                E_Furnace_gen_directload_W[hour] = E_req_hour_W
                E_req_hour_W = 0.0
            else:
                E_Furnace_gen_export_W[hour] = 0.0
                E_Furnace_gen_directload_W[hour] = abs(delta_E)
                E_req_hour_W = E_req_hour_W - E_Furnace_gen_directload_W[hour]
        else:
            # since we cannot store it is then exported
            E_Furnace_gen_export_W[hour] = E_Furnace_gen_W[hour]
            E_Furnace_gen_directload_W[hour] = 0.0

        # CCGT_cooling
        if E_req_hour_W > 0.0:
            delta_E = E_CCGT_gen_W[hour] - E_req_hour_W
            if delta_E >= 0.0:
                E_CCGT_gen_export_W[hour] = delta_E
                E_CCGT_gen_directload_W[hour] = E_req_hour_W
                E_req_hour_W = 0.0
            else:
                E_CCGT_gen_export_W[hour] = 0.0
                E_CCGT_gen_directload_W[hour] = abs(delta_E)
                E_req_hour_W = E_req_hour_W - E_CCGT_gen_directload_W[hour]
        else:
            # since we cannot store it is then exported
            E_CCGT_gen_export_W[hour] = E_CCGT_gen_W[hour]
            E_CCGT_gen_directload_W[hour] = 0.0

        # PV
        if E_req_hour_W > 0.0:
            delta_E = E_PV_gen_W[hour] - E_req_hour_W
            if delta_E >= 0.0:
                E_PV_gen_export_W[hour] = delta_E
                E_PV_gen_directload_W[hour] = E_req_hour_W
                E_req_hour_W = 0.0
            else:
                E_PV_gen_export_W[hour] = 0.0
                E_PV_gen_directload_W[hour] = abs(delta_E)
                E_req_hour_W = E_req_hour_W - E_PV_gen_directload_W[hour]
        else:
            # since we cannot store it is then exported
            E_PV_gen_export_W[hour] = E_PV_gen_W[hour]
            E_PV_gen_directload_W[hour] = 0.0

        # PVT
        if E_req_hour_W > 0.0:
            delta_E = E_PVT_gen_W[hour] - E_req_hour_W
            if delta_E >= 0.0:
                E_PVT_gen_export_W[hour] = delta_E
                E_PVT_gen_directload_W[hour] = E_req_hour_W
                E_req_hour_W = 0.0
            else:
                E_PVT_gen_export_W[hour] = 0.0
                E_PVT_gen_directload_W[hour] = abs(delta_E)
                E_req_hour_W = E_req_hour_W - E_PVT_gen_directload_W[hour]
        else:
            # since we cannot store it is then exported
            E_PVT_gen_export_W[hour] = E_PVT_gen_W[hour]
            E_PVT_gen_directload_W[hour] = 0.0

        # COVERED BY THE GRID (IMPORTS)
        if E_req_hour_W > 0.0:
            E_GRID_directload_W[hour] = E_req_hour_W

    # TOTAL EXPORTS:
    activation_curve = {
        "DATE": date,
        'E_CHP_gen_directload_W':E_CHP_gen_directload_W,
        'E_CHP_gen_export_W':E_CHP_gen_export_W,
        'E_CCGT_gen_directload_W': E_CCGT_gen_directload_W,
        'E_CCGT_gen_export_W': E_CHP_gen_export_W,
        'E_Furnace_gen_directload_W':E_Furnace_gen_directload_W,
        'E_Furnace_gen_export_W': E_Furnace_gen_export_W,
        'E_PV_gen_directload_W':E_PV_gen_directload_W,
        'E_PV_gen_export_W':E_PV_gen_export_W,
        'E_PVT_gen_directload_W': E_PVT_gen_directload_W,
        'E_PVT_gen_export_W': E_PVT_gen_export_W,
        'E_GRID_directload_W':E_GRID_directload_W
    }
    pd.DataFrame(activation_curve).to_csv(locator.get_optimization_slave_electricity_activation_pattern_heating(
                master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)

    return activation_curve

def calc_district_system_electricity_generated(cooling_activation_data, heating_activation_data,
                                               storage_activation_data):
    E_CHP_gen_W = heating_activation_data['E_CHP_gen_W'].values
    E_Furnace_gen_W = heating_activation_data['E_Furnace_gen_W'].values
    E_CCGT_gen_W = cooling_activation_data["E_gen_CCGT_associated_with_absorption_chillers_W"].values
    E_PV_gen_W = storage_activation_data['E_PV_Wh'].values
    E_PVT_gen_W = storage_activation_data['E_PVT_Wh'].values
    E_sys_gen_W = E_CHP_gen_W + \
                  E_Furnace_gen_W + \
                  E_CCGT_gen_W + \
                  E_PV_gen_W + \
                  E_PVT_gen_W
    return E_CHP_gen_W, E_Furnace_gen_W, E_CCGT_gen_W, E_PV_gen_W, E_PVT_gen_W, E_sys_gen_W


def calc_district_system_electricity_requirements(DCN_barcode, DHN_barcode, building_names, cooling_activation_data,
                                                  heating_activation_data, locator, storage_activation_data):
    # by buildings
    E_building_req_W = extract_demand_buildings(DCN_barcode, DHN_barcode, building_names, locator)

    # by generation units
    E_generation_req_W = extract_requirements_generation_units(cooling_activation_data, heating_activation_data)

    # by storage system
    E_Storage_req_W = storage_activation_data['E_aux_ch_W'].values + storage_activation_data['E_aux_dech_W'].values
    E_aux_solar_and_heat_recovery_W = storage_activation_data['E_aux_solar_and_heat_recovery_Wh'].values
    E_sys_req_W = E_building_req_W + \
                  E_generation_req_W + \
                  E_Storage_req_W + \
                  E_aux_solar_and_heat_recovery_W
    return E_sys_req_W


def extract_requirements_generation_units(cooling_activation_data, heating_activation_data):
    E_HPServer_req_W = heating_activation_data["E_HPServer_req_W"].values
    E_HPSew_req_W = heating_activation_data["E_HPSew_req_W"].values
    E_HPLake_req_W = heating_activation_data["E_HPLake_req_W"].values
    E_GHP_req_W = heating_activation_data["E_GHP_req_W"].values
    E_BaseBoiler_req_W = heating_activation_data["E_BaseBoiler_req_W"].values
    E_PeakBoiler_req_W = heating_activation_data["E_PeakBoiler_req_W"].values
    E_BackupBoiler_req_W = heating_activation_data["E_BackupBoiler_req_W"].values
    E_used_Lake_W = cooling_activation_data['E_used_Lake_W']
    E_used_VCC_W = cooling_activation_data['E_used_VCC_W']
    E_used_VCC_backup_W = cooling_activation_data['E_used_VCC_backup_W']
    E_used_ACH_W = cooling_activation_data['E_used_ACH_W']
    E_used_CT_W = cooling_activation_data['E_used_CT_W']

    E_generation_req_W = E_HPServer_req_W +\
                         E_HPSew_req_W + \
                         E_HPLake_req_W +\
                         E_GHP_req_W +\
                         E_BaseBoiler_req_W +\
                         E_PeakBoiler_req_W +\
                         E_BackupBoiler_req_W + \
                         E_used_Lake_W +\
                         E_used_VCC_W + \
                         E_used_VCC_backup_W + \
                         E_used_ACH_W +\
                         E_used_CT_W

    return E_generation_req_W


def extract_demand_buildings(DCN_barcode, DHN_barcode, building_names, locator):
    # by buildings'electrical system
    E_building_req_W = np.zeros(8760)
    for name in building_names:  # adding the electricity demand of
        building_demand = pd.read_csv(locator.get_demand_results_file(name))
        E_building_req_W = E_building_req_W + building_demand['E_sys_kWh'].values * 1000
    # by buildings' individual heating system and cooling system
    for i, name in zip(DCN_barcode, building_names):
        if i is '1':
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            E_building_req_W = E_building_req_W + (
                    building_demand['E_cdata_kWh'] + building_demand['E_cs_kWh'] + building_demand[
                'E_cre_kWh']) * 1000
        else:
            # TODO: read files from decentralized results (THIS IS WRONG!!!!!)
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            E_building_req_W = E_building_req_W + (
                    building_demand['E_cdata_kWh'] + building_demand['E_cs_kWh'] + building_demand[
                'E_cre_kWh']) * 1000
    for i, name in zip(DHN_barcode, building_names):
        if i is '1':
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            E_building_req_W = E_building_req_W + (
                    building_demand['E_ww_kWh'] + building_demand['E_hs_kWh'] + building_demand['E_pro_kWh']) * 1000
        else:
            # TODO: read files from decentralized results (THIS IS WRONG!!!!!)
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            E_building_req_W = E_building_req_W + (
                    building_demand['E_cdata_kWh'] + building_demand['E_cs_kWh'] + building_demand[
                'E_cre_kWh']) * 1000
    return E_building_req_W


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 25
    individual = 10
    print("Calculating imports and exports of individual" + str(individual) + " of generation " + str(generation))

    electricity_calculations_of_all_buildings(generation, individual, locator, district_heating_network,
                                              district_cooling_network)


if __name__ == '__main__':
    main(cea.config.Configuration())
