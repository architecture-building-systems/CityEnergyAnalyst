# -*- coding: utf-8 -*-


from __future__ import division
from cea.demand import control_heating_cooling_systems

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


#
#  CHECK SYSTEM STATUS
#

def is_mechanical_ventilation_active(bpr, tsd, t):

    # TODO: check for ventilation schedule
    if has_mechanical_ventilation(bpr) \
            and tsd['m_ve_required'][t] > 0:

        # mechanical ventilation is active if there is a ventilation demand
        return True

    elif has_mechanical_ventilation(bpr) \
            and is_night_flushing_active(bpr, tsd, t):

        # mechanical ventilation for night flushing
        return True

    else:
        return False


def is_window_ventilation_active(bpr, tsd, t):

    if has_window_ventilation(bpr) \
            and not is_mechanical_ventilation_active(bpr, tsd, t):

        # window ventilation in case of non-active mechanical ventilation
        return True

    else:
        return False


def is_mechanical_ventilation_heat_recovery_active(bpr, tsd, t):
    """
    Control of activity of heat exchanger of mechanical ventilation system
    
    Author: Gabriel Happle
    Date: APR 2017
    
    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: dict
    :param t: time step / hour of the year
    :type t: int
    :return: Heat exchanger ON/OFF status
    :rtype: bool
    """

    if is_mechanical_ventilation_active(bpr, tsd, t)\
            and has_mechanical_ventilation_heat_recovery(bpr)\
            and control_heating_cooling_systems.is_heating_season(t, bpr):

        # heat recovery is always active if mechanical ventilation is active (no intelligent by pass)
        # this is the usual system configuration according to Clayton Miller
        return True

    elif is_mechanical_ventilation_active(bpr, tsd, t)\
            and has_mechanical_ventilation_heat_recovery(bpr)\
            and control_heating_cooling_systems.is_cooling_season(t, bpr)\
            and tsd['T_int'][t-1] < tsd['T_ext'][t]:

        return True

    elif is_mechanical_ventilation_active(bpr, tsd, t) \
            and control_heating_cooling_systems.is_cooling_season(t, bpr) \
            and tsd['T_int'][t-1] >= tsd['T_ext'][t]:

        # heat recovery is deactivated in the cooling case,
        #  if outdoor air conditions are colder than indoor (free cooling)

        return False

    else:
        return False


def is_night_flushing_active(bpr, tsd, t):

    # night flushing is available for window ventilation (manual) and mechanical ventilation (automatic)
    # night flushing is active during the night in the cooling season,
    #  IF the outdoor conditions are favourable (only temperature at the moment)
    temperature_zone_control = 26  # (°C) night flushing only if temperature is higher than 26 # TODO review and make dynamic
    delta_t = 2 # (°C) night flushing only if outdoor temperature is two degrees lower than indoor # TODO review and make dynamic

    if has_night_flushing(bpr) \
            and control_heating_cooling_systems.is_cooling_season(t, bpr) \
            and is_night_time(t) \
            and tsd['T_int'][t-1] > temperature_zone_control \
            and tsd['T_int'][t-1] > tsd['T_ext'][t] + delta_t\
            and tsd['rh_ext'][t] < bpr.comfort['rhum_max_pc']:

        return True

    else:
        return False


def is_economizer_active(bpr, tsd, t):
    """
    Control of activity of economizer of mechanical ventilation system
    Economizer of mechanical ventilation is controlled via zone set point temperatures, indoor air temperature and
    outdoor air temperature.
    Economizer is active during cooling season if the indoor air temperature exceeds the set point and the outdoor
    temperatures are lower than the set point.
    Economizer increases mechanical ventilation flow rate to the maximum.
    
    Author: Gabriel Happle
    Date: APR 2017
    
    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: dict
    :param t: time step / hour of the year
    :type t: int
    :return: Economizer ON/OFF status
    :rtype: bool
    """

    if has_mechanical_ventilation_economizer(bpr) \
            and control_heating_cooling_systems.is_cooling_season(t, bpr) \
            and tsd['T_int'][t-1] > tsd['ta_cs_set'][t] >= tsd['T_ext'][t]:

        return True

    else:
        return False




#
# CHECK SYSTEM CONFIGURATION
#

def has_mechanical_ventilation(bpr):

    if bpr.hvac['MECH_VENT']:
        return True
    elif not bpr.hvac['MECH_VENT']:
        return False
    else:
        raise ValueError(bpr.hvac['MECH_VENT'])


def has_window_ventilation(bpr):

    if bpr.hvac['WIN_VENT']:
        return True
    elif not bpr.hvac['WIN_VENT']:
        return False
    else:
        raise ValueError(bpr.hvac['WIN_VENT'])


def has_mechanical_ventilation_heat_recovery(bpr):

    if bpr.hvac['HEAT_REC']:
        return True
    elif not bpr.hvac['HEAT_REC']:
        return False
    else:
        raise ValueError(bpr.hvac['HEAT_REC'])


def has_night_flushing(bpr):

    if bpr.hvac['NIGHT_FLSH']:
        return True
    elif not bpr.hvac['NIGHT_FLSH']:
        return False
    else:
        raise ValueError(bpr.hvac['NIGHT_FLSH'])


def has_mechanical_ventilation_economizer(bpr):

    if bpr.hvac['ECONOMIZER']:
        return True
    elif not bpr.hvac['ECONOMIZER']:
        return False
    else:
        raise ValueError(bpr.hvac['ECONOMIZER'])


def is_night_time(t):
    """
    Check if a certain hour of year is during night or not

    :param t:
    :return:
    """
    return not is_day_time(t)


def is_day_time(t):
    """
    Check if a certain hour of the year is during the daytime or not

    :param t:
    :return:
    """
    start_night = 21  # 21:00 # TODO: make dynamic (e.g. as function of location/country)
    stop_night = 7  # 07:00 # TODO: make dynamic (e.g. as function of location/country)
    hour_of_day = t % 24
    return stop_night < hour_of_day < start_night
