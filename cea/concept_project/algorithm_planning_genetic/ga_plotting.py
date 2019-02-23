import matplotlib.pyplot as plt
import time
import numpy as np
from ga_config import *
import get_initial_network as gia


def plot_network(df_nodes, tranches, idx_edge, dict_path, ind, y_range, fig, (ax1, ax2)):

    # Plotting Graph
    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()

    for idx_gene, gene in enumerate(ind):
        if gene > 0:
            start_node = idx_edge[idx_gene][0]
            end_node = idx_edge[idx_gene][1]

            list_path = dict_path[start_node][end_node]

            for idx_path, path in enumerate(list_path[:-1]):
                int_node1 = list_path[idx_path]
                int_node2 = list_path[idx_path+1]

                geo_node1 = df_nodes.loc[int_node1].geometry.xy
                geo_node2 = df_nodes.loc[int_node2].geometry.xy

                ax1.plot((geo_node1[0][0],
                         geo_node2[0][0]),
                         (geo_node1[1][0],
                         geo_node2[1][0]),
                         color='black')

            # centroid = line.values[0].centroid
            # length = str(round(line.values[0].length, 1))

            # ax1.plot(point1, point2, color='black')
            # ax.text(centroid.x, centroid.y, name, fontsize=10)
            # ax.text(centroid.x, centroid.y, length, fontsize=10)

    for idx, point in df_nodes.iterrows():
        # name = str(point['Name'])
        # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
        else:  # intersection
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

    # for idx, point in building_points.iterrows():
    #     ax.plot(point.geometry.xy[0], point.geometry.xy[1], marker='s', color='red', markersize=10)

    x_range = np.arange(N_GENERATIONS+1)
    # Plotting Fitness
    ax2.axis('auto')
    # ax2.set_aspect('equal')
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Minimal Cost of Networks')
    ax2.set_xlim([0, N_GENERATIONS])

    ax2.bar(x_range, y_range, color='black', width=1)
    # ax2.set_xticks(x_range)


def plot_complete(df_nodes, tranches, ind, y_range, fig, (ax1, ax2)):
    locater = 'C:/reference-case-WTP/MIX_high_density/'
    building_points, building_poly = gia.calc_substation_location(locater)

    # Plotting Graph
    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    # ax2.set_axis_off()

    # building_poly.plot(ax=ax1, color='white', edgecolor='grey')

    # for idx, point in building_points.iterrows():
    #     ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='s', color='purple', markersize=8)

    for gene_idx, gene in enumerate(ind):
        line = tranches.loc[gene_idx]

        point1 = line.values[0].xy[0]
        point2 = line.values[0].xy[1]
        centroid = line.values[0].centroid
        length = str(round(line.values[0].length, 1))
        name = str(line['Name'][6:])

        ax1.plot(point1, point2, color='black')
        # ax1.plot(point1, point2)

        # ax1.text(centroid.x, centroid.y, name, fontsize=10)
        # ax1.text(centroid.x, centroid.y, length, fontsize=10)

    for idx, point in df_nodes.iterrows():
        # name = str(point['Name'])
        # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
        else:  # intersection
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

    x_range = np.arange(N_GENERATIONS+1)
    # Plotting Fitness
    ax2.axis('auto')
    # ax2.set_aspect('equal')
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Minimal Cost of Networks')
    ax2.set_xlim([0, N_GENERATIONS])

    ax2.bar(x_range, y_range, color='black', width=1)
    # ax2.set_xticks(x_range)


def plot_network_on_street_save(df_nodes, tranches, idx_edge, dict_path, ind):

    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    # Plotting Graph
    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    for idx_gene, gene in enumerate(ind):
        if gene > 0:
            start_node = idx_edge[idx_gene][0]
            end_node = idx_edge[idx_gene][1]

            list_path = dict_path[start_node][end_node]

            for idx_path, path in enumerate(list_path[:-1]):
                int_node1 = list_path[idx_path]
                int_node2 = list_path[idx_path+1]

                geo_node1 = df_nodes.loc[int_node1].geometry.xy
                geo_node2 = df_nodes.loc[int_node2].geometry.xy

                ax1.plot((geo_node1[0][0],
                         geo_node2[0][0]),
                         (geo_node1[1][0],
                         geo_node2[1][0]),
                         color='black')

            # centroid = line.values[0].centroid
            # length = str(round(line.values[0].length, 1))

            # ax1.plot(point1, point2, color='black')
            # ax.text(centroid.x, centroid.y, name, fontsize=10)
            # ax.text(centroid.x, centroid.y, length, fontsize=10)

    for idx, point in df_nodes.iterrows():
        # name = str(point['Name'])
        # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
        # else:  # intersection
        #     ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

    # for idx, point in building_points.iterrows():
    #     ax.plot(point.geometry.xy[0], point.geometry.xy[1], marker='s', color='red', markersize=10)

    # Plotting Buildings
    building_points, building_poly = gia.calc_substation_location()
    building_poly.plot(ax=ax1, color='white', edgecolor='grey')


def plot_network_graph_save(df_nodes, tranches, idx_edge, dict_path, ind):
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    # Plotting Graph
    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    for idx_gene, gene in enumerate(ind):
        if gene > 0:
            int_node1 = idx_edge[idx_gene][0]
            int_node2 = idx_edge[idx_gene][1]

            geo_node1 = df_nodes.loc[int_node1].geometry.xy
            geo_node2 = df_nodes.loc[int_node2].geometry.xy

            edge_color = 'black'

            ax1.plot((geo_node1[0][0], geo_node2[0][0]),
                     (geo_node1[1][0], geo_node2[1][0]),
                     color=edge_color)

            # centroid = line.values[0].centroid
            # length = str(round(line.values[0].length, 1))

            # ax1.plot(point1, point2, color='black')
            # ax.text(centroid.x, centroid.y, name, fontsize=10)
            # ax.text(centroid.x, centroid.y, length, fontsize=10)

    for idx, point in df_nodes.iterrows():
        # name = str(point['Name'])
        # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
        # else:  # intersection
        #     ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

    # for idx, point in building_points.iterrows():
    #     ax.plot(point.geometry.xy[0], point.geometry.xy[1], marker='s', color='red', markersize=10)