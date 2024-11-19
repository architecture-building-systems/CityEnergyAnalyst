import itertools
import os
from concurrent.futures import ThreadPoolExecutor

import fiona
import pandas as pd
from pyproj import CRS, Transformer

from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers.base import MapLayer
from cea.interfaces.dashboard.map_layers.solar_irradiance import SolarIrradiationCategory


class SolarIrradiationMapLayer(MapLayer):
    category = SolarIrradiationCategory
    name = "solar-irradiation"
    label = "Solar Irradiation [kWh/m2]"
    description = "Solar irradiation of building surfaces"

    @property
    def input_files(self):
        scenario_name = self.parameters['scenario-name']
        locator = InputLocator(os.path.join(self.project, scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()

        return ([(locator.get_radiation_metadata, [building]) for building in buildings] +
                [(locator.get_radiation_building_sensors, [building]) for building in buildings])

    @classmethod
    def expected_parameters(cls):
        return {
            'scenario-name': {
                "type": "string",
                "description": "Scenario of the layer",
            },
            'hour': {
                "type": "integer",
                "selector": "time-series",
                "description": "Period to generate the data",
                "default": 4380
            },
            # TODO: Move to separate property e.g. data filter parameters
            'threshold': {
                "type": "array",
                "selector": "threshold",
                "description": "Thresholds for the layer",
                "label": "Annual Solar Irradiation Threshold",
                "range": "total",
                "default": [0, 1000]
            },
        }

    def generate_output(self):
        """Generates the output for this layer"""
        scenario_name = self.parameters['scenario-name']
        locator = InputLocator(os.path.join(self.project, scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()
        hour = self.parameters['hour']

        # Format for each data point: {"position":[0,0,0],"normal":[0,0,0],"color":[0,0,0]}
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
            building_sensors = pd.read_feather(locator.get_radiation_building_sensors(building))

            # Get terrain elevation
            if "terrain_elevation" in metadata.columns:
                terrain_elevation = metadata["terrain_elevation"].values[0]
            else:
                terrain_elevation = 0

            total_min = building_sensors.min(numeric_only=True).min()
            total_max = building_sensors.max(numeric_only=True).max()

            sensor_values = building_sensors.iloc[hour]
            period_min = sensor_values.min()
            period_max = sensor_values.max()

            # Ensure metadata index matches sensor_values keys
            metadata_subset = metadata.loc[list(sensor_values.keys())]

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
                    "value": float(sensor_values[sensor])
                }
                for sensor, x, y, z in zip(sensor_values.keys(),
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
