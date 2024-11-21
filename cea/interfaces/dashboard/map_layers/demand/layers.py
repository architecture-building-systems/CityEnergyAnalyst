import itertools
import os
from concurrent.futures import ThreadPoolExecutor

import fiona
import pandas as pd
from pyproj import CRS, Transformer

from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer
from cea.interfaces.dashboard.map_layers.demand import DemandCategory


class DemandMapLayer(MapLayer):
    category = DemandCategory
    name = "demand"
    label = "Demand [kWh]"
    description = "Energy Demand of buildings"

    @property
    def input_files(self):
        scenario_name = self.parameters['scenario-name']
        locator = InputLocator(os.path.join(self.project, scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()

        return [(locator.get_demand_results_file, [building]) for building in buildings]

    @classmethod
    def expected_parameters(cls):
        return {
            'scenario-name': {
                "type": "string",
                "description": "Scenario of the layer",
            },
            'period': {
                "type": "array",
                "selector": "time-series",
                "description": "Period to generate the data (start, end) in days",
                "default": [1, 365]
            },
        }

    def generate_output(self):
        """Generates the output for this layer"""
        scenario_name = self.parameters['scenario-name']
        locator = InputLocator(os.path.join(self.project, scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()
        period = self.parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
            }
        }

        # Convert coordinates to WGS84
        with fiona.open(locator.get_zone_geometry()) as src:
            transformer = Transformer.from_crs(src.crs, CRS.from_epsg(4326), always_xy=True)

        def get_building_sensors(building):
            metadata = pd.read_csv(locator.get_radiation_metadata(building)).set_index('SURFACE')
            building_sensors = pd.read_feather(locator.get_radiation_building_sensors(building)) * 1 / 1000 # Convert W/m2 to kWh/m2

            # Get terrain elevation
            if "terrain_elevation" in metadata.columns:
                terrain_elevation = metadata["terrain_elevation"].values[0]
            else:
                terrain_elevation = 0

            total_min = 0
            total_max = building_sensors.sum(numeric_only=True).max()

            if start < end:
                period_sensor_values = building_sensors.iloc[start:end+1].sum(numeric_only=True)
            else:
                period_sensor_values = building_sensors.iloc[start:].sum(numeric_only=True) + building_sensors.iloc[:end+1].sum(numeric_only=True)
            period_min = period_sensor_values.min()
            period_max = period_sensor_values.max()

            # Ensure metadata index matches sensor_values keys
            metadata_subset = metadata.loc[list(period_sensor_values.keys())]

            # Vectorized transformation
            transformed_positions = transformer.transform(
                metadata_subset['Xcoor'].values,
                metadata_subset['Ycoor'].values,
                metadata_subset['Zcoor'].values - terrain_elevation
            )

            # Create data efficiently using list comprehension
            data = [
                {
                    "position": [float(x), float(y), float(z)],
                    "value": float(period_sensor_values[sensor])
                }
                for sensor, x, y, z in zip(period_sensor_values.keys(),
                                           transformed_positions[0], transformed_positions[1], transformed_positions[2])
            ]

            return total_min, total_max, period_min, period_max, data

        with ThreadPoolExecutor() as executor:
            values = executor.map(get_building_sensors, buildings)

        total_min, total_max, period_min, period_max, data = zip(*values)

        output['data'] = list(itertools.chain(*data))
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
