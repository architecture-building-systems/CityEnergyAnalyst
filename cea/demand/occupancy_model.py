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
    """
    Reads schedules from the archetype schedule Excel file along with the corresponding internal loads and ventilation
    demands.

    :param dates: dates and times throughout the year
    :type dates: DatetimeIndex
    :param locator: an instance of InputLocator set to the scenario
    :type locator: InputLocator
    :param list_uses: list of occupancy types used in the scenario
    :type list_uses: list

    :return schedules: yearly schedule for each occupancy type used in the project
    :type schedules: list[tuple]
    :return occ_densities: occupant density in people per square meter for each occupancy type used in the project
    :type occ_densities: list[float]
    :return internal_loads: dictionary containing the internal loads for each occupancy type used in the project
    :type internal_loads: dict[list[float]]
    :return ventilation: ventilation demand for each occupancy type used in the project
    :type ventilation: list[float]
    """

    def get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule):
        """
        For a given use type, this script generates yearly schedules for occupancy, electricity demand,
        hot water demand, process electricity demand based on the daily and monthly schedules obtained from the
        archetype database.

        :param dates: dates and times throughout the year
        :type dates: DatetimeIndex
        :param occ_schedules: occupancy schedules for a weekdays, Saturdays and Sundays from the archetype database
        :type occ_schedules: list[array]
        :param el_schedules: electricity schedules for a weekdays, Saturdays and Sundays from the archetype database
        :type el_schedules: list[array]
        :param dhw_schedules: domestic hot water schedules for a weekdays, Saturdays and Sundays from the archetype
        database
        :type dhw_schedules: list[array]
        :param pro_schedules: process electricity schedules for a weekdays, Saturdays and Sundays from the archetype
        database
        :type pro_schedules: list[array]
        :param month_schedule: monthly schedules from the archetype database
        :type month_schedule: ndarray

        :return occ: occupancy schedule for each hour of the year
        :type occ: list[float]
        :return el: electricity schedule for each hour of the year
        :type el: list[float]
        :return dhw: domestic hot water schedule for each hour of the year
        :type dhw: list[float]
        :return pro: process electricity schedule for each hour of the year
        :type pro: list[float]

        """

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
    archetypes_internal_loads = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS').set_index('Code')
    Qs_Wp = []
    X_ghp = []
    Ea_Wm2 = []
    El_Wm2 = []
    Epro_Wm2 = []
    Ere_Wm2 = []
    Ed_Wm2 = []
    Vww_lpd = []
    Vw_lpd = []
    archetypes_indoor_comfort = pd.read_excel(locator.get_archetypes_properties(), 'INDOOR_COMFORT').set_index('Code')
    Ve_lps = []
    for use in list_uses:
        # Read from archetypes_schedules and properties
        archetypes_schedules = pd.read_excel(locator.get_archetypes_schedules(), use).T

        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule, \
        area_per_occupant = read_schedules(use, archetypes_schedules)

        # get occupancy density per schedule in a list
        if area_per_occupant != 0:
            occ_densities.append(1/area_per_occupant)
        else: occ_densities.append(area_per_occupant)

        # get internal loads per schedule in a list
        Qs_Wp.append(archetypes_internal_loads['Qs_Wp'][use])
        X_ghp.append(archetypes_internal_loads['X_ghp'][use])
        Ea_Wm2.append(archetypes_internal_loads['Ea_Wm2'][use])
        El_Wm2.append(archetypes_internal_loads['El_Wm2'][use])
        Epro_Wm2.append(archetypes_internal_loads['Epro_Wm2'][use])
        Ere_Wm2.append(archetypes_internal_loads['Ere_Wm2'][use])
        Ed_Wm2.append(archetypes_internal_loads['Ed_Wm2'][use])
        Vww_lpd.append(archetypes_internal_loads['Vww_lpd'][use])
        Vw_lpd.append(archetypes_internal_loads['Vw_lpd'][use])

        # get ventilation required per schedule in a list
        Ve_lps.append(archetypes_indoor_comfort['Ve_lps'][use])

        # get yearly schedules in a list
        schedule = get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule)
        schedules.append(schedule)

    internal_loads = {'Qs_Wp': Qs_Wp, 'X_ghp': X_ghp, 'Ea_Wm2': Ea_Wm2, 'El_Wm2': El_Wm2,
                                      'Epro_Wm2': Epro_Wm2, 'Ere_Wm2': Ere_Wm2, 'Ed_Wm2': Ed_Wm2, 'Vww_lpd': Vww_lpd,
                                      'Vw_lpd': Vw_lpd}
    ventilation = Ve_lps

    return schedules, occ_densities, internal_loads, ventilation

def read_schedules(use, x):
    """
    This function reads the occupancy, electricity, domestic hot water, process electricity and monthly schedules for a
    given use type from the schedules database.

    :param use: occupancy type (e.g. 'SCHOOL')
    :type use: str
    :param x: Excel worksheet containing the schedule database for a given occupancy type from the archetypes database
    :type x: DataFrame

    :return occ: the daily occupancy schedule for the given occupancy type
    :type occ: list[array]
    :return el: the daily electricity schedule for the given occupancy type
    :type el: list[array]
    :return dhw: the daily domestic hot water schedule for the given occupancy type
    :type dhw: list[array]
    :return pro: the daily process electricity schedule for the given occupancy type
    :type pro: list[array]
    :return month: the monthly schedule for the given occupancy type
    :type month: ndarray
    :return occ_density: the occupants per square meter for the given occupancy type
    :type occ_density: int
    :return internal_loads: the internal loads and ventilation needs for the given occupancy types
    :type internal_loads: list

    """
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

    # # get internal loads and ventilation in a list
    # internal_loads = [Qs_Wp, X_ghp, Ea_Wm2, El_Wm2, Epro_Wm2, Ere_Wm2, Ed_Wm2, Vww_lpd, Vw_lpd, Ve_lps]

    return occ, el, dhw, pro, month, occ_density # , Qs_Wp, X_ghp, Ea_Wm2, El_Wm2, Epro_Wm2, Ere_Wm2, Ed_Wm2, Vww_lpd, Vw_lpd, Ve_lps
