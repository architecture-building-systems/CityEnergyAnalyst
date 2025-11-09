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
        network_type = parameters.get('network-type')

        # Return empty list if network type not selected yet
        if not network_type:
            return []

        # Get the network type folder
        network_type_folder = self.locator.get_output_thermal_network_type_folder(network_type, '')
        network_type_folder = network_type_folder.rstrip(os.sep)

        if not os.path.exists(network_type_folder):
            return []

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

        return available_networks

    def _get_network_layout_files(self, parameters):
        network_type = parameters.get('network-type', 'DC')
        network_name = parameters.get('network-name', '')

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
                    description="Name of the network layout to visualize",
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
            FileRequirement(
                "Network Layout",
                file_locator="layer:_get_network_layout_files",
                depends_on=["network-type", "network-name"],
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""
        network_type = parameters.get('network-type', 'DC')
        network_name = parameters.get('network-name', '')

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

        edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
        # Massflow files stored in network_name folder
        massflow_edges_path = self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)

        crs = get_geographic_coordinate_system()
        edges_df = gpd.read_file(edges_path).to_crs(crs).set_index("name")
        nodes_df = gpd.read_file(nodes_path).to_crs(crs).set_index("name")
        massflow_edges_df = pd.read_csv(massflow_edges_path)

        edges_df["peak_mass_flow"] = massflow_edges_df.max().round(1)

        output['nodes'] = json.loads(nodes_df.to_json())
        output['edges'] = json.loads(edges_df.to_json())

        return output
