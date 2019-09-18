import json
import re

import geopandas as gpd
import networkx as nx
import shapely
from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile
from cea.utilities.standardize_coordinates import get_projected_coordinate_system
import get_initial_network as gia

from cea.technologies.network_layout.main import layout_network, NetworkLayout
from cea.technologies.network_layout.substations_location import calc_substation_location

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def initial_network(config, locator):
    """
    Initiate data of main problem

    :param config:
    :param locator:
    :returns:
        - **points_on_line** : information about every node in study case
        - **tranches** : tranches
        - **dict_length** : dictionary containing lengths
        - **dict_path** : dictionary containing paths
    :rtype: geodf, geodf, dict, dict

    """

    input_buildings_shp = locator.get_electric_substation_input_location()
    output_substations_shp = locator.get_electric_substation_output_location()
    input_streets_shp = locator.get_street_network()

    building_points, _ = calc_substation_location(input_buildings_shp, output_substations_shp, [])
    # connect building nodes to street
    points_on_line, tranches = gia.connect_building_to_grid(building_points, input_streets_shp)
    # write node types (consumer/plant) in the attribute table
    points_on_line_processed = gia.process_network(points_on_line, config, locator)
    # get lengths of all edges
    dict_length, dict_path = gia.create_length_complete_dict(points_on_line_processed, tranches)

    return points_on_line_processed, tranches, dict_length, dict_path

def find_gridpath(m, dict_path):
    """
    Find path of edges on STREET network between ELECTRIC consumer and plant node

    :param m: complete pyomo model
    :type m: pyomo model
    :param dict_path: list of edges between two nodes
    :type dict_path: dictionary
    :returns: set_tranches: tuples with unique edges (startnode, endnode)
    :rtype: set(int, int)

    """

    var_x = m.var_x.values()

    set_tranches = set()
    for x in var_x:
        if x.value > 0.5:
            int_x = re.findall(r'\d+', x.local_name)

            int_startnode = int(int_x[0])
            int_endnode = int(int_x[1])

            list_path = dict_path[int_startnode][int_endnode]

            for idx_path, path in enumerate(list_path[:-1]):
                int_node1 = list_path[idx_path]
                int_node2 = list_path[idx_path + 1]

                if (int_node2, int_node1) not in set_tranches:
                    set_tranches.add((int_node1, int_node2))

    return set_tranches


def set_to_list_geo(set_tranches, points_on_line):
    """
    Convert set of (startnode, endnode) to a list of coordinate data of each node

    :param set_tranches: tuples with unique edges (startnode, endnode)
    :type set_tranches: set(int, int)
    :param points_on_line: information about every node in study case
    :type points_on_line: GeoDataFrame
    :returns: list_geotranch: tuples with geo data of startnode and endnode
    :rtype: list(float, float)

    """

    list_geotranch = []
    for tranch in set_tranches:
        node1 = points_on_line.loc[points_on_line['Node_int'] == tranch[0]]
        node2 = points_on_line.loc[points_on_line['Node_int'] == tranch[1]]

        geo1 = node1['geometry'].values[0]
        geo2 = node2['geometry'].values[0]

        str_geo1 = str('[') + str(geo1.x) + str(',') + str(geo1.y) + str(']')
        str_geo2 = str('[') + str(geo2.x) + str(',') + str(geo2.y) + str(']')

        str_geo = str('[') + str_geo1 + str(',') + str_geo2 + str(']')

        list_geotranch.append(str_geo)

    return list_geotranch


def find_thermal_network_path(m, points_on_line, set_grid, dict_length, dict_connected):
    """
    Find path of edges on GRID network between THERMAL consumer and plant node

    :param m: complete pyomo model
    :type m: pyomo model
    :param points_on_line: information about every node in study case
    :type points_on_line: GeoDataFrame
    :param set_grid: tuples with unique edges (startnode, endnode)
    :type set_grid: set(int, int)
    :param dict_length: length on street network between every node
    :type dict_length: dictionary
    :returns:
        - **set_thermal_network**: tuples with unique edges (startnode, endnode)    :
    :rtype: set(int, int)

    """

    list_connected = []
    for idx_connected, connected in enumerate(dict_connected):
        list_connected.append((idx_connected, int(connected)))

    set_thermal_network = set()

    if list_connected:
        G_grid = nx.Graph()

        # Add plant node
        node_plant = points_on_line[points_on_line['Type'] == 'PLANT']
        idx_plant = int(node_plant.index.values[0])
        G_grid.add_node(idx_plant)

        for line in set_grid:
            start_node_index = line[0]
            end_node_index = line[1]
            tranch_length = dict_length[start_node_index][end_node_index]

            G_grid.add_edge(int(start_node_index),
                            int(end_node_index),
                            weight=tranch_length,
                            )

        for connected in list_connected:
            if connected[1] is 1:
                idx_consumer = connected[0]
                if idx_consumer is not idx_plant:
                    list_path = nx.shortest_path(G_grid,
                                                 source=idx_plant,
                                                 target=idx_consumer,
                                                 weight='weight')

                    for idx_path, path in enumerate(list_path[:-1]):
                        int_node1 = list_path[idx_path]
                        int_node2 = list_path[idx_path + 1]

                        set_thermal_network.add((int_node1, int_node2))

    return set_thermal_network


def connect_building_to_street(m, points_on_line, list_geo_thermal_network, config, locator, dict_connected):
    """
    Connect centroid of every THERMAL consumer building to thermal network

    :param m: complete pyomo model
    :type m: pyomo model
    :param points_on_line: information about every node in study case
    :type points_on_line: GeoDataFrame
    :param list_geo_thermal_network: tuples with geo data of startnode and endnode
    :type list_geo_thermal_network: list(float, float)
    :param config:
    :param locator:
    :param dict_connected:
    :return: list_geo_thermal_network
    :rtype: list(float, float)

    """

    input_buildings_shp = locator.get_electric_substation_input_location()
    output_substations_shp = locator.get_electric_substation_output_location()
    building_centroids, poly = calc_substation_location(input_buildings_shp, output_substations_shp, [])

    list_connected = []
    for idx_connected, connected in enumerate(dict_connected):
        list_connected.append((idx_connected, int(connected)))

    for connected in list_connected:
        if connected[1]:
            int_node = connected[0]

            geo1 = points_on_line.iloc[int_node]['geometry'].xy
            geo2 = building_centroids.iloc[int_node]['geometry'].xy

            str_geo1 = str('[') + str(geo1[0][0]) + str(',') + str(geo1[1][0]) + str(']')
            str_geo2 = str('[') + str(geo2[0][0]) + str(',') + str(geo2[1][0]) + str(']')

            str_geo = str('[') + str_geo1 + str(',') + str_geo2 + str(']')
            list_geo_thermal_network.append(str_geo)

    return list_geo_thermal_network


def write_coordinates_to_shp_file(config, locator, list_geotranch, name):
    """
    Write grid.shp and thermal_network.shp on base of list of coordinate data

    :param list_geotranch: tuples with geo data of startnode and endnode
    :type list_geotranch: list(float, float)
    :param name: filename of shp file
    :type name: string
    :return: shp file stored in \\inputs\\networks\\
    :rtype: Nonetype

    """

    input_street_shp = locator.get_street_network()
    output_path_shp = locator.get_electric_network_output_location(name)

    geometry = [shapely.geometry.LineString(json.loads(g)) for g in list_geotranch]

    gdf_street = gpd.GeoDataFrame.from_file(input_street_shp)
    lat, lon = get_lat_lon_projected_shapefile(gdf_street)
    crs = get_projected_coordinate_system(lat, lon)
    gdf = gpd.GeoDataFrame(crs=crs, geometry=geometry)

    gdf.to_file(output_path_shp, driver='ESRI Shapefile', encoding='ISO-8859-1')


def electrical_network_layout_to_shapefile(m, electrical_grid_file_name, thermal_network_file_name, config, locator,
                                           dict_connected):
    """
    This function converts the results of the grid optimization and generates a thermal network. Grid and thermal
    network are written as shp files to folder \\inputs\\networks\\

    :param m: complete pyomo model
    :type m: pyomo model
    :param electrical_grid_file_name:
    :param thermal_network_file_name:
    :param config:
    :param locator:
    :param dict_connected:

    """

    #CREATE THE ELECTRICAL NETWORK FILE
    # Initiate data of main problem
    points_on_line, tranches, dict_length, dict_path = initial_network(config, locator)

    # Find path of edges on STREET network between ELECTRIC consumer and plant node
    set_grid = find_gridpath(m, dict_path)

    # Convert set of (startnode, endnode) to a list of coordinate data of each node
    list_geo_grid = set_to_list_geo(set_grid, points_on_line)

    # Write grid.shp and thermal_network.shp on base of list of coordinate data
    write_coordinates_to_shp_file(config, locator, list_geo_grid, electrical_grid_file_name)

    # CREATE THE ELECTRICAL NETWORK FILE AS STREETS
    # from cea.technologies.thermal_network.network_layout.connectivity_potential import calc_connectivity_network
    # path_streets_shp = locator.get_electric_network_output_location(electrical_grid_file_name)
    # path_connection_point_buildings_shp = locator.get_electric_substation_output_location()
    # path_potential_network = locator.get_electric_network_output_location(thermal_network_file_name)
    # calc_connectivity_network(path_streets_shp, path_connection_point_buildings_shp, path_potential_network)

    # # # Find path of edges on GRID network between THERMAL consumer and plant node
    # set_thermal_network = find_thermal_network_path(m, points_on_line, set_grid, dict_length, dict_connected)
    #
    # # Convert set of (startnode, endnode) to a list of coordinate data of each node
    # list_geo_thermal_network = set_to_list_geo(set_thermal_network, points_on_line)
    #
    # # Connect centroid of every THERMAL consumer building to thermal network
    # list_geo_thermal_network = connect_building_to_street(m, points_on_line, list_geo_thermal_network, config, locator,
    #                                                       dict_connected)
    #
    # print ('list_geo_thermal_network')
    #
    # print (list_geo_thermal_network)
    #
    # # Write grid.shp and thermal_network.shp on base of list of coordinate data
    # write_coordinates_to_shp_file(config, locator, list_geo_thermal_network, thermal_network_file_name)


def thermal_network_layout_to_shapefile(config, input_path_name, locator):
    connected_building_names = []  # Placeholder, this is only used in Network optimization
    network_layout = NetworkLayout(network_layout=config.network_layout)
    layout_network(network_layout, locator, connected_building_names, input_path_name)
