import os
import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.demand import DemandCategory
from cea.plots.colors import color_to_hex


def safe_filter_buildings_with_geometry(locator, buildings: list) -> tuple:
    """
    Filter buildings to only include those that exist in zone geometry.
    Returns tuple of (filtered_buildings, geometry_df, centroids).
    Gracefully handles missing buildings by excluding them.
    """
    if not buildings:
        return [], None, []

    try:
        zone_gdf = gpd.read_file(locator.get_zone_geometry()).set_index("name")

        # Filter to only buildings that exist in geometry
        existing_buildings = [b for b in buildings if b in zone_gdf.index]

        if not existing_buildings:
            return [], None, []

        geometry_df = zone_gdf.loc[existing_buildings]
        centroids = geometry_df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        return existing_buildings, geometry_df, centroids
    except Exception as e:
        print(f"Warning: Error reading zone geometry: {e}")
        return [], None, []


class DemandMapLayer(MapLayer):
    category = DemandCategory
    name = "demand"
    label = "Grid Electricity Consumption [kWh]"
    description = "Energy Demand of buildings"

    _data_columns = {
        "GRID_kWh": {
            "label": "Grid Electricity Final-Use [kWh]",
            "colours": {
                "colour_array": [color_to_hex("brown_lighter"), color_to_hex("brown")],
                "points": 12
            }
        },
        "E_sys_kWh": {
            "label": "Electricity End-Use [kWh]",
            "colours": {
                "colour_array": [color_to_hex("green_lighter"), color_to_hex("green")],
                "points": 12
            }
        },
        "Qcs_sys_kWh": {
            "label": "Space Cooling End-Use [kWh]",
            "colours": {
                "colour_array": [color_to_hex("blue_lighter"), color_to_hex("blue")],
                "points": 12
            }
        },
        "Qhs_sys_kWh": {
            "label": "Space Heating End-Use [kWh]",
            "colours": {
                "colour_array": [color_to_hex("red_lighter"), color_to_hex("red")],
                "points": 12
            }
        },
        "Qww_sys_kWh": {
            "label": "Domestic Hot Water End-Use [kWh]",
            "colours": {
                "colour_array": [color_to_hex("orange_lighter"), color_to_hex("orange")],
                "points": 12
            }
        },
    }

    def _get_data_columns(self):
        return list(self._data_columns.keys())

    def _get_results_files(self, _):
        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_demand_results_file(building) for building in buildings]

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
                "Demand Results",
                file_locator="layer:_get_results_files",
                optional=True,  # Individual building files may be missing
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

        if data_column not in self._data_columns.keys():
            raise ValueError(f"Invalid data column: {data_column}")

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": self._data_columns[data_column]["label"],
                "description": self.description,
                "colours": self._data_columns[data_column]["colours"]
            }
        }

        # Filter buildings that exist in geometry
        buildings, _, building_centroids = safe_filter_buildings_with_geometry(self.locator, buildings)

        if not buildings:
            output['properties']['range'] = {
                'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
                'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0}
            }
            return output

        def get_building_demand(building, centroid):
            try:
                demand_file = self.locator.get_demand_results_file(building)
                if not os.path.exists(demand_file):
                    return None

                demand = pd.read_csv(demand_file, usecols=[data_column])[data_column]

                total_min = 0
                total_max = demand.sum()

                if start < end:
                    period_value = demand.iloc[start:end + 1].sum()
                else:
                    period_value = demand.iloc[start:].sum() + demand.iloc[:end + 1].sum()
                period_min = period_value
                period_max = period_value

                data_point = {"position": [centroid.x, centroid.y], "value": period_value}

                return total_min, total_max, period_min, period_max, data_point
            except Exception as e:
                print(f"Warning: Error reading demand for {building}: {e}")
                return None

        # with ThreadPoolExecutor() as executor:
        #     values = executor.map(get_building_demand, buildings, building_centroids)
        #
        # total_min, total_max, period_min, period_max, data = zip(*values)

        values = [get_building_demand(building, centroid) for building, centroid in zip(buildings, building_centroids)]

        # Filter out None values (missing files)
        values = [v for v in values if v is not None]

        if not values:
            output['properties']['range'] = {
                'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
                'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0}
            }
            return output

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
