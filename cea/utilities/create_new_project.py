"""
A tool to create a new project / scenario with the CEA.
"""

from __future__ import division
from __future__ import print_function

import os

import cea.config
import cea.inputlocator
from geopandas import GeoDataFrame as Gdf
from cea.utilities.dbf import dataframe_to_dbf
import shutil


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

COLUMNS_ZONE_GEOMETRY = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
COLUMNS_ZONE_AGE = ['built', 'roof', 'windows', 'partitions', 'basement', 'HVAC', 'envelope']


def create_new_project(locator, config):

    # Local variables
    zone_geometry_path = config.create_new_project.zone
    terrain_path = config.create_new_project.terrain
    occupancy_types = config.create_new_project.occupancy_types

    #verify files (if they have the columns cea needs) and then save to new project location
    zone = Gdf.from_file(zone_geometry_path)
    try:
        zone_test = zone[COLUMNS_ZONE_GEOMETRY]
    except ValueError:
        print("one or more columns in the input file is not compatible with cea, please ensure the column"+
                        " names comply with:", COLUMNS_ZONE_GEOMETRY)
    else:
        zone.to_file(locator.get_zone_geometry())
        shutil.copy(terrain_path, locator.get_terrain())

    ## create occupancy file and year file
    zone = Gdf.from_file(zone_geometry_path).drop('geometry', axis=1)
    for field in occupancy_types:
        zone[field] = 0
    zone[occupancy_types[:2]] = 0.5 # adding 0.5 area use to the first two uses
    dataframe_to_dbf(zone[['Name'] + occupancy_types], locator.get_building_occupancy())
    for field in COLUMNS_ZONE_AGE:
        zone[field] = 0
    zone['built'] = 2017 # adding year of construction
    dataframe_to_dbf(zone[['Name'] + COLUMNS_ZONE_AGE], locator.get_building_age())

    # add other folders by calling locator
    locator.get_measurements()
    locator.get_input_network_folder("DH")
    locator.get_input_network_folder("DC")
    locator.get_weather_folder()

def main(config):
    # print out all configuration variables used by this script
    print("Running create-new-project with project = %s" % config.create_new_project.project)
    print("Running create-new-project with scenario = %s" % config.create_new_project.scenario)
    print("Running create-new-project with occupancy-types = %s" % config.create_new_project.occupancy_types)
    print("Running create-new-project with zone = %s" % config.create_new_project.zone)
    print("Running create-new-project with terrain = %s" % config.create_new_project.terrain)
    print("Running create-new-project with terrain = %s" % config.create_new_project.terrain)
    print("Running create-new-project with output-path = %s" % config.create_new_project.output_path)

    scenario = os.path.join(config.create_new_project.output_path, config.create_new_project.project,
                            config.create_new_project.scenario)

    locator = cea.inputlocator.InputLocator(scenario)
    create_new_project(locator, config)

    print("New project/scenario created in: %s" % scenario)

if __name__ == '__main__':
    main(cea.config.Configuration())
