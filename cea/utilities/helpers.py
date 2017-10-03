# -*- coding: utf-8 -*-
"""
Some helper functions that could be useful
"""

from __future__ import division
import math
import numpy as np


def hoy_2_doy(hoy):
    """
    Hour of year to day of year
    hoy: hour of year
    doy: day of year
    """

    if check_hoy(hoy):
        return int(math.floor(hoy/24)) + 1
    else:
        return None


def doy_2_hoy(doy):
    """
    Day of year to hour of year

    doy: day of year
    hoy: hour of year
    """

    if check_doy(doy):
        return doy*24
    else:
        return None


def hoy_2_woy(hoy):
    """
    Hour of year to week of year
    hoy: hour of year
    woy: weak of year
    """

    if check_hoy(hoy):
        return int(math.floor(hoy_2_doy(hoy)/7)) + 1
    else:
        return None


def hoy_2_moy(hoy):
    """
    hour of year to month of year
    hoy: hour of year
    moy: month of year
    """

    if check_hoy(hoy):

        # months_of_year = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        days_in_month = np.array([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

        return np.where(np.cumsum(days_in_month) >= hoy_2_doy(hoy))[0][0]
    else:
        return None


def hoy_2_hod(hoy):
    """
    hour of year to hour of day
    hoy: hour of year
    hod: hour of day
    """

    if check_hoy(hoy):
        return hoy % 24
    else:
        return None


def hoy_2_dom(hoy):
    """
    hour of year to day of month
    hoy: hour of year
    dom: day of month
    """

    if check_hoy(hoy):

        days_in_month = np.array([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        doy = hoy_2_doy(hoy)
        moy = hoy_2_moy(hoy)
        return doy - np.cumsum(days_in_month)[moy] + days_in_month[moy]
    else:
        return None


def hoy_2_seasonhour(hoy, gv):
    """
    hour of year to hour relative to start of heating season
    hoy: hour of year
    seasonhour: hour relative to start of heating season
    """

    hoy_heat_stop, hoy_heat_start = gv.seasonhours

    if check_hoy(hoy):
        if hoy > hoy_heat_start - 1:
            seasonhour = hoy - hoy_heat_start
        else:
            seasonhour = hoy + 8760 - hoy_heat_start

        return seasonhour

    else:
        return None


def seasonhour_2_hoy(seasonhour, gv):
    """
    hour relative to start of heating season to hour of year

    :param seasonhour: hour relative to start of heating season
    :type seasonhour: int
    :returns hoy: hour of year
    :rtype hoy: int
    """

    hoy_heat_stop, hoy_heat_start = gv.seasonhours

    # convert negative seasonhours to positive (for heating up phase consideration)
    if seasonhour < 0:
        seasonhour = 8760 - abs(seasonhour)

    if check_hoy(seasonhour):
        if seasonhour < 8760 - hoy_heat_start:
            hoy = hoy_heat_start + seasonhour
        else:
            hoy = hoy_heat_start - 8760 + seasonhour
        return hoy

    else:
        return None


def check_hoy(hoy):
    """
    check for hour of year within bounds
    hoy: hour of year
    bool
    """

    if 0 <= hoy <= 8759:
        return True
    else:
        print('Error: hour of year out of bounds')
        print(hoy)
        return False


def check_doy(doy):
    """
    check for day of year within bounds
    doy: day of year
    bool
    """

    if 0 <= doy <= 359:
        return True
    else:
        print('Error: day of year out of bounds')
        print(doy)
        return False


def is_nighttime_hoy(hoy):
    """
    Check if a certain hour of year is during night or not
    hoy: hour of year
    bool
    """
    if check_hoy(hoy):

        location = 'CH'  # TODO get location

        start_night = 21  # 21:00 # TODO: make dynamic (e.g. as function of location/country)
        stop_night = 7  # 07:00 # TODO: make dynamic (e.g. as function of location/country)

        if start_night <= hoy_2_hod(hoy) or stop_night >= hoy_2_hod(hoy):
            return True
        else:
            return False
    else:
        return


def is_daytime_hoy(hoy):
    """
    Check if a certain hour of the year is during the daytime or not
    hoy : hour of year
    bool
    """
    if check_hoy(hoy):

        if not is_nighttime_hoy(hoy):
            return True
        else:
            return False
    else:
        return


def is_heatingseason_hoy(hoy):
    """
    checks if a certain hour of the year is part of the heating season or not
    hoy : hour of year
    bool
    """

    if check_hoy(hoy):

        #TODO: get location from (?)
        location = 'CH'

        #TODO: get start heating season f(location)
        # seasonhours = [3216, 6192]
        seasonhours = [0, 8670]  # FIXME Singapore workaround
        if hoy > seasonhours[1] or hoy < seasonhours[0]:
            return True
        else:
            return False

    else:
        return


def is_coolingseason_hoy(hoy):
    """
    checks if a certain hour of the year is part of the cooling season or not
    hoy : hour of year
    bool
    """

    if check_hoy(hoy):
        if not is_heatingseason_hoy(hoy):
            return True
        else:
            return False

    else:
        return


def sind(angle):
    """
    Calculates sine function with input in degree.

    :param angle: angle in degree
    :type angle: float
    :return: sine of the angle
    :rtype: float

    Author: Shanshan Hsieh, 27/04/2017
    """
    return np.sin(np.radians(angle))


def cosd(angle):
    """
    Calculates cosine function with input in degree.

    :param angle: angle in degree
    :type angle: float
    :return: cosine of the angle
    :rtype: float

    Author: Shanshan Hsieh, 27/04/2017
    """
    return np.cos(np.radians(angle))


def tand(angle):
    """
    Calculates tangent function with input in degree.

    :param angle: angle in degree
    :type angle: float
    :return: tan of the angle
    :rtype: float

    Author: Shanshan Hsieh, 27/04/2017
    """
    return np.tan(np.radians(angle))





def test_helpers():
    """
    test helpers
    """
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    # translate hours of year to hours relative to start of heating season
    a = np.vectorize(hoy_2_seasonhour)(range(8760), gv)
    # translate back
    b = np.vectorize(seasonhour_2_hoy)(a, gv)
    # compare
    print(np.array_equal(range(8760), b))


if __name__ == '__main__':
    test_helpers()
