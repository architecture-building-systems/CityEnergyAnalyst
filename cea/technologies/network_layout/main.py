


import os
import pandas as pd

import cea.config
import cea.inputlocator
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network
from cea.technologies.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree
from cea.technologies.network_layout.substations_location import calc_building_centroids
from cea.technologies.constants import TYPE_MAT_DEFAULT, PIPE_DIAMETER_DEFAULT

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_buildings_with_district_system(locator, network_type):
    """
    Auto-detect buildings that have district heating or cooling systems defined in supply.csv

    :param locator: InputLocator instance
    :param network_type: 'DH' or 'DC'
    :return: List of building names with scale=DISTRICT for the specified network type
    """
    try:
        # Read supply.csv
        supply_systems = pd.read_csv(locator.get_building_supply())

        # Determine which supply type to check based on network type
        if network_type == 'DH':
            supply_type_col = 'supply_type_hs'
            assembly_file = locator.get_database_assemblies_supply_heating()
        elif network_type == 'DC':
            supply_type_col = 'supply_type_cs'
            assembly_file = locator.get_database_assemblies_supply_cooling()
        else:
            raise ValueError(f"Invalid network_type: {network_type}. Must be 'DH' or 'DC'.")

        # Read supply assemblies to get scale information
        supply_assemblies = pd.read_csv(assembly_file)

        # Merge to get scale for each building
        buildings_with_scale = supply_systems.merge(
            supply_assemblies[['code', 'scale']],
            left_on=supply_type_col,
            right_on='code',
            how='left'
        )

        # Filter buildings with DISTRICT scale
        district_buildings = buildings_with_scale[buildings_with_scale['scale'] == 'DISTRICT']['name'].tolist()

        return district_buildings

    except Exception as e:
        print(f"WARNING: Could not auto-detect district buildings from supply.csv: {e}")
        print("Proceeding with empty building list.")
        return []


def layout_network(network_layout, locator, plant_building_names=None, output_name_network="", optimization_flag=False):
    if plant_building_names is None:
        plant_building_names = []
    weight_field = 'Shape_Leng'
    total_demand_location = locator.get_total_demand()
    temp_path_potential_network_shp = locator.get_temporary_file("potential_network.shp")  # shapefile, location of output.
    temp_path_building_centroids_shp = locator.get_temporary_file("nodes_buildings.shp")

    # type_mat_default = network_layout.type_mat
    type_mat_default = TYPE_MAT_DEFAULT
    pipe_diameter_default = network_layout.pipe_diameter
    type_network = network_layout.network_type
    list_district_scale_buildings = network_layout.connected_buildings
    consider_only_buildings_with_demand = network_layout.consider_only_buildings_with_demand

    # Auto-detect buildings with district systems from supply.csv if no buildings specified
    if not list_district_scale_buildings:
        list_district_scale_buildings = get_buildings_with_district_system(locator, type_network)
        if list_district_scale_buildings:
            print(f"\nINFO: Auto-detected {len(list_district_scale_buildings)} buildings with district {type_network} from supply.csv:")
            print(f"  Buildings: {', '.join(list_district_scale_buildings)}")
            print(f"  To override this, specify buildings in the 'connected-buildings' parameter.\n")
        else:
            # Fallback to all buildings if none found with district scale
            print(f"\nWARNING: No buildings specified and none found with district {type_network} in supply.csv.")
            print(f"  Falling back to default behaviour: connecting ALL buildings in the scenario.")
            print(f"  To connect specific buildings, either:")
            print(f"    1. Set scale=DISTRICT in supply.csv for the desired buildings, OR")
            print(f"    2. Specify buildings using the 'connected-buildings' parameter.\n")
            # Leave list_district_scale_buildings as empty to trigger default behaviour downstream
            # The calc_building_centroids function will use all buildings when list is empty
    # allow_looped_networks = network_layout.allow_looped_networks
    allow_looped_networks = False
    steiner_algorithm = network_layout.algorithm

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_zone_shp = locator.get_zone_geometry()

    # Calculate points where the substations will be located (building centroids)
    building_centroids_df = calc_building_centroids(path_zone_shp,
                                                    temp_path_building_centroids_shp,
                                                    list_district_scale_buildings,
                                                    plant_building_names,
                                                    consider_only_buildings_with_demand,
                                                    type_network,
                                                    total_demand_location)

    # Calculate potential network
    crs_projected = calc_connectivity_network(path_streets_shp,
                                              building_centroids_df,
                                              path_potential_network=temp_path_potential_network_shp)

    # calc minimum spanning tree and save results to disk
    path_output_edges_shp = locator.get_network_layout_edges_shapefile(type_network, output_name_network)
    path_output_nodes_shp = locator.get_network_layout_nodes_shapefile(type_network, output_name_network)
    output_network_folder = locator.get_output_thermal_network_type_folder(type_network, output_name_network)

    disconnected_building_names = [x for x in list_district_scale_buildings if x not in list_district_scale_buildings]

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
                               allow_looped_networks,
                               optimization_flag,
                               plant_building_names,
                               disconnected_building_names,
                               steiner_algorithm)


class NetworkLayout(object):
    """Capture network layout information"""

    def __init__(self, network_layout=None):
        self.network_type = "DC"
        self.connected_buildings = []
        self.connected_buildings = network_layout.connected_buildings
        self.disconnected_buildings = []
        self.pipe_diameter = PIPE_DIAMETER_DEFAULT
        self.type_mat = TYPE_MAT_DEFAULT
        self.create_plant = True
        self.allow_looped_networks = False
        self.consider_only_buildings_with_demand = False

        self.algorithm = None

        attributes = ["network_type", "pipe_diameter", "type_mat", "create_plant", "allow_looped_networks",
                      "consider_only_buildings_with_demand", "connected_buildings", "disconnected_buildings",
                      "algorithm"]
        for attr in attributes:
            # copy any matching attributes in network_layout (because it could be an instance of NetworkInfo)
            if hasattr(network_layout, attr):
                setattr(self, attr, getattr(network_layout, attr))


def main(config: cea.config.Configuration):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_layout = NetworkLayout(network_layout=config.network_layout)
    plant_building_names = config.network_layout.plant_buildings

    layout_network(network_layout, locator, plant_building_names=plant_building_names)


if __name__ == '__main__':
    main(cea.config.Configuration())
