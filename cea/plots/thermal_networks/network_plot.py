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

    if str(analysis_fields[0]).split("_")[0] == 'Tnode':
        label = "T [K] "
    elif str(analysis_fields[0]).split("_")[0] == 'Pnode':
        label = "P [kPa] "
    else:
        label = ""


    # identify number of plants and nodes
    plant_nodes = []
    for node, node_index in zip(df.index, range(len(df.index))):
        if max(df.ix[node]) <= 0:  # only -1 and 0 so plant!
            plant_nodes.append(node_index)
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
        diameter_data = data_frame['Diameters'].ix['PIPE' + str(i)][0]
        loss_data = data_frame[analysis_fields[1]]['PIPE' + str(i)]
        #loss_data[loss_data == 0] = np.nan
        loss_data = np.nanmean(loss_data)
        graph.add_edge(new_edge[0], new_edge[1], edge_number=i, Diameter = diameter_data,
                       Loss= loss_data,
                       edge_label = 'Edge '+str(i)+"\n D: "+str(np.round(diameter_data*100,1))
                       +" cm \n Loss: "+str(np.round(loss_data,2))+" kWh")  # add edges to graph
    #todo: exchange average with slider


    node_colors = {}
    for node in graph.nodes():
        data = data_frame[analysis_fields[0]]['NODE'+str(node)]
        node_colors[node]=np.nanmean(data)
    nx.set_node_attributes(graph, 'node_colors', node_colors)

    #pos = nx.get_node_attributes(graph,'pos')
    Loss = [graph[u][v]['Loss'] for u,v in graph.edges()]
    Diameter = [graph[u][v]['Diameter'] for u,v in graph.edges()]
    Diameter = [i * 100 for i in Diameter]
    edge_number = dict([((u,v),d['edge_label']) for u,v,d in graph.edges(data=True)])
    node_colors = [graph.node[u]['node_colors'] for u in graph.nodes()]

    plt.figure(figsize=(18, 18))
    nodes = nx.draw_networkx_nodes(graph, pos, node_color=node_colors, with_labels=True,
                                   edge_cmap=plt.cm.autumn)
    edges = nx.draw_networkx_edges(graph, pos, edge_color=Loss, with_labels = True,  width=Diameter,
                                   edge_cmap=plt.cm.autumn)
    for node in graph.nodes():
        x, y = pos[node]
        plt.text(x, y + 10, s="Node "+str(node) +"\n" + label +": "
                              +str(np.round(node_colors[node],0)),
                 bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'), horizontalalignment='center')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_number, bbox=dict(facecolor='white',
                                                                                alpha=0.85,
                                                                                edgecolor='none'))

    plt.colorbar(nodes, label=label, aspect=50, pad=0, fraction=0.09)
    plt.colorbar(edges, label = 'Loss [kWh]', aspect=50, pad=0, fraction =0.09)
    plt.axis('off')
    plt.title(title)
    plt.savefig(output_path,  bbox_inches="tight")