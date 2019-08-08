import os

import cea.config
import cea.globalvar
import cea.inputlocator
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network
from cea.technologies.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree
from cea.technologies.network_layout.substations_location import calc_substation_location

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def network_layout(config, locator, plant_building_names=[], input_path_name='streets', output_name_network="",
                   optimization_flag=False):
    # Local variables
    weight_field = 'Shape_Leng'
    total_demand_location = locator.get_total_demand()
    path_potential_network = locator.get_temporary_file("potential_network.shp")  # shapefile, location of output.

    type_mat_default = config.network_layout.type_mat
    pipe_diameter_default = config.network_layout.pipe_diameter
    type_network = config.network_layout.network_type
    create_plant = config.network_layout.create_plant
    connected_buildings = config.network_layout.connected_buildings
    consider_only_buildings_with_demand = config.network_layout.consider_only_buildings_with_demand
    disconnected_buildings = config.network_layout.disconnected_buildings

    if input_path_name == 'streets':  # point to default location of streets file
        path_streets_shp = locator.get_street_network()  # shapefile with the stations
        input_buildings_shp = locator.get_zone_geometry()
        output_substations_shp = locator.get_temporary_file("nodes_buildings.shp")
        # Calculate points where the substations will be located
        calc_substation_location(input_buildings_shp, output_substations_shp, connected_buildings,
                                 consider_only_buildings_with_demand, type_network, total_demand_location)
    elif input_path_name == 'electrical_grid':  # point to location of electrical grid
        path_streets_shp = locator.get_electric_network_output_location(input_path_name)
        output_substations_shp = locator.get_electric_substation_output_location()
    else:
        raise Exception("the value of the variable input_path_name is not valid")

    # Calculate potential network
    crs_projected = calc_connectivity_network(path_streets_shp, output_substations_shp,
                                              path_potential_network)

    # calc minimum spanning tree and save results to disk
    output_edges = locator.get_network_layout_edges_shapefile(type_network, output_name_network)
    output_nodes = locator.get_network_layout_nodes_shapefile(type_network, output_name_network)
    output_network_folder = locator.get_input_network_folder(type_network, output_name_network)

    calc_steiner_spanning_tree(crs_projected, path_potential_network, output_network_folder, output_substations_shp,
                               output_edges, output_nodes, weight_field, type_mat_default, pipe_diameter_default,
                               type_network, total_demand_location, create_plant,
                               config.network_layout.allow_looped_networks, optimization_flag, plant_building_names,
                               disconnected_buildings)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_layout(config, locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
