import matplotlib.pyplot as plt
import get_initial_network as gia
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning.pyomo_multi_linetype import initial_network
from cea.technologies.thermal_network.network_layout.substations_location import calc_substation_location
import re

__author__ =  "Thanh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def plot_complete(m, config, locator, network_number, generation):

    points_on_line, tranches, dict_length, dict_path = initial_network(config, locator)
    var_x = m.var_x.values()

    # Plotting Graph
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    # Plotting Buildings
    input_buildings_shp = locator.get_electric_substation_input_location()
    output_substations_shp = locator.get_electric_substation_output_location()
    building_points, building_poly = calc_substation_location(input_buildings_shp,output_substations_shp, [])
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

    plt.savefig(locator.get_concept_network_plot_complete(network_number, generation))


def plot_network_on_street(m, config, locator, network_number, generation):
    points_on_line, tranches, dict_length, dict_path = initial_network(config, locator)
    var_x = m.var_x.values()

    # Plotting Graph
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    ax1.axis('auto')
    ax1.set_aspect('equal')
    ax1.set_axis_off()
    ax2.set_axis_off()

    # Plotting Buildings
    input_buildings_shp = locator.get_electric_substation_input_location()
    output_substations_shp = locator.get_electric_substation_output_location()
    building_points, building_poly = calc_substation_location(input_buildings_shp, output_substations_shp, [])
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

    plt.savefig(locator.get_concept_network_on_streets(network_number, generation))


def plot_network(m, config, locator, network_number, generation):

    points_on_line, tranches, dict_length, dict_path = initial_network(config, locator)
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

    plt.savefig(locator.get_concept_network_plot(network_number, generation))
