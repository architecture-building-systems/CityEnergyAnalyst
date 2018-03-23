# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
import datetime

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def has_heating_system(bpr):
    """
    determines whether a building has a heating system installed or not

    :param bpr: building properties row object

    :returns:
    :rtype: bool
    """

    if bpr.hvac['type_hs'] in {'T1', 'T2', 'T3', 'T4'}:
        return True
    elif bpr.hvac['type_hs'] in {'T0'}:
        return False
    else:
        raise ValueError('Invalid value for type_hs: %s' % bpr.hvac['type_hs'])


def has_cooling_system(bpr):
    """
    determines whether a building has a cooling system installed or not

    :param bpr: building properties row object
    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T1', 'T2', 'T3', 'T4'}:
        return True
    elif bpr.hvac['type_cs'] in {'T0'}:
        return False
    else:
        raise ValueError('Invalid value for type_cs: %s' % bpr.hvac['type_cs'])


def has_radiator_heating_system(bpr):
    """
    Checks if building has radiator heating system

    :param bpr: building properties row object
    :return:
    :rtype: bool
    """

    if bpr.hvac['type_hs'] in {'T1', 'T2'}:
        # radiator or floor heating
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T3', 'T4'}:
        # no system or central ac
        return False
    else:
        raise ValueError('Invalid value for type_hs: %s' % bpr.hvac['type_hs'])


def has_floor_heating_system(bpr):
    """
    Checks if building has floor heating system

    :param bpr: building properties row object
    :return:
    :rtype: bool
    """
    if bpr.hvac['type_hs'] in {'T4'}:
        # floor heating
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T1', 'T2', 'T3'}:
        # no system, radiators or central ac
        return False
    else:
        raise ValueError('Invalid value for type_hs: %s' % bpr.hvac['type_hs'])


def has_central_ac_heating_system(bpr):
    """
    Checks if building has central AC heating system

    :param bpr: building properties row object

    :rtype: bool
    """

    if bpr.hvac['type_hs'] in {'T3'}:  # central ac
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T1', 'T2', 'T4'}:
        return False
    else:
        raise ValueError('Invalid value for type_hs: %s' % bpr.hvac['type_hs'])


def has_local_ac_cooling_system(bpr):
    """
    Checks if building has mini-split unit AC cooling system

    :param bpr: building properties row object
    :return:
    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T2'}:  # mini-split ac
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T1', 'T3', 'T4'}:
        return False
    else:
        raise ValueError('Invalid value for type_cs: %s' % bpr.hvac['type_cs'])


def has_central_ac_cooling_system(bpr):
    """
    Checks if building has central AC cooling system

    :param bpr: building properties row object
    :return:
    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T3'}:  # central ac
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T1', 'T2', 'T4'}:
        return False
    else:
        raise ValueError('Invalid value for type_cs: %s' % bpr.hvac['type_cs'])


def has_3for2_cooling_system(bpr):
    """
    Checks if building has 3for2 cooling system

    :param bpr: building properties row object
    :return:
    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T4'}:  # 3for2
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T1', 'T2', 'T3'}:
        return False
    else:
        raise ValueError('Invalid value for type_cs: %s' % bpr.hvac['type_cs'])


def has_ceiling_cooling_system(bpr):
    """
    Checks if building has ceiling cooling system

    :param bpr: building properties row object
    :return:
    :rtype: bool
    """

    if bpr.hvac['type_cs'] in {'T1'}:  # ceiling cooling
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T2', 'T3', 'T4'}:
        return False
    else:
        raise ValueError('Invalid value for type_cs: %s' % bpr.hvac['type_cs'])


def cooling_system_is_active(tsd, t):
    """
    Checks whether the cooling system is active according to rules for a specific hour of the year
    i.e., is there a set point temperature
    i.e., is the outdoor air temperature higher than the set point temperature

    :param tsd:
    :param t:
    :return:
    :rtype: bool
    """

    if not np.isnan(tsd['ta_cs_set'][t]) \
            and tsd['T_ext'][t] >= tsd['ta_cs_set'][t]:
        # system has set point and other rules

        return True
    else:
        return False


def heating_system_is_active(tsd, t):
    """
    Checks whether the heating system is active according to rules for a specific hour of the year
    i.e., is there a set point temperature

    :param tsd:
    :param t:
    :return:
    :rtype: bool
    """

    if not np.isnan(tsd['ta_hs_set'][t]):
        # system has set point and other rules
        return True
    else:
        return False


def convert_date_to_hour(date):
    """
    converts date in 'MM-DD' format into hour of the year (first hour of the day)
    i.e. '01-01' results in 0

    :param date: date in 'MM-DD' format (from .xlsx database input)
    :type date: str
    :return: hour of the year (first hour of the day)
    :rtype: int
    """
    SECONDS_PER_HOUR = 60 * 60

    month, day = map(int, date.split('-'))
    delta = datetime.datetime(2017, month, day) - datetime.datetime(2017, 1, 1)
    return int(delta.total_seconds() / SECONDS_PER_HOUR)


def is_heating_season(t, bpr):
    """
    checks if time step is part of the heating season for the building

    :param t: hour of the year, simulation time step [0...8760]
    :type t: int
    :param bpr: BuildingPropertiesRow
    :param bpr: cea.demand.building_properties.BuildingPropertiesRow
    :return: True or False
    :rtype: bool
    """

    if bpr.hvac['has-heating-season']:

        heating_start = convert_date_to_hour(bpr.hvac['heating-season-start'])
        heating_end = convert_date_to_hour(bpr.hvac['heating-season-end']) + 23  # end at the last hour of the day

        # check if heating season is at the end of the year (north hemisphere) or in the middle of the year (south)
        if heating_start < heating_end and \
                heating_start <= t <= heating_end:

            # heating season time on south hemisphere
            return True

        elif heating_start > heating_end and \
                (heating_start <= t <= 8760 or 0 <= t <= heating_end):
            # heating season over the year end (north hemisphere)
            return True

        else:
            # not time of heating season
            return False

    elif not bpr.hvac['has-heating-season']:
        # no heating season
        return False


def is_cooling_season(t, bpr):
    """
    checks if time step is part of the cooling season for the building

    :param t: hour of the year, simulation time step [0...8760]
    :type t: int
    :param bpr: BuildingPropertiesRow
    :param bpr: cea.demand.building_properties.BuildingPropertiesRow
    :return: True or False
    :rtype: bool
        """

    if bpr.hvac['has-cooling-season']:

        cooling_start = convert_date_to_hour(bpr.hvac['cooling-season-start'])
        cooling_end = convert_date_to_hour(bpr.hvac['cooling-season-end']) + 23  # end at the last hour of the day

        # check if cooling season is at the end of the year (south hemisphere) or in the middle of the year (norht)
        if cooling_start < cooling_end and \
                cooling_start <= t <= cooling_end:

            # cooling season time on north hemisphere
            return True

        elif cooling_start > cooling_end and \
                (cooling_start <= t <= 8760 or 0 <= t <= cooling_end):
            # cooling season around the year end (south hemisphere)
            return True

        else:
            # not time of cooling season
            return False

    elif not bpr.hvac['has-cooling-season']:
        # no cooling season
        return False

# temperature controllers


def calc_simple_temp_control(tsd, bpr, weekday):
    """

    :param tsd:
    :param bpr:
    :param weekday:
    :return:
    """

    tsd['ta_hs_set'] = np.vectorize(get_heating_system_set_point)(tsd['people'], range(8760), bpr, weekday)
    tsd['ta_cs_set'] = np.vectorize(get_cooling_system_set_point)(tsd['people'], range(8760), bpr, weekday)

    return tsd


def get_heating_system_set_point(people, t, bpr, weekday):
    """

    :param people:
    :param t:
    :param bpr:
    :param weekday:
    :return:
    """

    if is_heating_season(t, bpr):

        if people == 0:
            if 5 <= weekday <= 6:  # system is off on the weekend
                return np.nan  # huge so the system will be off
            else:
                return bpr.comfort['Ths_setb_C']
        else:
            return bpr.comfort['Ths_set_C']
    else:
        return np.nan  # huge so the system will be off


def get_cooling_system_set_point(people, t, bpr, weekday):
    """

    :param people:
    :param t:
    :param bpr:
    :param weekday:
    :return:
    """

    if is_cooling_season(t, bpr):
        if people == 0:
            if 5 <= weekday <= 6:  # system is off on the weekend
                return np.nan  # huge so the system will be off
            else:
                return bpr.comfort['Tcs_setb_C']
        else:
                return bpr.comfort['Tcs_set_C']
    else:
        return np.nan  # huge so the system will be off
