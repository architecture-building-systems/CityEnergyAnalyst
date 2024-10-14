import os

import fiona
import pandas as pd
from pyproj import CRS, Transformer

from cea.config import Parameter
from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers.base import MapLayer


class SolarIrradianceMapLayer(MapLayer):
    category = "solar-potentials"
    name = "solar-irradiance"
    label = "Solar irradiance [kW/m2]"
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
            'threshold': {
                "type": "array",
                "selector": "threshold",
                "description": "Thresholds for the layer",
                "label": "Annual Solar Irradiation Threshold",
                "range": "total"
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

        total_min, total_max = 10e10, 0
        period_min, period_max = 10e10, 0
        for building in buildings:
            metadata = pd.read_csv(locator.get_radiation_metadata(building)).set_index('SURFACE')
            building_sensors = pd.read_feather(locator.get_radiation_building_sensors(building))

            # Get terrain elevation
            if "terrain_elevation" in metadata.columns:
                terrain_elevation = metadata["terrain_elevation"].values[0]
            else:
                terrain_elevation = 0

            total_min = min(total_min, building_sensors.min(numeric_only=True).min())
            total_max = max(total_max, building_sensors.max(numeric_only=True).max())

            sensor_values = building_sensors.iloc[hour]
            period_min = min(period_min, sensor_values.min())
            period_max = max(period_max, sensor_values.max())
            for sensor, value in sensor_values.items():
                sensor_metadata = metadata.loc[sensor]
                sensor_position = transformer.transform(sensor_metadata['Xcoor'], sensor_metadata['Ycoor'],
                                                        sensor_metadata['Zcoor'] - terrain_elevation)
                # sensor_normal = (sensor_metadata['Xdir'], sensor_metadata['Ydir'], sensor_metadata['Zdir'])

                sensor_output = {
                    "position": sensor_position,
                    "value": value
                }
                output['data'].append(sensor_output)

        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': float(total_min),
                'max': float(total_max)
            },
            'period': {
                'label': 'Period Range',
                'min': float(period_min),
                'max': float(period_max)
            }
        }

        return output
