"""
This script extracts surrounding buildings of the zone geometry from Open street maps
"""
from __future__ import division
from __future__ import print_function

import os

import osmnx as ox
from geopandas import GeoDataFrame as Gdf
from geopandas import overlay
from shapely.ops import cascaded_union, polygonize
from scipy.spatial import Delaunay
import numpy as np
import math
import fiona
import shapely.geometry as geometry

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system, get_lat_lon_projected_shapefile

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
        edges.add( (i, j) )
        edge_points.append(coords[ [i, j] ])

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
        a = math.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
        b = math.sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
        c = math.sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)

        # Semiperimeter of triangle
        s = (a + b + c)/2.0

        # Area of triangle by Heron's formula
        area = math.sqrt(s*(s-a)*(s-b)*(s-c))
        circum_r = a*b*c/(4.0*area)

        # Here's the radius filter.
        #print circum_r
        if circum_r < 1.0/alpha:
            add_edge(edges, edge_points, coords, ia, ib)
            add_edge(edges, edge_points, coords, ib, ic)
            add_edge(edges, edge_points, coords, ic, ia)

    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points


def calc_surrounding_area(zone_gdf, buffer_m):
    import matplotlib.pyplot as plt
    geometry_without_holes = zone_gdf.convex_hull
    geometry_without_holes_gdf = Gdf(geometry=geometry_without_holes.values)
    geometry_without_holes_gdf["one_class"] = "buildings"
    geometry_merged = geometry_without_holes_gdf.dissolve(by='one_class', aggfunc='sum')
    geometry_merged_final = Gdf(geometry=geometry_merged.convex_hull)
    new_buffer = Gdf(geometry=geometry_merged_final.buffer(buffer_m))
    area = overlay(geometry_merged_final, new_buffer, how='symmetric_difference')
    area.plot()
    plt.show()
    x=1

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


def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    buffer_m = 100
    shapefile_out_path = locator.get_district_geometry()
    zone = Gdf.from_file(locator.get_zone_geometry())

    #trnasform zone file to geographic coordinates
    zone = zone.to_crs(get_geographic_coordinate_system())
    lon = zone.geometry[0].centroid.coords.xy[0][0]
    lat = zone.geometry[0].centroid.coords.xy[1][0]
    zone = zone.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    #get a polygon of the surrounding area
    polygon = calc_surrounding_area(zone, buffer_m)

    #get and clean the streets
    data = ox.footprints.create_footprints_gdf(polygon=polygon)

    #project coordinate system
    data = data.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    #clean data and save to shapefile
    data.loc[:, "highway"] = [x[0] if type(x) == list else x for x in data["highway"].values]
    data.loc[:, "name"] = [x[0] if type(x) == list else x for x in data["name"].values]
    data.fillna(value="Unknown", inplace=True)
    data[['geometry', "name", "highway"]].to_file(shapefile_out_path)

    ##THIS IS ONE METHOD KEEP IT JUST IN CASE. IT IS FUNCTIONAL, BUT LESS EFECTIVE THAN THE ONE ABOVE
    # bounding_box = 'way(' + lat_min + ',' + lon_min + ',' + lat_max + ',' + lon_max + ')'
    # query = bounding_box + '["highway"];(._;>;);out body;'
    # api = overpy.Overpass()
    # # fetch all ways and nodes
    # result = api.query(query)
    # schema = {'geometry': 'LineString', 'properties': {'Name': 'str:80'}}
    # with fiona.open(shapefile_out_path, 'w', crs=crs,
    #                 driver='ESRI Shapefile', schema=schema) as output:
    #     for way in result.ways:
    #         # the shapefile geometry use (lon,lat)
    #         line = {'type': 'LineString', 'coordinates': [(node.lon, node.lat) for node in way.nodes]}
    #         prop = {'Name': way.tags.get("name", "n/a")}
    #         output.write({'geometry': line, 'properties': prop})
    # #project coordinates
    # data = Gdf.from_file(shapefile_out_path)
    # data = data.to_crs(get_projected_coordinate_system(float(lat_min), float(lon_min)))
    # data.to_file(shapefile_out_path)

    # get_projected_coordinate_system(float(lat_min), float(lon_min))


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
