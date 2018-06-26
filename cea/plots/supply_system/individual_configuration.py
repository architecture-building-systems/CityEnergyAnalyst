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
from cea.optimization.constants import SIZING_MARGIN
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.technologies.solar import constants
from cea.technologies.solar.photovoltaic import calc_Cinv_pv, calc_Crem_pv
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
    district_supply_sys_columns = ['Lake [W]', 'VCC(LT) [W]', 'VCC(HT) [W]', 'single effect ACH(LT) [W]',
                                   'single effect ACH(HT) [W]', 'DX [W]', 'CCGT_heat [W]', 'SC_FP [m2]', 'SC_ET [m2]',
                                   'PV [m2]', 'Storage [W]', 'CT [W]', 'Capex_a', 'Opex_a']
    district_supply_sys = pd.DataFrame(columns=district_supply_sys_columns)
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

        # get centralized system
        cen_cooling_sys_detail = calc_cen_supply_sys_cooling(generation, individual, district_supply_sys_columns,
                                                             locator)
        district_supply_sys = district_supply_sys.append(cen_cooling_sys_detail)

        # get supply systems at decentralized buildings
        for building in decentralized_buildings:
            bui_cooling_sys_config = calc_building_supply_system(individual_system_configuration, network_name)
            district_supply_sys = district_supply_sys.append(
                calc_bui_sys_decentralized(building, bui_cooling_sys_config, district_supply_sys_columns, locator, config))

        # get supply systems at network connected buildings
        for building in network_connected_buildings:
            district_supply_sys = district_supply_sys.append(
                calc_bui_sys_network_connected(building, district_supply_sys_columns, locator, config))

    return district_supply_sys


def calc_bui_sys_network_connected(building, district_supply_sys_columns, locator, config):
    bui_sys_detail = pd.DataFrame(columns=district_supply_sys_columns, index=[building])
    bui_sys_detail = bui_sys_detail.fillna(0.0)

    Capex_a_PV, Opex_a_PV, PV_installed_area_m2 = calc_pv_costs(building, config, locator)

    bui_sys_detail.loc[building, 'PV [m2]'] = PV_installed_area_m2
    bui_sys_detail.loc[building, 'Capex_a'] = Capex_a_PV
    bui_sys_detail.loc[building, 'Opex_a'] = Opex_a_PV
    return bui_sys_detail


def calc_cen_costs_cooling(generation, individual, locator):
    cooling_costs = pd.read_csv(
        locator.get_optimization_slave_investment_cost_detailed_cooling(individual, generation))
    capex_a_columns = [item for item in cooling_costs.columns if 'Capex_a' in item]
    cen_capex_a = cooling_costs[capex_a_columns].sum(axis=1).values[0]
    opex_a_columns = [item for item in cooling_costs.columns if 'Opex' in item]
    cen_opex_a = cooling_costs[opex_a_columns].sum(axis=1).values[0]
    return cen_capex_a, cen_opex_a


def calc_cen_supply_sys_cooling(generation, individual, district_supply_sys_columns, locator):
    cooling_activation_column = ['Q_from_ACH_W', 'Q_from_Lake_W', 'Q_from_VCC_W', 'Q_from_VCC_backup_W',
                                 'Q_from_storage_tank_W', 'Qc_CT_associated_with_all_chillers_W',
                                 'Qh_CCGT_associated_with_absorption_chillers_W']
    cooling_activation_pattern = pd.read_csv(
        locator.get_optimization_slave_cooling_activation_pattern(individual, generation))
    cen_cooling_sys = cooling_activation_pattern[cooling_activation_column].max()

    cen_cooling_sys_detail = pd.DataFrame(columns=district_supply_sys_columns, index=['Centralized Plant'])
    cen_cooling_sys_detail = cen_cooling_sys_detail.fillna(0.0)

    cen_cooling_sys_detail.loc['Centralized Plant', 'Lake [W]'] = cen_cooling_sys['Q_from_Lake_W']
    cen_cooling_sys_detail.loc['Centralized Plant', 'VCC(LT) [W]'] = cen_cooling_sys['Q_from_VCC_W'] + cen_cooling_sys[
        'Q_from_VCC_backup_W']
    cen_cooling_sys_detail.loc['Centralized Plant', 'single effect ACH(LT) [W]'] = cen_cooling_sys['Q_from_ACH_W']
    cen_cooling_sys_detail.loc['Centralized Plant', 'Storage [W]'] = cen_cooling_sys['Q_from_storage_tank_W']
    cen_cooling_sys_detail.loc['Centralized Plant', 'CT [W]'] = cen_cooling_sys['Qc_CT_associated_with_all_chillers_W']
    cen_cooling_sys_detail.loc['Centralized Plant', 'CCGT_heat [W]'] = cen_cooling_sys[
        'Qh_CCGT_associated_with_absorption_chillers_W']
    cen_capex_a, cen_opex_a = calc_cen_costs_cooling(generation, individual, locator)
    cen_cooling_sys_detail.loc['Centralized Plant', 'Capex_a'] = cen_capex_a
    cen_cooling_sys_detail.loc['Centralized Plant', 'Opex_a'] = cen_opex_a

    return cen_cooling_sys_detail


# def calc_cen_supply_sys_electricity(network_name, generation, individual, locator):
#     if network_name == 'DCN':
#         el_activation_columns = ['Area_PV_m2', 'E_CHP_to_directload_W', 'E_CHP_to_grid_W', 'E_PV_W', 'E_from_grid_W']
#         el_activation_pattern = pd.read_csv(
#             locator.get_optimization_slave_electricity_activation_pattern_cooling(individual, generation))
#         el_sys_activation_pattern = el_activation_pattern[el_activation_columns]
#         el_sys_activation_pattern['E_CHP_W'] = el_activation_pattern['E_CHP_to_directload_W'] + el_activation_pattern[
#             'E_CHP_to_grid_W']
#         el_sys_activation_pattern.drop('E_CHP_to_directload_W', axis=1, inplace=True)
#         el_sys_activation_pattern.drop('E_CHP_to_grid_W', axis=1, inplace=True)
#         cen_el_supply_sys = el_sys_activation_pattern.max()
#     elif network_name == 'DHN':
#         el_activation_columns = ['Area_PV_m2', 'E_CHP_to_directload_W', 'E_CHP_to_grid_W', 'E_PV_W', 'E_from_grid_W']
#         el_activation_pattern = pd.read_csv(
#             locator.get_optimization_slave_electricity_activation_pattern_heating(individual, generation))
#         el_sys_activation_pattern = el_activation_pattern[el_activation_columns]
#         el_sys_activation_pattern['E_CHP_W'] = el_activation_pattern['E_CHP_to_directload_W'] + el_activation_pattern[
#             'E_CHP_to_grid_W']
#         el_sys_activation_pattern.drop('E_CHP_to_directload_W', axis=1, inplace=True)
#         el_sys_activation_pattern.drop('E_CHP_to_grid_W', axis=1, inplace=True)
#         cen_el_supply_sys = el_sys_activation_pattern.max()
#     else:
#         raise ValueError('Wrong network_name')
#
#     return cen_el_supply_sys


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


def calc_bui_sys_decentralized(building, bui_sys_config, district_supply_sys_columns, locator, config):
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

        Capex_a_PV, Opex_a_PV, PV_installed_area_m2 = calc_pv_costs(building, config, locator)
        Capex_a_total = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]'] + Capex_a_PV
        Opex_a_total = bui_results_best.loc[0, 'Operation Costs [CHF]'] + Opex_a_PV

        bui_sys_detail.loc[building, 'PV [m2]'] = PV_installed_area_m2
        bui_sys_detail.loc[building, 'Capex_a'] = Capex_a_total
        bui_sys_detail.loc[building, 'Opex_a'] = Opex_a_total


    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU_SCU [W]'], 0.0):
        VCC_size_W = bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU_SCU [W]']
        CT_size_W = calc_CT_size_for_VCC(VCC_size_W)
        bui_sys_detail.loc[building, 'VCC(LT) [W]'] = VCC_size_W
        bui_sys_detail.loc[building, 'CT [W]'] = CT_size_W

        Capex_a_PV, Opex_a_PV, PV_installed_area_m2 = calc_pv_costs(building, config, locator)
        Capex_a_total = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]'] + Capex_a_PV
        Opex_a_total = bui_results_best.loc[0, 'Operation Costs [CHF]'] + Opex_a_PV

        bui_sys_detail.loc[building, 'PV [m2]'] = PV_installed_area_m2
        bui_sys_detail.loc[building, 'Capex_a'] = Capex_a_total
        bui_sys_detail.loc[building, 'Opex_a'] = Opex_a_total



    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]'], 0.0):
        ACH_size_W = bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]']
        CT_size_W = calc_CT_size_for_ACH(ACH_size_W)
        bui_sys_detail.loc[building, 'single effect ACH(LT) [W]'] = ACH_size_W
        bui_sys_detail.loc[building, 'CT [W]'] = CT_size_W
        sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, 'FP'))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'SC_FP [m2]'] = sc_installed_area
        bui_sys_detail.loc[building, 'Capex_a'] = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]']
        bui_sys_detail.loc[building, 'Opex_a'] = bui_results_best.loc[0, 'Operation Costs [CHF]']

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]'], 0.0):
        ACH_size_W = bui_results_best.loc[0, 'Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]']
        CT_size_W = calc_CT_size_for_ACH(ACH_size_W)
        bui_sys_detail.loc[building, 'single effect ACH(LT) [W]'] = ACH_size_W
        bui_sys_detail.loc[building, 'CT [W]'] = CT_size_W
        sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, 'ET'))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'SC_ET [m2]'] = sc_installed_area
        bui_sys_detail.loc[building, 'Capex_a'] = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]']
        bui_sys_detail.loc[building, 'Opex_a'] = bui_results_best.loc[0, 'Operation Costs [CHF]']

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power VCC to SCU [W]'], 0.0):
        VCC_HT_size_W = bui_results_best.loc[0, 'Nominal Power VCC to SCU [W]']
        VCC_LT_size_W = bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU [W]']
        CT_size_W = calc_CT_size_for_VCC(sum(VCC_HT_size_W,VCC_LT_size_W))
        bui_sys_detail.loc[building, 'VCC(HT) [W]'] = VCC_HT_size_W
        bui_sys_detail.loc[building, 'VCC(LT) [W]'] = VCC_LT_size_W
        bui_sys_detail.loc[building, 'CT [W]'] = CT_size_W

        Capex_a_PV, Opex_a_PV, PV_installed_area_m2 = calc_pv_costs(building, config, locator)
        Capex_a_total = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]'] + Capex_a_PV
        Opex_a_total = bui_results_best.loc[0, 'Operation Costs [CHF]'] + Opex_a_PV

        bui_sys_detail.loc[building, 'PV [m2]'] = PV_installed_area_m2
        bui_sys_detail.loc[building, 'Capex_a'] = Capex_a_total
        bui_sys_detail.loc[building, 'Opex_a'] = Opex_a_total

    elif not np.isclose(bui_results_best.loc[0, 'Nominal Power single effect ACH to SCU (FP) [W]'], 0.0):
        ACH_HT_size_W = bui_results_best.loc[0, 'Nominal Power single effect ACH to SCU (FP) [W]']
        CT_for_ACH_size = calc_CT_size_for_ACH(ACH_HT_size_W)
        VCC_LT_size_W = bui_results_best.loc[0, 'Nominal Power VCC to AHU_ARU [W]']
        CT_for_VCC_size = calc_CT_size_for_VCC(VCC_LT_size_W)
        bui_sys_detail.loc[building, 'single effect ACH(HT) [W]'] = ACH_HT_size_W
        bui_sys_detail.loc[building, 'VCC(LT) [W]'] = VCC_LT_size_W
        bui_sys_detail.loc[building, 'CT [W]'] = CT_for_ACH_size + CT_for_VCC_size
        sc_installed_area = pd.read_csv(locator.SC_metadata_results(building, 'FP'))['area_installed_module_m2'].sum()
        bui_sys_detail.loc[building, 'SC_FP [m2]'] = sc_installed_area
        bui_sys_detail.loc[building, 'Capex_a'] = bui_results_best.loc[0, 'Annualized Investment Costs [CHF]']

    else:
        raise ValueError('No cooling system is specified for the decentralized building ', building)


    return bui_sys_detail


def calc_pv_costs(building, config, locator):
    pv_installed_building = pd.read_csv(locator.PV_results(building))[['E_PV_gen_kWh', 'Area_PV_m2']]
    pv_installed_area = pv_installed_building['Area_PV_m2'].max()
    pv_annual_production_kWh = pv_installed_building['E_PV_gen_kWh'].sum()
    Capex_a_PV, Opex_a_fixed_PV = calc_Cinv_pv(pv_installed_area, locator, config)
    Opex_a_PV = calc_opex_PV(pv_annual_production_kWh, pv_installed_area) + Opex_a_fixed_PV
    return Capex_a_PV, Opex_a_PV, pv_installed_area


def calc_opex_PV(pv_annual_production_kWh, pv_installed_area_m2):
    """
    calculate the operation cost from selling electricity produced from PV to the grid
    :param pv_annual_production_kWh: 
    :param pv_installed_area_m2: 
    :return: 
    """
    P_nom_PV_W = (1000 * 0.16) * pv_installed_area_m2
    Opex_a_PV = (pv_annual_production_kWh * calc_Crem_pv(P_nom_PV_W)/100)*(-1) # from cent to dollar, negative sign indicating income
    return Opex_a_PV


def calc_CT_size_for_ACH(ACH_size_W):
    EER = 0.76 #TODO: this is an assumption since the values are not saved at the moment
    CT_size_W = ACH_size_W*((EER + 1) / EER) * (1 + SIZING_MARGIN)
    return CT_size_W


def calc_CT_size_for_VCC(VCC_size_W):
    COP = 2.78 #TODO: this is an assumption since the values are not saved at the moment
    CT_size_W = VCC_size_W*((COP + 1) / COP) * (1 + SIZING_MARGIN)
    return CT_size_W


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    generation = '0'
    individual = '0'
    print('Fetching supply system configuration of... generation: %s, individual: %s' % (generation, individual))
    district_supply_sys = supply_system_configuration(generation, individual, locator, config)
    print('Done!')


if __name__ == '__main__':
    main(cea.config.Configuration())
