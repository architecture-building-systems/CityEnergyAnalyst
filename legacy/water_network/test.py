import wntr
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
import random

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

    # create node catalogue indicating which nodes are plants and which consumers

    node_df.coordinates = pd.Series(node_df.coordinates)
    all_nodes_df = node_df[['Type', 'Building', 'coordinates']]
    all_nodes_df.to_csv(locator.get_thermal_network_node_types_csv_file(network_type, network_name))
    # extract the list of buildings in the current network
    building_names = all_nodes_df.Building[all_nodes_df.Type == 'CONSUMER'].reset_index(drop=True)

    # create first edge-node matrix
    list_pipes = edge_df.index.values
    list_nodes = node_df.index.values
    edge_node_matrix = np.zeros((len(list_nodes), len(list_pipes)))
    for j in range(len(list_pipes)):  # TODO: find ways to accelerate
        for i in range(len(list_nodes)):
            if edge_df['end node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif edge_df['start node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes,
                                columns=list_pipes)  # first edge-node matrix

    ## An edge node matrix is generated as a first guess and then virtual substation mass flows are imposed to
    ## calculate mass flows in each edge (mass_flow_guess).
    node_mass_flows_df = pd.DataFrame(data=np.zeros([1, len(edge_node_df.index)]), columns=edge_node_df.index)
    total_flow = 0
    number_of_plants = sum(all_nodes_df['Type'] == 'PLANT')

    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'CONSUMER':
            node_mass_flows_df[node] = 1  # virtual consumer mass flow requirement
            total_flow += 1
    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'PLANT':
            node_mass_flows_df[node] = - total_flow / number_of_plants  # virtual plant supply mass flow

    # The direction of flow is then corrected
    # keep track if there was a change for the iterative process
    pd.options.mode.chained_assignment = None  # avoid warnings of copies
    changed = [True] * node_mass_flows_df.shape[1]
    while any(changed):
        for i in range(node_mass_flows_df.shape[1]):
            # we have a plant with incoming mass flows, or we don't have a plant but only exiting mass flows
            if ((node_mass_flows_df[node_mass_flows_df.columns[i]].min() < 0) and (
                    edge_node_df.iloc[i].max() > 0)) or \
                    ((node_mass_flows_df[node_mass_flows_df.columns[i]].min() >= 0) and (
                            edge_node_df.iloc[i].max() <= 0)):
                j = np.nonzero(edge_node_df.iloc[i])[0]
                if len(j) > 1:  # valid if e.g. if more than one flow and all flows incoming. Only need to flip one.
                    j = random.choice(j)
                edge_node_df[edge_node_df.columns[j]] = -edge_node_df[edge_node_df.columns[j]]
                new_nodes = [edge_df['end node'][j], edge_df['start node'][j]]
                edge_df['start node'][j] = new_nodes[0]
                edge_df['end node'][j] = new_nodes[1]
                changed[i] = True
            else:
                changed[i] = False
    return edge_df, edge_node_df, node_df

import cea.inputlocator
import cea.config

config = cea.config.Configuration()
locator = cea.inputlocator.InputLocator(scenario=config.scenario)

# add options for data sources: heating or cooling network, csv or shp
network_type = config.thermal_network.network_type  # set to either 'DH' or 'DC'
file_type = config.thermal_network.file_type  # set to csv or shp

# this does a rule of max and min flow to set a diameter. if false it takes the input diameters
set_diameter = config.thermal_network.set_diameter  # boolean
network_names = config.thermal_network.network_names
network_name = ''
edge_df, edge_node_df, node_df = get_thermal_network_from_shapefile(locator, network_type, network_name)

# Create a water network model
wn = wntr.network.WaterNetworkModel()

#add loads
wn.add_pattern('pat1', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
wn.add_pattern('pat2', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

lenght_edges = edge_df.shape[0]
# add nodes
for node in node_df.iterrows():
    if node[1]["Type"] == "CONSUMER":
        base_demand = 100
        demand_pattern = 'pat2'
        wn.add_junction(node[0], base_demand=base_demand, demand_pattern=demand_pattern, elevation=0, coordinates=node[1]["coordinates"])
    elif node[1]["Type"] == "PLANT":
        reservoir_pattern = 'pat1'
        wn.add_reservoir(node[0], base_head=100000, head_pattern=reservoir_pattern, coordinates=node[1]["coordinates"])
    else:
        base_demand = 0
        demand_pattern = 'pat2'
        wn.add_junction(node[0], base_demand=base_demand, demand_pattern=demand_pattern, elevation=0, coordinates=node[1]["coordinates"])

# add pipes
for edge in edge_df.iterrows():
    length = edge[1]["pipe length"]
    wn.add_pipe(edge[0], edge[1]["start node"], edge[1]["end node"], length=length, diameter=0.3048, roughness=100, minor_loss=0.0, status='OPEN')

#add options
wn.options.time.duration = 24*3600
wn.options.time.hydraulic_timestep = 15*60
wn.options.time.pattern_timestep = 60*60

# Graph the network
# wntr.graphics.plot_network(wn, title=wn.name)

# Simulate hydraulics
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()

# Plot results on the network
# pressure_at_5hr = results.node['pressure'].loc[4*3600, :]
# wntr.graphics.plot_network(wn, node_attribute=pressure_at_5hr, node_size=30, title='Pressure at 5 hours')
# plt.show()