from typing import Optional
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point

from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.life_cycle_analysis import LifeCycleAnalysisCategory
from cea.plots.colors import color_to_hex
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

logger = getCEAServerLogger("cea-server-lca-map-layers")

IGNORE_COLUMNS = {"name", "GFA_m2", "period", "date", "hour", "month", "day"}

def period_to_year(period: pd.Series) -> pd.Series:
    """Convert a period string of the form 'Y_XXXX' to an integer year XXXX"""
    return period.str.extract(r'Y_(\d{4})')[0].astype(int)


def safe_filter_buildings_with_geometry(locator, buildings: list) -> tuple:
    """
    Filter buildings to only include those that exist in zone geometry.
    Returns tuple of (filtered_buildings, geometry_df, centroids).
    Gracefully handles missing buildings by excluding them.
    """
    import geopandas as gpd
    from pyproj import CRS

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


def get_columns_from_building_files(paths: list) -> Optional[list]:
    """
    Read only the header row of each file in parallel and return the sorted union
    of all data columns (excluding IGNORE_COLUMNS). Returns None if no file is readable.
    """
    def read_header(path):
        try:
            return set(pd.read_csv(path, nrows=0).columns)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return None

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(read_header, paths))

    columns = set()
    for result in results:
        if result is not None:
            columns |= result

    columns -= IGNORE_COLUMNS
    return sorted(columns) if columns else None


def get_whatif_names(locator) -> list:
    """Return sorted list of what-if names that have lifecycle analysis results."""
    base = locator.get_analysis_parent_folder()
    return sorted([name for name in os.listdir(base)]) if os.path.isdir(base) else []


def delete_whatif(locator, whatif_name: str) -> None:
    """Delete an on-disk what-if scenario folder under the analysis parent folder."""
    if not whatif_name:
        raise ValueError("What-if name is required")
    base = locator.get_analysis_parent_folder()
    target = os.path.join(base, whatif_name)
    if not os.path.isdir(target):
        raise ValueError(f"What-if scenario '{whatif_name}' not found on disk")
    shutil.rmtree(target)


class WhatifDeletableMixin:
    """Provides delete_parameter_choice for LCA layers that expose a `whatif_name` parameter."""

    def delete_parameter_choice(self, parameter_name: str, value: str) -> None:
        if parameter_name != 'whatif_name':
            raise NotImplementedError(
                f"Parameter '{parameter_name}' does not support deletion"
            )
        delete_whatif(self.locator, value)


# Service-demand rollup columns (not per-carrier); excluded from the
# energy-carrier dropdown and ignored when building it up.
_ENERGY_DEMAND_ROLLUP_COLUMNS = {
    'Qhs_sys_kWh', 'Qww_sys_kWh', 'Qcs_sys_kWh', 'E_sys_kWh',
}

# High-level carriers surfaced to the user. The order is also the dropdown
# order. For each raw per-column value ending in ``_kWh`` we map it to one of
# these carriers via :func:`_column_to_carrier`; unknown columns are ignored.
_ENERGY_CARRIERS = ['GRID', 'NATURALGAS', 'OIL', 'COAL', 'WOOD', 'SOLAR']

# Display names shown in the dropdown. Internal values (dictionary keys) are
# kept so that column matching still works against the raw CSV headers.
_CARRIER_DISPLAY_NAMES = {
    'GRID': 'grid_electricity',
    'NATURALGAS': 'natural_gas',
    'OIL': 'oil',
    'COAL': 'coal',
    'WOOD': 'wood',
    'SOLAR': 'solar',
}

# Colour gradient (lighter, darker) per carrier — used by both the
# HexagonLayer single-carrier gradient and the stacked ColumnLayer per-
# carrier segment fill.
_CARRIER_COLOURS = {
    'GRID': ('red_lighter', 'red'),
    'NATURALGAS': ('brown_lighter', 'brown'),
    'OIL': ('grey_lighter', 'grey'),
    'COAL': ('black', 'black'),
    'WOOD': ('green_lighter', 'green'),
    'SOLAR': ('yellow_lighter', 'yellow'),
}

# Internal value to use as the default selection when the layer first loads.
_DEFAULT_CARRIER = 'GRID'


def _column_to_carrier(column: str) -> Optional[str]:
    """Map a raw ``*_kWh`` column name to a high-level carrier, or None.

    Mirrors the aggregation rules used by
    ``cea.analysis.final_energy.calculation._aggregate_hourly_data``.
    """
    if not column.endswith('_kWh') or column in _ENERGY_DEMAND_ROLLUP_COLUMNS:
        return None

    # Solar thermal generation columns. PV / PVT-electric are treated as
    # grid-replacement, not a separate carrier, so they are ignored here.
    if column.startswith('PV_'):
        return None
    if column.startswith('PVT_'):
        if column.endswith('_Q_kWh'):
            return 'SOLAR'
        return None
    if column.startswith('SC_'):
        return 'SOLAR'

    # Plant columns (district heating / cooling plants).
    if column.startswith('plant_pumping_'):
        return 'GRID'
    if column.startswith('plant_primary_') or column.startswith('plant_tertiary_'):
        # plant_primary_<NT>_<CARRIER>_kWh → parts[3]
        parts = column.split('_')
        if len(parts) >= 5:
            carrier = parts[3]
            return carrier if carrier in _ENERGY_CARRIERS else None
        return None

    # Building service / booster columns: Qhs_sys_<CARRIER>_kWh etc.
    if '_sys_' in column or '_booster_' in column:
        parts = column.split('_')
        if len(parts) >= 4:
            carrier = parts[2]
            return carrier if carrier in _ENERGY_CARRIERS else None

    return None


class EnergyByCarrierMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "energy-by-carrier"
    label = "Energy by Carrier (Hourly/Daily)"
    description = "Per-entity final energy consumption by carrier (includes district plants)"
    # Force to appear first within the Life Cycle Analysis category.
    order = 0

    def _read_entity_summary(self, whatif_name: str) -> Optional[pd.DataFrame]:
        """Read the buildings+plants summary (final_energy_buildings.csv) for a what-if."""
        if not whatif_name:
            return None
        path = self.locator.get_final_energy_buildings_file(whatif_name)
        if not os.path.exists(path):
            return None
        try:
            return pd.read_csv(path)
        except Exception as exc:
            logger.debug(f"Could not read {path}: {exc}")
            return None

    def _get_entity_files(self, whatif_name: str) -> list:
        """Return the list of per-entity (building + plant) CSV paths for a what-if."""
        summary = self._read_entity_summary(whatif_name)
        if summary is None or 'name' not in summary.columns:
            return []
        files = []
        for entity_name in summary['name'].tolist():
            # Both building and plant files share the same folder and `{name}.csv`
            # naming, so the building locator resolves both.
            path = self.locator.get_final_energy_building_file(entity_name, whatif_name)
            if os.path.exists(path):
                files.append(path)
        return files

    def _get_data_columns(self, parameters):
        """Return available carriers as a {choices, default} dict.

        Scans every entity's hourly file, maps each column to a carrier via
        :func:`_column_to_carrier`, and returns only the carriers actually
        present in the data. Choices are ``{value, label}`` dicts where the
        value is the internal code (e.g. ``GRID``) and the label is the
        user-facing name (e.g. ``grid_electricity``). Default is always
        ``GRID`` / ``grid_electricity`` when present.
        """
        whatif_name = parameters.get('whatif_name')
        if not whatif_name:
            return

        paths = self._get_entity_files(whatif_name)
        if not paths:
            return
        columns = get_columns_from_building_files(paths)
        if not columns:
            return columns

        present = set()
        for col in columns:
            carrier = _column_to_carrier(col)
            if carrier:
                present.add(carrier)

        available = [c for c in _ENERGY_CARRIERS if c in present]
        if not available:
            return []

        default = _DEFAULT_CARRIER if _DEFAULT_CARRIER in available else available[0]
        return {
            "choices": [
                {"value": c, "label": _CARRIER_DISPLAY_NAMES.get(c, c)}
                for c in available
            ],
            "default": default,
        }

    def _get_whatif_names(self) -> Optional[list]:
        """Return sorted list of what-if names that have final-energy results."""
        names = get_whatif_names(self.locator)
        return [name for name in names if os.path.isdir(self.locator.get_final_energy_folder(name))]

    def _get_results_files(self, parameters) -> list:
        whatif_name = parameters.get('whatif_name')
        if not whatif_name:
            return []
        return self._get_entity_files(whatif_name)

    @classmethod
    def expected_parameters(cls):
        return {
            'whatif_name':
                ParameterDefinition(
                    "what-if-name",
                    "string",
                    description="Select a what-if scenario with final-energy results",
                    options_generator="_get_whatif_names",
                    selector="choice",
                ),
            'data-column':
                ParameterDefinition(
                    "carrier",
                    "string",
                    description="Final energy carrier to visualize",
                    options_generator="_get_data_columns",
                    selector="choice",
                    depends_on=['whatif_name'],
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
                "Final Energy Hourly Files",
                file_locator="layer:_get_results_files",
                optional=True,
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generate hex-bin (single carrier) or stacked-column (multi carriers) output.

        Mirrors :class:`LifecycleEmissionsMapLayer.generate_data`: a single
        selected carrier renders as a ``HexagonLayer`` on the frontend, and
        a list of 2+ carriers renders as one ``ColumnLayer`` per carrier
        with a shared stack base, so segments visually sit on top of each
        other.
        """
        whatif_name = parameters.get('whatif_name')
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        raw_selection = parameters['data-column']
        if isinstance(raw_selection, list):
            selected = [c for c in raw_selection if c in _ENERGY_CARRIERS]
        elif isinstance(raw_selection, str):
            selected = [raw_selection] if raw_selection in _ENERGY_CARRIERS else []
        else:
            selected = []
        # Canonical order so stacks are predictable regardless of pick order.
        selected = [c for c in _ENERGY_CARRIERS if c in selected]
        is_stacked = len(selected) > 1

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        if not whatif_name or not selected:
            fallback = selected[0] if selected else None
            colour_pair = _CARRIER_COLOURS.get(fallback, ('brown_lighter', 'brown'))
            display_carrier = _CARRIER_DISPLAY_NAMES.get(fallback, fallback) if fallback else None
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": (
                        f"Energy by Carrier - {display_carrier} [kWh]"
                        if display_carrier else "Energy by Carrier [kWh]"
                    ),
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
                    "range": empty_range,
                    "stacked": False,
                },
            }

        summary = self._read_entity_summary(whatif_name)
        if summary is None or 'name' not in summary.columns:
            fallback = selected[0]
            colour_pair = _CARRIER_COLOURS.get(fallback, ('brown_lighter', 'brown'))
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Energy by Carrier - {_CARRIER_DISPLAY_NAMES.get(fallback, fallback)} [kWh]",
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
                    "range": empty_range,
                    "stacked": False,
                },
            }

        raw = self._get_data_columns(parameters)
        if isinstance(raw, dict):
            available_carriers = [c['value'] for c in raw.get('choices', [])]
        else:
            available_carriers = raw or []
        missing = [c for c in selected if c not in available_carriers]
        if missing:
            raise ValueError(f"Invalid carrier(s): {missing}")

        # Read the zone CRS. ``final_energy_buildings.csv`` stores building
        # x_coord/y_coord as zone-CRS centroids (see
        # cea.analysis.final_energy.calculation) and plant x_coord/y_coord in
        # the network-nodes shapefile CRS, which is the same zone CRS in a
        # CEA scenario.
        try:
            zone_gdf = gpd.read_file(self.locator.get_zone_geometry())
            source_crs = zone_gdf.crs
        except Exception as exc:
            logger.debug(f"Could not read zone geometry: {exc}")
            source_crs = None

        if source_crs is None:
            logger.debug("EnergyByCarrier: missing zone CRS; cannot project entities.")
            output['properties']['range'] = empty_range
            return output

        # Keep only rows that have usable coordinates.
        needs_xy = {'x_coord', 'y_coord'}
        if not needs_xy.issubset(summary.columns):
            logger.debug(
                "EnergyByCarrier: summary is missing x_coord/y_coord columns "
                f"(found: {list(summary.columns)}); cannot place entities."
            )
            output['properties']['range'] = empty_range
            return output

        usable = summary.dropna(subset=['x_coord', 'y_coord', 'name'])
        if usable.empty:
            logger.debug("EnergyByCarrier: no entities with valid coordinates.")
            output['properties']['range'] = empty_range
            return output

        entity_gdf = gpd.GeoDataFrame(
            {'name': usable['name'].tolist()},
            geometry=gpd.points_from_xy(
                usable['x_coord'].astype(float),
                usable['y_coord'].astype(float),
            ),
            crs=source_crs,
        )
        centroids = entity_gdf.geometry.to_crs(get_geographic_coordinate_system())
        entity_names = entity_gdf['name'].tolist()

        def get_entity_values(entity_name, centroid):
            """Return {carrier: period_sum} for this entity over the selected period."""
            entity_file = self.locator.get_final_energy_building_file(entity_name, whatif_name)
            if not os.path.exists(entity_file):
                logger.debug(f"EnergyByCarrier: missing file for {entity_name}")
                return None
            try:
                header = pd.read_csv(entity_file, nrows=0).columns
            except Exception as exc:
                logger.debug(f"EnergyByCarrier: header read failed for {entity_name}: {exc}")
                return None

            # Bucket columns by selected carrier up front so we only read
            # each CSV once.
            buckets = {cat: [] for cat in selected}
            for col in header:
                mapped = _column_to_carrier(col)
                if mapped in buckets:
                    buckets[mapped].append(col)

            flat_cols = [c for cols in buckets.values() for c in cols]
            flat_cols = list(dict.fromkeys(flat_cols))
            if not flat_cols:
                per_carrier = {cat: 0.0 for cat in selected}
            else:
                try:
                    df = pd.read_csv(entity_file, usecols=flat_cols)
                except Exception as exc:
                    logger.debug(f"EnergyByCarrier: data read failed for {entity_name}: {exc}")
                    return None
                per_carrier = {}
                for cat in selected:
                    cols = buckets[cat]
                    if not cols:
                        per_carrier[cat] = 0.0
                        continue
                    series = df[cols].sum(axis=1).astype(float)
                    if start < end:
                        per_carrier[cat] = float(series.iloc[start:end + 1].sum())
                    else:
                        per_carrier[cat] = float(
                            series.iloc[start:].sum() + series.iloc[:end + 1].sum()
                        )

            return {
                'name': entity_name,
                'position': [centroid.x, centroid.y],
                'values': per_carrier,
            }

        entities = [get_entity_values(name, c) for name, c in zip(entity_names, centroids)]
        entities = [e for e in entities if e is not None]

        if not entities:
            fallback = selected[0]
            colour_pair = _CARRIER_COLOURS.get(fallback, ('brown_lighter', 'brown'))
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Energy by Carrier - {_CARRIER_DISPLAY_NAMES.get(fallback, fallback)} [kWh]",
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
                    "range": empty_range,
                    "stacked": False,
                },
            }

        if not is_stacked:
            carrier = selected[0]
            display_carrier = _CARRIER_DISPLAY_NAMES.get(carrier, carrier)
            colour_pair = _CARRIER_COLOURS.get(carrier, ('brown_lighter', 'brown'))
            data_points = [
                {
                    "position": e["position"],
                    "value": e["values"][carrier],
                    # Extra fields for the HexagonLayer hover tooltip.
                    "name": e["name"],
                    "category": carrier,
                }
                for e in entities
            ]
            period_values = [p["value"] for p in data_points]
            nonzero_totals = sum(1 for p in period_values if p > 0)
            logger.debug(
                f"EnergyByCarrier[{carrier}]: {len(entities)} entities, "
                f"{nonzero_totals} with non-zero totals; "
                f"total_max={max(period_values) if period_values else 0:.2f}"
            )
            return {
                "data": data_points,
                "properties": {
                    "name": self.name,
                    "label": f"Energy by Carrier - {display_carrier} [kWh]",
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
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

        # Stacked-multi path: one ColumnLayer per carrier on the frontend.
        categories_payload = []
        for cat in selected:
            _, darker = _CARRIER_COLOURS.get(cat, ('brown_lighter', 'brown'))
            hex_colour = color_to_hex(darker)
            r = int(hex_colour[1:3], 16)
            g = int(hex_colour[3:5], 16)
            b = int(hex_colour[5:7], 16)
            categories_payload.append({
                "name": _CARRIER_DISPLAY_NAMES.get(cat, cat),
                # Internal code retained so the frontend can key values.
                "key": cat,
                "colour": hex_colour,
                "rgb": [r, g, b],
            })

        stack_totals = [
            sum(max(e["values"].get(c, 0.0), 0.0) for c in selected)
            for e in entities
        ]

        # Transform `values` so the frontend can key by display name (which
        # is what categories[i].name carries in the stacked payload).
        data_points = []
        for e in entities:
            renamed_values = {
                _CARRIER_DISPLAY_NAMES.get(c, c): float(e["values"].get(c, 0.0))
                for c in selected
            }
            data_points.append({
                "name": e["name"],
                "position": e["position"],
                "values": renamed_values,
            })

        return {
            "data": data_points,
            "properties": {
                "name": self.name,
                "label": "Energy by Carrier - stacked [kWh]",
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


_LIFECYCLE_EMISSION_CATEGORIES = ['operation', 'production', 'demolition', 'biogenic']
_DEFAULT_LIFECYCLE_CATEGORY = 'operation'

# Colour gradient per category, keyed to the CEA emission-timeline plot
# palette (see cea.visualisation.special.emission_timeline). Each entry is
# a (lighter, darker) pair of CEA named colours for the hex legend gradient.
_LIFECYCLE_CATEGORY_COLOURS = {
    # 'operation' is not a single category in the timeline plot — it is the
    # sum of electricity/heating/cooling/DHW — so we reuse the electricity
    # (green) colour which is typically the dominant operational component.
    'operation': ('green_lighter', 'green'),
    'production': ('purple_lighter', 'purple'),
    'demolition': ('brown_lighter', 'brown'),
    'biogenic': ('grey_lighter', 'grey'),
}


class LifecycleEmissionsMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "lifecycle-emissions"
    label = "Lifecycle Emissions (Annual)"
    description = ""

    def _get_data_columns(self, parameters):
        """Return the high-level emission categories present in this what-if.

        Each timeline CSV has columns like ``operation_electricity_kgCO2``,
        ``production_windows_kgCO2`` etc. We aggregate by prefix and expose
        only the four categories: operation, production, demolition,
        biogenic — ordered canonically, with ``operation`` as the default.
        """
        buildings = self.locator.get_zone_building_names()
        whatif_name = parameters.get('whatif_name')

        if not buildings or not whatif_name:
            return

        paths = [self.locator.get_emissions_whatif_building_timeline_file(b, whatif_name) for b in buildings]
        columns = get_columns_from_building_files(paths)
        if not columns:
            return columns

        present = set()
        for col in columns:
            for cat in _LIFECYCLE_EMISSION_CATEGORIES:
                if col.startswith(f"{cat}_"):
                    present.add(cat)
                    break

        available = [c for c in _LIFECYCLE_EMISSION_CATEGORIES if c in present]
        if not available:
            return []

        default = (
            _DEFAULT_LIFECYCLE_CATEGORY
            if _DEFAULT_LIFECYCLE_CATEGORY in available
            else available[0]
        )
        return {
            "choices": [{"value": c, "label": c} for c in available],
            "default": default,
        }

    def _get_whatif_names(self) -> Optional[list]:
        """Return sorted list of what-if names that have lifecycle analysis results."""
        names = get_whatif_names(self.locator)
        return [name for name in names if os.path.exists(self.locator.get_emissions_whatif_timeline_file(name))]

    def _get_results_files(self, parameters) -> list:
        whatif_name = parameters.get('whatif_name')
        
        if not whatif_name:
            return []

        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_emissions_whatif_building_timeline_file(b, whatif_name) for b in buildings]

    def _get_period_range(self, parameters) -> list:
        """Get the valid period range from available data"""
        whatif_name = parameters.get('whatif_name')
        if not whatif_name:
            return [None, None]

        try:
            buildings = self.locator.get_zone_building_names()
            timeline_df = self.locator.get_emissions_whatif_building_timeline_file(buildings[0], whatif_name)
            df = pd.read_csv(timeline_df)
            df['year'] = period_to_year(df['period'])
            return [int(df['year'].min()), int(df['year'].max())]
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return [None, None]


    @classmethod
    def expected_parameters(cls):
        return {
            'whatif_name':
                ParameterDefinition(
                    "what-if-name",
                    "string",
                    description="Select a what-if scenario with emission results",
                    options_generator="_get_whatif_names",
                    selector="choice",
                ),
            'data-column':
                ParameterDefinition(
                    "emission/category",
                    "string",
                    description="Lifecycle emission category to visualise",
                    options_generator="_get_data_columns",
                    selector="choice",
                    depends_on=['whatif_name'],
                    multi=True,
                ),
            'timeline':
                ParameterDefinition(
                    "Period",
                    "array",
                    description="Period to generate the data based on years",
                    selector="slider",
                    options_generator="_get_period_range",
                    depends_on=['whatif_name']
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
                optional=True,  # Individual building files may be missing
            ),
        ]

    def _read_entity_summary(self, whatif_name: str) -> Optional[pd.DataFrame]:
        """Read emissions_buildings.csv (contains both buildings and plants)."""
        if not whatif_name:
            return None
        path = self.locator.get_emissions_whatif_buildings_file(whatif_name)
        if not os.path.exists(path):
            return None
        try:
            return pd.read_csv(path)
        except Exception as exc:
            logger.debug(f"Could not read lifecycle emissions summary {path}: {exc}")
            return None

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer.

        Single-category (string or 1-element list): HexagonLayer-style output
        with a single value per entity.
        Multi-category (list with 2+ entries): stacked-column output with
        per-category values per entity; the frontend renders one
        ColumnLayer per category.

        Entities include both zone buildings *and* district plants (read
        from emissions_buildings.csv, which has x_coord/y_coord for both).
        """

        whatif_name = parameters.get('whatif_name')

        raw_selection = parameters['data-column']
        period = parameters['timeline']
        start, end = period

        # Normalize selection to a list; filter to known categories and
        # preserve canonical order (operation → production → demolition → biogenic).
        if isinstance(raw_selection, list):
            selected = [c for c in raw_selection if c in _LIFECYCLE_EMISSION_CATEGORIES]
        elif isinstance(raw_selection, str):
            selected = [raw_selection] if raw_selection in _LIFECYCLE_EMISSION_CATEGORIES else []
        else:
            selected = []

        selected = [c for c in _LIFECYCLE_EMISSION_CATEGORIES if c in selected]
        is_stacked = len(selected) > 1

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        # Enumerate entities (buildings + plants) from emissions_buildings.csv
        # which is the only source with plant coordinates and a stable list.
        summary = self._read_entity_summary(whatif_name) if whatif_name else None
        entity_rows = None
        source_crs = None
        if summary is not None and {'name', 'x_coord', 'y_coord'}.issubset(summary.columns):
            entity_rows = summary.dropna(subset=['name', 'x_coord', 'y_coord'])
            try:
                zone_gdf = gpd.read_file(self.locator.get_zone_geometry())
                source_crs = zone_gdf.crs
            except Exception as exc:
                logger.debug(f"LifecycleEmissions: could not read zone CRS: {exc}")
                source_crs = None

        if entity_rows is None or entity_rows.empty or source_crs is None or not whatif_name or not selected:
            fallback = selected[0] if selected else None
            colour_pair = _LIFECYCLE_CATEGORY_COLOURS.get(
                fallback, ('grey_lighter', 'black')
            )
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": (
                        f"Lifecycle Emissions - {fallback} [kgCO\u2082e]"
                        if fallback else "Lifecycle Emissions [kgCO\u2082e]"
                    ),
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
                    "range": empty_range,
                    "stacked": False,
                },
            }

        def _coerce_years(series: pd.Series) -> pd.Series:
            """Robustly convert a timeline 'period' column to integer years.

            Handles 'Y_XXXX' strings, plain integer/float years, and mixed.
            """
            if pd.api.types.is_numeric_dtype(series):
                return series.astype(int)
            extracted = series.astype(str).str.extract(r'(\d{4})')[0]
            return pd.to_numeric(extracted, errors='coerce').astype('Int64')

        def read_category_values(entity_name):
            """Return {category: period_sum} for the entity's timeline file."""
            try:
                entity_file = self.locator.get_emissions_whatif_building_timeline_file(
                    entity_name, whatif_name
                )
                if not os.path.exists(entity_file):
                    logger.info(
                        f"LifecycleEmissions: missing timeline file for {entity_name}: {entity_file}"
                    )
                    return None

                # Read the full file once — plant timelines may have the
                # period as the DataFrame index rather than a column, and
                # are small (1 row per year) so cost is negligible.
                df = pd.read_csv(entity_file)

                # Locate the period column. It may be named 'period',
                # 'Unnamed: 0' (anonymous index), or be the actual index.
                period_col = None
                if 'period' in df.columns:
                    period_col = 'period'
                else:
                    for candidate in df.columns:
                        if candidate.lower().startswith('unnamed') or candidate == '':
                            period_col = candidate
                            break

                if period_col is None:
                    # Fall back to the first column.
                    period_col = df.columns[0]

                years = _coerce_years(df[period_col])
                if years.isna().all():
                    logger.info(
                        f"LifecycleEmissions: could not parse period column '{period_col}' for {entity_name}"
                    )
                    return None
                df = df.loc[years.notna()].copy()
                years = years.dropna().astype(int)

                result = {}
                matched_any = False
                for cat in selected:
                    cols = [c for c in df.columns if c.startswith(f"{cat}_")]
                    if cols:
                        matched_any = True
                        series = df[cols].sum(axis=1).astype(float)
                    else:
                        series = pd.Series(0.0, index=df.index)
                    series.index = years.values
                    result[cat] = float(series.loc[start:end].sum())

                if not matched_any:
                    logger.info(
                        f"LifecycleEmissions: no category columns for {entity_name}; "
                        f"columns={list(df.columns)}, selected={selected}"
                    )
                return result
            except Exception as exc:
                logger.info(
                    f"LifecycleEmissions: error reading {entity_name}: {exc}"
                )
                return None

        # Project entity coordinates (zone CRS) to geographic lon/lat.
        entity_gdf = gpd.GeoDataFrame(
            {'name': entity_rows['name'].tolist()},
            geometry=gpd.points_from_xy(
                entity_rows['x_coord'].astype(float),
                entity_rows['y_coord'].astype(float),
            ),
            crs=source_crs,
        )
        centroids = entity_gdf.geometry.to_crs(get_geographic_coordinate_system())

        entities = []
        plant_names_in_summary = set()
        if 'type' in entity_rows.columns:
            plant_names_in_summary = set(
                entity_rows[entity_rows['type'] == 'plant']['name'].tolist()
            )

        for entity_name, centroid in zip(entity_gdf['name'].tolist(), centroids):
            cat_values = read_category_values(entity_name)
            if cat_values is None:
                continue
            entities.append({
                "name": entity_name,
                "position": [centroid.x, centroid.y],
                "values": cat_values,
            })

        entity_names_rendered = {e['name'] for e in entities}
        plants_rendered = entity_names_rendered & plant_names_in_summary
        logger.info(
            f"LifecycleEmissions: {len(entities)}/{len(entity_gdf)} entities rendered, "
            f"plants in summary={len(plant_names_in_summary)}, "
            f"plants rendered={len(plants_rendered)}, "
            f"selected categories={selected}"
        )

        if not entities:
            fallback = selected[0]
            colour_pair = _LIFECYCLE_CATEGORY_COLOURS.get(fallback, ('grey_lighter', 'black'))
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Lifecycle Emissions - {fallback} [kgCO\u2082e]",
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
                    "range": empty_range,
                    "stacked": False,
                },
            }

        if not is_stacked:
            # Single-category path: mirror the previous HexagonLayer shape.
            category = selected[0]
            colour_pair = _LIFECYCLE_CATEGORY_COLOURS.get(category, ('grey_lighter', 'black'))
            data_points = [
                {
                    "position": e["position"],
                    "value": e["values"][category],
                    # Extra fields for the hover tooltip on the HexagonLayer
                    # path: HexagonLayer exposes the source records via
                    # `object.points`, so the frontend can read these.
                    "name": e["name"],
                    "category": category,
                }
                for e in entities
            ]
            period_values = [p["value"] for p in data_points]
            return {
                "data": data_points,
                "properties": {
                    "name": self.name,
                    "label": f"Lifecycle Emissions - {category} [kgCO\u2082e]",
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex(colour_pair[0]),
                            color_to_hex(colour_pair[1]),
                        ],
                        "points": 12,
                    },
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

        # Stacked-multi path: keep per-category values on each entity and
        # expose a per-category colour list so the frontend can render one
        # ColumnLayer per category with a shared stack base.
        categories_payload = []
        for cat in selected:
            _, darker = _LIFECYCLE_CATEGORY_COLOURS.get(cat, ('grey_lighter', 'black'))
            hex_colour = color_to_hex(darker)
            # hex "#rrggbb" → [R, G, B] for deck.gl
            r = int(hex_colour[1:3], 16)
            g = int(hex_colour[3:5], 16)
            b = int(hex_colour[5:7], 16)
            categories_payload.append({
                "name": cat,
                "colour": hex_colour,
                "rgb": [r, g, b],
            })

        stack_totals = [
            sum(max(e["values"].get(c, 0.0), 0.0) for c in selected)
            for e in entities
        ]

        return {
            "data": entities,
            "properties": {
                "name": self.name,
                "label": "Lifecycle Emissions - stacked [kgCO\u2082e]",
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


class OperationalEmissionsMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "operational-emissions"
    label = "Operational Emissions (Hourly/Daily)"
    description = ""

    def _get_data_columns(self, parameters) -> Optional[list]:
        buildings = self.locator.get_zone_building_names()
        whatif_name = parameters.get('whatif_name')

        if not buildings or not whatif_name:
            return

        paths = [self.locator.get_emissions_whatif_building_file(b, whatif_name) for b in buildings]
        return get_columns_from_building_files(paths)

    def _get_whatif_names(self) -> Optional[list]:
        """Return sorted list of what-if names that have operational emissions results."""
        names = get_whatif_names(self.locator)
        return [name for name in names if os.path.exists(self.locator.get_emissions_whatif_operational_file(name))]

    def _get_results_files(self, parameters) -> list:
        whatif_name = parameters.get('whatif_name')

        if not whatif_name:
            return []

        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_emissions_whatif_building_file(b, whatif_name) for b in buildings]

    @classmethod
    def expected_parameters(cls):
        return {
            'whatif_name':
                ParameterDefinition(
                    "What-if scenario",
                    "string",
                    description="Select a what-if scenario with operational emission results",
                    options_generator="_get_whatif_names",
                    selector="choice",
                ),
            'data-column':
                ParameterDefinition(
                    "Data Column",
                    "string",
                    description="Data column to use",
                    options_generator="_get_data_columns",
                    selector="choice",
                    depends_on=['whatif_name']
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
                optional=True,  # Individual building files may be missing
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""

        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()
        whatif_name = parameters.get('whatif_name')
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        data_column = parameters['data-column']

        if data_column is None or data_column not in self._get_data_columns(parameters):
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

        # Filter buildings that exist in geometry
        buildings, _, building_centroids = safe_filter_buildings_with_geometry(self.locator, buildings)

        if not buildings or not whatif_name:
            output['properties']['range'] = {
                'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
                'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0}
            }
            return output

        def get_data(building, centroid):
            try:
                building_file = self.locator.get_emissions_whatif_building_file(building, whatif_name)
                if not os.path.exists(building_file):
                    return None

                data = pd.read_csv(building_file, usecols=[data_column])[data_column]

                total_min = 0
                total_max = data.sum()

                if start < end:
                    period_value = data.iloc[start:end + 1].sum()
                else:
                    period_value = data.iloc[start:].sum() + data.iloc[:end + 1].sum()
                period_min = period_value
                period_max = period_value

                data_point = {"position": [centroid.x, centroid.y], "value": period_value}

                return total_min, total_max, period_min, period_max, data_point
            except Exception as e:
                print(f"Warning: Error reading operational emissions for {building}: {e}")
                return None

        values = [get_data(building, centroid) for building, centroid in zip(buildings, building_centroids)]

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


class EmissionTimelineMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "emission-timeline"
    label = "Emission Timeline"
    description = ""

    def _get_whatif_names(self) -> Optional[list]:
        """Return sorted list of what-if names that have emission results."""
        names = get_whatif_names(self.locator)
        return [name for name in names if os.path.exists(self.locator.get_emissions_whatif_timeline_file(name))]
    
    def _get_results_files(self, parameters) -> list:
        whatif_name = parameters.get('whatif_name')
        
        if not whatif_name:
            return []

        buildings = self.locator.get_zone_building_names()
        return [self.locator.get_emissions_whatif_building_timeline_file(b, whatif_name) for b in buildings]

    def _get_period_range(self, parameters) -> list:
        """Get the valid period range from available data"""
        whatif_name = parameters.get('whatif_name')

        if whatif_name is None:
            return [None, None]

        try:
            timeline_df = self.locator.get_emissions_whatif_timeline_file(whatif_name)
            df = pd.read_csv(timeline_df)
            df['year'] = period_to_year(df['period'])
            return [int(df['year'].min()), int(df['year'].max())]
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return [None, None]

    @classmethod
    def expected_parameters(cls):
        return {
            'whatif_name':
                ParameterDefinition(
                    "What-if scenario",
                    "string",
                    description="Select a what-if scenario with emission results",
                    options_generator="_get_whatif_names",
                    selector="choice",
                ),
            'timeline':
                ParameterDefinition(
                    "Period",
                    "array",
                    description="Period to generate the data based on years",
                    selector="slider",
                    options_generator="_get_period_range",
                    depends_on=['whatif_name']
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


class AnthropogenicHeatMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "anthropogenic-heat-rejection"
    label = "Anthropogenic Heat Rejection (Hourly/Daily)"
    description = "Visualise heat rejection from building systems and district cooling plants"

    def _get_whatif_names(self) -> Optional[list]:
        """Return sorted list of what-if names that have heat rejection results."""
        base = os.path.join(self.locator.scenario, 'outputs', 'data', 'analysis')
        if not os.path.exists(base):
            return None
        names = [
            d for d in os.listdir(base)
            if os.path.exists(os.path.join(base, d, 'heat', 'heat_rejection_buildings.csv'))
        ]
        return sorted(names) or None

    def _get_results_files(self, parameters):
        """Return required files for caching"""
        whatif_name = parameters.get('whatif_name')
        if not whatif_name:
            return []
        buildings_file = self.locator.get_heat_rejection_whatif_buildings_file(whatif_name)
        if not os.path.exists(buildings_file):
            return []

        buildings_df = pd.read_csv(buildings_file)
        entity_names = buildings_df['name'].tolist()

        files = [buildings_file]
        for entity_name in entity_names:
            entity_file = self.locator.get_heat_rejection_whatif_building_file(entity_name, whatif_name)
            if os.path.exists(entity_file):
                files.append(entity_file)

        return files

    @classmethod
    def expected_parameters(cls):
        return {
            'whatif_name':
                ParameterDefinition(
                    "What-if scenario",
                    "string",
                    description="Select a what-if scenario with heat rejection results",
                    options_generator="_get_whatif_names",
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
                file_locator="layer:_get_results_files",
                optional=True,
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the hexagon heatmap output for anthropogenic heat rejection"""

        whatif_name = parameters.get('whatif_name')
        if not whatif_name:
            return {"data": [], "properties": {"name": self.name, "label": "Anthropogenic Heat Rejection", "description": self.description}}

        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        buildings_file = self.locator.get_heat_rejection_whatif_buildings_file(whatif_name)
        if not os.path.exists(buildings_file):
            return {"data": [], "properties": {"name": self.name, "label": "Anthropogenic Heat Rejection", "description": self.description}}

        buildings_df = pd.read_csv(buildings_file)
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
            entity_file = self.locator.get_heat_rejection_whatif_building_file(entity_name, whatif_name)

            if not os.path.exists(entity_file):
                return 0.0, 0.0, {"position": [centroid.x, centroid.y], "value": 0.0}

            entity_df = pd.read_csv(entity_file)

            total_value = entity_df['heat_rejection_kW'].sum()

            period_df = entity_df.iloc[start:end+1]
            period_value = period_df['heat_rejection_kW'].sum()

            data_point = {"position": [centroid.x, centroid.y], "value": period_value}

            return total_value, period_value, data_point

        buildings_df = buildings_df.set_index('name')

        zone_gdf = gpd.read_file(self.locator.get_zone_geometry())

        entity_gdf = gpd.GeoDataFrame(
            buildings_df.loc[entity_names],
            geometry=gpd.points_from_xy(
                buildings_df.loc[entity_names]['x_coord'],
                buildings_df.loc[entity_names]['y_coord']
            ),
            crs=zone_gdf.crs
        )
        entity_centroids = entity_gdf.geometry.to_crs(CRS.from_epsg(4326))

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

        non_zero_data = [(t, p, d) for t, p, d in zip(total_values, period_values, data) if p > 0 or t > 0]

        if non_zero_data:
            total_values, period_values, data = zip(*non_zero_data)
        else:
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
