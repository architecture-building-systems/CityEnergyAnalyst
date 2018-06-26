from __future__ import print_function
from __future__ import division
from cea.utilities.standarize_coordinates import get_lat_lon_projected_shapefile
from geopandas import GeoDataFrame as gdf
import os
import time
import numpy as np
import pandas as pd
from scipy import interpolate
import cea.globalvar
import cea.inputlocator
from math import *
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.technologies.solar import constants
import cea.config

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def supply_system_configuration(generation, individual, locator, config):
    district_supply_sys_columns = ['Lake [W]', 'VCC [W]', 'single effect ACH [W]', 'double effect ACH [W]',
                                   'DX [W]', 'CCGT_heat [W]', 'SC_FP [m2]', 'SC_ET [m2]', 'PV [m2]', 'Capex_a',
                                   'Opex_a']

    # get supply system configuration of a particular individual
    all_individuals = pd.read_csv(locator.get_optimization_all_individuals())
    individual_system_configuration = all_individuals.loc[
        (all_individuals['generation'].isin([generation])) & all_individuals['individual'].isin([individual])]

    if config.optimization.isheating:
        network_name = 'DHN'
        network_connected_buildings, decentralized_buildings = calc_building_lists(individual_system_configuration,
                                                                                   network_name)
        centralized_cost_detail_heating = pd.read_csv(
            locator.get_optimization_slave_investment_cost_detailed(individual, generation))
    if config.optimization.iscooling:
        network_name = 'DCN'
        network_connected_buildings, decentralized_buildings = calc_building_lists(individual_system_configuration,
                                                                                   network_name)

        # get supply systems at centralized plants
        # cen_cost_detail_cooling = pd.read_csv(
        #     locator.get_optimization_slave_investment_cost_detailed_cooling(individual, generation))
        # cen_cooling_tech_column = ['Lake Cooling Share', 'VCC Cooling Share', 'Absorption Chiller Share',
        #                            'Storage Share']
        # cen_cooling_tech_share = individual_system_configuration[cen_cooling_tech_column]

        # get centralized system sizes
        cen_supply_sys_cooling = calc_cen_supply_sys_cooling(generation, individual, locator)
        cen_supply_sys_electricity = calc_cen_supply_sys_electricity(network_name, generation, individual, locator)
        # get centralized system cost
        cen_capex_a_cooling, cen_opex_a_cooling = calc_cen_costs_cooling(generation, individual,
                                                                         locator)  # FIXME: cost of PV?

        # get supply systems at decentralized buildings
        bui_supply_sys = []
        for building in decentralized_buildings:
            bui_sys_config = calc_building_supply_system(individual_system_configuration, network_name)
            bui_supply_sys.append(calc_bui_sys_detail(building, bui_sys_config, district_supply_sys_columns, locator))
        for building in network_connected_buildings:
            bui_supply_sys[building]

    return


def calc_cen_costs_cooling(generation, individual, locator):
    cooling_costs = pd.read_csv(
        locator.get_optimization_slave_investment_cost_detailed_cooling(individual, generation))
    capex_a_columns = [item for item in cooling_costs.columns if 'Capex_a' in item]
    cen_capex_a = cooling_costs[capex_a_columns].sum(axis=1).values[0]
    opex_a_columns = [item for item in cooling_costs.columns if 'Opex_a' in item]
    cen_opex_a = cooling_costs[opex_a_columns].sum(axis=1).values[0]
    return cen_capex_a, cen_opex_a


def calc_cen_supply_sys_cooling(generation, individual, locator):
    cooling_activation_column = ['Q_from_ACH_W', 'Q_from_Lake_W', 'Q_from_VCC_W', 'Q_from_VCC_backup_W',
                                 'Q_from_storage_tank_W', 'Qc_CT_associated_with_all_chillers_W',
                                 'Qh_CCGT_associated_with_absorption_chillers_W']
    cooling_activation_pattern = pd.read_csv(
        locator.get_optimization_slave_cooling_activation_pattern(individual, generation))
    cen_cooling_sys = cooling_activation_pattern[cooling_activation_column].max()
    return cen_cooling_sys


def calc_cen_supply_sys_electricity(network_name, generation, individual, locator):
    if network_name == 'DCN':
        el_activation_columns = ['Area_PV_m2', 'E_CHP_to_directload_W', 'E_CHP_to_grid_W', 'E_PV_W', 'E_from_grid_W']
        el_activation_pattern = pd.read_csv(
            locator.get_optimization_slave_electricity_activation_pattern_cooling(individual, generation))
        el_sys_activation_pattern = el_activation_pattern[el_activation_columns]
        el_sys_activation_pattern['E_CHP_W'] = el_activation_pattern['E_CHP_to_directload_W'] + el_activation_pattern[
            'E_CHP_to_grid_W']
        el_sys_activation_pattern.drop('E_CHP_to_directload_W', axis=1, inplace=True)
        el_sys_activation_pattern.drop('E_CHP_to_grid_W', axis=1, inplace=True)
        cen_el_supply_sys = el_sys_activation_pattern.max()
    elif network_name == 'DHN':
        el_activation_columns = ['Area_PV_m2', 'E_CHP_to_directload_W', 'E_CHP_to_grid_W', 'E_PV_W', 'E_from_grid_W']
        el_activation_pattern = pd.read_csv(
            locator.get_optimization_slave_electricity_activation_pattern_heating(individual, generation))
        el_sys_activation_pattern = el_activation_pattern[el_activation_columns]
        el_sys_activation_pattern['E_CHP_W'] = el_activation_pattern['E_CHP_to_directload_W'] + el_activation_pattern[
            'E_CHP_to_grid_W']
        el_sys_activation_pattern.drop('E_CHP_to_directload_W', axis=1, inplace=True)
        el_sys_activation_pattern.drop('E_CHP_to_grid_W', axis=1, inplace=True)
        cen_el_supply_sys = el_sys_activation_pattern.max()
    else:
        raise ValueError('Wrong network_name')

    return cen_el_supply_sys


def calc_building_lists(individual_system_configuration, network_name):
    buildings_list = [item for item in individual_system_configuration.columns if network_name in item and 'B' in item]
    buildings_df = individual_system_configuration[buildings_list]
    network_connected_buildings = buildings_df[buildings_df[buildings_list] > 0.00000].dropna(axis=1).columns
    network_connected_buildings = [x.split()[0] for x in network_connected_buildings]
    decentralized_buildings = buildings_df[buildings_df[buildings_list] < 1.00000].dropna(axis=1).columns
    decentralized_buildings = [x.split()[0] for x in decentralized_buildings]
    return network_connected_buildings, decentralized_buildings


def calc_building_supply_system(individual_system_configuration, network_name):
    all_configuration_dict = {1: "ARU_SCU", 2: "AHU_SCU", 3: "AHU_ARU", 4: "SCU", 5: "ARU", 6: "AHU", 7: "AHU_ARU_SCU"}
    unit_configuration_name = network_name + ' unit configuration'
    unit_configuration = int(individual_system_configuration[unit_configuration_name].values[0])
    if unit_configuration in all_configuration_dict:
        decentralized_config = all_configuration_dict[unit_configuration]
    else:
        raise ValueError('DCN unit configuration does not exist.')
    return decentralized_config


def calc_bui_sys_detail(building, bui_sys_config, district_supply_sys_columns, locator):
    # get nominal power and costs from disconnected calculation
    bui_results = pd.read_csv(
        locator.get_optimization_disconnected_folder_building_result_cooling(building, bui_sys_config))
    bui_results_best = bui_results[bui_results['Best configuration'] > 0.0]

    technology_columns = [item for item in bui_results_best.columns if 'Nominal Power' in item]
    cost_columns = [item for item in bui_results_best.columns if 'Costs' in item]
    technology_columns.extend(cost_columns)
    bui_results_best = bui_results_best[technology_columns].reset_index(drop=True)

    # write building system configuration to output
    bui_sys_detail = pd.DataFrame(columns=district_supply_sys_columns, index=[building])
    bui_sys_detail = bui_sys_detail.fillna(0.0)

    if not np.isclose(bui_results_best.loc[0, 'Nominal Power DX to AHU_ARU_SCU [W]'], 0.0):
        bui_sys_detail.loc[building, 'DX [W]'] = bui_results_best.loc[0, 'Nominal Power DX to AHU_ARU_SCU [W]']
        pv_installed_area = pd.read_csv(locator.PV_metadata_results(building))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'PV[m2]'] = pv_installed_area

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU_SCU [W]'], 0.0):
        bui_sys_detail.loc[building, 'VCC(LT) [W]'] = bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU_SCU [W]']
        pv_installed_area = pd.read_csv(locator.PV_metadata_results(building))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'PV[m2]'] = pv_installed_area

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]'], 0.0):
        bui_sys_detail.loc[building, 'ACH(LT) [W]'] = bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]']
        sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, 'FP'))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'SC_FP [m2]'] = sc_installed_area

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]'], 0.0):
        bui_sys_detail.loc[building, 'ACH(LT) [W]'] = bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]']
        sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, 'ET'))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'SC_ET [m2]'] = sc_installed_area

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power VCC to SCU [W]'], 0.0):
        bui_sys_detail.loc[building, 'VCC(HT) [W]'] = bui_results_best.loc[0, 'Nominal Power VCC to SCU [W]']
        bui_sys_detail.loc[building, 'VCC(LT) [W]'] = bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU [W]']
        pv_installed_area = pd.read_csv(locator.PV_metadata_results(building))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'PV[m2]'] = pv_installed_area

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power single effect ACH to SCU (FP) [W]'], 0.0):
        bui_sys_detail.loc[building, 'ACH(HT) [W]'] = bui_results_best.loc[0, 'Nominal Power single effect ACH to SCU (FP) [W]']
        bui_sys_detail.loc[building, 'VCC(LT) [W]'] = bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU [W]']
        sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, 'FP'))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'SC_FP [m2]'] = sc_installed_area

    else: raise ValueError ('No cooling system is specified for the decentralized building ', building)

    bui_sys_detail.loc[building, 'Opex_a'] = bui_results_best.loc[0, 'Operation Costs [CHF]']
    bui_sys_detail.loc[building, 'Capex_a'] = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]']
    #
    # # get installed area of solar collectors
    # sc_panel_types = ['FP', 'ET']
    # for panel_type in sc_panel_types:
    #     bui_results_best.loc[0, 'SC_' + panel_type + '[m2]'] = 0.0  # initiate a new column
    #     columns = [item for item in bui_results_best.columns if panel_type in item]
    #     for tech in columns:
    #         if not np.isclose(bui_results_best[tech], 0.0):
    #             sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, panel_type))[
    #                 'area_installed_module_m2'].sum()
    #             bui_results_best.loc[0, 'SC_' + panel_type + '[m2]'] = sc_installed_area
    #
    # if np.isclose(bui_results_best['SC_FP[m2]'], 0.0) & np.isclose(bui_results_best['SC_ET[m2]'], 0.0):
    #     pv_installed_area = pd.read_csv(locator.PV_metadata_results(building))['area_installed_module_m2'].sum()
    #     bui_results_best.loc[0, 'PV[m2]'] = pv_installed_area

    # bui_results_best.rename(columns={'Nominal Power DX to AHU_ARU_SCU [W]': 'DX [W]',
    #                                  'Nominal Power VCC to AHU_ARU [W]': 'VCC [W]',
    #                                  'Nominal Power VCC to AHU_ARU_SCU [W]': 'VCC [W]',
    #                                  'Nominal Power VCC to SCU [W]': 'VCC_high_T [W]',
    #                                  'Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]': 'single effect ACH [W]',
    #                                  'Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]': 'single effect ACH [W]'},
    #                         inplace = True)

    return bui_results_best


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    generation = '0'
    individual = '0'
    print('Fetching supply system configuration of... generation: %s, individual: %s' % (generation, individual))
    supply_system_configuration(generation, individual, locator, config)
    print('Done!')


if __name__ == '__main__':
    main(cea.config.Configuration())
