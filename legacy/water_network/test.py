from __future__ import division

import geopandas as gpd
import wntr


def extract_network_from_shapefile(edge_shapefile_df, node_shapefile_df):
    """
    Extracts network data into DataFrames for pipes and nodes in the network

    :param edge_shapefile_df: DataFrame containing all data imported from the edge shapefile
    :param node_shapefile_df: DataFrame containing all data imported from the node shapefile
    :type edge_shapefile_df: DataFrame
    :type node_shapefile_df: DataFrame
    :return node_df: DataFrame containing all nodes and their corresponding coordinates
    :return edge_df: list of edges and their corresponding lengths and start and end nodes
    :rtype node_df: DataFrame
    :rtype edge_df: DataFrame

    """
    # set precision of coordinates
    decimals = 6
    # create node dictionary with plant and consumer nodes
    node_dict = {}
    node_shapefile_df.set_index("Name", inplace=True)
    node_shapefile_df = node_shapefile_df.astype('object')
    node_shapefile_df['coordinates'] = node_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort node_df by index number
    node_sorted_index = node_shapefile_df.index.to_series().str.split('NODE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    node_shapefile_df = node_shapefile_df.reindex(index=node_sorted_index.index)
    # assign node properties (plant/consumer/none)
    node_shapefile_df['plant'] = ''
    node_shapefile_df['consumer'] = ''
    node_shapefile_df['none'] = ''

    for node, row in node_shapefile_df.iterrows():
        coord_node = row['geometry'].coords[0]
        if row['Type'] == "PLANT":
            node_shapefile_df.loc[node, 'plant'] = node
        elif row['Type'] == "CONSUMER":  # TODO: add 'PROSUMER' by splitting nodes
            node_shapefile_df.loc[node, 'consumer'] = node
        else:
            node_shapefile_df.loc[node, 'none'] = node
        coord_node_round = (round(coord_node[0], decimals), round(coord_node[1], decimals))
        node_dict[coord_node_round] = node

    # create edge dictionary with pipe lengths and start and end nodes
    # complete node dictionary with missing nodes (i.e., joints)
    edge_shapefile_df.set_index("Name", inplace=True)
    edge_shapefile_df = edge_shapefile_df.astype('object')
    edge_shapefile_df['coordinates'] = edge_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort edge_df by index number
    edge_sorted_index = edge_shapefile_df.index.to_series().str.split('PIPE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    edge_shapefile_df = edge_shapefile_df.reindex(index=edge_sorted_index.index)
    # assign edge properties
    edge_shapefile_df['pipe length'] = 0
    edge_shapefile_df['start node'] = ''
    edge_shapefile_df['end node'] = ''

    for pipe, row in edge_shapefile_df.iterrows():
        # get the length of the pipe and add to dataframe
        edge_shapefile_df.loc[pipe, 'pipe length'] = row['geometry'].length
        # get the start and end notes and add to dataframe
        edge_coords = row['geometry'].coords
        start_node = (round(edge_coords[0][0], decimals), round(edge_coords[0][1], decimals))
        end_node = (round(edge_coords[1][0], decimals), round(edge_coords[1][1], decimals))
        if start_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'start node'] = node_dict[start_node]
        else:
            print('The start node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')
        if end_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'end node'] = node_dict[end_node]
        else:
            print('The end node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')

    return node_shapefile_df, edge_shapefile_df


def get_thermal_network_from_shapefile(locator, network_type, network_name):
    """
    This function reads the existing node and pipe network from a shapefile and produces an edge-node incidence matrix
    (as defined by Oppelt et al., 2016) as well as the edge properties (length, start node, and end node) and node
    coordinates.
    """

    # import shapefiles containing the network's edges and nodes
    network_edges_df = gpd.read_file(locator.get_network_layout_edges_shapefile(network_type, network_name))
    network_nodes_df = gpd.read_file(locator.get_network_layout_nodes_shapefile(network_type, network_name))

    # check duplicated NODE/PIPE IDs
    duplicated_nodes = network_nodes_df[network_nodes_df.Name.duplicated(keep=False)]
    duplicated_edges = network_edges_df[network_edges_df.Name.duplicated(keep=False)]
    if duplicated_nodes.size > 0:
        raise ValueError('There are duplicated NODE IDs:', duplicated_nodes)
    if duplicated_edges.size > 0:
        raise ValueError('There are duplicated PIPE IDs:', duplicated_nodes)

    # get node and pipe information
    node_df, edge_df = extract_network_from_shapefile(network_edges_df, network_nodes_df)

    return edge_df, node_df


def calc_max_diameter(volume_flow_m3s, velocity_ms):
    import math
    diameter_m = math.sqrt((volume_flow_m3s / velocity_ms) * (4 / math.pi))
    return diameter_m


def calc_head_loss_m(diamter_m, max_volume_flow_rates_m3s, coefficient_friction, length_m):
    hf_L = (10.67 / (coefficient_friction ** 1.85)) * (max_volume_flow_rates_m3s ** 1.852) / (diamter_m ** 4.8704)
    head_loss_m = hf_L * length_m
    return head_loss_m


import cea.inputlocator
import cea.config
import numpy as np
import pandas as pd

config = cea.config.Configuration()
locator = cea.inputlocator.InputLocator(scenario=config.scenario)

# add options for data sources: heating or cooling network, csv or shp
network_type = config.thermal_network.network_type  # set to either 'DH' or 'DC'
file_type = config.thermal_network.file_type  # set to csv or shp

# this does a rule of max and min flow to set a diameter. if false it takes the input diameters
set_diameter = config.thermal_network.set_diameter  # boolean
network_names = config.thermal_network.network_names
network_name = ''
edge_df, node_df = get_thermal_network_from_shapefile(locator, network_type, network_name)

# Create a water network model
wn = wntr.network.WaterNetworkModel()

# add loads
wn.add_pattern('pat1', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
wn.add_pattern('pat2', [10, 10, 10, 10, 10, 10, 10, 10, 10, 10])
# add nodes
for node in node_df.iterrows():
    if node[1]["Type"] == "CONSUMER":
        base_demand_m3s = 0.03
        demand_pattern = 'pat2'
        wn.add_junction(node[0], base_demand=base_demand_m3s, demand_pattern=demand_pattern, elevation=0,
                        coordinates=node[1]["coordinates"])
    elif node[1]["Type"] == "PLANT":
        base_head = 1000
        reservoir_pattern = 'pat1'
        start_node = node[0]
        end_node = edge_df[edge_df['start node'] == start_node]['end node'].values[0]
        wn.add_reservoir(start_node, base_head=base_head, head_pattern=reservoir_pattern,
                         coordinates=node[1]["coordinates"])
    else:
        base_demand_m3s = 0
        demand_pattern = 'pat2'
        wn.add_junction(node[0], base_demand=base_demand_m3s, demand_pattern=demand_pattern, elevation=0,
                        coordinates=node[1]["coordinates"])

# add pipes
for edge in edge_df.iterrows():
    length = edge[1]["pipe length"]
    wn.add_pipe(edge[0], edge[1]["start node"], edge[1]["end node"], length=length, roughness=100, minor_loss=0.0,
                status='OPEN')

# add options
wn.options.time.duration = 10 * 3600
wn.options.time.hydraulic_timestep = 60 * 60
wn.options.time.pattern_timestep = 60 * 60
velocity_ms = 3
coefficient_friction_hanzen_williams = 150
lequivalent_length_factor = 0.2

# Simulate hydraulics
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()

volume_flow_rates_m3s = results.link['flowrate'].abs()
max_volume_flow_rates_m3s = volume_flow_rates_m3s.max()
pipe_names = max_volume_flow_rates_m3s.index.values
diameter_m = np.vectorize(calc_max_diameter)(max_volume_flow_rates_m3s, velocity_ms=velocity_ms)
max_head_loss_m = [calc_head_loss_m(diameter,
                                    max_volume_flow_rates_m3s=mass_flow,
                                    coefficient_friction=coefficient_friction_hanzen_williams,
                                    length_m=edge_df.loc[pipe_name, 'pipe length'])*(1+lequivalent_length_factor) for pipe_name, diameter, mass_flow in
                                    zip(pipe_names, diameter_m, max_volume_flow_rates_m3s)]


data  = pd.DataFrame({'pipe_names':pipe_names,
                      'max_volume_flow_rates_m3s':max_volume_flow_rates_m3s.values,
                      'diameter_m':diameter_m,
                      'max_head_loss_m':max_head_loss_m
                      })

curve_points = data.sum(axis=0)
curve_points_y = curve_points['max_head_loss_m']
curve_points_x = curve_points['max_volume_flow_rates_m3s']


xy_tuples_list=[(0, curve_points_y), (0.0, curve_points_y*2), (curve_points_x/2, curve_points_y/2)]
wn.add_curve('curve1', curve_type='HEAD', xy_tuples_list=xy_tuples_list)
for node in node_df.iterrows():
    if node[1]["Type"] == "PLANT":
        base_head = 1
        start_node = node[0]
        end_node = edge_df[edge_df['start node'] == start_node]['end node'].values[0]
        reservoir = wn.get_node(start_node)
        reservoir.base_head = base_head
        wn.add_pump(name='pump',
                    start_node_name=start_node,
                    end_node_name=end_node, pump_type='HEAD',
                    pump_parameter='curve1')

sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()
x = 1

# Plot results on the network
# pressure_at_5hr = results.node['pressure'].loc[4*3600, :]
# wntr.graphics.plot_network(wn, node_attribute=pressure_at_5hr, node_size=30, title='Pressure at 5 hours')
# plt.show()
