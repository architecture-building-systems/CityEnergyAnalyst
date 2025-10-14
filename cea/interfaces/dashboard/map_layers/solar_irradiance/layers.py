import itertools
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import rasterio
from pyproj import CRS, Transformer

from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.solar_irradiance import SolarIrradiationCategory


class SolarIrradiationMapLayer(MapLayer):
    category = SolarIrradiationCategory
    name = "solar-irradiation"
    label = "Solar Irradiation [kWh/m2]"
    description = "Solar irradiation of building surfaces"

    def _get_sensor_metadata(self, _):
        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        return [self.locator.get_radiation_metadata(building) for building in buildings]

    def _get_sensor_data(self, _):
        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        return [self.locator.get_radiation_building_sensors(building) for building in buildings]

    @classmethod
    def expected_parameters(cls):
        # TODO: Move to separate property e.g. data filter parameters

        return {
            'period':
                ParameterDefinition(
                    "Period",
                    "array",
                    default=[1, 365],
                    description="Period to generate the data (start, end) in days",
                    selector="time-series",
                ),
            'threshold':
                ParameterDefinition(
                    "Threshold",
                    "array",
                    default=[0, 3000],
                    description="Thresholds for the layer",
                    selector="threshold",
                    filter="range",
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
                "Sensor Metadata",
                file_locator="layer:_get_sensor_metadata",
            ),
            FileRequirement(
                "Sensor Data",
                file_locator="layer:_get_sensor_data",
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""
        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
                "colours": {
                    "colour_array": ['#2A7BB2', '#eb5025', '#f9e246'],
                    "points": 12
                }
            }
        }

        # Convert coordinates to WGS84 based on terrain (sensor crs are based on terrain)
        with rasterio.open(self.locator.get_terrain()) as src:
            src_crs = src.crs
        transformer = Transformer.from_crs(src_crs, CRS.from_epsg(4326), always_xy=True)

        def get_building_sensors(building):
            metadata = pd.read_csv(self.locator.get_radiation_metadata(building)).set_index('SURFACE')
            building_sensors = pd.read_feather(
                self.locator.get_radiation_building_sensors(building)) * 1 / 1000  # Convert W/m2 to kWh/m2

            # Get terrain elevation
            if "terrain_elevation" in metadata.columns:
                terrain_elevation = metadata["terrain_elevation"].values[0]
            else:
                terrain_elevation = 0

            total_min = 0
            total_max = building_sensors.sum(numeric_only=True).max()

            if start < end:
                period_sensor_values = building_sensors.iloc[start:end + 1].sum(numeric_only=True)
            else:
                period_sensor_values = building_sensors.iloc[start:].sum(numeric_only=True) + building_sensors.iloc[
                                                                                              :end + 1].sum(
                    numeric_only=True)
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
