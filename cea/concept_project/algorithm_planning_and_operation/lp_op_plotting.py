import matplotlib.pyplot as plt
import get_initial_network as gia
import re
from lp_op_config import *
import matplotlib.lines as mlines
import matplotlib

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Settings
font = {
    'family': 'Arial',
    'weight': 'regular',
    'size': 13
}
matplotlib.rc('font', **font)
marker_size = 6


def initial_network():
    gia.calc_substation_location()
    df_nodes, tranches = gia.connect_building_to_grid()
    df_nodes_processed = gia.process_network(df_nodes)
    dict_length, dict_path = gia.create_length_dict(df_nodes_processed, tranches)

    return df_nodes_processed, tranches, dict_length, dict_path


def plot_nodes(df_nodes, ax):
    # Plot Nodes
    for idx, point in df_nodes.iterrows():
        name = str(point['Name'][4::])

        if point['Type'] == 'PLANT':
            ax.plot(point.geometry.xy[0], point.geometry.xy[1], marker='s', color='red', markersize=marker_size)
            # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)
        elif point['Type'] == 'CONSUMER':
            ax.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=marker_size)
            # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)
        # else:
        #     ax.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=marker_size)
        #     # ax.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

    return ax


def plot_lines_on_street(var_x, dict_path, df_nodes, ax):
    for x in var_x:
        if x.value > 0.5 or PLOT_ALL_LINES_ON_STREETS:
            node_int = re.findall(r'\d+', x.local_name)

            start_node = int(node_int[0])
            end_node = int(node_int[1])

            list_path = dict_path[start_node][end_node]

            for idx_path, path in enumerate(list_path[:-1]):
                int_node1 = list_path[idx_path]
                int_node2 = list_path[idx_path + 1]

                geo_node1 = df_nodes.loc[int_node1].geometry.xy
                geo_node2 = df_nodes.loc[int_node2].geometry.xy

                if PLOT_ALL_LINES_ON_STREETS:
                    edge_color = 'black'
                else:
                    if int(node_int[2]) < len(PLOT_COLORS):
                        edge_color = PLOT_COLORS[int(node_int[2])]
                    else:
                        edge_color = 'black'


                ax.plot((geo_node1[0][0], geo_node2[0][0]),
                        (geo_node1[1][0], geo_node2[1][0]),
                        color=edge_color)

    return ax


def plot_lines(var_x, df_nodes, ax):
    for x in var_x:
        if x.value > 0.5:
            node_int = re.findall(r'\d+', x.local_name)

            int_node1 = int(node_int[0])
            int_node2 = int(node_int[1])

            geo_node1 = df_nodes.loc[int_node1].geometry.xy
            geo_node2 = df_nodes.loc[int_node2].geometry.xy

            edge_color = None

            if int(node_int[2]) < len(PLOT_COLORS):
                edge_color = PLOT_COLORS[int(node_int[2])]
            else:
                edge_color = 'black'

            ax.plot((geo_node1[0][0], geo_node2[0][0]),
                    (geo_node1[1][0], geo_node2[1][0]),
                    color=edge_color)

    return ax


def plot_network_on_street(m):
    if SCENARIO == '/newcase/med/':
        df_nodes, tranches, dict_length, dict_path = initial_network()
    else:
        df_nodes, tranches, dict_length, dict_path = initial_network()

    var_x = m.var_x.values()

    # Plotting Graph
    fig, ax = plt.subplots(1, 1)

    ax.axis('auto')
    ax.set_aspect('equal')
    ax.set_axis_off()

    ax = plot_lines_on_street(var_x, dict_path, df_nodes, ax)

    # Plotting Buildings
    building_points, building_poly = gia.calc_substation_location()
    building_poly.plot(ax=ax, color='white', edgecolor='grey')
    for x, y, name in zip(building_points.geometry.x, building_points.geometry.y, building_points['Name']):
        ax.text(x, y, name, fontsize=8, horizontalalignment='center')

    # Plotting Nodes
    ax = plot_nodes(df_nodes, ax)
    plt.tight_layout()

    # Get legend entries
    legend_items = [
        mlines.Line2D([], [], linestyle='', marker='s', color='red', markersize=marker_size, label='Substation\nconnection'),
        mlines.Line2D([], [], linestyle='', marker='o', color='green', markersize=marker_size, label='Building\nconnection'),
        # mlines.Line2D([], [], linestyle='', marker='o', color='blue', markersize=marker_size, label='Street\nintersection')
    ]
    for line_type in m.set_linetypes:
        legend_items.append(
            mlines.Line2D([], [], color=PLOT_COLORS[int(line_type)], label='Linetype {}'.format(line_type))
        )

    # Add legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    plt.legend(handles=legend_items, loc='center', bbox_to_anchor=(1.1, 0.45))

    return fig


def plot_network(m):
    df_nodes, tranches, dict_length, dict_path = initial_network()

    var_x = m.var_x.values()

    # Plotting Graph
    fig, ax = plt.subplots(1, 1)

    ax.axis('auto')
    ax.set_aspect('equal')
    ax.set_axis_off()

    ax = plot_lines(var_x, df_nodes, ax)

    # Plotting Nodes
    ax = plot_nodes(df_nodes, ax)
    plt.tight_layout()

    # Get legend entries
    legend_items = [
        mlines.Line2D([], [], linestyle='', marker='s', color='red', markersize=marker_size, label='Substation\nconnection'),
        mlines.Line2D([], [], linestyle='', marker='o', color='green', markersize=marker_size, label='Building\nconnection'),
        # mlines.Line2D([], [], linestyle='', marker='o', color='blue', markersize=marker_size, label='Street\nintersection')
    ]
    for line_type in m.set_linetypes:
        legend_items.append(
            mlines.Line2D([], [], color=PLOT_COLORS[int(line_type)], label='Linetype {}'.format(line_type))
        )

    # Add legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    plt.legend(handles=legend_items, loc='center', bbox_to_anchor=(1.1, 0.45))

    return fig


def plot_building_peaks(m):
    pass
