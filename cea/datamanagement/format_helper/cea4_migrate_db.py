"""
Mirgate the format of the DB to CEA-4 format.

"""


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


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-4
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_db_file_3(scenario, item):

    if item == "CONSTRUCTION_STANDARD":
        path_to_input_file = os.path.join(scenario, "inputs", "technology", "archetypes", "CONSTRUCTION_STANDARD.xlsx")
    elif item == "USE_TYPE_PROPERTIES":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "archetypes", "use_types", "USE_TYPE_PROPERTIES.xlsx")
    elif item == "SCHEDULE":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "archetypes", "use_types")
    elif item == "ENVELOPE":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "assemblies", "ENVELOPE.xlsx")
    elif item == "HVAC":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "assemblies", "HVAC.xlsx")
    elif item == "SUPPLY":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "assemblies", "SUPPLY.xlsx")
    elif item == "CONVERSION":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "components", "CONVERSION.xlsx")
    elif item == "DISTRIBUTION":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "components", "DISTRIBUTION.xlsx")
    elif item == "FEEDSTOCKS":
        path_to_input_file = os.path.join(scenario, "inputs",  "technology", "components", "FEEDSTOCKS.xlsx")
    else:
        raise ValueError(f"Unknown item {item}")

    return path_to_input_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------
