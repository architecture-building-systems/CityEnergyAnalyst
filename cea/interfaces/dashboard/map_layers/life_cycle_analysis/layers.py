from typing import Optional

import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.life_cycle_analysis import LifeCycleAnalysisCategory
from cea.plots.colors import color_to_hex


class EmbodiedEmissionsMapLayer(MapLayer):
    category = LifeCycleAnalysisCategory
    name = "embodied-emissions"
    label = "Embodied Emissions"
    description = ""

    def _get_data_columns(self) -> Optional[list]:
        results_path = self.locator.get_lca_embodied()

        try:
            emissions_df = pd.read_csv(results_path)
            columns = set(emissions_df.columns)
        except (pd.errors.EmptyDataError, FileNotFoundError):
            return

        return sorted(list(columns - {"name", "GFA_m2"}))

    @classmethod
    def expected_parameters(cls):
        return {
            'data-column':
                ParameterDefinition(
                    "Data Column",
                    "string",
                    description="Data column to use",
                    options_generator="_get_data_columns",
                    selector="choice",
                ),
            'radius':
                ParameterDefinition(
                    "Radius",
                    "number",
                    default=5,
                    description="Radius of hexagon bin in meters",
                    selector="input",
                    range=[0, 100],
                    filter="radius",
                ),
            'scale':
                ParameterDefinition(
                    "Scale",
                    "number",
                    default=1,
                    description="Scale of hexagon bin height",
                    selector="input",
                    range=[0.1, 10],
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
                "Embodied Emissions Results",
                file_locator="locator:get_lca_embodied",
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""

        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        data_column = parameters['data-column']

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": "Embodied Emissions",
                "description": self.description,
                "colours": {
                    "colour_array": [color_to_hex("grey_lighter"), color_to_hex("black")],
                    "points": 12
                }
            }
        }

        df = gpd.read_file(self.locator.get_zone_geometry()).set_index("name").loc[buildings]
        building_centroids = df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        results_path = self.locator.get_lca_embodied()
        emissions_df = pd.read_csv(results_path, usecols=["name", data_column], index_col="name")[data_column].loc[
            buildings]

        output['data'] = [{"position": [centroid.x, centroid.y], "value": emissions} for centroid, emissions in
                          zip(building_centroids, emissions_df)]
        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': float(min(emissions_df)),
                'max': float(max(emissions_df))
            },
        }

        return output


class OperationalEmissionsMapLayer(MapLayer):
    category = LifeCycleAnalysisCategory
    name = "operational-emissions"
    label = "Operational Emissions"
    description = ""

    def _get_data_columns(self) -> Optional[list]:
        results_path = self.locator.get_lca_operation()

        try:
            emissions_df = pd.read_csv(results_path)
            columns = set(emissions_df.columns)
        except (pd.errors.EmptyDataError, FileNotFoundError):
            return

        return sorted(list(columns - {"name", "GFA_m2"}))

    @classmethod
    def expected_parameters(cls):
        return {
            'data-column':
                ParameterDefinition(
                    "Data Column",
                    "string",
                    description="Data column to use",
                    options_generator="_get_data_columns",
                    selector="choice",
                ),
            'radius':
                ParameterDefinition(
                    "Radius",
                    "number",
                    default=5,
                    description="Radius of hexagon bin in meters",
                    selector="input",
                    range=[0, 100],
                    filter="radius",
                ),
            'scale':
                ParameterDefinition(
                    "Scale",
                    "number",
                    default=1,
                    description="Scale of hexagon bin height",
                    selector="input",
                    range=[0.1, 10],
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
                "Operational Emissions Results",
                file_locator="locator:get_lca_operation",
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""

        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        data_column = parameters['data-column']

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": "Operational Emissions",
                "description": self.description,
                "colours": {
                    "colour_array": [color_to_hex("grey_lighter"), color_to_hex("black")],
                    "points": 12
                }
            }
        }

        df = gpd.read_file(self.locator.get_zone_geometry()).set_index("name").loc[buildings]
        building_centroids = df.geometry.centroid.to_crs(CRS.from_epsg(4326))
        
        results_path = self.locator.get_lca_operation()
        emissions_df = pd.read_csv(results_path, usecols=["name", data_column], index_col="name")[data_column].loc[
            buildings]

        output['data'] = [{"position": [centroid.x, centroid.y], "value": emissions} for centroid, emissions in
                          zip(building_centroids, emissions_df)]
        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': float(min(emissions_df)),
                'max': float(max(emissions_df))
            },
        }

        return output
