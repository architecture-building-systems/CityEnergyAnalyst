from typing import Optional
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.life_cycle_analysis import LifeCycleAnalysisCategory
from cea.plots.colors import color_to_hex
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from cea.visualisation.format.plot_colours import (
    CARRIER_COLOURS as _CARRIER_COLOURS,
    DEFAULT_CARRIER_COLOURS as _DEFAULT_CARRIER_COLOURS,
)

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
    """Return what-if names ordered by most-recently modified first.

    The dropdown that consumes this list takes its default value from the
    first entry, so a fresh `cea final-energy` / `cea emissions` / etc.
    run will surface as the auto-selected what-if in the LCA map layers
    immediately after the success notification's "View Results" click.

    - Skips hidden entries (e.g. macOS ``.DS_Store``) and non-directories.
    - Sort key: ``(-mtime, name)`` → newest first, ties broken alphabetically.
    """
    base = locator.get_analysis_parent_folder()
    if not os.path.isdir(base):
        return []
    entries = []
    for name in os.listdir(base):
        if name.startswith('.'):
            continue
        path = os.path.join(base, name)
        if not os.path.isdir(path):
            continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0.0
        entries.append((name, mtime))
    entries.sort(key=lambda x: (-x[1], x[0]))
    return [name for name, _ in entries]


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

# Carrier default for first-load selection. Must match the ``feedstock_file``
# used for the electricity row in ``ENERGY_CARRIERS.csv`` (almost always
# ``GRID``). Looked up via :func:`electricity_carrier` when available and
# falls back to the string literal if not.
_DEFAULT_CARRIER_FALLBACK = 'GRID'

# Carrier colour palette — resolved via the canonical ``CARRIER_COLOURS``
# dict (imported at module top) so the HexagonLayer gradient, the
# stacked ColumnLayer segments, bar plots, and the energy sankey all
# render a given carrier identically. User-added carriers (e.g.
# ``PROPANE``) fall back to :data:`_DEFAULT_CARRIER_COLOURS`.


def _column_to_carrier(column: str) -> Optional[str]:
    """Map a raw ``*_kWh`` column name to its carrier code (``GRID``,
    ``NATURALGAS``, ``SOLAR``, …) or None.

    Mirrors the aggregation rules used by
    ``cea.analysis.final_energy.calculation._aggregate_hourly_data``.
    Carrier codes returned here are the same ``feedstock_file`` values
    that live in ``ENERGY_CARRIERS.csv`` — no lowercase-alias layer.
    """
    if not column.endswith('_kWh') or column in _ENERGY_DEMAND_ROLLUP_COLUMNS:
        return None

    # Diagnostic *_dumped_kWh columns (SC tank surplus) are not a delivered
    # carrier — exclude from the Energy-by-Carrier map.
    if column.endswith('_dumped_kWh'):
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
        # Pumping electricity column is ``plant_pumping_<NT>_<CARRIER>_kWh``;
        # parse the carrier token instead of assuming ``GRID``.
        parts = column.split('_')
        if len(parts) >= 5:
            return parts[3]
        return None
    if column.startswith('plant_primary_') or column.startswith('plant_tertiary_'):
        # plant_primary_<NT>_<CARRIER>_kWh → parts[3] = UPPERCASE carrier
        parts = column.split('_')
        if len(parts) >= 5:
            return parts[3]
        return None

    # Building service / booster columns: Qhs_sys_<CARRIER>_kWh etc.
    if '_sys_' in column or '_booster_' in column:
        parts = column.split('_')
        if len(parts) >= 4:
            return parts[2]

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
        """Return available carriers as a ``{choices, default}`` dict.

        The full carrier list comes from the scenario's ``ENERGY_CARRIERS.csv``
        (plus ``SOLAR`` as a routing-only carrier that isn't in the feedstock
        library). The dropdown is then filtered to just the carriers whose
        columns actually appear in this what-if's hourly files, so users
        only see carriers with data. Default selection is the scenario's
        electricity carrier (``GRID`` unless renamed).
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

        from cea.technologies.energy_carriers import (
            available_carriers, electricity_carrier,
        )
        try:
            known = available_carriers(self.locator) | {'SOLAR'}
        except Exception:
            known = {'SOLAR'}
        try:
            default_carrier = electricity_carrier(self.locator)
        except Exception:
            default_carrier = _DEFAULT_CARRIER_FALLBACK

        present = set()
        for col in columns:
            carrier = _column_to_carrier(col)
            if carrier:
                present.add(carrier)

        available = sorted(known & present)
        if not available:
            return []

        default = default_carrier if default_carrier in available else available[0]
        return {
            "choices": [
                {"value": c, "label": c}
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
            selected = list(raw_selection)
        elif isinstance(raw_selection, str):
            selected = [raw_selection]
        else:
            selected = []
        # Stable alphabetical order so stacks are predictable regardless of
        # pick order. Carriers are validated against the dynamic list from
        # ``_get_data_columns`` further down.
        selected = sorted(dict.fromkeys(selected))
        is_stacked = len(selected) > 1

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        if not whatif_name or not selected:
            fallback = selected[0] if selected else None
            colour_pair = _CARRIER_COLOURS.get(fallback, _DEFAULT_CARRIER_COLOURS)
            display_carrier = fallback if fallback else None
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": (
                        f"Carrier - {display_carrier} [kWh]"
                        if display_carrier else "Carrier [kWh]"
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
            colour_pair = _CARRIER_COLOURS.get(fallback, _DEFAULT_CARRIER_COLOURS)
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Carrier - {fallback} [kWh]",
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

        # Factory for the empty-range response used by the early-exit
        # branches below. `fallback` is always non-None here because
        # `selected` was already validated earlier in the function.
        def _empty_output(fallback):
            colour_pair = _CARRIER_COLOURS.get(fallback, _DEFAULT_CARRIER_COLOURS)
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Carrier - {fallback} [kWh]",
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
            return _empty_output(selected[0])

        # Keep only rows that have usable coordinates.
        needs_xy = {'x_coord', 'y_coord'}
        if not needs_xy.issubset(summary.columns):
            logger.debug(
                "EnergyByCarrier: summary is missing x_coord/y_coord columns "
                f"(found: {list(summary.columns)}); cannot place entities."
            )
            return _empty_output(selected[0])

        usable = summary.dropna(subset=['x_coord', 'y_coord', 'name'])
        if usable.empty:
            logger.debug("EnergyByCarrier: no entities with valid coordinates.")
            return _empty_output(selected[0])

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
            colour_pair = _CARRIER_COLOURS.get(fallback, _DEFAULT_CARRIER_COLOURS)
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Carrier - {fallback} [kWh]",
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
            display_carrier = carrier
            colour_pair = _CARRIER_COLOURS.get(carrier, _DEFAULT_CARRIER_COLOURS)
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
                    "label": f"Carrier - {display_carrier} [kWh]",
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
            _, darker = _CARRIER_COLOURS.get(cat, _DEFAULT_CARRIER_COLOURS)
            hex_colour = color_to_hex(darker)
            r = int(hex_colour[1:3], 16)
            g = int(hex_colour[3:5], 16)
            b = int(hex_colour[5:7], 16)
            categories_payload.append({
                "name": cat,
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
                c: float(e["values"].get(c, 0.0))
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
                "label": "Carrier - stacked [kWh]",
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


# --- Operational Emissions constants and helpers ---

# Top-level category parameter. Mirrors the plot's `y-category-to-plot`.
_OPERATIONAL_CATEGORIES = ['operation', 'energy_carrier']

# Service identifiers surfaced to the user as lowercase snake_case display
# names (matches the unified UI layer — see [plots-operational-emissions]).
_OPERATION_SERVICES = [
    'electricity',
    'space_heating',
    'space_cooling',
    'domestic_hot_water',
    'district_heating',
    'district_cooling',
    'solar_pv_electricity',
    'solar_pvt_electricity',
    'solar_pvt_thermal',
    'solar_thermal',
]

# Colour gradient per service display name for the stacked ColumnLayer.
_OPERATION_SERVICE_COLOURS = {
    'electricity':           ('green_lighter', 'green'),
    'space_heating':         ('red_lighter', 'red'),
    'space_cooling':         ('blue_lighter', 'blue'),
    'domestic_hot_water':    ('orange_lighter', 'orange'),
    'district_heating':      ('red_light', 'red_dark'),
    'district_cooling':      ('blue_light', 'blue'),
    'solar_pv_electricity':  ('yellow_lighter', 'yellow'),
    'solar_pvt_electricity': ('brown_lighter', 'brown'),
    'solar_pvt_thermal':     ('purple_lighter', 'purple'),
    'solar_thermal':         ('yellow_light', 'brown'),
}
# Per-carrier colours for the stacked ColumnLayer. Keys are UPPERCASE
# ``feedstock_file`` codes (same as ``ENERGY_CARRIERS.csv``). Each darker
# colour is unique — shared with :data:`_CARRIER_COLOURS` above so a
# given carrier renders the same way in both map layers. User-added
# carriers fall back to :data:`_DEFAULT_CARRIER_COLOURS` (defined above).
_OPERATIONAL_CARRIER_COLOURS = _CARRIER_COLOURS


def _op_column_to_service(column: str) -> Optional[str]:
    """Map an operational-emissions column to a high-level service display
    name, or None.

    Internal CSV column formats (unchanged):
      Qhs_sys_<CARRIER>_kgCO2e          → space_heating
      Qhs_booster_<CARRIER>_kgCO2e      → space_heating
      Qcs_sys_<CARRIER>_kgCO2e          → space_cooling
      Qww_sys_<CARRIER>_kgCO2e          → domestic_hot_water
      Qww_booster_<CARRIER>_kgCO2e      → domestic_hot_water
      E_sys_<CARRIER>_kgCO2e            → electricity
      plant_{primary|tertiary|pumping}_DH_<CARRIER>_kgCO2e → district_heating
      plant_{primary|tertiary|pumping}_DC_<CARRIER>_kgCO2e → district_cooling
    Solar offset columns (negative):
      PV_E_offset_kgCO2e   → solar_pv_electricity
      PVT_E_offset_kgCO2e  → solar_pvt_electricity
      PVT_Q_offset_kgCO2e  → solar_pvt_thermal
      SC_Q_offset_kgCO2e   → solar_thermal
    """
    if not column.endswith('_kgCO2e'):
        return None
    if column == 'PV_E_offset_kgCO2e':
        return 'solar_pv_electricity'
    if column == 'PVT_E_offset_kgCO2e':
        return 'solar_pvt_electricity'
    if column == 'PVT_Q_offset_kgCO2e':
        return 'solar_pvt_thermal'
    if column == 'SC_Q_offset_kgCO2e':
        return 'solar_thermal'
    if column.startswith('E_sys_'):
        return 'electricity'
    if column.startswith('Qhs_sys_') or column.startswith('Qhs_booster_'):
        return 'space_heating'
    if column.startswith('Qcs_sys_'):
        return 'space_cooling'
    if column.startswith('Qww_sys_') or column.startswith('Qww_booster_'):
        return 'domestic_hot_water'
    if (
        column.startswith('plant_primary_DH_')
        or column.startswith('plant_tertiary_DH_')
        or column.startswith('plant_pumping_DH_')
    ):
        return 'district_heating'
    if (
        column.startswith('plant_primary_DC_')
        or column.startswith('plant_tertiary_DC_')
        or column.startswith('plant_pumping_DC_')
    ):
        return 'district_cooling'
    return None


def _op_column_to_carrier(column: str) -> Optional[str]:
    """Map an operational-emissions column to its carrier code (``GRID``,
    ``NATURALGAS``, …) or None.

    Excludes solar offsets since those are not a physical fuel carrier.
    The carrier sits at the last underscore-separated token before the
    ``_kgCO2e`` suffix (e.g. ``Qhs_sys_NATURALGAS_kgCO2e``). Callers
    filter against the scenario's ``ENERGY_CARRIERS.csv`` so a spurious
    non-carrier token can't leak through.
    """
    if not column.endswith('_kgCO2e'):
        return None
    if 'offset' in column:
        return None
    stripped = column[: -len('_kgCO2e')]
    parts = stripped.split('_')
    if not parts:
        return None
    return parts[-1] or None


class OperationalEmissionsMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "operational-emissions"
    label = "Operational Emissions (Hourly/Daily)"
    description = ""

    def _read_entity_summary(self, whatif_name: str) -> Optional[pd.DataFrame]:
        """Read emissions_buildings.csv (buildings + plants with coords)."""
        if not whatif_name:
            return None
        path = self.locator.get_emissions_whatif_buildings_file(whatif_name)
        if not os.path.exists(path):
            return None
        try:
            return pd.read_csv(path)
        except Exception as exc:
            logger.debug(f"OperationalEmissions: could not read {path}: {exc}")
            return None

    def _get_categories(self, parameters):
        return {
            'choices': [{'value': c, 'label': c} for c in _OPERATIONAL_CATEGORIES],
            'default': 'operation',
        }

    def _get_data_columns(self, parameters):
        """Return operation services or energy carriers based on the
        currently-selected category, filtered to the ones actually
        present in the selected what-if's hourly emissions files.
        """
        whatif_name = parameters.get('whatif_name')
        category = parameters.get('category') or 'operation'
        if not whatif_name:
            return

        summary = self._read_entity_summary(whatif_name)
        if summary is None or 'name' not in summary.columns:
            return []
        names = summary['name'].dropna().tolist()
        paths = [
            self.locator.get_emissions_whatif_building_file(n, whatif_name)
            for n in names
        ]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            return []

        columns = get_columns_from_building_files(paths)
        if not columns:
            return []

        if category == 'operation':
            present = set()
            for col in columns:
                svc = _op_column_to_service(col)
                if svc:
                    present.add(svc)
            available = [s for s in _OPERATION_SERVICES if s in present]
        else:  # 'energy_carrier'
            from cea.technologies.energy_carriers import available_carriers
            try:
                known = available_carriers(self.locator)
            except Exception:
                known = set()
            present = set()
            for col in columns:
                car = _op_column_to_carrier(col)
                if car and car in known:
                    present.add(car)
            available = sorted(present)

        if not available:
            return []
        return {
            'choices': [{'value': x, 'label': x} for x in available],
            'default': available[0],
        }

    def _get_whatif_names(self) -> Optional[list]:
        """Return sorted list of what-if names that have operational emissions results."""
        names = get_whatif_names(self.locator)
        return [name for name in names if os.path.exists(self.locator.get_emissions_whatif_operational_file(name))]

    def _get_results_files(self, parameters) -> list:
        whatif_name = parameters.get('whatif_name')
        if not whatif_name:
            return []
        summary = self._read_entity_summary(whatif_name)
        if summary is None or 'name' not in summary.columns:
            return []
        files = []
        for name in summary['name'].dropna().tolist():
            p = self.locator.get_emissions_whatif_building_file(name, whatif_name)
            if os.path.exists(p):
                files.append(p)
        return files

    @classmethod
    def expected_parameters(cls):
        return {
            'whatif_name':
                ParameterDefinition(
                    "what-if-name",
                    "string",
                    description="Select a what-if scenario with operational emission results",
                    options_generator="_get_whatif_names",
                    selector="choice",
                ),
            'category':
                ParameterDefinition(
                    "category",
                    "string",
                    description="Aggregate by operation service or by energy carrier",
                    options_generator="_get_categories",
                    selector="choice",
                    depends_on=['whatif_name'],
                ),
            'data-column':
                ParameterDefinition(
                    "operation/carrier",
                    "string",
                    description="Service(s) or carrier(s) to visualise",
                    options_generator="_get_data_columns",
                    selector="choice",
                    depends_on=['whatif_name', 'category'],
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
                "Operational Emissions Hourly Files",
                file_locator="layer:_get_results_files",
                optional=True,
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Single (HexagonLayer) or stacked (ColumnLayer) output.

        Mirrors :class:`LifecycleEmissionsMapLayer.generate_data` but with
        a category-aware per-column mapping (``_op_column_to_service`` or
        ``_op_column_to_carrier``).
        """
        whatif_name = parameters.get('whatif_name')
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        raw_category = parameters.get('category') or 'operation'
        if raw_category not in _OPERATIONAL_CATEGORIES:
            raw_category = 'operation'

        if raw_category == 'operation':
            allowed = _OPERATION_SERVICES
            col_to_key = _op_column_to_service
            colour_map = _OPERATION_SERVICE_COLOURS
        else:
            # Carriers are the scenario's ``ENERGY_CARRIERS.csv`` codes;
            # user-added carriers appear here without code changes.
            from cea.technologies.energy_carriers import available_carriers
            try:
                allowed = sorted(available_carriers(self.locator))
            except Exception:
                allowed = []
            col_to_key = _op_column_to_carrier
            colour_map = _OPERATIONAL_CARRIER_COLOURS

        raw_selection = parameters['data-column']
        if isinstance(raw_selection, list):
            selected = [c for c in raw_selection if c in allowed]
        elif isinstance(raw_selection, str):
            selected = [raw_selection] if raw_selection in allowed else []
        else:
            selected = []
        selected = [c for c in allowed if c in selected]
        is_stacked = len(selected) > 1

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        def empty_output(fallback=None):
            fallback_label = f" - {fallback}" if fallback else ""
            colour_pair = colour_map.get(fallback, ('grey_lighter', 'black'))
            return {
                "data": [],
                "properties": {
                    "name": self.name,
                    "label": f"Operational Emissions{fallback_label} [kgCO\u2082e]",
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

        if not whatif_name or not selected:
            return empty_output(selected[0] if selected else None)

        summary = self._read_entity_summary(whatif_name)
        if (
            summary is None
            or 'name' not in summary.columns
            or not {'x_coord', 'y_coord'}.issubset(summary.columns)
        ):
            return empty_output(selected[0])

        try:
            zone_gdf = gpd.read_file(self.locator.get_zone_geometry())
            source_crs = zone_gdf.crs
        except Exception as exc:
            logger.debug(f"OperationalEmissions: could not read zone CRS: {exc}")
            source_crs = None
        if source_crs is None:
            return empty_output(selected[0])

        usable = summary.dropna(subset=['name', 'x_coord', 'y_coord'])
        if usable.empty:
            return empty_output(selected[0])

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

        def read_entity_values(entity_name):
            """Return {selection_key: period_sum} for the entity."""
            entity_file = self.locator.get_emissions_whatif_building_file(
                entity_name, whatif_name
            )
            if not os.path.exists(entity_file):
                return None
            try:
                header = pd.read_csv(entity_file, nrows=0).columns
            except Exception as exc:
                logger.debug(
                    f"OperationalEmissions: header read failed for {entity_name}: {exc}"
                )
                return None

            # Bucket columns by selected key up front.
            buckets = {key: [] for key in selected}
            for col in header:
                mapped = col_to_key(col)
                if mapped in buckets:
                    buckets[mapped].append(col)
            flat_cols = list(dict.fromkeys(c for cs in buckets.values() for c in cs))
            if not flat_cols:
                return {key: 0.0 for key in selected}
            try:
                df = pd.read_csv(entity_file, usecols=flat_cols)
            except Exception as exc:
                logger.debug(
                    f"OperationalEmissions: data read failed for {entity_name}: {exc}"
                )
                return None
            per_key = {}
            for key in selected:
                cols = buckets[key]
                if not cols:
                    per_key[key] = 0.0
                    continue
                series = df[cols].sum(axis=1).astype(float)
                if start < end:
                    per_key[key] = float(series.iloc[start:end + 1].sum())
                else:
                    per_key[key] = float(
                        series.iloc[start:].sum() + series.iloc[:end + 1].sum()
                    )
            return per_key

        entities = []
        for name, centroid in zip(entity_names, centroids):
            values = read_entity_values(name)
            if values is None:
                continue
            entities.append({
                "name": name,
                "position": [centroid.x, centroid.y],
                "values": values,
            })

        if not entities:
            return empty_output(selected[0])

        if not is_stacked:
            key = selected[0]
            colour_pair = colour_map.get(key, ('grey_lighter', 'black'))
            data_points = [
                {
                    "position": e["position"],
                    "value": e["values"][key],
                    "name": e["name"],
                    "category": key,
                }
                for e in entities
            ]
            period_values = [p["value"] for p in data_points]
            return {
                "data": data_points,
                "properties": {
                    "name": self.name,
                    "label": f"Operational Emissions - {key} [kgCO\u2082e]",
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

        # Stacked-multi
        categories_payload = []
        for key in selected:
            _, darker = colour_map.get(key, ('grey_lighter', 'black'))
            hex_colour = color_to_hex(darker)
            r = int(hex_colour[1:3], 16)
            g = int(hex_colour[3:5], 16)
            b = int(hex_colour[5:7], 16)
            categories_payload.append({
                "name": key,
                "colour": hex_colour,
                "rgb": [r, g, b],
            })

        stack_totals = [
            sum(max(e["values"].get(k, 0.0), 0.0) for k in selected)
            for e in entities
        ]

        return {
            "data": entities,
            "properties": {
                "name": self.name,
                "label": "Operational Emissions - stacked [kgCO\u2082e]",
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
                    "what-if-name",
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
        """Return what-if names with heat-rejection results, mtime-desc.

        Uses the shared ``get_whatif_names`` helper so the dropdown
        ordering and the auto-selected default match every other LCA
        layer — the just-run what-if surfaces at the top of the list
        immediately after the success notification's "View Results" click.
        """
        names = get_whatif_names(self.locator)
        names = [
            name for name in names
            if os.path.exists(self.locator.get_heat_rejection_whatif_buildings_file(name))
        ]
        return names or None

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
                    "what-if-name",
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
                    default=2,
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
