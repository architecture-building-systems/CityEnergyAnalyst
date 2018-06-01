from __future__ import division
import pandas as pd
import numpy as np
import random
import cea.globalvar
import cea.inputlocator
import cea.config

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_schedules(list_uses, archetype_schedules, bpr, archetype_values, stochastic_occupancy):
    """
    Given schedule data for archetypal building uses, `calc_schedule` calculates the schedule for a building
    with possibly a mixed schedule as defined in `building_uses` using a weighted average approach. The schedules are
    normalized such that the final demands and internal gains are calculated from the specified building properties and
    not the archetype values. Depending on the value given to `stochastic_occupancy` either the deterministic or
    stochastic model of occupancy will be used.

    The script generates the following schedules:
    - ``people``: number of people at each hour [in p]
    - ``ve``: ventilation demand schedule normalized by the archetypal ventilation demand per person [in (l/s)/(l/p/s)]
    - ``Qs``: sensible heat gain due to occupancy normalized by the archetypal gains per person [in W/(Wp)]
    - ``X``: moisture gain due to occupants normalized by the archetypal gains per person [in (g/h)/(g/p/h)]
    - ``Ea``: electricity demand for appliances at each hour normalized by the archetypal demand per m2 [in W/(W/m2)]
    - ``El``: electricity demand for lighting at each hour normalized by the archetypal demand per m2 [in W/(W/m2)]
    - ``Epro``: electricity demand for process at each hour normalized by the archetypal demand per m2 [in W/(W/m2)]
    - ``Ere``: electricity demand for refrigeration at each hour normalized by the archetypal demand per m2 [W/(W/m2)]
    - ``Ed``: electricity demand for data centers at each hour normalized by the archetypal demand per m2 [in W/(W/m2)]
    - ``Vww``: domestic hot water schedule at each hour normalized by the archetypal demand [in (l/h)/(l/p/d)]
    - ``Vw``: total water schedule at each hour normalized by the archetypal demand [in (l/h)/(l/p/d)]
    - ``Qhpro``: heating demand for process at each hour normalized by the archetypal demand per m2 [in W/(W/m2)]

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param archetype_schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type archetype_schedules: list[ndarray[float]]

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :param archetype_values: occupant density, ventilation and internal loads for each archetypal occupancy type
    :type archetype_values: dict[str:array]
    
    :param stochastic_occupancy: a boolean that states whether the stochastic occupancy model (True) or the 
        deterministic one (False) should be used
    :type stochastic_occupancy: Boolean

    :returns schedules: a dictionary containing the weighted average schedules for: occupancy; ventilation demand;
        sensible heat and moisture gains due to occupancy; electricity demand for appliances, lighting, processes,
        refrigeration and data centers; demand for water and domestic hot water
    :rtype: dict[array]
    """

    # calculate average occupant density for the building
    people_per_square_meter = 0
    for num in range(len(list_uses)):
        people_per_square_meter += bpr.occupancy[list_uses[num]] * archetype_values['people'][num]

    # no need to calculate occupancy if people_per_square_meter == 0
    if people_per_square_meter > 0:
        if stochastic_occupancy:
            schedules = calc_stochastic_schedules(archetype_schedules, archetype_values, bpr, list_uses,
                                                  people_per_square_meter)
        else:
            schedules = calc_deterministic_schedules(archetype_schedules, archetype_values, bpr, list_uses,
                                                     people_per_square_meter)
    else:
        schedules = {}
        # occupant-related schedules are 0 since there are no occupants
        for schedule in ['people', 've', 'Qs', 'X', 'Vww', 'Vw']:
            schedules[schedule] = np.zeros(8760)
        # electricity and process schedules may be greater than 0
        for schedule in ['Ea', 'El', 'Qcre', 'Ed', 'Epro', 'Qhpro']:
            codes = {'Ea': 1, 'El': 1, 'Ed': 1, 'Epro': 3, 'Qhpro': 3,'Qcre': 3}
            schedules[schedule] = bpr.rc_model['Aef'] * \
                                  calc_remaining_schedules_deterministic(archetype_schedules,
                                                                         archetype_values[schedule], list_uses,
                                                                         bpr.occupancy, codes[schedule],
                                                                         archetype_values['people'])

    return schedules


def calc_deterministic_schedules(archetype_schedules, archetype_values, bpr, list_uses, people_per_square_meter):
    """
    Calculate the profile of deterministic occupancy for each each type of use in the building based on archetypal
    schedules. For variables that depend on the number of people, the schedule needs to be calculated by number of
    people for each use at each time step, not the share of the occupancy for each, so the schedules for humidity gains,
    heat gains and ventilation demand are also calculated based on the archetypal values for these properties.
    These are then normalized so that the user provided value and not the archetypal one is used for the demand
    calculations.

    e.g.
        - For humidity gains, X, for each use i, sum of (schedule[i]*archetypal_X[i]*share_of_area[i])/sum of (X[i]*share_of_area[i])
            (This generates a normalized schedule for X for a given building, which is then multiplied by the user-supplied value
            for humidity gains in the building.)

    :param archetype_schedules: defined in calc_schedules
    :param archetype_values: defined in calc_schedules
    :param bpr: defined in calc_schedules
    :param list_uses: defined in calc_schedules
    :param people_per_square_meter: defined in calc_schedules

    :return schedules: dict containing the deterministic schedules for occupancy, humidity gains, ventilation and heat
        gains due to occupants for a given building with single or mixed uses
    :rtype schedules: dict
    """

    # define schedules and codes
    occupant_schedules = ['ve', 'Qs', 'X']
    electricity_schedules = ['Ea', 'El', 'Ed']
    water_schedules = ['Vww', 'Vw']
    process_schedules = ['Epro', 'Qhpro', 'Qcre']

    # schedule_codes define which archetypal schedule should be used for the given schedule
    schedule_codes = {'people': 0, 'electricity': 1, 'water': 2, 'processes': 3}

    # start empty schedules
    schedules = {}
    normalizing_values = {}
    for schedule in ['people'] + occupant_schedules + electricity_schedules + water_schedules + process_schedules:
        schedules[schedule] = np.zeros(8760, dtype=float)
        normalizing_values[schedule] = 0.0
    for num in range(len(list_uses)):
        if bpr.occupancy[list_uses[num]] > 0:
            current_share_of_use = bpr.occupancy[list_uses[num]]
            if archetype_values['people'][num] != 0:  # do not consider when the value is 0
                current_schedule = np.rint(np.array(archetype_schedules[num][0]) * archetype_values['people'][num] *
                                           current_share_of_use * bpr.rc_model['Af'])
                schedules['people'] += current_schedule
                for label in occupant_schedules:
                    current_archetype_values = archetype_values[label]
                    if current_archetype_values[num] != 0:  # do not consider when the value is 0
                        normalizing_values[label] += current_archetype_values[num] * archetype_values['people'][
                            num] * current_share_of_use / people_per_square_meter
                        schedules[label] = np.vectorize(calc_average)(schedules[label], current_schedule,
                                                                      current_archetype_values[num])

    for label in occupant_schedules:
        if normalizing_values[label] == 0:
            schedules[label] = np.zeros(8760)
        else:
            schedules[label] = schedules[label] / normalizing_values[label]

    # create remaining schedules
    for schedule in electricity_schedules:
        schedules[schedule] = calc_remaining_schedules_deterministic(archetype_schedules, archetype_values[schedule],
                                                                     list_uses, bpr.occupancy,
                                                                     schedule_codes['electricity'],
                                                                     archetype_values['people']) * bpr.rc_model['Aef']
    for schedule in water_schedules:
        schedules[schedule] = calc_remaining_schedules_deterministic(archetype_schedules, archetype_values[schedule],
                                                                     list_uses, bpr.occupancy, schedule_codes['water'],
                                                                     archetype_values['people']) * \
                              bpr.rc_model['Af'] * people_per_square_meter
    for schedule in process_schedules:
        schedules[schedule] = calc_remaining_schedules_deterministic(archetype_schedules, archetype_values[schedule],
                                                                     list_uses, bpr.occupancy,
                                                                     schedule_codes['processes'],
                                                                     archetype_values['people']) * bpr.rc_model['Aef']

    return schedules


def calc_stochastic_schedules(archetype_schedules, archetype_values, bpr, list_uses, people_per_square_meter):
    """
    Calculate the profile of random occupancy for each occupant in each type of use in the building. Each profile is
    calculated individually with a randomly-selected mobility parameter mu.

    For each use in the building, occupant presence at each time t is calculated based on the stochastic occupancy model
    by Page et al. (2008). Occupant presence is modeled based on the probability of occupant presence at the current and
    next time step as given by the occupant schedules used in the deterministic model. The mobility parameter for each
    occupant is selected at random from the vector of mobility parameters assumed by Sandoval et al. (2017). Based on
    the type of activity and occupant presence, the

    :param archetype_schedules: defined in calc_schedules
    :param archetype_values: defined in calc_schedules
    :param list_uses: defined in calc_schedules
    :param bpr: defined in calc_schedules
    :param people_per_square_meter: defined in calc_schedules

    :return schedules: dict containing the stochastic schedules for occupancy, humidity gains, ventilation and heat
        gains due to occupants for a given building with single or mixed uses
    :rtype schedules: dict

    .. [Page, J., et al., 2008] Page, J., et al. A generalised stochastic model for the simulation of occupant presence.
        Energy and Buildings, Vol. 40, No. 2, 2008, pp 83-98.
    .. [Sandoval, D., et al., 2017] Sandoval, D., et al. How low exergy buildings and distributed electricity storage
        can contribute to flexibility within the demand side. Applied Energy, Vol. 187, No. 1, 2017, pp. 116-127.
    """

    # define schedules and codes
    occupant_schedules = ['ve', 'Qs', 'X']
    electricity_schedules = ['Ea', 'El', 'Ere', 'Ed']
    water_schedules = ['Vww', 'Vw']
    process_schedules = ['Epro', 'Qhpro']
    # schedule_codes define which archetypal schedule should be used for the given schedule
    schedule_codes = {'people': 0, 'electricity': 1, 'water': 2, 'processes': 3}

    # start empty schedules
    schedules = {}
    normalizing_values = {}
    for schedule in ['people'] + occupant_schedules + electricity_schedules + water_schedules + process_schedules:
        schedules[schedule] = np.zeros(8760)
        normalizing_values[schedule] = 0.0

    # vector of mobility parameters
    mu_v = [0.18, 0.33, 0.54, 0.67, 0.82, 1.22, 1.50, 3.0, 5.67]
    len_mu_v = len(mu_v)

    for num in range(len(list_uses)):
        current_share_of_use = bpr.occupancy[list_uses[num]]
        current_stochastic_schedule = np.zeros(8760)
        if current_share_of_use > 0:
            occupants_in_current_use = int(archetype_values['people'][num] * current_share_of_use * bpr.rc_model['Af'])
            archetype_schedule = archetype_schedules[num][0]
            for occupant in range(occupants_in_current_use):
                mu = mu_v[int(len_mu_v * random.random())]
                occupant_pattern = calc_individual_occupant_schedule(mu, archetype_schedule)
                current_stochastic_schedule += occupant_pattern
                schedules['people'] += occupant_pattern
                for label in occupant_schedules:
                    schedules[label] = np.vectorize(calc_average)(schedules[label], occupant_pattern,
                                                                  archetype_values[label][num])

            for label in occupant_schedules:
                current_archetype_values = archetype_values[label]
                if current_archetype_values[num] != 0:  # do not consider when the value is 0
                    normalizing_values[label] += current_archetype_values[num] * archetype_values['people'][num] * \
                                                 current_share_of_use / people_per_square_meter

            # for all other schedules, the database schedule is normalized by the schedule for people and then 
            # multiplied by the number of people from the stochastic calculation
            current_stochastic_schedule /= occupants_in_current_use
            unoccupied_times = np.array([i == 0 for i in archetype_schedules[num][schedule_codes['people']]])
            normalized_schedule = make_normalized_stochastic_schedule(current_stochastic_schedule,
                                                                      archetype_schedules[num][
                                                                          schedule_codes['people']],
                                                                      unoccupied_times)
            # since electricity demand is != 0 when the number of occupants is 0,
            # share_time_occupancy_density = 1 if there are no occupants and equal to the normalized schedule otherwise
            share_time_occupancy_density = unoccupied_times + (1 - unoccupied_times) * normalized_schedule

            # calculate remaining schedules
            for label in electricity_schedules:
                if archetype_values[label][num] != 0:
                    normalizing_values[label], schedules[label] = calc_remaining_schedules_stochastic(
                        normalizing_values[label], archetype_values[label][num], current_share_of_use,
                        bpr.rc_model['Aef'], schedules[label], archetype_schedules[num][schedule_codes['electricity']],
                        share_time_occupancy_density)
            for label in water_schedules:
                if archetype_values[label][num] != 0:
                    normalizing_values[label], schedules[label] = calc_remaining_schedules_stochastic(
                        normalizing_values[label], archetype_values[label][num], current_share_of_use,
                        bpr.rc_model['Af'], schedules[label], archetype_schedules[num][schedule_codes['water']],
                        share_time_occupancy_density * archetype_values['people'][num])
            for label in process_schedules:
                if archetype_values[label][num] != 0:
                    normalizing_values[label], schedules[label] = calc_remaining_schedules_stochastic(
                        normalizing_values[label], archetype_values[label][num], current_share_of_use,
                        bpr.rc_model['Aef'], schedules[label], archetype_schedules[num][schedule_codes['processes']],
                        share_time_occupancy_density)

    for label in occupant_schedules + electricity_schedules + process_schedules + water_schedules:
        if normalizing_values[label] == 0:
            schedules[label] = np.zeros(8760)
        else:
            schedules[label] /= normalizing_values[label]

    return schedules


def calc_individual_occupant_schedule(mu, archetype_schedule):
    """
    Calculates the stochastic occupancy pattern for an individual based on Page et al. (2007).

    :param mu: parameter of mobility
    :type mu: float
    :param archetype_schedule: schedule of occupancy for the corresponding archetype
    :type archetype_schedule: list[float]

    :return pattern: yearly occupancy pattern for a given occupant in a given occupancy type
    :rtype pattern: list[int]
    """

    # assign initial state: assume equal to the archetypal occupancy schedule at t = 0
    state = archetype_schedule[0]

    # start list of occupancy states throughout the year
    pattern = [state]

    # calculate probability of presence for each hour of the year
    for i in range(len(archetype_schedule[:-1])):
        # get probability of presence at t and t+1 from archetypal schedule
        p_0 = archetype_schedule[i]
        p_1 = archetype_schedule[i + 1]
        # calculate probability of transition from absence to presence (T01) and from presence to presence (T11)
        T01, T11 = calculate_transition_probabilities(mu, p_0, p_1)

        if state == 1:
            next = get_random_presence(T11)
        else:
            next = get_random_presence(T01)

        pattern.append(next)
        state = next

    return pattern


def calculate_transition_probabilities(mu, P0, P1):
    """
    Calculates the transition probabilities at a given time step as defined by Page et al. (2007).
    These are the probability of arriving (T01) and the probability of staying in (T11) given the parameter of mobility
    mu, the probability of the present state (P0), and the probability of the next state t+1 (P1).

    :param mu: parameter of mobility
    :type mu: float
    :param P0: probability of presence at the current time step t
    :type P0: float
    :param P1: probability of presence at the next time step t+1
    :type P1: float

    :return T01: probability of transition from absence to presence at current time step
    :rtype T01: float
    :return T11: probability of transition from presence to presence at current time step
    :rtype T11: float
    """

    # Calculate mobility factor fraction from Page et al. equation 5
    m = (mu - 1) / (mu + 1)
    # Calculate transition probability of arriving and transition probability of staying
    T01 = (m) * P0 + P1
    if P0 != 0:
        T11 = ((P0 - 1) / P0) * (m * P0 + P1) + P1 / P0
    else:
        T11 = 0

    # For some instances of mu the probabilities are bigger than 1, so the min function is used in the return statement.
    return min(1, T01), min(1, T11)


def get_random_presence(p):
    """
    Get the current occupant state (presence=1 or absence=0) at the current time step given a probability p.

    :param p: A probability (e.g. T01, T11)
    :type p: float

    Returns the randomly-chosen state (0 or 1).
    """

    # Calculate probability of presence
    P1 = int(p * 100)
    # Calculate probability of absence
    P0 = 100 - P1

    # Create population of possible values and choose one value
    weighted_choices = [(1, P1), (0, P0)]
    population = [val for val, cnt in weighted_choices for i in range(cnt)]

    return random.choice(population)


def calc_remaining_schedules_deterministic(archetype_schedules, archetype_values, list_uses, occupancy, schedule_code,
                                           archetype_occupants):
    """
    This script calculates the schedule for electricity, hot water or process energy demand. The resulted schedules are
    normalized so that when multiplied by the user-given normalized demand for the entire building is given, the hourly
    demand for each of these services at a given time t is calculated.

    For a given demand type X (electricity/hot water/process energy demand) and occupancy type i, each schedule is
    defined as (sum of schedule[i]*X[i]*share_of_area[i])/(sum of X[i]*share_of_area[i]).

    :param archetype_schedules: defined in calc_schedules
    :param archetype_values: defined in calc_schedules
    :param list_uses: defined in calc_schedules
    :param occupancy: defined in calc_schedules
    :param schedule_code: defined in calc_schedules
    :param archetype_occupants: occupants for the given building function according to archetype

    :return: normalized schedule for a given occupancy type
    """

    current_schedule = np.zeros(8760)
    normalizing_value = 0.0
    for num in range(len(list_uses)):
        if archetype_values[num] != 0:  # do not consider when the value is 0
            if occupancy[list_uses[num]] > 0:
                current_share_of_use = occupancy[list_uses[num]]
                if schedule_code == 2:
                    # for variables that depend on the number of people, the schedule needs to be calculated by number
                    # of people for each use at each time step, not the share of the occupancy for each
                    share_time_occupancy_density = archetype_values[num] * current_share_of_use * \
                                                   archetype_occupants[num]
                else:
                    share_time_occupancy_density = archetype_values[num] * current_share_of_use

                normalizing_value += share_time_occupancy_density

                current_schedule = np.vectorize(calc_average)(current_schedule, archetype_schedules[num][schedule_code],
                                                              share_time_occupancy_density)

    if normalizing_value == 0:
        return current_schedule * 0
    else:
        return current_schedule / normalizing_value


def calc_remaining_schedules_stochastic(normalizing_value, archetype_value, current_share_of_use, reference_area,
                                        schedule, archetype_schedule, share_time_occupancy_density):
    """
    This script calculates the schedule for electricity, hot water or process energy demand when the stochastic model of
    occupancy is used. The resulted schedules are normalized so that when multiplied by the user-given normalized demand
    for the entire building is given, the hourly demand for each of these services at a given time t is calculated.

    For a given demand type X (electricity/hot water/process energy demand) and occupancy type i, each schedule is
    defined as (sum of schedule[i]*X[i]*share_of_area[i])/(sum of X[i]*share_of_area[i]).

    Unlike calc_remaining_schedules_deterministic, the schedule for each of these services in this case is calculated
    by multiplying the deterministic schedule for the given service by the normalized stochastic schedule of occupancy.

    :param normalizing_value: normalizing value for the current schedule
    :param archetype_value: defined in calc_schedules
    :param current_share_of_use: share of the current use in the total area of the building
    :param reference_area: area for the calculation of the given service, either 'Aef' or 'Af'
    :param schedule: current schedule being calculated
    :param archetype_schedule: archetypal schedule of the current service
    :param share_time_occupancy_density: normalizing schedule to calculate the effect of stochastic occupancy on the
        schedule for the current service; equals the number of people according to the stochastic model divided by the
        number of people according to the deterministic schedule; equals 1 if there are no occupants in the building

    :return normalizing_value: updated normalizing value for the current schedule
    :return schedule: updated schedule for the current service
    """

    normalizing_value += archetype_value * current_share_of_use
    schedule = np.vectorize(calc_average)(schedule, archetype_schedule, (current_share_of_use * reference_area) *
                                          archetype_value * share_time_occupancy_density)

    return normalizing_value, schedule


def make_normalized_stochastic_schedule(stochastic_schedule, deterministic_schedule, unoccupied_times):
    """
    Creates a normalized stochastic schedule where for each time t the value is the number of people
    generated by the stochastic schedule divided by the number of people according to the deterministic
    schedule. At times when the building is unoccupied, the value is defined as 1 to avoid division errors.

    :param stochastic_schedule: occupant schedule generated by the stochastic model
    :type stochastic_schedule: ndarray[float]
    :param deterministic_schedule: occupant schedule generated by the deterministic model
    :type deterministic_schedule: ndarray[float]
    :param unoccupied_times: array containing booleans that state whether the building is occupied or not
    :type unoccupied_times: ndarray[Boolean]
    :param current_share_of_use: percentage of the building area that corresponds to the current building function
    :type current_share_of_use: float
    :return: array containing the normalized stochastic schedule
    :rtype: ndarray[float]
    """

    return stochastic_schedule / (unoccupied_times + (1 - unoccupied_times) * deterministic_schedule)


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
    :rtype occ: list[float]
    :return el: electricity schedule for each hour of the year
    :rtype el: list[float]
    :return dhw: domestic hot water schedule for each hour of the year
    :rtype dhw: list[float]
    :return pro: process electricity schedule for each hour of the year
    :rtype pro: list[float]
    """

    occ, el, dhw, pro = ([] for i in range(4))

    if dhw_schedules[0].sum() != 0:
        dhw_weekday_max = dhw_schedules[0].sum() ** -1
    else:
        dhw_weekday_max = 0

    if dhw_schedules[1].sum() != 0:
        dhw_sat_max = dhw_schedules[1].sum() ** -1
    else:
        dhw_sat_max = 0

    if dhw_schedules[2].sum() != 0:
        dhw_sun_max = dhw_schedules[2].sum() ** -1
    else:
        dhw_sun_max = 0

    for date in dates:
        month_year = month_schedule[date.month - 1]
        hour_day = date.hour
        dayofweek = date.dayofweek
        if 0 <= dayofweek < 5:  # weekday
            occ.append(occ_schedules[0][hour_day] * month_year)
            el.append(el_schedules[0][hour_day] * month_year)
            dhw.append(dhw_schedules[0][hour_day] * month_year * dhw_weekday_max)  # normalized dhw demand flow rates
            pro.append(pro_schedules[0][hour_day] * month_year)
        elif dayofweek is 5:  # saturday
            occ.append(occ_schedules[1][hour_day] * month_year)
            el.append(el_schedules[1][hour_day] * month_year)
            dhw.append(dhw_schedules[1][hour_day] * month_year * dhw_sat_max)  # normalized dhw demand flow rates
            pro.append(pro_schedules[1][hour_day] * month_year)
        else:  # sunday
            occ.append(occ_schedules[2][hour_day] * month_year)
            el.append(el_schedules[2][hour_day] * month_year)
            dhw.append(dhw_schedules[2][hour_day] * month_year * dhw_sun_max)  # normalized dhw demand flow rates
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
    :rtype occ: list[array]
    :return el: the daily electricity schedule for the given occupancy type
    :rtype el: list[array]
    :return dhw: the daily domestic hot water schedule for the given occupancy type
    :rtype dhw: list[array]
    :return pro: the daily process electricity schedule for the given occupancy type
    :rtype pro: list[array]
    :return month: the monthly schedule for the given occupancy type
    :rtype month: ndarray
    :return area_per_occupant: the occupants per square meter for the given occupancy type
    :rtype area_per_occupant: int
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
    :rtype schedules: list[tuple]
    :return archetype_values: dict containing the values for occupant density  (in people/m2) internal loads and
        ventilation demand for each occupancy type used in the project
    :rtype archetype_values: dict[list[float]]
    """

    # get internal loads and indoor comfort from archetypes
    archetypes_internal_loads = pd.read_excel(locator.get_archetypes_properties(region), 'INTERNAL_LOADS').set_index(
        'Code')
    archetypes_indoor_comfort = pd.read_excel(locator.get_archetypes_properties(region), 'INDOOR_COMFORT').set_index(
        'Code')

    # create empty lists of archetypal schedules, occupant densities and each archetype's ventilation and internal loads
    schedules, occ_densities, Qs_Wm2, X_ghm2, Vww_ldm2, Vw_ldm2, Ve_lsm2, Qhpro_Wm2, Ea_Wm2, El_Wm2, Epro_Wm2, \
    Qcre_Wm2, Ed_Wm2 = ([] for i in range(13))

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
        Qcre_Wm2.append(archetypes_internal_loads['Qcre_Wm2'][use])
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
                        'Epro': Epro_Wm2, 'Qcre': Qcre_Wm2, 'Ed': Ed_Wm2, 'Vww': Vww_ldm2,
                        'Vw': Vw_ldm2, 've': Ve_lsm2, 'Qhpro': Qhpro_Wm2}

    return schedules, archetype_values


def calc_average(last, current, share_of_use):
    """
    function to calculate the weighted average of schedules
    """
    return last + current * share_of_use


def main(config):
    from cea.demand.building_properties import BuildingProperties

    gv = cea.globalvar.GlobalVariables()
    gv.config = config
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    config.demand.buildings = locator.get_zone_building_names()[0]
    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    building_properties = BuildingProperties(locator, gv, True, 'CH', False)
    bpr = building_properties[locator.get_zone_building_names()[0]]
    list_uses = ['OFFICE', 'INDUSTRIAL']
    bpr.occupancy = {'OFFICE': 0.5, 'INDUSTRIAL': 0.5}
    use_stochastic_occupancy = config.demand.use_stochastic_occupancy

    # calculate schedules
    archetype_schedules, archetype_values = schedule_maker('CH', date, locator, list_uses)
    return calc_schedules(list_uses, archetype_schedules, bpr, archetype_values, use_stochastic_occupancy)


if __name__ == '__main__':
    main(cea.config.Configuration())
