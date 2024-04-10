


import math

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR, SOIL_Cp_JkgK, SOIL_lambda_WmK, SOIL_rho_kgm3, GW_TEMPERATURE, PERMEABIL, PIEZ, DIST_PIEZ, MAX_T_INCREASE, HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import GHP_HMAX_SIZE, GHP_A
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_geothermal_potential(locator, config):
    "A very simplified calculation based on the area available"

    # local variables
    weather_file = locator.get_weather_file()
    buildings = config.shallow_geothermal.buildings_available
    extra_area = config.shallow_geothermal.extra_area_available
    depth_m = config.shallow_geothermal.average_probe_depth

    permeability = PERMEABIL
    water_level_piezometers = PIEZ
    dist_piezometers = DIST_PIEZ
    water_temperature_raise = MAX_T_INCREASE
    water_heat_capacity = HEAT_CAPACITY_OF_WATER_JPERKGK

    # dataprocessing
    area_below_buildings = calc_area_buildings(locator, buildings)
    T_ambient_C = epwreader.epw_reader(weather_file)[['drybulb_C']].values

    # total area available
    area_geothermal = extra_area + area_below_buildings

    T_ground_K = calc_ground_temperature(T_ambient_C, depth_m)

    # convert back to degrees C
    t_source_final = [x - 273 for x in T_ground_K]
    t_source_avg = np.mean(t_source_final)

    gw_flow = calc_groundwater_flow(permeability, water_level_piezometers, dist_piezometers) #L/s

    Q_max_kwh = [(gw_flow * water_heat_capacity / 1000) * (water_temperature_raise - x) for x in t_source_final]   # in kW

    # export
    output_file = locator.get_geothermal_potential()
    pd.DataFrame({"Ts_C": t_source_final, "QGHP_kW": Q_max_kwh, "Area_avail_m2": area_geothermal}).to_csv(output_file,
                                                                                                          index=False,
                                                                                                          float_format='%.3f')
    update_ec(locator, t_source_avg)


def calc_area_buildings(locator, buildings_list):
    # initialize value
    prop_geometry = Gdf.from_file(locator.get_zone_geometry())
    prop_geometry['footprint'] = prop_geometry.area

    footprint = prop_geometry[prop_geometry["Name"].isin(buildings_list)]['footprint']
    area_below_buildings = footprint.sum()

    return area_below_buildings



def calc_ground_temperature(T_ambient_C, depth_m):
    """
    Calculates hourly ground temperature fluctuation over a year following [Kusuda, T. et al., 1965]_.

    :param T_ambient_C: vector with outdoor temperature
    :type T_ambient_C: np array
    :param depth_m: depth


    :return T_ground_K: vector with ground temperatures in [K]
    :rtype T_ground_K: np array

    ..[Kusuda, T. et al., 1965] Kusuda, T. and P.R. Achenbach (1965). Earth Temperatures and Thermal Diffusivity at
    Selected Stations in the United States. ASHRAE Transactions. 71(1):61-74
    """

    heat_capacity_soil = SOIL_Cp_JkgK
    conductivity_soil = SOIL_lambda_WmK
    density_soil = SOIL_rho_kgm3

    T_avg = np.mean(T_ambient_C) + 273.15  # to K
    T_amplitude = abs((max(T_ambient_C)[0] + 273.15 - T_avg))  # K
    T_ground_K = calc_temperature_underground(T_amplitude, T_avg, conductivity_soil, density_soil, depth_m,
                                              heat_capacity_soil)

    return T_ground_K


def calc_temperature_underground(T_amplitude_K, T_avg, conductivity_soil, density_soil, depth_m, heat_capacity_soil):
    diffusivity = conductivity_soil / (density_soil * heat_capacity_soil)  # in m2/s
    wave_lenght = (math.pi * 2 / HOURS_IN_YEAR)
    hour_with_minimum = 1
    e = math.sqrt(wave_lenght / (2 * diffusivity)) * depth_m  # soil constants
    T_ground_K = [T_avg + T_amplitude_K * (math.exp(-e) * math.cos(wave_lenght * (i - hour_with_minimum) - e))
                  for i in range(1, HOURS_IN_YEAR + 1)]

    return T_ground_K

def calc_groundwater_flow(permeability, water_level_piezometers, dist_piezometers):

    flow_L_s = (math.pi * permeability * (water_level_piezometers[1] ** 2 - water_level_piezometers[0] ** 2) /
                math.log(dist_piezometers[1] / dist_piezometers[0])) * 1000  # L/s

    return flow_L_s

def update_ec(locator, groundwater_temperature):
    water_temp = math.trunc(groundwater_temperature)
    e_carriers = pd.read_excel(locator.get_database_energy_carriers(), sheet_name='ENERGY_CARRIERS')
    row_copy = e_carriers.loc[e_carriers['description'] == 'Fresh water'].copy()
    row_copy['mean_qual'] = water_temp
    row_copy['code'] = f'T{water_temp}LW'
    row_copy['description'] = 'Ground Water'
    row_copy['subtype'] = 'water sink'

    if not e_carriers.loc[e_carriers['description'] == 'Ground Water'].empty:
        row_copy.index = e_carriers.loc[e_carriers['description'] == 'Ground Water'].index
        e_carriers.loc[e_carriers['description'] == 'Ground Water'] = row_copy.copy()
    else:
        e_carriers = pd.concat([e_carriers, row_copy], axis=0)

    e_carriers.to_excel(locator.get_database_energy_carriers(), sheet_name='ENERGY_CARRIERS', index=False)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    calc_geothermal_potential(locator=locator, config=config)

if __name__ == '__main__':
    main(cea.config.Configuration())
