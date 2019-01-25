import os
import datetime
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

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

def matsim_population_reader(file):
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

def main(file_path):
    matsim_population_reader(file_path)

if __name__ == '__main__':
    main(r'C:\Users\User\Documents\MATSim\ZH_Hochschulquartier\files_andreas\Share 20.11\zurich_population_cleanup.xml')
