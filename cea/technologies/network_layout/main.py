import os

import geopandas as gpd
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


def get_buildings_from_supply_csv(locator, network_type):
    """
    Read supply.csv and return list of buildings configured for district heating/cooling.

    :param locator: InputLocator instance
    :param network_type: "DH" or "DC"
    :return: List of building names
    """
    supply_df = pd.read_csv(locator.get_building_supply())

    # Read assemblies database to map codes to scale (DISTRICT vs BUILDING)
    if network_type == "DH":
        assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_heating())
        system_type_col = 'supply_type_hs'
    else:  # DC
        assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_cooling())
        system_type_col = 'supply_type_cs'

    # Create mapping: code -> scale (DISTRICT/BUILDING)
    scale_mapping = assemblies_df.set_index('code')['scale'].to_dict()

    # Filter buildings with DISTRICT scale
    supply_df['scale'] = supply_df[system_type_col].map(scale_mapping)
    district_buildings = supply_df[supply_df['scale'] == 'DISTRICT']['name'].tolist()

    return district_buildings


def get_buildings_with_demand(locator, network_type):
    """
    Read total_demand.csv and return list of buildings with heating/cooling demand.

    :param locator: InputLocator instance
    :param network_type: "DH" or "DC"
    :return: List of building names
    """
    total_demand = pd.read_csv(locator.get_total_demand())

    if network_type == "DH":
        field = "QH_sys_MWhyr"
    else:  # DC
        field = "QC_sys_MWhyr"

    buildings_with_demand = total_demand[total_demand[field] > 0.0]['name'].tolist()
    return buildings_with_demand


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
    # allow_looped_networks = network_layout.allow_looped_networks
    allow_looped_networks = False
    steiner_algorithm = network_layout.algorithm

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_zone_shp = locator.get_zone_geometry()

    # Calculate points where the substations will be located (building centroids)
    building_centroids_df = calc_building_centroids(
        path_zone_shp,
        list_district_scale_buildings,
        plant_building_names,
        consider_only_buildings_with_demand,
        type_network,
        total_demand_location,
    )
    
    street_network_df = gpd.GeoDataFrame.from_file(path_streets_shp)

    # Calculate potential network
    potential_network_df = calc_connectivity_network(street_network_df, building_centroids_df)
    potential_network_df.to_file(temp_path_potential_network_shp, driver='ESRI Shapefile')
    crs_projected = potential_network_df.crs

    if crs_projected is None:
        raise ValueError("The CRS of the potential network shapefile is undefined. Please check if the input street network has a defined projection system.")

    # Save building centroids with projected crs
    building_centroids_df.to_crs(crs_projected).to_file(temp_path_building_centroids_shp, driver='ESRI Shapefile')

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

    # Check if user provided custom network layout
    edges_shp = config.network_layout.user_edges_shp_path
    nodes_shp = config.network_layout.user_nodes_shp_path
    geojson_path = config.network_layout.user_network_geojson_path

    if edges_shp or nodes_shp or geojson_path:
        print("\n" + "=" * 80)
        print("USER-DEFINED NETWORK LAYOUT")
        print("=" * 80 + "\n")

        # Import validation functions from user_network_loader
        from cea.optimization_new.user_network_loader import (
            load_user_defined_network,
            validate_network_covers_district_buildings
        )

        # Load and validate user-defined network
        try:
            result = load_user_defined_network(config, locator)
            if result is None:
                raise ValueError("User network loading returned None")
            nodes_gdf, edges_gdf = result

            print(f"  - Nodes: {len(nodes_gdf)}")
            print(f"  - Edges: {len(edges_gdf)}")

            network_type = config.network_layout.network_type
            overwrite_supply = config.network_layout.overwrite_supply_settings
            connected_buildings_config = config.network_layout.connected_buildings

            # Determine which buildings should be in the network
            if overwrite_supply:
                # Use connected-buildings parameter (what-if scenarios)
                if connected_buildings_config:
                    buildings_to_validate = connected_buildings_config
                    print(f"  - Mode: Overwrite supply.csv (using connected-buildings parameter)")
                    print(f"  - Connected buildings: {len(buildings_to_validate)}")
                else:
                    # Blank connected-buildings: use buildings with demand
                    buildings_to_validate = get_buildings_with_demand(locator, network_type)
                    print(f"  - Mode: Overwrite supply.csv (connected-buildings blank)")
                    print(f"  - Buildings with demand: {len(buildings_to_validate)}")
            else:
                # Use supply.csv to determine district buildings
                buildings_to_validate = get_buildings_from_supply_csv(locator, network_type)
                print(f"  - Mode: Use supply.csv settings")
                print(f"  - District buildings from supply.csv: {len(buildings_to_validate)}")

            # Check for buildings without demand and warn (Option 2: warn but include)
            buildings_with_demand = get_buildings_with_demand(locator, network_type)
            buildings_without_demand = [b for b in buildings_to_validate if b not in buildings_with_demand]

            if buildings_without_demand:
                print(f"  ⚠ Warning: {len(buildings_without_demand)} building(s) have no {network_type} demand:")
                for building_name in buildings_without_demand[:10]:
                    print(f"      - {building_name}")
                if len(buildings_without_demand) > 10:
                    print(f"      ... and {len(buildings_without_demand) - 10} more")
                print(f"  Note: These buildings will be included in layout but may not be simulated in thermal-network")

            # Validate network covers all specified buildings
            if buildings_to_validate:
                nodes_gdf, auto_created_buildings = validate_network_covers_district_buildings(
                    nodes_gdf,
                    gpd.read_file(locator.get_zone_geometry()),
                    buildings_to_validate,
                    network_type,
                    edges_gdf
                )

                if auto_created_buildings:
                    print(f"  ⚠ Auto-created {len(auto_created_buildings)} missing building node(s):")
                    for building_name in auto_created_buildings[:10]:
                        print(f"      - {building_name}")
                    if len(auto_created_buildings) > 10:
                        print(f"      ... and {len(auto_created_buildings) - 10} more")
                    print("  Note: Nodes created at edge endpoints closest to building centroids (in-memory only)")
                else:
                    print("  ✓ All specified buildings have valid nodes in network")
            else:
                print("  ⚠ Warning: No buildings to validate (empty building list)")
                print("  Note: Network will be saved but may not work in thermal-network or optimization")

            # Save to standard location
            output_edges_path = locator.get_network_layout_edges_shapefile(network_type)
            output_nodes_path = locator.get_network_layout_nodes_shapefile(network_type)

            # Ensure output directory exists
            output_folder = os.path.dirname(output_edges_path)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Save to shapefiles
            edges_gdf.to_file(output_edges_path, driver='ESRI Shapefile')
            nodes_gdf.to_file(output_nodes_path, driver='ESRI Shapefile')

            print(f"\n  ✓ User-defined network saved to:")
            print(f"    {output_folder}")
            print("\n" + "=" * 80 + "\n")

        except Exception as e:
            print(f"\n✗ Error loading user-defined network: {e}\n")
            print("=" * 80 + "\n")
            raise
    else:
        # Generate network layout using Steiner tree (current behavior)
        layout_network(network_layout, locator, plant_building_names=plant_building_names)


if __name__ == '__main__':
    main(cea.config.Configuration())
