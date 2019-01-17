from __future__ import division
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import random
import cea.globalvar
import cea.inputlocator
import cea.config

__author__ = "Martin Mosteiro-Romero"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro-Romero"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def event_xml_reader(file, facilities_file, buildings):
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
    building_dict = {}
    events_df = pd.DataFrame(data=None, columns=['person', 'activity', 'building'])

    for event in root:
    #     if event.get('facility') in buildings:
    #         if event.get('type') == 'actstart':
    #             if not event.get('actType') in activity_types:
    #                 activity_types.append(event.get('actType'))
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
        # building_df.to_csv(r'%TEMP%'+building+'.csv')


    print len(activity_types), len(building_list), len(person_list), times, i

    return

def population_xml_reader(file):
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

def main(source):
    if source == 'events_file':
        events_file = r'C:\Users\User\Documents\MATSim\zurich_10pct\output_events.xml'
        facilities_file = r'C:\Users\User\Documents\MATSim\zurich_10pct\zurich_facilities.xml'
        buildings = ['0a1c3c9605f8e2bd8fdd2ba597d5743b15e472e3', '0a5d0f204fb373b60261da3e545fd888d4dab34c',
                     '0e7a8b818cc87f5bdd10a97b5452024bba1b189c', '1fa865a625226bfa1f19e9bd358cd059c64303f7',
                     '3831c7caa22c3c628b6b825e7e925dcae6afc881', '3f43f24455bff143a5bbe8bd82f019e08e82986b',
                     '41ea6984f7400cae78c07657e8fef47e24e31371', '490bde96dd00b6336484a212ff3e1e223dfaed1d',
                     '4aa1d11afb169725328dd0a4ffed05d0ebadf4e4', '57775d1ac68a1079c3902bc6c5695f5d71b6e2d1',
                     '599c287b0b1cef3072fb5e35cdd318416ea2ce9f', '66e4dfa31d357104d893805eae1b006786432915',
                     '719d26caadaa0c631cc7b6e8fa6087d41898a037', '8115b892c8f1bf1e998bbc5a88adf9a6ca9e1fa2',
                     '85aac55874cf5466c43b52724a89a40241935ae8', '8da861dac9ca12e0f4ceedd242992664340d205b',
                     '92da1d1df6cd3f8679d4367acb50adedf659f501', '93846f8a56d54f504c56e003e31a906b8ddb1f8a',
                     '94628003b0a5c47d45576c4f6a50ab4578289cfb', '98bd5dbdc9b545f3675ee05c66d48cd427e2f87f',
                     'a047e3acd94eb7d072eaf2fafddfd58f0f7c9af5', 'a0ef39ebb0ff574c31ed8cfdc724f5ae6a8cc075',
                     'aca1f577ef0cc9791d0abe16c2218555b1b7969b', 'acdfee6ec16450cbd91dc1f3647633e0805bfad6',
                     'aec2813e27ca9711be3ea05e3cfb4fcc85a68763', 'b6623e78ddd4247919a4035ab84bf72278b5bb53',
                     'c052f0880b1e70f890ba5e1eb5e528f096f16a2a', 'c1c38fe5615cf6c97849f26abda0343fd0e5cafa',
                     'c2a59d0662d5b8c58b0c1ee320c4f8373a854e8c', 'cbe50497dcc6556094a237b4b99d0bc51c60724c',
                     'dd41a456a90b4205afe36fedef3bb614ecffc87a', 'e85e4a51e2b2a126057ae7e495b2f933489d41a2',
                     'ea61ef88aa6b20722cce2d005b45a9dd2f35fd68', 'f0017830ee75268a88989d05ae32aa8e7a288f6c',
                     'fb6d69c0420444a09fb6d8cae2a5cdc309f10e4d', 'fe3625f82cc2355d3e32c14a0e97cdaf3f27bf05',
                     'leisure_10687', 'leisure_17285', 'leisure_18880', 'leisure_37081', 'leisure_42087',
                     'leisure_45349', 'outside_14', 'outside_4', 'outside_87', 'shop_27644', 'shop_30301', 'shop_37722',
                     'shop_49427', 'shop_52785', 'shop_67490']
        event_xml_reader(events_file, facilities_file, buildings)
    elif source == 'population_file':
        population_file = r'C:\Users\User\Documents\MATSim\ZH_Hochschulquartier\files_andreas\Share 20.11\zurich_population_cleanup.xml'
        population_xml_reader(population_file)
    else:
        print 'source file type not recognized'
    return

if __name__ == '__main__':
    main('population_file')
