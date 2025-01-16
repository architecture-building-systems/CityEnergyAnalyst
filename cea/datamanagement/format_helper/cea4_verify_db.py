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
def path_to_db_file_4(scenario, item):

    if item == "CONSTRUCTION_TYPE":
        path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "CONSTRUCTION_TYPE.xlsx")
    elif item == "USE_TYPE_PROPERTIES":
        path_db_file = os.path.join(scenario, "inputs",  "database", "ARCHETYPES", "USE_TYPE.xlsx")
    elif item == "SCHEDULES":
        path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES")
    elif item == "ENVELOPE":
        path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "ENVELOPE")
    elif item == "HVAC":
        path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "HVAC")
    elif item == "SUPPLY":
        path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "SUPPLY")
    elif item == "CONVERSION":
        path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "CONVERSION")
    elif item == "DISTRIBUTION":
        path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "DISTRIBUTION")
    elif item == "FEEDSTOCKS":
        path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "FEEDSTOCKS")
    else:
        raise ValueError(f"Unknown item {item}")

    return path_db_file


