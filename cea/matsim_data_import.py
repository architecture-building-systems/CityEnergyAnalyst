import os
import pandas as pd
import xml.etree.ElementTree as ET

xml_filename = 'plans100'
xml_folder = r'C:\Users\User\Downloads'
path_to_xml = os.path.join(xml_folder, xml_filename+'.xml')

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

for person in all_plans.keys():
    all_plans[person].to_csv(os.path.join(r'C:\Users\User\Downloads', xml_filename, person + '_plan.csv'))

