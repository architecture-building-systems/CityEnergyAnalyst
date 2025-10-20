


import math

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR, SOIL_Cp_JkgK, SOIL_lambda_WmK, SOIL_rho_kgm3
from cea.optimization.constants import GHP_HMAX_SIZE, GHP_A
from cea.utilities import epwreader
from cea.utilities.date import get_date_range_hours_from_year

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system


def calc_geothermal_potential(locator, config):
    "A very simplified calculation based on the area available"

    # local variables
    weather_file = locator.get_weather_file()
    buildings = config.shallow_geothermal.buildings_available
    extra_area = config.shallow_geothermal.extra_area_available
    depth_m = config.shallow_geothermal.average_probe_depth

    # dataprocessing
    weather_data = epwreader.epw_reader(weather_file)
    area_below_buildings = calc_area_buildings(locator, buildings)
    T_ambient_C =weather_data[['drybulb_C']].values

    # create date range for the calculation year
    year = weather_data['year'][0]
    date_range = get_date_range_hours_from_year(year)

    # total area available
    area_geothermal = extra_area + area_below_buildings

    T_ground_K = calc_ground_temperature(T_ambient_C, depth_m)

    # convert back to degrees C
    t_source_final = [x[0] - 273 for x in T_ground_K]

    Q_max_kwh = np.ceil(area_geothermal / GHP_A) * GHP_HMAX_SIZE / 1000  # [kW th]

    # export
    output_file = locator.get_geothermal_potential()
    # Ensure the output directory exists
    locator.ensure_parent_folder_exists(output_file)
    pd.DataFrame({"date": pd.to_datetime(date_range), "Ts_C": t_source_final, "QGHP_kW": Q_max_kwh, "Area_avail_m2": area_geothermal}).to_csv(output_file,
                                                                                                          index=False,
                                                                                                          float_format='%.3f')


def calc_area_buildings(locator, buildings_list):
    # initialize value
    prop_geometry = Gdf.from_file(locator.get_zone_geometry())

    # reproject to projected coordinate system (in meters) to calculate area
    lat, lon = get_lat_lon_projected_shapefile(prop_geometry)
    prop_geometry = prop_geometry.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    prop_geometry['footprint'] = prop_geometry.area

    footprint = prop_geometry[prop_geometry["name"].isin(buildings_list)]['footprint']
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

    T_amplitude = abs((max(T_ambient_C) - min(T_ambient_C)) + 273.15)  # to K
    T_avg = np.mean(T_ambient_C) + 273.15  # to K
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


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(config.scenario)
    calc_geothermal_potential(locator=locator, config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())
