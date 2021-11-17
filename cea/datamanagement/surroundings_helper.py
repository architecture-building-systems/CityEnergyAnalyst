"""
This script extracts surrounding buildings of the zone geometry from Open street maps
"""

import math
import os

import numpy as np
import osmnx.footprints
import pandas as pd
from geopandas import GeoDataFrame as gdf
from geopandas.tools import sjoin as spatial_join

import cea.config
import cea.inputlocator
from cea.datamanagement.zone_helper import parse_building_floors
from cea.demand import constants
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_surrounding_area(zone_gdf, buffer_m):
    """
    Adds buffer to zone to get surroundings area

    :param geopandas.GeoDataFrame zone_gdf: Zone GeoDataFrame
    :param float buffer_m: Buffer to add to zone building geometries
    :return: Surrounding area GeoDataFrame
    """
    surrounding_area = gdf(geometry=[zone_gdf.geometry.buffer(buffer_m).unary_union], crs=zone_gdf.crs)
    return surrounding_area


def clean_attributes(shapefile, buildings_height, buildings_floors, key):
    # local variables
    no_buildings = shapefile.shape[0]
    list_of_columns = shapefile.columns
    if buildings_height is None and buildings_floors is None:
        print('Warning! you have not indicated a height or number of floors above ground for the buildings, '
              'we are reverting to data stored in Open Street Maps (It might not be accurate at all),'
              'if we do not find data in OSM for a particular building, we get the median in the surroundings, '
              'if we do not get any data we assume 4 floors per building')
        # Check which attributes the OSM has, Sometimes it does not have any and indicate the data source
        if 'building:levels' not in list_of_columns:
            shapefile['building:levels'] = [3] * no_buildings
            shapefile['REFERENCE'] = "CEA - assumption"
        elif pd.isnull(shapefile['building:levels']).all():
            shapefile['building:levels'] = [3] * no_buildings
            shapefile['REFERENCE'] = "CEA - assumption"
        else:
            shapefile['REFERENCE'] = ["OSM - median" if x is np.nan else "OSM - as it is" for x in
                                      shapefile['building:levels']]
        if 'roof:levels' not in list_of_columns:
            shapefile['roof:levels'] = 0

        # get the median from the area:
        data_osm_floors1 = shapefile['building:levels'].fillna(0)
        data_osm_floors2 = shapefile['roof:levels'].fillna(0)
        data_floors_sum = [x + y for x, y in
                           zip([parse_building_floors(x) for x in data_osm_floors1],
                               [parse_building_floors(x) for x in data_osm_floors2])]
        data_floors_sum_with_nan = [np.nan if x < 1.0 else x for x in data_floors_sum]
        data_osm_floors_joined = int(
            math.ceil(np.nanmedian(data_floors_sum_with_nan)))  # median so we get close to the worse case
        shapefile["floors_ag"] = [int(x) if x is not np.nan else data_osm_floors_joined for x in
                                  data_floors_sum_with_nan]
        shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F
    else:
        shapefile['REFERENCE'] = "User - assumption"
        if buildings_height is None and buildings_floors is not None:
            shapefile["floors_ag"] = [buildings_floors] * no_buildings
            shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F
        elif buildings_height is not None and buildings_floors is None:
            shapefile["height_ag"] = [buildings_height] * no_buildings
            shapefile["floors_ag"] = [int(math.floor(x)) for x in shapefile["height_ag"] / constants.H_F]
        else:  # both are not none
            shapefile["height_ag"] = [buildings_height] * no_buildings
            shapefile["floors_ag"] = [buildings_floors] * no_buildings

    # add description
    if "description" in list_of_columns:
        shapefile["description"] = shapefile['description']
    elif 'addr:housename' in list_of_columns:
        shapefile["description"] = shapefile['addr:housename']
    elif 'amenity' in list_of_columns:
        shapefile["description"] = shapefile['amenity']
    else:
        shapefile["description"] = [np.nan] * no_buildings

    shapefile["category"] = shapefile['building']
    shapefile["Name"] = [key + str(x + 1000) for x in
                         range(no_buildings)]  # start in a big number to avoid potential confusion\
    result = shapefile[
        ["Name", "height_ag", "floors_ag", "description", "category", "geometry", "REFERENCE"]]

    result.reset_index(inplace=True, drop=True)

    return result


def erase_no_surrounding_areas(all_surroundings, zone, area_with_buffer):
    """
    Remove buildings inside zone and outside of buffer from Surroundings GeoDataFrame

    :param geopandas.GeoDataFrame all_surroundings: Surroundings GeoDataFrame
    :param geopandas.GeoDataFrame zone: Zone GeoDataFrame
    :param geopandas.GeoDataFrame area_with_buffer: Buffer area GeoDataFrame
    :return: GeoDataFrame with surrounding buildings
    """
    buffer_polygon = area_with_buffer.to_crs(zone.crs).geometry.values[0]
    zone_area = gdf(geometry=[zone.geometry.unary_union], crs=zone.crs)

    within_buffer = all_surroundings.geometry.intersects(buffer_polygon)
    surroundings = all_surroundings[within_buffer]
    rep_points = gdf(geometry=surroundings.geometry.representative_point(), crs=all_surroundings.crs)
    not_in_zone = spatial_join(rep_points, zone_area, how='left')['index_right'].isna()

    return surroundings[not_in_zone].copy()


def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    buffer_m = config.surroundings_helper.buffer
    buildings_height = config.surroundings_helper.height_ag
    buildings_floors = config.surroundings_helper.floors_ag
    shapefile_out_path = locator.get_surroundings_geometry()
    zone = gdf.from_file(locator.get_zone_geometry())

    # trnasform zone file to geographic coordinates
    zone = zone.to_crs(get_geographic_coordinate_system())
    lon = zone.geometry[0].centroid.coords.xy[0][0]
    lat = zone.geometry[0].centroid.coords.xy[1][0]
    zone = zone.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # get a polygon of the surrounding area, and one polygon representative of the zone area
    print("Calculating surrounding area")
    area_with_buffer = calc_surrounding_area(zone, buffer_m)

    # get footprints of all the surroundings
    print("Getting building footprints")
    area_with_buffer_polygon = area_with_buffer.to_crs(get_geographic_coordinate_system()).geometry.values[0]
    all_surroundings = osmnx.footprints.footprints_from_polygon(polygon=area_with_buffer_polygon)
    all_surroundings = all_surroundings.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # erase overlapping area
    print("Removing unwanted buildings")
    surroundings = erase_no_surrounding_areas(all_surroundings, zone, area_with_buffer)

    assert surroundings.shape[0] > 0, 'No buildings were found within range based on buffer parameter.'

    # clean attributes of height, name and number of floors
    result = clean_attributes(surroundings, buildings_height, buildings_floors, key="CEA")
    result = result.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # save to shapefile
    result.to_file(shapefile_out_path)


def main(config):
    """
    Create the surroundings.shp file

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    geometry_extractor_osm(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
