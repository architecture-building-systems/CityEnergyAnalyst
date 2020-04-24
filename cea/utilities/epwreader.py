"""
Energyplus file reader
"""
from __future__ import division
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


def epw_to_dataframe(weather_path):
    epw_labels = ['year', 'month', 'day', 'hour', 'minute', 'datasource', 'drybulb_C', 'dewpoint_C', 'relhum_percent',
                  'atmos_Pa', 'exthorrad_Whm2', 'extdirrad_Whm2', 'horirsky_Whm2', 'glohorrad_Whm2',
                  'dirnorrad_Whm2', 'difhorrad_Whm2', 'glohorillum_lux', 'dirnorillum_lux', 'difhorillum_lux',
                  'zenlum_lux', 'winddir_deg', 'windspd_ms', 'totskycvr_tenths', 'opaqskycvr_tenths', 'visibility_km',
                  'ceiling_hgt_m', 'presweathobs', 'presweathcodes', 'precip_wtr_mm', 'aerosol_opt_thousandths',
                  'snowdepth_cm', 'days_last_snow', 'Albedo', 'liq_precip_depth_mm', 'liq_precip_rate_Hour']

    df = pd.read_csv(weather_path, skiprows=8, header=None, names=epw_labels).drop('datasource', axis=1)
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
            print('Dates missing:', difference)
        raise Exception('Incorrect number of rows. Expected {}, got {}'.format(HOURS_IN_YEAR, len(epw_data)))

    epw_data['ratio_diffhout'] = epw_data['difhorrad_Whm2'] / epw_data['glohorrad_Whm2']
    epw_data['ratio_diffhout'] = epw_data['ratio_diffhout'].replace(np.inf, np.nan)
    epw_data['wetbulb_C'] = np.vectorize(calc_wetbulb)(epw_data['drybulb_C'], epw_data['relhum_percent'])
    epw_data['skytemp_C'] = np.vectorize(calc_skytemp)(epw_data['drybulb_C'], epw_data['dewpoint_C'],
                                                       epw_data['opaqskycvr_tenths'])

    return epw_data


def calc_skytemp(Tdrybulb, Tdewpoint, N):
    """
    Documentation e.g. here:
    https://www.energyplus.net/sites/default/files/docs/site_v8.3.0/EngineeringReference/05-Climate/index.html
    or:
    https://bigladdersoftware.com/epx/docs/8-6/engineering-reference/climate-calculations.html

    :param Tdrybulb: Dry bulb temperature [C]
    :param Tdewpoint: Wet bulb temperature [C]
    :param N: opaque skycover in [tenths], minimum is 0, maximum is 10 see: http://glossary.ametsoc.org/wiki/Sky_cover
    :return: sky temperature [C]
    """

    sky_e = (0.787 + 0.764 * math.log((Tdewpoint + KELVIN_OFFSET) / KELVIN_OFFSET)) * (
            1 + 0.0224 * N - 0.0035 * N ** 2 + 0.00028 * N ** 3)
    hor_IR = sky_e * BOLTZMANN * (Tdrybulb + KELVIN_OFFSET) ** 4
    sky_T = ((hor_IR / BOLTZMANN) ** 0.25) - KELVIN_OFFSET

    return sky_T  # sky temperature in C


def calc_wetbulb(Tdrybulb, RH):
    Tw = Tdrybulb * math.atan(0.151977 * ((RH + 8.313659) ** (0.5))) + math.atan(Tdrybulb + RH) - math.atan(
        RH - 1.676331) + (0.00391838 * (RH ** (3 / 2))) * math.atan(0.023101 * RH) - 4.686035

    return Tw  # wetbulb temperature in C


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    epw_data = epw_reader(weather_path=(locator.get_weather_file()))
    print(epw_data)


if __name__ == '__main__':
    import cea.config

    main(cea.config.Configuration())
