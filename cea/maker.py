"""
===========================
Query schedules according to database
===========================
J. Fonseca  script development          26.08.15
"""

import pandas as pd
import globalvar
import inputlocator
from geopandas import GeoDataFrame as gpdf

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def schedule_maker(date, locator, list_uses):
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

def get_yearly_vectors(date, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule):
    occ = []
    el = []
    dhw = []
    pro = []
    for hour in range(8760):
        month_year = month_schedule[date[hour].month-1]
        hour_day = date[hour].hour
        dayofweek = date[hour].dayofweek
        if dayofweek is 0 or 1 or 2 or 3 or 4: #weekday
            occ.append(occ_schedules[0][hour_day] * month_year)
            el.append(el_schedules[0][hour_day] * month_year)
            dhw.append(dhw_schedules[0][hour_day] * month_year)
            pro.append(pro_schedules[0][hour_day] * month_year)
        elif dayofweek is 5: #saturday
            occ.append(occ_schedules[1][hour_day] * month_year)
            el.append(el_schedules[1][hour_day] * month_year)
            dhw.append(dhw_schedules[1][hour_day] * month_year)
            pro.append(pro_schedules[1][hour_day] * month_year)
        else: # sunday
            occ.append(occ_schedules[2][hour_day] * month_year)
            el.append(el_schedules[2][hour_day] * month_year)
            dhw.append(dhw_schedules[2][hour_day] * month_year)
            pro.append(pro_schedules[2][hour_day] * month_year)

    return occ, el, dhw, pro

def test_schedule_maker():
    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    prop_occupancy_df = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1).set_index('Name')[:270]
    prop_occupancy = prop_occupancy_df.loc[:, (prop_occupancy_df != 0).any(axis=0)]
    gv = globalvar.GlobalVariables()
    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    list_uses = list(prop_occupancy.drop('PFloor', axis=1).columns)
    schedule_maker(date=date, locator=locator, list_uses=list_uses)

if __name__ == '__main__':
    test_schedule_maker()
