from __future__ import division

import os
import random

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.schedule_helper import read_cea_schedule
from cea.demand.building_properties import calc_useful_areas
from cea.utilities.dbf import dbf_to_dataframe
from cea.demand.constants import VARIABLE_CEA_SCHEDULE_RELATION, TEMPERATURE_VARIABLES, PEOPLE_DEPENDENT_VARIABLES,AREA_DEPENDENT_VARIABLES

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# # local constants
# DECIMALS_FOR_SCHEDULE_ROUNDING = 5
# # define schedules and codes
# OCCUPANT_SCHEDULES = ['ve', 'Qs', 'X']
# ELECTRICITY_SCHEDULES = ['Ea', 'El', 'Ed', 'Qcre']
# WATER_SCHEDULES = ['Vww', 'Vw']
# PROCESS_SCHEDULES = ['Epro', 'Qhpro', 'Qcpro']
# TEMPERATURE_SCHEDULES = ['Ths_set', 'Tcs_set']
# # map specific schedules to archetype schedules
# SCHEDULE_CODE_MAP = {'people': 'people',
#                      've': 'people',
#                      'Qs': 'people',
#                      'X': 'people',
#                      'Vww': 'hotwater',
#                      'Vw': 'hotwater',
#                      'Ea': 'appliance_light',
#                      'El': 'appliance_light',
#                      'Ed': 'appliance_light',
#                      'Qcre': 'appliance_light',
#                      'Epro': 'process',
#                      'Qhpro': 'process',
#                      'Qcpro': 'process',
#                      'Ths_set': 'heating_setpoint',
#                      'Tcs_set': 'cooling_setpoint'}

def occupancy_main(locator, config):
    # local variables
    buildings = config.occupancy.buildings
    occupancy_model = config.occupancy.occupancy_model

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
    date_range = 

    if buildings == []:
        buildings = locator.get_zone_building_names()

    for building in buildings:
        internal_loads_building = internal_loads.ix[building]
        indoor_comfort_building = indoor_comfort.ix[building]
        prop_geometry_building = prop_geometry.ix[building]
        daily_schedule_building, \
        daily_schedule_building_metadata = read_cea_schedule(locator.get_building_schedules(building))
        monthly_multiplier = daily_schedule_building_metadata['MONTHLY_MULTIPLIER']
        if occupancy_model == 'deterministic':
            calc_deterministic_schedules(locator,
                                         building,
                                         date_range,
                                         daily_schedule_building,
                                         monthly_multiplier,
                                         internal_loads_building,
                                         indoor_comfort_building,
                                         prop_geometry_building)
        elif occupancy_model == 'stochaistic':
            calc_stochastic_schedules(locator,
                                      building,
                                      daily_schedule_building,
                                      monthly_multiplier,
                                      internal_loads_building,
                                      indoor_comfort_building,
                                      prop_geometry_building)
        else:
            Exception('there is no valid input for type of occupancy model')

    # # calculate average occupant density for the building
    # people_per_square_meter = 0
    # for num in range(len(list_uses)):
    #     people_per_square_meter += bpr.occupancy[list_uses[num]] * archetype_values['people'][num]
    #
    # # no need to calculate occupancy if people_per_square_meter == 0
    # if people_per_square_meter > 0:
    #     if stochastic_occupancy:
    #         schedules = calc_stochastic_schedules(archetype_schedules, archetype_values, bpr, list_uses,
    #                                               people_per_square_meter)
    #     else:
    #         schedules = calc_deterministic_schedules(archetype_schedules, archetype_values, bpr, list_uses,
    #                                                  people_per_square_meter)
    # else:
    #     schedules = {}
    #     # occupant-related schedules are 0 since there are no occupants
    #     for schedule in ['people', 've', 'Qs', 'X', 'Vww', 'Vw']:
    #         schedules[schedule] = np.zeros(HOURS_IN_YEAR)
    #     # electricity and process schedules may be greater than 0
    #     for schedule in ['Ea', 'El', 'Qcre', 'Ed', 'Epro', 'Qhpro', 'Qcpro']:
    #         schedules[schedule] = bpr.rc_model['Aef'] * \
    #                               calc_remaining_schedules_deterministic(archetype_schedules,
    #                                                                      archetype_values[schedule], list_uses,
    #                                                                      bpr.occupancy, SCHEDULE_CODE_MAP[schedule],
    #                                                                      archetype_values['people'])
    #
    # # temperature set points are not mixed in mix-use buildings
    # for schedule_type in TEMPERATURE_SCHEDULES:
    #     # use schedule of mainuse directly
    #     schedule_string = archetype_schedules[list_uses.index(bpr.comfort['mainuse'])][SCHEDULE_CODE_MAP[schedule_type]]
    #     # convert schedule to building-specific temperatures
    #     schedules[schedule_type] = convert_schedule_string_to_temperature(schedule_string, schedule_type, bpr)
    #
    # # round schedules to avoid rounding errors when saving and reading schedules from disk
    # for schedule_type in schedules.keys():
    #     schedules[schedule_type] = np.round(schedules[schedule_type], DECIMALS_FOR_SCHEDULE_ROUNDING)


def calc_deterministic_schedules(locator,
                                 building,
                                 date_range,
                                 daily_schedule_building,
                                 monthly_multiplier,
                                 internal_loads_building,
                                 indoor_comfort_building,
                                 prop_geometry_building):

    deterministic_schedule = {}
    for variable, array in daily_schedule_building.items():
        if variable in TEMPERATURE_VARIABLES:
            yearly_array = get_yearly_vectors(date_range, variable, array, monthly_multiplier)
            deterministic_schedule[variable] = np.vectorize(convert_schedule_string_to_temperature)(yearly_array, variable, indoor_comfort_building)
        elif variable in ['Occ_m2pax']:
            deterministic_schedule[variable] = yearly_array * (1/internal_loads_building[variable]) * prop_geometry_building['Aocc']
        elif variable in ['Ve_lps', 'Qs_Wp', 'X_ghp', 'Vww_lpd', 'Vw_lpd']:
            deterministic_schedule[variable] = yearly_array * internal_loads_building[variable] * prop_geometry_building['Aocc'] * 1/internal_loads_building['Occ_m2pax']
        elif variable in ['Ea_Wm2', 'El_Wm2', 'Ed_Wm2', 'Epro_Wm2','Qcre_Wm2', 'Qhpro_Wm2', 'Qcpro_Wm2']:
            deterministic_schedule[variable] = yearly_array * internal_loads_building[variable] * prop_geometry_building['Aef']


    yearly_deterministic_schedule.to_csv(locator.get_occupancy_model_file(building))


def convert_schedule_string_to_temperature(schedule_string, schedule_type, indoor_comfort_building):
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

    schedule_float = []

    if schedule_type in ['Ths_set_C']:

        for code in schedule_string:
            if code in ['OFF']:
                schedule_float.append(np.nan)
            elif code in ['SETPOINT']:
                schedule_float.append(float(indoor_comfort_building['Ths_set_C']))
            elif code in ['SETBACK']:
                schedule_float.append(float(indoor_comfort_building['Ths_setb_C']))
            else:
                print('Invalid value in temperature schedule detected. Setpoint temperature assumed: {}'.format(code))
                schedule_float.append(float(indoor_comfort_building['Ths_set_C']))

    elif schedule_type in ['Tcs_set_C']:

        for code in schedule_string:
            if code in ['OFF']:
                schedule_float.append(np.nan)
            elif code in ['SETPOINT']:
                schedule_float.append(float(indoor_comfort_building['Tcs_set_C']))
            elif code in ['SETBACK']:
                schedule_float.append(float(indoor_comfort_building['Tcs_setb_C']))
            else:
                print('Invalid value in temperature schedule detected. Setpoint temperature assumed: {}'.format(code))
                schedule_float.append(float(indoor_comfort_building['Tcs_set_C']))

    return np.array(schedule_float)


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


def get_yearly_vectors(dates, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month_schedule,
                       heating_setpoint, cooling_setpoint):
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

    occ, el, dhw, pro, heating_setpoint_year, cooling_setpoint_year = ([] for i in range(6))

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
            heating_setpoint_year.append(heating_setpoint[0][hour_day])
            cooling_setpoint_year.append(cooling_setpoint[0][hour_day])
        elif dayofweek is 5:  # saturday
            occ.append(occ_schedules[1][hour_day] * month_year)
            el.append(el_schedules[1][hour_day] * month_year)
            dhw.append(dhw_schedules[1][hour_day] * month_year * dhw_sat_max)  # normalized dhw demand flow rates
            pro.append(pro_schedules[1][hour_day] * month_year)
            heating_setpoint_year.append(heating_setpoint[1][hour_day])
            cooling_setpoint_year.append(cooling_setpoint[1][hour_day])
        else:  # sunday
            occ.append(occ_schedules[2][hour_day] * month_year)
            el.append(el_schedules[2][hour_day] * month_year)
            dhw.append(dhw_schedules[2][hour_day] * month_year * dhw_sun_max)  # normalized dhw demand flow rates
            pro.append(pro_schedules[2][hour_day] * month_year)
            heating_setpoint_year.append(heating_setpoint[2][hour_day])
            cooling_setpoint_year.append(cooling_setpoint[2][hour_day])

    return {'people': occ, 'appliance_light': el, 'hotwater': dhw, 'process': pro,
            'heating_setpoint': heating_setpoint_year, 'cooling_setpoint': cooling_setpoint_year}


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


def get_building_schedules(locator, bpr, date_range, config):
    """
    Gets building schedules either from (user-defined) csv files or from creates them from the archetypes database.
    Schedules that are created, are saved to disc.
    This is the main function of this script.
    It includes two functions that were previously called in demand_main and in thermal_loads:
    - schedule_maker: it was reading the archetyp schedules database and other archetypal values
    - calc_schedules: it was creating schedules of mixed use buildings from the archetype schedules
    :param locator: the input locator
    :type locator: cea.inputlocator.InputLocator
    :param bpr: the building properties object
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :param date_range: the data range for the year of th calculation
    :type: pd.data_range
    :param config: the configuration
    :type config: cea.config.Configuration
    :return: building_schedules, a dict containing the building schedules in form of np.array with 8760 elements
    :rtype: dict
    """

    # get the building name
    building_name = bpr.name

    # first the script checks if pre-defined schedules for the building exist

    if os.path.isfile(locator.get_building_schedules(building_name)):
        print("Schedules for building {} detected. Using these schedules.".format(building_name))
        building_schedules = read_schedules_from_file(locator.get_building_schedules(building_name))
    else:
        print(
            "No schedules detected for building {}. Creating schedules from archetypes database".format(building_name))
        # get list of uses in building
        list_uses = [key for (key, value) in bpr.occupancy.items() if value > 0.0]
        # get occupancy schedule config
        stochastic_occupancy = config.demand.use_stochastic_occupancy
        # read archetypes database
        archetype_schedules, archetype_values = schedule_maker(date_range, locator, list_uses)
        # calculate mixed-use building schedules
        building_schedules = occupancy_main(list_uses, archetype_schedules, bpr, archetype_values, stochastic_occupancy)
        # write the building schedules to disc for the next simulation or manipulation by the user
        save_schedules_to_file(locator, building_schedules, building_name)

    return building_schedules


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    occupancy_main(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
