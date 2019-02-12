"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import os

import pandas as pd
from geopandas import GeoDataFrame as gdf
from shapely.geometry import Point, LineString
from shapely.ops import split, snap

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
    line = gdf_line.geometry.unary_union
    line._crs = crs
    coords = gdf_points.geometry.unary_union
    coords._crs = crs

    # snap and split coords on line
    # returns GeometryCollection
    snap_points = snap(coords, line, tolerance)
    snap_points._crs = crs
    split_line = split(line, snap_points)
    split_line._crs = crs
    segments = [feature for feature in split_line if feature.length > 0.01]

    gdf_segments = gdf(geometry=segments, crs=crs)
    # gdf_segments.columns = ['index', 'geometry']

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
                points.append(gdf(geometry=[point_inline_projection], crs=crs))

    return points


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

    #check coordinate system
    street_network = street_network.to_crs(get_geographic_coordinate_system())
    lon = street_network.geometry[0].centroid.coords.xy[0][0]
    lat = street_network.geometry[0].centroid.coords.xy[1][0]
    street_network = street_network.to_crs(get_projected_coordinate_system(lat, lon))
    crs = street_network.crs


    # get list of nearest points
    near_points = near_analysis(buiding_centroids, street_network, crs)

    # extend to the buiding centroids
    all_points = near_points.append(buiding_centroids)
    all_points.crs = crs

    # Aggregate these points with the GroupBy
    lines_to_buildings = all_points.groupby(['Name'])['geometry'].apply(lambda x: LineString(x.tolist()))
    lines_to_buildings = gdf(lines_to_buildings, geometry='geometry', crs=crs)

    # extend to the streets
    prototype_network = lines_to_buildings.append(street_network).reset_index(drop=True)
    prototype_network.crs = crs
    # compute endpoints of the new prototype network
    gdf_points = computer_end_points(prototype_network.geometry, crs)
    gdf_intersections = compute_intersections(prototype_network.geometry, crs)
    gdf_points_snapped = gdf_points.append(gdf_intersections)
    gdf_points_snapped.crs = crs
    # snap these points to the lines
    gdf_points_snapped = snap_points(gdf_points_snapped, prototype_network, crs)

    # get segments
    gdf_segments = split_line_by_nearest_points(prototype_network, gdf_points_snapped, 10, crs)
    print(gdf_segments.crs)

    # gdf_segments.plot()
    # import matplotlib.pyplot as plt
    # gdf_points.plot()
    # gdf_points_snapped.plot()
    # plt.show()
    # x=1

    gdf_segments.to_file(path_potential_network, driver='ESRI Shapefile')
    gdf_points_snapped.to_file(r'C:\Users\JimenoF\AppData\Local\Temp/trypoints.shp' , driver='ESRI Shapefile')


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
