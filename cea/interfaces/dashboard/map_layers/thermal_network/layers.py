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

    def _get_network_names(self, parameters):
        """Get list of available network layouts for the selected network type"""
        import os
        try:
            network_type = parameters.get('network-type')

            print(f"[ThermalNetworkMapLayer] _get_network_names called with network_type={network_type}")

            # Return placeholder option if network type not selected yet
            if not network_type:
                print(f"[ThermalNetworkMapLayer] No network type provided, returning placeholder")
                return [""]

            # Get the network type folder
            network_type_folder = self.locator.get_output_thermal_network_type_folder(network_type, '')
            network_type_folder = network_type_folder.rstrip(os.sep)

            if not os.path.exists(network_type_folder):
                print(f"[ThermalNetworkMapLayer] Network type folder doesn't exist: {network_type_folder}, returning placeholder")
                return [""]

            # List subdirectories that contain valid network files in layout/ subfolder (both edges and nodes required)
            available_networks = []
            for item in os.listdir(network_type_folder):
                item_path = os.path.join(network_type_folder, item)
                if os.path.isdir(item_path):
                    # Check for layout files using InputLocator methods
                    edges_path = self.locator.get_network_layout_edges_shapefile(network_type, item)
                    nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, item)

                    if os.path.exists(edges_path) and os.path.exists(nodes_path):
                        available_networks.append(item)

            # Sort by folder name (most recent timestamp first)
            available_networks.sort(reverse=True)

            print(f"[ThermalNetworkMapLayer] Found {len(available_networks)} networks: {available_networks}")

            # If no networks found, return a placeholder empty string option
            # This allows the frontend to proceed with an empty selection and show the base layer without network
            if not available_networks:
                print(f"[ThermalNetworkMapLayer] No networks found, returning placeholder empty string option")
                return [""]

            return available_networks

        except Exception as e:
            print(f"[ThermalNetworkMapLayer] Error in _get_network_names: {e}")
            import traceback
            traceback.print_exc()
            return [""]

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

        # Handle None, undefined, or empty string
        if network_name is None or network_name == 'undefined':
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
