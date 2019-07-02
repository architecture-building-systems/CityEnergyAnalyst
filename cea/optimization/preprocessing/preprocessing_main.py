"""
Pre-processing algorithm

"""

from __future__ import division

import os
import cea.config
import cea.globalvar
import cea.inputlocator
import pandas as pd
import numpy as np

from cea.optimization.master import summarize_network
from cea.technologies import substation
from cea.constants import HOURS_IN_YEAR
from cea.resources.geothermal import calc_ground_temperature
from cea.optimization.constants import Z0
from cea.utilities import epwreader
import cea.optimization.preprocessing.processheat as process_heat
from cea.optimization.preprocessing import electricity

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def preproccessing(locator, total_demand, building_names, weather_file, config, prices, lca):
    """
    This function aims at preprocessing all data for the optimization.

    :param locator: path to locator function
    :param total_demand: dataframe with total demand and names of all building in the area
    :param building_names: dataframe with names of all buildings in the area
    :param weather_file: path to wather file
    :param gv: path to global variables class
    :type locator: class
    :type total_demand: list
    :type building_names: list
    :type weather_file: string
    :type gv: class
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

    # local variables
    network_depth_m = Z0
    district_heating_network = config.optimization.district_heating_network
    district_cooling_network = config.optimization.district_cooling_network

    print("PRE-PROCESSING 1/5: weather properties")
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    ground_temp = calc_ground_temperature(locator, config, T_ambient, depth_m=network_depth_m)

    print("PRE-PROCESSING 2/5: solar features")
    solar_features = SolarFeatures(locator, building_names)

    print("PRE-PROCESSING 3/5: building substations")
    substation.substation_main(locator, total_demand, building_names,
                               heating_configuration=7,
                               cooling_configuration=7,
                               Flag=False)  # True if disconnected buildings are calculated

    print("PRE-PROCESSING 4/5: thermal networks")# at first estimate a distribution with all the buildings connected
    if district_heating_network:
        buildings_names_connected = get_building_names_connected_according_to_load(total_demand, load_name='QH_sys_MWhyr')
        num_tot_buildings = len(buildings_names_connected)
        summarize_network.network_main(locator, buildings_names_connected,
                                       ground_temp, num_tot_buildings, "DH",
                                       "all")  # "_all" key for all buildings
    if district_cooling_network:
        buildings_names_connected = get_building_names_connected_according_to_load(total_demand, load_name='QC_sys_MWhyr')
        num_tot_buildings = len(buildings_names_connected)
        summarize_network.network_main(locator, buildings_names_connected,
                                       ground_temp, num_tot_buildings, "DC","all")  # "_all" key for all buildings

    print("PRE-PROCESSING 5/5: thermal networks""GETTING EXTRA COSTS AND EMISSIONS FROM ELECTRICITY")
    elecCosts, elecCO2, elecPrim = extra_costs_emissions_primary_energy(building_names, config, lca, locator, prices,
                                                                        total_demand)

    return elecCosts, elecCO2, elecPrim, solar_features, ground_temp


def get_building_names_connected_according_to_load(total_demand, load_name):
    building_names = total_demand.Name.values
    buildings_names_connected = []
    for building in building_names:
        demand = total_demand[total_demand['Name'] == building].loc[:, load_name].values[0]
        if demand > 0.0:
            buildings_names_connected.append(building)
    return buildings_names_connected


def extra_costs_emissions_primary_energy(building_names, config, lca, locator, prices, total_demand):
    # GET EXTRAS
    # estimate the extra costs, emissions and primary energy of electricity.
    print
    "electricity"
    elecCosts, elecCO2, elecPrim = electricity.calc_pareto_electricity(locator, lca, config, building_names)
    # estimate the extra costs, emissions and primary energy for process heat
    print
    "Process-heat"
    hpCosts, hpCO2, hpPrim = process_heat.calc_pareto_Qhp(locator, total_demand, prices, lca, config)

    extraCosts = elecCosts + hpCosts
    extraCO2 = elecCO2 + hpCO2
    extraPrim = elecPrim + hpPrim

    # Capex_a and Opex_fixed
    results = pd.DataFrame({"elecCosts": [elecCosts],
                            "hpCosts": [hpCosts],
                            "elecCO2": [elecCO2],
                            "hpCO2": [hpCO2],
                            "elecPrim": [elecPrim],
                            "hpPrim": [hpPrim],
                            "extraCosts": [extraCosts],
                            "extraCO2": [extraCO2],
                            "extraPrim": [extraPrim]
                            })
    results.to_csv(locator.get_preprocessing_costs(), index=False)

    return elecCosts, elecCO2, elecPrim


class SolarFeatures(object):
    def __init__(self, locator, building_names, ):
        E_PV_gen_kWh = np.zeros(HOURS_IN_YEAR)
        E_PVT_gen_kWh = np.zeros(HOURS_IN_YEAR)
        Q_PVT_gen_kWh = np.zeros(HOURS_IN_YEAR)
        Q_SC_FP_gen_kWh = np.zeros(HOURS_IN_YEAR)
        Q_SC_ET_gen_kWh = np.zeros(HOURS_IN_YEAR)
        A_PV_m2 = np.zeros(HOURS_IN_YEAR)
        A_PVT_m2 = np.zeros(HOURS_IN_YEAR)
        A_SC_FP_m2 = np.zeros(HOURS_IN_YEAR)
        A_SC_ET_m2 = np.zeros(HOURS_IN_YEAR)

        for name in building_names:
            building_PV = pd.read_csv(os.path.join(locator.get_potentials_solar_folder(), name + '_PV.csv'))
            building_PVT = pd.read_csv(os.path.join(locator.get_potentials_solar_folder(), name + '_PVT.csv'))
            building_SC_FP = pd.read_csv(os.path.join(locator.get_potentials_solar_folder(), name + '_SC_FP.csv'))
            building_SC_ET = pd.read_csv(os.path.join(locator.get_potentials_solar_folder(), name + '_SC_ET.csv'))
            E_PV_gen_kWh = E_PV_gen_kWh + building_PV['E_PV_gen_kWh']
            E_PVT_gen_kWh = E_PVT_gen_kWh + building_PVT['E_PVT_gen_kWh']
            Q_PVT_gen_kWh = Q_PVT_gen_kWh + building_PVT['Q_PVT_gen_kWh']
            Q_SC_FP_gen_kWh = Q_SC_FP_gen_kWh + building_SC_FP['Q_SC_gen_kWh']
            Q_SC_ET_gen_kWh = Q_SC_ET_gen_kWh + building_SC_ET['Q_SC_gen_kWh']
            A_PV_m2 = building_PV['Area_PV_m2']
            A_PVT_m2 = building_PVT['Area_PVT_m2']
            A_SC_FP_m2 = building_SC_FP['Area_SC_m2']
            A_SC_ET_m2 = building_SC_ET['Area_SC_m2']

        self.Peak_PV_Wh = E_PV_gen_kWh.values.max() * 1E3
        self.A_PV_m2 = A_PV_m2.values.max()
        self.Peak_PVT_Wh = E_PVT_gen_kWh.values.max() * 1E3
        self.Q_nom_PVT_Wh = Q_PVT_gen_kWh.values.max() * 1E3
        self.A_PVT_m2 = A_PVT_m2.values.max()
        self.Q_nom_SC_FP_Wh = Q_SC_FP_gen_kWh.values.max() * 1E3
        self.A_SC_FP_m2 = A_SC_FP_m2.values.max()
        self.Q_nom_SC_ET_Wh = Q_SC_ET_gen_kWh.values.max() * 1E3
        self.A_SC_ET_m2 = A_SC_ET_m2.values.max()


# ============================
# test
# ============================


def main(config):
    """
    run the whole preprocessing routine
    """
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = locator.get_building_names()
    weather_file = config.weather
    preproccessing(locator, total_demand, building_names, weather_file, gv, config)

    print 'test_preprocessing_main() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())
