from __future__ import division

import os
import random

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR, MONTHS_IN_YEAR
from cea.datamanagement.schedule_helper import read_cea_schedule
from cea.demand.building_properties import calc_useful_areas
from cea.demand.constants import VARIABLE_CEA_SCHEDULE_RELATION
from cea.utilities import epwreader
from cea.utilities.date import get_dates_from_year
from cea.utilities.dbf import dbf_to_dataframe

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def occupancy_main(locator, config):
    # local variables
    buildings = config.occupancy.buildings
    occupancy_model = config.occupancy.occupancy_model

    if occupancy_model == 'deterministic':
        stochastic_schedule = False
    elif occupancy_model == 'stochastic':
        stochastic_schedule = True
    else:
        Exception('there is no valid input for type of occupancy model')

    if buildings == []:
        buildings = locator.get_zone_building_names()

    # get variables of indoor comfort and internal loads
    internal_loads = dbf_to_dataframe(locator.get_building_internal()).set_index('Name')
    indoor_comfort = dbf_to_dataframe(locator.get_building_comfort()).set_index('Name')
    architecture = dbf_to_dataframe(locator.get_building_architecture()).set_index('Name')

    # get building properties
    prop_geometry = Gdf.from_file(locator.get_zone_geometry())
    prop_geometry['footprint'] = prop_geometry.area
    prop_geometry['GFA_m2'] = prop_geometry['footprint'] * (prop_geometry['floors_ag'] + prop_geometry['floors_bg'])
    prop_geometry = prop_geometry.merge(architecture, on='Name').set_index('Name')
    prop_geometry = calc_useful_areas(prop_geometry)

    # get calculation year from weather file
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C',
                                                       'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]

    # create date range for the calculation year
    date_range = get_dates_from_year(year)

    for building in buildings:
        internal_loads_building = internal_loads.ix[building]
        indoor_comfort_building = indoor_comfort.ix[building]
        prop_geometry_building = prop_geometry.ix[building]
        daily_schedule_building, daily_schedule_building_metadata = read_cea_schedule(
            locator.get_building_schedules(building))
        monthly_multiplier = daily_schedule_building_metadata['MONTHLY_MULTIPLIER']
        calc_schedules(locator,
                                     building,
                                     date_range,
                                     daily_schedule_building,
                                     monthly_multiplier,
                                     internal_loads_building,
                                     indoor_comfort_building,
                                     prop_geometry_building,
                                     stochastic_schedule)


def calc_schedules(locator,
                   building,
                   date_range,
                   daily_schedule_building,
                   monthly_multiplier,
                   internal_loads_building,
                   indoor_comfort_building,
                   prop_geometry_building,
                   stochastic_schedule):
    """
    Calculate the profile of occupancy, electricity demand and domestic hot water consumption from the input schedules.
    For variables that depend on the number of people (humidity gains, heat gains and ventilation demand), additional
    schedules are created given the the number of people present at each time.

    Two occupant models are included: a deterministic one, which simply uses the schedules provided by the user; and a
    stochastic one, which is based on the two-state Markov chain model of Page et al. (2008). In the latter case,
    occupant presence is modeled based on the probability of occupant presence at the current and next time step as
    given by the occupant schedules used in the deterministic model.

    :param locator: InputLocator instance
    :param building: name of current building
    :param date_range: range of dates being considered
    :type date_range: DatetimeIndex
    :param daily_schedule_building: building schedules for occupancy, electricity demand, water consumption, and system operation
    :type daily_schedule_building: {str: array}
    :param monthly_multiplier: percentage of the total number of occupants present at each month of the year
    :type monthly_multiplier: [float]
    :param internal_loads_building: internal loads for the current building (from case study inputs)
    :param indoor_comfort_building: indoor comfort properties for the current building (from case study inputs)
    :param prop_geometry_building: building geometry (from case study inputs)
    :param stochastic_schedule: Boolean that defines whether the stochastic occupancy model should be used

    .. [Page, J., et al., 2008] Page, J., et al. A generalised stochastic model for the simulation of occupant presence.
        Energy and Buildings, Vol. 40, No. 2, 2008, pp 83-98.

    """

    final_schedule = {}
    days_in_schedule = len(list(set(daily_schedule_building['DAY'])))

    # SCHEDULE FOR PEOPLE OCCUPANCY
    array = daily_schedule_building[VARIABLE_CEA_SCHEDULE_RELATION['Occ_m2pax']]
    if internal_loads_building['Occ_m2pax'] > 0.0:
        yearly_array = get_yearly_vectors(date_range, days_in_schedule, array, monthly_multiplier)
        number_of_occupants = np.int(1 / internal_loads_building['Occ_m2pax'] * prop_geometry_building['Aocc'])
        if stochastic_schedule:
            # if the stochastic schedules are used, the stochastic schedule generator is called once for every occupant
            final_schedule['Occ_m2pax'] = np.zeros(HOURS_IN_YEAR)
            for occupant in range(number_of_occupants):
                final_schedule['Occ_m2pax'] += calc_individual_occupant_schedule(yearly_array)
        else:
            final_schedule['Occ_m2pax'] = np.round(yearly_array * number_of_occupants)
    else:
        final_schedule['Occ_m2pax'] = np.zeros(HOURS_IN_YEAR)

    # HEAT AND HUMIDITY GAINS FROM OCCUPANTS
    for variable in ['Qs_Wpax', 'X_ghpax']:
        final_schedule[variable] = final_schedule['Occ_m2pax'] * internal_loads_building[variable]

    # VENTILATION SCHEDULE
    final_schedule['Ve_lpspax'] = final_schedule['Occ_m2pax'] * indoor_comfort_building['Ve_lpspax']

    # SCHEDULE FOR WATER CONSUMPTION
    for variable in ['Vww_lpdpax', 'Vw_lpdpax']:
        if internal_loads_building[variable] > 0.0:
            array = daily_schedule_building[VARIABLE_CEA_SCHEDULE_RELATION[variable]]
            yearly_array = get_yearly_vectors(date_range,
                                              days_in_schedule,
                                              array,
                                              monthly_multiplier,
                                              normalize_first_daily_profile=True)
            if stochastic_schedule:
            #     yearly_array = calc_individual_occupant_schedule(yearly_array)
            # TODO: define how stochastic occupancy affects water schedules
            # currently MULTI_RES water schedules include water consumption at times of zero occupancy
                final_schedule[variable] = yearly_array * internal_loads_building[variable] * number_of_occupants
            else:
                final_schedule[variable] = yearly_array * internal_loads_building[variable] * number_of_occupants
        else:
            final_schedule[variable] = np.zeros(HOURS_IN_YEAR)

    # APPLIANCE ELECTRICITY SCHEDULE
    variable = 'Ea_Wm2'
    if internal_loads_building[variable] > 0.0:
        array = daily_schedule_building[VARIABLE_CEA_SCHEDULE_RELATION[variable]]
        # adjust the demand for appliances based on the number of occupants
        if stochastic_schedule:
            # base load is independent of occupants
            base_load = np.min(array)
            occupant_load = array - base_load
            # get yearly array for occupant-related loads
            yearly_array = get_yearly_vectors(date_range, days_in_schedule, occupant_load, monthly_multiplier)
            # adjust the yearly array based on the number of occupants produced by the stochastic occupancy model
            deterministic_occupancy_array = np.round(
                get_yearly_vectors(date_range, days_in_schedule, array, monthly_multiplier) * 1 /
                internal_loads_building['Occ_m2pax'] * prop_geometry_building['Aocc'])
            adjusted_array = yearly_array * final_schedule['Occ_m2pax'] / deterministic_occupancy_array
            # nan values correspond to time steps where both occupant schedules are 0
            adjusted_array[np.isnan(adjusted_array)] = 0.0
            # inf values correspond to time steps where the stochastic schedule has at least one occupant and the
            # deterministic one has none. In those cases, the peak hour is used as a reference value
            peak_hour = np.argmax(yearly_array)
            peak_load_occupancy = deterministic_occupancy_array[peak_hour]
            for t in np.where(np.isinf(adjusted_array)):
                adjusted_array[t] = final_schedule['Occ_m2pax'][t] * np.max(yearly_array) / peak_load_occupancy

            final_schedule[variable] = (adjusted_array + base_load) * internal_loads_building[variable] * \
                                       prop_geometry_building['Aef']
        else:
            yearly_array = get_yearly_vectors(date_range, days_in_schedule, array, monthly_multiplier)
            final_schedule[variable] = yearly_array * internal_loads_building[variable] * \
                                       prop_geometry_building['Aef']
    else:
        final_schedule[variable] = np.zeros(HOURS_IN_YEAR)

    # LIGHTING ELECTRICITY SCHEDULE
    variable = 'El_Wm2'
    # this schedule is assumed to be independent of occupant presence
    array = daily_schedule_building[VARIABLE_CEA_SCHEDULE_RELATION[variable]]
    yearly_array = get_yearly_vectors(date_range, days_in_schedule, array, monthly_multiplier)
    final_schedule[variable] = yearly_array * internal_loads_building[variable] * prop_geometry_building['Aef']

    # LIGHTING AND PROCESS ENERGY DEMAND SCHEDULES
    for variable in ['Ed_Wm2', 'Epro_Wm2', 'Qcre_Wm2', 'Qhpro_Wm2', 'Qcpro_Wm2']:
        # these schedules are assumed to be independent of occupant presence and have no monthly variations
        array = daily_schedule_building[VARIABLE_CEA_SCHEDULE_RELATION[variable]]
        yearly_array = get_yearly_vectors(date_range, days_in_schedule, array,
                                          monthly_multiplier=list(np.ones(MONTHS_IN_YEAR)))
        final_schedule[variable] = yearly_array * internal_loads_building[variable] * prop_geometry_building['Aef']

    # SCHEDULE FOR HEATING/COOLING SET POINT TEMPERATURES
    for variable in ['Ths_set_C', 'Tcs_set_C']:
        array = daily_schedule_building[VARIABLE_CEA_SCHEDULE_RELATION[variable]]
        array = np.vectorize(convert_schedule_string_to_temperature)(array,
                                                                     variable,
                                                                     indoor_comfort_building['Ths_set_C'],
                                                                     indoor_comfort_building['Ths_setb_C'],
                                                                     indoor_comfort_building['Tcs_set_C'],
                                                                     indoor_comfort_building['Tcs_setb_C'])
        final_schedule[variable] = get_yearly_vectors(date_range, days_in_schedule, array,
                                                      monthly_multiplier=list(np.ones(MONTHS_IN_YEAR)))

    final_dict = {
        'DATE': date_range,
        'Ths_set_C': final_schedule['Ths_set_C'],
        'Tcs_set_C': final_schedule['Tcs_set_C'],
        'people_pax': final_schedule['Occ_m2pax'],
        'Ve_lps': final_schedule['Ve_lpspax'],
        'Qs_W': final_schedule['Qs_Wpax'],
        'X_gh': final_schedule['X_ghpax'],
        'Vww_lph': final_schedule['Vww_lpdpax'],
        'Vw_lph': final_schedule['Vw_lpdpax'],
        'Ea_W': final_schedule['Ea_Wm2'],
        'El_W': final_schedule['El_Wm2'],
        'Ed_W': final_schedule['Ed_Wm2'],
        'Epro_W': final_schedule['Epro_Wm2'],
        'Qcre_W': final_schedule['Qcre_Wm2'],
        'Qhpro_W': final_schedule['Qhpro_Wm2'],
        'Qcpro_W': final_schedule['Qcpro_Wm2'],
    }

    yearly_occupancy_schedules = pd.DataFrame(final_dict)
    yearly_occupancy_schedules.to_csv(locator.get_occupancy_model_file(building), index=False, na_rep='OFF',
                                      float_format='%.3f')


def convert_schedule_string_to_temperature(schedule_string, schedule_type, Ths_set_C, Ths_setb_C, Tcs_set_C,
                                           Tcs_setb_C):
    """
    converts an archetypal temperature schedule consisting of strings to building-specific temperatures
    :param schedule_string: list of strings containing codes : 'OFF', 'SETPOINT', 'SETBACK'
    :type schedule_string: list of strings
    :param schedule_type: type of the schedule, either 'Ths_set' or 'Tcs_set'
    :type schedule_type: str
    :param bpr: BuildingPropertiesRow object, from here the setpoint and setback temperatures are extracted
    :type bpr: BuildingPropoertiesRow
    :return: an array of temperatures containing np.nan when the system is OFF
    :rtype: numpy.array
    """

    if schedule_type == 'Ths_set_C':
        if schedule_string == 'OFF':
            schedule_float = np.nan
        elif schedule_string == 'SETPOINT':
            schedule_float = float(Ths_set_C)
        elif schedule_string == 'SETBACK':
            schedule_float = float(Ths_setb_C)
        else:
            schedule_float = float(Ths_set_C)
            print('Invalid value in temperature schedule detected. Setpoint temperature assumed: {}'.format(
                schedule_float))


    elif schedule_type == 'Tcs_set_C':
        if schedule_string == 'OFF':
            schedule_float = np.nan
        elif schedule_string == 'SETPOINT':
            schedule_float = float(Tcs_set_C)
        elif schedule_string == 'SETBACK':
            schedule_float = float(Tcs_setb_C)
        else:
            schedule_float = float(Tcs_set_C)
            print('Invalid value in temperature schedule detected. Setpoint temperature assumed: {}'.format(
                schedule_float))

    return schedule_float


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

    # start empty schedules
    schedules = {}
    normalizing_values = {}
    for schedule in ['people'] + OCCUPANT_SCHEDULES + ELECTRICITY_SCHEDULES + WATER_SCHEDULES + PROCESS_SCHEDULES:
        schedules[schedule] = np.zeros(HOURS_IN_YEAR)
        normalizing_values[schedule] = 0.0

    # vector of mobility parameters
    mu_v = [0.18, 0.33, 0.54, 0.67, 0.82, 1.22, 1.50, 3.0, 5.67]
    len_mu_v = len(mu_v)

    for num in range(len(list_uses)):
        current_share_of_use = bpr.occupancy[list_uses[num]]
        current_stochastic_schedule = np.zeros(HOURS_IN_YEAR)
        if current_share_of_use > 0:
            occupants_in_current_use = int(
                archetype_values['people'][num] * current_share_of_use * bpr.rc_model['Aocc'])
            archetype_schedule = archetype_schedules[num]['people']
            for occupant in range(occupants_in_current_use):
                mu = mu_v[int(len_mu_v * random.random())]
                occupant_pattern = calc_individual_occupant_schedule(mu, archetype_schedule)
                current_stochastic_schedule += occupant_pattern
                schedules['people'] += occupant_pattern
                for label in OCCUPANT_SCHEDULES:
                    schedules[label] = np.vectorize(calc_average)(schedules[label], occupant_pattern,
                                                                  archetype_values[label][num])

            for label in OCCUPANT_SCHEDULES:
                current_archetype_values = archetype_values[label]
                if current_archetype_values[num] != 0:  # do not consider when the value is 0
                    normalizing_values[label] += current_archetype_values[num] * archetype_values['people'][num] * \
                                                 current_share_of_use / people_per_square_meter

            # for all other schedules, the database schedule is normalized by the schedule for people and then 
            # multiplied by the number of people from the stochastic calculation
            if occupants_in_current_use > 0:
                current_stochastic_schedule /= occupants_in_current_use
            unoccupied_times = np.array([i == 0 for i in archetype_schedules[num][SCHEDULE_CODE_MAP[label]]])
            normalized_schedule = make_normalized_stochastic_schedule(current_stochastic_schedule,
                                                                      archetype_schedules[num][
                                                                          SCHEDULE_CODE_MAP[label]],
                                                                      unoccupied_times)
            # since electricity demand is != 0 when the number of occupants is 0,
            # share_time_occupancy_density = 1 if there are no occupants and equal to the normalized schedule otherwise
            share_time_occupancy_density = unoccupied_times + (1 - unoccupied_times) * normalized_schedule

            # calculate remaining schedules
            for label in ELECTRICITY_SCHEDULES:
                if archetype_values[label][num] != 0:
                    normalizing_values[label], schedules[label] = calc_remaining_schedules_stochastic(
                        normalizing_values[label], archetype_values[label][num], current_share_of_use,
                        bpr.rc_model['Aef'], schedules[label], archetype_schedules[num][SCHEDULE_CODE_MAP[label]],
                        share_time_occupancy_density)
            for label in WATER_SCHEDULES:
                if archetype_values[label][num] != 0:
                    normalizing_values[label], schedules[label] = calc_remaining_schedules_stochastic(
                        normalizing_values[label], archetype_values[label][num], current_share_of_use,
                        bpr.rc_model['Aocc'], schedules[label], archetype_schedules[num][SCHEDULE_CODE_MAP[label]],
                        share_time_occupancy_density * archetype_values['people'][num])
            for label in PROCESS_SCHEDULES:
                if archetype_values[label][num] != 0:
                    normalizing_values[label], schedules[label] = calc_remaining_schedules_stochastic(
                        normalizing_values[label], archetype_values[label][num], current_share_of_use,
                        bpr.rc_model['Aef'], schedules[label], archetype_schedules[num][SCHEDULE_CODE_MAP[label]],
                        share_time_occupancy_density)

    for label in OCCUPANT_SCHEDULES + ELECTRICITY_SCHEDULES + PROCESS_SCHEDULES + WATER_SCHEDULES:
        if normalizing_values[label] == 0:
            schedules[label] = np.zeros(HOURS_IN_YEAR)
        else:
            schedules[label] /= normalizing_values[label]

    return schedules


def calc_individual_occupant_schedule(archetype_schedule):
    """
    Calculates the stochastic occupancy pattern for an individual based on Page et al. (2007).

    :param mu: parameter of mobility
    :type mu: float
    :param archetype_schedule: schedule of occupancy for the corresponding archetype
    :type archetype_schedule: list[float]

    :return pattern: yearly occupancy pattern for a given occupant in a given occupancy type
    :rtype pattern: list[int]
    """

    # get a random mobility parameter mu between 0 and 0.5
    mu = random.uniform(0, 0.5)

    # assign initial state by comparing a random number to the deterministic schedule's probability of occupant presence at t = 0
    if random.random() <= archetype_schedule[0]:
        state = 1
    else:
        state = 0

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

    return np.array(pattern)


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


def get_yearly_vectors(date_range, days_in_schedule, schedule_array, monthly_multiplier,
                       normalize_first_daily_profile=False):
    # transform into arrays
    # per weekday, saturday, sunday
    array_per_day = schedule_array.reshape(3, int(len(schedule_array) / days_in_schedule))
    array_week = array_per_day[0]
    array_sat = array_per_day[1]
    array_sun = array_per_day[2]
    if normalize_first_daily_profile:
        # for water consumption we need to normalize to the daily maximum
        # this is to account for typical units of water consumption in liters per person per day (lpd).

        if array_week.sum() != 0.0:
            norm_weekday_max = array_week.sum() ** -1
        else:
            norm_weekday_max = 0.0

        if array_sat.sum() != 0.0:
            norm_sat_max = array_sat.sum() ** -1
        else:
            norm_sat_max = 0.0

        if array_sun.sum() != 0.0:
            norm_sun_max = array_sun.sum() ** -1
        else:
            norm_sun_max = 0.0
    else:
        norm_weekday_max = 1.0
        norm_sat_max = 1.0
        norm_sun_max = 1.0

    yearly_array = [
        calc_hourly_value(date, array_week, array_sat, array_sun, norm_weekday_max, norm_sat_max, norm_sun_max,
                          monthly_multiplier) for date in date_range]

    return np.array(yearly_array)


def calc_hourly_value(date, array_week, array_sat, array_sun, norm_weekday_max, norm_sat_max, norm_sun_max,
                      monthly_multiplier):
    month_year = monthly_multiplier[date.month - 1]
    hour_day = date.hour
    dayofweek = date.dayofweek
    if 0 <= dayofweek < 5:  # weekday
        return array_week[hour_day] * month_year * norm_weekday_max  # normalized dhw demand flow rates
    elif dayofweek is 5:  # saturday
        return array_sat[hour_day] * month_year * norm_sat_max  # normalized dhw demand flow rates
    else:  # sunday
        return array_sun[hour_day] * month_year * norm_sun_max  # normalized dhw demand flow rates


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
    :rtype schedules: list[tuple]
    :return archetype_values: dict containing the values for occupant density  (in people/m2) internal loads and
        ventilation demand for each occupancy type used in the project
    :rtype archetype_values: dict[list[float]]
    """

    # read schedules of all buildings
    from cea.datamanagement.schedule_helper import ScheduleData
    schedules_DB = locator.get_building_schedules_folder()
    schedule_data_all_buildings = ScheduleData(locator, schedules_DB)

    # get yearly schedules in a list
    schedule_data_all_buildings_yearly = get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules,
                                                            pro_schedules, month_schedule,
                                                            heating_setpoint, cooling_setpoint)

    return schedule_data_all_buildings_yearly


def calc_average(last, current, share_of_use):
    """
    function to calculate the weighted average of schedules
    """
    return last + current * share_of_use


def read_schedules_from_file(schedules_csv):
    """
    A function to read building schedules from a csv file to a dict.
    :param schedules_csv: the file path to the csv file
    :type schedules_csv: os.path
    :return: building_schedules, the building schedules
    :rtype: dict
    """

    # read csv into dataframe
    df_schedules = pd.read_csv(schedules_csv)
    # convert to dataframe to dict
    building_schedules = df_schedules.to_dict(orient='list')
    # convert lists to np.arrays
    for key, value in building_schedules.items():
        try:
            building_schedules[key] = np.round(np.array(value), DECIMALS_FOR_SCHEDULE_ROUNDING)
            # round values to expected number of decimals of data created in calc_schedules()
        except TypeError:
            setpoint_array_float = np.zeros_like(np.array(value), dtype='f') + np.nan
            # go through each element
            for i in range(len(value)):
                try:
                    # try to add the temperature
                    setpoint_array_float[i] = np.round(value[i], DECIMALS_FOR_SCHEDULE_ROUNDING)
                except TypeError:
                    # if string value can not be converted to float, it is considered "OFF", "off"
                    # not necessary to do anything, because the array already contains np.nan
                    pass
            building_schedules[key] = setpoint_array_float

    return building_schedules


def save_schedules_to_file(locator, building_schedules, building_name):
    """
    A function to save schedules to csv files in the inputs/building-properties directory

    :param locator: the input locator
    :type locator: cea.inputlocator.InputLocator
    :param building_schedules: the building schedules
    :type building_schedules: dict
    :param building_name: the building name
    :type building_name: str
    :return: this function returns nothing
    """
    schedules_csv_file = locator.get_building_schedules(building_name)
    # convert to DataFrame to use pandas csv writing method
    df_building_schedules = pd.DataFrame.from_dict(building_schedules)
    df_building_schedules.to_csv(schedules_csv_file, index=False, na_rep='OFF')  # replace nan with 'OFF'
    print("Saving schedules for building {} to outputs/data/demand directory.".format(building_name))
    print("Please copy (custom) schedules to inputs/building-properties to use them in the next run.")


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    print('Running occupancy model for scenario %s' % config.scenario)
    print('Running occupancy model  with occupancy model=%s' % config.occupancy.occupancy_model)
    locator = cea.inputlocator.InputLocator(config.scenario)
    occupancy_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
