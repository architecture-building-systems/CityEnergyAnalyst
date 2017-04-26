"""
Query schedules according to database
"""

# HISTORY
# J. Fonseca  script development          26.08.2015
# D. Thomas   documentation               10.08.2016

from __future__ import division
import pandas as pd
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_occ_schedule(list_uses, schedules, occ_density, building_uses, Af):
    """
    Given schedule data for archetypical building uses, `calc_occ_schedule` calculates the schedule for a building
    with possibly a mixed schedule as defined in `building_uses` using a weighted average approach.

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: list[ndarray[float]]

    :param occ_density: the list of occupancy densities per every schedule
    :type occ_density:: list[float]

    :param building_uses: for each use in `list_uses`, the percentage of that use for this building.
        Sum of values is 1.0
    :type building_uses: dict[str, float]

    :param Af: total conditioned floor area

    :type Af: float

    :returns:
    :rtype: ndarray
    """
    # weighted average of schedules
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    occ = np.zeros(8760)

    num_profiles = len(list_uses)
    for num in range(num_profiles):
        if occ_density[num] != 0: # do not consider when the occupancy is 0
            current_share_of_use = building_uses[list_uses[num]]
            share_time_occupancy_density = (1/occ_density[num])*current_share_of_use
            occ = np.vectorize(calc_average)(occ, schedules[num][0], share_time_occupancy_density)
    result = occ*Af

    return result


# read schedules from excel file

def schedule_maker(dates, locator, list_uses):
    def get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule):
        occ = []
        el = []
        dhw = []
        pro = []

        if dhw_schedules[0].sum() != 0:
            dhw_weekday_max = dhw_schedules[0].sum() ** -1
        else: dhw_weekday_max = 0

        if dhw_schedules[1].sum() != 0:
            dhw_sat_max = dhw_schedules[1].sum() ** -1
        else: dhw_sat_max = 0

        if dhw_schedules[2].sum() != 0:
            dhw_sun_max = dhw_schedules[2].sum() ** -1
        else: dhw_sun_max = 0

        for date in dates:
            month_year = month_schedule[date.month - 1]
            hour_day = date.hour
            dayofweek = date.dayofweek
            if 0 <= dayofweek < 5:  # weekday
                occ.append(occ_schedules[0][hour_day] * month_year)
                el.append(el_schedules[0][hour_day] * month_year)
                dhw.append(dhw_schedules[0][hour_day] * month_year * dhw_weekday_max) # normalized dhw demand flow rates
                pro.append(pro_schedules[0][hour_day] * month_year)
            elif dayofweek is 5:  # saturday
                occ.append(occ_schedules[1][hour_day] * month_year)
                el.append(el_schedules[1][hour_day] * month_year)
                dhw.append(dhw_schedules[1][hour_day] * month_year * dhw_sat_max) # normalized dhw demand flow rates
                pro.append(pro_schedules[1][hour_day] * month_year)
            else:  # sunday
                occ.append(occ_schedules[2][hour_day] * month_year)
                el.append(el_schedules[2][hour_day] * month_year)
                dhw.append(dhw_schedules[2][hour_day] * month_year * dhw_sun_max) # normalized dhw demand flow rates
                pro.append(pro_schedules[2][hour_day] * month_year)

        return occ, el, dhw, pro

    schedules = []
    occ_densities = []
    for use in list_uses:
        # Read from archetypes_schedules
        x = pd.read_excel(locator.get_archetypes_schedules(), use).T

        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule, occ_density = read_schedules(use, x)

        # read occupancy density per schedule
        occ_densities.append(occ_density)

        # get yearly schedules in a list
        schedule = get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule)
        schedules.append(schedule)

    return schedules, occ_densities


def read_schedules(use, x):

    # read schedules from excel file
    occ = [x['Weekday_1'].values[:24], x['Saturday_1'].values[:24], x['Sunday_1'].values[:24]]
    el = [x['Weekday_2'].values[:24], x['Saturday_2'].values[:24], x['Sunday_2'].values[:24]]
    dhw = [x['Weekday_3'].values[:24], x['Saturday_3'].values[:24], x['Sunday_3'].values[:24]]
    month = x['month'].values[:12]

    if use is "INDUSTRIAL":
        pro = [x['Weekday_4'].values[:24], x['Saturday_4'].values[:24], x['Sunday_4'].values[:24]]
    else:
        pro = [np.zeros(24), np.zeros(24), np.zeros(24)]

    # read occupancy density
    occ_density = x['density'].values[:1][0]

    return occ, el, dhw, pro, month, occ_density
