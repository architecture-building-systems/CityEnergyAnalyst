"""
A tool to create a new project / scenario with the CEA.
"""





import os
from shutil import copyfile

from geopandas import GeoDataFrame as Gdf
from osgeo import gdal

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings, \
    verify_input_typology, verify_input_terrain, COLUMNS_ZONE_TYPOLOGY
from cea.utilities.dbf import dataframe_to_dbf, dbf_to_dataframe
from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM, raster_to_WSG_and_UTM

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_new_scenario(locator, config):
    # Local variables
    zone_geometry_path = config.create_new_scenario.zone
    surroundings_geometry_path = config.create_new_scenario.surroundings
    street_geometry_path = config.create_new_scenario.streets
    terrain_path = config.create_new_scenario.terrain
    typology_path = config.create_new_scenario.typology

    # the folders _before_ we try copying to them
    locator.ensure_parent_folder_exists(locator.get_zone_geometry())
    locator.ensure_parent_folder_exists(locator.get_terrain())
    locator.ensure_parent_folder_exists(locator.get_building_typology())
    locator.ensure_parent_folder_exists(locator.get_street_network())

    # import file
    zone, lat, lon = shapefile_to_WSG_and_UTM(zone_geometry_path)
    # verify if input file is correct for CEA, if not an exception will be released
    verify_input_geometry_zone(zone)
    zone.to_file(locator.get_zone_geometry())

    # apply coordinate system of terrain into zone and save zone to disk.
    if terrain_path == '':
        print("there is no terrain file, run pour datamanagement tools later on for this please")
    else:
        terrain = raster_to_WSG_and_UTM(terrain_path, lat, lon)
        driver = gdal.GetDriverByName('GTiff')
        verify_input_terrain(terrain)
        driver.CreateCopy(locator.get_terrain(), terrain)

    # now create the surroundings file if it does not exist
    if surroundings_geometry_path == '':
        print("there is no surroundings file, run pour datamanagement tools later on for this please")
    else:
        # import file
        surroundings, _, _ = shapefile_to_WSG_and_UTM(surroundings_geometry_path)
        # verify if input file is correct for CEA, if not an exception will be released
        verify_input_geometry_surroundings(surroundings)
        # create new file
        surroundings.to_file(locator.get_surroundings_geometry())

    # now transfer the streets
    if street_geometry_path == '':
        print("there is no streets file, run pour datamanagement tools later on for this please")
    else:
        street, _, _ = shapefile_to_WSG_and_UTM(street_geometry_path)
        street.to_file(locator.get_street_network())

    ## create occupancy file and year file
    if typology_path == '':
        print("there is no typology file, we proceed to create it based on the geometry of your zone")
        zone = Gdf.from_file(zone_geometry_path).drop('geometry', axis=1)
        zone['STANDARD'] = 'STANDARD1'
        zone['YEAR'] = 2020
        zone['1ST_USE'] = 'MULTI_RES'
        zone['1ST_USE_R'] = 1.0
        zone['2ND_USE'] = "NONE"
        zone['2ND_USE_R'] = 0.0
        zone['3RD_USE'] = "NONE"
        zone['3RD_USE_R'] = 0.0
        dataframe_to_dbf(zone[COLUMNS_ZONE_TYPOLOGY], locator.get_building_typology())
    else:
        # import file
        occupancy_file = dbf_to_dataframe(typology_path)
        occupancy_file_test = occupancy_file[COLUMNS_ZONE_TYPOLOGY]
        # verify if input file is correct for CEA, if not an exception will be released
        verify_input_typology(occupancy_file_test)
        # create new file
        copyfile(typology_path, locator.get_building_typology())

    # add other folders by calling the locator
    locator.get_input_network_folder("DH", "")
    locator.get_input_network_folder("DC", "")
    locator.get_weather_folder()


def main(config):
    # print out all configuration variables used by this script
    print("Running create-new-scenario for project = %s" % config.create_new_scenario.project)
    print("Running create-new-scenario with scenario = %s" % config.create_new_scenario.scenario)
    print("Running create-new-scenario with typology = %s" % config.create_new_scenario.typology)
    print("Running create-new-scenario with zone = %s" % config.create_new_scenario.zone)
    print("Running create-new-scenario with terrain = %s" % config.create_new_scenario.terrain)
    print("Running create-new-scenario with output-path = %s" % config.create_new_scenario.output_path)

    scenario = os.path.join(config.create_new_scenario.output_path,
                            config.create_new_scenario.project,
                            config.create_new_scenario.scenario)

    locator = cea.inputlocator.InputLocator(scenario)
    create_new_scenario(locator, config)

    print("New project/scenario created in: %s" % scenario)


if __name__ == '__main__':
    main(cea.config.Configuration())