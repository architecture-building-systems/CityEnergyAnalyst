"""
solar equations
"""




import numpy as np
import pandas as pd
import cea.config
import ephem
import datetime
import collections
from math import *
from timezonefinder import TimezoneFinder
import pytz
from cea.constants import HOURS_IN_YEAR

import os
import time
from itertools import repeat
from math import *
from multiprocessing import Pool

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as gdf
from scipy import interpolate

import cea.config
import cea.inputlocator
import cea.utilities.parallel
from cea.analysis.costs.equations import calc_capex_annualized
from cea.constants import HOURS_IN_YEAR
from cea.technologies.solar import constants
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2021, Future Cities Laboratory, Singapore - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "shi@arch.ethz.ch"
__status__ = "Production"


from cea.utilities.date import get_date_range_hours_from_year


# filter sensor points with low solar potential
def filter_low_potential(radiation_json_path, metadata_csv_path, config):
    """
    To filter the sensor points/hours with low radiation potential.

    #. keep sensors above min radiation
    #. eliminate points when hourly production < 50 W/m2
    #. augment the solar radiation due to differences between panel reflectance and original reflectances used in daysim

    :param radiation_csv: solar insulation data on all surfaces of each building
    :type radiation_csv: .csv
    :param metadata_csv: solar insulation sensor data of each building
    :type metadata_csv: .csv

    :return max_annual_radiation: yearly horizontal radiation [Wh/m2/year]
    :rtype max_annual_radiation: float
    :return annual_radiation_threshold: minimum yearly radiation threshold for sensor selection [Wh/m2/year]
    :rtype annual_radiation_threshold: float
    :return sensors_rad_clean: radiation data of the filtered sensors [Wh/m2]
    :rtype sensors_rad_clean: dataframe
    :return sensors_metadata_clean: data of filtered sensor points measuring solar insulation of each building
    :rtype sensors_metadata_clean: dataframe

    Following assumptions are made:

    #. Sensor points with low yearly radiation are deleted. The threshold (minimum yearly radiation) is a percentage
       of global horizontal radiation. The percentage threshold (min_radiation) is a global variable defined by users.
    #. For each sensor point kept, the radiation value is set to zero when radiation value is below 50 W/m2.
    #. Unlike BIPV, window surfaces are not removed for BIA simulations
    """

    # def f(x):
    #     if x <= 50:
    #         return 0
    #     else:
    #         return x

    # read radiation file
    sensors_rad = pd.read_json(radiation_json_path)
    sensors_metadata = pd.read_csv(metadata_csv_path)

    # join total radiation to sensor_metadata
    sensors_rad_sum = sensors_rad.sum(0).to_frame('total_rad_Whm2')  # add new row with yearly radiation
    sensors_metadata.set_index('SURFACE', inplace=True)
    sensors_metadata = sensors_metadata.merge(sensors_rad_sum, left_index=True, right_index=True)  # [Wh/m2]

    # keep sensors if allow pv installation on walls or on roofs
    if config.agriculture.crop_on_roof is False:
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'roofs']
    if config.agriculture.crop_on_wall is False:
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'walls']

    # set min yearly radiation threshold for sensor selection
    # keep sensors above min production in sensors_rad
    max_annual_radiation = sensors_rad_sum.max().values[0]
    annual_radiation_threshold_Whperm2 = float(config.agriculture.annual_radiation_threshold_BIA)*1000
    sensors_metadata_clean = sensors_metadata[sensors_metadata.total_rad_Whm2 >= annual_radiation_threshold_Whperm2]
    sensors_rad_clean = sensors_rad[sensors_metadata_clean.index.tolist()]  # keep sensors above min radiation

    return max_annual_radiation, annual_radiation_threshold_Whperm2, sensors_rad_clean, sensors_metadata_clean

def calc_properties_crop_db(database_path, config):
    """
    To assign PV module properties according to panel types.

    :param type_PVpanel: type of PV panel used
    :type type_PVpanel: string
    :return: dict with Properties of the panel taken form the database
    """
    type_crop = config.solar.type_crop
    data = pd.read_excel(database_path, sheet_name="BIA")
    crop_properties = data[data['code'] == type_crop].reset_index().T.to_dict()[0]

    return crop_properties



def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running Day Light Integral with scenario = %s' % config.scenario)
    #print('Running Day Light Integral with annual-radiation-threshold-kWh/m2 = %s' % config.agriculture.annual_radiation_threshold)


    building_names = locator.get_zone_building_names()
    zone_geometry_df = gdf.from_file(locator.get_zone_geometry())
    latitude, longitude = get_lat_lon_projected_shapefile(zone_geometry_df)

    # list_buildings_names =['B026', 'B036', 'B039', 'B043', 'B050'] for missing buildings
    weather_data = epwreader.epw_reader(locator.get_weather_file())
    date_local = solar_equations.calc_datetime_local_from_weather_file(weather_data, latitude, longitude)

    num_process = config.get_number_of_processes()
    n = len(building_names)
    cea.utilities.parallel.vectorize(filter_low_potential, num_process)(repeat(radiation_json_path, n),
                                                           repeat(metadata_csv_path, n),
                                                           repeat(config, n))

if __name__ == '__main__':
    main(cea.config.Configuration())

