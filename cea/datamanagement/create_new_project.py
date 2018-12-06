"""
A tool to create a new project / scenario with the CEA.
"""

from __future__ import division
from __future__ import print_function

import os
from shutil import copyfile

from geopandas import GeoDataFrame as Gdf
from osgeo import gdal

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_district, \
    verify_input_occupancy, verify_input_age, verify_input_terrain, COLUMNS_ZONE_OCCUPANCY, COLUMNS_ZONE_AGE
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


def create_new_project(locator, config):
    # Local variables
    zone_geometry_path = config.create_new_project.zone
    district_geometry_path = config.create_new_project.district
    street_geometry_path = config.create_new_project.streets
    terrain_path = config.create_new_project.terrain
    occupancy_path = config.create_new_project.occupancy
    age_path = config.create_new_project.age

    # import file
    zone, lat, lon = shapefile_to_WSG_and_UTM(zone_geometry_path)
    # verify if input file is correct for CEA, if not an exception will be released
    verify_input_geometry_zone(zone)
    zone.to_file(locator.get_zone_geometry())


    # apply coordinate system of terrain into zone and save zone to disk.
    terrain = raster_to_WSG_and_UTM(terrain_path, lat, lon)
    driver = gdal.GetDriverByName('GTiff')
    verify_input_terrain(driver, locator.get_terrain(), terrain)
    driver.CreateCopy(locator.get_terrain(), terrain)

    # now create the district file if it does not exist
    if district_geometry_path == '':
        print("there is no district file, we proceed to create it based on the geometry of your zone")
        zone.to_file(locator.get_district_geometry())
    else:
        # import file
        district, _, _ = shapefile_to_WSG_and_UTM(district_geometry_path)
        # verify if input file is correct for CEA, if not an exception will be released
        verify_input_geometry_district(zone)
        # create new file
        district.to_file(locator.get_district_geometry())

    # now transfer the streets
    if street_geometry_path == '':
        print("there is no street file, optimizaiton of cooling networks wont be possible")
    else:
        street, _, _ = shapefile_to_WSG_and_UTM(street_geometry_path)
        street.to_file(locator.get_street_network())

    ## create occupancy file and year file
    if occupancy_path == '':
        print("there is no occupancy file, we proceed to create it based on the geometry of your zone")
        zone = Gdf.from_file(zone_geometry_path).drop('geometry', axis=1)
        for field in COLUMNS_ZONE_OCCUPANCY:
            zone[field] = 0.0
        zone[COLUMNS_ZONE_OCCUPANCY[:2]] = 0.5  # adding 0.5 area use to the first two uses
        dataframe_to_dbf(zone[['Name'] + COLUMNS_ZONE_OCCUPANCY], locator.get_building_occupancy())
    else:
        # import file
        occupancy_file = dbf_to_dataframe(occupancy_path)
        occupancy_file_test = occupancy_file[['Name'] + COLUMNS_ZONE_OCCUPANCY]
        # verify if input file is correct for CEA, if not an exception will be released
        verify_input_occupancy(occupancy_file_test)
        # create new file
        copyfile(occupancy_path, locator.get_building_occupancy())

    ## create age file
    if age_path == '':
        print(
            "there is no file with the age of the buildings, we proceed to create it based on the geometry of your zone")
        zone = Gdf.from_file(zone_geometry_path).drop('geometry', axis=1)
        for field in COLUMNS_ZONE_AGE:
            zone[field] = 0.0
        zone['built'] = 2017  # adding year of construction
        dataframe_to_dbf(zone[['Name'] + COLUMNS_ZONE_AGE], locator.get_building_age())
    else:
        # import file
        age_file = dbf_to_dataframe(age_path)
        age_file_test = age_file[['Name'] + COLUMNS_ZONE_AGE]
        # verify if input file is correct for CEA, if not an exception will be released
        verify_input_age(age_file_test)
        # create new file
        copyfile(age_path, locator.get_building_age())

    # add other folders by calling the locator
    locator.get_measurements()
    locator.get_input_network_folder("DH", "")
    locator.get_input_network_folder("DC", "")
    locator.get_weather_folder()


def main(config):
    # print out all configuration variables used by this script
    print("Running create-new-project with project = %s" % config.create_new_project.project)
    print("Running create-new-project with scenario = %s" % config.create_new_project.scenario)
    print("Running create-new-project with occupancy-types = %s" % config.create_new_project.occupancy)
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
