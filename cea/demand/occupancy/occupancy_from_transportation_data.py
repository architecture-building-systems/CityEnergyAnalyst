from __future__ import division

import copy
import os
import xml.etree.ElementTree as ET
from datetime import datetime

import cea.globalvar
import geopandas as gpd
import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_DAY, HOURS_IN_YEAR
from cea.demand.demand_main import get_dates_from_year
from cea.demand.occupancy.occupancy_model import calc_individual_occupant_schedule, save_schedules_to_file, \
    schedule_maker, OCCUPANT_SCHEDULES, ELECTRICITY_SCHEDULES, WATER_SCHEDULES, PROCESS_SCHEDULES
from cea.utilities import epwreader
from cea.utilities.dbf import dbf_to_dataframe

__author__ = "Martin Mosteiro-Romero"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro-Romero"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

OTHER_SCHEDULES = ['Epro_Wm2', 'Ed_Wm2', 'Qcre_Wm2', 'Qhpro_Wm2']
FACILITY_TYPES = {'student': ['SCHOOL', 'UNIVERSITY'], 'employee': ['OFFICE', 'LAB', 'HOSPITAL', 'INDUSTRIAL']}


def calc_schedules_from_transportation_data(locator, dates, use_stochastic_occupancy):
    """
    Calculates the schedule for a building using MATSim data when available. When MATSim data is not available, the same
    procedure from `cea.occupancy.calc_schedules` is used.

    The schedules are normalized such that the final demands and internal gains are calculated from the specified
    building properties and not the archetype values. Depending on the value given to `stochastic_occupancy` either the
    deterministic or stochastic model of occupancy will be used.

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

    :param all_schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type all_schedules: list[ndarray[float]]

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :param archetype_values: occupant density, ventilation and internal loads for each archetypal occupancy type
    :type archetype_values: dict[str:array]

    :param use_stochastic_occupancy: a boolean that states whether the stochastic occupancy model (True) or the
        deterministic one (False) should be used
    :type use_stochastic_occupancy: Boolean

    :returns schedules: a dictionary containing the weighted average schedules for: occupancy; ventilation demand;
        sensible heat and moisture gains due to occupancy; electricity demand for appliances, lighting, processes,
        refrigeration and data centers; demand for water and domestic hot water
    :rtype: dict[array]
    """

    # get zone geometry, building properties and building occupancy for the case study
    geometry = gpd.read_file(locator.get_zone_geometry()).set_index('Name')
    building_properties = dbf_to_dataframe(locator.get_building_comfort()).merge(
        dbf_to_dataframe(locator.get_building_internal())).merge(
        dbf_to_dataframe(locator.get_building_architecture())).set_index('Name')
    building_properties.loc[geometry.index, 'GFA_m2'] = geometry.area * (geometry['floors_ag'] + geometry['floors_bg'])
    building_properties.loc[geometry.index, 'NFA_m2'] = building_properties.loc[geometry.index, 'GFA_m2'] * \
                                                        building_properties.loc[geometry.index, 'Ns']
    building_properties.loc[geometry.index, 'Aef_m2'] = building_properties.loc[geometry.index, 'GFA_m2'] * \
                                                        building_properties.loc[geometry.index, 'Es']
    occupancy = dbf_to_dataframe(locator.get_building_occupancy()).set_index('Name')
    # get occupant schedules for each facility in the transportation case study
    facility_schedules = matsim_population_reader(locator)
    # get standard schedules for all occupancy types in the case study
    archetype_schedules, archetype_values = schedule_maker(dates, locator, get_all_archetype_names(locator))

    for building in facility_schedules.keys():
        # get list of occupancy types in the building
        list_uses = [f for f in occupancy.columns if not np.isclose(occupancy.loc[building, f], 0.0)]
        # get occupant schedules for the current building
        occupant_schedules = facility_schedules[building]
        # create a DataFrame to contain all schedules to be created
        building_schedules = pd.DataFrame(data=np.zeros((HOURS_IN_YEAR, len(archetype_values.keys()))),
                                          index=range(HOURS_IN_YEAR), columns=archetype_values.keys())
        # only hospital employees are taken from transportation data, patients are defined based on schedules
        hospital_employees = 0
        # define single schedules for buildings where transportation data is available
        for user_type in FACILITY_TYPES.keys():
            if user_type in occupant_schedules.keys():
                for use in FACILITY_TYPES[user_type]:
                    if use in occupancy.columns:
                        # assign the number of occupants to a given user type (e.g. 'employee' or 'student') to each
                        # corresponding occupancy type (e.g., 'OFFICE' or 'LAB') by the floor area of each occupancy type
                        if np.sum(pd.Series(occupancy.loc[building])[FACILITY_TYPES[user_type]]) > 0:
                            share_of_current_function = occupancy.loc[building, use] / np.sum(
                                pd.Series(occupancy.loc[building])[FACILITY_TYPES[user_type]])
                            number_of_people = np.int(share_of_current_function * len(occupant_schedules[user_type]))
                            # remove current occupancy type from list of uses whose schedules need to be created from the
                            # standard values
                            if (use in list_uses) and (use != 'HOSPITAL'):
                                list_uses.remove(use)
                        else:
                            number_of_people = 0
                        # define a yearly schedule for each occupant in the transportation schedules
                        for person in range(number_of_people):
                            # schedules are drawn randomly from the pool for a given user type for the given building
                            person_schedule = occupant_schedules[user_type][np.random.randint(0, number_of_people)]
                            # hospital buildings are occupied 7 days a week, all other FACILITY_TYPES are occupied 5 days a
                            # week
                            if use != 'HOSPITAL':
                                occupant_schedule = [np.array(person_schedule),
                                                     np.zeros(HOURS_IN_DAY), np.zeros(HOURS_IN_DAY)]
                            else:
                                # while actual employees don't work 7 days a week, we assume a given employee is replaced by
                                # another equivalent employee on weekends
                                occupant_schedule = [np.array(person_schedule)] * 3
                            # create yearly schedule for current occupant
                            yearly_schedule = get_yearly_occupancy_single_person(dates, occupant_schedule,
                                                                                 archetype_schedules[use][
                                                                                     'monthly'])
                            # add occupant to building's schedule
                            building_schedules = add_occupant_schedules(building_schedules, yearly_schedule,
                                                                        archetype_values.loc[use])
                            # add schedule for electricity demand for appliances
                            building_schedules = add_appliance_schedules(building_schedules, np.array(yearly_schedule[0]),
                                                                         archetype_values.loc[use],
                                                                         archetype_schedules[use]['base_load'])
                        # lighting schedules in workplaces and school buildings are assumed not to depend on occupants
                        building_schedules = add_lighting_schedule(building_schedules,
                                                                   archetype_schedules[use]['electricity'],
                                                                   archetype_values.loc[use, 'El'],
                                                                   building_properties.loc[building, 'Aef_m2'] *
                                                                   occupancy.loc[building, use])
                        if use == 'HOSPITAL':
                            hospital_employees = number_of_people

        # make sure the number of occupants at each time step is an integer
        building_schedules['people'] = np.round(np.array(building_schedules['people']))
        # define single occupants' schedules for other uses
        for use in list_uses:
            # get number of occupants from archetype values
            occupants_in_current_use = int(building_properties.loc[building, 'NFA_m2'] * occupancy.loc[
                building, use] * archetype_values.loc[use, 'people'])
            # hospital employees have already been accounted for, remove from list of occupants to be added
            if use == 'HOSPITAL':
                occupants_in_current_use -= int(hospital_employees)

            if occupancy.loc[building, use] > 0:
                # use stochastic occupancy schedule generator
                if use_stochastic_occupancy:
                    for occupant in range(occupants_in_current_use):
                        # calculate stochastic schedule for each occupant
                        occupant_schedule = calc_individual_occupant_schedule(archetype_schedules[use]['people'])
                        water_schedule = occupant_schedule * np.array(archetype_schedules[use]['water'])
                        building_schedules = add_occupant_schedules(building_schedules,
                                                                    [occupant_schedule, water_schedule],
                                                                    archetype_values.loc[use])
                        building_schedules = add_appliance_schedules(building_schedules, occupant_schedule,
                                                                     archetype_values.loc[use],
                                                                     np.min(archetype_schedules[use]['electricity']))
                # use deterministic occupancy schedule generator
                else:
                    building_schedules = add_single_schedules(building_schedules, archetype_schedules[use],
                                                              archetype_values.loc[use], occupants_in_current_use,
                                                              building_properties.loc[building, 'Aef_m2'] *
                                                              occupancy.loc[building, use])

                # lighting schedules are assumed not to depend on occupants
                building_schedules = add_lighting_schedule(building_schedules,
                                                           archetype_schedules[use]['electricity'],
                                                           archetype_values.loc[use, 'El'],
                                                           building_properties.loc[building, 'Aef_m2'] *
                                                           occupancy.loc[building, use])

        building_schedules = calc_process_refrigeration_data(building_schedules, occupancy.loc[building],
                                                             building_properties.loc[building], archetype_schedules)

        normalizing_values = get_normalizing_values(occupancy.loc[building], archetype_values)
        for schedule in building_schedules.keys():
            building_schedules[schedule] /= normalizing_values[schedule]
        # write the building schedules to disc for the next simulation or manipulation by the user
        save_schedules_to_file(locator, building_schedules, building)

    return building_schedules


def calc_process_refrigeration_data(building_schedules, building_occupancy, building_properties, archetype_schedules):
    '''
    This function calculates the demands for processes, refrigeration and data centers for a given building.

    :param building_schedules: DataFrame with all schedules for the current building
    :param building_occupancy: Share of each occupancy type in the current building
    :param building_properties: Internal loads and indoor comfort parameters for current building
    :param archetype_schedules: Schedules for occupant presence, electricity, water and processes for current building
    :return: updated building_schedules
    '''
    # processes in industry buildings have ramp down schedules, otherwise assume constant process schedule
    if building_occupancy['INDUSTRIAL'] > 0.0:
        process_type = 'INDUSTRIAL'
    else:
        process_type = 'LAB'

    for schedule in PROCESS_SCHEDULES: #['Epro', 'Qhpro']:
        building_schedules[schedule] = np.array(archetype_schedules[process_type]['processes']) * building_properties[
            schedule + '_Wm2'] * building_properties['NFA_m2']

    # refrigeration schedule is only defined for cool room archetype
    building_schedules['Qcre'] = np.array(archetype_schedules['COOLROOM']['electricity']) * building_properties[
        'Qcre_Wm2'] * building_properties['NFA_m2']

    # data center schedule is only defined for server room archetype
    building_schedules['Ed'] = np.array(archetype_schedules['SERVERROOM']['electricity']) * building_properties[
        'Ed_Wm2'] * building_properties['NFA_m2']

    return building_schedules


def add_occupant_schedules(building_schedules, yearly_schedule, archetype_values):
    '''
    This function adds the schedule for the current occupant or for all occupants in the current occupancy type as well
    as their associated demands for water and comfort to the building schedule.

    :param building_schedules: DataFrame containing all schedules for the current building
    :param yearly_schedule: Yearly schedule for the current occupant(s)' presence and water consumption
    :param archetype_values: Indoor comfort and internal loads parameters for the current building occupancy type
    :return: updated building_schedules
    '''

    building_schedules['people'] += yearly_schedule[0]

    for schedule in OCCUPANT_SCHEDULES: # ['Qs', 'X', 've']:
        building_schedules[schedule] += np.array(yearly_schedule[0]) * archetype_values[schedule]
    for schedule in WATER_SCHEDULES: # ['Vww', 'Vw']:
        building_schedules[schedule] += np.array(yearly_schedule[1]) * archetype_values[schedule]

    return building_schedules


def add_appliance_schedules(building_schedules, occupant_schedule, archetype_values, minimum_load):
    '''
    This function creates a schedule for electrical appliances for a given user in a building. We assume archetypal
    demand for appliances can be assigned to each occupant (i.e., if a given function has an occupant density of 10 m2
    per person and appliance power of 9 W/m2, then the demand per person is 90 W).

    :param building_schedules:
    :param occupant_schedule:
    :param archetype_values:
    :param minimum_value:
    :return: updated building_schedules
    '''

    if archetype_values['people'] > 0.0:
        # calculate demand per person from the archetypal values for appliance demand and occupant density
        demand_per_person = archetype_values['Ea'] / archetype_values['people']

        # define base load as the minimum power demand in the standard appliance schedule
        base_load = np.ones(len(occupant_schedule)) * minimum_load * [occupant_schedule == 0.0]
        appliance_schedule = (occupant_schedule + base_load)[0]

        # add appliance schedule to the building schedules
        building_schedules['Ea'] += appliance_schedule * demand_per_person

    return building_schedules


def add_lighting_schedule(building_schedules, lighting_schedule, lighting_power_density, area):
    '''
    This function adds the lighting demand for a given occupancy type to the building's lighting schedule based on the
    archetypal electricity demand schedule.

    :param building_schedules: DataFrame containing all the schedules for the current building.
    :param lighting_schedule: Archetypal lighting schedule for the current occupancy type.
    :param lighting_power_density: Demand for lighting for the current occupancy type in W/m2.
    :param area: electrified area for the given building function
    :return: updated building_schedules
    '''

    building_schedules['El'] += np.array(lighting_schedule) * lighting_power_density * area

    return building_schedules

def get_normalizing_values(occupancy, archetype_values):
    '''
    The schedules produced from the MATSim population are based on the CEA archetype database, meaning user-provided
    building properties such as the actual lighting power density for the whole building (W/m2) are not taken into
    account.

    In order to make sure user-supplied parameters are used in the simulation, all schedules are normalized by the
    corresponding archetypal value for each property and are later multiplied by the user-supplied value later in the
    demand model.

    So for example if the schedules generated here predict a lighting power of 1 W, this lighting power is then
    normalized by the archetypal power density for the building (equal to sum(Ea,i * occupancy_i) for occupancy types i)
    such that in the demand model the schedule is then multiplied by the user-provided W/m2 for the entire building.

    :param occupancy:
    :param archetype_values:
    :param building_properties:
    :return:
    '''
    normalizing_values = pd.Series(data=1.0, index=archetype_values.columns)
    for schedule in OCCUPANT_SCHEDULES + WATER_SCHEDULES:
        normalizing_values[schedule] = np.sum(
            occupancy.loc[archetype_values.index] * archetype_values['people'] * archetype_values[schedule]) / np.sum(
            occupancy.loc[archetype_values.index] * archetype_values['people'])
    for schedule in ELECTRICITY_SCHEDULES + PROCESS_SCHEDULES:
        normalizing_values[schedule] = np.sum(occupancy.loc[archetype_values.index] * archetype_values[schedule])

    return normalizing_values

def add_single_schedules(building_schedules, yearly_schedule, archetype_values, number_of_occupants, electrified_area):
    '''
    This function adds a single occupancy type's schedules to the building schedules.

    :param building_schedules: DataFrame containing the current building's schedules.
    :param yearly_schedule: dict containing the current function's schedules to be added to the building's schedules.
    :param archetype_values: DataFrame containing the archetypal internal loads and indoor comfort parameters.
    :param occupied_area: net floor area in the current building (NFA)
    :param electrified_area: electrified area in the current building (Aef)
    :return: updated building_schedules
    '''
    # make sure the number of occupants at each time step is an integer
    occupant_schedule = np.round(np.array(yearly_schedule['people']) * number_of_occupants)

    # add number of occupants in current use to the building schedule
    building_schedules['people'] += occupant_schedule

    # add schedules that depend only on the number of people
    for schedule in OCCUPANT_SCHEDULES: #['Qs', 'X', 've']:
        building_schedules[schedule] += occupant_schedule * archetype_values[schedule]

    # add electricity schedules
    for schedule in ['Ea', 'El']:
        building_schedules[schedule] += np.array(yearly_schedule['electricity']) * archetype_values[
            schedule] * electrified_area

    # add domestic hot water schedules
    for schedule in WATER_SCHEDULES: # ['Vww', 'Vw']:
        building_schedules[schedule] += np.array(yearly_schedule['water']) * archetype_values[schedule] * (
            number_of_occupants)

    return building_schedules


def get_yearly_occupancy(dates, daily_schedules, month_schedule):
    occ, dhw = ([] for i in range(2))

    if daily_schedules[0].sum() != 0:
        dhw_weekday_max = daily_schedules[0].sum() ** -1
    else:
        dhw_weekday_max = 0

    if daily_schedules[1].sum() != 0:
        dhw_sat_max = daily_schedules[1].sum() ** -1
    else:
        dhw_sat_max = 0

    if daily_schedules[2].sum() != 0:
        dhw_sun_max = daily_schedules[2].sum() ** -1
    else:
        dhw_sun_max = 0

    for date in dates:
        month_year = month_schedule[date.month - 1]
        hour_day = date.hour
        dayofweek = date.dayofweek
        if 0 <= dayofweek < 5:  # weekday
            occ.append(daily_schedules[0][hour_day] * month_year)
            dhw.append(daily_schedules[0][hour_day] * month_year * dhw_weekday_max)  # normalized dhw demand flow rates
        elif dayofweek is 5:  # saturday
            occ.append(daily_schedules[1][hour_day] * month_year)
            dhw.append(daily_schedules[1][hour_day] * month_year * dhw_sat_max)  # normalized dhw demand flow rates
        else:  # sunday
            occ.append(daily_schedules[2][hour_day] * month_year)
            dhw.append(daily_schedules[2][hour_day] * month_year * dhw_sun_max)  # normalized dhw demand flow rates

    return occ, dhw


def get_yearly_occupancy_single_person(dates, daily_schedules, month_schedule):
    '''
    This function creates a yearly occupancy schedule for a single building occupant. Vacation weeks are assigned by a
    random draw at the beginning of each week. Short-term absences (single day) are not considered.

    The probability of domestic hot water consumption at each hour of the day is assumed to be the same as the occupant
    presence (as done in the archetypal schedules).

    :param dates: datetime for the year in consideration
    :param daily_schedules: daily schedule for the occupant in question
    :param month_schedule: monthly schedule for the given function based on standard values
    :return occ, dhw: occupant and domestic hot water schedule for the current occupant
    '''
    occ, dhw = ([] for i in range(2))

    if daily_schedules[0].sum() != 0:
        dhw_weekday_max = daily_schedules[0].sum() ** -1
    else:
        dhw_weekday_max = 0

    if daily_schedules[1].sum() != 0:
        dhw_sat_max = daily_schedules[1].sum() ** -1
    else:
        dhw_sat_max = 0

    if daily_schedules[2].sum() != 0:
        dhw_sun_max = daily_schedules[2].sum() ** -1
    else:
        dhw_sun_max = 0

    long_absence = False
    absences = []
    for date in dates:
        month_year = month_schedule[date.month - 1]
        hour_day = date.hour
        dayofweek = date.dayofweek
        if date.dayofweek == 1 and date.hour == 0:
            if np.random.random() < (1 - month_year):
                long_absence = True
                absences.append(date)
            else:
                long_absence = False
        if not long_absence:
            if 0 <= dayofweek < 5:  # weekday
                occ.append(daily_schedules[0][hour_day])
                dhw.append(
                    daily_schedules[0][hour_day] * dhw_weekday_max)  # normalized dhw demand flow rates
            elif dayofweek is 5:  # saturday
                occ.append(daily_schedules[1][hour_day])
                dhw.append(
                    daily_schedules[1][hour_day] * dhw_sat_max)  # normalized dhw demand flow rates
            else:  # sunday
                occ.append(daily_schedules[2][hour_day])
                dhw.append(
                    daily_schedules[2][hour_day] * dhw_sun_max)  # normalized dhw demand flow rates
        else:  # long absence
            occ.append(0.0)
            dhw.append(0.0)  # normalized dhw demand flow rates

    return occ, dhw

def get_all_archetype_names(locator):
    '''
    This function gets the names of all occupancy types according to the archetype database.

    :param locator: InputLocator instance
    :return: [str]
    '''
    archetypes_internal_loads = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS')

    return list(archetypes_internal_loads['Code'])

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


def matsim_population_reader(locator):
    '''
    Code to read xml population file from a MATSim transportation model and transform it into an occupant schedule for
    CEA.

    :param locator: InputLocator instance
    :return:
    '''

    # get building properties
    geometry_df = gpd.read_file(locator.get_zone_geometry()).set_index('Name')
    architecture_df = dbf_to_dataframe(locator.get_building_architecture()).set_index('Name')
    floor_areas = geometry_df.area * geometry_df['floors_ag'] * architecture_df['Hs']
    occupancy = dbf_to_dataframe(locator.get_building_occupancy()).set_index('Name')

    # get facilities and their corresponding names in the current case study
    facilities = get_facility_ids(locator)

    # create empty dicts and blank schedule
    buildings = {}
    building_schedules = {'employee': [], 'student': []}
    blank_schedule = np.zeros(HOURS_IN_DAY)

    # parse population file
    tree = ET.parse(locator.get_population())
    root = tree.getroot()

    # get each person's plans
    for person in root:
        current_plan = {}
        for occupation in building_schedules.keys():
            if occupation in person.find('attributes')[6].text:
                # only add occupant types in the pre-defined building_schedules dict
                for plan in person.find('plan'):
                    for activity in plan.iter('activity'):
                        if activity.get('type') != 'lunch':
                            facility = activity.get('facility')
                            if facility in facilities.keys():
                                # only consider facilities in the facility catalogue
                                if not facility in current_plan.keys():
                                    current_plan[facility] = blank_schedule.copy()
                                # define individual occupant's schedule in this particular facility
                                start_time = datetime.strptime(activity.get('start_time'), '%H:%M:%S').hour
                                current_plan[facility][start_time] += 1 - (datetime.strptime(activity.get('start_time'),
                                                                                             '%H:%M:%S').minute) / 60
                                if activity.get('end_time') != '24:00:00':
                                    end_time = datetime.strptime(activity.get('end_time'), '%H:%M:%S').hour
                                    current_plan[facility][end_time] += datetime.strptime(activity.get('end_time'),
                                                                                          '%H:%M:%S').minute / 60
                                else:
                                    end_time = HOURS_IN_DAY
                                current_plan[facility][start_time + 1:end_time] += 1.0
                for facility in current_plan.keys():
                    if not facility in buildings.keys():
                        buildings[facility] = copy.deepcopy(building_schedules)
                    buildings[facility][occupation].append(current_plan[facility].tolist())

    for facility in buildings.keys(): # facilities.keys():
        building_names = facilities[facility]
        if len(building_names) > 0:
            first_student = 0
            first_employee = 0
            for i in range(len(building_names)):
                if (len(buildings[facility]['employee']) > 0) and (np.sum(floor_areas[building_names] * np.sum(
                        occupancy.loc[building_names, FACILITY_TYPES['employee']].transpose())) > 0.0):
                    # for now distribute only by conditioned area
                    employees = int(len(buildings[facility]['employee']) *
                                    (floor_areas[building_names[i]] *
                                     np.sum(occupancy.loc[building_names[i], FACILITY_TYPES['employee']])) / np.sum(
                        floor_areas[building_names] *
                        np.sum(occupancy.loc[building_names, FACILITY_TYPES['employee']].transpose())))
                else:
                    employees = 0
                if len(buildings[facility]['student']) > 0:
                    students = int(len(buildings[facility]['student']) * (floor_areas[building_names[i]] * np.sum(
                        occupancy.loc[building_names[i], FACILITY_TYPES['student']])) / np.sum(
                        floor_areas[building_names] * np.sum(
                            occupancy.loc[building_names, FACILITY_TYPES['student']].transpose())))
                else:
                    students = 0
                buildings[building_names[i]] = copy.deepcopy(building_schedules)
                for j in range(employees):
                    k = np.random.randint(len(buildings[facility]['employee']))
                    buildings[building_names[i]]['employee'].append(buildings[facility]['employee'][k])
                for j in range(students):
                    k = np.random.randint(len(buildings[facility]['student']))
                    buildings[building_names[i]]['student'].append(buildings[facility]['student'][k])

                first_student += students
                first_employee += employees
            buildings.pop(facility)
        else:
            buildings.pop(facility)

    return buildings


def get_facility_ids(locator):
    '''
    This function imports a csv file containing the list of building names from the CEA case study along with their
    corresponding MATSim facility id's from the MATSim case study and returns a dict containing the MATSim id's as
    keys along with a list of building corresponding to each facility. This makes it possible to have multiple buildings
    identified by a single MATSim location id (useful for buildings that are clustered in transportation studies), but
    not to have multiple MATSim locations assigned to a single building (which is rather atypical).

    :param locator: InputLocator instance
    :return facilities:
    '''

    buildings = pd.read_csv(locator.get_facilities()).set_index('Name')

    facilities = {}

    for building_name in buildings.index:
        facility = buildings.loc[building_name, 'id']
        if facility not in facilities.keys():
            facilities[facility] = [building_name]
        else:
            facilities[facility].append(building_name)

    return facilities


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    # TODO: figure out weather file issue
    weather_data = epwreader.epw_reader(os.path.join(locator.get_weather_folder(), 'weather.epw'))[
        ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]
    dates = get_dates_from_year(weather_data['year'][0])
    use_stochastic_occupancy = config.demand.use_stochastic_occupancy

    return calc_schedules_from_transportation_data(locator, dates, use_stochastic_occupancy)


if __name__ == '__main__':
    main(cea.config.Configuration())
