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
    label = "Demand [kWh]"
    description = "Energy Demand of buildings"

    # Dropdown-visible service name → internal CSV column + colour pair.
    # Service names match the unified UI layer convention (snake_case
    # words, matching the operational/lifecycle emissions map layers).
    _data_columns = {
        "electricity": {
            "column": "E_sys_kWh",
            "label": "End-use Demand - electricity [kWh]",
            "colours": {
                "colour_array": [color_to_hex("green_lighter"), color_to_hex("green")],
                "points": 12
            }
        },
        "space_heating": {
            "column": "Qhs_sys_kWh",
            "label": "End-use Demand - space_heating [kWh]",
            "colours": {
                "colour_array": [color_to_hex("red_lighter"), color_to_hex("red")],
                "points": 12
            }
        },
        "space_cooling": {
            "column": "Qcs_sys_kWh",
            "label": "End-use Demand - space_cooling [kWh]",
            "colours": {
                "colour_array": [color_to_hex("blue_lighter"), color_to_hex("blue")],
                "points": 12
            }
        },
        "domestic_hot_water": {
            "column": "Qww_sys_kWh",
            "label": "End-use Demand - domestic_hot_water [kWh]",
            "colours": {
                "colour_array": [color_to_hex("orange_lighter"), color_to_hex("orange")],
                "points": 12
            }
        },
    }

    def _get_data_columns(self):
        return {
            "choices": [
                {"value": key, "label": key}
                for key in self._data_columns.keys()
            ],
            "default": "electricity",
        }

    def _get_results_files(self, _):
        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_demand_results_file(building) for building in buildings]

    @classmethod
    def expected_parameters(cls):
        return {
            'data-column':
                ParameterDefinition(
                    "service",
                    "string",
                    description="End-use service(s) to visualise",
                    options_generator="_get_data_columns",
                    selector="choice",
                    multi=True,
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
                    default=2,
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
        """Generate single (HexagonLayer) or stacked (ColumnLayer) output.

        - 1 service selected → HexagonLayer shape with that column's
          gradient and legend label.
        - 2+ services selected → stacked shape with one ColumnLayer per
          service; frontend renders segments on top of each other.

        Mirrors the Operational/Lifecycle Emissions pattern.
        """
        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        raw_selection = parameters['data-column']

        # Backwards compatibility: previous versions stored the raw CSV
        # column name (e.g. 'E_sys_kWh') or a single display-name string
        # in `data-column`. Normalise to a list of display names.
        legacy_to_display = {
            entry["column"]: display
            for display, entry in self._data_columns.items()
        }

        def _normalise(value):
            if value is None:
                return None
            if value in self._data_columns:
                return value
            if value in legacy_to_display:
                return legacy_to_display[value]
            return None

        if isinstance(raw_selection, list):
            selected = [n for n in (_normalise(v) for v in raw_selection) if n]
        elif isinstance(raw_selection, str):
            n = _normalise(raw_selection)
            selected = [n] if n else []
        else:
            selected = []

        # Preserve canonical (dict insertion) order so stacks are predictable.
        canonical_order = list(self._data_columns.keys())
        selected = [s for s in canonical_order if s in selected]
        is_stacked = len(selected) > 1

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        def empty_output(fallback=None):
            entry = self._data_columns.get(fallback) if fallback else None
            label = entry["label"] if entry else "End-use Demand [kWh]"
            colours = entry["colours"] if entry else {
                "colour_array": [color_to_hex("grey_lighter"), color_to_hex("black")],
                "points": 12,
            }
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": label,
                    "description": self.description,
                    "colours": colours,
                    "range": empty_range,
                    "stacked": False,
                },
            }

        if not selected:
            return empty_output()

        # Filter buildings that exist in geometry
        buildings, _, building_centroids = safe_filter_buildings_with_geometry(
            self.locator, buildings
        )
        if not buildings:
            return empty_output(selected[0])

        def read_building_values(building):
            """Return {service: period_sum} for this building, or None on missing."""
            demand_file = self.locator.get_demand_results_file(building)
            if not os.path.exists(demand_file):
                return None
            try:
                columns = [self._data_columns[s]["column"] for s in selected]
                df = pd.read_csv(demand_file, usecols=columns)
            except Exception as exc:
                print(f"Warning: Error reading demand for {building}: {exc}")
                return None
            out = {}
            for service in selected:
                col = self._data_columns[service]["column"]
                series = df[col].astype(float)
                if start < end:
                    out[service] = float(series.iloc[start:end + 1].sum())
                else:
                    out[service] = float(
                        series.iloc[start:].sum() + series.iloc[:end + 1].sum()
                    )
            return out

        entities = []
        for building, centroid in zip(buildings, building_centroids):
            values = read_building_values(building)
            if values is None:
                continue
            entities.append({
                "name": building,
                "position": [centroid.x, centroid.y],
                "values": values,
            })

        if not entities:
            return empty_output(selected[0])

        if not is_stacked:
            service = selected[0]
            entry = self._data_columns[service]
            data_points = [
                {
                    "position": e["position"],
                    "value": e["values"][service],
                    "name": e["name"],
                    "category": service,
                }
                for e in entities
            ]
            period_values = [p["value"] for p in data_points]
            return {
                "data": data_points,
                "properties": {
                    "name": self.name,
                    "label": entry["label"],
                    "description": self.description,
                    "colours": entry["colours"],
                    "range": {
                        "total": {
                            "label": "Total Range",
                            "min": 0.0,
                            "max": float(max(period_values)) if period_values else 0.0,
                        },
                        "period": {
                            "label": "Period Range",
                            "min": float(min(period_values)) if period_values else 0.0,
                            "max": float(max(period_values)) if period_values else 0.0,
                        },
                    },
                    "stacked": False,
                },
            }

        # Stacked-multi path: one ColumnLayer per service on the frontend.
        categories_payload = []
        for service in selected:
            colour_array = self._data_columns[service]["colours"]["colour_array"]
            hex_colour = colour_array[-1] if colour_array else "#888888"
            r = int(hex_colour[1:3], 16)
            g = int(hex_colour[3:5], 16)
            b = int(hex_colour[5:7], 16)
            categories_payload.append({
                "name": service,
                "colour": hex_colour,
                "rgb": [r, g, b],
            })

        stack_totals = [
            sum(max(e["values"].get(s, 0.0), 0.0) for s in selected)
            for e in entities
        ]

        return {
            "data": entities,
            "properties": {
                "name": self.name,
                "label": "End-use Demand - stacked [kWh]",
                "description": self.description,
                "stacked": True,
                "categories": categories_payload,
                "range": {
                    "total": {
                        "label": "Total Range",
                        "min": 0.0,
                        "max": float(max(stack_totals)) if stack_totals else 0.0,
                    },
                    "period": {
                        "label": "Period Range",
                        "min": 0.0,
                        "max": float(max(stack_totals)) if stack_totals else 0.0,
                    },
                },
            },
        }
