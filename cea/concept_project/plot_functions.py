import matplotlib.pyplot as plt
import get_initial_network as gia
import re

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def initial_network(config, locator):
    gia.calc_substation_location(config, locator)
    points_on_line, tranches = gia.connect_building_to_grid(config, locator)
    points_on_line_processed = gia.process_network(points_on_line, config, locator)
    dict_length, dict_path = gia.create_length_dict(points_on_line_processed, tranches)

    return points_on_line_processed, tranches, dict_length, dict_path


def plot_complete(m):
    points_on_line, tranches, dict_length, dict_path = initial_network()
    var_x = m.var_x.values()

    # Plotting Graph
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    # Plotting Buildings
    building_points, building_poly = gia.calc_substation_location()
    building_poly.plot(ax=ax1, color='white', edgecolor='grey')

    for x in var_x:
        node_int = re.findall(r'\d+', x.local_name)

        start_node = int(node_int[0])
        end_node = int(node_int[1])
        type = int(node_int[1])

        list_path = dict_path[start_node][end_node]

        for idx_path, path in enumerate(list_path[:-1]):
            int_node1 = list_path[idx_path]
            int_node2 = list_path[idx_path + 1]

            geo_node1 = points_on_line.loc[int_node1].geometry.xy
            geo_node2 = points_on_line.loc[int_node2].geometry.xy

            ax1.plot((geo_node1[0][0],
                      geo_node2[0][0]),
                     (geo_node1[1][0],
                      geo_node2[1][0]),
                     color='grey')

        print start_node, end_node, type

    for idx, point in points_on_line.iterrows():
        name = str(point['Name'][4::])

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
        else:  # intersection
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

        ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

    plt.show()


def plot_network_on_street(m):
    points_on_line, tranches, dict_length, dict_path = initial_network()
    var_x = m.var_x.values()

    # Plotting Graph
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    # Plotting Buildings
    building_points, building_poly = gia.calc_substation_location()
    building_poly.plot(ax=ax1, color='white', edgecolor='grey')

    # Plotting Lines
    for x in var_x:
        if x.value > 0.5:
            node_int = re.findall(r'\d+', x.local_name)

            start_node = int(node_int[0])
            end_node = int(node_int[1])
            linetype = int(node_int[2])

            list_path = dict_path[start_node][end_node]

            for idx_path, path in enumerate(list_path[:-1]):
                int_node1 = list_path[idx_path]
                int_node2 = list_path[idx_path + 1]

                geo_node1 = points_on_line.loc[int_node1].geometry.xy
                geo_node2 = points_on_line.loc[int_node2].geometry.xy

                edge_color = None

                if int(node_int[2]) == 0:
                    edge_color = 'green'
                elif int(node_int[2]) == 1:
                    edge_color = 'yellow'
                elif int(node_int[2]) == 2:
                    edge_color = 'red'

                ax1.plot((geo_node1[0][0], geo_node2[0][0]),
                         (geo_node1[1][0], geo_node2[1][0]),
                         color=edge_color)

            print start_node, end_node, linetype

    for idx, point in points_on_line.iterrows():
        name = str(point['Name'][4::])

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
        # else:  # intersection
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

        ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)

    plt.show()


def plot_network(m):
    points_on_line, tranches, dict_length, dict_path = initial_network()
    var_x = m.var_x.values()

    # Plotting Graph
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    for x in var_x:
        if x.value > 0.5:
            node_int = re.findall(r'\d+', x.local_name)

            int_node1 = int(node_int[0])
            int_node2 = int(node_int[1])

            geo_node1 = points_on_line.loc[int_node1].geometry.xy
            geo_node2 = points_on_line.loc[int_node2].geometry.xy

            edge_color = None

            if int(node_int[2]) == 0:
                edge_color = 'green'
            elif int(node_int[2]) == 1:
                edge_color = 'yellow'
            elif int(node_int[2]) == 2:
                edge_color = 'red'

            ax1.plot((geo_node1[0][0], geo_node2[0][0]),
                     (geo_node1[1][0], geo_node2[1][0]),
                     color=edge_color)

    for idx, point in points_on_line.iterrows():
        name = str(point['Name'][4::])

        if point['Type'] == 'PLANT':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='red', markersize=5)
            ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)
        elif point['Type'] == 'CONSUMER':
            ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='green', markersize=5)
            ax1.text(point.geometry.xy[0][0], point.geometry.xy[1][0], name, fontsize=8)
        # else:  # intersection
        #     ax1.plot(point.geometry.xy[0], point.geometry.xy[1], marker='o', color='blue', markersize=5)

    plt.show()