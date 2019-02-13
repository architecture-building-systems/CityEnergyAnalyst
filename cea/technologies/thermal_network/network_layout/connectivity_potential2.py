"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import os

import pandas as pd
from geopandas import GeoDataFrame as gdf
from shapely.geometry import Point, LineString, box, MultiLineString
from shapely.ops import split, snap, linemerge


import cea.config
import cea.globalvar
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Malcolm Kesson", "Mattijn"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def compute_intersections(lines, crs):
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

    geometry = inters
    df = gdf(geometry=geometry, crs=crs)
    return df


def computer_end_points(lines, crs):
    endpts = [(Point(list(line.coords)[0]), Point(list(line.coords)[-1])) for line in lines]
    # flatten the resulting list to a simple list of points
    endpts = [pt for sublist in endpts for pt in sublist]

    geometry = endpts
    df = gdf(geometry=geometry, crs=crs)

    return df

def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    # This is taken from shapely manual
    if distance <= 0.0 or distance >= line.length:
        return [None, LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            result = [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
            return result
        if pd > distance:
            cp = line.interpolate(distance)
            result = [LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]
            return result


def split_line_with_points(line, points):
    """Splits a line string in several segments considering a list of points.

    The points used to cut the line are assumed to be in the line string
    and given in the order of appearance they have in the line string.

    ['LINESTRING (1 2, 8 7, 4 5, 2 4)', 'LINESTRING (2 4, 4 7, 8 5, 9 18)', 'LINESTRING (9 18, 1 2, 12 7, 4 5, 6 5)', 'LINESTRING (6 5, 4 9)']

    """
    segments = []
    current_line = line
    for p in points:
        d = current_line.project(p)
        seg, current_line = cut(current_line, d)
        if seg is not None:
            segments.append(seg)
    segments.append(current_line)
    return segments

def split_line_by_nearest_points(gdf_line, gdf_points, tolerance, crs):
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
    line = gdf_line.unary_union
    line._crs = crs
    snap_points = gdf_points.unary_union
    snap_points._crs = crs

    # snap and split coords on line
    # returns GeometryCollection
    # snap_points = snap(coords, line, tolerance)
    # snap_points._crs = crs
    one_iter_segments = []
    for l in gdf_line.geometry:
        one_iter_segments.extend(split_line_with_points(l, gdf_points.geometry))

    segments = []
    for l in one_iter_segments:
        segments.extend(split_line_with_points(l, gdf_points.geometry))


    # split_line = split(line, snap_points)
    # split_line._crs = crs
    # segments = [feature for feature in split_line]# if feature.length > 0.01]

    gdf_segments = gdf(geometry=segments, crs=crs)

    return gdf_segments


def near_analysis(buiding_centroids, street_network, crs):
    near_point = []
    building_name = []
    for point, name in zip(buiding_centroids.geometry, buiding_centroids.Name):
        point._crs = crs
        distance = 10e10
        for line in street_network.geometry:
            line._crs = crs
            nearest_point_candidate = line.interpolate(line.project(point))
            nearest_point_candidate._crs = crs
            distance_candidate = point.distance(nearest_point_candidate)
            if distance_candidate < distance:
                distance = distance_candidate
                nearest_point = nearest_point_candidate
        building_name.append(name)
        near_point.append(nearest_point)

    geometry = near_point
    df = gdf(geometry=geometry, crs=crs)
    df["Name"] = building_name
    return df


def snap_points(points, lines, crs):
    near_point = []
    for point in points.geometry:
        point._crs = crs
        distance = 1.0
        for line in lines.geometry:
            line._crs = crs
            point_inline_projection = line.interpolate(line.project(point))
            point_inline_projection._crs = crs
            distance_to_line = point.distance(point_inline_projection)
            if distance_to_line < distance:
                points = gdf(pd.concat([points, pd.DataFrame({"geometry":[point_inline_projection]})], ignore_index=True, sort=True), crs=crs)

    return points


def one_linestring_per_intersection(lines, crs):
    """ Move line endpoints to intersections of line segments.

    Given a list of touching or possibly intersecting LineStrings, return a
    list LineStrings that have their endpoints at all crossings and
    intersecting points and ONLY there.

    Args:
        a list of LineStrings or a MultiLineString

    Returns:
        a list of LineStrings
    """
    lines_merged = linemerge(lines)

    # intersecting multiline with its bounding box somehow triggers a first
    bounding_box = box(*lines_merged.bounds)

    # perform linemerge (one linestring between each crossing only)
    # if this fails, write function to perform this on a bbox-grid and then
    # merge the result
    lines_merged = lines_merged.intersection(bounding_box)
    lines_merged = linemerge(lines_merged)

    geometry = [line for line in lines_merged]
    df = gdf(geometry=geometry, crs=crs)

    return df


def line_merge(linestrings_or_multilinestrings):
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

    return linemerge(lines)


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

    # check coordinate system
    street_network = street_network.to_crs(get_geographic_coordinate_system())
    lon = street_network.geometry[0].centroid.coords.xy[0][0]
    lat = street_network.geometry[0].centroid.coords.xy[1][0]
    street_network = street_network.to_crs(get_projected_coordinate_system(lat, lon))
    crs = street_network.crs

    buiding_centroids = buiding_centroids.to_crs(get_geographic_coordinate_system())
    lon = buiding_centroids.geometry[0].centroid.coords.xy[0][0]
    lat = buiding_centroids.geometry[0].centroid.coords.xy[1][0]
    buiding_centroids = buiding_centroids.to_crs(get_projected_coordinate_system(lat, lon))
    crs = buiding_centroids.crs

    # get list of nearest points
    near_points = near_analysis(buiding_centroids, street_network, crs)

    # extend to the buiding centroids
    all_points = near_points.append(buiding_centroids)
    all_points.crs = crs

    # Aggregate these points with the GroupBy
    lines_to_buildings = all_points.groupby(['Name'])['geometry'].apply(lambda x: LineString(x.tolist()))
    lines_to_buildings = gdf(lines_to_buildings, geometry='geometry', crs=crs)

    # extend to the streets
    prototype_network = gdf(pd.concat([lines_to_buildings, street_network], ignore_index=True, sort=True), crs=crs)
    # compute endpoints of the new prototype network
    gdf_points = computer_end_points(prototype_network.geometry, crs)
    gdf_intersections = compute_intersections(prototype_network.geometry, crs)
    gdf_points_snapped = gdf(pd.concat([gdf_points, gdf_intersections], ignore_index=True, sort=True), crs=crs)

    # snap these points to the lines
    gdf_points_snapped = snap_points(gdf_points_snapped, prototype_network, crs)

    # get segments with method 1
    gdf_segments = split_line_by_nearest_points(prototype_network, gdf_points_snapped, 0.5, crs)

    # get segments with method 2
    gdf_segments = one_linestring_per_intersection(gdf_segments.geometry.values, crs)

    #change to projected coordinate system
    gdf_segments = gdf_segments.to_crs(get_projected_coordinate_system(lat, lon))
    gdf_points_snapped = gdf_points_snapped.to_crs(get_projected_coordinate_system(lat, lon))
    print(gdf_segments.crs)

    # gdf_segments.plot()
    # gdf_points.plot()
    # gdf_points_snapped.plot()
    # plt.show()
    # x=1

    gdf_segments.to_file(path_potential_network, driver='ESRI Shapefile')
    gdf_points_snapped.to_file(r'C:\Users\JimenoF\AppData\Local\Temp/trypoints.shp', driver='ESRI Shapefile')


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
