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


def calc_schedules(list_uses, schedules, specific_values, building_uses, area, schedule_type):
    """
    Given schedule data for archetypical building uses, `calc_schedule` calculates the schedule for a building
    with possibly a mixed schedule as defined in `building_uses` using a weighted average approach. The script generates
    the given schedule_type.

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: list[ndarray[float]]

    :param specific_values: for the variable to be calculated, list of yearly values per m2 or per person (e.g. occupant
    density)
    :type specific_values: list[float]

    :param building_uses: for each use in `list_uses`, the percentage of that use for this building. Sum of values is 1.0
    :type building_uses: dict[str, float]

    :param area: total conditioned or electrified floor area (Af or Ae)
    :type area: float

    :param schedule_type: defines the type of schedule to be generated based on the schedules in the archetype data
    base. Valid inputs are 'people' (for occupancy, occupant-related internal loads and ventilation), 'electricity' (for
    lighting, appliances, refrigeration and data centers), 'water' (for total water and hot water), or 'process'.
    :param schedule_type: string

    :returns:
    :rtype: ndarray
    """

    # code to get each corresponding schedule from `schedules`
    schedule_code_dict = {'people': 0, 'electricity': 1, 'water': 2, 'process': 3}
    code = schedule_code_dict[schedule_type]

    # weighted average of schedules
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    specific_result = np.zeros(8760)

    num_profiles = len(list_uses)
    for num in range(num_profiles):
        if specific_values[num] != 0: # do not consider when the occupancy is 0
            current_share_of_use = building_uses[list_uses[num]]
            share_time_occupancy_density = (specific_values[num]) * current_share_of_use
            specific_result = np.vectorize(calc_average)(specific_result, schedules[num][code],
                                                         share_time_occupancy_density)

    result = specific_result * area

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
    areas_per_occupant = []
    Qs_Wp = []
    X_ghp = []
    Ea_Wm2 = []
    El_Wm2 = []
    Epro_Wm2 = []
    Ere_Wm2 = []
    Ed_Wm2 = []
    Vww_lpd = []
    Vw_lpd = []
    Ve_lps = []
    for use in list_uses:
        # Read from archetypes_schedules
        x = pd.read_excel(locator.get_archetypes_schedules(), use).T

        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule, area_per_occupant, internal_loads = \
            read_schedules(use, x)

        # get occupancy density per schedule in a list
        if area_per_occupant != 0:
            occ_densities.append(1/area_per_occupant)
        else: occ_densities.append(area_per_occupant)
        # areas_per_occupant.append(area_per_occupant)
        # get internal loads per schedule in a list
        Qs_Wp.append(internal_loads[0])
        X_ghp.append(internal_loads[1])
        Ea_Wm2.append(internal_loads[2])
        El_Wm2.append(internal_loads[3])
        Epro_Wm2.append(internal_loads[4])
        Ere_Wm2.append(internal_loads[5])
        Ed_Wm2.append(internal_loads[6])
        Vww_lpd.append(internal_loads[7])
        Vw_lpd.append(internal_loads[8])
        Ve_lps.append(internal_loads[9])

        # get yearly schedules in a list
        schedule = get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule)
        schedules.append(schedule)

    internal_loads = {'Qs_Wp': Qs_Wp, 'X_ghp': X_ghp, 'Ea_Wm2': Ea_Wm2, 'El_Wm2': El_Wm2,
                                      'Epro_Wm2': Epro_Wm2, 'Ere_Wm2': Ere_Wm2, 'Ed_Wm2': Ed_Wm2, 'Vww_lpd': Vww_lpd,
                                      'Vw_lpd': Vw_lpd}
    ventilation = Ve_lps

    return schedules, occ_densities, internal_loads, ventilation


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
    # read occupant loads
    Qs_Wp = x['Qs_Wp'].values[:1][0]
    X_ghp = x['X_ghp'].values[:1][0]
    # read electricity demands
    Ea_Wm2 = x['Ea_Wm2'].values[:1][0]
    El_Wm2 = x['El_Wm2'].values[:1][0]
    Epro_Wm2 = x['Epro_Wm2'].values[:1][0]
    Ere_Wm2 = x['Ere_Wm2'].values[:1][0]
    Ed_Wm2 = x['Ed_Wm2'].values[:1][0]
    # read water demands
    Vww_lpd = x['Vww_lpd'].values[:1][0]
    Vw_lpd = x['Vw_lpd'].values[:1][0]
    # read ventilation demand
    Ve_lps = x['Ve_lps'].values[:1][0]

    # get internal loads and ventilation in a list
    internal_loads = [Qs_Wp, X_ghp, Ea_Wm2, El_Wm2, Epro_Wm2, Ere_Wm2, Ed_Wm2, Vww_lpd, Vw_lpd, Ve_lps]

    return occ, el, dhw, pro, month, occ_density, internal_loads
