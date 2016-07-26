"""
==================================================
solar equations
==================================================

"""


from __future__ import division
import numpy as np
import pandas as pd
import ephem
import datetime
import math



__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""
============================
import ephem library
============================

"""

def _ephem_setup(latitude, longitude, altitude, pressure, temperature):
    # observer
    obs = ephem.Observer()
    obs.lat = str(latitude)
    obs.lon = str(longitude)
    obs.elevation = altitude
    obs.pressure = pressure / 100.
    obs.temp = temperature

    #sun
    sun = ephem.Sun()
    return obs, sun


def pyephem(time, latitude, longitude, altitude=0, pressure=101325,
            temperature=12):

    # Written by Will Holmgren (@wholmgren), University of Arizona, 2014

    try:
        time_utc = time.tz_convert('UTC')
    except TypeError:
        time_utc = time

    sun_coords = pd.DataFrame(index=time)

    obs, sun = _ephem_setup(latitude, longitude, altitude,
                            pressure, temperature)

    # make and fill lists of the sun's altitude and azimuth
    # this is the pressure and temperature corrected apparent alt/az.
    alts = []
    azis = []
    for thetime in time_utc:
        obs.date = ephem.Date(thetime)
        sun.compute(obs)
        alts.append(sun.alt)
        azis.append(sun.az)

    sun_coords['apparent_elevation'] = alts
    sun_coords['apparent_azimuth'] = azis

    # redo it for p=0 to get no atmosphere alt/az
    obs.pressure = 0
    alts = []
    azis = []
    for thetime in time_utc:
        obs.date = ephem.Date(thetime)
        sun.compute(obs)
        alts.append(sun.alt)
        azis.append(sun.az)

    sun_coords['elevation'] = alts
    sun_coords['azimuth'] = azis

    # convert to degrees. add zenith
    sun_coords = np.rad2deg(sun_coords)
    sun_coords['apparent_zenith'] = 90 - sun_coords['apparent_elevation']
    sun_coords['zenith'] = 90 - sun_coords['elevation']

    return sun_coords

"""
============================
solar properties
============================

"""

def calc_sun_properties(latitude, longitude, weather_data, gv):

    date = pd.date_range(gv.date_start, periods=8760, freq='H')

    # solar elevation, azuimuth and values for the 9-3pm period of no shading on the solar solstice
    sun_coords = pyephem(date, latitude, longitude)
    sun_coords['declination'] = np.vectorize(declination_degree)(date, 365)
    sun_coords['hour_angle'] = np.vectorize(get_hour_angle)(date, longitude)
    worst_sh = sun_coords['elevation'].loc[gv.worst_hour, 'Sh']
    worst_Az = sun_coords['azimuth'].loc[gv.worst_hour, 'Az']

    # mean trnasmissivity
    weather_data['diff'] = weather_data.difhorrad_Whm2 / weather_data.glohorrad_Whm2
    T_G_hour = weather_data[np.isfinite(weather_data['diff'])]
    T_G_day = np.round(T_G_hour.groupby(['dayofyear']).mean(), 2)
    T_G_day['diff'] = T_G_day['diff'].replace(1, 0.90)
    T_G_day['trr'] = (1 - T_G_day['diff'])
    transmittivity = T_G_day['ttr'].mean()

    return sun_coords['declination'], sun_coords['zenith'], sun_coords['azimuth'], sun_coords['hour_angle'], transmittivity, worst_sh, worst_Az


def calc_sunrise(sunrise, Yearsimul, longitude, latitude):
    o, s = _ephem_setup(latitude, longitude, altitude=0, pressure=101325, temperature=12)
    for day in range(1, 366):  # Calculated according to NOAA website
        o.date = datetime.datetime(Yearsimul, 1, 1) + datetime.timedelta(day - 1)
        next_event = o.next_rising(s)
        sunrise[day - 1] = next_event.datetime().hour
    return sunrise


def declination_degree(when, TY):
    """The declination of the sun is the angle between Earth's equatorial plane and a line
    between the Earth and the sun. It varies between 23.45 degrees and -23.45 degrees,
    hitting zero on the equinoxes and peaking on the solstices.
    Parameters
    ----------
    when : datetime.datetime
        date/time for which to do the calculation
    TY : float
        Total number of days in a year. eg. 365 days per year,(no leap days)
    Returns
    -------
    DEC : float
        The declination of the Sun
    References
    ----------
    .. [1] http://pysolar.org/
    """
    return 23.45 * math.sin((2 * math.pi / (TY)) * ((when.utctimetuple().tm_yday) - 81))


def get_hour_angle(when, longitude_deg):
    solar_time = get_solar_time(longitude_deg, when)
    return 15 * (12 - solar_time)


def get_solar_time(longitude_deg, when):
    "returns solar time in hours for the specified longitude and time," \
    " accurate only to the nearest minute."
    when = when.utctimetuple()
    return \
        (
            (when.tm_hour * 60 + when.tm_min + 4 * longitude_deg + equation_of_time(when.tm_yday))
        /
            60
        )