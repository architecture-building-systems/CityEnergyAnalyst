import os
import copy
from datetime import datetime
import pandas as pd
import numpy as np
import cea.config
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

student_facilities = ['SCHOOL', 'LIBRARY']
employee_facilities = ['OFFICE', 'LAB', 'HOSPITAL', 'INDUSTRIAL']

def convert_matsim_plans_to_csv(xml_filename='plans100', xml_folder=r'C:\Users\User\Downloads'):
    # create path to xml file
    path_to_xml = os.path.join(xml_folder, xml_filename+'.xml')

    # parse xml file
    tree = ET.parse(path_to_xml)
    root = tree.getroot()

    all_plans = {}
    for person in root:
        i = 0
        first_run = True
        for act in person.iter('act'):
            if first_run:
                list_columns = act.attrib.keys()
                all_plans[person.attrib['id']] = pd.DataFrame(data=None, columns=list_columns)
                first_run = False
            for key in act.attrib.keys():
                all_plans[person.attrib['id']].loc[i, key] = act.attrib[key]
            i += 1

    # create a csv file for each person's plans
    for person in all_plans.keys():
        all_plans[person].to_csv(os.path.join(r'C:\Users\User\Downloads', xml_filename, person + '_plan.csv'))

def event_xml_reader(file):
    '''
    Code to read xml event file from a transportation model and transform it into an activity model for CEA.

    :param file:
    :return:
    '''

    tree = ET.parse(file)
    root = tree.getroot()
    event_types = []
    activity_types = []
    building_list = []
    person_list = []
    times = [1000000, 0]
    i = 0
    person_dict = {}
    events_df = pd.DataFrame(data=None, columns=['person', 'activity', 'building'])

    for event in root:
        if not event.get('type') in event_types:
            event_types.append(event.get('type'))
        if event.get('type') == 'actstart':
            activity = event.get('actType').split('_')[0]
            building = event.get('facility')
            time = int(float(event.get('time')))
            person = event.get('person')
            events_df.loc[time, ['person', 'activity', 'building']] = [person, activity, building]
            if activity in activity_types:
                activity_types.append(activity)
            if not building in building_list:
                building_list.append(building)
            if not person in person_list:
                person_list.append(person)
                person_dict[event.get('person')] = pd.DataFrame(data=None, columns=['activity', 'building'])
            if time < times[0]:
                times[0] = time
            if time > times[1]:
                times[1] = time
            i += 1
            person_dict[person].loc[time, 'activity'] = activity
            person_dict[person].loc[time, 'building'] = building

    for building in building_list:
        building_df = pd.DataFrame(data=np.zeros((times[1]-times[0], len(activity_types))), columns=activity_types)
        for person in person_dict.keys():
            if building in person_dict[person]['building']:
                current_df = person_dict[person]
                for time in current_df.index():
                    building_df.loc[time, current_df.loc[time, 'activity']] += 1

    print len(activity_types), len(building_list), len(person_list), times, i

    return

def matsim_population_to_curve(file):
    '''
    Code to read xml population file from a transportation model and transform it into an activity model for CEA.

    :param file:
    :return:
    '''
    tree = ET.parse(file)
    root = tree.getroot()
    activity_types = []
    building_list = []
    user_types = {}
    length_of_day = 24 * 60
    schedules = {'employeeETHUZH': [], 'employeeUSZ': [], 'patientUSZ': [], 'student': [], 'lunch': []}
    number_of_people = 0

    for person in root:
        occupation = person.find('attributes')[6].text
        current_schedule = np.zeros(length_of_day)

        if not occupation in user_types.keys():
            user_types[occupation] = 1
        else:
            user_types[occupation] += 1
        for plan in person.find('plan'):
            for activity in plan.iter('activity'):
                activity_type = activity.get('type')
                facility = activity.get('facility')
                if not 'Home' in facility:
                    if not activity_type in activity_types:
                        activity_types.append(activity_type)
                    if not facility in building_list:
                        building_list.append(facility)
                    start_time = datetime.strptime(activity.get('start_time'), '%H:%M:%S').hour * 60 + \
                                 datetime.strptime(activity.get('start_time'), '%H:%M:%S').minute
                    if activity.get('end_time') != '24:00:00':
                        end_time = datetime.strptime(activity.get('end_time'), '%H:%M:%S').hour * 60 + \
                                   datetime.strptime(activity.get('end_time'), '%H:%M:%S').minute
                    else:
                        end_time = length_of_day

                    schedule = np.zeros(length_of_day)
                    schedule[start_time:end_time] = 1.0

                    if activity_type == 'lunch':
                        schedules['lunch'].append(schedule.tolist())
                    else:
                        current_schedule += schedule

        schedules[occupation].append(current_schedule.tolist())
        number_of_people += 1

    unique_schedules = {}
    aggregated_schedules = {}
    for key in schedules.keys():
        for schedule in schedules[key]:
            if not key in unique_schedules.keys():
                unique_schedules[key] = [schedule]
                aggregated_schedules[key] = np.array(schedule)
            else:
                if not schedule in unique_schedules[key]:
                    unique_schedules[key].append(schedule)
                aggregated_schedules[key] += np.array(schedule)

    for key in unique_schedules.keys():
        print(key, len(unique_schedules[key]), len(schedules[key]))
        plt.plot(range(length_of_day), aggregated_schedules[key])
        plt.title('MATSim schedules')
    plt.legend(aggregated_schedules.keys())
    plt.show()

    return

def matsim_population_reader(locator, building_properties):
    '''
    Code to read xml population file from a transportation model and transform it into an activity model for CEA.

    :param file:
    :return:
    '''

    floor_areas = building_properties._prop_RC_model.Af
    occupancy = building_properties._prop_occupancy
    facilities = pd.read_csv(locator.get_facilities()).set_index('id')
    tree = ET.parse(locator.get_population())
    root = tree.getroot()
    # activity_types = []
    # building_list = []
    # user_types = {}
    length_of_day = 24
    buildings = {}
    building_schedules = {'employee': [], 'student': []}
    # schedules = {'employeeETHUZH': [], 'employeeUSZ': [], 'patientUSZ': [], 'student': [], 'lunch': []}
    number_of_people = 0
    blank_schedule = np.zeros(length_of_day)

    for person in root:
        current_plan = {}
        for occupation in building_schedules.keys():
            if occupation in person.find('attributes')[6].text:
                # only add occupant types in the pre-defined building_schedules dict
                for plan in person.find('plan'):
                    for activity in plan.iter('activity'):
                        if activity.get('type') != 'lunch':
                            facility = activity.get('facility')
                            if facility in facilities.index:
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
                                    end_time = length_of_day
                                current_plan[facility][start_time+1:end_time] += 1.0
                for facility in current_plan.keys():
                    if not facility in buildings.keys():
                        buildings[facility] = copy.deepcopy(building_schedules)
                    buildings[facility][occupation].append(current_plan[facility].tolist())

    for facility in facilities.index:
        building_names = facilities.loc[facility, 'EGID'].split('_')
        if len(building_names) > 1:
            # for now, split by conditioned area
            first_student = 0
            first_employee = 0
            for i in range(len(building_names)):
                if len(buildings[facility]['employee']) > 0:
                    employees = int(len(buildings[facility]['employee']) *
                                    (floor_areas[building_names[i]] *
                                     np.sum(occupancy.loc[building_names[i], employee_facilities])) / np.sum(
                        floor_areas[building_names] *
                        np.sum(occupancy.loc[building_names, employee_facilities].transpose())))
                else:
                    employees = 0
                if len(buildings[facility]['student']) > 0:
                    students = int(len(buildings[facility]['student']) *
                                   (floor_areas[building_names[i]] *
                                    np.sum(occupancy.loc[building_names[i], student_facilities])) / np.sum(
                        floor_areas[building_names] *
                        np.sum(occupancy.loc[building_names, student_facilities].transpose())))
                else:
                    students = 0
                buildings[building_names[i]] = copy.deepcopy(building_schedules)
                buildings[building_names[i]]['employee'] = buildings[facility]['employee'][
                                                           first_employee:employees]
                buildings[building_names[i]]['student'] = buildings[facility]['student'][
                                                          first_student:students]
                first_student += students
                first_employee += employees
            buildings.pop(facility)
        else:
            buildings[building_names[0]] = buildings.pop(facility)

    return buildings

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    matsim_population_reader(locator)

if __name__ == '__main__':
    main(cea.config.Configuration())
