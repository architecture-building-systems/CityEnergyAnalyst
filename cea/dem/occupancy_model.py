"""
===========================
Query schedules according to database
===========================
J. Fonseca  script development          26.08.15
"""
from __future__ import division
import pandas as pd
import cea.inputlocator
from geopandas import GeoDataFrame as gpdf
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

def calc_occ(list_uses, schedules, building_uses, Occ_m2p, Af):
    schedule = calc_occ_schedule(list_uses, schedules, building_uses)
    people = schedule * (Occ_m2p) ** -1 * Af  # in people
    return people

def calc_occ_schedule(list_uses, schedules, building_uses):
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
read schedules El, Qww and occupancy
=========================================
"""

def schedule_maker(date, locator, list_uses):
    def get_yearly_vectors(date, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule):
        occ = []
        el = []
        dhw = []
        pro = []
        for hour in range(8760):
            month_year = month_schedule[date[hour].month - 1]
            hour_day = date[hour].hour
            dayofweek = date[hour].dayofweek
            if dayofweek is 0 or 1 or 2 or 3 or 4:  # weekday
                occ.append(occ_schedules[0][hour_day] * month_year)
                el.append(el_schedules[0][hour_day] * month_year)
                dhw.append(dhw_schedules[0][hour_day] * month_year)
                pro.append(pro_schedules[0][hour_day] * month_year)
            elif dayofweek is 5:  # saturday
                occ.append(occ_schedules[1][hour_day] * month_year)
                el.append(el_schedules[1][hour_day] * month_year)
                dhw.append(dhw_schedules[1][hour_day] * month_year)
                pro.append(pro_schedules[1][hour_day] * month_year)
            else:  # sunday
                occ.append(occ_schedules[2][hour_day] * month_year)
                el.append(el_schedules[2][hour_day] * month_year)
                dhw.append(dhw_schedules[2][hour_day] * month_year)
                pro.append(pro_schedules[2][hour_day] * month_year)

        return occ, el, dhw, pro


    schedules = []
    for use in list_uses:
        # Read from archetypes_schedules
        x = pd.read_excel(locator.get_archetypes_schedules(), use).T

        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule = read_schedules(use, x)

        schedule = get_yearly_vectors(date, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule)
        schedules.append(schedule)

    return schedules


def read_schedules(use, x):

    occ = [x['Weekday_1'].values,x['Saturday_1'].values,x['Sunday_1'].values]
    el = [x['Weekday_2'].values, x['Saturday_2'].values, x['Sunday_2'].values]
    dhw = [x['Weekday_3'].values, x['Saturday_3'].values, x['Sunday_3'].values]
    month = x['month'].values

    if use is "INDUSTRIAL":
        pro = [x['Weekday_4'].values, x['Saturday_4'].values, x['Sunday_4'].values]
    else:
        pro = [[0]*24, [0]*24,[0]*24]

    return occ, el, dhw, pro, month

