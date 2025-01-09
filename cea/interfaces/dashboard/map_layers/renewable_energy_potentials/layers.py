import os
from typing import List

import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.config import DEFAULT_CONFIG, Configuration
from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.renewable_energy_potentials import RenewableEnergyPotentialsCategory
from cea.plots.colors import color_to_hex


class SolarPotentialsLayer(MapLayer):
    category = RenewableEnergyPotentialsCategory
    name = "renewable-energy-potentials"
    label = "Renewable Energy Potentials [kWh]"
    description = "Renewable energy potentials of buildings"

    _technologies = {
        "PV": "Photovoltaic panels",
        "PVT": "Photovoltaic-thermal panels",
        "SC": "Solar collectors"
    }

    _data_columns = {
        "PV": "E_PV_gen_kWh",
        "PVT": "E_PVT_gen_kWh",
        "SC": "Q_SC_gen_kWh",
    }

    def _get_technologies(self) -> List[str]:
        return list(self._technologies.keys())

    def _get_panel_types(self, parameters: dict) -> List[str]:
        config = Configuration(DEFAULT_CONFIG)
        config.project = self.project
        config.scenario_name = self.scenario_name

        technology = parameters.get("technology")

        if technology == "PV":
            df = pd.read_excel(self.locator.get_database_conversion_systems(), sheet_name="PHOTOVOLTAIC_PANELS")
            return df["code"].unique().tolist()
        elif technology == "SC":
            df = pd.read_excel(self.locator.get_database_conversion_systems(), sheet_name="SOLAR_THERMAL_PANELS")
            return df["type"].unique().tolist()

        return None

    def _get_results_files(self, parameters: dict):
        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        technology = parameters.get("technology")
        panel_type = parameters.get("panel-type")

        if technology == "PV":
            if panel_type is None:
                raise ValueError("Panel type is required for PV")
            return [self.locator.PV_results(building, panel_type) for building in buildings]
        elif technology == "PVT":
            return [self.locator.PVT_results(building) for building in buildings]
        elif technology == "SC":
            if panel_type is None:
                raise ValueError("Panel type is required for SC")
            return [self.locator.SC_results(building, panel_type) for building in buildings]

        raise ValueError(f"Invalid technology specified: {technology}")

    @classmethod
    def expected_parameters(cls):
        return {
            'technology':
                ParameterDefinition(
                    "Technology",
                    "string",
                    description="Technology of the layer",
                    options_generator="_get_technologies",
                    selector="choice",
                ),
            'panel-type':
                ParameterDefinition(
                    "Panel Type",
                    "string",
                    description="Panel type of the layer",
                    options_generator="_get_panel_types",
                    depends_on=["technology"],
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
                "Zone Buildings geometry",
                file_locator="locator:get_zone_geometry",
            ),
            FileRequirement(
                "Solar potentials",
                file_locator="layer:_get_results_files",
                depends_on=["technology", "panel-type"],
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""
        locator = InputLocator(os.path.join(self.project, self.scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
                "colours": {
                    "colour_array": [color_to_hex("yellow_lighter"), color_to_hex("yellow")],
                    "points": 12
                }
            }
        }

        technology = parameters.get("technology")
        panel_type = parameters.get("panel-type")
        data_column = self._data_columns[technology]

        def get_building_potential(building, centroid):
            if technology == "PV":
                path = self.locator.PV_results(building, panel_type)
            elif technology == "PVT":
                path = self.locator.PVT_results(building)
            elif technology == "SC":
                path = self.locator.SC_results(building, panel_type)
            else:
                raise ValueError(f"Invalid technology specified: {technology}")

            df = pd.read_csv(path, usecols=[data_column])[data_column]

            total_min = 0
            total_max = df.sum()

            if start < end:
                period_value = df.iloc[start:end + 1].sum()
            else:
                period_value = df.iloc[start:].sum() + df.iloc[:end + 1].sum()
            period_min = period_value
            period_max = period_value

            data = {"position": [centroid.x, centroid.y], "value": period_value}

            return total_min, total_max, period_min, period_max, data

        df = gpd.read_file(locator.get_zone_geometry()).set_index("name").loc[buildings]
        building_centroids = df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        values = (get_building_potential(building, centroid)
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
