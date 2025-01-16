"""
Verify the format of DB for CEA-4 model.

"""


import os
import cea.config
import time
import pandas as pd
import shutil
import geopandas as gpd



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"






## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-4
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_db_file_4(scenario, item, sheet_name=None):

    if item == "CONSTRUCTION_TYPE":
        path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "CONSTRUCTION_TYPE.csv")
    elif item == "USE_TYPE":
        path_db_file = os.path.join(scenario, "inputs",  "database", "ARCHETYPES", "USE_TYPE.csv")
    elif item == "SCHEDULES":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES")
        else:
            path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES", "{use_type}.csv".format(use_type=sheet_name))
    elif item == "ENVELOPE":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "ENVELOPE")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "ENVELOPE", "{envelope_assemblies}.csv".format(envelope_assemblies=sheet_name))
    elif item == "HVAC":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "HVAC")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "HVAC", "{hvac_assemblies}.csv".format(hvac_assemblies=sheet_name))
    elif item == "SUPPLY":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "SUPPLY")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "SUPPLY", "{supply_assemblies}.csv".format(supply_assemblies=sheet_name))
    elif item == "CONVERSION":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "CONVERSION")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "CONVERSION", "{conversion_components}.csv".format(conversion_components=sheet_name))
    elif item == "DISTRIBUTION":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "DISTRIBUTION")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "DISTRIBUTION", "{distribution_components}.csv".format(distribution_components=sheet_name))
    elif item == "FEEDSTOCKS":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "FEEDSTOCKS")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "FEEDSTOCKS", "{feedstocks_components}.csv".format(feedstocks_components=sheet_name))
    else:
        raise ValueError(f"Unknown item {item}")

    return path_db_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------


def print_verification_results_4_db(scenario_name, dict_missing):

    if all(not value for value in dict_missing.values()):
        print("✓" * 3)
        print('The Database is verified as present and compatible with the current version of CEA-4 for Scenario: {scenario}, including:'.format(scenario=scenario_name),
              )
    else:
        print("!" * 3)
        print('All or some of Database files/columns are missing or incompatible with the current version of CEA-4 for Scenario: {scenario}. '.format(scenario=scenario_name))
        print('- If you are migrating your input data from CEA-3 to CEA-4 format, set the toggle `migrate_from_cea_3` to `True` and run the script again. ')
        print('- If you manually prepared the Database, check the log for missing files and/or incompatible columns. Modify your Database accordingly.')



## --------------------------------------------------------------------------------------------------------------------
## Unique traits for the CEA-4 format
## --------------------------------------------------------------------------------------------------------------------

def cea4_verify_db(scenario, print_results=False):
    """
    Verify the database for the CEA-4 format.

    :param scenario: the scenario to verify
    :param print_results: if True, print the results
    :return: a dictionary with the missing files
    """

    #1. about zone.shp and surroundings.shp
    list_missing_attributes_zone = []
    list_missing_attributes_surroundings = []
    list_missing_files_shp_building_geometry = verify_file_exists_4(scenario, SHAPEFILES)

    return dict_missing

## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------


def main(config):
    # Start the timer
    t0 = time.perf_counter()
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    # Get the scenario name
    scenario = config.scenario
    scenario_name = os.path.basename(scenario)

    # Print: Start
    div_len = 37 - len(scenario_name)
    print('+' * 60)
    print("-" * 1 + ' Scenario: {scenario} '.format(scenario=scenario_name) + "-" * div_len)

    # Execute the verification
    dict_missing = cea4_verify_db(scenario, print_results=True)

    # Print the results
    # print_verification_results_4_db(scenario_name, dict_missing)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0

    # Print: End
    # print("-" * 1 + ' Scenario: {scenario} - end '.format(scenario=scenario_name) + "-" * 50)
    print('+' * 60)
    print('The entire process of CEA-4 format verification is now completed - time elapsed: %.2f seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())
