"""
===========================
Query schedules according to database
===========================
J. Fonseca  script development          26.08.2015
D. Thomas   documentation               10.08.2016
"""

from __future__ import division
import pandas as pd
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

"""
=========================================
Occupancy
=========================================
"""


def calc_occ(list_uses, schedules, bpr):
    """
    Calculate the occupancy in number of people for the whole building per timestep.

    PARAMETERS
    ----------

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: list[ndarray[float]]

    :param bpr: The properties of the building to calculate
    :type bpr: cea.demand.thermal_loads.BuildingPropertiesRow

    RETURNS
    -------

    :returns: Occupancy as number of persons per timestep for the whole building
    :rtype: ndarray
    """
    schedule = calc_occ_schedule(list_uses, schedules, bpr.occupancy)
    people = schedule * bpr.rc_model['Af'] / bpr.architecture['Occ_m2p']  # in people
    return people


def calc_occ_schedule(list_uses, schedules, building_uses):
    """
    Given schedule data for archetypical building uses, `calc_occ_schedule` calculates the schedule for a building
    with possibly a mixed schedule as defined in `building_uses` using a weighted average approach.

    PARAMETERS
    ----------

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: list[ndarray[float]]

    :param building_uses: for each use in `list_uses`, the percentage of that use for this building.
        Sum of values is 1.0
    :type building_uses: dict[str, float]

    RETURNS
    -------

    :returns:
    :rtype: ndarray
    """
    # weighted average of schedules
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    occ = np.zeros(8760)
    num_profiles = len(list_uses)
    for num in range(num_profiles):
        current_share_of_use = building_uses[list_uses[num]]
        occ = np.vectorize(calc_average)(occ, schedules[num][0], current_share_of_use)

    return occ


"""
=========================================
read schedules from excel file
=========================================
"""


def schedule_maker(dates, locator, list_uses):
    def get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule):
        occ = []
        el = []
        dhw = []
        pro = []

        if dhw_schedules[0].sum() != 0:
            dhw_weekday_sum = dhw_schedules[0].sum() ** -1
        else: dhw_weekday_sum = 0

        if dhw_schedules[1].sum() != 0:
            dhw_sat_sum = dhw_schedules[1].sum() ** -1
        else: dhw_sat_sum = 0

        if dhw_schedules[2].sum() != 0:
            dhw_sun_sum = dhw_schedules[2].sum() ** -1
        else: dhw_sun_sum = 0

        for date in dates:
            month_year = month_schedule[date.month - 1]
            hour_day = date.hour
            dayofweek = date.dayofweek
            if 0 <= dayofweek < 5:  # weekday
                occ.append(occ_schedules[0][hour_day] * month_year)
                el.append(el_schedules[0][hour_day] * month_year)
                dhw.append(dhw_schedules[0][hour_day] * month_year * dhw_weekday_sum) # normalized dhw demand flow rates
                pro.append(pro_schedules[0][hour_day] * month_year)
            elif dayofweek is 5:  # saturday
                occ.append(occ_schedules[1][hour_day] * month_year)
                el.append(el_schedules[1][hour_day] * month_year)
                dhw.append(dhw_schedules[1][hour_day] * month_year * dhw_sat_sum) # normalized dhw demand flow rates
                pro.append(pro_schedules[1][hour_day] * month_year)
            else:  # sunday
                occ.append(occ_schedules[2][hour_day] * month_year)
                el.append(el_schedules[2][hour_day] * month_year)
                dhw.append(dhw_schedules[2][hour_day] * month_year * dhw_sun_sum) # normalized dhw demand flow rates
                pro.append(pro_schedules[2][hour_day] * month_year)

        return occ, el, dhw, pro

    schedules = []
    for use in list_uses:
        # Read from archetypes_schedules
        x = pd.read_excel(locator.get_archetypes_schedules(), use).T

        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule = read_schedules(use, x)

        schedule = get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule)
        schedules.append(schedule)

    return schedules


def read_schedules(use, x):
    occ = [x['Weekday_1'].values, x['Saturday_1'].values, x['Sunday_1'].values]
    el = [x['Weekday_2'].values, x['Saturday_2'].values, x['Sunday_2'].values]
    dhw = [x['Weekday_3'].values, x['Saturday_3'].values, x['Sunday_3'].values]
    month = x['month'].values

    if use is "INDUSTRIAL":
        pro = [x['Weekday_4'].values, x['Saturday_4'].values, x['Sunday_4'].values]
    else:
        pro = [np.zeros(24), np.zeros(24), np.zeros(24)]

    return occ, el, dhw, pro, month
