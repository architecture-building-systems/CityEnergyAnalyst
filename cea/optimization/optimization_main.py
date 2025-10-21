"""
multi-objective optimization of supply systems for the CEA
"""

import os
import time
import warnings

import pandas as pd

import cea.config
import cea.inputlocator
from cea.optimization.master import master_main
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load
from cea.optimization.preprocessing.preprocessing_main import preproccessing
from cea.optimization.constants import DH_ACRONYM, DC_ACRONYM

warnings.filterwarnings("ignore")

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-an Ngugen", "Jimeno A. Fonseca", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# optimization

def moo_optimization(locator, weather_file, config):
    '''
    This function optimizes the conversion, storage and distribution systems of a heating distribution for the case
    study. It requires that the energy demand, technology potential and thermal networks are simulated, as follows:

        - energy demand simulation: run cea/demand/demand_main.py
        - PV potential: run cea/technologies/solar/photovoltaic.py
        - PVT potential: run cea/technologies/solar/photovoltaic_thermal.py
        - flat plate solar collector potential: run cea/technologies/solar/solar_collector.py with
          config.solar.type_scpanel = 'FP'
        - evacuated tube solar collector potential: run cea/technologies/solar/solar_collector.py with
          config.solar.type_scpanel = 'ET'
        - waste water heat recovery: run cea/resources/sewage_heat_exchanger.py
        - lake water potential: run cea/resources/water_body_potential.py
        - thermal network simulation: run cea/technologies/thermal_network/thermal_network.py
          if no network is currently present in the case study, consider running network_layout/main.py first
        - decentralized building simulation: run cea/optimization/preprocessing/decentralized_building_main.py

    :param locator: path to input locator
    :param weather_file: path to weather file
    :type locator: cea.inputlocator.InputLocator
    :type weather_file: string

    :returns: None
    :rtype: Nonetype
    '''
    t0 = time.perf_counter()

    # read total demand file and names and number of all buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names_all = list(total_demand.Name.values)  # needs to be a list to avoid errors

    # local flags
    if config.optimization.network_type == DH_ACRONYM:
        district_heating_network = True
        district_cooling_network = False
    elif config.optimization.network_type == DC_ACRONYM:
        district_heating_network = False
        district_cooling_network = True
    else:
        raise Exception("no valid values for 'network-type' input parameter")

    # GET NAMES_OF BUILDINGS THAT HAVE HEATING, COOLING AND ELECTRICITY LOAD SEPARATELY
    buildings_heating_demand = get_building_names_with_load(total_demand, load_name='QH_sys_MWhyr')
    buildings_cooling_demand = get_building_names_with_load(total_demand, load_name='QC_sys_MWhyr')
    buildings_electricity_demand = get_building_names_with_load(total_demand, load_name='E_sys_MWhyr')

    # pre-process information regarding resources and technologies (they are treated before the optimization)
    # optimize best systems for every individual building (they will compete against a district distribution solution)
    print("PRE-PROCESSING")
    weather_features, network_features, prices, lca = preproccessing(locator,
                                                                     total_demand,
                                                                     buildings_heating_demand,
                                                                     buildings_cooling_demand,
                                                                     weather_file,
                                                                     district_heating_network,
                                                                     district_cooling_network)

    # optimize conversion systems
    print("SUPPLY SYSTEMS OPTIMIZATION")
    master_main.non_dominated_sorting_genetic_algorithm(locator,
                                                        building_names_all,
                                                        district_heating_network,
                                                        district_cooling_network,
                                                        buildings_heating_demand,
                                                        buildings_cooling_demand,
                                                        buildings_electricity_demand,
                                                        network_features,
                                                        weather_features,
                                                        config,
                                                        prices,
                                                        lca)

    t1 = time.perf_counter()
    print('Centralized Optimization succeeded after %s seconds' % (t1 - t0))


# ============================
# test
# ============================


def main(config: cea.config.Configuration):
    """
    run the whole optimization routine
    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_file = locator.get_weather_file()

    try:
        check_input_files(config, locator)
    except ValueError as err:
        import sys
        print(err)
        sys.exit(1)
    moo_optimization(locator=locator, weather_file=weather_file, config=config)


def check_input_files(config, locator):
    """
    Raise a ``ValueError`` if any of the required input files are missing.
    :param cea.config.Configuration config: The config object to use
    :param cea.config.InputLocator locator: The input locator to use
    :return: None
    """
    network_type = config.optimization.network_type
    if not demand_files_exist(locator):
        raise ValueError("Missing demand data of the scenario. Consider running demand script first.")
    if not os.path.exists(locator.SC_totals(panel_type='FP')):
        raise ValueError(
            "Missing SC potential of panel type 'FP' of the scenario. Consider running solar-collector script first with panel_type as FP and t-in-SC as 75")
    if not os.path.exists(locator.SC_totals(panel_type='ET')):
        raise ValueError(
            "Missing SC potential of panel type 'ET' of the scenario. Consider running solar-collector script first with panel_type as ET and t-in-SC as 150")
    if not os.path.exists(locator.get_thermal_network_edge_list_file(network_type, '')):
        raise ValueError(
            "Missing thermal network simulation results. Consider running thermal network simulation script first.")


def demand_files_exist(locator):
    """verify that the necessary demand files exist"""
    return all(os.path.exists(locator.get_demand_results_file(building_name)) for building_name in
               locator.get_zone_building_names())


if __name__ == '__main__':
    main(cea.config.Configuration())
