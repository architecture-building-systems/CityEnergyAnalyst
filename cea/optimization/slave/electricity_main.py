"""
Electricity imports and exports script

This file takes in the values of the electricity activation pattern (which is only considering buildings present in
network and corresponding district energy systems) and adds in the electricity requirement of decentralized buildings
and recalculates the imports from grid and exports to the grid
"""
from __future__ import division
from __future__ import print_function

import os

import numpy as np
import pandas as pd

import cea.technologies.solar.photovoltaic as pv
from cea.constants import HOURS_IN_YEAR
from cea.optimization.master.emissions_model import calc_emissions_Whyr_to_tonCO2yr, calc_pen_Whyr_to_MJoilyr

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def electricity_calculations_of_all_buildings(locator, master_to_slave_vars,
                                              district_heating_generation_dispatch,
                                              districy_heating_electricity_requirements_dispatch,
                                              district_cooling_generation_dispatch,
                                              districy_cooling_electricity_requirements_dispatch
                                              ):
    # local variables
    building_names = master_to_slave_vars.building_names_electricity

    # GET ENERGY GENERATION OF THE ELECTRICAL GRID
    district_microgrid_generation_dispatch = calc_district_system_electricity_generated(locator,
                                                                                        master_to_slave_vars)

    # GET ENERGY REQUIREMENTS
    district_electricity_demands, \
    E_sys_req_W = calc_district_system_electricity_requirements(master_to_slave_vars,
                                                                building_names,
                                                                locator,
                                                                districy_heating_electricity_requirements_dispatch,
                                                                districy_cooling_electricity_requirements_dispatch
                                                                )

    # GET ACTIVATION CURVE
    # INITIALIZE VARIABLES:
    if master_to_slave_vars.DHN_exists:
        E_CHP_gen_W = district_heating_generation_dispatch['E_CHP_gen_W']
        E_PVT_gen_W = district_heating_generation_dispatch['E_PVT_gen_W']
        E_Furnace_dry_gen_W = district_heating_generation_dispatch['E_Furnace_dry_gen_W']
        E_Furnace_wet_gen_W = district_heating_generation_dispatch['E_Furnace_wet_gen_W']
    else:
        E_CHP_gen_W = E_PVT_gen_W = E_Furnace_dry_gen_W = E_Furnace_wet_gen_W = np.zeros(HOURS_IN_YEAR)

    if master_to_slave_vars.DCN_exists:
        E_Trigen_NG_gen_W = district_cooling_generation_dispatch['E_Trigen_NG_gen_W']
    else:
        E_Trigen_NG_gen_W = np.zeros(HOURS_IN_YEAR)

    E_PV_gen_W = district_microgrid_generation_dispatch['E_PV_gen_W']

    E_CHP_gen_directload_W, \
    E_CHP_gen_export_W, \
    E_Trigen_gen_directload_W, \
    E_Trigen_gen_export_W, \
    E_Furnace_dry_gen_directload_W, \
    E_Furnace_dry_gen_export_W, \
    E_Furnace_wet_gen_directload_W, \
    E_Furnace_wet_gen_export_W, \
    E_PV_gen_directload_W, \
    E_PV_gen_export_W, \
    E_PVT_gen_directload_W, \
    E_PVT_gen_export_W, \
    E_GRID_directload_W = np.vectorize(electricity_activation_curve)(E_CHP_gen_W,
                                                                     E_PVT_gen_W,
                                                                     E_Furnace_dry_gen_W,
                                                                     E_Furnace_wet_gen_W,
                                                                     E_Trigen_NG_gen_W,
                                                                     E_PV_gen_W,
                                                                     E_sys_req_W)

    district_electricity_dispatch = {'E_CHP_gen_directload_W': E_CHP_gen_directload_W,
                                     'E_CHP_gen_export_W': E_CHP_gen_export_W,
                                     'E_Trigen_gen_directload_W': E_Trigen_gen_directload_W,
                                     'E_Trigen_gen_export_W': E_Trigen_gen_export_W,
                                     'E_Furnace_dry_gen_directload_W': E_Furnace_dry_gen_directload_W,
                                     'E_Furnace_dry_gen_export_W': E_Furnace_dry_gen_export_W,
                                     'E_Furnace_wet_gen_directload_W': E_Furnace_wet_gen_directload_W,
                                     'E_Furnace_wet_gen_export_W': E_Furnace_wet_gen_export_W,
                                     'E_PV_gen_directload_W': E_PV_gen_directload_W,
                                     'E_PV_gen_export_W': E_PV_gen_export_W,
                                     'E_PVT_gen_directload_W': E_PVT_gen_directload_W,
                                     'E_PVT_gen_export_W': E_PVT_gen_export_W,
                                     'E_GRID_directload_W': E_GRID_directload_W
                                     }

    # CALC COSTS
    district_microgrid_costs = calc_electricity_performance_costs(locator, master_to_slave_vars)

    return district_microgrid_costs, \
           district_electricity_dispatch, \
           district_electricity_demands


def calc_electricity_performance_emissions(lca, E_PV_gen_export_W, E_GRID_directload_W):
    # SOlar technologies
    GHG_PV_gen_export_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(sum(E_PV_gen_export_W), lca.EL_TO_CO2)
    GHG_PV_gen_directload_tonCO2 = 0.0  # because the price of fuel is already included

    PEN_PV_gen_export_MJoil = calc_pen_Whyr_to_MJoilyr(sum(E_PV_gen_export_W), lca.EL_TO_OIL_EQ)
    PEN_PV_gen_directload_MJoil = 0.0  # because the price of fuel is already included

    GHG_PV_connected_tonCO2 = GHG_PV_gen_directload_tonCO2 - GHG_PV_gen_export_tonCO2
    PEN_PV_connected_MJoil = PEN_PV_gen_directload_MJoil - PEN_PV_gen_export_MJoil

    # GRid
    GHG_GRID_directload_tonCO2 = calc_emissions_Whyr_to_tonCO2yr(sum(E_GRID_directload_W), lca.EL_TO_CO2)
    PEN_GRID_directload_MJoil = calc_pen_Whyr_to_MJoilyr(sum(E_GRID_directload_W), lca.EL_TO_OIL_EQ)

    # calculate emissions of generation units BUT solar (the last will be calculated in the next STEP)
    # PEN_HPSolarandHeatRecovery_MJoil = E_aux_solar_and_heat_recovery_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
    # GHG_HPSolarandHeatRecovery_tonCO2 = E_aux_solar_and_heat_recovery_W * lca.EL_TO_CO2 * WH_TO_J / 1E6

    performance_electricity = {
        # emissions
        "GHG_PV_connected_tonCO2": GHG_PV_connected_tonCO2,
        "GHG_GRID_connected_tonCO2": GHG_GRID_directload_tonCO2,

        # primary energy
        "PEN_PV_connected_MJoil": PEN_PV_connected_MJoil,
        "PEN_GRID_connected_MJoil": PEN_GRID_directload_MJoil
    }

    return performance_electricity


def calc_electricity_performance_costs(locator, master_to_slave_vars):
    # PV COSTS
    PV_installed_area_m2 = master_to_slave_vars.A_PV_m2  # kW
    Capex_a_PV_USD, Opex_fixed_PV_USD, Capex_PV_USD = pv.calc_Cinv_pv(PV_installed_area_m2, locator)

    performance_electricity_costs = {
        "Capex_a_PV_connected_USD": Capex_a_PV_USD,
        "Capex_a_GRID_connected_USD": 0.0,

        # total_capex
        "Capex_total_PV_connected_USD": Capex_PV_USD,
        "Capex_total_GRID_connected_USD": 0.0,

        # opex fixed costs
        "Opex_fixed_PV_connected_USD": Opex_fixed_PV_USD,
        "Opex_fixed_GRID_connected_USD": 0.0,

    }
    return performance_electricity_costs


def electricity_activation_curve(E_CHP_gen_W,
                                 E_PVT_gen_W,
                                 E_Furnace_dry_gen_W,
                                 E_Furnace_wet_gen_W,
                                 E_Trigen_NG_gen_W,
                                 E_PV_gen_W,
                                 E_req_hour_W):
    # CHP
    if E_CHP_gen_W > 0.0 and E_req_hour_W > 0.0:
        delta_E = E_CHP_gen_W - E_req_hour_W
        if delta_E >= 0.0:
            E_CHP_gen_export_W = delta_E
            E_CHP_gen_directload_W = E_req_hour_W
            E_req_hour_W = 0.0
        else:
            E_CHP_gen_export_W = 0.0
            E_CHP_gen_directload_W = E_CHP_gen_W
            E_req_hour_W = E_req_hour_W - E_CHP_gen_directload_W
    else:
        # since we cannot store it is then exported
        E_CHP_gen_export_W = E_CHP_gen_W
        E_CHP_gen_directload_W = 0.0

    # FURNACE DRY
    if E_Furnace_dry_gen_W > 0.0 and E_req_hour_W > 0.0:
        delta_E = E_Furnace_dry_gen_W - E_req_hour_W
        if delta_E >= 0.0:
            E_Furnace_dry_gen_export_W = delta_E
            E_Furnace_dry_gen_directload_W = E_req_hour_W
            E_req_hour_W = 0.0
        else:
            E_Furnace_dry_gen_export_W = 0.0
            E_Furnace_dry_gen_directload_W = E_Furnace_dry_gen_W
            E_req_hour_W = E_req_hour_W - E_Furnace_dry_gen_directload_W
    else:
        # since we cannot store it is then exported
        E_Furnace_dry_gen_export_W = E_Furnace_dry_gen_W
        E_Furnace_dry_gen_directload_W = 0.0

    # FURNACE WET
    if E_Furnace_wet_gen_W > 0.0 and E_req_hour_W > 0.0:
        delta_E = E_Furnace_wet_gen_W - E_req_hour_W
        if delta_E >= 0.0:
            E_Furnace_wet_gen_export_W = delta_E
            E_Furnace_wet_gen_directload_W = E_req_hour_W
            E_req_hour_W = 0.0
        else:
            E_Furnace_wet_gen_export_W = 0.0
            E_Furnace_wet_gen_directload_W = E_Furnace_wet_gen_W
            E_req_hour_W = E_req_hour_W - E_Furnace_wet_gen_directload_W
    else:
        # since we cannot store it is then exported
        E_Furnace_wet_gen_export_W = E_Furnace_wet_gen_W
        E_Furnace_wet_gen_directload_W = 0.0

    # CCGT_cooling
    if E_Trigen_NG_gen_W > 0.0 and E_req_hour_W > 0.0:
        delta_E = E_Trigen_NG_gen_W - E_req_hour_W
        if delta_E >= 0.0:
            E_Trigen_gen_export_W = delta_E
            E_Trigen_gen_directload_W = E_req_hour_W
            E_req_hour_W = 0.0
        else:
            E_Trigen_gen_export_W = 0.0
            E_Trigen_gen_directload_W = E_Trigen_NG_gen_W
            E_req_hour_W = E_req_hour_W - E_Trigen_gen_directload_W
    else:
        # since we cannot store it is then exported
        E_Trigen_gen_export_W = E_Trigen_NG_gen_W
        E_Trigen_gen_directload_W = 0.0

    # PV
    if E_PV_gen_W > 0.0 and E_req_hour_W > 0.0:
        delta_E = E_PV_gen_W - E_req_hour_W
        if delta_E >= 0.0:
            E_PV_gen_export_W = delta_E
            E_PV_gen_directload_W = E_req_hour_W
            E_req_hour_W = 0.0
        else:
            E_PV_gen_export_W = 0.0
            E_PV_gen_directload_W = E_PV_gen_W
            E_req_hour_W = E_req_hour_W - E_PV_gen_directload_W
    else:
        # since we cannot store it is then exported
        E_PV_gen_export_W = E_PV_gen_W
        E_PV_gen_directload_W = 0.0

    # PVT
    if E_PVT_gen_W > 0.0 and E_req_hour_W > 0.0:
        delta_E = E_PVT_gen_W - E_req_hour_W
        if delta_E >= 0.0:
            E_PVT_gen_export_W = delta_E
            E_PVT_gen_directload_W = E_req_hour_W
            E_req_hour_W = 0.0
        else:
            E_PVT_gen_export_W = 0.0
            E_PVT_gen_directload_W = E_PVT_gen_W
            E_req_hour_W = E_req_hour_W - E_PVT_gen_directload_W
    else:
        # since we cannot store it is then exported
        E_PVT_gen_export_W = E_PVT_gen_W
        E_PVT_gen_directload_W = 0.0

    # COVERED BY THE GRID (IMPORTS)
    if E_req_hour_W > 0.0:
        E_GRID_directload_W = E_req_hour_W
    else:
        E_GRID_directload_W = 0.0

    return E_CHP_gen_directload_W, \
           E_CHP_gen_export_W, \
           E_Trigen_gen_directload_W, \
           E_Trigen_gen_export_W, \
           E_Furnace_dry_gen_directload_W, \
           E_Furnace_dry_gen_export_W, \
           E_Furnace_wet_gen_directload_W, \
           E_Furnace_wet_gen_export_W, \
           E_PV_gen_directload_W, \
           E_PV_gen_export_W, \
           E_PVT_gen_directload_W, \
           E_PVT_gen_export_W, \
           E_GRID_directload_W


def calc_district_system_electricity_generated(locator,
                                               master_to_slave_vars):
    # TECHNOLOGEIS THAT ONLY GENERATE ELECTRICITY
    E_PV_gen_W = calc_available_generation_PV(locator, master_to_slave_vars.building_names_all,
                                              master_to_slave_vars.PV_share)

    district_electricity_generation_dispatch = {
        'E_PV_gen_W': E_PV_gen_W
    }

    return district_electricity_generation_dispatch


def calc_available_generation_PV(locator, buildings, share_allowed):
    E_PV_gen_kWh = np.zeros(HOURS_IN_YEAR)
    for building_name in buildings:
        building_PVT = pd.read_csv(
            os.path.join(locator.get_potentials_solar_folder(), building_name + '_PV.csv')).fillna(value=0.0)
        E_PV_gen_kWh += building_PVT['E_PV_gen_kWh']
    E_PVT_gen_Wh = E_PV_gen_kWh * share_allowed * 1000
    return E_PVT_gen_Wh


def calc_district_system_electricity_requirements(master_to_slave_vars,
                                                  building_names,
                                                  locator,
                                                  DH_electricity_requirements,
                                                  DC_electricity_requirements):
    # by buildings
    electricity_demand_buildings= extract_electricity_demand_buildings(master_to_slave_vars,
                                                                             building_names,
                                                                             locator)

    # add those due to district heating and district cooling systems
    join1 = dict(electricity_demand_buildings, **DH_electricity_requirements)
    requirements_electricity = dict(join1, **DC_electricity_requirements)
    E_sys_req_W = sum(requirements_electricity.itervalues())

    # now get all the requirements
    requirements_electricity["E_electricalnetwork_sys_req_W"] = E_sys_req_W

    return requirements_electricity, E_sys_req_W


def extract_electricity_demand_buildings(master_to_slave_vars, building_names, locator):
    # store the names of the buildings connected to district heating or district cooling
    buildings_connected_to_district_heating = master_to_slave_vars.buildings_connected_to_district_heating
    buildings_connected_to_district_cooling = master_to_slave_vars.buildings_connected_to_district_cooling

    # these are all the buildngs with heating and cooling demand
    building_names_heating = master_to_slave_vars.building_names_heating
    building_names_cooling = master_to_slave_vars.building_names_cooling

    # system requirements
    E_hs_ww_req_W = np.zeros(HOURS_IN_YEAR)
    E_cs_cre_cdata_req_W = np.zeros(HOURS_IN_YEAR)
    E_hs_ww_req_disconnected_W = np.zeros(HOURS_IN_YEAR)
    E_cs_cre_cdata_req_disconnected_W = np.zeros(HOURS_IN_YEAR)

    # End-use demands
    Eal_req_W = np.zeros(HOURS_IN_YEAR)
    Edata_req_W = np.zeros(HOURS_IN_YEAR)
    Epro_req_W = np.zeros(HOURS_IN_YEAR)
    Eaux_req_W = np.zeros(HOURS_IN_YEAR)

    # for all buildings with electricity demand
    for name in building_names:  # adding the electricity demand of
        building_demand = pd.read_csv(locator.get_demand_results_file(name))
        # end-use electrical demands
        Eal_req_W += building_demand['Eal_kWh'] * 1000
        Edata_req_W += building_demand['Edata_kWh'] * 1000
        Epro_req_W += building_demand['Epro_kWh'] * 1000
        Eaux_req_W += building_demand['Eaux_kWh'] * 1000

    # when the two networks are present
    if master_to_slave_vars.DHN_exists and master_to_slave_vars.DCN_exists:
        for name in building_names:
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            if name in buildings_connected_to_district_heating and name in buildings_connected_to_district_cooling:
                # if connected to the heating network
                E_hs_ww_req_W += 0.0
                E_cs_cre_cdata_req_W += 0.0
            elif name in buildings_connected_to_district_heating:
                # if disconnected from the heating network
                E_hs_ww_req_W += 0.0
                if master_to_slave_vars.WasteServersHeatRecovery == 1:
                    E_cs_cre_cdata_req_W += (building_demand['E_cs_kWh'] +
                                             building_demand['E_cre_kWh']) * 1000  # to W
                else:
                    E_cs_cre_cdata_req_W += (building_demand['E_cs_kWh'] +
                                             building_demand['E_cre_kWh'] +
                                             building_demand['E_cdata_kWh']) * 1000  # to W
            elif name in buildings_connected_to_district_cooling:
                E_hs_ww_req_W += (building_demand['E_hs_kWh'] + building_demand['E_ww_kWh']) * 1000  # to W
                E_cs_cre_cdata_req_W += 0.0
            else:
                building_dencentralized_system_heating = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_heating_activation(name))
                building_dencentralized_system_cooling = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_cooling_activation(name))
                E_hs_ww_req_disconnected_W += building_dencentralized_system_heating['E_hs_ww_req_W']
                E_cs_cre_cdata_req_disconnected_W += building_dencentralized_system_cooling['E_cs_cre_cdata_req_W']

    # if only a district heating network exists.
    elif master_to_slave_vars.DHN_exists:
        for name in building_names:
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            if name in buildings_connected_to_district_heating:
                # if connected to the heating network
                E_hs_ww_req_W += 0.0  # because it is connected to the heating network
                if master_to_slave_vars.WasteServersHeatRecovery == 1:
                    E_cs_cre_cdata_req_W += (building_demand['E_cs_kWh'] +
                                             building_demand['E_cre_kWh']) * 1000  # to W
                else:
                    E_cs_cre_cdata_req_W += (building_demand['E_cs_kWh'] +
                                             building_demand['E_cre_kWh'] +
                                             building_demand['E_cdata_kWh']) * 1000  # to W
            else:
                # if not then get airconditioning loads of the baseline
                E_cs_cre_cdata_req_W += (building_demand['E_cs_kWh'] +
                                         building_demand['E_cre_kWh'] +
                                         building_demand['E_cdata_kWh']) * 1000  # to W
                if name in building_names_heating:
                    # if there is a decentralized heating use it.
                    building_dencentralized_system = pd.read_csv(
                        locator.get_optimization_decentralized_folder_building_result_heating_activation(name))
                    E_hs_ww_req_disconnected_W += building_dencentralized_system['E_hs_ww_req_W']
                else:
                    # if not (cae of building with electric load and not heating)
                    E_hs_ww_req_disconnected_W += 0.0

    # if only a district cooling network exists.
    elif master_to_slave_vars.DCN_exists:
        for name in building_names:
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            if name in buildings_connected_to_district_cooling:
                # if connected to the cooling network
                E_hs_ww_req_W += (building_demand['E_hs_kWh'] + building_demand['E_ww_kWh']) * 1000  # to W
                E_cs_cre_cdata_req_W += 0.0
            else:
                # if not then get electric boilers etc form baseline.
                E_hs_ww_req_W += (building_demand['E_hs_kWh'] + building_demand['E_ww_kWh']) * 1000  # to W
                if name in building_names_cooling:
                    # if there is a decentralized cooling use it.
                    building_dencentralized_system = pd.read_csv(
                        locator.get_optimization_decentralized_folder_building_cooling_activation(name))
                    E_cs_cre_cdata_req_disconnected_W += building_dencentralized_system['E_cs_cre_cdata_req_W']
                else:
                    # if not (cae of building with electric load and not cooling
                    E_cs_cre_cdata_req_disconnected_W += 0.0

    E_req_buildings = {
        # end-use demands
        'Eal_req_W': Eal_req_W,
        'Edata_req_W': Edata_req_W,
        'Epro_req_W': Epro_req_W,
        'Eaux_req_W': Eaux_req_W,

        # system requirements (by decentralized units)
        'E_hs_ww_req_connected_W': E_hs_ww_req_W,
        'E_cs_cre_cdata_req_connected_W': E_cs_cre_cdata_req_W,
        'E_hs_ww_req_disconnected_W': E_hs_ww_req_disconnected_W,
        'E_cs_cre_cdata_req_disconnected_W': E_cs_cre_cdata_req_disconnected_W
    }

    return E_req_buildings



def extract_fuels_demand_buildings(master_to_slave_vars, building_names, locator):
    # store the names of the buildings connected to district heating or district cooling
    buildings_connected_to_district_heating = master_to_slave_vars.buildings_connected_to_district_heating
    buildings_connected_to_district_cooling = master_to_slave_vars.buildings_connected_to_district_cooling

    # these are all the buildngs with heating and cooling demand
    building_names_heating = master_to_slave_vars.building_names_heating

    # system requirements
    NG_hs_ww_req_W  = np.zeros(HOURS_IN_YEAR)

    # when the two networks are present
    if master_to_slave_vars.DHN_exists and master_to_slave_vars.DCN_exists:
        for name in building_names:
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            if name in buildings_connected_to_district_heating and name in buildings_connected_to_district_cooling:
                # if connected to the heating network
                NG_hs_ww_req_W += 0.0
            elif name in buildings_connected_to_district_heating:
                # if disconnected from the heating network
                NG_hs_ww_req_W += 0.0
            elif name in buildings_connected_to_district_cooling:
                NG_hs_ww_req_W += (building_demand['NG_hs_kWh'] + building_demand['NG_ww_kWh']) * 1000  # to W
            else:
                building_dencentralized_system_heating = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_heating_activation(name))
                NG_hs_ww_req_W += building_dencentralized_system_heating['NG_BackupBoiler_req_Wh'] + \
                                  building_dencentralized_system_heating['NG_Boiler_req_Wh']

    # if only a district heating network exists.
    elif master_to_slave_vars.DHN_exists:
        for name in building_names:
            if name in buildings_connected_to_district_heating:
                # if connected to the heating network
                NG_hs_ww_req_W += 0.0
            else:
                # if not then get airconditioning loads of the baseline
                if name in building_names_heating:
                    # if there is a decentralized heating use it.
                    building_dencentralized_system = pd.read_csv(
                        locator.get_optimization_decentralized_folder_building_result_heating_activation(name))
                    NG_hs_ww_req_W += building_dencentralized_system['NG_BackupBoiler_req_Wh'] + \
                                      building_dencentralized_system['NG_Boiler_req_Wh']
                else:
                    # if not (cae of building with electric load and not heating)
                    NG_hs_ww_req_W += 0.0

    # if only a district cooling network exists.
    elif master_to_slave_vars.DCN_exists:
        for name in building_names:
            building_demand = pd.read_csv(locator.get_demand_results_file(name))
            # if not then get electric boilers etc form baseline.
            NG_hs_ww_req_W += (building_demand['NG_hs_kWh'] + building_demand['NG_ww_kWh']) * 1000  # to W

    NG_req_buildings = {
        # system requirements (by decentralized units)
        'NG_hs_ww_req_W': NG_hs_ww_req_W
    }

    return NG_req_buildings