from __future__ import division

import geopandas as gpd
import wntr
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load


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
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3
import pandas as pd
from cea.technologies.thermal_network.substation_matrix import  determine_building_supply_temperatures
import cea.technologies.substation as substation

config = cea.config.Configuration()
locator = cea.inputlocator.InputLocator(scenario=config.scenario)

# add options for data sources: heating or cooling network, csv or shp
network_type = config.thermal_network.network_type  # set to either 'DH' or 'DC'
network_name = ''

#GET INFORMATION ABOUT THE NETWORK
edge_df, node_df = get_thermal_network_from_shapefile(locator, network_type, network_name)


#GET INFORMATION ABOUT THE DEMAND OF BUILDINGS AND CONNECT TO THE NODE INFO
substation_cooling_systems = ["ahu", "aru", "scu"]
substation_heating_systems = ["ahu", "aru", "shu", "ww"]
substation_systems = {'heating': substation_heating_systems if network_type == "DH" else [],
                      'cooling': substation_cooling_systems if network_type == "DC" else []}

building_names = locator.get_zone_building_names()
#calculate substations for all buildings
# local variables
total_demand = pd.read_csv(locator.get_total_demand())
volume_flow_m3pers_building = {}
if network_type == "DH":
    buildings_name_with_heating = get_building_names_with_load(total_demand, load_name='QH_sys_MWhyr')
    buildings_name_with_space_heating = get_building_names_with_load(total_demand, load_name='Qhs_sys_MWhyr')
    DHN_barcode = "111111thermalnetwork"
    if (buildings_name_with_heating != [] and buildings_name_with_space_heating != []):
        building_names = buildings_name_with_heating
        substation.substation_main_heating(locator, total_demand, building_names, DHN_barcode=DHN_barcode)
    else:
        raise Exception('problem here')

    for building_name in building_names:
        substation_results = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DH", DHN_barcode))
        volume_flow_m3pers_building[building_name] = substation_results["mdot_DH_result_kgpers"] / P_WATER_KGPERM3

if network_type == "DC":
    buildings_name_with_cooling = get_building_names_with_load(total_demand, load_name='QC_sys_MWhyr')
    DCN_barcode = "111111thermalnetwork"
    if buildings_name_with_cooling != []:
        building_names = buildings_name_with_cooling
        substation.substation_main_cooling(locator, total_demand, building_names, DCN_barcode=DCN_barcode)
    else:
        raise Exception('problem here')

    for building_name in building_names:
        substation_results = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", DCN_barcode))
        volume_flow_m3pers_building[building_name] = substation_results["mdot_DH_result_kgpers"] / P_WATER_KGPERM3

# Create a water network model
wn = wntr.network.WaterNetworkModel()

# add loads
for building in volume_flow_m3pers_building.keys():
    wn.add_pattern(building, volume_flow_m3pers_building['B1014'].tolist())
coefficient_friction_hanzen_williams = 100
thermal_transfer_unit_design_head_m = 2.5 #half as we duplicate the pressure needs to calculate the pumping needs

# add nodes
for node in node_df.iterrows():
    if node[1]["Type"] == "CONSUMER":
        base_demand_m3s = 1 # it gets multiplied by the demand
        demand_pattern = node[1]['Building']
        wn.add_junction(node[0],
                        base_demand=base_demand_m3s,
                        demand_pattern=demand_pattern,
                        elevation=thermal_transfer_unit_design_head_m,
                        coordinates=node[1]["coordinates"])
    elif node[1]["Type"] == "PLANT":
        base_head = 10000
        start_node = node[0]
        name_node_plant = start_node
        end_node = edge_df[edge_df['start node'] == start_node]['end node'].values[0]
        wn.add_reservoir(start_node,
                         base_head=base_head,
                         coordinates=node[1]["coordinates"])
    else:
        wn.add_junction(node[0],
                        elevation=0,
                        coordinates=node[1]["coordinates"])

# add pipes
for edge in edge_df.iterrows():
    length = edge[1]["pipe length"]
    edge_name = edge[0]
    wn.add_pipe(edge_name, edge[1]["start node"],
                edge[1]["end node"],
                length=length,
                roughness=coefficient_friction_hanzen_williams,
                minor_loss=0.0,
                status='OPEN')

# add options
wn.options.time.duration = 24 * 3600 * 365
wn.options.time.hydraulic_timestep = 60 * 60
wn.options.time.pattern_timestep = 60 * 60
velocity_ms = 3

lequivalent_length_factor = 0.2

#1st ITERATION GET MASS FLOWS AND CALCULATE DIAMETER
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()
max_volume_flow_rates_m3s = results.link['flowrate'].abs().max()
pipe_names = max_volume_flow_rates_m3s.index.values
diameter_m = pd.Series(np.vectorize(calc_max_diameter)(max_volume_flow_rates_m3s, velocity_ms=velocity_ms), pipe_names)

#2nd ITERATION GET PRESSURE POINTS AND MASSFLOWS FOR SIZING PUMPING NEEDS - this could be for all the year
#modify diameter and run simualtions
for edge in edge_df.iterrows():
    edge_name = edge[0]
    pipe = wn.get_link(edge_name)
    pipe.diameter = diameter_m[edge_name]
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()



#3d ITERATION GET FINAL UTILIZATION OF THE GRID (SUPPLY SIDE)
#get accumulated heat loss per hour
unitary_head_loss_ftperkft = results.link['headloss'].abs()
unitary_head_loss_m_l = unitary_head_loss_ftperkft * 0.30487 / 304.87
head_loss_m = unitary_head_loss_m_l.copy()
for column in head_loss_m.columns.values:
    length = edge_df.loc[column]['pipe length']
    head_loss_m[column] = head_loss_m[column] * length
accumulated_head_loss_m = head_loss_m.sum(axis=1) + thermal_transfer_unit_design_head_m * len(building_names)

#apply this pattern to the reservoir
base_head = 1
pattern = accumulated_head_loss_m.tolist()
wn.add_pattern('reservoir', pattern)
end_node = edge_df[edge_df['start node'] == name_node_plant]['end node'].values[0]
reservoir = wn.get_node(name_node_plant)
reservoir.head_timeseries.base_value = int(base_head)
pat = wn.get_pattern('reservoir')
reservoir.head_timeseries._pattern = 'reservoir'
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()
x=1
# Plot results on the network
# pressure_at_5hr = results.node['pressure'].loc[4*3600, :]
# wntr.graphics.plot_network(wn, node_attribute=pressure_at_5hr, node_size=30, title='Pressure at 5 hours')
# plt.show()
