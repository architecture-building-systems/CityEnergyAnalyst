# -*- coding: utf-8 -*-
"""
Extra costs to an individual

"""




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
from cea.optimization.constants import N_PVT, ACH_TYPE_DOUBLE, N_SC_ET, N_SC_FP
from cea.optimization.constants import VCC_CODE_CENTRALIZED
from cea.optimization.master.emissions_model import calc_emissions_Whyr_to_tonCO2yr
from cea.technologies.pumps import calc_Cinv_pump
from cea.technologies.supply_systems_database import SupplySystemsDatabase
from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def buildings_building_scale_objective_functions(column_names_buildings_heating,
                                                 column_names_buildings_cooling, locator, master_to_slave_vars):
    """
    Computes costs & GHG emissions for the individual.
    If the optimisation looks for the ideal DC network primary energy needs & anthropogenic heat release are also calculated.

    :param list column_names_buildings_heating: names of buildings with a positive heating demand
    :param list column_names_buildings_cooling: names of buildings with a positive cooling demand
    :param locator: input locator set to scenario
    :param master_to_slave_vars: class containing the features of a specific individual
    :type locator: cea.inputlocator.InputLocator class object
    :type master_to_slave_vars: cea.optimization.slave_data.SlaveData class object

    :return dict disconnected_costs: costs of heating and cooling systems of disconnected buildings (acc. to individual)
    :return dict disconnected_emissions: GHG emissions of heating and cooling systems of disconnected buildings (acc. to individual)
    :return dict disconnected_heat_rejection: (anthropogenic) heat rejection of cooling systems of disconnected buildings (acc. to individual)
    :return dict disconnected_system_energy_demand: system energy demand of cooling system of disconnected buildings (acc. to individual)
    :return DataFrame capacity_installed_heating_sys_df: capacities of heating system components installed in disconnected buildings (acc. to individual)
    :return DataFrame capacity_installed_cooling_sys_df: capacities of cooling system components installed in disconnected buildings (acc. to individual)
    """
    DHN_barcode = master_to_slave_vars.DHN_barcode
    DCN_barcode = master_to_slave_vars.DCN_barcode

    # DISCONNECTED BUILDINGS  - HEATING LOADS
    GHG_heating_sys_building_scale_tonCO2yr, \
    Capex_total_heating_sys_building_scale_USD, \
    Capex_a_heating_sys_building_scale_USD, \
    Opex_var_heating_sys_disconnected, \
    Opex_fixed_heating_sys_building_scale_USD, \
    capacity_installed_heating_sys_df = calc_costs_emissions_decentralized_DH(DHN_barcode,
                                                                              column_names_buildings_heating,
                                                                              locator)

    # DISCONNECTED BUILDINGS - COOLING LOADS
    GHG_cooling_sys_building_scale_tonCO2yr, \
    Capex_total_cooling_sys_building_scale_USD, \
    Capex_a_cooling_sys_building_scale_USD, \
    Opex_var_cooling_sys_disconnected, \
    Opex_fixed_cooling_sys_building_scale_USD, \
    Qh_sys_release_Wh, \
    NG_sys_req_Wh, \
    E_sys_req_Wh, \
    capacity_installed_cooling_sys_df = calc_objective_functions_decentralized_DC(DCN_barcode,
                                                                                  column_names_buildings_cooling,
                                                                                  locator)

    disconnected_costs = {
        # heating
        "Capex_a_heating_building_scale_USD": Capex_a_heating_sys_building_scale_USD,
        "Capex_total_heating_building_scale_USD": Capex_total_heating_sys_building_scale_USD,
        "Opex_var_heating_building_scale_USD": Opex_var_heating_sys_disconnected,
        "Opex_fixed_heating_building_scale_USD": Opex_fixed_heating_sys_building_scale_USD,
        # cooling
        "Capex_a_cooling_building_scale_USD": Capex_a_cooling_sys_building_scale_USD,
        "Capex_total_cooling_building_scale_USD": Capex_total_cooling_sys_building_scale_USD,
        "Opex_var_cooling_building_scale_USD": Opex_var_cooling_sys_disconnected,
        "Opex_fixed_cooling_building_scale_USD": Opex_fixed_cooling_sys_building_scale_USD,
    }

    disconnected_emissions = {
        # CO2 EMISSIONS
        "GHG_heating_building_scale_tonCO2": GHG_heating_sys_building_scale_tonCO2yr,
        "GHG_cooling_building_scale_tonCO2": GHG_cooling_sys_building_scale_tonCO2yr,
    }

    disconnected_heat_rejection = {
        # rejected (anthropogenic) heat from cooling systems
        "DC_HR_cooling_building_scale_Wh": Qh_sys_release_Wh,
    }

    disconnected_system_energy_demand = {
        # energy demand of cooling system
        "SED_NG_cooling_building_scale_Wh": NG_sys_req_Wh,
        "SED_E_cooling_building_scale_Wh": E_sys_req_Wh,
    }

    return disconnected_costs, disconnected_emissions, \
           disconnected_heat_rejection, disconnected_system_energy_demand, \
           capacity_installed_heating_sys_df, capacity_installed_cooling_sys_df


def calc_network_costs_heating(locator, master_to_slave_vars, network_features, network_type):
    """
    Returns the costs of the district heating network as well as the capacity of the pumps installed in the network.

    :param locator: input locator set to scenario
    :param master_to_slave_vars: class containing the features of a specific individual
    :param network_features: description of the thermal network (pumping energy, pipeCosts, thermal losses)
    :param string network_type: code describing which type of network is processed
    :type locator: cea.inputlocator.InputLocator class object
    :type master_to_slave_vars: cea.optimization.slave_data.SlaveData class object
    :type network_features: cea.optimization.distribution.network_optimization_features.NetworkOptimizationFeatures class object

    :return dict performance: Costs of district heating network
    :return float64 P_motor_tot_W: Power of pumps installed in the network
    """

    # Initialize class
    pipesCosts_USD = network_features.pipesCosts_DHN_USD
    num_buildings_connected = master_to_slave_vars.number_of_buildings_district_scale_heating

    num_all_buildings = master_to_slave_vars.num_total_buildings
    ratio_connected = num_buildings_connected / num_all_buildings

    # Capital costs
    Inv_IR_percent = 5
    Inv_LT_yr = 20
    Inv_OM = 0.10
    Capex_Network_USD = pipesCosts_USD * ratio_connected
    Capex_a_Network_USD = calc_capex_annualized(Capex_Network_USD, Inv_IR_percent, Inv_LT_yr)
    Opex_fixed_Network_USD = Capex_Network_USD * Inv_OM

    # costs of pumps
    Capex_a_pump_USD, \
    Opex_fixed_pump_USD, \
    Capex_pump_USD, \
    P_motor_tot_W = PumpModel.calc_Ctot_pump(master_to_slave_vars,
                                             network_features,
                                             locator,
                                             network_type)

    # summarize
    Capex_Network_USD += Capex_pump_USD
    Capex_a_Network_USD += Capex_a_pump_USD
    Opex_fixed_Network_USD += Opex_fixed_pump_USD

    # CAPEX AND OPEX OF HEATING SUBSTATIONS
    DHN_barcode = master_to_slave_vars.DHN_barcode
    building_names = master_to_slave_vars.building_names_heating
    Capex_SubstationsHeating_USD, \
    Capex_a_SubstationsHeating_USD, \
    Opex_fixed_SubstationsHeating_USD = calc_substations_costs_heating(building_names, DHN_barcode,
                                                                       locator)

    performance = {
        'Capex_a_DHN_district_scale_USD': Capex_a_Network_USD,
        "Capex_a_SubstationsHeating_district_scale_USD": Capex_a_SubstationsHeating_USD,

        "Capex_total_DHN_district_scale_USD": Capex_Network_USD,
        "Capex_total_SubstationsHeating_district_scale_USD": Capex_SubstationsHeating_USD,

        "Opex_fixed_DHN_district_scale_USD": Opex_fixed_Network_USD,
        "Opex_fixed_SubstationsHeating_district_scale_USD": Opex_fixed_SubstationsHeating_USD,
    }
    return performance, P_motor_tot_W


def calc_substations_costs_heating(building_names, district_network_barcode, locator):
    Capex_Substations_USD = 0.0
    Capex_a_Substations_USD = 0.0
    Opex_fixed_Substations_USD = 0.0
    for (index, building_name) in zip(district_network_barcode, building_names):
        if index == "1":
            df = pd.read_csv(
                locator.get_optimization_substations_results_file(building_name, "DH", district_network_barcode),
                usecols=["Q_dhw_W", "Q_heating_W"])

            subsArray = np.array(df)
            Q_max_W = np.amax(subsArray[:, 0] + subsArray[:, 1])
            HEX_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="HEX")
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
            Inv_IR = HEX_cost_data.iloc[0]['IR_%']
            Inv_LT = HEX_cost_data.iloc[0]['LT_yr']
            Inv_OM = HEX_cost_data.iloc[0]['O&M_%'] / 100

            Capex_total_USD = Inv_a + Inv_b * (Q_max_W) ** Inv_c + (Inv_d + Inv_e * Q_max_W) * log(Q_max_W)
            Capex_a_USD = calc_capex_annualized(Capex_total_USD, Inv_IR, Inv_LT)
            Opex_fixed_USD = Capex_total_USD * Inv_OM

            Capex_Substations_USD += Capex_total_USD
            Capex_a_Substations_USD += Capex_a_USD
            Opex_fixed_Substations_USD += Opex_fixed_USD

    return Capex_Substations_USD, Capex_a_Substations_USD, Opex_fixed_Substations_USD


def calc_variable_costs_district_scale_buildings(sum_natural_gas_imports_W,
                                                 sum_wet_biomass_imports_W,
                                                 sum_dry_biomass_imports_W,
                                                 sum_electricity_imports_W,
                                                 sum_electricity_exports_W,
                                                 prices,
                                                 ):
    # COSTS
    Opex_var_NG_sys_district_scale_USD = sum(sum_natural_gas_imports_W * prices.NG_PRICE)
    Opex_var_WB_sys_district_scale_USD = sum(sum_wet_biomass_imports_W * prices.WB_PRICE)
    Opex_var_DB_sys_district_scale_USD = sum(sum_dry_biomass_imports_W * prices.DB_PRICE)
    Opex_var_GRID_buy_sys_district_scale_USD = sum(sum_electricity_imports_W * prices.ELEC_PRICE)
    Opex_var_GRID_sell_sys_district_scale_USD = -sum(sum_electricity_exports_W * prices.ELEC_PRICE_EXPORT)

    district_variable_costs = {
        "Opex_var_NG_district_scale_USD": Opex_var_NG_sys_district_scale_USD,
        "Opex_var_WB_district_scale_USD": Opex_var_WB_sys_district_scale_USD,
        "Opex_var_DB_district_scale_USD": Opex_var_DB_sys_district_scale_USD,
        "Opex_var_GRID_imports_district_scale_USD": Opex_var_GRID_buy_sys_district_scale_USD,
        "Opex_var_GRID_exports_district_scale_USD": Opex_var_GRID_sell_sys_district_scale_USD
    }

    return district_variable_costs


def calc_emissions_district_scale_buildings(sum_natural_gas_imports_W,
                                            sum_wet_biomass_imports_W,
                                            sum_dry_biomass_imports_W,
                                            sum_electricity_imports_W,
                                            sum_electricity_exports_W,
                                            lca):
    # SUMMARIZE
    GHG_NG_district_scale_tonCO2yr = sum(calc_emissions_Whyr_to_tonCO2yr(sum_natural_gas_imports_W, lca.NG_TO_CO2_EQ))
    GHG_WB_district_scale_tonCO2yr = sum(calc_emissions_Whyr_to_tonCO2yr(sum_wet_biomass_imports_W, lca.WETBIOMASS_TO_CO2_EQ))
    GHG_DB_district_scale_tonCO2yr = sum(calc_emissions_Whyr_to_tonCO2yr(sum_dry_biomass_imports_W, lca.DRYBIOMASS_TO_CO2_EQ))
    GHG_GRID_imports_district_scale_tonCO2yr = sum(calc_emissions_Whyr_to_tonCO2yr(sum_electricity_imports_W, lca.EL_TO_CO2_EQ))
    GHG_GRID_exports_district_scale_tonCO2yr = - sum(calc_emissions_Whyr_to_tonCO2yr(sum_electricity_exports_W, lca.EL_TO_CO2_EQ))

    buildings_district_scale_emissions_primary_energy = {
        "GHG_NG_district_scale_tonCO2yr": GHG_NG_district_scale_tonCO2yr,
        "GHG_WB_district_scale_tonCO2yr": GHG_WB_district_scale_tonCO2yr,
        "GHG_DB_district_scale_tonCO2yr": GHG_DB_district_scale_tonCO2yr,
        "GHG_GRID_imports_district_scale_tonCO2yr": GHG_GRID_imports_district_scale_tonCO2yr,
        "GHG_GRID_exports_district_scale_tonCO2yr": GHG_GRID_exports_district_scale_tonCO2yr,
    }

    return buildings_district_scale_emissions_primary_energy


def calc_heat_release_district_scale_buildings(district_cooling_heat_release):

    # SUMMARIZE
    district_cooling_sensible_heat_release_W = sum(district_cooling_heat_release['Q_release_Trigen_NG_W'])
    district_cooling_latent_heat_release_W = (sum(district_cooling_heat_release['Q_release_BaseVCC_WS_W']) +
                                              sum(district_cooling_heat_release['Q_release_PeakVCC_WS_W']) +
                                              sum(district_cooling_heat_release['Q_release_FreeCooling_W']) +
                                              sum(district_cooling_heat_release['Q_release_BaseVCC_AS_W']) +
                                              sum(district_cooling_heat_release['Q_release_PeakVCC_AS_W']) +
                                              sum(district_cooling_heat_release['Q_release_BackupVCC_AS_W']))

    district_cooling_heat_release_summary = {"DC_HR_sensible_district_scale_Wh": district_cooling_sensible_heat_release_W,
                                             "DC_HR_latent_district_scale_Wh": district_cooling_latent_heat_release_W}

    return district_cooling_heat_release_summary


def calc_system_energy_demand_district_scale_buildings(sum_natural_gas_imports_W,
                                                       sum_wet_biomass_imports_W,
                                                       sum_dry_biomass_imports_W,
                                                       sum_electricity_imports_W,
                                                       sum_electricity_exports_W):

    # SUMMARIZE
    SED_natural_gas_W = sum(sum_natural_gas_imports_W)
    SED_wet_biomass_W = sum(sum_wet_biomass_imports_W)
    SED_dry_biomass_W = sum(sum_dry_biomass_imports_W)
    SED_electricity_W = sum(sum_electricity_imports_W) - sum(sum_electricity_exports_W)

    district_system_energy_demand = {"SED_natural_gas_district_scale_Wh": SED_natural_gas_W,
                                     "SED_wet_biomass_district_scale_Wh": SED_wet_biomass_W,
                                     "SED_dry_biomass_district_scale_Wh": SED_dry_biomass_W,
                                     "SED_electricity_district_scale_Wh": SED_electricity_W}

    return district_system_energy_demand


def summary_fuel_electricity_consumption(district_cooling_fuel_requirements_dispatch,
                                         district_heating_fuel_requirements_dispatch,
                                         district_microgrid_requirements_dispatch,
                                         district_electricity_demands):
    # join in one dictionary to facilitate the iteration
    join1 = dict(district_microgrid_requirements_dispatch, **district_heating_fuel_requirements_dispatch)
    data = dict(join1, **district_cooling_fuel_requirements_dispatch)
    # Iterate over all the files
    sum_natural_gas_imports_W = (data['NG_CHP_req_W'] +
                                 data['NG_BaseBoiler_req_W'] +
                                 data['NG_PeakBoiler_req_W'] +
                                 data['NG_BackupBoiler_req_W'] +
                                 data['NG_Trigen_req_W'])

    sum_wet_biomass_imports_W = data['WB_Furnace_req_W']

    sum_dry_biomass_imports_W = data['DB_Furnace_req_W']

    # discount those of disconnected buildings (which are part of the directload
    # dispatch, this is only for calculation of emissions purposes
    # it avoids double counting when calculating emissions due to decentralized buildings)
    sum_electricity_imports_W = (data['E_GRID_directload_W'] -
                                 district_electricity_demands['E_hs_ww_req_building_scale_W'] -
                                 district_electricity_demands['E_cs_cre_cdata_req_building_scale_W'])

    sum_electricity_exports_W = (data['E_CHP_gen_export_W'] +
                                 data['E_Furnace_dry_gen_export_W'] +
                                 data['E_Furnace_wet_gen_export_W'] +
                                 data['E_PV_gen_export_W'] +
                                 data['E_PVT_gen_export_W'] +
                                 data['E_Trigen_gen_export_W'])

    return sum_natural_gas_imports_W, \
           sum_wet_biomass_imports_W, \
           sum_dry_biomass_imports_W, \
           sum_electricity_imports_W, \
           sum_electricity_exports_W


def buildings_district_scale_objective_functions(district_heating_costs,
                                                 district_cooling_costs,
                                                 district_microgrid_costs,
                                                 district_microgrid_requirements_dispatch,
                                                 district_heating_fuel_requirements_dispatch,
                                                 district_cooling_fuel_requirements_dispatch,
                                                 district_electricity_demands,
                                                 district_cooling_heat_release,
                                                 prices,
                                                 lca
                                                 ):
    """
    Returns the objective function values for the connected centralised thermal energy systems (DC/DH-substation + network)
    according to the investigated individual.

    :param dict district_heating_costs: cost of components and operation in district heating system
    :param dict district_cooling_costs: cost of components and operation in district cooling system
    :param dict district_microgrid_costs: costs of microgrid and PV of centralised thermal energy systems
    :param dict district_microgrid_requirements_dispatch: electricity demand and generation of centralised thermal energy systems
    :param dict district_heating_fuel_requirements_dispatch: fuel demand of district heating system
    :param dict district_cooling_fuel_requirements_dispatch: fuel demand of district cooling system
    :param dict district_electricity_demands: electricity demand of centralised thermal energy systems
    :param dict district_cooling_heat_release: (anthropogenic) heat release of district cooling system
    :param prices: prices of available energy carriers (electricity, gas, wood, dry biomass ...)
    :param lca: emission intensities of fuels
    :type prices: cea.optimization.prices.Prices class object
    :type lca: cea.optimization.lca_calculations.LcaCalculations class object

    :return connected_costs, connected_emissions, connected_heat_release, connected_system_energy_demand
    """
    # SUMMARIZE IMPORTS AND EXPORTS
    sum_natural_gas_imports_W, \
    sum_wet_biomass_imports_W, \
    sum_dry_biomass_imports_W, \
    sum_electricity_imports_W, \
    sum_electricity_exports_W = summary_fuel_electricity_consumption(district_cooling_fuel_requirements_dispatch,
                                                                     district_heating_fuel_requirements_dispatch,
                                                                     district_microgrid_requirements_dispatch,
                                                                     district_electricity_demands)

    # CALCULATE all_COSTS
    district_variable_costs = calc_variable_costs_district_scale_buildings(sum_natural_gas_imports_W,
                                                                           sum_wet_biomass_imports_W,
                                                                           sum_dry_biomass_imports_W,
                                                                           sum_electricity_imports_W,
                                                                           sum_electricity_exports_W,
                                                                           prices,
                                                                           )
    # join all the costs
    join1 = dict(district_heating_costs, **district_cooling_costs)
    join2 = dict(join1, **district_microgrid_costs)
    connected_costs = dict(join2, **district_variable_costs)

    # CALCULATE EMISSIONS
    connected_emissions = calc_emissions_district_scale_buildings(sum_natural_gas_imports_W,
                                                                  sum_wet_biomass_imports_W,
                                                                  sum_dry_biomass_imports_W,
                                                                  sum_electricity_imports_W,
                                                                  sum_electricity_exports_W,
                                                                  lca)

    # CALCULATE (ANTHROPOGENIC) HEAT RELEASE
    connected_heat_release = calc_heat_release_district_scale_buildings(district_cooling_heat_release)

    # CALCULATE SYSTEM ENERGY DEMAND
    connected_system_energy_demand = calc_system_energy_demand_district_scale_buildings(sum_natural_gas_imports_W,
                                                                                        sum_wet_biomass_imports_W,
                                                                                        sum_dry_biomass_imports_W,
                                                                                        sum_electricity_imports_W,
                                                                                        sum_electricity_exports_W)

    return connected_costs, connected_emissions, connected_heat_release, connected_system_energy_demand


def calc_network_costs_cooling(locator, master_to_slave_vars, network_features, network_type):
    # Initialize class
    pipesCosts_USD = network_features.pipesCosts_DCN_USD
    num_buildings_connected = master_to_slave_vars.number_of_buildings_district_scale_cooling

    num_all_buildings = master_to_slave_vars.num_total_buildings
    ratio_connected = num_buildings_connected / num_all_buildings

    # Capital costs
    Inv_IR = 5
    Inv_LT = 20
    Inv_OM = 0.10
    Capex_Network_USD = pipesCosts_USD * ratio_connected
    Capex_a_Network_USD = calc_capex_annualized(Capex_Network_USD, Inv_IR, Inv_LT)
    Opex_fixed_Network_USD = Capex_Network_USD * Inv_OM

    # costs of pumps
    Capex_a_pump_USD, \
    Opex_fixed_pump_USD, \
    Capex_pump_USD, \
    P_motor_tot_W = PumpModel.calc_Ctot_pump(master_to_slave_vars,
                                             network_features,
                                             locator,
                                             network_type
                                             )

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

    performance = {
        'Capex_a_DCN_district_scale_USD': Capex_a_Network_USD,
        "Capex_a_SubstationsCooling_district_scale_USD": Capex_a_Substations_USD,

        "Capex_total_DCN_district_scale_USD": Capex_Network_USD,
        "Capex_total_SubstationsCooling_district_scale_USD": Capex_Substations_USD,

        "Opex_fixed_DCN_district_scale_USD": Opex_fixed_Network_USD,
        "Opex_fixed_SubstationsCooling_district_scale_USD": Opex_fixed_Substations_USD,

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
            HEX_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="HEX")
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
            Inv_IR = HEX_cost_data.iloc[0]['IR_%']
            Inv_LT = HEX_cost_data.iloc[0]['LT_yr']
            Inv_OM = HEX_cost_data.iloc[0]['O&M_%'] / 100

            Capex_total_USD = Inv_a + Inv_b * (Q_max_W) ** Inv_c + (Inv_d + Inv_e * Q_max_W) * log(Q_max_W)
            Capex_a_USD = calc_capex_annualized(Capex_total_USD, Inv_IR, Inv_LT)
            Opex_fixed_USD = Capex_total_USD * Inv_OM

            Capex_Substations_USD += Capex_total_USD
            Capex_a_Substations_USD += Capex_a_USD
            Opex_fixed_Substations_USD += Opex_fixed_USD

    return Capex_Substations_USD, Capex_a_Substations_USD, Opex_fixed_Substations_USD, Opex_var_Substations_USD


def calc_generation_costs_cooling_storage(master_to_slave_variables,
                                          daily_storage):
    """
    Calculate operation and maintenance costs of the thermal storage unit.

    :param master_to_slave_variables: class containing the features of a specific individual
    :param daily_storage: storage characteristics and parameters
    :type master_to_slave_variables: cea.optimization.slave_data.SlaveData class object
    :type daily_storage: cea.technologies.storage_tank_pcm.Storage_tank_PCM class object

    :return performance: costs of thermal storage unit
    """
    # STORAGE TANK
    if master_to_slave_variables.Storage_cooling_on == 1:
        Capex_a_Tank_USD, Opex_fixed_Tank_USD, Capex_Tank_USD = daily_storage.costs_storage()
    else:
        Capex_a_Tank_USD = 0.0
        Opex_fixed_Tank_USD = 0.0
        Capex_Tank_USD = 0.0

    # PLOT RESULTS
    performance = {
        # annualized capex
        "Capex_a_DailyStorage_WS_district_scale_USD": Capex_a_Tank_USD,

        # total capex
        "Capex_total_DailyStorage_WS_district_scale_USD": Capex_Tank_USD,

        # opex fixed
        "Opex_fixed_DailyStorage_WS_district_scale_USD": Opex_fixed_Tank_USD,
    }

    return performance


def calc_generation_costs_capacity_installed_cooling(locator,
                                                     master_to_slave_variables,
                                                     supply_systems,
                                                     mdotnMax_kgpers,
                                                     ):
    """
    Calculate capacities and costs of components installed in district cooling substation.

    :param locator: input locator set to scenario
    :param master_to_slave_variables: class containing the features of a specific individual
    :param supply_systems: database of thermal energy system components
    :param fload64 mdotnMax_kgpers: maximum mass flow rate of water in district cooling network pipes
    :type locator: cea.inputlocator.InputLocator class object
    :type master_to_slave_variables: cea.optimization.slave_data.SlaveData class object
    :type supply_systems: cea.technologies.supply_systems_database.SupplySystemsDatabase

    :return performance_costs: operation and maintenance costs of components in district cooling substation
    :return capacity_installed: capacity of components installed in district cooling substation
    """
    # TRIGENERATION
    if master_to_slave_variables.NG_Trigen_on == 1:
        Capacity_NG_Trigen_ACH_W = master_to_slave_variables.NG_Trigen_ACH_size_W
        Capacity_NG_Trigen_th_W = master_to_slave_variables.NG_Trigen_CCGT_size_thermal_W
        Capacity_NG_Trigen_el_W = master_to_slave_variables.NG_Trigen_CCGT_size_electrical_W

        # ACH
        Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Capacity_NG_Trigen_ACH_W,
                                                                                              supply_systems.Absorption_chiller,
                                                                                              ACH_TYPE_DOUBLE)
        # CCGT
        Capex_a_CCGT_USD, Opex_fixed_CCGT_USD, Capex_CCGT_USD = cogeneration.calc_Cinv_CCGT(Capacity_NG_Trigen_el_W,
                                                                                            supply_systems.CCGT)

        Capex_a_Trigen_NG_USD = Capex_a_ACH_USD + Capex_a_CCGT_USD
        Opex_fixed_Trigen_NG_USD = Opex_fixed_ACH_USD + Opex_fixed_CCGT_USD
        Capex_Trigen_NG_USD = Capex_ACH_USD + Capex_CCGT_USD
    else:
        Capacity_NG_Trigen_ACH_W = 0.0
        Capacity_NG_Trigen_th_W = 0.0
        Capacity_NG_Trigen_el_W = 0.0
        Capex_a_Trigen_NG_USD = 0.0
        Opex_fixed_Trigen_NG_USD = 0.0
        Capex_Trigen_NG_USD = 0.0

    # WATER-SOURCE VAPOR COMPRESSION CHILLER BASE
    if master_to_slave_variables.WS_BaseVCC_on == 1:
        Capacity_BaseVCC_WS_W = master_to_slave_variables.WS_BaseVCC_size_W
        # VCC
        Capex_a_BaseVCC_WS_USD, Opex_fixed_BaseVCC_WS_USD, Capex_BaseVCC_WS_USD = VCCModel.calc_Cinv_VCC(
            Capacity_BaseVCC_WS_W,
            locator,
            VCC_CODE_CENTRALIZED)
        # Pump uptake from water body
        # Values for the calculation of Delta P (from F. Muller network optimization code)
        # WARNING : current = values for Inducity - Zug
        DELTA_P_COEFF = 104.81
        DELTA_P_ORIGIN = 59016
        mdotnMax_kgpers = mdotnMax_kgpers * master_to_slave_variables.WS_BaseVCC_size_W / master_to_slave_variables.Q_cooling_nom_W  # weighted do the max installed
        deltaPmax = 2 * (DELTA_P_COEFF * mdotnMax_kgpers + DELTA_P_ORIGIN)
        # get pumping energy and peak load
        peak_pump_power_W = PumpModel.calc_pump_power(mdotnMax_kgpers, deltaPmax)

        Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD = calc_Cinv_pump(peak_pump_power_W,
                                                                               locator,
                                                                               'PU1')

        Capex_a_BaseVCC_WS_USD += Capex_a_pump_USD
        Opex_fixed_BaseVCC_WS_USD += Opex_fixed_pump_USD
        Capex_BaseVCC_WS_USD += Capex_pump_USD
    else:
        Capacity_BaseVCC_WS_W = 0.0
        Capex_a_BaseVCC_WS_USD = 0.0
        Opex_fixed_BaseVCC_WS_USD = 0.0
        Capex_BaseVCC_WS_USD = 0.0

    # WATER-SOURCE VAPOR COMPRESSION CHILLER PEAK
    if master_to_slave_variables.WS_PeakVCC_on == 1:
        Capacity_PeakVCC_WS_W = master_to_slave_variables.WS_PeakVCC_size_W
        # VCC
        Capex_a_PeakVCC_WS_USD, Opex_fixed_PeakVCC_WS_USD, Capex_PeakVCC_WS_USD = VCCModel.calc_Cinv_VCC(
            Capacity_PeakVCC_WS_W,
            locator,
            VCC_CODE_CENTRALIZED)
        # Pump uptake from water body
        # Values for the calculation of Delta P (from F. Muller network optimization code)
        # WARNING : current = values for Inducity - Zug
        DELTA_P_COEFF = 104.81
        DELTA_P_ORIGIN = 59016
        mdotnMax_kgpers = mdotnMax_kgpers * master_to_slave_variables.WS_PeakVCC_size_W / master_to_slave_variables.Q_cooling_nom_W  # weighted do the max installed
        deltaPmax = 2 * (DELTA_P_COEFF * mdotnMax_kgpers + DELTA_P_ORIGIN)

        # get pumping energy and peak load
        peak_pump_power_W = PumpModel.calc_pump_power(mdotnMax_kgpers, deltaPmax)

        Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD = calc_Cinv_pump(peak_pump_power_W,
                                                                               locator,
                                                                               'PU1')

        Capex_a_PeakVCC_WS_USD += Capex_a_pump_USD
        Opex_fixed_PeakVCC_WS_USD += Opex_fixed_pump_USD
        Capex_PeakVCC_WS_USD += Capex_pump_USD
    else:
        Capacity_PeakVCC_WS_W = 0.0
        Capex_a_PeakVCC_WS_USD = 0.0
        Opex_fixed_PeakVCC_WS_USD = 0.0
        Capex_PeakVCC_WS_USD = 0.0

    # AIR-SOURCE VAPOR COMPRESSION CHILLER BASE
    if master_to_slave_variables.AS_BaseVCC_on == 1:
        Capacity_BaseVCC_AS_W = master_to_slave_variables.AS_BaseVCC_size_W
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Capacity_BaseVCC_AS_W, locator,
                                                                                    VCC_CODE_CENTRALIZED)

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Capacity_BaseVCC_AS_W, locator, 'CT1')

        Capex_a_BaseVCC_AS_USD = Capex_a_VCC_USD + Capex_a_CT_USD
        Opex_fixed_BaseVCC_AS_USD = Opex_fixed_VCC_USD + Opex_fixed_CT_USD
        Capex_BaseVCC_AS_USD = Capex_VCC_USD + Capex_CT_USD

    else:
        Capacity_BaseVCC_AS_W = 0.0
        Capex_a_BaseVCC_AS_USD = 0.0
        Opex_fixed_BaseVCC_AS_USD = 0.0
        Capex_BaseVCC_AS_USD = 0.0

    # AIR-SOURCE VAPOR COMPRESSION CHILLER PEAK
    if master_to_slave_variables.AS_PeakVCC_on == 1:
        Capacity_PeakVCC_AS_W = master_to_slave_variables.AS_PeakVCC_size_W
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Capacity_PeakVCC_AS_W, locator,
                                                                                    VCC_CODE_CENTRALIZED)

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Capacity_PeakVCC_AS_W, locator, 'CT1')

        Capex_a_PeakVCC_AS_USD = Capex_a_VCC_USD + Capex_a_CT_USD
        Opex_fixed_PeakVCC_AS_USD = Opex_fixed_VCC_USD + Opex_fixed_CT_USD
        Capex_PeakVCC_AS_USD = Capex_VCC_USD + Capex_CT_USD
    else:
        Capacity_PeakVCC_AS_W = 0.0
        Capex_a_PeakVCC_AS_USD = 0.0
        Opex_fixed_PeakVCC_AS_USD = 0.0
        Capex_PeakVCC_AS_USD = 0.0

    # AIR-SOURCE VCC BACK-UP
    if master_to_slave_variables.AS_BackupVCC_on == 1:
        Capacity_BackupVCC_AS_W = master_to_slave_variables.AS_BackupVCC_size_W
        # VCC
        Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = VCCModel.calc_Cinv_VCC(Capacity_BackupVCC_AS_W, locator,
                                                                                    VCC_CODE_CENTRALIZED)

        # COOLING TOWER
        Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = CTModel.calc_Cinv_CT(Capacity_BackupVCC_AS_W, locator, 'CT1')

        Capex_a_BackupVCC_AS_USD = Capex_a_VCC_USD + Capex_a_CT_USD
        Opex_fixed_BackupVCC_AS_USD = Opex_fixed_VCC_USD + Opex_fixed_CT_USD
        Capex_BackupVCC_AS_USD = Capex_VCC_USD + Capex_CT_USD

    else:
        Capacity_BackupVCC_AS_W = 0.0
        Capex_a_BackupVCC_AS_USD = 0.0
        Opex_fixed_BackupVCC_AS_USD = 0.0
        Capex_BackupVCC_AS_USD = 0.0

    # STORAGE (Only capacity, since the rest is outside)
    Capacity_DailyStorage_W = master_to_slave_variables.Storage_cooling_size_W

    # PLOT RESULTS
    capacity_installed = {
        "Capacity_TrigenCCGT_heat_NG_district_scale_W": Capacity_NG_Trigen_th_W,
        "Capacity_TrigenACH_cool_NG_district_scale_W": Capacity_NG_Trigen_ACH_W,
        "Capacity_TrigenCCGT_el_NG_district_scale_W": Capacity_NG_Trigen_el_W,
        "Capacity_BaseVCC_WS_cool_district_scale_W": Capacity_BaseVCC_WS_W,
        "Capacity_PeakVCC_WS_cool_district_scale_W": Capacity_PeakVCC_WS_W,
        "Capacity_BaseVCC_AS_cool_district_scale_W": Capacity_BaseVCC_AS_W,
        "Capacity_PeakVCC_AS_cool_district_scale_W": Capacity_PeakVCC_AS_W,
        "Capacity_BackupVCC_AS_cool_district_scale_W": Capacity_BackupVCC_AS_W,
        "Capacity_DailyStorage_WS_cool_district_scale_W": Capacity_DailyStorage_W,
    }

    performance_costs = {
        # annualized capex
        "Capex_a_Trigen_NG_district_scale_USD": Capex_a_Trigen_NG_USD,
        "Capex_a_BaseVCC_WS_district_scale_USD": Capex_a_BaseVCC_WS_USD,
        "Capex_a_PeakVCC_WS_district_scale_USD": Capex_a_PeakVCC_WS_USD,
        "Capex_a_BaseVCC_AS_district_scale_USD": Capex_a_BaseVCC_AS_USD,
        "Capex_a_PeakVCC_AS_district_scale_USD": Capex_a_PeakVCC_AS_USD,
        "Capex_a_BackupVCC_AS_district_scale_USD": Capex_a_BackupVCC_AS_USD,

        # total capex
        "Capex_total_Trigen_NG_district_scale_USD": Capex_Trigen_NG_USD,
        "Capex_total_BaseVCC_WS_district_scale_USD": Capex_BaseVCC_WS_USD,
        "Capex_total_PeakVCC_WS_district_scale_USD": Capex_PeakVCC_WS_USD,
        "Capex_total_BaseVCC_AS_district_scale_USD": Capex_BaseVCC_AS_USD,
        "Capex_total_PeakVCC_AS_district_scale_USD": Capex_PeakVCC_AS_USD,
        "Capex_total_BackupVCC_AS_district_scale_USD": Capex_BackupVCC_AS_USD,

        # opex fixed
        "Opex_fixed_Trigen_NG_district_scale_USD": Opex_fixed_Trigen_NG_USD,
        "Opex_fixed_BaseVCC_WS_district_scale_USD": Opex_fixed_BaseVCC_WS_USD,
        "Opex_fixed_PeakVCC_WS_district_scale_USD": Opex_fixed_PeakVCC_WS_USD,
        "Opex_fixed_BaseVCC_AS_district_scale_USD": Opex_fixed_BaseVCC_AS_USD,
        "Opex_fixed_PeakVCC_AS_district_scale_USD": Opex_fixed_PeakVCC_AS_USD,
        "Opex_fixed_BackupVCC_AS_district_scale_USD": Opex_fixed_BackupVCC_AS_USD,
    }

    return performance_costs, capacity_installed


def calc_generation_costs_capacity_installed_heating(locator,
                                                     master_to_slave_vars,
                                                     config,
                                                     storage_activation_data,
                                                     mdotnMax_kgpers
                                                     ):
    """
    Calculate capacities and costs of components installed in district heating substation.

    :param locator: input locator set to scenario
    :param master_to_slave_vars: class containing the features of a specific individual
    :param config: configurations of CEA
    :param storage_activation_data: heat storage dispatch curve
    :param fload64 mdotnMax_kgpers: maximum mass flow rate of water in district cooling network pipes
    :type locator: cea.inputlocator.InputLocator class object
    :type master_to_slave_vars: cea.optimization.slave_data.SlaveData class object
    :type config: cea.config.Configuration class object

    :return performance_costs: operation and maintenance costs of components in district heating substation
    :return capacity_installed: capacity of components installed in district heating substation
    """

    thermal_network = master_to_slave_vars.DH_network_summary_individual
    supply_systems = SupplySystemsDatabase(locator)
    GHP_cost_data = supply_systems.HP
    BH_cost_data = supply_systems.BH
    boiler_cost_data = supply_systems.Boiler

    # CCGT
    if master_to_slave_vars.CC_on == 1:
        Capacity_CHP_NG_heat_W = master_to_slave_vars.CCGT_SIZE_W
        Capacity_CHP_NG_el_W = master_to_slave_vars.CCGT_SIZE_electrical_W
        Capex_a_CHP_NG_USD, Opex_fixed_CHP_NG_USD, Capex_CHP_NG_USD = chp.calc_Cinv_CCGT(Capacity_CHP_NG_el_W,
                                                                                         supply_systems.CCGT)
    else:
        Capacity_CHP_NG_heat_W = 0.0
        Capacity_CHP_NG_el_W = 0.0
        Capex_a_CHP_NG_USD = 0.0
        Opex_fixed_CHP_NG_USD = 0.0
        Capex_CHP_NG_USD = 0.0

    # DRY BIOMASS
    if master_to_slave_vars.Furnace_dry_on == 1:
        Capacity_furnace_dry_heat_W = master_to_slave_vars.DBFurnace_Q_max_W
        Capacity_furnace_dry_el_W = master_to_slave_vars.DBFurnace_electrical_W
        Capex_a_furnace_dry_USD, \
        Opex_fixed_furnace_dry_USD, \
        Capex_furnace_dry_USD = furnace.calc_Cinv_furnace(Capacity_furnace_dry_heat_W, locator, 'FU1')
    else:
        Capacity_furnace_dry_el_W = 0.0
        Capacity_furnace_dry_heat_W = 0.0
        Capex_furnace_dry_USD = 0.0
        Capex_a_furnace_dry_USD = 0.0
        Opex_fixed_furnace_dry_USD = 0.0

    # WET BIOMASS
    if master_to_slave_vars.Furnace_wet_on == 1:
        Capacity_furnace_wet_heat_W = master_to_slave_vars.WBFurnace_Q_max_W
        Capacity_furnace_wet_el_W = master_to_slave_vars.WBFurnace_electrical_W
        Capex_a_furnace_wet_USD, \
        Opex_fixed_furnace_wet_USD, \
        Capex_furnace_wet_USD = furnace.calc_Cinv_furnace(Capacity_furnace_wet_heat_W, locator, 'FU1')
    else:
        Capacity_furnace_wet_heat_W = 0.0
        Capacity_furnace_wet_el_W = 0.0
        Capex_a_furnace_wet_USD = 0.0
        Opex_fixed_furnace_wet_USD = 0.0
        Capex_furnace_wet_USD = 0.0

    # BOILER BASE LOAD
    if master_to_slave_vars.Boiler_on == 1:
        Capacity_BaseBoiler_NG_W = master_to_slave_vars.Boiler_Q_max_W
        Capex_a_BaseBoiler_NG_USD, \
        Opex_fixed_BaseBoiler_NG_USD, \
        Capex_BaseBoiler_NG_USD = boiler.calc_Cinv_boiler(Capacity_BaseBoiler_NG_W, 'BO1', boiler_cost_data)
    else:
        Capacity_BaseBoiler_NG_W = 0.0
        Capex_a_BaseBoiler_NG_USD = 0.0
        Opex_fixed_BaseBoiler_NG_USD = 0.0
        Capex_BaseBoiler_NG_USD = 0.0

    # BOILER PEAK LOAD
    if master_to_slave_vars.BoilerPeak_on == 1:
        Capacity_PeakBoiler_NG_W = master_to_slave_vars.BoilerPeak_Q_max_W
        Capex_a_PeakBoiler_NG_USD, \
        Opex_fixed_PeakBoiler_NG_USD, \
        Capex_PeakBoiler_NG_USD = boiler.calc_Cinv_boiler(Capacity_PeakBoiler_NG_W, 'BO1', boiler_cost_data)
    else:
        Capacity_PeakBoiler_NG_W = 0.0
        Capex_a_PeakBoiler_NG_USD = 0.0
        Opex_fixed_PeakBoiler_NG_USD = 0.0
        Capex_PeakBoiler_NG_USD = 0.0

    # HEATPUMP LAKE
    if master_to_slave_vars.HPLake_on == 1:
        Capacity_WS_HP_W = master_to_slave_vars.HPLake_maxSize_W
        Capex_a_Lake_USD, \
        Opex_fixed_Lake_USD, \
        Capex_Lake_USD = hp.calc_Cinv_HP(Capacity_WS_HP_W, locator, 'HP2')

        # Pump uptake from water body
        # Values for the calculation of Delta P (from F. Muller network optimization code)
        # WARNING : current = values for Inducity - Zug
        DELTA_P_COEFF = 104.81
        DELTA_P_ORIGIN = 59016
        mdotnMax_kgpers = mdotnMax_kgpers * master_to_slave_vars.HPLake_maxSize_W / master_to_slave_vars.Q_heating_nom_W  # weighted do the max installed
        deltaPmax = 2 * (DELTA_P_COEFF * mdotnMax_kgpers + DELTA_P_ORIGIN)
        # get pumping energy and peak load
        peak_pump_power_W = PumpModel.calc_pump_power(mdotnMax_kgpers, deltaPmax)

        Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD = calc_Cinv_pump(peak_pump_power_W,
                                                                               locator,
                                                                               'PU1')

        Capex_a_Lake_USD += Capex_a_pump_USD
        Opex_fixed_Lake_USD += Opex_fixed_pump_USD
        Capex_Lake_USD += Capex_pump_USD

    else:
        Capacity_WS_HP_W = 0.0
        Capex_a_Lake_USD = 0.0
        Opex_fixed_Lake_USD = 0.0
        Capex_Lake_USD = 0.0

    # HEATPUMP_SEWAGE
    if master_to_slave_vars.HPSew_on == 1:
        Capacity_SS_HP_W = master_to_slave_vars.HPSew_maxSize_W
        Capex_a_Sewage_USD, \
        Opex_fixed_Sewage_USD, \
        Capex_Sewage_USD = hp.calc_Cinv_HP(Capacity_SS_HP_W, locator, 'HP2')
    else:
        Capacity_SS_HP_W = 0.0
        Capex_a_Sewage_USD = 0.0
        Opex_fixed_Sewage_USD = 0.0
        Capex_Sewage_USD = 0.0

    # GROUND HEAT PUMP
    if master_to_slave_vars.GHP_on == 1:
        Capacity_GS_HP_W = master_to_slave_vars.GHP_maxSize_W
        Capex_a_GHP_USD, \
        Opex_fixed_GHP_USD, \
        Capex_GHP_USD = hp.calc_Cinv_GHP(Capacity_GS_HP_W, GHP_cost_data, BH_cost_data)
    else:
        Capacity_GS_HP_W = 0.0
        Capex_a_GHP_USD = 0.0
        Opex_fixed_GHP_USD = 0.0
        Capex_GHP_USD = 0.0

    # BACK-UP BOILER
    if master_to_slave_vars.BackupBoiler_on != 0:
        Capacity_BackupBoiler_NG_W = master_to_slave_vars.BackupBoiler_size_W
        Capex_a_BackupBoiler_NG_USD, \
        Opex_fixed_BackupBoiler_NG_USD, \
        Capex_BackupBoiler_NG_USD = boiler.calc_Cinv_boiler(Capacity_BackupBoiler_NG_W, 'BO1', boiler_cost_data)
    else:
        Capacity_BackupBoiler_NG_W = 0.0
        Capex_a_BackupBoiler_NG_USD = 0.0
        Opex_fixed_BackupBoiler_NG_USD = 0.0
        Capex_BackupBoiler_NG_USD = 0.0

    # DATA CENTRE SOURCE HEAT PUMP
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        Capacity_DS_HP_W = thermal_network["Qcdata_netw_total_kWh"].max() * 1000  # convert to Wh
        Capex_a_wasteserver_HEX_USD, Opex_fixed_wasteserver_HEX_USD, Capex_wasteserver_HEX_USD = hex.calc_Cinv_HEX(
            Capacity_DS_HP_W, locator, config, 'HEX1')

        Q_HP_max_Wh = storage_activation_data["Q_HP_Server_W"].max()
        Capex_a_wasteserver_HP_USD, Opex_fixed_wasteserver_HP_USD, Capex_wasteserver_HP_USD = hp.calc_Cinv_HP(
            Q_HP_max_Wh, locator, 'HP2')
    else:
        Capex_a_wasteserver_HEX_USD = 0.0
        Opex_fixed_wasteserver_HEX_USD = 0.0
        Capex_wasteserver_HEX_USD = 0.0
        Capacity_DS_HP_W = 0.0
        Capex_a_wasteserver_HP_USD = 0.0
        Opex_fixed_wasteserver_HP_USD = 0.0
        Capex_wasteserver_HP_USD = 0.0

    # SOLAR TECHNOLOGIES
    # ADD COSTS AND EMISSIONS DUE TO SOLAR TECHNOLOGIES
    Capacity_SC_ET_area_m2 = master_to_slave_vars.A_SC_ET_m2
    Capacity_SC_ET_W = Capacity_SC_ET_area_m2 * N_SC_ET * 1000  # W
    Capex_a_SC_ET_USD, \
    Opex_fixed_SC_ET_USD, \
    Capex_SC_ET_USD = stc.calc_Cinv_SC(Capacity_SC_ET_area_m2, locator,
                                       'ET')

    Capacity_SC_FP_m2 = master_to_slave_vars.A_SC_FP_m2
    Capacity_SC_FP_W = Capacity_SC_FP_m2 * N_SC_FP * 1000  # W
    Capex_a_SC_FP_USD, \
    Opex_fixed_SC_FP_USD, \
    Capex_SC_FP_USD = stc.calc_Cinv_SC(Capacity_SC_FP_m2, locator,
                                       'FP')

    Capacity_PVT_m2 = master_to_slave_vars.A_PVT_m2
    Capacity_PVT_el_W = Capacity_PVT_m2 * N_PVT * 1000  # W
    Capacity_PVT_th_W = Capacity_PVT_m2 * N_SC_FP * 1000  # W
    Capex_a_PVT_USD, \
    Opex_fixed_PVT_USD, \
    Capex_PVT_USD = pvt.calc_Cinv_PVT(Capacity_PVT_el_W, locator)

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

    # SEASONAL STORAGE (Costs are outside of this function)
    Capacity_seasonal_storage_m3 = storage_activation_data['Storage_Size_m3']
    Capacity_seasonal_storage_W = storage_activation_data['Q_storage_max_W']

    capacity_installed = {
        "Capacity_CHP_NG_heat_district_scale_W": Capacity_CHP_NG_heat_W,
        "Capacity_CHP_NG_el_district_scale_W": Capacity_CHP_NG_el_W,
        "Capacity_CHP_WB_heat_district_scale_W": Capacity_furnace_wet_heat_W,
        "Capacity_CHP_WB_el_district_scale_W": Capacity_furnace_wet_el_W,
        "Capacity_CHP_DB_heat_district_scale_W": Capacity_furnace_dry_heat_W,
        "Capacity_CHP_DB_el_district_scale_W": Capacity_furnace_dry_el_W,
        "Capacity_BaseBoiler_NG_heat_district_scale_W": Capacity_BaseBoiler_NG_W,
        "Capacity_PeakBoiler_NG_heat_district_scale_W": Capacity_PeakBoiler_NG_W,
        "Capacity_BackupBoiler_NG_heat_district_scale_W": Capacity_BackupBoiler_NG_W,
        "Capacity_HP_WS_heat_district_scale_W": Capacity_WS_HP_W,
        "Capacity_HP_SS_heat_district_scale_W": Capacity_SS_HP_W,
        "Capacity_HP_GS_heat_district_scale_W": Capacity_GS_HP_W,
        "Capacity_HP_DS_heat_district_scale_W": Capacity_DS_HP_W,
        "Capacity_SC_ET_heat_district_scale_W": Capacity_SC_ET_W,
        "Capacity_SC_FP_heat_district_scale_W": Capacity_SC_FP_W,
        "Capacity_SC_ET_district_scale_m2": Capacity_SC_ET_area_m2,
        "Capacity_SC_FP_district_scale_m2": Capacity_SC_FP_m2,
        "Capacity_PVT_district_scale_m2": Capacity_PVT_m2,
        "Capacity_PVT_el_district_scale_W": Capacity_PVT_el_W,
        "Capacity_PVT_heat_district_scale_W": Capacity_PVT_th_W,
        "Capacity_SeasonalStorage_WS_heat_district_scale_W": Capacity_seasonal_storage_W,
        "Capacity_SeasonalStorage_WS_heat_district_scale_m3": Capacity_seasonal_storage_m3,
    }

    performance_costs = {
        "Capex_a_SC_ET_district_scale_USD": Capex_a_SC_ET_USD + Capex_a_HP_SC_ET_USD + Capex_a_HEX_SC_ET_USD,
        "Capex_a_SC_FP_district_scale_USD": Capex_a_SC_FP_USD + Capex_a_HP_SC_FP_USD + Capex_a_HEX_SC_FP_USD,
        "Capex_a_PVT_district_scale_USD": Capex_a_PVT_USD + Capex_a_HP_PVT_USD + Capex_a_HEX_PVT_USD,
        "Capex_a_HP_Server_district_scale_USD": Capex_a_wasteserver_HP_USD + Capex_a_wasteserver_HEX_USD,
        "Capex_a_HP_Sewage_district_scale_USD": Capex_a_Sewage_USD,
        "Capex_a_HP_Lake_district_scale_USD": Capex_a_Lake_USD,
        "Capex_a_GHP_district_scale_USD": Capex_a_GHP_USD,
        "Capex_a_CHP_NG_district_scale_USD": Capex_a_CHP_NG_USD,
        "Capex_a_Furnace_wet_district_scale_USD": Capex_a_furnace_wet_USD,
        "Capex_a_Furnace_dry_district_scale_USD": Capex_a_furnace_dry_USD,
        "Capex_a_BaseBoiler_NG_district_scale_USD": Capex_a_BaseBoiler_NG_USD,
        "Capex_a_PeakBoiler_NG_district_scale_USD": Capex_a_PeakBoiler_NG_USD,
        "Capex_a_BackupBoiler_NG_district_scale_USD": Capex_a_BackupBoiler_NG_USD,

        # total_capex
        "Capex_total_SC_ET_district_scale_USD": Capex_SC_ET_USD + Capex_HP_SC_ET_USD + Capex_HEX_SC_ET_USD,
        "Capex_total_SC_FP_district_scale_USD": Capex_SC_FP_USD + Capex_HP_SC_FP_USD + Capex_HEX_SC_FP_USD,
        "Capex_total_PVT_district_scale_USD": Capex_PVT_USD + Capex_HP_PVT_USD + Capex_HEX_PVT_USD,
        "Capex_total_HP_Server_district_scale_USD": Capex_wasteserver_HP_USD + Capex_wasteserver_HEX_USD,
        "Capex_total_HP_Sewage_district_scale_USD": Capex_Sewage_USD,
        "Capex_total_HP_Lake_district_scale_USD": Capex_Lake_USD,
        "Capex_total_GHP_district_scale_USD": Capex_GHP_USD,
        "Capex_total_CHP_NG_district_scale_USD": Capex_CHP_NG_USD,
        "Capex_total_Furnace_wet_district_scale_USD": Capex_furnace_wet_USD,
        "Capex_total_Furnace_dry_district_scale_USD": Capex_furnace_dry_USD,
        "Capex_total_BaseBoiler_NG_district_scale_USD": Capex_BaseBoiler_NG_USD,
        "Capex_total_PeakBoiler_NG_district_scale_USD": Capex_PeakBoiler_NG_USD,
        "Capex_total_BackupBoiler_NG_district_scale_USD": Capex_BackupBoiler_NG_USD,

        # opex fixed costs
        "Opex_fixed_SC_ET_district_scale_USD": Opex_fixed_SC_ET_USD,
        "Opex_fixed_SC_FP_district_scale_USD": Opex_fixed_SC_FP_USD,
        "Opex_fixed_PVT_district_scale_USD": Opex_fixed_PVT_USD,
        "Opex_fixed_HP_Server_district_scale_USD": Opex_fixed_wasteserver_HP_USD + Opex_fixed_wasteserver_HEX_USD,
        "Opex_fixed_HP_Sewage_district_scale_USD": Opex_fixed_Sewage_USD,
        "Opex_fixed_HP_Lake_district_scale_USD": Opex_fixed_Lake_USD,
        "Opex_fixed_GHP_district_scale_USD": Opex_fixed_GHP_USD,
        "Opex_fixed_CHP_NG_district_scale_USD": Opex_fixed_CHP_NG_USD,
        "Opex_fixed_Furnace_wet_district_scale_USD": Opex_fixed_furnace_wet_USD,
        "Opex_fixed_Furnace_dry_district_scale_USD": Opex_fixed_furnace_dry_USD,
        "Opex_fixed_BaseBoiler_NG_district_scale_USD": Opex_fixed_BaseBoiler_NG_USD,
        "Opex_fixed_PeakBoiler_NG_district_scale_USD": Opex_fixed_PeakBoiler_NG_USD,
        "Opex_fixed_BackupBoiler_NG_district_scale_USD": Opex_fixed_BackupBoiler_NG_USD,

    }

    return performance_costs, capacity_installed


def calc_seasonal_storage_costs(locator, storage_activation_data):
    # STORAGE
    # costs of storage are already calculated
    Capacity_seasonal_storage_m3 = storage_activation_data['Storage_Size_m3']
    # Get results from storage operation
    Capex_a_storage_USD, \
    Opex_fixed_storage_USD, \
    Capex_storage_USD = thermal_storage.calc_Cinv_storage(Capacity_seasonal_storage_m3, locator, 'TES1')
    # HEATPUMP FOR SEASONAL SOLAR STORAGE OPERATION (CHARGING AND DISCHARGING) TO DH
    storage_dispatch_df = pd.DataFrame(storage_activation_data)
    array = np.array(storage_dispatch_df[["E_Storage_charging_req_W",
                                          "E_Storage_discharging_req_W",
                                          "Q_Storage_gen_W",
                                          "Q_Storage_req_W"]])
    Q_HP_max_storage_W = 0
    for i in range(8760):
        if array[i][0] > 0:
            Q_HP_max_storage_W = max(Q_HP_max_storage_W, array[i][3] + array[i][0])
        elif array[i][1] > 0:
            Q_HP_max_storage_W = max(Q_HP_max_storage_W, array[i][2] + array[i][1])
    Capex_a_HP_storage_USD, Opex_fixed_HP_storage_USD, Capex_HP_storage_USD = hp.calc_Cinv_HP(Q_HP_max_storage_W,
                                                                                              locator,
                                                                                              'HP2')

    performance_costs = {
        "Capex_a_SeasonalStorage_WS_district_scale_USD": Capex_a_storage_USD + Capex_a_HP_storage_USD,
        "Capex_total_SeasonalStorage_WS_district_scale_USD": Capex_storage_USD + Capex_HP_storage_USD,
        "Opex_fixed_SeasonalStorage_WS_district_scale_USD": Opex_fixed_storage_USD + Opex_fixed_HP_storage_USD,
    }

    return performance_costs


def calc_objective_functions_decentralized_DC(DCN_barcode, buildings_names_with_cooling_load, locator,
                                              ):
    GHG_sys_building_scale_tonCO2yr = 0.0
    Capex_a_sys_building_scale_USD = 0.0
    Opex_var_sys_disconnected = 0.0
    Capex_total_sys_building_scale_USD = 0.0
    Opex_fixed_sys_building_scale_USD = 0.0
    Qh_sys_release_Wh = 0.0
    NG_sys_req_Wh = 0.0
    E_sys_req_Wh = 0.0
    capacity_installed_df = pd.DataFrame()
    for (index, building_name) in zip(DCN_barcode, buildings_names_with_cooling_load):
        if index == "0":  # choose the best decentralized configuration
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_name,
                                                                                                   configuration='AHU_ARU_SCU'))
            dfBest = df[df["Best configuration"] == 1]
            GHG_sys_building_scale_tonCO2yr += dfBest["GHG_tonCO2"].iloc[0]  # [ton CO2]
            Capex_total_sys_building_scale_USD += dfBest["Capex_total_USD"].iloc[0]
            Capex_a_sys_building_scale_USD += dfBest["Capex_a_USD"].iloc[0]
            Opex_var_sys_disconnected += dfBest["Opex_var_USD"].iloc[0]
            Opex_fixed_sys_building_scale_USD += dfBest["Opex_fixed_USD"].iloc[0]
            Qh_sys_release_Wh += dfBest["Qh_sys_release_Wh"].iloc[0]
            NG_sys_req_Wh += dfBest["NG_sys_req_Wh"].iloc[0]
            E_sys_req_Wh += dfBest["E_sys_req_Wh"].iloc[0]

            data = pd.DataFrame({'Name': building_name,
                                 'Capacity_DX_AS_cool_building_scale_W': dfBest["Capacity_DX_AS_W"].iloc[0],
                                 'Capacity_BaseVCC_AS_cool_building_scale_W': dfBest["Capacity_BaseVCC_AS_W"].iloc[0],
                                 'Capacity_VCCHT_AS_cool_building_scale_W': dfBest["Capacity_VCCHT_AS_W"].iloc[0],
                                 'Capacity_ACH_SC_FP_cool_building_scale_W': dfBest["Capacity_ACH_SC_FP_W"].iloc[0],
                                 'Capaticy_ACH_SC_ET_cool_building_scale_W': dfBest["Capaticy_ACH_SC_ET_W"].iloc[0],
                                 'Capacity_ACHHT_FP_cool_building_scale_W': dfBest["Capacity_ACHHT_FP_W"].iloc[0]},
                                index=[0])
            capacity_installed_df = pd.concat([capacity_installed_df, data], ignore_index=True)

    return GHG_sys_building_scale_tonCO2yr, \
           Capex_total_sys_building_scale_USD, \
           Capex_a_sys_building_scale_USD, \
           Opex_var_sys_disconnected, \
           Opex_fixed_sys_building_scale_USD, \
           Qh_sys_release_Wh, \
           NG_sys_req_Wh, \
           E_sys_req_Wh, \
           capacity_installed_df


def calc_costs_emissions_decentralized_DH(DHN_barcode, buildings_names_with_heating_load, locator):
    GHG_sys_building_scale_tonCO2yr = 0.0
    Capex_a_sys_building_scale_USD = 0.0
    CostDiscBuild = 0.0
    Opex_var_sys_disconnected = 0.0
    Capex_total_sys_building_scale_USD = 0.0
    Opex_fixed_sys_building_scale_USD = 0.0
    capacity_installed_df = pd.DataFrame()
    for (index, building_name) in zip(DHN_barcode, buildings_names_with_heating_load):
        if index == "0":
            df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_heating(building_name))
            dfBest = df[df["Best configuration"] == 1]
            CostDiscBuild += dfBest["TAC_USD"].iloc[0]  # [USD]
            GHG_sys_building_scale_tonCO2yr += dfBest["GHG_tonCO2"].iloc[0]  # [ton CO2]
            Capex_total_sys_building_scale_USD += dfBest["Capex_total_USD"].iloc[0]
            Capex_a_sys_building_scale_USD += dfBest["Capex_a_USD"].iloc[0]
            Opex_var_sys_disconnected += dfBest["Opex_var_USD"].iloc[0]
            Opex_fixed_sys_building_scale_USD += dfBest["Opex_fixed_USD"].iloc[0]

            data = pd.DataFrame({'Name': building_name,
                                 'Capacity_BaseBoiler_NG_heat_building_scale_W': dfBest["Capacity_BaseBoiler_NG_W"].iloc[
                                     0],
                                 'Capacity_FC_NG_heat_building_scale_W': dfBest["Capacity_FC_NG_W"].iloc[0],
                                 'Capacity_GS_HP_heat_building_scale_W': dfBest["Capacity_GS_HP_W"].iloc[0]}, index=[0])
            capacity_installed_df = pd.concat([capacity_installed_df, data], ignore_index=True)

    return GHG_sys_building_scale_tonCO2yr, \
           Capex_total_sys_building_scale_USD, \
           Capex_a_sys_building_scale_USD, \
           Opex_var_sys_disconnected, \
           Opex_fixed_sys_building_scale_USD, \
           capacity_installed_df
