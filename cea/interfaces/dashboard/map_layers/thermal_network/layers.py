import json
import os

import fiona
import pandas as pd
import geopandas as gpd
from pyproj import CRS, Transformer

from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers.base import MapLayer
from cea.interfaces.dashboard.map_layers.thermal_network import ThermalNetworkCategory
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system


class ThermalNetworkMapLayer(MapLayer):
    category = ThermalNetworkCategory
    name = "thermal-network"
    label = "Thermal Network"
    description = "Thermal Network Design"

    @property
    def input_files(self):
        scenario_name = self.parameters['scenario-name']
        network_type = self.parameters.get('network-type', 'DC')
        # FIXME: network_name is usually not used in the script
        network_name = ""
        print(network_type)
        locator = InputLocator(os.path.join(self.project, scenario_name))

        return [
            (locator.get_network_layout_edges_shapefile,[network_type, network_name]),
            (locator.get_network_layout_nodes_shapefile, [network_type, network_name]),
            (locator.get_thermal_network_layout_massflow_edges_file, [network_type, network_name]),
            # (locator.get_thermal_demand_csv_file, network_type, network_name),
            # (locator.get_thermal_network_edge_list_file, network_type, network_name),
            # (locator.get_network_thermal_loss_edges_file, network_type, network_name),
        ]

    @classmethod
    def expected_parameters(cls):
        return {
            'scenario-name': {
                "type": "string",
                "description": "Scenario of the layer",
            },
            'network-type': {
                "type": "string",
                "selector": "choice",
                "description": "Type of the network",
                "default": "DC",
                "choices": ["DC", "DH"]
            },
            # 'width-scale': {
            #     "type": "float",
            #     "selector": "input",
            #     "description": "Scale factor for the width of the pipes",
            #     "default": 1.0
            # },
        }

    def generate_output(self):
        scenario_name = self.parameters['scenario-name']
        locator = InputLocator(os.path.join(self.project, scenario_name))

        network_type = self.parameters.get('network-type', 'DC')
        # FIXME: network_name is usually not used in the script
        network_name = ""

        output = {
            "nodes": None,
            "edges": None,
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
            }
        }

        edges_path = locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)
        massflow_edges_path = locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)

        crs = get_geographic_coordinate_system()
        edges_df = gpd.read_file(edges_path).to_crs(crs).set_index("Name")
        nodes_df = gpd.read_file(nodes_path).to_crs(crs).set_index("Name")
        massflow_edges_df = pd.read_csv(massflow_edges_path)

        edges_df["peak_mass_flow"] = massflow_edges_df.max().round(1)

        output['nodes'] = json.loads(nodes_df.to_json())
        output['edges'] = json.loads(edges_df.to_json())

        return output
