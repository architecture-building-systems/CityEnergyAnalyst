from __future__ import division
import xml.etree.ElementTree as ET
import pandas as pd
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points
import geopandas as gpd
import numpy as np
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

events_file = r'C:\Users\User\Documents\MATSim\zurich_10pct\output_events.xml'
facilities_file = r'C:\Users\User\Documents\MATSim\zurich_10pct\zurich_facilities.xml'
zone_df = gpd.read_file(r'C:\Users\User\Documents\GitHub\cea-reference-case\reference-case-zurich\baseline\inputs\building-geometry\zone.shp')

events_tree = ET.parse(events_file)
facilities_tree = ET.parse(facilities_file)
events_root = events_tree.getroot()
facilities_root = facilities_tree.getroot()

facilities_list = []
for event in events_root:
    if event.get('type') == 'actstart' or event.get('type') == 'actend':
        if not event.get('facility') in facilities_list:
            facilities_list.append(event.get('facility'))

facilities_subset = pd.DataFrame(data=None, columns=['id', 'x', 'y'])

facilities_in = []
facilities_out = []
coordinates_list = []
i = 0
for facility in facilities_root:
    if facility.get('id') in facilities_list:
        if not facility.get('id') in facilities_in:
            facilities_in.append(facility.get('id'))
            facilities_subset.loc[i, ['id', 'x', 'y']] = [facility.get('id'), facility.get('x'), facility.get('y')]
            coordinates_list.append(Point(float(facilities_subset.loc[i, 'x']) - 2000000,
                                          float(facilities_subset.loc[i, 'y']) - 1000000))
            i += 1
    else:
        if not facility.get('id') in facilities_out:
            facilities_out.append(facility.get('id'))
coordinate_multi_point = MultiPoint(coordinates_list)
# facilities_subset.set_index('id', inplace=True).to_csv(r'C:\Users\User\Documents\MATSim\zurich_10pct\zurich_facilities.csv')

facilities_zone = pd.DataFrame(data=None, columns=['id', 'x', 'y', 'Name', 'descriptio', 'geometry'])
# i = 0
# coordinates_list = []
# for facility in facilities_subset.index:
# for i in facilities_subset.index:
#     coordinates_list.append(Point(float(facilities_subset.loc[i, 'x']) - 2000000,
#                                   float(facilities_subset.loc[i, 'y']) - 1000000))
# coordinate_multi_point = MultiPoint(coordinates_list)
# for building in zone_df.index:
#   facilities_zone.loc[i, ['Name', 'descriptio', 'geometry']] = [building, zone_df.loc[building, 'descriptio'],
#                                                               zone_df.loc[building, 'geometry']]
#   nearest_coords = nearest_points(zone_df.loc[building, 'geometry'], coordinate_multi_point)[1]
#   facilities_zone.loc[i, ['id', 'x', 'y']] = [facility, facilities_subset.loc[facility, 'x'],
#                                               facilities_subset.loc[facility, 'y']]
for j in zone_df.index:
    facilities_zone.loc[j, ['Name', 'descriptio', 'geometry']] = zone_df.loc[j, ['Name', 'descriptio', 'geometry']]
    nearest_coords = nearest_points(zone_df.loc[j, 'geometry'], coordinate_multi_point)[1]
    facility = facilities_subset.index[coordinates_list.index(nearest_coords)]
    facilities_zone.loc[j, ['id', 'x', 'y']] = facilities_subset.loc[facility, ['id','x', 'y']]

facilities_zone.set_index('Name').to_csv(r'C:\Users\User\Documents\MATSim\ZH_Hochschulquartier\HSQ_facilities.csv')