from __future__ import division
from __future__ import print_function

import os

import cea.config
import cea.inputlocator
from geopandas import GeoDataFrame as Gdf
import shutil
from sets import Set


"""
A tool to create a new project / scenario with the CEA.
"""

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

COLUMNS_ZONE_GEOMETRY = ['Name', 'floors_bg', 'floors_ag',	'height_bg',	'height_ag' 'S']
COLUMNS_ZONE_AGE = ['built', 'roof',	'windows',	'partitions',	'basement',	'HVAC',	'envelope']


def new_project_creator(locator, config):

    # Local variables
    zone_geometry_path = config.new_project_scenario.zone
    terrain_path = config.new_project_scenario.terrain
    region = config.new_project_scenario.region
    occupancy_types = config.new_project_scenario.occupancy_types

    #verify files (if they have the columns cea needs) and then save to new project location
    zone = Gdf.from_file(zone_geometry_path)

    a = Set(zone.columns)
    b = Set(COLUMNS_ZONE_GEOMETRY)
    s1 = list(a.intersection(b))

    ## create occupancy file and year file
    zone[occupancy_types] = 0
    zone[occupancy_types + ['Name']].to_file(locator.get_building_occupancy())
    zone[COLUMNS_ZONE_AGE] = 0
    zone[COLUMNS_ZONE_AGE+['Name']].to_file(locator.get_building_age())


def main(config):
    # print out all configuration variables used by this script
    print("Running project creator for new project = %s" % config.new_project_scenario.project)
    print("Running project creator for new scenario = %s" % config.new_project_scenario.scenario)

    scenario = os.path.join(config.new_project_scenario.output_path, config.new_project_scenario.project,
                            config.new_project_scenario.scenario)
    locator = cea.inputlocator.InputLocator(scenario)
    new_project_creator(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
