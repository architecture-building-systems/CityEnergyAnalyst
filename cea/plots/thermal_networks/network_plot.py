from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def network_plot(data_frame, title, output_path, analysis_fields, demand_data, all_nodes):
    # iterate through all input data, make sure we have positive data. Except for edge node matrix which ahs to retain -1 values
    for key in data_frame.keys():
        if isinstance(data_frame[key], pd.DataFrame) and key != 'edge_node':  # use only absolute values
            data_frame[key] = data_frame[key].abs()
    # save original demand data and output path for later use
    demand_data_original = demand_data.copy()
    original_output_path = output_path
    # Check if this is the network layout plot, set a flag
    if 'Network Layout' in title:
        is_layout_plot = True
        T_flag = False
    else:
        is_layout_plot = False

    # Two plot types with aggregated and peak values for the non layout plot
    if is_layout_plot:
        plots = ['']
    else:
        plots = ['aggregated', 'peak']
    # iterate through plot types
    for type in plots:
        demand_data = demand_data_original.copy()  # read in demand data
        output_path = original_output_path
        if not is_layout_plot:
            output_path = output_path.replace('.png',
                                              '') + type + '.png'  # refactor string to reset it to correct output path
        # read in edge node matrix
        df = data_frame['edge_node']
        # read in edge coordinates
        pos = data_frame['coordinates']
        # iterate through all nodes
        for key in pos.keys():
            if isinstance(key, str):
                new_key = int(key.replace("NODE", ""))
                pos[new_key] = pos.pop(key)  # reformate keys to contain numbers only
        if not is_layout_plot:
            if str(analysis_fields[0]).split("_")[
                0] == 'Tnode':  # we are running the thermal plot since we have temperature data
                label = "T "  # label for legend
                if type == 'aggregated':  # aggregated plot
                    bar_label = 'Average Supply Temperature Nodes [deg C]'
                    bar_label_2 = 'Aggregated Pipe Heat Loss [kWh_th]'
                else:  # peak data plot
                    bar_label = 'Peak Supply Temperature Nodes [deg C]'
                    bar_label_2 = 'Peak Pipe Heat Loss [kW_th]'
                T_flag = True  # indicator for later that we are plotting the temperature data
            elif str(analysis_fields[0]).split("_")[0] == 'P':  # plotting hydraulic information of network
                label = "P En"
                if type == 'aggregated':  # aggregated plot
                    bar_label = 'Aggregated Pumping Energy Buildings [kWh_el]'
                    bar_label_2 = 'Aggregated Pumping Energy Pipes [kWh_el]'
                else:  # peak data plot
                    bar_label = 'Peak Pumping Energy Buildings [kW_el]'
                    bar_label_2 = 'Peak Pumping Energy Pipes [kW_el]'
                T_flag = False  # indicator for later that we are not plotting the temperature data
            else:
                label = ""
                T_flag = False

        # convert df to networkx type graph
        df = np.transpose(df)  # transpose matrix to more intuitively setup graph
        graph = nx.Graph()  # set up networkx type graph
        for i in range(df.shape[0]):
            new_edge = [0, 0]
            for j in range(0, df.shape[1]):
                if df.iloc[i][df.columns[j]] == 1:
                    new_edge[0] = j
                elif df.iloc[i][df.columns[j]] == -1:
                    new_edge[1] = j
            diameter_data = data_frame['Diameters'].ix[i][0]  # read in pipe diameters
            if not is_layout_plot:
                loss_data = data_frame[analysis_fields[1]][
                    data_frame[analysis_fields[1]].columns[i]]  # read in relevant loss data
                loss_data[loss_data == 0] = np.nan  # setup to find average without 0 elements
                if type == 'aggregated':  # plotting aggregated data
                    loss_data = np.nansum(loss_data)
                else:  # plotting peak data
                    loss_data = np.nanmax(abs(loss_data))
                loss_data = np.nan_to_num(
                    loss_data)  # just in case one edge was always 0, replace nan with 0 so that plot looks ok
                # add edges to graph with complete edge label and diameter data included
                graph.add_edge(new_edge[0], new_edge[1], edge_number=i, Diameter=diameter_data,
                               Loss=loss_data, edge_label='')
            else:
                DN_data = data_frame['DN'].ix[i]  # read in pipe diameters
                graph.add_edge(new_edge[0], new_edge[1], edge_number=i, Diameter=diameter_data,
                               edge_label=str(data_frame['Diameters'].index[i]) + "\n DN: " + str(
                                   int(DN_data)))
        # adapt node indexes to match real node numbers. E.g. if some node numbers are missing
        new_nodes = {}
        # iterate through all nodes
        for key_index in range(len(graph.nodes())):
            new_nodes[sorted(graph.nodes())[key_index]] = int(sorted(pos.keys())[key_index])
        nx.relabel_nodes(graph, new_nodes, copy=False)

        # rename demand data columns to match graph nodes
        new_columns = []
        for building in demand_data.columns:  # check if we have a demand at this building
            if all_nodes['Building'].isin([building]).any():
                index = np.where(building == all_nodes['Building'])[0][0]
                new_columns.append(all_nodes['Name'][index].replace("NODE", ""))
            else:
                demand_data = demand_data.drop(building, 1)  # delete since this building is not in our network
        demand_data.columns = new_columns

        # find plant nodes
        plant_nodes = []
        for node in df.columns:
            if max(df[node]) <= 0:  # only -1 and 0 so plant!
                plant_nodes.append(int(node.replace("NODE", "")))

        node_demand = {}
        # color nodes according to node attributes
        if not is_layout_plot:
            node_colors = {}

            for node in graph.nodes():
                if "NODE" + str(node) in data_frame[analysis_fields[0]].columns:
                    data = data_frame[analysis_fields[0]]["NODE" + str(node)]
                else:
                    node_index = np.where(all_nodes['Name'] == "NODE" + str(node))[0]
                    if len(node_index) == 1:
                        building = str(all_nodes['Building'][node_index].values[0])
                        if building in data_frame[analysis_fields[0]].columns:
                            data = data_frame[analysis_fields[0]][building]
                        else:
                            data = np.ndarray([0])
                    else:
                        data = np.ndarray([0])
                data[data == 0] = np.nan
                if type == "aggregated":
                    if T_flag:
                        node_colors[node] = np.nanmean(abs(data))  # show average supply temperature
                    else:
                        node_colors[node] = np.nansum(abs(data))
                else:
                    if T_flag:
                        if 'DC' in title:  # DC network so use minimum supply temperature
                            node_colors[node] = np.nanmin(data)
                        else:  # DH so use maximum supply temperature
                            node_colors[node] = np.nanmax(data)
                    else:
                        if len(data) > 0:
                            node_colors[node] = np.nanmax(data)
                        else:
                            node_colors[node] = np.nan
                        if np.isnan(node_colors[node]):
                            node_colors[node] = 0.0
            nx.set_node_attributes(graph, name='node_colors', values=node_colors)

        for node in graph.nodes():
            # store demand data for node sizing
            if str(node) in demand_data.columns:
                if np.nanmax(abs(demand_data[str(node)])) > 0:
                    node_demand[node] = np.nanmax(abs(demand_data[str(node)]))
                else:
                    node_demand[node] = 210  # 300 is the default node size, chose smaller to show lower relevance
            else:  # no demand at this node, NONE building
                node_demand[node] = 210  # 300 is the default node size

        nx.set_node_attributes(graph, name='node_demand', values=node_demand)

        # create lists of all losses, diameters, edge numbers, demands and node colors (temp. plots)
        if not is_layout_plot:
            Loss = [graph[u][v]['Loss'] for u, v in graph.edges()]
        Diameter = [graph[u][v]['Diameter'] for u, v in graph.edges()]
        Diameter = [i * 100 for i in Diameter]
        if is_layout_plot:
            edge_number = dict([((u, v), d['edge_label']) for u, v, d in graph.edges(data=True)])

        if not is_layout_plot:
            node_colors = [graph.node[u]['node_colors'] for u in graph.nodes()]
        peak_demand = [graph.node[u]['node_demand'] for u in graph.nodes()]

        # create figure
        fig, ax = plt.subplots(1, 1, figsize=(18, 18))

        if not is_layout_plot:
            nodes = nx.draw_networkx_nodes(graph, pos, node_color=node_colors, with_labels=True,
                                           edge_cmap=plt.cm.Blues, node_size=peak_demand)
        else:
            nodes = nx.draw_networkx_nodes(graph, pos, node_color='orange', with_labels=True,
                                           node_size=peak_demand)

        if not is_layout_plot:
            edges = nx.draw_networkx_edges(graph, pos, edge_color=Loss, width=Diameter,
                                           edge_cmap=plt.cm.Oranges)
        else:
            edges = nx.draw_networkx_edges(graph, pos, edge_color='gray', with_labels=True, width=Diameter)

        y_list = []
        for node, node_index in zip(graph.nodes(), range(len(graph.nodes()))):
            x, y = pos[node]
            y_list.append(y)
        y_range = max(y_list) - min(y_list)  # range of y coordinates of all nodes
        # setup building names list
        building_names = pd.DataFrame(all_nodes['Building'])
        building_names = building_names.set_index(all_nodes['Name'])

        # set text with node information
        for node, node_index in zip(graph.nodes(), range(len(graph.nodes()))):
            peak_demand = graph.node[node]['node_demand']
            if not is_layout_plot:
                node_colors = graph.node[node]['node_colors']
            x, y = pos[node]
            if node in plant_nodes:
                if T_flag:
                    text = 'Plant\n' + label + ': ' + str(np.round(node_colors, 0))
                else:
                    text = 'Plant'
            else:
                if peak_demand != 210:  # not the default value which is chosen if node has no demand
                    if is_layout_plot:
                        if str(building_names.ix['NODE' + str(node)].tolist()[0]) != 'NONE':
                            text = str(building_names.ix['NODE' + str(node)].tolist()[0])
                        else:
                            text = ''
                    else:
                        if str(building_names.ix['NODE' + str(node)].tolist()[0]) != 'NONE':
                            text = label + ": " + str(
                                np.round(node_colors, 1)) + "\nDem: " + str(
                                np.round(peak_demand, 0))
                        else:
                            text = ''
                else:  # no node demand, none type
                    if is_layout_plot:
                        if str(building_names.ix['NODE' + str(node)].tolist()[0]) != 'NONE':
                            text = str(building_names.ix['NODE' + str(node)].tolist()[0])
                        else:
                            text = ''
                    else:
                        if str(building_names.ix['NODE' + str(node)].tolist()[0]) != 'NONE':
                            text = label + ": " + str(np.round(node_colors, 0)) + '\nDem: 0'
                        else:
                            text = ''
            if text:
                plt.text(x, y + y_range / 40, text,
                         bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'),
                         horizontalalignment='center')
        # add edge labels
        if is_layout_plot:
            nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_number, bbox=dict(facecolor='white',
                                                                                        alpha=0.7,
                                                                                        edgecolor='none'))
        # create label text
        if is_layout_plot:
            legend_text = 'DN = Pipe Diameter'
        else:
            if T_flag:
                if type == 'aggregated':
                    legend_text = 'T = Average Supply Temperature [deg C]\n Dem = Peak Building Demand [kW] \n For detailed loss information see the energy_loss_bar diagram'
                else:
                    legend_text = 'T = Peak Supply Temperature [deg C]\n Dem = Peak Building Demand [kW]'
            else:
                if type == 'aggregated':
                    legend_text = 'P En = Aggregate Pumping Energy at Building [kWh]\n Dem = Peak Building Demand [kW] \n For detailed loss information see the energy_loss_bar diagram'
                else:
                    legend_text = 'P En = Peak Pumping Energy at Building [kW]\n Dem = Peak Building Demand [kW]'

        if not is_layout_plot:
            # add colorbars
            plt.colorbar(nodes, label=bar_label, aspect=50, pad=0, fraction=0.09, shrink=0.8)
            plt.colorbar(edges, label=bar_label_2, aspect=50, pad=0, fraction=0.09, shrink=0.8)
        plt.text(0.90, 0.02, s=legend_text, fontsize=14,
                 bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'), horizontalalignment='center',
                 verticalalignment='center', transform=ax.transAxes)
        plt.axis('off')
        if not is_layout_plot:
            if type == 'aggregated':
                plt.title('Aggregated' + title, fontsize=18)
            else:
                plt.title('Peak' + title, fontsize=18)
        else:
            plt.title(title, fontsize=18)
        plt.tight_layout()
        plt.savefig(output_path)
