"""
Pre-processing algorithm

"""

from __future__ import division

from cea.optimization.constants import Z0
from cea.optimization.distribution.network_optimization_features import NetworkOptimizationFeatures
from cea.optimization.master import summarize_network
from cea.resources.geothermal import calc_ground_temperature
from cea.technologies import substation
from cea.utilities import epwreader
from cea.technologies.supply_systems_database import SupplySystemsDatabase
from cea.optimization.lca_calculations import LcaCalculations
from cea.optimization.prices import Prices as Prices
import shutil


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

class WeatherFeatures(object):
    def __init__(self, weather_file, locator):
        self.weather_data = epwreader.epw_reader(weather_file)
        self.date = self.weather_data['date']
        self.T_ambient = self.weather_data['drybulb_C']
        self.ground_temp = calc_ground_temperature(locator, self.T_ambient, depth_m=Z0)


def preproccessing(locator, total_demand, buildings_heating_demand, buildings_cooling_demand,
                   weather_file, district_heating_network, district_cooling_network):
    """
    This function aims at preprocessing all data for the optimization.

    :param locator: path to locator function
    :param total_demand: dataframe with total demand and names of all building in the area
    :param building_names: dataframe with names of all buildings in the area
    :param weather_file: path to wather file
    :type locator: class
    :type total_demand: list
    :type building_names: list
    :type weather_file: string
    :return:
        - extraCosts: extra pareto optimal costs due to electricity and process heat (
            these are treated separately and not considered inside the optimization)
        - extraCO2: extra pareto optimal emissions due to electricity and process heat (
            these are treated separately and not considered inside the optimization)
        - extraPrim: extra pareto optimal primary energy due to electricity and process heat (
            these are treated separately and not considered inside the optimization)
        - solar_features: extraction of solar features form the results of the solar technologies
            calculation.

    :rtype: float, float, float, float

    """
    print("PRE-PROCESSING 0/4: initialize directory")
    shutil.rmtree(locator.get_optimization_master_results_folder())
    shutil.rmtree(locator.get_optimization_network_results_folder())
    shutil.rmtree(locator.get_optimization_slave_results_folder())
    shutil.rmtree(locator.get_optimization_substations_folder())

    print("PRE-PROCESSING 1/4: weather features")  # at first estimate a distribution with all the buildings connected
    weather_features = WeatherFeatures(weather_file, locator)

    print("PRE-PROCESSING 2/4: conversion systems database")  # at first estimate a distribution with all the buildings connected
    supply_systems = SupplySystemsDatabase(locator)

    print("PRE-PROCESSING 3/4: feedstocks systems database")  # at first estimate a distribution with all the buildings connected
    prices = Prices(supply_systems)
    lca = LcaCalculations(supply_systems)

    print("PRE-PROCESSING 4/4: network features")  # at first estimate a distribution with all the buildings connected
    if district_heating_network:
        num_tot_buildings = len(buildings_heating_demand)
        DHN_barcode = ''.join(str(1) for e in range(num_tot_buildings))
        substation.substation_main_heating(locator, total_demand, buildings_heating_demand,
                                           DHN_barcode=DHN_barcode)

        summarize_network.network_main(locator, buildings_heating_demand, weather_features.ground_temp, num_tot_buildings, "DH",
                                       DHN_barcode)
        # "_all" key for all buildings
    if district_cooling_network:
        num_tot_buildings = len(buildings_cooling_demand)
        DCN_barcode = ''.join(str(1) for e in range(num_tot_buildings))
        substation.substation_main_cooling(locator, total_demand, buildings_cooling_demand, DCN_barcode=DCN_barcode)

        summarize_network.network_main(locator, buildings_cooling_demand,
                                       weather_features.ground_temp, num_tot_buildings, "DC",
                                       DCN_barcode)  # "_all" key for all buildings

    network_features = NetworkOptimizationFeatures(district_heating_network, district_cooling_network, locator)

    return weather_features, network_features, prices, lca


def get_building_names_with_load(total_demand, load_name):
    building_names = total_demand.Name.values
    buildings_names_connected = []
    for building in building_names:
        demand = total_demand[total_demand['Name'] == building].loc[:, load_name].values[0]
        if demand > 0.0:
            buildings_names_connected.append(building)
    return buildings_names_connected
