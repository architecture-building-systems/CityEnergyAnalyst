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
_ENERGY_CARRIERS = ['NATURALGAS', 'GRID', 'SOLAR', 'PV']


def _column_to_carrier(column: str) -> Optional[str]:
    """Map a raw ``*_kWh`` column name to a high-level carrier, or None.

    Mirrors the aggregation rules used by
    ``cea.analysis.final_energy.calculation._aggregate_hourly_data``.
    """
    if not column.endswith('_kWh') or column in _ENERGY_DEMAND_ROLLUP_COLUMNS:
        return None

    # Solar / PV generation columns.
    if column.startswith('PV_'):
        return 'PV'
    if column.startswith('PVT_'):
        if column.endswith('_E_kWh'):
            return 'PV'
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

    def _get_data_columns(self, parameters) -> Optional[list]:
        """Return the list of high-level carriers available in this what-if.

        Scans the union of columns across every entity's hourly file and maps
        each column to a carrier via :func:`_column_to_carrier`. Only carriers
        actually present in the data are returned, preserving the canonical
        order defined by ``_ENERGY_CARRIERS``.
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

        return [c for c in _ENERGY_CARRIERS if c in present]

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
                    "What-if scenario",
                    "string",
                    description="Select a what-if scenario with final-energy results",
                    options_generator="_get_whatif_names",
                    selector="choice",
                ),
            'data-column':
                ParameterDefinition(
                    "Energy Carrier",
                    "string",
                    description="Final energy carrier / column to visualize",
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
                "Final Energy Hourly Files",
                file_locator="layer:_get_results_files",
                optional=True,
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        whatif_name = parameters.get('whatif_name')
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        carrier = parameters['data-column']

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": f"Energy by Carrier — {carrier}" if carrier else "Energy by Carrier",
                "description": self.description,
                "colours": {
                    "colour_array": [color_to_hex("brown_lighter"), color_to_hex("brown")],
                    "points": 12
                }
            }
        }

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        if not whatif_name:
            output['properties']['range'] = empty_range
            return output

        summary = self._read_entity_summary(whatif_name)
        if summary is None or 'name' not in summary.columns:
            output['properties']['range'] = empty_range
            return output

        available_carriers = self._get_data_columns(parameters) or []
        if carrier is None or carrier not in available_carriers:
            raise ValueError(f"Invalid carrier: {carrier}")

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

        def get_data(entity_name, centroid):
            entity_file = self.locator.get_final_energy_building_file(entity_name, whatif_name)
            if not os.path.exists(entity_file):
                logger.debug(f"EnergyByCarrier: missing file for {entity_name}")
                return None

            try:
                header = pd.read_csv(entity_file, nrows=0).columns
            except Exception as exc:
                logger.debug(f"EnergyByCarrier: header read failed for {entity_name}: {exc}")
                return None

            matching_cols = [c for c in header if _column_to_carrier(c) == carrier]

            if not matching_cols:
                period_value = 0.0
                total_value = 0.0
            else:
                try:
                    data = pd.read_csv(entity_file, usecols=matching_cols).sum(axis=1)
                except Exception as exc:
                    logger.debug(f"EnergyByCarrier: data read failed for {entity_name}: {exc}")
                    return None
                total_value = float(data.sum())
                if start < end:
                    period_value = float(data.iloc[start:end + 1].sum())
                else:
                    period_value = float(
                        data.iloc[start:].sum() + data.iloc[:end + 1].sum()
                    )

            return {
                'name': entity_name,
                'total': total_value,
                'period': period_value,
                'point': {"position": [centroid.x, centroid.y], "value": period_value},
            }

        values = [get_data(name, c) for name, c in zip(entity_names, centroids)]
        values = [v for v in values if v is not None]

        if not values:
            output['properties']['range'] = empty_range
            return output

        totals = [v['total'] for v in values]
        periods = [v['period'] for v in values]
        data_points = [v['point'] for v in values]

        nonzero_totals = sum(1 for t in totals if t > 0)
        logger.debug(
            f"EnergyByCarrier[{carrier}]: {len(values)} entities, "
            f"{nonzero_totals} with non-zero totals; "
            f"total_max={max(totals) if totals else 0:.2f}"
        )

        output['data'] = data_points
        output['properties']['range'] = {
            'total': {
                'label': 'Total Range',
                'min': 0.0,
                'max': float(max(totals)) if totals else 0.0,
            },
            'period': {
                'label': 'Period Range',
                'min': float(min(periods)) if periods else 0.0,
                'max': float(max(periods)) if periods else 0.0,
            },
        }
        return output


class LifecycleEmissionsMapLayer(WhatifDeletableMixin, MapLayer):
    category = LifeCycleAnalysisCategory
    name = "lifecycle-emissions"
    label = "Lifecycle Emissions (Annual)"
    description = ""

    def _get_data_columns(self, parameters) -> Optional[list]:
        buildings = self.locator.get_zone_building_names()
        whatif_name = parameters.get('whatif_name')

        if not buildings or not whatif_name:
            return

        paths = [self.locator.get_emissions_whatif_building_timeline_file(b, whatif_name) for b in buildings]
        return get_columns_from_building_files(paths)

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
                    "What-if scenario",
                    "string",
                    description="Select a what-if scenario with emission results",
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

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""

        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()
        whatif_name = parameters.get('whatif_name')

        data_column = parameters['data-column']
        period = parameters['timeline']
        start, end = period

        output = {
            "data": [],
            "properties": {
                "name": self.name,
                "label": "Embodied Emissions",
                "description": self.description,
                "colours": {
                    "colour_array": [color_to_hex("grey_lighter"), color_to_hex("black")],
                    "points": 12
                }
            }
        }

        # Filter buildings that exist in geometry
        buildings, _, building_centroids = safe_filter_buildings_with_geometry(self.locator, buildings)

        # If no buildings or what-if scenario is selected, return empty data with range of 0 to avoid errors in frontend
        if not buildings or not whatif_name:
            output['properties']['range'] = {
                'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
                'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0}
            }
            return output

        def get_data(building, centroid):
            try:
                building_file = self.locator.get_emissions_whatif_building_timeline_file(building, whatif_name)
                if not os.path.exists(building_file):
                    return None

                df = pd.read_csv(building_file, usecols=["period", data_column])

                data = df[data_column]
                data.index = period_to_year(df['period'])

                total_min = 0
                total_max = data.sum()

                period_value = data.loc[start:end].sum()
                period_min = period_value
                period_max = period_value

                data_point = {"position": [centroid.x, centroid.y], "value": period_value}

                return total_min, total_max, period_min, period_max, data_point
            except Exception as e:
                print(f"Warning: Error reading lifecycle emissions for {building}: {e}")
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
