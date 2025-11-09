import json

import pandas as pd
import geopandas as gpd

from cea.interfaces.dashboard.map_layers.base import MapLayer, ParameterDefinition, FileRequirement, cache_output
from cea.interfaces.dashboard.map_layers.thermal_network import ThermalNetworkCategory
from cea.plots.colors import color_to_hex
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system


class ThermalNetworkMapLayer(MapLayer):
    category = ThermalNetworkCategory
    name = "thermal-network"
    label = "Thermal Network"
    description = "Thermal Network Design"

    _network_types = ["DC", "DH"]

    def _get_network_types(self):
        return self._network_types

    def _get_legacy_file_path(self, network_type, filename):
        """Get path to legacy file directly under network_type folder (not in layout/)"""
        import os
        network_type_folder = self.locator.get_output_thermal_network_type_folder(network_type, '')
        return os.path.join(network_type_folder.rstrip(os.sep), filename)

    def _migrate_legacy_network(self, network_type):
        """
        Migrate legacy network structure to new structure.
        Old: DC/edges.shp, DC/nodes.shp, root/DC__*.csv
        New: DC/existing_network/layout/edges.shp, DC/existing_network/DC_existing_network_*.csv
        """
        import os
        import shutil
        import glob

        try:
            # Check if old structure exists (edges.shp directly under network_type folder)
            old_edges_path = self._get_legacy_file_path(network_type, 'edges.shp')
            old_nodes_path = self._get_legacy_file_path(network_type, 'nodes.shp')

            if not os.path.exists(old_edges_path) or not os.path.exists(old_nodes_path):
                return  # No legacy structure found

            print(f"[ThermalNetworkMapLayer] Detected legacy network structure for {network_type}, migrating...")

            # Create new structure with network name "existing_network"
            new_network_name = "existing_network"

            # Get new paths using InputLocator
            new_edges_path = self.locator.get_network_layout_edges_shapefile(network_type, new_network_name)
            new_nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, new_network_name)
            new_network_folder = self.locator.get_output_thermal_network_type_folder(network_type, new_network_name)
            new_layout_folder = os.path.dirname(new_edges_path)

            # Create layout folder
            os.makedirs(new_layout_folder, exist_ok=True)

            # Move edges.shp and all related files (.shx, .dbf, .prj, .cpg)
            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                old_file = self._get_legacy_file_path(network_type, f'edges{ext}')
                if os.path.exists(old_file):
                    new_file = new_edges_path.replace('.shp', ext)
                    print(f"[ThermalNetworkMapLayer] Moving {old_file} -> {new_file}")
                    shutil.move(old_file, new_file)

            # Move nodes.shp and all related files
            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                old_file = self._get_legacy_file_path(network_type, f'nodes{ext}')
                if os.path.exists(old_file):
                    new_file = new_nodes_path.replace('.shp', ext)
                    print(f"[ThermalNetworkMapLayer] Moving {old_file} -> {new_file}")
                    shutil.move(old_file, new_file)

            # Migrate Part 2 results from root folder (with double underscore pattern)
            thermal_network_root = self.locator.get_thermal_network_folder()
            old_pattern = f"{network_type}__*.csv"
            old_files = glob.glob(os.path.join(thermal_network_root, old_pattern))

            # Define mapping of suffixes to InputLocator methods for Part 2 files
            part2_file_methods = {
                'massflow_edges_kgs.csv': 'get_thermal_network_layout_massflow_edges_file',
                'velocity_edges_ms.csv': 'get_thermal_network_velocity_edges_file',
                'massflow_nodes_kgs.csv': 'get_thermal_network_layout_massflow_nodes_file',
                'temperature_supply_nodes_C.csv': 'get_network_temperature_supply_nodes_file',
                'temperature_return_nodes_C.csv': 'get_network_temperature_return_nodes_file',
                'temperature_plant_C.csv': 'get_network_temperature_plant',
                'pressure_losses_edges_kW.csv': 'get_thermal_network_pressure_losses_edges_file',
                'pressure_losses_substations_kW.csv': 'get_thermal_network_substation_ploss_file',
                'thermal_demand_per_building_W.csv': 'get_thermal_demand_csv_file',
                'thermal_loss_edges_kW.csv': 'get_network_thermal_loss_edges_file',
                'linear_thermal_loss_edges_Wperm.csv': 'get_network_linear_thermal_loss_edges_file',
                'total_thermal_loss_edges_kW.csv': 'get_network_total_thermal_loss_file',
                'pressure_at_nodes_Pa.csv': 'get_network_pressure_at_nodes',
                'total_pressure_drop_Pa.csv': 'get_network_total_pressure_drop_file',
                'linear_pressure_drop_Paperm.csv': 'get_network_linear_pressure_drop_edges',
                'plant_pumping_pressure_loss_Pa.csv': 'get_network_energy_pumping_requirements_file',
                'plant_heat_requirement_kW.csv': 'get_thermal_network_plant_heat_requirement_file',
            }

            for old_file in old_files:
                # Extract suffix from old filename: DC__massflow_edges_kgs.csv -> massflow_edges_kgs.csv
                old_filename = os.path.basename(old_file)
                suffix = old_filename.replace(f"{network_type}__", "")

                # Try to find matching InputLocator method
                if suffix in part2_file_methods:
                    # Use InputLocator method to get new path
                    method_name = part2_file_methods[suffix]
                    method = getattr(self.locator, method_name)
                    new_file = method(network_type, new_network_name)

                    print(f"[ThermalNetworkMapLayer] Moving {old_file} -> {new_file}")
                    shutil.move(old_file, new_file)
                else:
                    # Fallback: construct path manually if method not found
                    new_filename = f"{network_type}_{new_network_name}_{suffix}"
                    new_file = os.path.join(new_network_folder, new_filename)
                    print(f"[ThermalNetworkMapLayer] Moving (fallback) {old_file} -> {new_file}")
                    shutil.move(old_file, new_file)

            print(f"[ThermalNetworkMapLayer] Successfully migrated legacy network to {new_network_folder}")

        except Exception as e:
            print(f"[ThermalNetworkMapLayer] Error migrating legacy network: {e}")
            import traceback
            traceback.print_exc()

    def _has_part2_results(self, network_type, network_name):
        """Check if a network has at least one Part 2 result file (massflow is the key indicator)"""
        import os
        # Check for massflow file as indicator that Part 2 has been run
        massflow_path = self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)
        return os.path.exists(massflow_path)

    def _get_network_names(self, parameters):
        """Get list of available network layouts for the selected network type"""
        import os
        try:
            network_type = parameters.get('network-type')

            print(f"[ThermalNetworkMapLayer] _get_network_names called with network_type={network_type}")

            # Return placeholder option if network type not selected yet
            if not network_type:
                print(f"[ThermalNetworkMapLayer] No network type provided, returning placeholder")
                return ["No network available"]

            # Get the network type folder
            network_type_folder = self.locator.get_output_thermal_network_type_folder(network_type, '')
            network_type_folder = network_type_folder.rstrip(os.sep)

            if not os.path.exists(network_type_folder):
                print(f"[ThermalNetworkMapLayer] Network type folder doesn't exist: {network_type_folder}, returning placeholder")
                return ["No network available"]

            # Check for and migrate legacy network structure
            self._migrate_legacy_network(network_type)

            # List subdirectories that contain valid network files in layout/ subfolder (both edges and nodes required)
            # AND have Part 2 results (massflow file must exist)
            available_networks = []
            for item in os.listdir(network_type_folder):
                item_path = os.path.join(network_type_folder, item)
                if os.path.isdir(item_path):
                    # Check for layout files using InputLocator methods
                    edges_path = self.locator.get_network_layout_edges_shapefile(network_type, item)
                    nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, item)

                    # Check if both layout files exist AND Part 2 results exist
                    if os.path.exists(edges_path) and os.path.exists(nodes_path):
                        if self._has_part2_results(network_type, item):
                            available_networks.append(item)
                        else:
                            print(f"[ThermalNetworkMapLayer] Network {item} has layout files but no Part 2 results, skipping")

            # Sort by folder name (most recent timestamp first)
            available_networks.sort(reverse=True)

            print(f"[ThermalNetworkMapLayer] Found {len(available_networks)} networks: {available_networks}")

            # If no networks found, return a placeholder option
            # This allows the frontend to proceed with an empty selection and show the base layer without network
            if not available_networks:
                print(f"[ThermalNetworkMapLayer] No networks found, returning placeholder option")
                return ["No network available"]

            return available_networks

        except Exception as e:
            print(f"[ThermalNetworkMapLayer] Error in _get_network_names: {e}")
            import traceback
            traceback.print_exc()
            return ["No network available"]

    def _get_network_layout_files(self, parameters):
        network_type = parameters.get('network-type', 'DC')
        network_name = parameters.get('network-name', '')

        # Handle None, undefined, or empty string
        if network_name is None or network_name == 'undefined':
            network_name = ''

        return [
            self.locator.get_network_layout_edges_shapefile(network_type, network_name),
            self.locator.get_network_layout_nodes_shapefile(network_type, network_name),
            # Massflow files stored in network_name folder
            self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name),
        ]

    # TODO: Add width parameter
    @classmethod
    def expected_parameters(cls):
        return {
            'network-type':
                ParameterDefinition(
                    "Network Type",
                    "string",
                    description="Type of the network",
                    options_generator="_get_network_types",
                    selector="choice",
                ),
            'network-name':
                ParameterDefinition(
                    "Network Name",
                    "string",
                    default="",
                    description="Name of the network layout to visualize (leave empty to show base layer only)",
                    selector="choice",
                    depends_on=["network-type"],
                    options_generator="_get_network_names",
                ),
            'scale':
                ParameterDefinition(
                    "Scale",
                    "number",
                    default=1,
                    description="Scale of pipe width",
                    selector="input",
                    range=[0.1, 100],
                    filter="scale",
                ),
        }

    @classmethod
    def file_requirements(cls):
        return [
            FileRequirement(
                "Zone Buildings Geometry",
                file_locator="locator:get_zone_geometry",
            ),
            # Network layout files are optional - layer will return empty data if not available
            # FileRequirement(
            #     "Network Layout",
            #     file_locator="layer:_get_network_layout_files",
            #     depends_on=["network-type", "network-name"],
            # ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""
        import os

        network_type = parameters.get('network-type', 'DC')
        network_name = parameters.get('network-name', '')

        # Handle None, undefined, empty string, or placeholder value
        if network_name is None or network_name == 'undefined' or network_name == 'No network available':
            network_name = ''

        print(f"[ThermalNetworkMapLayer] generate_data called with network_type={network_type}, network_name='{network_name}'")

        if network_type not in self._network_types:
            raise ValueError(f"Invalid network type: {network_type}")

        primary_colour = color_to_hex("blue") if network_type == "DC" else color_to_hex("red")

        output = {
            "nodes": None,
            "edges": None,
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
                "colours": {
                    "edges": primary_colour,
                    "nodes": {
                        "plant": primary_colour,
                        "consumer": color_to_hex("white"),
                    }
                }
            }
        }

        # Return empty data if no network is selected
        if not network_name:
            print(f"[ThermalNetworkMapLayer] No network name provided, returning empty output")
            return output

        try:
            edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
            nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
            # Massflow files stored in network_name folder
            massflow_edges_path = self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)

            # Return empty data if files don't exist
            if not os.path.exists(edges_path) or not os.path.exists(nodes_path):
                print(f"[ThermalNetworkMapLayer] Network files don't exist at {edges_path}, returning empty output")
                return output

            print(f"[ThermalNetworkMapLayer] Loading network from {edges_path}")
            crs = get_geographic_coordinate_system()
            edges_df = gpd.read_file(edges_path).to_crs(crs).set_index("name")
            nodes_df = gpd.read_file(nodes_path).to_crs(crs).set_index("name")

            # Only load massflow data if it exists (Part 2 may not have been run yet)
            if os.path.exists(massflow_edges_path):
                print(f"[ThermalNetworkMapLayer] Loading massflow from {massflow_edges_path}")
                massflow_edges_df = pd.read_csv(massflow_edges_path)
                edges_df["peak_mass_flow"] = massflow_edges_df.max().round(1)
            else:
                print(f"[ThermalNetworkMapLayer] Massflow file doesn't exist, skipping")

            output['nodes'] = json.loads(nodes_df.to_json())
            output['edges'] = json.loads(edges_df.to_json())

            print(f"[ThermalNetworkMapLayer] Successfully loaded network with {len(nodes_df)} nodes and {len(edges_df)} edges")
            return output

        except Exception as e:
            print(f"[ThermalNetworkMapLayer] Error loading network: {e}")
            import traceback
            traceback.print_exc()
            # Return empty output instead of crashing
            return output
