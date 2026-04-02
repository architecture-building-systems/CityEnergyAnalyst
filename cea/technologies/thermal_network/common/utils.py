"""
Shared utility helpers for thermal network models.
"""
import pandas as pd

from cea.resources.geothermal import calc_ground_temperature
from cea.technologies.constants import NETWORK_DEPTH
from cea.utilities.date import get_date_range_hours_from_year
from cea.utilities.epwreader import epw_reader


def add_date_to_dataframe(locator, df):
    # create date range for the calculation year
    weather_file = locator.get_weather_file()
    weather_data = epw_reader(weather_file)
    year = weather_data['year'][0]
    date_range = get_date_range_hours_from_year(year)

    # Convert date_range to datetime
    date_column = pd.to_datetime(date_range, errors='coerce')

    # Insert the 'date' column at the first position
    df.insert(0, 'date', date_column)

    return df


def calculate_ground_temperature(locator):
    """
    calculate ground temperatures.

    :param locator:
    :return: list of ground temperatures, one for each hour of the year
    :rtype: list[np.float64]
    """
    weather_file = locator.get_weather_file()
    T_ambient_C = epw_reader(weather_file)['drybulb_C']
    network_depth_m = NETWORK_DEPTH  # [m]
    T_ground_K = calc_ground_temperature(T_ambient_C.values, network_depth_m)

    return T_ground_K
