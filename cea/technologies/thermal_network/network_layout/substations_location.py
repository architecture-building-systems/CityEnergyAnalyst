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

from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_substation_location(input_buildings_shp, output_substations_shp, connected_buildings):

    # # get coordinate system and project to WSG 84
    poly = gdf.from_file(input_buildings_shp)
    if connected_buildings != []:
        #get only buildings
        poly = poly.loc[poly['Name'].isin(connected_buildings)]
        poly = poly.reset_index(drop=True)

    poly = poly.to_crs(get_geographic_coordinate_system())
    lon = poly.geometry[0].centroid.coords.xy[0][0]
    lat = poly.geometry[0].centroid.coords.xy[1][0]

    # get coordinate system and re project to UTM
    poly = poly.to_crs(get_projected_coordinate_system(lat, lon))

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
    calc_substation_location(input_buildings_shp, output_substations_shp)



if __name__ == '__main__':
    main(cea.config.Configuration())