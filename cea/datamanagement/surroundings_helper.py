
"""
This script extracts surrounding buildings of the zone geometry from Open street maps
"""

import math
import os

import numpy as np
import osmnx
import pandas as pd
from geopandas import GeoDataFrame as gdf
from geopandas.tools import sjoin as spatial_join
from shapely import MultiPolygon

import cea.config
import cea.inputlocator
from cea.datamanagement.zone_helper import parse_building_floors, clean_geometries
from cea.demand import constants
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system, \
    get_lat_lon_projected_shapefile

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def generate_empty_surroundings(crs) -> gdf:
    return gdf(columns=["name", "height_ag", "floors_ag"], geometry=[], crs=crs)


def calc_surrounding_area(zone_gdf: gdf, buffer_m: float):
    """
    Adds buffer to zone to get surroundings area

    :param geopandas.GeoDataFrame zone_gdf: Zone GeoDataFrame
    :param float buffer_m: Buffer to add to zone building geometries
    :return: Surrounding area GeoDataFrame
    """
    merged_zone = zone_gdf.geometry.union_all()
    if isinstance(merged_zone, MultiPolygon):
        merged_zone = merged_zone.convex_hull

    surrounding_area = gdf(geometry=[merged_zone.buffer(buffer_m)], crs=zone_gdf.crs)
    return surrounding_area


def get_zone_and_surr_in_projected_crs(locator):
    # generate GeoDataFrames from files
    zone_gdf = gdf.from_file(locator.get_zone_geometry())
    surroundings_gdf = gdf.from_file(locator.get_surroundings_geometry())
    # get longitude and latitude of zone centroid
    lat, lon = get_lat_lon_projected_shapefile(zone_gdf)

    # check if the coordinate reference systems (crs) of the zone and its surroundings match
    if zone_gdf.crs != surroundings_gdf.crs or zone_gdf.crs != get_projected_coordinate_system(lat=lat, lon=lon):
        # if they don't match project the zone and its surroundings to the global crs...
        zone_gdf = zone_gdf.to_crs(get_projected_coordinate_system(lat=lat, lon=lon))
        surroundings_gdf = surroundings_gdf.to_crs(get_projected_coordinate_system(lat=lat, lon=lon))
        # and save the projected GDFs to their corresponding shapefiles
        zone_gdf.to_file(locator.get_zone_geometry())
        surroundings_gdf.to_file(locator.get_surroundings_geometry())
    return zone_gdf, surroundings_gdf


def clean_attributes(shapefile, key):
    # local variables
    no_buildings = shapefile.shape[0]
    list_of_columns = shapefile.columns

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
    shapefile["floors_ag"] = [int(x) if not pd.isna(x) else data_osm_floors_joined for x in data_floors_sum_with_nan]
    shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F

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
    shapefile["name"] = [key + str(x + 1000) for x in
                         range(no_buildings)]  # start in a big number to avoid potential confusion\
    result = shapefile[
        ["name", "height_ag", "floors_ag", "description", "category", "geometry", "REFERENCE"]]

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

    within_buffer = all_surroundings.geometry.intersects(buffer_polygon)
    surroundings = all_surroundings[within_buffer]

    footprints_without_overlaps = [s_building_footprint for s_building_footprint in surroundings.geometry
                                   if not any([s_building_footprint.intersects(z_building_footprint)
                                               for z_building_footprint in zone.geometry])]
    footprints_gdf = gdf(geometry=footprints_without_overlaps, crs=surroundings.crs)
    relevant_surroundings = spatial_join(surroundings, footprints_gdf, predicate='within')

    return relevant_surroundings.copy()


def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    buffer_m = config.surroundings_helper.buffer
    shapefile_out_path = locator.get_surroundings_geometry()
    zone = gdf.from_file(locator.get_zone_geometry())

    # trnasform zone file to geographic coordinates
    lat, lon = get_lat_lon_projected_shapefile(zone)
    zone = zone.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # get a polygon of the surrounding area, and one polygon representative of the zone area
    print("Calculating surrounding area")
    area_with_buffer = calc_surrounding_area(zone, buffer_m)

    # get footprints of all the surroundings
    print("Getting building footprints")
    area_with_buffer_polygon = area_with_buffer.to_crs(get_geographic_coordinate_system()).geometry.values[0]
    all_surroundings = osmnx.features_from_polygon(polygon=area_with_buffer_polygon, tags={"building": True})
    all_surroundings = all_surroundings.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # erase overlapping area
    print("Removing unwanted buildings")
    surroundings = erase_no_surrounding_areas(all_surroundings, zone, area_with_buffer)

    if not surroundings.shape[0] > 0:
        print('No buildings were found within range based on buffer parameter.')
        # Create an empty surroundings file
        result = generate_empty_surroundings(surroundings.crs)
    else:
        # clean attributes of height, name and number of floors
        result = clean_attributes(surroundings, key="CEA")
        result = result.to_crs(get_projected_coordinate_system(float(lat), float(lon)))
        result = clean_geometries(result)

    # save to shapefile
    result.to_file(shapefile_out_path)


def main(config: cea.config.Configuration):
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
