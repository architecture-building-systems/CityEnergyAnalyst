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
    # zone_geometry_path = config.create_new_scenario.zone
    surroundings_geometry_path = config.create_new_scenario.surroundings
    # street_geometry_path = config.create_new_scenario.streets
    # terrain_path = config.create_new_scenario.terrain
    # typology_path = config.create_new_scenario.typology

    # the folders _before_ we try copying to them
    locator.ensure_parent_folder_exists(locator.get_zone_geometry())
    locator.ensure_parent_folder_exists(locator.get_terrain())
    locator.ensure_parent_folder_exists(locator.get_building_typology())
    locator.ensure_parent_folder_exists(locator.get_street_network())

    # # import zone.shp
    # if zone_geometry_path == '':
    #     print("No zone.shp file imported. This is the CEA minimum input. Ensure zone.shp under >inputs>building-geometry before executing simulations.")
    # else:
    #     zone, lat, lon = shapefile_to_WSG_and_UTM(zone_geometry_path)
    #     # verify if input file is correct for CEA, if not an exception will be released
    #     verify_input_geometry_zone(zone)
    #     zone.to_file(locator.get_zone_geometry())
    #
    # # import terrain.tif
    # if terrain_path == '':
    #     print("No terrain.tif file imported. Execute Terrain-helper later.")
    # else:
    #     terrain = raster_to_WSG_and_UTM(terrain_path, lat, lon)
    #     driver = gdal.GetDriverByName('GTiff')
    #     verify_input_terrain(terrain)
    #     driver.CreateCopy(locator.get_terrain(), terrain)

    # import surroundings.shp
    if surroundings_geometry_path == '':
        print("No surroundings.shp file imported. Execute Surroundings-helper later.")
    else:
        # import file
        surroundings, _, _ = shapefile_to_WSG_and_UTM(surroundings_geometry_path)
        # verify if input file is correct for CEA, if not an exception will be released
        verify_input_geometry_surroundings(surroundings)
        # create new file
        surroundings.to_file(locator.get_surroundings_geometry())

    # # import streets.shp
    # if street_geometry_path == '':
    #     print("No streets.shp file imported. Execute Streets-helper later.")
    # else:
    #     street, _, _ = shapefile_to_WSG_and_UTM(street_geometry_path)
    #     street.to_file(locator.get_street_network())
    #
    # # import typology.dbf
    # if typology_path == '':
    #     print("No typology.dbf file imported. This is the CEA minimum input. Ensure typology.dbf under >inputs>building-properties before executing simulations.")
    #     # zone = Gdf.from_file(zone_geometry_path).drop('geometry', axis=1)
    #     # zone['STANDARD'] = 'STANDARD1'
    #     # zone['YEAR'] = 2020
    #     # zone['1ST_USE'] = 'MULTI_RES'
    #     # zone['1ST_USE_R'] = 1.0
    #     # zone['2ND_USE'] = "NONE"
    #     # zone['2ND_USE_R'] = 0.0
    #     # zone['3RD_USE'] = "NONE"
    #     # zone['3RD_USE_R'] = 0.0
    #     # dataframe_to_dbf(zone[COLUMNS_ZONE_TYPOLOGY], locator.get_building_typology())
    # else:
    #     # import file
    #     occupancy_file = dbf_to_dataframe(typology_path)
    #     occupancy_file_test = occupancy_file[COLUMNS_ZONE_TYPOLOGY]
    #     # verify if input file is correct for CEA, if not an exception will be released
    #     verify_input_typology(occupancy_file_test)
    #     # create new file
    #     copyfile(typology_path, locator.get_building_typology())

    # add other folders by calling the locator
    locator.get_input_network_folder("DH", "")
    locator.get_input_network_folder("DC", "")
    locator.get_weather_folder()


def main(config):
    # print out all configuration variables used by this script
    print("Running create-new-scenario for project = %s" % config.create_new_scenario.project_name)
    print("Running create-new-scenario with output-path = %s" % config.create_new_scenario.output_path)

    scenario_name = config.create_new_scenario.scenario_name
    if not scenario_name:
        print("New project created in: %s" % config.create_new_scenario.output_path)
        print("No scenario has been created under this project, as no user defined scenario-name has been received.")

    else:
        scenario = os.path.join(config.create_new_scenario.output_path,
                                config.create_new_scenario.project_name,
                                config.create_new_scenario.scenario_name)

        locator = cea.inputlocator.InputLocator(scenario)
        create_new_scenario(locator, config)

        print("New project and scenario created in: %s" % scenario)

if __name__ == '__main__':
    main(cea.config.Configuration())
