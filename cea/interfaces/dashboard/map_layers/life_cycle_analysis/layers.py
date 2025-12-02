from typing import Optional
import os

import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.life_cycle_analysis import LifeCycleAnalysisCategory
from cea.plots.colors import color_to_hex

IGNORE_COLUMNS = {"name", "GFA_m2", "period", "date", "hour", "month", "day"}

def period_to_year(period: pd.Series) -> pd.Series:
    """Convert a period string of the form 'Y_XXXX' to an integer year XXXX"""
    return period.str.extract(r'Y_(\d{4})')[0].astype(int)


class LifecycleEmissionsMapLayer(MapLayer):
    category = LifeCycleAnalysisCategory
    name = "lifecycle-emissions"
    label = "Lifecycle Emissions (Annual)"
    description = ""

    def _get_data_columns(self) -> Optional[list]:
        buildings = self.locator.get_zone_building_names()
        if not buildings:
            return
        results_path = self.locator.get_lca_timeline_building(buildings[0])

        try:
            emissions_df = pd.read_csv(results_path)
            columns = set(emissions_df.columns) - IGNORE_COLUMNS
        except (pd.errors.EmptyDataError, FileNotFoundError):
            return

        return sorted(list(columns))

    def _get_results_files(self, _):
        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_lca_timeline_building(b) for b in buildings]

    def _get_period_range(self) -> list:
        """Get the valid period range from available data"""
        try:
            buildings = self.locator.get_zone_building_names()
            timeline_df = self.locator.get_lca_timeline_building(buildings[0])
            df = pd.read_csv(timeline_df)
            df['year'] = period_to_year(df['period'])
            return [int(df['year'].min()), int(df['year'].max())]
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return [None, None]


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
            'timeline':
                ParameterDefinition(
                    "Period",
                    "array",
                    description="Period to generate the data based on years",
                    selector="slider",
                    options_generator="_get_period_range",
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
                "Embodied Emissions Timeline Files",
                file_locator="layer:_get_results_files",
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""

        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        data_column = parameters['data-column']
        period = parameters['timeline']
        start, end = period

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

        def get_data(building, centroid):
            df = pd.read_csv(
                self.locator.get_lca_timeline_building(building), usecols=["period", data_column]
            )

            data = df[data_column]
            data.index = period_to_year(df['period'])

            total_min = 0
            total_max = data.sum()

            period_value = data.loc[start:end].sum()
            period_min = period_value
            period_max = period_value

            data = {"position": [centroid.x, centroid.y], "value": period_value}

            return total_min, total_max, period_min, period_max, data

        df = gpd.read_file(self.locator.get_zone_geometry()).set_index("name").loc[buildings]
        building_centroids = df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        values = (get_data(building, centroid)
                  for building, centroid in zip(buildings, building_centroids))

        total_min, total_max, period_min, period_max, data = zip(*values)

        output['data'] = data
        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': float(min(total_min)),
                'max': float(max(total_max))
            },
            'period': {
                'label': 'Period Range',
                'min': float(min(period_min)),
                'max': float(max(period_max))
            }
        }
        return output


class OperationalEmissionsMapLayer(MapLayer):
    category = LifeCycleAnalysisCategory
    name = "operational-emissions"
    label = "Operational Emissions (Hourly/Daily)"
    description = ""

    def _get_data_columns(self) -> Optional[list]:
        buildings = self.locator.get_zone_building_names()
        if not buildings:
            return
        results_path = self.locator.get_lca_operational_hourly_building(buildings[0])

        try:
            emissions_df = pd.read_csv(results_path)
            columns = set(emissions_df.columns) - IGNORE_COLUMNS
        except (pd.errors.EmptyDataError, FileNotFoundError):
            return

        return sorted(list(columns))

    def _get_results_files(self, _):
        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_lca_operational_hourly_building(building) for building in buildings]

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
            'period':
                ParameterDefinition(
                    "Period",
                    "array",
                    default=[1, 365],
                    description="Period to generate the data (start, end) in days",
                    selector="time-series",
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
                "Operational Emissions Hourly Files",
                file_locator="layer:_get_results_files",
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""

        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])
        
        data_column = parameters['data-column']

        if data_column is None or data_column not in self._get_data_columns():
            raise ValueError(f"Invalid data column: {data_column}")


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

        def get_data(building, centroid):
            data = pd.read_csv(self.locator.get_lca_operational_hourly_building(building), usecols=[data_column])[data_column]

            total_min = 0
            total_max = data.sum()

            if start < end:
                period_value = data.iloc[start:end + 1].sum()
            else:
                period_value = data.iloc[start:].sum() + data.iloc[:end + 1].sum()
            period_min = period_value
            period_max = period_value

            data = {"position": [centroid.x, centroid.y], "value": period_value}

            return total_min, total_max, period_min, period_max, data

        df = gpd.read_file(self.locator.get_zone_geometry()).set_index("name").loc[buildings]
        building_centroids = df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        values = (get_data(building, centroid)
                  for building, centroid in zip(buildings, building_centroids))

        total_min, total_max, period_min, period_max, data = zip(*values)

        output['data'] = data
        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': float(min(total_min)),
                'max': float(max(total_max))
            },
            'period': {
                'label': 'Period Range',
                'min': float(min(period_min)),
                'max': float(max(period_max))
            }
        }
        return output


class EmissionTimelineMapLayer(MapLayer):
    category = LifeCycleAnalysisCategory
    name = "emission-timeline"
    label = "Emission Timeline"
    description = ""

    def _get_results_files(self, _):
        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_lca_timeline_building(b) for b in buildings]

    def _get_period_range(self) -> list:
        """Get the valid period range from available data"""
        try:
            buildings = self.locator.get_zone_building_names()
            timeline_df = self.locator.get_lca_timeline_building(buildings[0])
            df = pd.read_csv(timeline_df)
            df['year'] = period_to_year(df['period'])
            return [int(df['year'].min()), int(df['year'].max())]
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return [None, None]

    @classmethod
    def expected_parameters(cls):
        return {
            'timeline':
                ParameterDefinition(
                    "Period",
                    "array",
                    description="Period to generate the data based on years",
                    selector="slider",
                    options_generator="_get_period_range",
                ),
        }
    
    @classmethod
    def file_requirements(cls):
        return [
            FileRequirement(
                "Lifecycle Emissions Timeline Files",
                file_locator="layer:_get_results_files",
            ),
        ]

    def generate_data(self, parameters: dict) -> dict:
        return {}


class AnthropogenicHeatMapLayer(MapLayer):
    category = LifeCycleAnalysisCategory
    name = "anthropogenic-heat-rejection"
    label = "Anthropogenic Heat Rejection (Hourly/Daily)"
    description = "Visualise heat rejection from building systems and district cooling plants"

    def _get_results_files(self, _):
        """Return required files for caching"""
        # Read buildings file to get list of entities
        buildings_file = self.locator.get_heat_rejection_buildings()
        if not os.path.exists(buildings_file):
            return []

        buildings_df = pd.read_csv(buildings_file)
        entity_names = buildings_df['name'].tolist()

        # Return buildings file + all individual entity files
        files = [buildings_file]
        for entity_name in entity_names:
            entity_file = self.locator.get_heat_rejection_hourly_building(entity_name)
            if os.path.exists(entity_file):
                files.append(entity_file)

        return files

    @classmethod
    def expected_parameters(cls):
        return {
            'period':
                ParameterDefinition(
                    "Period",
                    "array",
                    default=[1, 365],
                    description="Period to generate the data (start, end) in days",
                    selector="time-series",
                ),
            'radius':
                ParameterDefinition(
                    "Radius",
                    "number",
                    default=5,
                    description="Radius of hexagon bin in metres",
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
                "Heat Rejection Buildings Summary",
                file_locator="locator:get_heat_rejection_buildings",
            ),
            FileRequirement(
                "Heat Rejection Hourly Building Files",
                file_locator="layer:_get_results_files",
                optional=True,  # Individual building files may be missing, handled gracefully
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the hexagon heatmap output for anthropogenic heat rejection"""

        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        # Read buildings file to get entity list and coordinates
        buildings_df = pd.read_csv(self.locator.get_heat_rejection_buildings())
        entity_names = buildings_df['name'].tolist()

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": "Anthropogenic Heat Rejection",
                "description": self.description,
                "colours": {
                    "colour_array": ["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
                    "points": 12
                }
            }
        }

        def get_data(entity_name, centroid):
            # Read individual entity file
            entity_file = self.locator.get_heat_rejection_hourly_building(entity_name)

            if not os.path.exists(entity_file):
                return 0.0, 0.0, {"position": [centroid.x, centroid.y], "value": 0.0}

            entity_df = pd.read_csv(entity_file)

            # Sum all heat rejection for this entity across all hours (should be exactly 8760)
            total_value = entity_df['heat_rejection_kW'].sum()

            # Filter by period (start and end are 0-indexed hour numbers)
            period_df = entity_df.iloc[start:end+1]
            period_value = period_df['heat_rejection_kW'].sum()

            data_point = {"position": [centroid.x, centroid.y], "value": period_value}

            return total_value, period_value, data_point

        # Set buildings file as index
        buildings_df = buildings_df.set_index('name')

        # Get zone geometry for CRS
        zone_gdf = gpd.read_file(self.locator.get_zone_geometry())

        # Create GeoDataFrame with entity coordinates
        entity_gdf = gpd.GeoDataFrame(
            buildings_df.loc[entity_names],
            geometry=gpd.points_from_xy(
                buildings_df.loc[entity_names]['x_coord'],
                buildings_df.loc[entity_names]['y_coord']
            ),
            crs=zone_gdf.crs
        )
        entity_centroids = entity_gdf.geometry.to_crs(CRS.from_epsg(4326))

        # Handle case where there are no entities or all files are missing
        if not entity_names:
            output['data'] = []
            output['properties']['range'] = {
                'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
                'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0}
            }
            return output

        values = (get_data(entity_name, centroid)
                  for entity_name, centroid in zip(entity_names, entity_centroids))

        total_values, period_values, data = zip(*values)

        # Filter out entities with zero values (missing files)
        non_zero_data = [(t, p, d) for t, p, d in zip(total_values, period_values, data) if p > 0 or t > 0]

        if non_zero_data:
            total_values, period_values, data = zip(*non_zero_data)
        else:
            # All entities have zero values
            total_values, period_values, data = (0.0,), (0.0,), []

        output['data'] = data
        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': float(min(total_values)) if total_values else 0.0,
                'max': float(max(total_values)) if total_values else 0.0
            },
            'period': {
                'label': 'Period Range',
                'min': float(min(period_values)) if period_values else 0.0,
                'max': float(max(period_values)) if period_values else 0.0
            }
        }

        return output
