"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import os

from geopandas import GeoDataFrame as gdf
from geopandas import GeoSeries as gds
from shapely.ops import split, snap
from shapely.geometry import (box, LineString, MultiLineString, MultiPoint,
    Point, Polygon)
import shapely.ops


import cea.config
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Mattijn", "Johannes Dorfner"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import math



def cut_line_at_points(line, points):
    # First coords of line
    coords = list(line.coords)

    # Keep list coords where to cut (cuts = 1)
    cuts = [0] * len(coords)
    cuts[0] = 1
    cuts[-1] = 1

    # Add the coords from the points
    coords += [list(p.coords)[0] for p in points]
    cuts += [1] * len(points)

    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]

    coords = [p for (d, p) in sorted(zip(dists, coords))]
    cuts = [p for (d, p) in sorted(zip(dists, cuts))]

    # generate the Lines
    # lines = [LineString([coords[i], coords[i+1]]) for i in range(len(coords)-1)]
    lines = []

    for i in range(len(coords) - 1):
        if cuts[i] == 1:
            # find next element in cuts == 1 starting from index i + 1
            j = cuts.index(1, i + 1)
            lines.append(LineString(coords[i:j + 1]))

    return gds(lines)


def computer_end_points(lines):
    endpts = [(Point(list(line.coords)[0]), Point(list(line.coords)[-1])) for line in lines]
    # flatten the resulting list to a simple list of points
    endpts = [pt for sublist in endpts for pt in sublist]

    geometry = endpts
    df = gdf(geometry=geometry)

    return df


def compute_intersections(lines):
    import itertools
    inters = []
    for line1, line2 in itertools.combinations(lines, 2):
        if line1.intersects(line2):
            inter = line1.intersection(line2)
            if "Point" == inter.type:
                inters.append(inter)
            elif "MultiPoint" == inter.type:
                inters.extend([pt for pt in inter])
            elif "MultiLineString" == inter.type:
                multiLine = [line for line in inter]
                first_coords = multiLine[0].coords[0]
                last_coords = multiLine[len(multiLine) - 1].coords[1]
                inters.append(Point(first_coords[0], first_coords[1]))
                inters.append(Point(last_coords[0], last_coords[1]))
            elif "GeometryCollection" == inter.type:
                for geom in inter:
                    if "Point" == geom.type:
                        inters.append(geom)
                    elif "MultiPoint" == geom.type:
                        inters.extend([pt for pt in geom])
                    elif "MultiLineString" == geom.type:
                        multiLine = [line for line in geom]
                        first_coords = multiLine[0].coords[0]
                        last_coords = multiLine[len(multiLine) - 1].coords[1]
                        inters.append(Point(first_coords[0], first_coords[1]))
                        inters.append(Point(last_coords[0], last_coords[1]))
    return inters

def split_line_by_nearest_points(gdf_line, gdf_points, tolerance):
    """
    Split the union of lines with the union of points resulting
    Parameters
    ----------
    gdf_line : geoDataFrame
        geodataframe with multiple rows of connecting line segments
    gdf_points : geoDataFrame
        geodataframe with multiple rows of single points

    Returns
    -------
    gdf_segments : geoDataFrame
        geodataframe of segments
    """

    # union all geometries
    line = gdf_line.geometry.unary_union
    coords = gdf_points.geometry.unary_union

    # snap and split coords on line
    # returns GeometryCollection
    # segments = []
    snap_points = snap(coords, line, tolerance)
    # for line in gdf_line.geometry:
    #     split_line = split(line, snap_points)
    #     segments_partial = [feature for feature in split_line]
    #     segments.extend(segments_partial)


    # transform Geometry Collection to GeoDataFrame
    split_line = split(line, snap_points)
    segments = [feature for feature in split_line]

    gdf_segments = gdf(
        list(range(len(segments))), geometry=segments)
    gdf_segments.columns = ['index', 'geometry']

    return gdf_segments

def near_analysis(buiding_centroids, street_network):
    near_point = []
    building_name = []
    for point, name in zip(buiding_centroids.geometry, buiding_centroids.Name):
        distance = 10e10
        for line in street_network.geometry:
            nearest_point_candidate = line.interpolate(line.project(point))
            distance_candidate = point.distance(nearest_point_candidate)
            if distance_candidate < distance:
                distance = distance_candidate
                nearest_point = nearest_point_candidate
        building_name.append(name)
        near_point.append(nearest_point)

    geometry = near_point
    df = gdf(geometry=geometry)
    df["Name"] = building_name
    return df


def one_linestring_per_intersection(lines):
    """ Move line endpoints to intersections of line segments.

    Given a list of touching or possibly intersecting LineStrings, return a
    list LineStrings that have their endpoints at all crossings and
    intersecting points and ONLY there.

    Args:
        a list of LineStrings or a MultiLineString

    Returns:
        a list of LineStrings
    """
    lines_merged = shapely.ops.linemerge(lines)

    # intersecting multiline with its bounding box somehow triggers a first
    bounding_box = box(*lines_merged.bounds)

    # perform linemerge (one linestring between each crossing only)
    # if this fails, write function to perform this on a bbox-grid and then
    # merge the result
    lines_merged = lines_merged.intersection(bounding_box)
    lines_merged = shapely.ops.linemerge(lines_merged)
    return lines_merged


def linemerge(linestrings_or_multilinestrings):
    """ Merge list of LineStrings and/or MultiLineStrings.

    Given a list of LineStrings and possibly MultiLineStrings, merge all of
    them to a single MultiLineString.

    Args:
        list of LineStrings and/or MultiLineStrings

    Returns:
        a merged LineString or MultiLineString
    """
    lines = []
    for line in linestrings_or_multilinestrings:
        if isinstance(line, MultiLineString):
            # line is a multilinestring, so append its components
            lines.extend(line)
        else:
            # line is a line, so simply append it
            lines.append(line)

    return shapely.ops.linemerge(lines)

def calc_connectivity_network(path_streets_shp, path_connection_point_buildings_shp, path_potential_network):
    """
    This script outputs a potential network connecting a series of building points to the closest street network
    the street network is assumed to be a good path to the district heating or cooling network

    :param path_streets_shp: path to street shapefile
    :param path_connection_point_buildings_shp: path to substations in buildings (or close by)
    :param path_potential_network: output path shapefile
    :return:
    """
    # first get the building centroids and the street network
    buiding_centroids = gdf.from_file(path_connection_point_buildings_shp)
    street_network = gdf.from_file(path_streets_shp)

    # get list of nearest points
    near_points = near_analysis(buiding_centroids, street_network)

    # extend to the buiding centroids
    all_points = near_points.append(buiding_centroids)

    # Aggregate these points with the GroupBy
    lines_to_buildings = all_points.groupby(['Name'])['geometry'].apply(lambda x: LineString(x.tolist()))
    lines_to_buildings = gdf(lines_to_buildings, geometry='geometry')

    # extend to the streets
    prototype_network = lines_to_buildings.append(street_network)

    # now clean the vertices
    gdf_segments = one_linestring_per_intersection(prototype_network.geometry.unary_union)
    gdf_segments_list = [line for line in gdf_segments]
    # gdf_points = computer_end_points(prototype_network.geometry)
    # gdf_segments = split_line_by_nearest_points(prototype_network, gdf_points, tolerance=0.5)
    gds(gdf_segments_list).plot()
    import matplotlib.pyplot as plt
    # gdf_points.plot()
    plt.show()
    x=1

    gds(gdf_segments_list).to_file(path_potential_network, driver='ESRI Shapefile')


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_connection_point_buildings_shp = locator.get_temporary_file(
        "nodes_buildings.shp")  # substation, it can be the centroid of the building
    path_potential_network = locator.get_temporary_file("potential_network.shp")  # shapefile, location of output.
    calc_connectivity_network(path_streets_shp, path_connection_point_buildings_shp,
                              path_potential_network)


if __name__ == '__main__':
    main(cea.config.Configuration())
