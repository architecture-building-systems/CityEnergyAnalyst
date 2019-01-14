import re
import json
import geopandas as gpd
import shapely
import networkx as nx
from concept_parameters import *
import get_initial_network as gia

from cea.utilities.standarize_coordinates import get_projected_coordinate_system
from cea.utilities.standarize_coordinates import get_lat_lon_projected_shapefile


def initial_network(config, locator):
    """
    Initiate data of main problem

    :param None
    :type Nonetype

    :returns: points_on_line: information about every node in study case
    :rtype: GeoDataFrame
    :returns: tranches
    :rtype: GeoDataFrame
    :returns: dict_length
    :rtype: dictionary
    :returns: dict_path: list of edges between two nodes
    :rtype: dictionary
    """

    gia.calc_substation_location(config, locator)
    points_on_line, tranches = gia.connect_building_to_grid(config, locator)
    points_on_line_processed = gia.process_network(points_on_line, config, locator)
    dict_length, dict_path = gia.create_length_complete_dict(points_on_line_processed, tranches)

    return points_on_line_processed, tranches, dict_length, dict_path


def find_gridpath(m, dict_path):
    """
    Find path of edges on STREET network between ELECTRIC consumer and plant node

    :param m: complete pyomo model
    :type pyomo model
    :param dict_path: list of edges between two nodes
    :type dictionary

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
    :type set(int, int)
    :param points_on_line: information about every node in study case
    :type GeoDataFrame

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
    :type pyomo model
    :param points_on_line: information about every node in study case
    :type GeoDataFrame
    :param set_grid: tuples with unique edges (startnode, endnode)
    :type set(int, int)
    :param dict_length: length on street network between every node
    :type dictionary

    :returns: set_thermal_network: tuples with unique edges (startnode, endnode)    :
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
    :type pyomo model
    :param points_on_line: information about every node in study case
    :type GeoDataFrame
    :param: list_geo_thermal_network: tuples with geo data of startnode and endnode
    :type: list(float, float)

    :returns: list_geo_thermal_network
    :rtype: list(float, float)
    """

    building_centroids, poly = gia.calc_substation_location(config, locator)

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


def write_shp(config, locator, list_geotranch, name='grid'):
    """
    Write grid.shp and thermal_network.shp on base of list of coordinate data

    :param: list_geotranch: tuples with geo data of startnode and endnode
    :type: list(float, float)
    :param: name: filename of shp file
    :type: string

    :returns: shp file stored in  \\inputs\\networks\\
    :rtype: Nonetype
    """

    input_street_shp = locator.get_streets_input_location()
    output_path_shp = locator.get_streets_output_location(name)

    geometry = [shapely.geometry.LineString(json.loads(g)) for g in list_geotranch]

    gdf_street = gpd.GeoDataFrame.from_file(input_street_shp)
    lat, lon = get_lat_lon_projected_shapefile(gdf_street)
    crs = get_projected_coordinate_system(lat, lon)
    gdf = gpd.GeoDataFrame(crs=crs, geometry=geometry)

    gdf.to_file(output_path_shp, driver='ESRI Shapefile', encoding='ISO-8859-1')


def creating_thermal_network_shape_file_main(m, electrical_grid_file_name, thermal_network_file_name, config, locator, dict_connected):
    """
    This function converts the results of the grid optimization and generates a thermal network. Grid and thermal
    network are written as shp files to folder \\inputs\\networks\\

    :param m: complete pyomo model
    :type pyomo model

    :returns: None
    :rtype: Nonetype
    """

    # Initiate data of main problem
    points_on_line, tranches, dict_length, dict_path = initial_network(config, locator)

    # Find path of edges on STREET network between ELECTRIC consumer and plant node
    set_grid = find_gridpath(m, dict_path)

    # Convert set of (startnode, endnode) to a list of coordinate data of each node
    list_geo_grid = set_to_list_geo(set_grid, points_on_line)

    print ('list geo grid')

    print (list_geo_grid)

    # Find path of edges on GRID network between THERMAL consumer and plant node
    set_thermal_network = find_thermal_network_path(m, points_on_line, set_grid, dict_length, dict_connected)

    # Convert set of (startnode, endnode) to a list of coordinate data of each node
    list_geo_thermal_network = set_to_list_geo(set_thermal_network, points_on_line)

    # Connect centroid of every THERMAL consumer building to thermal network
    list_geo_thermal_network = connect_building_to_street(m, points_on_line, list_geo_thermal_network, config, locator, dict_connected)

    print ('list_geo_thermal_network')

    print (list_geo_thermal_network)

    # Write grid.shp and thermal_network.shp on base of list of coordinate data
    write_shp(config, locator, list_geo_grid, name=electrical_grid_file_name)
    write_shp(config, locator, list_geo_thermal_network, name=thermal_network_file_name)
