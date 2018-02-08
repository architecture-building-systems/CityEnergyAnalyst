"""
This script calculates the location of substations in case we do not have it.
it is estimated as the centroid of buildings.
"""


from __future__ import division
from geopandas import GeoDataFrame as gdf
import cea.globalvar
import cea.inputlocator
import cea.config
import os
import gdal
import osr
import pycrs
import fiona
import utm
from cea.utilities.standarize_coordinates import shapefile_to_WSG_and_UTM

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_substation_location(input_buildings_shp, output_substations_shp):

    # get coordinate system and project to WSG 84
    code_projection = shapefile_to_WSG_and_UTM(input_buildings_shp)

    poly = gdf.from_file(input_buildings_shp)
    poly = poly.to_crs(epsg=4326)
    lon = poly.geometry[0].centroid.coords.xy[0][0]
    lat = poly.geometry[0].centroid.coords.xy[1][0]

    # get coordinate system and re project to UTM
    utm_data = utm.from_latlon(lat, lon)
    zone = utm_data[2]
    south_or_north = utm_data[3]
    code_projection = "+proj=utm +zone=" + str(zone)+south_or_north + " +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    poly = poly.to_crs(code_projection)

    # create points
    points = poly.copy()
    points.geometry = poly['geometry'].centroid

    # saving result
    points.to_file(output_substations_shp, driver='ESRI Shapefile')


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    input_buildings_shp = locator.get_zone_geometry()
    output_substations_shp = locator.get_connection_point()
    terrain_path = locator.get_terrain()
    calc_substation_location(input_buildings_shp, output_substations_shp)



if __name__ == '__main__':
    main(cea.config.Configuration())