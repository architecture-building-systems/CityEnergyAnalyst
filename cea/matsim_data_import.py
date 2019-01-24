import os
import pandas as pd
import xml.etree.ElementTree as ET

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

def matsim_population_reader():