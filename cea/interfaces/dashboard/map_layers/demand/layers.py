import os

import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer
from cea.interfaces.dashboard.map_layers.demand import DemandCategory


class DemandMapLayer(MapLayer):
    category = DemandCategory
    name = "demand"
    label = "Grid Electricity Consumption [kWh]"
    description = "Energy Demand of buildings"

    @property
    def input_files(self):
        scenario_name = self.parameters['scenario-name']
        locator = InputLocator(os.path.join(self.project, scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()

        return [(locator.get_demand_results_file, [building]) for building in buildings] + [
            (locator.get_zone_geometry, [])]

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
            'radius': {
                "type": "number",
                "filter": "radius",
                "selector": "input",
                "description": "Radius of hexagon bin in meters",
                "range": [0, 100],
                "default": 5
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
        data_column = "GRID_kWh"

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
            }
        }

        def get_building_demand(building, centroid):
            demand = pd.read_csv(locator.get_demand_results_file(building), usecols=[data_column])[data_column]

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

        df = gpd.read_file(locator.get_zone_geometry()).set_index("Name").loc[buildings]
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
