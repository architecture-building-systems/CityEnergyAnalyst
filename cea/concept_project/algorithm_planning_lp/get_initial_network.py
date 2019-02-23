import pandas as pd
from geopandas import GeoDataFrame as gdf
import time
from shapely.geometry import LineString, Point
import networkx as nx
from lp_config import *
import matplotlib.pyplot as plt


def calc_substation_location():
    """
    Determine building centroids of buildings and building shapes

    :param: none
    :type: Nonetype

    :returns: shp file stored in  \\inputs\\networks\\
    :rtype: Nonetype
    """

    input_buildings_shp = LOCATOR + SCENARIO +'inputs/building-geometry/zone.shp'
    building_poly = gdf.from_file(input_buildings_shp)

    building_centroids = building_poly.copy()
    building_centroids.geometry = building_poly['geometry'].centroid

    return building_centroids, building_poly


def connect_building_to_grid():
    """
    Splits street network at every connection point of a building and intersection. Since LineStrings of
    the street network at intersections are barely touching, an extrapolation have to be done.
    The function returns Gedataframes about connection points of the buildings and the splitted lines.

    :param: none
    :type: Nonetype

    :returns: df_nodes: information about every node in study case
    :rtype: GeoDataFrame
    :returns: tranches: information about every tranch in study case (splitted street network)
    :rtype: GeoDataFrame
    """

    # import streets
    input_streets_shp = LOCATOR + SCENARIO + 'inputs/networks/streets.shp'
    lines = gdf.from_file(input_streets_shp)

    # find centroids of buildings
    building_points, building_poly = calc_substation_location()

    # Create DF for points on line
    df_nodes = building_points.copy()
    df_nodes.drop(['floors_bg', 'height_bg', 'floors_ag', 'height_ag', ], axis=1, inplace=True)

    for idx, point in df_nodes.iterrows():
        df_nodes.loc[idx, 'Building'] = ('B%03i' % (idx+1))

    # Prepare DF for nearest point on line
    building_points['min_dist_to_lines'] = 0
    building_points['nearest_line'] = None

    for idx, point in building_points.iterrows():
        distances = lines.distance(point.geometry)
        nearest_line_idx = distances.idxmin()
        building_points.loc[idx, 'nearest_line'] = nearest_line_idx
        building_points.loc[idx, 'min_dist_to_lines'] = lines.distance(point.geometry).min()

        # find point on nearest line
        project_distances = lines.project(point.geometry)
        project_distance_nearest_line = lines.interpolate(project_distances[nearest_line_idx])
        df_nodes.loc[idx, 'geometry'] = project_distance_nearest_line[nearest_line_idx]

    # Determine Intersections of lines
    for idx, line in lines.iterrows():

        line.geometry = line.geometry.buffer(0.0001)
        line_intersections = lines.intersection(line.geometry)

        for index, intersection in line_intersections.iteritems():
            if intersection.geom_type == 'LineString' and index != idx:
                centroid_buffered = line_intersections[index].centroid.buffer(0.1)  # middle of Linestrings
                if not df_nodes.intersects(centroid_buffered).any():
                    index_df_nodes = df_nodes.shape[0]  # current number of rows in df_nodes
                    df_nodes.loc[index_df_nodes, 'geometry'] = line_intersections[index].centroid
                    df_nodes.loc[index_df_nodes, 'Building'] = None

    # Split Linestrings at df_nodes
    tranches_list = []

    for idx, line in lines.iterrows():
        line_buffered = line.copy()
        line_buffered.geometry = line.geometry.buffer(0.0001)
        line_point_intersections = df_nodes.intersection(line_buffered.geometry)
        filtered_points = line_point_intersections[line_point_intersections.is_empty == False]

        # start_point = Point(line.values[1].xy[0][0], line.values[1].xy[1][0])
        start_point = Point(line.geometry.xy[0][0], line.values[1].xy[1][0])

        distance = filtered_points.distance(start_point)
        filtered_points = gdf(data=filtered_points)
        filtered_points['distance'] = distance
        filtered_points.sort_values(by='distance', inplace=True)

        # Create new Lines
        for idx1 in range(0, len(filtered_points)-1):
            start = filtered_points.iloc[idx1][0]
            end = filtered_points.iloc[idx1+1][0]
            newline = LineString([start, end])
            tranches_list.append(newline)

    tranches = gdf(data=tranches_list)
    tranches.columns = ['geometry']
    tranches['Name'] = None
    tranches['Startnode'] = None
    tranches['Endnode'] = None
    tranches['Startnode_int'] = None
    tranches['Endnode_int'] = None
    tranches['Length'] = 0

    for idx, tranch in tranches.iterrows():
        tranches.loc[idx, 'Name'] = 'tranch' + str(idx)
        tranches.loc[idx, 'Length'] = tranch.values[0].length

        startnode = tranch.values[0].boundary[0]
        endnode = tranch.values[0].boundary[1]

        # startnode = Point(tranch.values[0].bounds[0], tranch.values[0].bounds[3])
        # endnode = Point(tranch.values[0].bounds[2], tranch.values[0].bounds[1])

        start_intersection = df_nodes.intersection(startnode.buffer(0.1))
        end_intersection = df_nodes.intersection(endnode.buffer(0.1))
        start_intersection_filtered = start_intersection[start_intersection.is_empty == False]
        end_intersection_filtered = end_intersection[end_intersection.is_empty == False]

        endnode_index = end_intersection_filtered.index.values[0]

        tranches.loc[idx, 'Startnode'] = 'Node' + str(start_intersection_filtered.index.values[0])
        tranches.loc[idx, 'Endnode'] = 'Node' + str(endnode_index)
        tranches.loc[idx, 'Startnode_int'] = int(start_intersection_filtered.index.values[0])
        tranches.loc[idx, 'Endnode_int'] = int(endnode_index)

    return df_nodes, tranches


def process_network(df_nodes):
    """
    Name and add information about every point in df_nodes. demand information is extracted from CEA data
    'Total_demand.csv'. Declare node[0] to 'PLANT', otherwise 'CONSUMER'

    :param: df_nodes: information about every node in study case
    :type: GeoDataFrame

    :returns: df_nodes: information about every node in study case
    :rtype: GeoDataFrame
    """

    building_path = LOCATOR + SCENARIO + '/outputs/data/demand/Total_demand.csv'
    building_prop = pd.read_csv(building_path)
    building_prop = building_prop[['Name', 'GRID0_kW']]
    building_prop.rename(columns={'Name': 'Building'}, inplace=True)

    # Name Points and assign integer index
    for idx, point in df_nodes.iterrows():
        df_nodes.loc[idx, 'Name'] = 'Node' + str(idx)
        df_nodes.loc[idx, 'Node_int'] = int(idx)

    df_nodes = pd.merge(df_nodes, building_prop, on='Building', how='outer')

    # Declare  plant and consumer nodes
    df_nodes['Type'] = None

    for idx, node in df_nodes.iterrows():
            if node['Building'] is not None:
                if idx == 0:
                    df_nodes.loc[idx, 'Type'] = 'PLANT'
                else:
                    df_nodes.loc[idx, 'Type'] = 'CONSUMER'

    return df_nodes


def create_length_dict(df_nodes, tranches):
    """
    Name and add information about every point in df_nodes. demand information is extracted from CEA data
    'Total_demand.csv'. Declare node[0] to 'PLANT', otherwise 'CONSUMER'

    :param: df_nodes: information about every node in study case
    :type: GeoDataFrame
    :returns: tranches: information about every tranch on street network in study case
    :rtype: GeoDataFrame

    :param dict_length: length on street network between every node
    :type dictionary
    :returns: dict_path: list of edges between two nodes
    :rtype: dictionary
    """

    G_complete = nx.Graph()

    for idx, node in df_nodes.iterrows():
        node_type = node['Type']
        G_complete.add_node(idx, type=node_type)

    for idx, tranch in tranches.iterrows():
        start_node_index = tranch['Startnode'][4::]
        end_node_index = tranch['Endnode'][4::]
        tranch_length = tranch['Length']
        G_complete.add_edge(int(start_node_index), int(end_node_index),
                            weight=tranch_length,
                            gene=idx,
                            startnode=start_node_index,
                            endnode=end_node_index)

    idx_nodes_sub = df_nodes[df_nodes['Type'] == 'PLANT'].index
    idx_nodes_consum = df_nodes[df_nodes['Type'] == 'CONSUMER'].index
    idx_nodes = idx_nodes_sub.append(idx_nodes_consum)

    dict_length = {}
    dict_path = {}
    for idx_node1 in idx_nodes:
        dict_length[idx_node1] = {}
        dict_path[idx_node1] = {}
        for idx_node2 in idx_nodes:
            if idx_node1 == idx_node2:
                dict_length[idx_node1][idx_node2] = 0.0
            else:
                nx.shortest_path(G_complete, 0, 1)
                dict_path[idx_node1][idx_node2] = nx.shortest_path(G_complete,
                                                                   source=idx_node1,
                                                                   target=idx_node2,
                                                                   weight='weight')
                dict_length[idx_node1][idx_node2] = nx.shortest_path_length(G_complete,
                                                                            source=idx_node1,
                                                                            target=idx_node2,
                                                                            weight='weight')
    return dict_length, dict_path


def main():

    points, building_poly = calc_substation_location()
    df_nodes, tranches = connect_building_to_grid()
    df_nodes_processed = process_network(df_nodes)
    dict_length, dict_path = create_length_dict(df_nodes_processed, tranches)


if __name__ == '__main__':
    t0 = time.clock()
    main()
    print 'get_initial_network() succeeded'
    print('total time: ', time.clock() - t0)
