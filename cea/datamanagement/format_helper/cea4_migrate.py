"""
Mirgate the format of the input data to CEA-4 format after verification.

"""

import cea.inputlocator
import os
import cea.config
import time
import pandas as pd
import geopandas as gpd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_verify import cea4_verify, verify_shp, verify_file_exists, verify_csv
from cea.utilities.dbf import dbf_to_dataframe


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-3
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_input_file_without_db_3(scenario, item):

    if item == "zone":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "zone.shp")
    elif item == "surroundings":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "surroundings.shp")
    elif item == "air_conditioning":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "air_conditioning.dbf")
    elif item == "architecture":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "architecture.dbf")
    elif item == "indoor_comfort":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "indoor_comfort.dbf")
    elif item == "internal_loads":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "internal_loads.dbf")
    elif item == "supply_systems":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply_systems.dbf")
    elif item == "typology":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "typology.dbf")
    elif item == 'streets':
        path_to_input_file = os.path.join(scenario, "inputs", "networks", "streets.shp")
    elif item == 'terrain':
        path_to_input_file = os.path.join(scenario, "inputs", "topography", "terrain.tif")
    elif item == 'weather':
        path_to_input_file = os.path.join(scenario, "inputs", "weather", "weather.epw")

    return path_to_input_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------


## --------------------------------------------------------------------------------------------------------------------
## Migrate to CEA-4 format from CEA-3 format
## --------------------------------------------------------------------------------------------------------------------

def migrate_cea3_to_cea4(scenario):

    # Create the list of items that has been changed from CEA-3 to CEA-4
    list_items_changed = ['zone', 'surroundings',
                          'air_conditioning', 'architecture', 'indoor_comfort', 'internal_loads', 'supply_systems',
                          'typology']
    dict_missing = cea4_verify(scenario)

    #0. get the scenario name
    scenario_name = os.path.basename(scenario)

    #1. about zone.shp and surroundings.shp
    COLUMNS_ZONE_3 = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
    COLUMNS_TYPOLOGY_3 = ['Name', 'YEAR', 'STANDARD', '1ST_USE', '1ST_USE_R', '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R']
    COLUMNS_SURROUNDINGS_3 = ['Name', 'height_ag', 'floors_ag']
    columns_mapping_dict_name = {'Name': 'name'}
    columns_mapping_dict_typology = {'YEAR': 'year',
                                     'STANDARD': 'const_type',
                                     '1ST_USE': 'use_type1',
                                     '1ST_USE_R': 'use_type1r',
                                     '2ND_USE': 'use_type2',
                                     '2ND_USE_R': 'use_type2r',
                                     '3RD_USE': 'use_type3',
                                     '3RD_USE_R': 'use_type3r'
                                     }

    list_missing_files_shp_building_geometry = dict_missing.get('building-geometry')
    list_missing_files_typology = verify_file_exists(scenario, ['typology'])
    list_missing_attributes_zone_4 = dict_missing.get('zone')

    if 'zone' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_zone_3 = verify_shp(scenario, 'zone', COLUMNS_ZONE_3)
        if not list_missing_attributes_zone_3 and list_missing_attributes_zone_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows the CEA-3 format.')
            zone_df = gpd.read_file(path_to_input_file_without_db_3(scenario, 'zone'))
            zone_df.rename(columns=columns_mapping_dict_name, inplace=True)
            if 'typology' not in list_missing_files_typology:
                list_missing_attributes_typology_3 = verify_csv(scenario, 'typology', COLUMNS_TYPOLOGY_3)
                if not list_missing_attributes_typology_3 and list_missing_attributes_zone_4:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'typology.shp follows the CEA-3 format.')
                    typology_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'typology'))
                    zone_df_4 = pd.merge(zone_df, typology_df, left_on=['name'], right_on=["Name"], how='left')
                    zone_df_4.drop(columns=['Name'], inplace=True)
                    typology_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                else:
                    raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'typology.shp does not follow the CEA-3 format. CEA cannot proceed with migration.')
        elif list_missing_attributes_zone_3 and not list_missing_attributes_zone_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows the CEA-4 format.')
        else:
            raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with migration.')
