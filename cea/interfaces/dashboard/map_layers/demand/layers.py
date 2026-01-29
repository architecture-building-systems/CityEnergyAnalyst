import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.demand import DemandCategory
from cea.plots.colors import color_to_hex


class DemandMapLayer(MapLayer):
    category = DemandCategory
    name = "demand"
    label = "End-use Electricity [kWh]"
    description = "Energy Demand of buildings"

    _data_columns = {
        "E_sys_kWh": {
            "label": "End-use Electricity [kWh]",
            "colours": {
                "colour_array": [color_to_hex("green_lighter"), color_to_hex("green")],
                "points": 12
            }
        },
        "Qcs_sys_kWh": {
            "label": "End-use Space Cooling [kWh]",
            "colours": {
                "colour_array": [color_to_hex("blue_lighter"), color_to_hex("blue")],
                "points": 12
            }
        },
        "Qhs_sys_kWh": {
            "label": "End-use Space Heating [kWh]",
            "colours": {
                "colour_array": [color_to_hex("red_lighter"), color_to_hex("red")],
                "points": 12
            }
        },
        "Qww_sys_kWh": {
            "label": "End-use Domestic Hot Water [kWh]",
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

        def get_building_demand(building, centroid):
            demand = pd.read_csv(self.locator.get_demand_results_file(building), usecols=[data_column])[data_column]

            total_min = 0
            total_max = demand.sum()

            if start < end:
                period_value = demand.iloc[start:end + 1].sum()
            else:
                period_value = demand.iloc[start:].sum() + demand.iloc[:end + 1].sum()
            period_min = period_value
            period_max = period_value

            data = {"position": [centroid.x, centroid.y], "value": period_value}

            return total_min, total_max, period_min, period_max, data

        df = gpd.read_file(self.locator.get_zone_geometry()).set_index("name").loc[buildings]
        building_centroids = df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        # with ThreadPoolExecutor() as executor:
        #     values = executor.map(get_building_demand, buildings, building_centroids)
        #
        # total_min, total_max, period_min, period_max, data = zip(*values)

        values = (get_building_demand(building, centroid)
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
