# -*- coding: utf-8 -*-
"""
Extra costs to an individual

"""
from __future__ import division

from math import log

import numpy as np
import pandas as pd

import cea.technologies.boiler as boiler
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as VCCModel
import cea.technologies.cogeneration as chp
import cea.technologies.cogeneration as cogeneration
import cea.technologies.cooling_tower as CTModel
import cea.technologies.furnace as furnace
import cea.technologies.heat_exchangers as hex
import cea.technologies.heatpumps as hp
import cea.technologies.pumps as PumpModel
import cea.technologies.solar.photovoltaic_thermal as pvt
import cea.technologies.solar.solar_collector as stc
import cea.technologies.thermal_storage as thermal_storage
from cea.constants import HOURS_IN_YEAR
from cea.optimization.constants import ACH_TYPE_DOUBLE
from cea.optimization.constants import N_PVT
from cea.optimization.master.emissions_model import calc_emissions_Whyr_to_tonCO2yr, calc_pen_Whyr_to_MJoilyr

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def buildings_disconnected_costs_and_emissions(column_names_buildings_heating,
                                               column_names_buildings_cooling, locator, master_to_slave_vars):
    DHN_barcode = master_to_slave_vars.DHN_barcode
    DCN_barcode = master_to_slave_vars.DCN_barcode

    # DISCONNECTED BUILDINGS  - HEATING LOADS
    GHG_heating_sys_disconnected_tonCO2yr, \
    PEN_heating_sys_disconnected_MJoilyr, \
    Capex_total_heating_sys_disconnected_USD, \
    Capex_a_heating_sys_disconnected_USD, \
    Opex_var_heating_sys_disconnected, \
    Opex_fixed_heating_sys_disconnected_USD = calc_costs_emissions_decentralized_DH(DHN_barcode,
                                                                                    column_names_buildings_heating,
                                                                                    locator)

    # DISCONNECTED BUILDINGS - COOLING LOADS
    GHG_cooling_sys_disconnected_tonCO2yr, \
    PEN_cooling_sys_disconnected_MJoilyr, \
    Capex_total_cooling_sys_disconnected_USD, \
    Capex_a_cooling_sys_disconnected_USD, \
    Opex_var_cooling_sys_disconnected, \
    Opex_fixed_cooling_sys_disconnected_USD = calc_costs_emissions_decentralized_DC(
        DCN_barcode,
        column_names_buildings_cooling, locator)

    disconnected_costs = {
        # heating
        "Capex_a_heating_disconnected_USD": Capex_a_heating_sys_disconnected_USD,
        "Capex_total_heating_disconnected_USD": Capex_total_heating_sys_disconnected_USD,
        "Opex_var_heating_disconnected_USD": Opex_var_heating_sys_disconnected,
        "Opex_fixed_heating_disconnected_USD": Opex_fixed_heating_sys_disconnected_USD,
        # cooling
        "Capex_a_cooling_disconnected_USD": Capex_a_cooling_sys_disconnected_USD,
        "Capex_total_cooling_disconnected_USD": Capex_total_cooling_sys_disconnected_USD,
        "Opex_var_cooling_disconnected_USD": Opex_var_cooling_sys_disconnected,
        "Opex_fixed_cooling_disconnected_USD": Opex_fixed_cooling_sys_disconnected_USD,
    }

    disconnected_emissions = {
        # CO2 EMISSIONS
        "GHG_heating_disconnected_tonCO2": GHG_heating_sys_disconnected_tonCO2yr,
        "GHG_cooling_disconnected_tonCO2": GHG_cooling_sys_disconnected_tonCO2yr,

        # PRIMARY ENERGY (NON-RENEWABLE)
        "PEN_heating_disconnected_MJoil": PEN_heating_sys_disconnected_MJoilyr,
        "PEN_cooling_disconnected_MJoil": PEN_cooling_sys_disconnected_MJoilyr
    }

    return disconnected_costs, disconnected_emissions


def calc_network_costs_heating(locator, master_to_slave_vars, network_features, lca, network_type):
    # Intitialize class
    pipesCosts_USD = network_features.pipesCosts_DHN_USD
    num_buildings_connected = master_to_slave_vars.number_of_buildings_connected_heating

    num_all_buildings = master_to_slave_vars.num_total_buildings
    ratio_connected = num_buildings_connected / num_all_buildings

    # Capital costs
    Inv_IR = 0.05
    Inv_LT = 20
    Inv_OM = 0.10
    Capex_Network_USD = pipesCosts_USD * ratio_connected
    Capex_a_Network_USD = Capex_Network_USD * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_Network_USD = Capex_Network_USD * Inv_OM

    # costs of pumps
    Capex_a_pump_USD, Opex_fixed_pump_USD, Opex_var_pump_USD, Capex_pump_USD, P_motor_tot_W = PumpModel.calc_Ctot_pump(
        master_to_slave_vars, network_features, locator, lca, network_type)

    # summarize
    Capex_Network_USD += Capex_pump_USD
    Capex_a_Network_USD += Capex_a_pump_USD
    Opex_fixed_Network_USD += Opex_fixed_pump_USD
    Opex_var_Network_USD = Opex_var_pump_USD

    # CAPEX AND OPEX OF HEATING SUBSTATIONS
    DHN_barcode = master_to_slave_vars.DHN_barcode
    building_names = master_to_slave_vars.building_names_heating
    Capex_SubstationsHeating_USD, \
    Capex_a_SubstationsHeating_USD, \
    Opex_fixed_SubstationsHeating_USD = calc_substations_costs_heating(building_names, DHN_barcode,
                                                                       locator)

    performance = {
        'Capex_a_DHN_connected_USD': Capex_a_Network_USD,
        "Capex_a_SubstationsHeating_connected_USD": Capex_a_SubstationsHeating_USD,

        "Capex_total_DHN_connected_USD": Capex_Network_USD,
        "Capex_total_SubstationsHeating_connected_USD": Capex_SubstationsHeating_USD,

        "Opex_fixed_DHN_connected_USD": Opex_fixed_Network_USD,
        "Opex_fixed_SubstationsHeating_connected_USD": Opex_fixed_SubstationsHeating_USD,
    }
    return performance, P_motor_tot_W


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


def calc_variable_costs_connected_buildings(sum_natural_gas_imports_W,
                                            sum_wet_biomass_imports_W,
                                            sum_dry_biomass_imports_W,
                                            sum_electricity_imports_W,
                                            sum_electricity_exports_W,
                                            prices,
                                            lca):
    # COSTS
    Opex_var_NG_sys_connected_USD = sum(sum_natural_gas_imports_W) * prices.NG_PRICE
    Opex_var_WB_sys_connected_USD = sum(sum_wet_biomass_imports_W) * prices.BG_PRICE
    Opex_var_DB_sys_connected_USD = sum(sum_dry_biomass_imports_W) * prices.BG_PRICE
    Opex_var_GRID_buy_sys_connected_USD = sum(sum_electricity_imports_W * lca.ELEC_PRICE)
    Opex_var_GRID_sell_sys_connected_USD = - sum(sum_electricity_exports_W * lca.ELEC_PRICE_EXPORT)

    district_variable_costs = {
        "Opex_var_NG_connected_USD": Opex_var_NG_sys_connected_USD,
        "Opex_var_WB_connected_USD": Opex_var_WB_sys_connected_USD,
        "Opex_var_DB_sconnected_USD": Opex_var_DB_sys_connected_USD,
        "Opex_var_GRID_imports_connected_USD": Opex_var_GRID_buy_sys_connected_USD,
        "Opex_var_GRID_exports_connected_USD": Opex_var_GRID_sell_sys_connected_USD
    }

    return district_variable_costs


def calc_emissions_connected_buildings(sum_natural_gas_imports_W,
                                       sum_wet_biomass_imports_W,
                                       sum_dry_biomass_imports_W,
                                       sum_electricity_imports_W,
                                       sum_electricity_exports_W,
                                       lca):
    # SUMMARIZE
    sum_natural_gas_imports_Whyr = sum(sum_natural_gas_imports_W)
    sum_wet_biomass_imports_Whyr = sum(sum_wet_biomass_imports_W)
    sum_dry_biomass_imports_Whyr = sum(sum_dry_biomass_imports_W)
    sum_electricity_imports_Whyr = sum(sum_electricity_imports_W)
    sum_electricity_exports_Whyr = sum(sum_electricity_exports_W)

    GHG_NG_connected_tonCO2yr = calc_emissions_Whyr_to_tonCO2yr(sum_natural_gas_imports_Whyr, lca.NG_BOILER_TO_CO2_STD)
    GHG_WB_connected_tonCO2yr = calc_emissions_Whyr_to_tonCO2yr(sum_wet_biomass_imports_Whyr, lca.FURNACE_TO_CO2_STD)
    GHG_DB_connected_tonCO2yr = calc_emissions_Whyr_to_tonCO2yr(sum_dry_biomass_imports_Whyr, lca.FURNACE_TO_CO2_STD)
    GHG_GRID_imports_connected_tonCO2yr = calc_emissions_Whyr_to_tonCO2yr(sum_electricity_imports_Whyr, lca.EL_TO_CO2)
    GHG_GRID_exports_connected_tonCO2yr = - calc_emissions_Whyr_to_tonCO2yr(sum_electricity_exports_Whyr, lca.EL_TO_CO2)

    PEN_NG_connected_MJoilyr = calc_pen_Whyr_to_MJoilyr(sum_natural_gas_imports_Whyr, lca.NG_BOILER_TO_OIL_STD)
    PEN_WB_connected_MJoilyr = calc_pen_Whyr_to_MJoilyr(sum_wet_biomass_imports_Whyr, lca.FURNACE_TO_OIL_STD)
    PEN_DB_connected_MJoilyr = calc_pen_Whyr_to_MJoilyr(sum_dry_biomass_imports_Whyr, lca.FURNACE_TO_OIL_STD)
    PEN_GRID_imports_connected_MJoilyr = calc_pen_Whyr_to_MJoilyr(sum_electricity_imports_Whyr, lca.EL_TO_OIL_EQ)
    PEN_GRID_exports_connected_MJoilyr = - calc_pen_Whyr_to_MJoilyr(sum_electricity_exports_Whyr, lca.EL_TO_OIL_EQ)

    buildings_connected_emissions_primary_energy = {
        "GHG_NG_connected_tonCO2yr": GHG_NG_connected_tonCO2yr,
        "GHG_WB_connected_tonCO2yr": GHG_WB_connected_tonCO2yr,
        "GHG_DB_connected_tonCO2yr": GHG_DB_connected_tonCO2yr,
        "GHG_GRID_imports_connected_tonCO2yr": GHG_GRID_imports_connected_tonCO2yr,
        "GHG_GRID_exports_connected_tonCO2yr": GHG_GRID_exports_connected_tonCO2yr,

        "PEN_NG_connected_MJoilyr": PEN_NG_connected_MJoilyr,
        "PEN_WB_connected_MJoilyr": PEN_WB_connected_MJoilyr,
        "PEN_DB_connected_MJoilyr": PEN_DB_connected_MJoilyr,
        "PEN_GRID_imports_connected_MJoilyr": PEN_GRID_imports_connected_MJoilyr,
        "PEN_GRID_exports_connected_MJoilyr": PEN_GRID_exports_connected_MJoilyr
    }

    return buildings_connected_emissions_primary_energy


def summary_fuel_electricity_consumption(master_to_slave_vars,
                                         district_cooling_fuel_requirements_dispatch,
                                         district_heating_fuel_requirements_dispatch,
                                         district_microgrid_requirements_dispatch):
    # join in one dictionary to facilitate the iteration
    join1 = dict(district_microgrid_requirements_dispatch, **district_heating_fuel_requirements_dispatch)
    joined_dict = dict(join1, **district_cooling_fuel_requirements_dispatch)
    # Iterate over all the files
    sum_natural_gas_imports_W = np.zeros(HOURS_IN_YEAR)
    sum_wet_biomass_imports_W = np.zeros(HOURS_IN_YEAR)
    sum_dry_biomass_imports_W = np.zeros(HOURS_IN_YEAR)
    sum_electricity_imports_W = np.zeros(HOURS_IN_YEAR)
    sum_electricity_exports_W = np.zeros(HOURS_IN_YEAR)

    for key, value in joined_dict.items():
        if "NG_" in key and "req" in key:
            sum_natural_gas_imports_W += value
        elif "WB_" in key and "req" in key:
            sum_wet_biomass_imports_W += value
        elif "DB_" in key and "req" in key:
            sum_dry_biomass_imports_W += value
        elif "E_" in key and "GRID" in key and "directload" in key:
            sum_electricity_imports_W += value
        elif "E_" in key and "export" in key:
            sum_electricity_exports_W += value

    return sum_natural_gas_imports_W, \
           sum_wet_biomass_imports_W, \
           sum_dry_biomass_imports_W, \
           sum_electricity_imports_W, \
           sum_electricity_exports_W


def buildings_connected_costs_and_emissions(master_to_slave_vars,
                                            district_heating_costs,
                                            district_cooling_costs,
                                            district_microgrid_costs,
                                            district_microgrid_requirements_dispatch,
                                            district_heating_fuel_requirements_dispatch,
                                            district_cooling_fuel_requirements_dispatch,
                                            prices,
                                            lca
                                            ):
    # SUMMARIZE IMPORST AND EXPORTS
    sum_natural_gas_imports_W, \
    sum_wet_biomass_imports_W, \
    sum_dry_biomass_imports_W, \
    sum_electricity_imports_W, \
    sum_electricity_exports_W = summary_fuel_electricity_consumption(master_to_slave_vars,
                                                                     district_cooling_fuel_requirements_dispatch,
                                                                     district_heating_fuel_requirements_dispatch,
                                                                     district_microgrid_requirements_dispatch)

    # CALCULATE all_COSTS
    district_variable_costs = calc_variable_costs_connected_buildings(sum_natural_gas_imports_W,
                                                                      sum_wet_biomass_imports_W,
                                                                      sum_dry_biomass_imports_W,
                                                                      sum_electricity_imports_W,
                                                                      sum_electricity_exports_W,
                                                                      prices,
                                                                      lca)
    # join all the costs
    join1 = dict(district_heating_costs, **district_cooling_costs)
    join2 = dict(join1, **district_microgrid_costs)
    connected_costs = dict(join2, **district_variable_costs)

    # CALCULATE EMISSIONS
    connected_emissions = calc_emissions_connected_buildings(sum_natural_gas_imports_W,
                                                             sum_wet_biomass_imports_W,
                                                             sum_dry_biomass_imports_W,
                                                             sum_electricity_imports_W,
                                                             sum_electricity_exports_W,
                                                             lca)
    return connected_costs, connected_emissions


def calc_network_costs_cooling(locator, master_to_slave_vars, network_features, lca, network_type):
    # Intitialize class
    pipesCosts_USD = network_features.pipesCosts_DCN_USD
    num_buildings_connected = master_to_slave_vars.number_of_buildings_connected_cooling

    num_all_buildings = master_to_slave_vars.num_total_buildings
    ratio_connected = num_buildings_connected / num_all_buildings

    # Capital costs
    Inv_IR = 0.05
    Inv_LT = 20
    Inv_OM = 0.10
    Capex_Network_USD = pipesCosts_USD * ratio_connected
    Capex_a_Network_USD = Capex_Network_USD * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_Network_USD = Capex_Network_USD * Inv_OM

    # costs of pumps
    Capex_a_pump_USD, Opex_fixed_pump_USD, Opex_var_pump_USD, Capex_pump_USD, P_motor_tot_W = PumpModel.calc_Ctot_pump(
        master_to_slave_vars, network_features, locator, lca, network_type)

    # COOLING SUBSTATIONS
    DCN_barcode = master_to_slave_vars.DCN_barcode
    building_names = master_to_slave_vars.building_names_cooling
    Capex_Substations_USD, \
    Capex_a_Substations_USD, \
    Opex_fixed_Substations_USD, \
    Opex_var_Substations_USD = calc_substations_costs_cooling(building_names, master_to_slave_vars, DCN_barcode,
                                                              locator)

    # summarize
    Capex_Network_USD += Capex_pump_USD
    Capex_a_Network_USD += Capex_a_pump_USD
    Opex_fixed_Network_USD += Opex_fixed_pump_USD
    Opex_var_Network_USD = Opex_var_pump_USD

    performance = {
        'Capex_a_DCN_connected_USD': Capex_a_Network_USD,
        "Capex_a_SubstationsCooling_connected_USD": Capex_a_Substations_USD,

        "Capex_total_DCN_connected_USD": Capex_Network_USD,
        "Capex_total_SubstationsCooling_connected_USD": Capex_Substations_USD,

        "Opex_fixed_DCN_connected_USD": Opex_fixed_Network_USD,
        "Opex_fixed_SubstationsCooling_connected_USD": Opex_fixed_Substations_USD,

    }
    return performance, P_motor_tot_W


def calc_substations_costs_cooling(building_names, master_to_slave_vars, district_network_barcode, locator):
    Capex_Substations_USD = 0.0
    Capex_a_Substations_USD = 0.0
    Opex_fixed_Substations_USD = 0.0
    Opex_var_Substations_USD = 0.0  # it is asssumed as 0 in substations
    for (index, building_name) in zip(district_network_barcode, building_names):
        if index == "1":
            district_heating_network = master_to_slave_vars.DHN_exists
            if district_heating_network and master_to_slave_vars.WasteServersHeatRecovery == 1:
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


def calc_generation_costs_cooling_storage(locator,
                                          master_to_slave_variables,
                                          config,
                                          daily_storage):
    # STORAGE TANK
    if master_to_slave_variables.Storage_cooling_on == 1:
        V_tank_m3 = daily_storage.V_tank_M3
        Capex_a_Tank_USD, Opex_fixed_Tank_USD, Capex_Tank_USD = thermal_storage.calc_Cinv_storage(V_tank_m3, locator,
                                                                                                  config, 'TES2')
    else:
        Capex_a_Tank_USD = 0.0
        Opex_fixed_Tank_USD = 0.0
        Capex_Tank_USD = 0.0

    # PLOT RESULTS
    performance = {
        # annualized capex
        "Capex_a_DailyStorage_WS_connected_USD": Capex_a_Tank_USD,

        # total capex
        "Capex_total_DailyStorage_WS_connected_USD": Capex_Tank_USD,

        # opex fixed
        "Opex_fixed_DailyStorage_WS_connected_USD": Opex_fixed_Tank_USD,
    }

    return performance


def calc_generation_costs_cooling(locator,
                                  master_to_slave_variables,
                                  config,
                                  ):
    # TRIGENERATION
    if master_to_slave_variables.NG_Trigen_on == 1:
        Qc_ACH_nom_W = master_to_slave_variables.NG_Trigen_ACH_size_W
        Q_GT_nom_W = master_to_slave_variables.NG_Trigen_CCGT_size_W

        # ACH
        Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_ACH_nom_W, locator,
                                                                                              ACH_TYPE_DOUBLE)
        # CCGT
        Capex_a_CCGT_USD, Opex_fixed_CCGT_USD, Capex_CCGT_USD = cogeneration.calc_Cinv_CCGT(Q_GT_nom_W, locator, config)

        Capex_a_Trigen_NG_USD = Capex_a_ACH_USD + Capex_a_CCGT_USD
        Opex_fixed_Trigen_NG_USD = Opex_fixed_ACH_USD + Opex_fixed_CCGT_USD
        Capex_Trigen_NG_USD = Capex_ACH_USD + Capex_CCGT_USD
    else:
        Capex_a_Trigen_NG_USD = 0.0
        Opex_fixed_Trigen_NG_USD = 0.0
        Capex_Trigen_NG_USD = 0.0

    # WATER-SOURCE VAPOR COMPRESION CHILLER BASE
    if master_to_slave_variables.WS_BaseVCC_on == 1:
        Qc_VCC_nom_W = master_to_slave_variables.WS_BaseVCC_size_W
        # VCC
        Capex_a_BaseVCC_WS_USD, Opex_fixed_BaseVCC_WS_USD, Capex_BaseVCC_WS_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_nom_W,
                                                                                                         locator,
                                                                                                         config,
                                                                                                         'CH3')
    else:
        Capex_a_BaseVCC_WS_USD = 0.0
        Opex_fixed_BaseVCC_WS_USD = 0.0
        Capex_BaseVCC_WS_USD = 0.0

    # WATER-SOURCE VAPOR COMPRESION CHILLER PEAK
    if master_to_slave_variables.WS_PeakVCC_on == 1:
        Qc_VCC_nom_W = master_to_slave_variables.WS_PeakVCC_size_W
        # VCC
        Capex_a_PeakVCC_WS_USD, Opex_fixed_PeakVCC_WS_USD, Capex_PeakVCC_WS_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_nom_W,
                                                                                                         locator,
                                                                                                         config,
                                                                                                         'CH3')
    else:
        Capex_a_PeakVCC_WS_USD = 0.0
        Opex_fixed_PeakVCC_WS_USD = 0.0
        Capex_PeakVCC_WS_USD = 0.0

    # AIR-SOURCE VAPOR COMPRESION CHILLER BASE
    if master_to_slave_variables.AS_BaseVCC_on == 1:
        Qc_VCC_nom_W = master_to_slave_variables.AS_BaseVCC_size_W
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_nom_W, locator, config,
                                                                                    'CH3')

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Qc_VCC_nom_W, locator, 'CT1')

        Capex_a_BaseVCC_AS_USD = Capex_a_VCC_USD + Capex_a_CT_USD
        Opex_fixed_BaseVCC_AS_USD = Opex_fixed_VCC_USD + Opex_fixed_CT_USD
        Capex_BaseVCC_AS_USD = Capex_VCC_USD + Capex_CT_USD

    else:
        Capex_a_BaseVCC_AS_USD = 0.0
        Opex_fixed_BaseVCC_AS_USD = 0.0
        Capex_BaseVCC_AS_USD = 0.0

    # AIR-SOURCE VAPOR COMPRESION CHILLER PEAK
    if master_to_slave_variables.AS_PeakVCC_on == 1:
        Qc_VCC_nom_W = master_to_slave_variables.AS_PeakVCC_size_W
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_nom_W, locator, config,
                                                                                    'CH3')

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Qc_VCC_nom_W, locator, 'CT1')

        Capex_a_PeakVCC_AS_USD = Capex_a_VCC_USD + Capex_a_CT_USD
        Opex_fixed_PeakVCC_AS_USD = Opex_fixed_VCC_USD + Opex_fixed_CT_USD
        Capex_PeakVCC_AS_USD = Capex_VCC_USD + Capex_CT_USD


    else:
        Capex_a_PeakVCC_AS_USD = 0.0
        Opex_fixed_PeakVCC_AS_USD = 0.0
        Capex_PeakVCC_AS_USD = 0.0

    # AIR-SOURCE VCC BACK-UP
    if master_to_slave_variables.AS_BackupVCC_on == 1:
        Qc_VCC_nom_W = master_to_slave_variables.AS_BackupVCC_size_W
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Qc_VCC_nom_W, locator, config,
                                                                                    'CH3')

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Qc_VCC_nom_W, locator, 'CT1')

        Capex_a_BackupVCC_AS_USD = Capex_a_VCC_USD + Capex_a_CT_USD
        Opex_fixed_BackupVCC_AS_USD = Opex_fixed_VCC_USD + Opex_fixed_CT_USD
        Capex_BackupVCC_AS_USD = Capex_VCC_USD + Capex_CT_USD

    else:
        Capex_a_BackupVCC_AS_USD = 0.0
        Opex_fixed_BackupVCC_AS_USD = 0.0
        Capex_BackupVCC_AS_USD = 0.0

    # PLOT RESULTS
    performance = {
        # annualized capex
        "Capex_a_Trigen_NG_connected_USD": Capex_a_Trigen_NG_USD,
        "Capex_a_BaseVCC_WS_connected_USD": Capex_a_BaseVCC_WS_USD,
        "Capex_a_PeakVCC_WS_connected_USD": Capex_a_PeakVCC_WS_USD,
        "Capex_a_BaseVCC_AS_connected_USD": Capex_a_BaseVCC_AS_USD,
        "Capex_a_PeakVCC_AS_connected_USD": Capex_a_PeakVCC_AS_USD,
        "Capex_a_BackupVCC_AS_connected_USD": Capex_a_BackupVCC_AS_USD,

        # total capex
        "Capex_total_Trigen_NG_connected_USD": Capex_Trigen_NG_USD,
        "Capex_total_BaseVCC_WS_connected_USD": Capex_BaseVCC_WS_USD,
        "Capex_total_PeakVCC_WS_connected_USD": Capex_PeakVCC_WS_USD,
        "Capex_total_BaseVCC_AS_connected_USD": Capex_BaseVCC_AS_USD,
        "Capex_total_PeakVCC_AS_connected_USD": Capex_PeakVCC_AS_USD,
        "Capex_total_BackupVCC_AS_connected_USD": Capex_BackupVCC_AS_USD,

        # opex fixed
        "Opex_fixed_Trigen_NG_connected_USD": Opex_fixed_Trigen_NG_USD,
        "Opex_fixed_BaseVCC_WS_connected_USD": Opex_fixed_BaseVCC_WS_USD,
        "Opex_fixed_PeakVCC_WS_connected_USD": Opex_fixed_PeakVCC_WS_USD,
        "Opex_fixed_BaseVCC_AS_connected_USD": Opex_fixed_BaseVCC_AS_USD,
        "Opex_fixed_PeakVCC_AS_connected_USD": Opex_fixed_PeakVCC_AS_USD,
        "Opex_fixed_BackupVCC_AS_connected_USD": Opex_fixed_BackupVCC_AS_USD,
    }

    return performance


def calc_generation_costs_heating(locator,
                                  master_to_slave_vars,
                                  config,
                                  storage_activation_data,
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
    :type indCombi: string
    :type buildList: list
    :type locator: string
    :type master_to_slave_vars: class
    :type Q_uncovered_design_W: float
    :type Q_uncovered_annual_W: float
    :type solar_features: class
    :type thermal_network: class

    :return: returns the objectives addCosts, addCO2, addPrim
    :rtype: tuple
    """

    thermal_network = pd.read_csv(
        locator.get_optimization_thermal_network_data_file(master_to_slave_vars.network_data_file_heating))

    # CCGT
    if master_to_slave_vars.CC_on == 1:
        CC_size_W = master_to_slave_vars.CCGT_SIZE_W
        Capex_a_CHP_NG_USD, Opex_fixed_CHP_NG_USD, Capex_CHP_NG_USD = chp.calc_Cinv_CCGT(CC_size_W, locator, config)
    else:
        Capex_a_CHP_NG_USD = 0.0
        Opex_fixed_CHP_NG_USD = 0.0
        Capex_CHP_NG_USD = 0.0

    # DRY BIOMASS
    if master_to_slave_vars.Furnace_dry_on == 1:
        Dry_Furnace_size_W = master_to_slave_vars.DBFurnace_Q_max_W
        Capex_a_furnace_dry_USD, \
        Opex_fixed_furnace_dry_USD, \
        Capex_furnace_dry_USD = furnace.calc_Cinv_furnace(Dry_Furnace_size_W, locator, 'FU1')
    else:
        Capex_furnace_dry_USD = 0.0
        Capex_a_furnace_dry_USD = 0.0
        Opex_fixed_furnace_dry_USD = 0.0

    # WET BIOMASS
    if master_to_slave_vars.Furnace_wet_on == 1:
        Wet_Furnace_size_W = master_to_slave_vars.WBFurnace_Q_max_W
        Capex_a_furnace_wet_USD, \
        Opex_fixed_furnace_wet_USD, \
        Capex_furnace_wet_USD = furnace.calc_Cinv_furnace(Wet_Furnace_size_W, locator, 'FU1')
    else:
        Capex_a_furnace_wet_USD = 0.0
        Opex_fixed_furnace_wet_USD = 0.0
        Capex_furnace_wet_USD = 0.0

    # BOILER BASE LOAD
    if master_to_slave_vars.Boiler_on == 1:
        Q_design_W = master_to_slave_vars.Boiler_Q_max_W
        Capex_a_BaseBoiler_NG_USD, \
        Opex_fixed_BaseBoiler_NG_USD, \
        Capex_BaseBoiler_NG_USD = boiler.calc_Cinv_boiler(Q_design_W, locator, config, 'BO1')
    else:
        Capex_a_BaseBoiler_NG_USD = 0.0
        Opex_fixed_BaseBoiler_NG_USD = 0.0
        Capex_BaseBoiler_NG_USD = 0.0

    # BOILER PEAK LOAD
    if master_to_slave_vars.BoilerPeak_on == 1:
        Q_design_W = master_to_slave_vars.BoilerPeak_Q_max_W
        Capex_a_PeakBoiler_NG_USD, \
        Opex_fixed_PeakBoiler_NG_USD, \
        Capex_PeakBoiler_NG_USD = boiler.calc_Cinv_boiler(Q_design_W, locator, config, 'BO1')
    else:
        Capex_a_PeakBoiler_NG_USD = 0.0
        Opex_fixed_PeakBoiler_NG_USD = 0.0
        Capex_PeakBoiler_NG_USD = 0.0

    # HEATPUMP LAKE
    if master_to_slave_vars.HPLake_on == 1:
        HP_Size_W = master_to_slave_vars.HPLake_maxSize_W
        Capex_a_Lake_USD, \
        Opex_fixed_Lake_USD, \
        Capex_Lake_USD = hp.calc_Cinv_HP(HP_Size_W, locator, 'HP2')
    else:
        Capex_a_Lake_USD = 0.0
        Opex_fixed_Lake_USD = 0.0
        Capex_Lake_USD = 0.0

    # HEATPUMP_SEWAGE
    if master_to_slave_vars.HPSew_on == 1:
        HP_Size_W = master_to_slave_vars.HPSew_maxSize_W
        Capex_a_Sewage_USD, \
        Opex_fixed_Sewage_USD, \
        Capex_Sewage_USD = hp.calc_Cinv_HP(HP_Size_W, locator, 'HP2')
    else:
        Capex_a_Sewage_USD = 0.0
        Opex_fixed_Sewage_USD = 0.0
        Capex_Sewage_USD = 0.0

    # GROUND HEAT PUMP
    if master_to_slave_vars.GHP_on == 1:
        GHP_Enom_W = master_to_slave_vars.GHP_maxSize_W
        Capex_a_GHP_USD, \
        Opex_fixed_GHP_USD, \
        Capex_GHP_USD = hp.calc_Cinv_GHP(GHP_Enom_W, locator, config)
    else:
        Capex_a_GHP_USD = 0.0
        Opex_fixed_GHP_USD = 0.0
        Capex_GHP_USD = 0.0

    # BACK-UP BOILER
    if master_to_slave_vars.BackupBoiler_on != 0:
        Q_backup_W = master_to_slave_vars.BackupBoiler_size_W
        Capex_a_BackupBoiler_NG_USD, \
        Opex_fixed_BackupBoiler_NG_USD, \
        Capex_BackupBoiler_NG_USD = boiler.calc_Cinv_boiler(Q_backup_W, locator, config, 'BO1')
    else:
        Capex_a_BackupBoiler_NG_USD = 0.0
        Opex_fixed_BackupBoiler_NG_USD = 0.0
        Capex_BackupBoiler_NG_USD = 0.0

    # DATA CENTRE SOURCE HEAT PUMP
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        Q_HEX_max_Wh = thermal_network["Qcdata_netw_total_kWh"].max() * 1000  # convert to Wh
        Capex_a_wasteserver_HEX_USD, Opex_fixed_wasteserver_HEX_USD, Capex_wasteserver_HEX_USD = hex.calc_Cinv_HEX(
            Q_HEX_max_Wh, locator, config, 'HEX1')

        Q_HP_max_Wh = storage_activation_data["Q_HP_Server_W"].max()
        Capex_a_wasteserver_HP_USD, Opex_fixed_wasteserver_HP_USD, Capex_wasteserver_HP_USD = hp.calc_Cinv_HP(
            Q_HP_max_Wh, locator, 'HP2')
    else:
        Capex_a_wasteserver_HEX_USD = 0.0
        Opex_fixed_wasteserver_HEX_USD = 0.0
        Capex_wasteserver_HEX_USD = 0.0
        Capex_a_wasteserver_HP_USD = 0.0
        Opex_fixed_wasteserver_HP_USD = 0.0
        Capex_wasteserver_HP_USD = 0.0

    # SOLAR TECHNOLOGIES
    # ADD COSTS AND EMISSIONS DUE TO SOLAR TECHNOLOGIES
    SC_ET_area_m2 = master_to_slave_vars.A_SC_ET_m2
    Capex_a_SC_ET_USD, \
    Opex_fixed_SC_ET_USD, \
    Capex_SC_ET_USD = stc.calc_Cinv_SC(SC_ET_area_m2, locator,
                                       'ET')

    SC_FP_area_m2 = master_to_slave_vars.A_SC_FP_m2
    Capex_a_SC_FP_USD, \
    Opex_fixed_SC_FP_USD, \
    Capex_SC_FP_USD = stc.calc_Cinv_SC(SC_FP_area_m2, locator,
                                       'FP')

    PVT_peak_kW = master_to_slave_vars.A_PVT_m2 * N_PVT  # kW
    Capex_a_PVT_USD, \
    Opex_fixed_PVT_USD, \
    Capex_PVT_USD = pvt.calc_Cinv_PVT(PVT_peak_kW, locator, config)

    # HEATPUMP FOR SOLAR UPGRADE TO DISTRICT HEATING
    Q_HP_max_PVT_wh = storage_activation_data["Q_HP_PVT_W"].max()
    Capex_a_HP_PVT_USD, \
    Opex_fixed_HP_PVT_USD, \
    Capex_HP_PVT_USD = hp.calc_Cinv_HP(Q_HP_max_PVT_wh, locator, 'HP2')

    # hack split into two technologies
    Q_HP_max_SC_ET_Wh = storage_activation_data["Q_HP_SC_ET_W"].max()
    Capex_a_HP_SC_ET_USD, \
    Opex_fixed_HP_SC_ET_USD, \
    Capex_HP_SC_ET_USD = hp.calc_Cinv_HP(Q_HP_max_SC_ET_Wh, locator, 'HP2')

    Q_HP_max_SC_FP_Wh = storage_activation_data["Q_HP_SC_FP_W"].max()
    Capex_a_HP_SC_FP_USD, \
    Opex_fixed_HP_SC_FP_USD, \
    Capex_HP_SC_FP_USD = hp.calc_Cinv_HP(Q_HP_max_SC_FP_Wh, locator, 'HP2')

    # HEAT EXCHANGER FOR SOLAR COLLECTORS
    Q_max_SC_ET_Wh = (storage_activation_data["Q_SC_ET_gen_directload_W"] +
                      storage_activation_data["Q_SC_ET_gen_storage_W"]).max()
    Capex_a_HEX_SC_ET_USD, \
    Opex_fixed_HEX_SC_ET_USD, \
    Capex_HEX_SC_ET_USD = hex.calc_Cinv_HEX(Q_max_SC_ET_Wh, locator, config, 'HEX1')

    Q_max_SC_FP_Wh = (storage_activation_data["Q_SC_FP_gen_directload_W"] +
                      storage_activation_data["Q_SC_FP_gen_storage_W"]).max()
    Capex_a_HEX_SC_FP_USD, \
    Opex_fixed_HEX_SC_FP_USD, \
    Capex_HEX_SC_FP_USD = hex.calc_Cinv_HEX(Q_max_SC_FP_Wh, locator, config, 'HEX1')

    Q_max_PVT_Wh = (storage_activation_data["Q_PVT_gen_directload_W"] +
                    storage_activation_data["Q_PVT_gen_storage_W"]).max()
    Capex_a_HEX_PVT_USD, \
    Opex_fixed_HEX_PVT_USD, \
    Capex_HEX_PVT_USD = hex.calc_Cinv_HEX(Q_max_PVT_Wh, locator, config, 'HEX1')

    performance_costs = {
        "Capex_a_SC_ET_connected_USD": Capex_a_SC_ET_USD + Capex_a_HP_SC_ET_USD + Capex_a_HEX_SC_ET_USD,
        "Capex_a_SC_FP_connected_USD": Capex_a_SC_FP_USD + Capex_a_HP_SC_FP_USD + Capex_a_HEX_SC_FP_USD,
        "Capex_a_PVT_connected_USD": Capex_a_PVT_USD + Capex_a_HP_PVT_USD + Capex_a_HEX_PVT_USD,
        "Capex_a_HP_Server_connected_USD": Capex_a_wasteserver_HP_USD + Capex_a_wasteserver_HEX_USD,
        "Capex_a_HP_Sewage_connected_USD": Capex_a_Sewage_USD,
        "Capex_a_HP_Lake_connected_USD": Capex_a_Lake_USD,
        "Capex_a_GHP_connected_USD": Capex_a_GHP_USD,
        "Capex_a_CHP_NG_connected_USD": Capex_a_CHP_NG_USD,
        "Capex_a_Furnace_wet_connected_USD": Capex_a_furnace_wet_USD,
        "Capex_a_Furnace_dry_connected_USD": Capex_a_furnace_dry_USD,
        "Capex_a_BaseBoiler_NG_connected_USD": Capex_a_BaseBoiler_NG_USD,
        "Capex_a_PeakBoiler_NG_connected_USD": Capex_a_PeakBoiler_NG_USD,
        "Capex_a_BackupBoiler_NG_connected_USD": Capex_a_BackupBoiler_NG_USD,

        # total_capex
        "Capex_total_SC_ET_connected_USD": Capex_SC_ET_USD + Capex_HP_SC_ET_USD + Capex_HEX_SC_ET_USD,
        "Capex_total_SC_FP_connected_USD": Capex_SC_FP_USD + Capex_HP_SC_FP_USD + Capex_HEX_SC_FP_USD,
        "Capex_total_PVT_connected_USD": Capex_PVT_USD + Capex_HP_PVT_USD + Capex_HEX_PVT_USD,
        "Capex_total_HP_Server_connected_USD": Capex_wasteserver_HP_USD + Capex_wasteserver_HEX_USD,
        "Capex_total_HP_Sewage_connected_USD": Capex_Sewage_USD,
        "Capex_total_HP_Lake_connected_USD": Capex_Lake_USD,
        "Capex_total_GHP_connected_USD": Capex_GHP_USD,
        "Capex_total_CHP_NG_connected_USD": Capex_CHP_NG_USD,
        "Capex_total_Furnace_wet_connected_USD": Capex_furnace_wet_USD,
        "Capex_total_Furnace_dry_connected_USD": Capex_furnace_dry_USD,
        "Capex_total_BaseBoiler_NG_connected_USD": Capex_BaseBoiler_NG_USD,
        "Capex_total_PeakBoiler_NG_connected_USD": Capex_PeakBoiler_NG_USD,
        "Capex_total_BackupBoiler_NG_connected_USD": Capex_BackupBoiler_NG_USD,

        # opex fixed costs
        "Opex_fixed_SC_ET_connected_USD": Opex_fixed_SC_ET_USD,
        "Opex_fixed_SC_FP_connected_USD": Opex_fixed_SC_FP_USD,
        "Opex_fixed_PVT_connected_USD": Opex_fixed_PVT_USD,
        "Opex_fixed_HP_Server_connected_USD": Opex_fixed_wasteserver_HP_USD + Opex_fixed_wasteserver_HEX_USD,
        "Opex_fixed_HP_Sewage_connected_USD": Opex_fixed_Sewage_USD,
        "Opex_fixed_HP_Lake_connected_USD": Opex_fixed_Lake_USD,
        "Opex_fixed_GHP_connected_USD": Opex_fixed_GHP_USD,
        "Opex_fixed_CHP_NG_connected_USD": Opex_fixed_CHP_NG_USD,
        "Opex_fixed_Furnace_wet_connected_USD": Opex_fixed_furnace_wet_USD,
        "Opex_fixed_Furnace_dry_connected_USD": Opex_fixed_furnace_dry_USD,
        "Opex_fixed_BaseBoiler_NG_connected_USD": Opex_fixed_BaseBoiler_NG_USD,
        "Opex_fixed_PeakBoiler_NG_connected_USD": Opex_fixed_PeakBoiler_NG_USD,
        "Opex_fixed_BackupBoiler_NG_connected_USD": Opex_fixed_BackupBoiler_NG_USD,
    }

    return performance_costs


def calc_costs_emissions_decentralized_DC(DCN_barcode, buildings_names_with_cooling_load, locator,
                                          ):
    GHG_sys_disconnected_tonCO2yr = 0.0
    Capex_a_sys_disconnected_USD = 0.0
    CostDiscBuild = 0.0
    Opex_var_sys_disconnected = 0.0
    PEN_sys_disconnected_MJoilyr = 0.0
    Capex_total_sys_disconnected_USD = 0.0
    Opex_fixed_sys_disconnected_USD = 0.0
    for (index, building_name) in zip(DCN_barcode, buildings_names_with_cooling_load):
        if index == "0":  # choose the best decentralized configuration
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_name,
                                                                                                   configuration='AHU_ARU_SCU'))
            dfBest = df[df["Best configuration"] == 1]
            GHG_sys_disconnected_tonCO2yr += dfBest["GHG_tonCO2"].iloc[0]  # [ton CO2]
            PEN_sys_disconnected_MJoilyr += dfBest["PEN_MJoil"].iloc[0]  # [MJ-oil-eq]
            Capex_total_sys_disconnected_USD += dfBest["Capex_total_USD"].iloc[0]
            Capex_a_sys_disconnected_USD += dfBest["Capex_a_USD"].iloc[0]
            Opex_var_sys_disconnected += dfBest["Opex_a_var_USD"].iloc[0]
            Opex_fixed_sys_disconnected_USD += dfBest["Opex_a_fixed_USD"].iloc[0]
    return GHG_sys_disconnected_tonCO2yr, \
           PEN_sys_disconnected_MJoilyr, \
           Capex_total_sys_disconnected_USD, \
           Capex_a_sys_disconnected_USD, \
           Opex_var_sys_disconnected, \
           Opex_fixed_sys_disconnected_USD


def calc_costs_emissions_decentralized_DH(DHN_barcode, buildings_names_with_heating_load, locator):
    GHG_sys_disconnected_tonCO2yr = 0.0
    Capex_a_sys_disconnected_USD = 0.0
    CostDiscBuild = 0.0
    Opex_var_sys_disconnected = 0.0
    PEN_sys_disconnected_MJoilyr = 0.0
    Capex_total_sys_disconnected_USD = 0.0
    Opex_fixed_sys_disconnected_USD = 0.0
    for (index, building_name) in zip(DHN_barcode, buildings_names_with_heating_load):
        if index == "0":
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_heating(building_name))
            dfBest = df[df["Best configuration"] == 1]
            CostDiscBuild += dfBest["TAC_USD"].iloc[0]  # [USD]
            GHG_sys_disconnected_tonCO2yr += dfBest["GHG_tonCO2"].iloc[0]  # [ton CO2]
            PEN_sys_disconnected_MJoilyr += dfBest["PEN_MJoil"].iloc[0]  # [MJ-oil-eq]
            Capex_total_sys_disconnected_USD += dfBest["Capex_total_USD"].iloc[0]
            Capex_a_sys_disconnected_USD += dfBest["Capex_a_USD"].iloc[0]
            Opex_var_sys_disconnected += dfBest["Opex_a_var_USD"].iloc[0]
            Opex_fixed_sys_disconnected_USD += dfBest["Opex_a_fixed_USD"].iloc[0]

    return GHG_sys_disconnected_tonCO2yr, \
           PEN_sys_disconnected_MJoilyr, \
           Capex_total_sys_disconnected_USD, \
           Capex_a_sys_disconnected_USD, \
           Opex_var_sys_disconnected, \
           Opex_fixed_sys_disconnected_USD
