from __future__ import division
import os

import cea.config
import cea.inputlocator
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network
from cea.technologies.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree
from cea.technologies.network_layout.substations_location import calc_building_centroids

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def layout_network(network_layout, locator, plant_building_names=None, output_name_network="", optimization_flag=False):

    # Local variables
    if plant_building_names is None:
        plant_building_names = []
    weight_field = 'Shape_Leng'
    total_demand_location = locator.get_total_demand()
    temp_path_potential_network_shp = locator.get_temporary_file("potential_network.shp")  # shapefile, location of output.
    temp_path_building_centroids_shp = locator.get_temporary_file("nodes_buildings.shp")

    type_mat_default = network_layout.type_mat
    pipe_diameter_default = network_layout.pipe_diameter
    type_network = network_layout.network_type
    create_plant = True #always create a plant or there will be errors in the thermal network simulation...
    list_district_scale_buildings = network_layout.connected_buildings
    consider_only_buildings_with_demand = network_layout.consider_only_buildings_with_demand
    allow_looped_networks = network_layout.allow_looped_networks

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_zone_shp = locator.get_zone_geometry()

    # Calculate points where the substations will be located (building centroids)
    building_centroids_df = calc_building_centroids(path_zone_shp,
                                                    temp_path_building_centroids_shp,
                                                    list_district_scale_buildings,
                                                    consider_only_buildings_with_demand,
                                                    type_network,
                                                    total_demand_location)

    # Calculate potential network
    crs_projected = calc_connectivity_network(path_streets_shp,
                                              building_centroids_df,
                                              temp_path_potential_network_shp)

    # calc minimum spanning tree and save results to disk
    path_output_edges_shp = locator.get_network_layout_edges_shapefile(type_network, output_name_network)
    path_output_nodes_shp = locator.get_network_layout_nodes_shapefile(type_network, output_name_network)
    output_network_folder = locator.get_input_network_folder(type_network, output_name_network)

    if list_district_scale_buildings != []:
        building_names = locator.get_zone_building_names()
        disconnected_building_names = [x for x in list_district_scale_buildings if x not in building_names]
    else:
        # if list_district_scale_buildings is left blank, we assume all buildings are connected (no disconnected buildings)
        disconnected_building_names = []
    calc_steiner_spanning_tree(crs_projected,
                               temp_path_potential_network_shp,
                               output_network_folder,
                               temp_path_building_centroids_shp,
                               path_output_edges_shp,
                               path_output_nodes_shp,
                               weight_field,
                               type_mat_default,
                               pipe_diameter_default,
                               type_network,
                               total_demand_location,
                               create_plant,
                               allow_looped_networks,
                               optimization_flag,
                               plant_building_names,
                               disconnected_building_names)


class NetworkLayout(object):
    """Capture network layout information"""

    def __init__(self, network_layout=None):
        self.network_type = "DC"
        self.connected_buildings = []
        self.disconnected_buildings = []
        self.pipe_diameter = 150
        self.type_mat = "T1"
        self.create_plant = True
        self.allow_looped_networks = False
        self.consider_only_buildings_with_demand = False

        attributes = ["network_type", "pipe_diameter", "type_mat", "create_plant", "allow_looped_networks",
                      "consider_only_buildings_with_demand", "connected_buildings", "disconnected_buildings"]
        for attr in attributes:
            # copy any matching attributes in network_layout (because it could be an instance of NetworkInfo)
            if hasattr(network_layout, attr):
                setattr(self, attr, getattr(network_layout, attr))


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_layout = NetworkLayout(network_layout=config.network_layout)
    layout_network(network_layout, locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
