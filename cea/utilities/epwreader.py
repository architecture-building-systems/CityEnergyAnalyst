"""
Energyplus file reader
"""

import pandas as pd
import math
import cea.inputlocator
import numpy as np
from cea.constants import BOLTZMANN, KELVIN_OFFSET, HOURS_IN_YEAR
from calendar import isleap

__author__ = "Clayton Miller"
__copyright__ = "Copyright 2014, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Clayton Miller", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.utilities.date import get_date_range_hours_from_year


HOR_IR_SKY_NO_VALUE = 9999
OPAQUE_SKY_NO_VALUE = 99

def epw_to_dataframe(weather_path):
    epw_labels = ['year', 'month', 'day', 'hour', 'minute', 'datasource', 'drybulb_C', 'dewpoint_C', 'relhum_percent',
                  'atmos_Pa', 'exthorrad_Whm2', 'extdirrad_Whm2', 'horirsky_Whm2', 'glohorrad_Whm2',
                  'dirnorrad_Whm2', 'difhorrad_Whm2', 'glohorillum_lux', 'dirnorillum_lux', 'difhorillum_lux',
                  'zenlum_lux', 'winddir_deg', 'windspd_ms', 'totskycvr_tenths', 'opaqskycvr_tenths', 'visibility_km',
                  'ceiling_hgt_m', 'presweathobs', 'presweathcodes', 'precip_wtr_mm', 'aerosol_opt_thousandths',
                  'snowdepth_cm', 'days_last_snow', 'Albedo', 'liq_precip_depth_mm', 'liq_precip_rate_Hour']

    df = pd.read_csv(weather_path, skiprows=8, header=None, names=epw_labels, encoding="utf-8").drop('datasource',
                                                                                                     axis=1)

    return df


def epw_reader(weather_path):
    epw_data = epw_to_dataframe(weather_path)

    year = epw_data["year"][0]
    # Create date range from epw data
    date_range = pd.DatetimeIndex(
        pd.to_datetime(dict(year=epw_data.year, month=epw_data.month, day=epw_data.day, hour=epw_data.hour - 1))
    )
    epw_data['date'] = date_range
    epw_data['dayofyear'] = date_range.dayofyear
    if isleap(year):
        epw_data = epw_data[~((date_range.month == 2) & (date_range.day == 29))].reset_index()

    # Make sure data has the correct number of rows
    if len(epw_data) != HOURS_IN_YEAR:
        # Check for missing dates from expected date range
        expected_date_index = get_date_range_hours_from_year(year)
        difference = expected_date_index.difference(epw_data.index)
        if len(difference):
            print(f"Dates missing: {difference}")
        raise ValueError(f'Incorrect number of rows. Expected {HOURS_IN_YEAR}, got {len(epw_data)}')

    try:
        epw_data['ratio_diffhout'] = epw_data['difhorrad_Whm2'] / epw_data['glohorrad_Whm2']
        epw_data['ratio_diffhout'] = epw_data['ratio_diffhout'].replace(np.inf, np.nan)
        epw_data['wetbulb_C'] = np.vectorize(calc_wetbulb)(epw_data['drybulb_C'], epw_data['relhum_percent'])
        epw_data['skytemp_C'] = np.vectorize(calc_skytemp)(epw_data['horirsky_Whm2'],
                                                           epw_data['drybulb_C'], epw_data['dewpoint_C'],
                                                           epw_data['opaqskycvr_tenths'])
    except ValueError as e:
        raise ValueError(f"Errors found in the provided weather file: {e}") from e

    return epw_data

def epw_location(weather_path):
    """
    Returns the location of the EPW file as a tuple (latitude, longitude, utc, elevation).

    :param weather_path: Path to the EPW file
    :return: dict containing latitude, longitude, utc, and elevation
    """
    with open(weather_path, 'r') as f:
        epw_data = f.readlines()
        
    lat = float(epw_data[0].split(',')[6])
    lon = float(epw_data[0].split(',')[7])
    utc = float(epw_data[0].split(',')[8])
    elevation = float(epw_data[0].split(',')[9].strip("\n"))

    return {"latitude": lat, "longitude": lon, "utc": utc, "elevation": elevation}


def calc_horirsky(Tdrybulb, Tdewpoint, N):
    """
    Based on the equation found here:
    https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v24.1.0/EngineeringReference.pdf (Section 5.1.2)

    :param Tdrybulb: Dry bulb temperature [C]
    :param Tdewpoint: Wet bulb temperature [C]
    :param N: opaque skycover in [tenths], minimum is 0, maximum is 10 see: http://glossary.ametsoc.org/wiki/Sky_cover
    :return: horizontal infrared radiation intensity [Whm2]
    """

    if N == OPAQUE_SKY_NO_VALUE:
        raise ValueError(f"Opaque Sky Cover (column 23) has a missing value. (found {N})")
    elif N > 10:
        raise ValueError(f"Opaque Sky Cover (column 23) is above 10. (found {N})")
    elif N < 0:
        raise ValueError(f"Opaque Sky Cover (column 23) is below 0. (found {N})")

    sky_e = (0.787 + 0.764 * math.log((Tdewpoint + KELVIN_OFFSET) / KELVIN_OFFSET)) * (
            1 + 0.0224 * N - 0.0035 * N ** 2 + 0.00028 * N ** 3)
    hor_IR = sky_e * BOLTZMANN * (Tdrybulb + KELVIN_OFFSET) ** 4

    return hor_IR


def calc_skytemp(hor_IR_Whm2, Tdrybulb, Tdewpoint, N):
    """
    Documentation e.g. here:
    https://www.energyplus.net/sites/default/files/docs/site_v8.3.0/EngineeringReference/05-Climate/index.html
    https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v24.1.0/EngineeringReference.pdf (Section 5.1.3)
    or:
    https://bigladdersoftware.com/epx/docs/8-6/engineering-reference/climate-calculations.html

    :param hor_IR_Whm2: horizontal infrared radiation intensity [Whm2], minimum is 0
    :param Tdrybulb: Dry bulb temperature [C]
    :param Tdewpoint: Wet bulb temperature [C]
    :param N: opaque skycover in [tenths], minimum is 0, maximum is 10 see: http://glossary.ametsoc.org/wiki/Sky_cover
    :return: sky temperature [C]
    """

    hor_IR = hor_IR_Whm2
    if hor_IR == HOR_IR_SKY_NO_VALUE:
        # Calculate value based on equation if missing
        hor_IR = calc_horirsky(Tdrybulb, Tdewpoint, N)
    elif hor_IR < 0:
        raise ValueError(f"Horizontal infrared radiation intensity (column 12) is below 0. (found {hor_IR})")

    sky_T = ((hor_IR / BOLTZMANN) ** 0.25) - KELVIN_OFFSET

    return sky_T  # sky temperature in C


def calc_wetbulb(Tdrybulb, RH):
    Tw = Tdrybulb * math.atan(0.151977 * ((RH + 8.313659) ** (0.5))) + math.atan(Tdrybulb + RH) - math.atan(
        RH - 1.676331) + (0.00391838 * (RH ** (3 / 2))) * math.atan(0.023101 * RH) - 4.686035

    return Tw  # wetbulb temperature in C


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    # for the interface, the user should pick a file out of those in ...DB/Weather/...
    epw_data = epw_reader(weather_path=(locator.get_weather_file()))
    print(epw_data)


if __name__ == '__main__':
    import cea.config

    main(cea.config.Configuration())
