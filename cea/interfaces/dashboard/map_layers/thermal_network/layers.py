import glob
import os
import json
import shutil

import pandas as pd
import geopandas as gpd

from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.map_layers.base import MapLayer, ParameterDefinition, FileRequirement, cache_output
from cea.interfaces.dashboard.map_layers.thermal_network import ThermalNetworkCategory
from cea.plots.colors import color_to_hex
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system


logger = getCEAServerLogger("ThermalNetworkMapLayer")


class ThermalNetworkMapLayer(MapLayer):
    category = ThermalNetworkCategory
    name = "thermal-network"
    label = "Thermal Network"
    description = "Thermal Network Design"

    _network_types = ["DC", "DH"]
    _default_network_name = "baseline"

    def _get_network_types(self):
        # Return both choices and default (DC is default)
        return {"choices": self._network_types, "default": self._network_types[0]}

    def _migrate_old_format(self, network_folder):
        # Check if the old format exists
        if not any(os.path.exists(os.path.join(network_folder, network_type)) for network_type in self._network_types):
            return

        network_name = self._default_network_name
        if os.path.exists(os.path.join(network_folder, network_name)):
            # Default network folder already exists, no need to migrate
            return

        for network_type in self._network_types:
            # Migrate old layout folder {network_folder}/DC to new folder e.g. {network_folder}/baseline/DC/
            old_layout_folder = os.path.join(network_folder, network_type)
            if os.path.exists(old_layout_folder):
                new_layout_folder = os.path.join(network_folder, network_name)
                os.makedirs(new_layout_folder, exist_ok=True)
                shutil.move(old_layout_folder, new_layout_folder)
            
            # Migrate old results files {network_folder}/DC__*.csv to new name e.g. {network_folder}/DC_baseline_*.csv
            old_results_files = glob.glob(os.path.join(network_folder, f"{network_type}__*.csv"))
            for old_results_file in old_results_files:
                filename = os.path.basename(old_results_file)
                new_filename = filename.replace(f"{network_type}__", f"{network_type}_{network_name}_", 1)
                new_results_file = os.path.join(network_folder, new_filename)
                shutil.move(old_results_file, new_results_file)
        
        logger.debug(f"Migrated old thermal network format in {network_folder} to new format.")

    def _check_valid_network(self, network_name: str, network_type: str):
        """Check if a network nodes and edges files exist for the given network type"""
        edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
        return os.path.exists(edges_path) and os.path.exists(nodes_path)
    
    def _check_potential_network(self, network_name: str, network_type: str):
        """Check if a potential network layout and network nodes exist for the given network type"""
        layout_path = self.locator.get_network_layout_shapefile(network_name)
        nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
        return os.path.exists(layout_path) and os.path.exists(nodes_path)

    def _get_network_names(self, parameters):
        """Get list of available network layouts for the selected network type"""
        try:
            network_folder = self.locator.get_thermal_network_folder()
            # Try to migrate old format if detected
            self._migrate_old_format(network_folder)

            network_type = parameters.get('network-type')

            # Return placeholder option if network type not selected yet
            if not network_type:
                return ["No network available"]

            available_networks = []
            for file in os.listdir(network_folder):
                # Ignore old format files
                if not os.path.isdir(os.path.join(network_folder, file)) or file.startswith(".") or any(file.startswith(nt) for nt in self._network_types):
                    continue

                network_name = file
                # Check if valid network or potential network exists
                if self._check_valid_network(network_name, network_type) or self._check_potential_network(network_name, network_type):
                    nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
                    mod_time = os.path.getmtime(nodes_path)
                    available_networks.append((network_name, mod_time))

            # Sort by folder name (most recent timestamp first)
            available_networks.sort(reverse=True)

            logger.debug(f"Found {len(available_networks)} networks: {available_networks}")

            # If no networks found, return a placeholder option
            if not available_networks:
                logger.debug("No networks found, returning placeholder option")
                return {"choices": ["No network available"], "default": "No network available"}

            # Return both choices and default (most recent network)
            choices = [name for name, _ in available_networks]
            print(choices)
            return {"choices": choices, "default": choices[0]}

        except Exception as e:
            logger.error(f"Error in _get_network_names: {e}")
            return {"choices": ["No network available"], "default": "No network available"}

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
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')

        # Handle None, undefined, empty string, or placeholder value
        if network_name is None or network_name == 'undefined' or network_name == 'No network available':
            raise ValueError("No valid network name provided")

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

        layout_path = self.locator.get_network_layout_shapefile(network_name)
        edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
        massflow_edges_path = self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)

        # Decide which files to load: either the full network (edges + nodes) or potential layout + nodes
        _edges_path = edges_path
        if not self._check_valid_network(network_name, network_type) and self._check_potential_network(network_name, network_type):
            logger.debug(f"Valid network files don't exist for {network_name} ({network_type}), loading potential layout instead.")
            _edges_path = layout_path
        else:
            logger.debug(f"Network files don't exist at {edges_path}.")
            return output

        logger.debug(f"Loading network from {_edges_path}")
        crs = get_geographic_coordinate_system()
        edges_df = gpd.read_file(_edges_path).to_crs(crs).set_index("name")
        nodes_df = gpd.read_file(nodes_path).to_crs(crs).set_index("name")

        # Only load massflow data if it exists
        if os.path.exists(massflow_edges_path):
            logger.debug(f"Loading massflow from {massflow_edges_path}")
            massflow_edges_df = pd.read_csv(massflow_edges_path)
            edges_df["peak_mass_flow"] = massflow_edges_df.max().round(1)
        else:
            logger.debug("Massflow file doesn't exist, skipping")

        output['nodes'] = json.loads(nodes_df.to_json())
        output['edges'] = json.loads(edges_df.to_json())

        return output
