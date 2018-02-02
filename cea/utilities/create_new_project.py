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
from osgeo import gdal
import osr


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

# def parse_gdal_geodataframe_projection(projection_raster):
#
#     {u'lon_0': 7.43958333333, u'k_0': 1, u'ellps': u'bessel', u'y_0': 200000, u'no_defs': True, u'proj': u'somerc',
#      u'x_0': 600000, u'units': u'm', u'lat_0': 46.9524055556}
#     projection_dict ={}


    # return projection_dict
def create_new_project(locator, config):

    # Local variables
    zone_geometry_path = config.create_new_project.zone
    district_geometry_path = config.create_new_project.district
    terrain_path = config.create_new_project.terrain
    occupancy_types = config.create_new_project.occupancy_types

    #read the zone.CPG and repalce whateever is there with UTF-8, and save
    cpg_file_path = zone_geometry_path.split('.shp',1)[0]+ '.CPG'
    cpg_file = open(cpg_file_path, "w")
    cpg_file.write("ISO-8859-1")
    cpg_file.close()

    #verify files (if they have the columns cea needs) and then save to new project location
    zone = Gdf.from_file(zone_geometry_path)
    try:
        zone_test = zone[COLUMNS_ZONE_GEOMETRY]
    except ValueError:
        print("one or more columns in the input file is not compatible with cea, please ensure the column"+
                        " names comply with:", COLUMNS_ZONE_GEOMETRY)
    else:
        #apply coordinate system of terrain into zone and save zone to disk.
        raster = gdal.Open(terrain_path)
        inSRS_wkt = raster.GetProjection()
        inSRS_converter = osr.SpatialReference()
        inSRS_converter.ImportFromWkt(inSRS_wkt)  # populates the spatial ref object with our WKT SRS
        projection_raster = inSRS_converter.ExportToProj4()
        zone.crs = projection_raster
        zone.to_file(locator.get_zone_geometry())
        #copy the existing terrain and save to disc
        shutil.copy(terrain_path, locator.get_terrain())

    #now create the district file if it does not exist
    if district_geometry_path == '':
        print("there is no district file, we proceed to create it based on the geometry of your zone")
        zone.to_file(locator.get_district_geometry())
    else:
        district = Gdf.from_file(district_geometry_path)
        district.csr = projection_raster
        district.to_file(locator.get_district_geometry())

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
