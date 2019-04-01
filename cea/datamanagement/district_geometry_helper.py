"""
This script extracts surrounding buildings of the zone geometry from Open street maps
"""
from __future__ import division
from __future__ import print_function

import math
import os

import numpy as np
import osmnx as ox
import shapely.geometry as geometry
from geopandas import GeoDataFrame as Gdf
from geopandas import overlay
from scipy.spatial import Delaunay
from shapely.ops import cascaded_union, polygonize
from cea.demand import constants
import matplotlib.pyplot as plt

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def alpha_shape(points, alpha):
    """
    Compute the alpha shape (concave hull) of a set of points.

    @param points: Iterable container of points.
    @param alpha: alpha value to influence the gooeyness of the border. Smaller
                  numbers don't fall inward as much as larger numbers. Too large,
                  and you lose everything!
    """
    if len(points) < 4:
        # When you have a triangle, there is no sense in computing an alpha
        # shape.
        return geometry.MultiPoint(list(points)).convex_hull

    def add_edge(edges, edge_points, coords, i, j):
        """Add a line between the i-th and j-th points, if not in the list already"""
        if (i, j) in edges or (j, i) in edges:
            # already added
            return
        edges.add((i, j))
        edge_points.append(coords[[i, j]])

    coords = np.array([point.coords[0] for point in points])

    tri = Delaunay(coords)
    edges = set()
    edge_points = []
    # loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = coords[ia]
        pb = coords[ib]
        pc = coords[ic]

        # Lengths of sides of triangle
        a = math.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = math.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = math.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)

        # Semiperimeter of triangle
        s = (a + b + c) / 2.0

        # Area of triangle by Heron's formula
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        circum_r = a * b * c / (4.0 * area)

        # Here's the radius filter.
        # print circum_r
        if circum_r < 1.0 / alpha:
            add_edge(edges, edge_points, coords, ia, ib)
            add_edge(edges, edge_points, coords, ib, ic)
            add_edge(edges, edge_points, coords, ic, ia)

    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points


def calc_surrounding_area(zone_gdf, buffer_m):
    geometry_without_holes = zone_gdf.convex_hull
    geometry_without_holes_gdf = Gdf(geometry=geometry_without_holes.values)
    geometry_without_holes_gdf["one_class"] = "buildings"
    geometry_merged = geometry_without_holes_gdf.dissolve(by='one_class', aggfunc='sum')
    geometry_merged_final = Gdf(geometry=geometry_merged.convex_hull)
    new_buffer = Gdf(geometry=geometry_merged_final.buffer(buffer_m))
    area = overlay(geometry_merged_final, new_buffer, how='symmetric_difference')

    # THIS IS ANOTHER METHOD, NOT FUNCTIONAL THOUGH
    # from shapely.ops import Point
    # # new GeoDataFrame with same columns
    # points = []
    # # Extraction of the polygon nodes and attributes values from polys and integration into the new GeoDataFrame
    # for index, row in zone_gdf.iterrows():
    #     for j in list(row['geometry'].exterior.coords):
    #         points.append(Point(j))
    #
    # concave_hull, edge_points = alpha_shape(points, alpha=0.1)
    # simple_polygons = [x for x in concave_hull]
    # geometry_merged_final = Gdf(geometry=simple_polygons)
    # geometry_merged_final.plot()
    # plt.show()
    # new_buffer = Gdf(geometry=geometry_merged_final.buffer(buffer_m))
    # area = overlay(geometry_merged_final, new_buffer, how='symmetric_difference')
    # area.plot()

    return area


def clean_attributes(shapefile, buildings_height, buildings_floors):

    #local variables
    no_buildings = shapefile.shape[0]
    if buildings_height is None and buildings_floors is None:
        print('you have not indicated a height/numer of floors for the buildings surrounding your area of analysis, '
              'we are reverting to data stored in Open Street Maps (It might not be accurrate at all')
        data_osm_floors1 = shapefile['building:levels'].fillna(0)
        data_osm_floors2 = shapefile['roof:levels'].fillna(0)
        data_floors_sum = [x + y for x, y in zip([float(x) for x in data_osm_floors1], [float(x) for x in data_osm_floors2])]
        data_floors_sum_with_nan = [np.nan if x<=0.0 else x for x in data_floors_sum]
        data_osm_floors_joined = int(math.ceil(np.nanmedian(data_floors_sum_with_nan))) #median so we get close to the worse case
        shapefile["floors_ag"] = [int(x) if x is not np.nan else data_osm_floors_joined for x in shapefile['building:levels'].values]
        shapefile["floors_bg"] = [0]*no_buildings #no info about
        shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F
        shapefile["height_bg"] = shapefile["floors_bg"] * constants.H_F  # average height per floor in m
        shapefile["description"] = shapefile['addr:housename']
        shapefile["type"] = shapefile['building']
        shapefile["Name"] = ["CEA"+str(x+1000) for x in range(no_buildings)] #start in a big number to avoid potential confusion\
        result = shapefile[["Name", "height_ag", "floors_ag", "height_bg", "floors_bg", "description", "type", "geometry"]]
    return result

def erase_no_surrounding_areas(all_district, area_buffer):
    polygon = area_buffer.geometry[0]
    all_district.within(polygon)
    subset = all_district[all_district.within(polygon)]
    return subset



def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    buffer_m = config.district_helper.buffer
    buildings_height = config.district_helper.height_ag
    buildings_floors = config.district_helper.floors_ag
    shapefile_out_path = locator.get_district_geometry()
    zone = Gdf.from_file(locator.get_zone_geometry())

    # trnasform zone file to geographic coordinates
    zone = zone.to_crs(get_geographic_coordinate_system())
    lon = zone.geometry[0].centroid.coords.xy[0][0]
    lat = zone.geometry[0].centroid.coords.xy[1][0]
    zone = zone.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # get a polygon of the surrounding area, and one polygon representative of the zone area
    area_with_buffer = calc_surrounding_area(zone, buffer_m)
    area_with_buffer.crs = get_projected_coordinate_system(float(lat), float(lon))
    area_with_buffer = area_with_buffer.to_crs(get_geographic_coordinate_system())

    # get footprints of all the district
    all_district = ox.footprints.create_footprints_gdf(polygon=area_with_buffer['geometry'].values[0])

    # erase overlapping area
    district = erase_no_surrounding_areas(all_district, area_with_buffer)

    # clean attributes of height, name and number of floors
    result = clean_attributes(district, buildings_height, buildings_floors)
    result = result.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # save to shapefile
    result.to_file(shapefile_out_path)


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    geometry_extractor_osm(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
