"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import os

from geopandas import GeoDataFrame as gdf
from geopandas import GeoSeries as gds
from shapely.geometry import Point, shape, LineString

import cea.config
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Malcolm Kesson", ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import math


def dot(v, w):
    x, y, z = v
    X, Y, Z = w
    return x * X + y * Y + z * Z


def length(v):
    x, y, z = v
    return math.sqrt(x * x + y * y + z * z)


def vector(b, e):
    x, y, z = b
    X, Y, Z = e
    return (X - x, Y - y, Z - z)


def unit(v):
    x, y, z = v
    mag = length(v)
    return (x / mag, y / mag, z / mag)


def distance(p0, p1):
    return length(vector(p0, p1))


def scale(v, sc):
    x, y, z = v
    return (x * sc, y * sc, z * sc)


def add(v, w):
    x, y, z = v
    X, Y, Z = w
    return (x + X, y + Y, z + Z)


# Given a line with coordinates 'start' and 'end' and the
# coordinates of a point 'pnt' the proc returns the shortest
# distance from pnt to the line and the coordinates of the
# nearest point on the line.
#
# 1  Convert the line segment to a vector ('line_vec').
# 2  Create a vector connecting start to pnt ('pnt_vec').
# 3  Find the length of the line vector ('line_len').
# 4  Convert line_vec to a unit vector ('line_unitvec').
# 5  Scale pnt_vec by line_len ('pnt_vec_scaled').
# 6  Get the dot product of line_unitvec and pnt_vec_scaled ('t').
# 7  Ensure t is in the range 0 to 1.
# 8  Use t to get the nearest location on the line to the end
#    of vector pnt_vec_scaled ('nearest').
# 9  Calculate the distance from nearest to pnt_vec_scaled.
# 10 Translate nearest back to the start/end line.
# Malcolm Kesson 16 Dec 2012

def pnt2line(pnt, start, end):
    line_vec = vector(start, end)
    pnt_vec = vector(start, pnt)
    line_len = length(line_vec)
    line_unitvec = unit(line_vec)
    pnt_vec_scaled = scale(pnt_vec, 1.0 / line_len)
    t = dot(line_unitvec, pnt_vec_scaled)
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    nearest = scale(line_vec, t)
    dist = distance(nearest, pnt_vec)
    nearest = add(nearest, start)
    return (dist, nearest)


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
    return endpts


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

    import matplotlib.pyplot as plt
    import fiona
    # now clean the street network (basically create all vertices possible.

    for line in street_network.geometry:
        inters = []
        line2 = street_network[street_network['geometry'] != line].unary_union
        if line.intersects(line2):
            inter = line.intersection(line2)
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

        inters
        intpoints = gds(inters)
        intpoints.plot()
        plt.show()

        sub_set_lines = street_network[street_network['geometry'] != line].reset_index()
        # sub_set_lines = list(street_network.geometry)
        end_points = computer_end_points(sub_set_lines.geometry)
        intersections = compute_intersections(sub_set_lines.geometry)
        result = end_points.extend([pt for pt in intersections if pt not in end_points])
        IntPoints = line.intersection(sub_set_lines.unary_union)
        intpoints = gds([pnt for pnt in IntPoints])
        sub_set_lines.plot()
        intpoints.plot()
        plt.show()
        # intpoints = gds(IntPoints)
        # intpoints.plot(marker="*", markersize=5)
        street_network_clean = cut_line_at_points(line, IntPoints)
        street_network_clean.plot(cmap='OrRd')
        # street_network.unary_union.plot()

        x = 1

    # read shapefile into networkx format into a directed graph, this is the potential network
    # graph = nx.read_shp(input_network_shp)
    # nodes_graph = nx.read_shp(building_nodes_shp)
    #
    # # transform to an undirected graph
    # iterator_edges = graph.edges(data=True)
    #
    # # get graph
    # G = nx.Graph()
    # for (x, y, data) in iterator_edges:
    #     x = (round(x[0], 4), round(x[1], 4))
    #     y = (round(y[0], 4), round(y[1], 4))
    #     G.add_edge(x, y, weight=data[weight_field])
    #
    # # get nodes
    # iterator_nodes = nodes_graph.nodes(data=False)
    # terminal_nodes = [(round(node[0], 4), round(node[1], 4)) for node in iterator_nodes]
    # if len(disconnected_building_names) > 0:
    #     # identify coordinates of disconnected buildings and remove form terminal nodes list
    #     all_buiding_nodes_df = gdf.from_file(building_nodes_shp)
    #     all_buiding_nodes_df['coordinates'] = all_buiding_nodes_df['geometry'].apply(
    #         lambda x: (round(x.coords[0][0], 4), round(x.coords[0][1], 4)))
    #     disconnected_building_coordinates = []
    #     for building in disconnected_building_names:
    #         index = np.where(all_buiding_nodes_df['Name'] == building)[0]
    #         disconnected_building_coordinates.append(all_buiding_nodes_df['coordinates'].values[index][0])
    #     for disconnected_building in disconnected_building_coordinates:
    #         terminal_nodes = [i for i in terminal_nodes if i != disconnected_building]
    #
    # # calculate steiner spanning tree of undirected graph
    # mst_non_directed = nx.Graph(steiner_tree(G, terminal_nodes))
    # nx.write_shp(mst_non_directed, output_network_folder)
    x = 1

    # potential_network.to_file(path_potential_network, driver='ESRI Shapefile')


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
