from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def network_plot(data_frame, title, output_path, analysis_fields):
    ''
    # read in edge node matrix
    df = data_frame['edge_node']
    # read in edge coordinates
    pos = data_frame['coordinates']
    for key in pos.keys():
        if isinstance(key, str):
            new_key = int(key.replace("NODE", ""))
            pos[new_key] = pos.pop(key)


    # identify number of plants and nodes
    plant_nodes = []
    for node, node_index in zip(df.index, range(len(df.index))):
        if max(df.ix[node]) <= 0:  # only -1 and 0 so plant!
            plant_nodes.append(node_index)
    # convert df to networkx type graph
    graph = nx.Graph()  # set up networkx type graph
    for i in range(df.shape[0]):
        new_edge = [0, 0]
        for j in range(0, df.shape[1]):
            if df.iloc[i][df.columns[j]] == 1:
                new_edge[0] = j
            elif df.iloc[i][df.columns[j]] == -1:
                new_edge[1] = j
        graph.add_edge(new_edge[0], new_edge[1], edge_number=i, Diameter = data_frame['Diameters'].ix['PIPE' + str(i)][0],
                       Loss= data_frame[analysis_fields[1]]['PIPE' + str(i)][3300])  # add edges to graph
    #todo: exchange 3300 with slider
    node_colors = []

    #pos = nx.spring_layout(graph)

    for node in graph.nodes():
        node_colors.append(data_frame[analysis_fields[0]]['NODE'+str(node)][3300])

    #nx.set_node_attributes(graph, 'pos', pos)

    #pos = nx.get_node_attributes(graph,'pos')
    Loss = [graph[u][v]['Loss'] for u,v in graph.edges()]
    Diameter = [graph[u][v]['Diameter'] for u,v in graph.edges()]
    Diameter = [i * 100 for i in Diameter]
    nodes = nx.draw_networkx_nodes(graph, pos, node_color=node_colors, with_labels=False,
                                   edge_cmap=plt.cm.hot)
    edges = nx.draw_networkx_edges(graph, pos, edge_color=Loss, width=Diameter,
                                   edge_cmap=plt.cm.autumn)
    plt.colorbar(nodes)
    plt.colorbar(edges)
    plt.axis('off')
    plt.show()
    plt.title(title)
    #todo: add hover labels
    plt.savefig(output_path)
