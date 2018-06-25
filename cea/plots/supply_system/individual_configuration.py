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
    # get supply system configuration of a particular individual
    all_individuals = pd.read_csv(locator.get_optimization_all_individuals())
    individual_system_configuration = all_individuals.loc[
        (all_individuals['generation'].isin([generation])) & all_individuals['individual'].isin([individual])]

    if config.optimization.isheating:
        network_name = 'DHN'
        centralized_cost_detail_heating = pd.read_csv(
            locator.get_optimization_slave_investment_cost_detailed(individual, generation))
    if config.optimization.iscooling:
        network_name = 'DCN'

        # get supply systems at centralized plants
        centralized_cost_detail_cooling = pd.read_csv(
            locator.get_optimization_slave_investment_cost_detailed_cooling(individual, generation))
        DCN_buildings_list = [item for item in individual_system_configuration.columns if
                              network_name in item and 'B' in item]
        DCN_buildings_df = individual_system_configuration[DCN_buildings_list]

        DCN_connected_buildings = DCN_buildings_df[DCN_buildings_df[DCN_buildings_list] > 0.00000].dropna(
            axis=1).columns
        DCN_connected_buildings = [x.split()[0] for x in DCN_connected_buildings]

        # get supply systems at decentralized buildings
        DCN_decentralized_buildings = DCN_buildings_df[DCN_buildings_df[DCN_buildings_list] < 1.00000].dropna(
            axis=1).columns
        DCN_decentralized_buildings = [x.split()[0] for x in DCN_decentralized_buildings]
        decentralized_tech_list = ['VCC', 'single effect ACH', 'double effect ACH', 'DX', 'SC']
        bui_supply_sys = {}
        for building in DCN_decentralized_buildings:
            bui_sys_config = calc_building_supply_system(individual_system_configuration, network_name)
            bui_supply_sys[building] = calc_bui_sys_detail(building, bui_sys_config, locator)
    return


def calc_building_supply_system(individual_system_configuration, network_name):
    all_configuration_dict = {1: "ARU_SCU", 2: "AHU_SCU", 3: "AHU_ARU", 4: "SCU", 5: "ARU", 6: "AHU", 7: "AHU_ARU_SCU"}
    unit_configuration_name = network_name + ' unit configuration'
    unit_configuration = int(individual_system_configuration[unit_configuration_name].values[0])
    if unit_configuration in all_configuration_dict:
        decentralized_config = all_configuration_dict[unit_configuration]
    else:
        raise ValueError('DCN unit configuration does not exist.')
    return decentralized_config


def calc_bui_sys_detail(building, bui_sys_config, locator):
    # get nominal power and costs from disconnected calculation
    bui_results = pd.read_csv(
        locator.get_optimization_disconnected_folder_building_result_cooling(building, bui_sys_config))
    bui_results_best = bui_results[bui_results['Best configuration'] > 0.0]

    technology_columns = [item for item in bui_results_best.columns if 'Nominal Power' in item]
    cost_columns = [item for item in bui_results_best.columns if 'Costs' in item]
    technology_columns.extend(cost_columns)
    bui_results_best = bui_results_best[technology_columns].reset_index(drop=True)

    # get installed area of solar collectors
    sc_panel_types = ['FP', 'ET']
    for panel_type in sc_panel_types:
        columns = [item for item in bui_results_best.columns if panel_type in item]
        for tech in columns:
            if not np.isclose(bui_results_best[tech], 0.0):
                installed_area = pd.read_csv(locator.SC_metadata_results(building, panel_type))[
                    'area_installed_module_m2'].sum()
                bui_results_best.loc[0, panel_type] = installed_area

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
