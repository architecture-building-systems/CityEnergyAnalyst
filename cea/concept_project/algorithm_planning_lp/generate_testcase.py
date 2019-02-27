import pandas as pd
import geopandas as gpd
import time
from lp_config import *
from shapely.geometry import LineString, Point
import random
import matplotlib.pyplot as plt
import networkx as nx

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def initiate_gdf():
    input_buildings_shp = LOCATOR + '/reference-case-WTP/MIX_high_density/' +'inputs/building-geometry/zone.shp'
    input_streets_shp = LOCATOR + '/reference-case-WTP/MIX_high_density/' + 'inputs/networks/streets.shp'

    building_poly = gpd.GeoDataFrame.from_file(input_buildings_shp)
    building_centroids = building_poly.copy()
    building_centroids.geometry = building_poly['geometry'].centroid

    # import streets
    lines = gpd.GeoDataFrame.from_file(input_streets_shp)

    # Create DF for points on line
    df_nodes = building_centroids.copy()

    lines_points = gpd.GeoDataFrame(pd.concat([lines, df_nodes], ignore_index=True))

    lines_points_90 = lines_points.copy()
    lines_points_90 = lines_points_90.geometry.scale(xfact=0.6, yfact=2.0, origin=(371554, 140760))
    lines_points_90 = gpd.GeoSeries.rotate(lines_points_90.geometry, 90, origin=(371450, 140600))
    gdf_lines_points_90 = gpd.GeoDataFrame(data=lines_points_90)
    gdf_lines_points_90.columns = ['geometry']

    lines_points_180 = lines_points.copy()
    lines_points_180 = lines_points_180.geometry.scale(xfact=0.5, yfact=0.5, origin=(371554, 140760))
    lines_points_180 = gpd.GeoSeries.rotate(lines_points_180.geometry, 180, origin=(371554, 140760))
    gdf_lines_points_180 = gpd.GeoDataFrame(data=lines_points_180)
    gdf_lines_points_180.columns = ['geometry']

    lines_points_270 = lines_points.copy()
    lines_points_270 = gpd.GeoSeries.rotate(lines_points_270.geometry, 270, origin=(371554, 140760))
    gdf_lines_points_270 = gpd.GeoDataFrame(data=lines_points_270)
    gdf_lines_points_270.columns = ['geometry']

    gdf_lines_points_med = gpd.GeoDataFrame(pd.concat([lines_points, gdf_lines_points_90], ignore_index=True))
    gdf_lines_points_big = gpd.GeoDataFrame(pd.concat([lines_points, gdf_lines_points_90, gdf_lines_points_180, gdf_lines_points_270], ignore_index=True))

    gdf_points_med = gdf_lines_points_med[gdf_lines_points_med.geometry.geom_type == 'Point'].reset_index(drop=True)
    gdf_points_med = gdf_points_med.drop(['Name', 'FID', 'floors_ag', 'floors_bg', 'height_ag', 'height_bg'], axis=1)
    gdf_lines_med = gdf_lines_points_med[gdf_lines_points_med.geometry.geom_type == 'LineString'].reset_index(drop=True)
    gdf_lines_med = gdf_lines_med.drop(['Name', 'floors_ag', 'floors_bg', 'height_ag', 'height_bg'], axis=1)

    gdf_points_big = gdf_lines_points_big[gdf_lines_points_big.geometry.geom_type == 'Point'].reset_index(drop=True)
    gdf_points_big = gdf_points_big.drop(['Name', 'FID', 'floors_ag', 'floors_bg', 'height_ag', 'height_bg'], axis=1)
    gdf_lines_big = gdf_lines_points_big[gdf_lines_points_big.geometry.geom_type == 'LineString'].reset_index(drop=True)
    gdf_lines_big = gdf_lines_big.drop(['Name', 'floors_ag', 'floors_bg', 'height_ag', 'height_bg'], axis=1)

    for idx, point in gdf_points_big.iterrows():
        gdf_points_big.loc[idx, 'Name'] = ('B%03i' % idx)

    for idx, point in gdf_points_med.iterrows():
        gdf_points_med.loc[idx, 'Name'] = ('B%03i' % idx)

    return gdf_points_med, gdf_lines_med, gdf_points_big, gdf_lines_big


def process_gdf(building_points, lines):

    # Create DF for points on line
    df_nodes = building_points.copy()

    for idx, point in df_nodes.iterrows():
        df_nodes.loc[idx, 'Building'] = ('B%03i' % idx)

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

        start_point = Point(line.values[1].xy[0][0], line.values[1].xy[1][0])

        distance = filtered_points.distance(start_point)
        filtered_points = gpd.GeoDataFrame(data=filtered_points)
        filtered_points['distance'] = distance
        filtered_points.sort_values(by='distance', inplace=True)

        # Create new Lines
        for idx1 in range(0, len(filtered_points)-1):
            start = filtered_points.iloc[idx1][0]
            end = filtered_points.iloc[idx1+1][0]
            newline = LineString([start, end])
            tranches_list.append(newline)

    tranches = gpd.GeoDataFrame(data=tranches_list)
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


def process_network_rand(df_nodes):

    random.seed(1000)
    mean = 2227.80459091 # mean value of GRID0_kW of Scenario MIX_high_density

    # Name Points and assign integer index
    for idx, point in df_nodes.iterrows():
        df_nodes.loc[idx, 'Name'] = 'Node' + str(idx)
        df_nodes.loc[idx, 'Node_int'] = int(idx)

    # Declare  plant and consumer nodes
    for idx, node in df_nodes.iterrows():
        if node['Building'] is not None:
            # Gaussian distribution. mu is the mean, and sigma is the standard deviation
            df_nodes.loc[idx, 'GRID0_kW'] = random.gauss(mean, 500)

            if idx == 0:
                df_nodes.loc[idx, 'Type'] = 'PLANT'
            else:
                df_nodes.loc[idx, 'Type'] = 'CONSUMER'

    return df_nodes


def process_network(df_nodes):
    building_path = LOCATOR + SCENARIO + '/outputs/data/demand/Total_demand.csv'
    building_prop = pd.read_csv(building_path)
    building_prop = building_prop[['Building', 'GRID0_kW']]

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


def plot_street(df_nodes, tranches):
    # Plotting Graph
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    for idx_tranch, tranch in tranches.iterrows():
        int_node1 = tranch['Startnode_int']
        int_node2 = tranch['Endnode_int']

        geo_node1 = df_nodes.loc[int_node1].geometry.xy
        geo_node2 = df_nodes.loc[int_node2].geometry.xy

        ax1.plot((geo_node1[0][0], geo_node2[0][0]),
                 (geo_node1[1][0], geo_node2[1][0]),
                 color='black')

    for idx, point in df_nodes.iterrows():
        name = str(point['Name'][4::])

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
            ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
            ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)
        else:
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)
            ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

    plt.show()


def connect_grids(list_new_tranches, df_nodes, tranches):
    int_len_tranch = len(tranches)

    for idx_tranch, tranch in enumerate(list_new_tranches):
        idx = int_len_tranch + idx_tranch

        tranches.loc[idx, 'Name'] = 'tranch' + str(idx)

        int_node1 = tranch[0]
        int_node2 = tranch[1]

        geo_node1 = df_nodes.loc[int_node1].geometry
        geo_node2 = df_nodes.loc[int_node2].geometry

        tranches.loc[idx, 'geometry'] = LineString([geo_node1, geo_node2])

        tranches.loc[idx, 'Length'] = tranches.loc[idx, 'geometry'].length
        tranches.loc[idx, 'Startnode'] = 'Node' + str(int_node1)
        tranches.loc[idx, 'Endnode'] = 'Node' + str(int_node2)
        tranches.loc[idx, 'Startnode_int'] = int_node1
        tranches.loc[idx, 'Endnode_int'] = int_node2

    return tranches


def write_files(df_nodes, gdf_points_big, tranches):
    path = 'C:/Users/xthan/Desktop/TUMCreate/python_code/concept/data/newcase/'
    df_nodes = df_nodes[df_nodes['Type'].notnull()]

    crs = '+proj=utm +zone=48N +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
    gdf_tranches = gpd.GeoDataFrame(crs=crs, geometry=tranches.geometry)
    gdf_points_big = gpd.GeoDataFrame(crs=crs, geometry=gdf_points_big.geometry)

    df_nodes.to_csv(path + 'med/outputs/data/demand/Total_demand.csv')
    # gdf_tranches.to_file(path + 'big/inputs/networks/streets.shp', driver='ESRI Shapefile', encoding='ISO-8859-1')
    # gdf_points_big.to_file(path + 'big/inputs/building-geometry/zone.shp', driver='ESRI Shapefile', encoding='ISO-8859-1')


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
    list_new_tranches_big = [(105, 31),
                             (107, 126),
                             (150, 130),
                             (131, 53),
                             (174, 153),
                             (177, 110),
                             (87, 9),
                             (179, 102),
                             (180, 109),
                             (109, 133),
                             (132, 157),
                             (156, 181)]

    list_new_tranches_med = [(65, 89),
                             (63, 82),
                             (21, 31),
                             (61, 90)]

    gdf_points_med, gdf_lines_med, gdf_points_big, gdf_lines_big = initiate_gdf()

    df_nodes_med, tranches_med = process_gdf(gdf_points_med, gdf_lines_med)
    # df_nodes_big, tranches_big = process_gdf(gdf_points_big, gdf_lines_big)

    # df_nodes_processed_med = process_network_rand(df_nodes_med)
    # df_nodes_processed_big = process_network_rand(df_nodes_big)

    df_nodes_processed_med = process_network(df_nodes_med)
    # df_nodes_processed_big = process_network(df_nodes_big)

    # tranches_big = connect_grids(list_new_tranches_big, df_nodes_processed_big, tranches_big)
    tranches_med = connect_grids(list_new_tranches_med, df_nodes_processed_med, tranches_med)

    # plot_street(df_nodes_processed_big, tranches_big)
    # plot_street(df_nodes_processed_med, tranches_med)

    # write_files(df_nodes_processed_med, gdf_points_med, tranches_med)
    # write_files(df_nodes_processed_big, gdf_points_big, tranches_big)

    # dict_length, dict_path = create_length_dict(df_nodes_processed_big, tranches_big)
    dict_length, dict_path = create_length_dict(df_nodes_processed_med, tranches_med)

    return df_nodes_processed_med, tranches_med, dict_length, dict_path


if __name__ == '__main__':
    t0 = time.clock()
    main()
    print 'get_initial_network() succeeded'
    print('total time: ', time.clock() - t0)
