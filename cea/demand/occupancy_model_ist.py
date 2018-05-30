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
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_schedules(region, list_uses, archetype_schedules, occupancy, archetype_values):
    """
    Given schedule data for archetypal building uses, `calc_schedule` calculates the schedule for a building
    with possibly a mixed schedule as defined in `building_uses` using a weighted average approach. The schedules are
    normalized such that the final demands and internal gains are calculated from the specified building properties and
    not the archetype values.

    Schedules for internal loads due to occupants and ventilation are in p/m2 (since for a variable X the hourly value
    is calculated as schedule * X * A). The electrical schedules are unitless.

    The script generates the following schedules:
    - ``people``: number of people per square meter at each hour [in p/m2]
    - ``ve``: ventilation demand schedule weighted by the corresponding occupancy types [in lps/(l/m2/s)]
    - ``Qs``: sensible heat gain due to occupancy weighted by the corresponding occupancy types [in Wp/Wm2]
    - ``X``: moisture gain due to occupants weighted by the corresponding occupancy types [in ghp/(g/m2/h)]
    - ``Ea``: electricity demand for appliances at each hour [unitless]
    - ``El``: electricity demand for lighting at each hour [unitless]
    - ``Epro``: electricity demand for process at each hour [unitless]
    - ``Ere``: electricity demand for refrigeration at each hour [unitless]
    - ``Ed``: electricity demand for data centers at each hour [unitless]
    - ``Vww``: domestic hot water schedule at each hour  weighted by the corresponding occupancy types [in lpd/(l/m2/d)]
    - ``Vw``: total water schedule at each hour weighted by the corresponding occupancy types [in lpd/(l/m2/d)]
    - ``Qhpro``: heating demand for process at each hour [unitless]

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param archetype_schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type archetype_schedules: list[ndarray[float]]

    :param occupancy: dict containing the share of the current building used by each type of occupancy
    :type occupancy: dict[str:float]

    :param archetype_values: occupant density, ventilation and internal loads for each archetypal occupancy type
    :type archetype_values: dict[str:array]

    :returns schedules: a dictionary containing the weighted average schedules for: occupancy; ventilation demand;
        sensible heat and moisture gains due to occupancy; electricity demand for appliances, lighting, processes,
        refrigeration and data centers; demand for water and domestic hot water
    :rtype: dict[array]
    """

    # set up schedules to be defined and empty dictionary
    schedule_labels = ['people', 've', 'Qs', 'X', 'Ea', 'El', 'Epro', 'Ere', 'Ed', 'Vww', 'Vw', 'Qhpro']
    schedules = {}

    # define the archetypal schedule type to be used for the creation of each schedule: 0 for occupancy, 1 for
    # electricity use, 2 for domestic hot water consumption, 3 for processes
    schedule_code_dict = {'people': 0, 've': 0, 'Qs': 0, 'X': 0, 'Ea': 1, 'El': 1, 'Ere': 1, 'Ed': 1, 'Vww': 2,
                          'Vw': 2, 'Epro': 3, 'Qhpro': 3}

    # define function to calculated the weighted average of schedules
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    # calculate average occupant density for the building
    people_per_square_meter = 0
    for num in range(len(list_uses)):
        people_per_square_meter += occupancy[list_uses[num]] * archetype_values['people'][num]

    for label in schedule_labels:
        # each schedule is defined as (sum of schedule[i]*X[i]*share_of_area[i])/(sum of X[i]*share_of_area[i]) for each
        # variable X and occupancy type i
        code = schedule_code_dict[label]
        current_schedule = np.zeros(8760)
        normalizing_value = 0.0
        current_archetype_values = archetype_values[label]
        for num in range(len(list_uses)):
            if current_archetype_values[num] != 0: # do not consider when the value is 0
                current_share_of_use = occupancy[list_uses[num]]
                # for variables that depend on the number of people, the schedule needs to be calculated by number of
                # people for each use at each time step, not the share of the occupancy for each
                if label in ['ve','Qs','X', 'Vww', 'Vw']:
                    share_time_occupancy_density = \
                        current_archetype_values[num] * archetype_values['people'][num] * current_share_of_use
                    if people_per_square_meter > 0:
                        normalizing_value += share_time_occupancy_density / people_per_square_meter
                else:
                    share_time_occupancy_density = current_archetype_values[num] * current_share_of_use
                    normalizing_value += share_time_occupancy_density

                current_schedule = np.vectorize(calc_average)(current_schedule, archetype_schedules[num][code],
                                                              share_time_occupancy_density)
        if label == 'people':
            schedules[label] = current_schedule
        elif normalizing_value == 0:
            schedules[label] = current_schedule * 0
        else:
            schedules[label] = current_schedule / normalizing_value

    return schedules

# read schedules and archetypal values from excel file
def schedule_maker(region, dates, locator, list_uses):
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

    # get internal loads and indoor comfort from archetypes
    archetypes_internal_loads = pd.read_excel(locator.get_archetypes_properties(region), 'INTERNAL_LOADS').set_index('Code')
    archetypes_indoor_comfort = pd.read_excel(locator.get_archetypes_properties(region), 'INDOOR_COMFORT').set_index('Code')

    # create empty list of archetypal schedules and occupant densities
    schedules = []
    occ_densities = []

    # create empty lists for the values of each archetype's ventilation and internal loads
    Qs_Wm2 = []
    X_ghm2 = []
    Ea_Wm2 = []
    El_Wm2 = []
    Epro_Wm2 = []
    Ere_Wm2 = []
    Ed_Wm2 = []
    Vww_ldm2 = []
    Vw_ldm2 = []
    Ve_lsm2 = []
    Qhpro_Wm2 = []

    for use in list_uses:
        # read from archetypes_schedules and properties
        archetypes_schedules = pd.read_excel(locator.get_archetypes_schedules(region), use).T

        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule, area_per_occupant = read_schedules(
            use, archetypes_schedules)

        # get occupancy density per schedule in a list
        if area_per_occupant != 0:
            occ_densities.append(1 / area_per_occupant)
        else:
            occ_densities.append(area_per_occupant)

        # get internal loads per schedule in a list
        Ea_Wm2.append(archetypes_internal_loads['Ea_Wm2'][use])
        El_Wm2.append(archetypes_internal_loads['El_Wm2'][use])
        Epro_Wm2.append(archetypes_internal_loads['Epro_Wm2'][use])
        Ere_Wm2.append(archetypes_internal_loads['Ere_Wm2'][use])
        Ed_Wm2.append(archetypes_internal_loads['Ed_Wm2'][use])
        Qs_Wm2.append(archetypes_internal_loads['Qs_Wp'][use])
        X_ghm2.append(archetypes_internal_loads['X_ghp'][use])
        Vww_ldm2.append(archetypes_internal_loads['Vww_lpd'][use])
        Vw_ldm2.append(archetypes_internal_loads['Vw_lpd'][use])
        Ve_lsm2.append(archetypes_indoor_comfort['Ve_lps'][use])
        Qhpro_Wm2.append(archetypes_internal_loads['Qhpro_Wm2'][use])

        # get yearly schedules in a list
        schedule = get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule)
        schedules.append(schedule)

    archetype_values = {'people': occ_densities, 'Qs': Qs_Wm2, 'X': X_ghm2, 'Ea': Ea_Wm2, 'El': El_Wm2,
                        'Epro': Epro_Wm2, 'Ere': Ere_Wm2, 'Ed': Ed_Wm2, 'Vww': Vww_ldm2,
                        'Vw': Vw_ldm2, 've': Ve_lsm2, 'Qhpro': Qhpro_Wm2}

    return schedules, archetype_values

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
    :return area_per_occupant: the occupants per square meter for the given occupancy type
    :type area_per_occupant: int

    """
    # read schedules from excel file
    occ = [x['Weekday_1'].values[:24], x['Saturday_1'].values[:24], x['Sunday_1'].values[:24]]
    el = [x['Weekday_2'].values[:24], x['Saturday_2'].values[:24], x['Sunday_2'].values[:24]]
    dhw = [x['Weekday_3'].values[:24], x['Saturday_3'].values[:24], x['Sunday_3'].values[:24]]
    month = x['month'].values[:12]

    if use == "INDUSTRIAL":
        pro = [x['Weekday_4'].values[:24], x['Saturday_4'].values[:24], x['Sunday_4'].values[:24]]
    else:
        pro = [np.zeros(24), np.zeros(24), np.zeros(24)]

    # read area per occupant
    area_per_occupant = x['density'].values[:1][0]

    return occ, el, dhw, pro, month, area_per_occupant
