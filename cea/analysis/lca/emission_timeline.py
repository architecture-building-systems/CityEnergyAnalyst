from __future__ import annotations

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from cea.analysis.lca.hourly_operational_emission import (
    OperationalHourlyTimeline,
    _tech_name_mapping,
)
from cea.constants import (
    CONVERSION_AREA_TO_FLOOR_AREA_RATIO,
    EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS,
    SERVICE_LIFE_OF_TECHNICAL_SYSTEMS,
)
from cea.datamanagement.database.components import Feedstocks

__author__ = "Yiqiao Wang, Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Yiqiao Wang", "Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


if TYPE_CHECKING:
    from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
    from cea.demand.building_properties import BuildingProperties
    from cea.inputlocator import InputLocator


_MAPPING_DICT = {
    "wall_ag": "wall",
    "wall_bg": "base",
    "wall_part": "part",
    "win_ag": "win",
    "roof": "roof",
    "upperside": "roof",
    "underside": "base",
    "floor": "floor",
    "base": "base",
    "technical_systems": "technical_systems", # not implemented in CEA, dummy value
}


# Mirror the per-component naming used by the existing CEA emissions timelines.
# Kept as a separate constant so other modules can reuse the canonical order.
TIMELINE_COMPONENTS: tuple[str, ...] = tuple(_MAPPING_DICT.keys())


def year_label(year: int) -> str:
    """Convert an integer year to the standard timeline index label `Y_YYYY`."""
    return f"Y_{int(year)}"


def normalise_years(year: int | list[int] | str | list[str]) -> list[str]:
    """Normalise year inputs to a list of timeline index labels (`Y_YYYY`).

    Accepted inputs:
    - `int` (e.g., 2020)
    - `list[int]`
    - `str` (already formatted label, e.g., `Y_2020`)
    - `list[str]`
    """
    if isinstance(year, int):
        return [year_label(year)]
    if isinstance(year, str):
        return [year]
    if isinstance(year, list):
        if len(year) == 0:
            return []
        if isinstance(year[0], int):
            return [year_label(y) for y in cast(list[int], year)]
        if isinstance(year[0], str):
            return list(cast(list[str], year))
    return []


def log_emission_in_timeline_df(
    df: pd.DataFrame,
    *,
    emission: float,
    year: int | list[int] | str | list[str],
    col: str,
    additive: bool = True,
) -> None:
    """Log emissions into an existing timeline DataFrame.

    This mirrors the behaviour of `BuildingEmissionTimeline._log_emission_in_timeline`,
    but is reusable by other timeline generators (e.g., district event timelines).
    """
    years_list = normalise_years(year)
    if not years_list:
        return

    if additive:
        current = df.loc[years_list, col]
        df.loc[years_list, col] = current.astype(float).add(float(emission))
    else:
        df.loc[years_list, col] = float(emission)


def phase_component_col(phase: str, component: str) -> str:
    """Return the standard emission column name `{phase}_{component}_kgCO2e`."""
    return f"{phase}_{component}_kgCO2e"


def years_from_index(index: pd.Index) -> list[int]:
    """Return integer years from an index.

    Accepted formats:
    - integer years (e.g., 2020)
    - strings like 'Y_2020'

    Raises:
        ValueError if any label cannot be parsed as a year.
    """
    years: list[int] = []
    for label in index:
        if isinstance(label, (int, np.integer)):
            years.append(int(label))
            continue
        s = str(label).strip()
        if s.startswith("Y_"):
            s = s[2:]
        if not s or not s.lstrip("-").isdigit():
            raise ValueError(
                "Index must contain years only (int years or 'Y_YYYY' labels). "
                f"Got invalid label: {label!r}"
            )
        years.append(int(s))
    return years


def discount_over_year_indexed(
    base: pd.Series,
    *,
    ref_year: int,
    tar_year: int,
    tar_fraction: float,
) -> pd.Series:
    """Apply the same discounting rule as `BuildingEmissionTimeline.discount_over_year`.

    This helper is intentionally index-driven, so other timeline generators can reuse the
    decarbonisation behaviour without subclassing `BuildingEmissionTimeline`.
    """
    if tar_year <= ref_year:
        raise ValueError("Target year must be greater than reference year.")
    if tar_fraction < 0:
        raise ValueError("Target fraction must be non-negative.")

    # idx = index if index is not None else base.index
    years = years_from_index(base.index)
    series = base.reindex(base.index).astype(float)

    years_arr = np.array(years, dtype=int)
    factors = np.ones(len(base.index), dtype=float)
    mask_linear = (years_arr >= int(ref_year)) & (years_arr <= int(tar_year))
    if mask_linear.any():
        n = int(mask_linear.sum())
        factors[mask_linear] = np.linspace(1.0, float(tar_fraction), n)
    factors[years_arr > int(tar_year)] = float(tar_fraction)

    return series * factors


def read_operational_timeseries(locator: "InputLocator", building_name: str) -> pd.DataFrame:
    """Load the hourly operational emissions table for a building, dropping non-emission columns."""
    operational = OperationalHourlyTimeline.from_result(locator, building_name)
    df = operational.operational_emission_timeline.copy()
    if "date" in df.columns:
        df = df.drop(columns=["date"])
    return df


def duplicate_yearly_to_index(yearly: pd.Series, *, index: pd.Index) -> pd.DataFrame:
    return pd.DataFrame(
        np.tile(yearly.to_numpy(dtype=float), (len(index), 1)), index=index, columns=yearly.index
    )


def apply_feedstock_policies_inplace(
    operational_multi_years: pd.DataFrame,
    *,
    feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
    feedstocks: list[str],
    demand_types: list[str],
) -> None:
    """Apply per-feedstock policies in-place (if any) to per-feedstock operational columns."""
    for raw_key, raw_policy in (feedstock_policies or {}).items():
        if not (isinstance(raw_policy, tuple) and len(raw_policy) == 3):
            raise ValueError(
                f"Policy for '{raw_key}' must be a tuple (reference_year, target_year, target_fraction)."
            )
        try:
            ref = int(raw_policy[0])
            tgt = int(raw_policy[1])
            frac = float(raw_policy[2])
        except (TypeError, ValueError):
            raise ValueError(
                f"Policy for '{raw_key}' must contain (int, int, float): got {raw_policy}."
            )
        if not tgt > ref:
            raise ValueError(
                f"Policy for '{raw_key}' target year must be greater than reference year."
            )
        if frac < 0:
            raise ValueError(
                f"Policy for '{raw_key}' target fraction must be non-negative."
            )
        fs_key_upper = str(raw_key).strip().upper()
        matching_fs = [fs for fs in feedstocks if str(fs).strip().upper() == fs_key_upper]
        if not matching_fs:
            continue
        for fs in matching_fs:
            for d in demand_types:
                col = f"{d}_{fs}_kgCO2e"
                if col in operational_multi_years.columns:
                    operational_multi_years[col] = discount_over_year_indexed(
                        operational_multi_years[col],
                        ref_year=ref,
                        tar_year=tgt,
                        tar_fraction=frac,
                    )


def apply_pv_offset_decarbonisation_inplace(
    operational_multi_years: pd.DataFrame,
    *,
    feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
) -> list[str]:
    """Apply GRID policy in-place (if any) to PV offset/export columns, and return those column names."""
    list_final_pv_cols: list[str] = []
    for col in operational_multi_years.columns:
        if col.startswith("PV_") and col.endswith("_kgCO2e"):
            if feedstock_policies and "GRID" in feedstock_policies:
                ref, tgt, frac = feedstock_policies["GRID"]
                operational_multi_years[col] = discount_over_year_indexed(
                    operational_multi_years[col],
                    ref_year=int(ref),
                    tar_year=int(tgt),
                    tar_fraction=float(frac),
                )
            list_final_pv_cols.append(col)
    return list_final_pv_cols


def aggregate_operational_by_demand(
    operational_multi_years: pd.DataFrame,
    *,
    demand_types: list[str],
) -> pd.DataFrame:
    out = pd.DataFrame(index=operational_multi_years.index)
    for d in demand_types:
        cols_d = [c for c in operational_multi_years.columns if c.startswith(f"{d}_") and c.endswith("_kgCO2e")]
        out[f"operation_{d}_kgCO2e"] = operational_multi_years[cols_d].sum(axis=1) if cols_d else 0.0
    return out


def fill_operational_emissions_inplace(
    df_timeline: pd.DataFrame,
    *,
    locator: "InputLocator",
    building_name: str,
    feedstock_db: Feedstocks,
    feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
    apply_decarbonisation: bool = True,
    include_pv_offset: bool = True,
) -> None:
    """Fill operational emissions into an existing timeline DataFrame.

    This is the reusable counterpart of `BuildingEmissionTimeline.fill_operational_emissions`.

    Options:
    - `apply_decarbonisation`: if False, ignores `feedstock_policies` (no discounting applied).
    - `include_pv_offset`: if False, PV offset/export columns are not written to the timeline.
    """
    demand_types = list(_tech_name_mapping.keys())
    feedstocks = list(feedstock_db._library.keys()) + ["NONE"]

    operational_timeseries = read_operational_timeseries(locator, building_name)
    yearly_sum = operational_timeseries.sum(axis=0)
    operational_multi_years = duplicate_yearly_to_index(yearly_sum, index=df_timeline.index)

    # Validate timeline index once (keeps later helpers simpler).
    years_from_index(df_timeline.index)

    if apply_decarbonisation:
        apply_feedstock_policies_inplace(
            operational_multi_years,
            feedstock_policies=feedstock_policies,
            feedstocks=feedstocks,
            demand_types=demand_types,
        )

    out = aggregate_operational_by_demand(
        operational_multi_years,
        demand_types=demand_types,
    )
    for col in [f"operation_{d}_kgCO2e" for d in demand_types]:
        if col in df_timeline.columns:
            df_timeline.loc[:, col] = out[col].to_numpy(dtype=float)
        else:
            df_timeline[col] = out[col].to_numpy(dtype=float)

    if not include_pv_offset:
        return

    if apply_decarbonisation:
        pv_cols = apply_pv_offset_decarbonisation_inplace(
            operational_multi_years,
            feedstock_policies=feedstock_policies,
        )
    else:
        pv_cols = [c for c in operational_multi_years.columns if c.startswith("PV_") and c.endswith("_kgCO2e")]
    for c in pv_cols:
        df_timeline[c] = operational_multi_years[c].to_numpy(dtype=float)


class EmissionTimelineFrame:
    """Small helper that owns *how* we write into timeline DataFrames.

    Design choice: composition over inheritance.

    - `BuildingEmissionTimeline` has domain-specific state (geometry, typology, envelope lookup,
      feedstocks, etc.). Subclassing it for every new timeline “flavour” (lifetime vs events)
      tends to couple constructors and makes future refactors harder.
    - A thin wrapper around `pd.DataFrame` lets multiple generators share the same logging
      semantics (index labels, column naming, additive vs overwrite) without sharing unrelated state.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    @classmethod
    def empty(
        cls,
        *,
        start_year: int,
        end_year: int,
        columns: list[str],
        index_name: str = "period",
    ) -> "EmissionTimelineFrame":
        idx = [year_label(y) for y in range(int(start_year), int(end_year) + 1)]
        df = pd.DataFrame(index=idx)
        df.index.name = index_name
        for c in columns:
            df[c] = 0.0
        return cls(df)

    def log(self, *, emission: float, year: int | list[int] | str | list[str], col: str, additive: bool = True) -> None:
        log_emission_in_timeline_df(self.df, emission=emission, year=year, col=col, additive=additive)

    def add_phase_component(self, *, year: int, phase: str, component: str, value_kgco2e: float) -> None:
        self.log(
            emission=float(value_kgco2e),
            year=year_label(year),
            col=phase_component_col(phase, component),
            additive=True,
        )

    def fill_operational_emissions(
        self,
        *,
        locator: "InputLocator",
        building_name: str,
        feedstock_db: Feedstocks,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
        apply_decarbonisation: bool = True,
        include_pv_offset: bool = True,
    ) -> None:
        fill_operational_emissions_inplace(
            self.df,
            locator=locator,
            building_name=building_name,
            feedstock_db=feedstock_db,
            feedstock_policies=feedstock_policies,
            apply_decarbonisation=apply_decarbonisation,
            include_pv_offset=include_pv_offset,
        )

    @staticmethod
    def add_phase_component_df(
        df: pd.DataFrame,
        *,
        year: int,
        phase: str,
        component: str,
        value_kgco2e: float,
    ) -> None:
        EmissionTimelineFrame(df).add_phase_component(
            year=year,
            phase=phase,
            component=component,
            value_kgco2e=value_kgco2e,
        )


class BaseEmissionTimeline:
    """Base class for *yearly* emissions timelines.

    Owns only:
    - the timeline DataFrame indexed by `Y_YYYY`
    - consistent logging semantics (add vs overwrite)
    - optional operational filling (including decarbonisation + PV offset)

    Subclasses provide domain-specific behaviour (lifetime scheduling, event/material deltas, etc.).
    """

    def __init__(self, timeline: pd.DataFrame):
        self.timeline = timeline
        self._frame = EmissionTimelineFrame(self.timeline)

    @classmethod
    def empty(
        cls,
        *,
        start_year: int,
        end_year: int,
        columns: list[str],
        index_name: str = "period",
    ) -> "BaseEmissionTimeline":
        frame = EmissionTimelineFrame.empty(
            start_year=start_year,
            end_year=end_year,
            columns=columns,
            index_name=index_name,
        )
        return cls(frame.df)

    def log(
        self,
        *,
        emission: float,
        year: int | list[int] | str | list[str],
        col: str,
        additive: bool = True,
    ) -> None:
        self._frame.log(emission=emission, year=year, col=col, additive=additive)

    def add_phase_component(self, *, year: int, phase: str, component: str, value_kgco2e: float) -> None:
        self._frame.add_phase_component(year=year, phase=phase, component=component, value_kgco2e=value_kgco2e)

    def fill_operational_emissions_for_building(
        self,
        *,
        locator: "InputLocator",
        building_name: str,
        feedstock_db: Feedstocks,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
        apply_decarbonisation: bool = True,
        include_pv_offset: bool = True,
    ) -> None:
        self._frame.fill_operational_emissions(
            locator=locator,
            building_name=building_name,
            feedstock_db=feedstock_db,
            feedstock_policies=feedstock_policies,
            apply_decarbonisation=apply_decarbonisation,
            include_pv_offset=include_pv_offset,
        )


class OperationalEmissionTimeline(BaseEmissionTimeline):
    """Operational-only yearly timeline that shares decarbonisation + PV-offset logic."""

    def __init__(
        self,
        *,
        locator: "InputLocator",
        building_name: str,
        feedstock_db: Feedstocks,
        start_year: int,
        end_year: int,
    ):
        self.locator = locator
        self.name = building_name
        self.feedstock_db = feedstock_db
        cols = [f"operation_{d}_kgCO2e" for d in _tech_name_mapping.keys()]
        super().__init__(EmissionTimelineFrame.empty(start_year=start_year, end_year=end_year, columns=cols).df)

    def fill(
        self,
        *,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
        apply_decarbonisation: bool = True,
        include_pv_offset: bool = True,
    ) -> None:
        self.fill_operational_emissions_for_building(
            locator=self.locator,
            building_name=self.name,
            feedstock_db=self.feedstock_db,
            feedstock_policies=feedstock_policies,
            apply_decarbonisation=apply_decarbonisation,
            include_pv_offset=include_pv_offset,
        )


class BuildingEmissionTimeline(BaseEmissionTimeline):
    """
    A class to manage the emission timeline for a building.
    The core attribute of this class is the timeline DataFrame indexed by year,
    which stores the emissions data over years.
    It logs emission for building components separately, so that the impact
    of each component can be tracked over time.

    Each building component has two main types of emissions associated with it:
    - `production`: the emissions associated with the materials and
    construction processes used to create the building component.
    - `biogenic`: the emissions that are stored within the material that
    would have otherwise been released during other processes or
    because of decay or wasting. In some results it's also called `uptake`.
    - `demolition`: the emissions associated with the deconstruction and
    disposal of building materials at the end of their service life.

    The components include:
    - vertical surfaces (excluding windows)
        - `wall_ag`: external wall that is above ground level and insulates
        the building from outside air.
        - `wall_bg`: external wall that is below ground level and typically
        insulates the building from ground temperature.
        - `wall_part`: partitional wall within the footprint of the building,
        typically not insulated.
    - windows on external vertical walls
        - `win_ag`: external window that is above ground level and typically
        has a lower U-value than the walls.
    - horizontal surfaces
        - `roof`: the top covering of the building, typically insulated.
        - `upperside`: the horizontal surface between interior space (below)
        and void deck (above), typically insulated, currently not implemented.
        - `underside`: the horizontal surface between the void deck (below)
        and the interior space (above), typically insulated.
        - `floor`: the interior horizontal surface of the building
        between two floors, typically uninsulated.
        - `base`: the part of the building that is in contact with the ground,
            typically insulated.
    - `technical_systems`: the technical systems of the building, including
        heating, cooling, ventilation, domestic hot water, electrical systems,

    Therefore, the column name is `{type}_{component}`, e.g., `production_wall_ag`,
        `biogenic_roof`.

        Notes on units / naming:
        - All *emission* columns in the timeline end with `_kgCO2e`.
            For example: `production_wall_ag_kgCO2e`, `biogenic_roof_kgCO2e`.
        - Non-emission metadata columns (e.g., `name`) do not follow this suffix.

    Finally, yearly operational emissions are also tracked in the timeline as
    `operation_{demand}_kgCO2e` (see `_COLUMN_MAPPING`).
    """

    _COLUMN_MAPPING = {f"{d}_kgCO2e": f"operation_{d}_kgCO2e" for d in _tech_name_mapping.keys()}
    _OPERATIONAL_COLS = list(_COLUMN_MAPPING.values())
    _EMISSION_TYPES = ["production", "biogenic", "demolition"]

    def __init__(
        self,
        building_properties: BuildingProperties,
        envelope_lookup: EnvelopeLookup,
        building_name: str,
        locator: InputLocator,
        end_year: int,
    ):
        """Initialize the BuildingEmissionTimeline object.

        :param building_properties: the BuildingProperties object containing the geometric,
            envelope and database data for all buildings in the district.
        :type building_properties: BuildingProperties
        :param envelope_lookup: the EnvelopeLookup object to access the envelope database.
        :type envelope_lookup: EnvelopeLookup
        :param building_name: the name of the building.
        :type building_name: str
        :param locator: the InputLocator object to locate input files.
        :type locator: InputLocator
        :param end_year: The last year that should exist in the building timeline.
        :type end_year: int
        """
        self.name = building_name
        self.locator = locator
        self._is_demolished = False
        self.envelope_lookup = envelope_lookup
        self.geometry = building_properties.geometry[self.name]
        self.typology = building_properties.typology[self.name]
        self.envelope = building_properties.envelope[self.name]
        self.feedstock_db = Feedstocks.from_locator(self.locator)
        self.surface_area = self.get_component_quantity(building_properties)
        timeline = self.initialize_timeline(end_year)
        super().__init__(timeline)

    def check_demolished(self):
        if self._is_demolished:
            raise RuntimeError("Building has been demolished; no further emissions can be logged.")

    def save_timeline(self):
        """Save the timeline DataFrame to a CSV file.
        If the folder does not exist, it will be created.
        """
        # first, check if timeline folder exist, if not create it
        if not os.path.exists(self.locator.get_lca_timeline_folder()):
            os.makedirs(self.locator.get_lca_timeline_folder())

        self.timeline.to_csv(self.locator.get_lca_timeline_building(self.name), float_format='%.2f')

    def log_emissions(
        self,
        area: float,
        production_per_area: float,
        biogenic_per_area: float,
        demolition_per_area: float,
        lifetime: int,
        key: str,
    ):
        self._log_emission_with_lifetime(
            emission=production_per_area * area, lifetime=lifetime, col=f"production_{key}_kgCO2e"
        )
        self._log_emission_with_lifetime(
            emission=-biogenic_per_area * area,
            lifetime=lifetime,
            col=f"biogenic_{key}_kgCO2e",
        )
        self._log_emission_with_lifetime(
            emission=demolition_per_area * area,
            lifetime=lifetime,
            col=f"demolition_{key}_kgCO2e",
        )
        self._log_emission_in_timeline(
            emission=0.0,  # when building is first built, no demolition emission
            year=self.typology["year"],
            col=f"demolition_{key}_kgCO2e",
            additive=False,
        )

    def fill_embodied_emissions(self) -> None:
        """
        Log the embodied emissions for the building components for
        the beginning construction year into the timeline,
        and whenever any component needs to be renovated.
        """
        self.check_demolished()
        
        for key, value in _MAPPING_DICT.items():
            area: float = self.surface_area[f"A{key}"]

            if key == "technical_systems":
                lifetime = SERVICE_LIFE_OF_TECHNICAL_SYSTEMS
                production = EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS
                biogenic = 0.0
                demolition = 0.0  # FIXME: assuming recycling of systems require generates emission, which is false
            else:
                type_str = f"type_{value}"
                lifetime_any = self.envelope_lookup.get_item_value(
                    code=self.envelope[type_str], field="Service_Life"
                )
                try: # if detailed LCA data (production + recycling) available, use it
                    ghg_production_any = self.envelope_lookup.get_item_value(
                        code=self.envelope[type_str], field="GHG_production_kgCO2m2"
                    )
                    ghg_recycling_any = self.envelope_lookup.get_item_value(
                        code=self.envelope[type_str], field="GHG_recycling_kgCO2m2"
                    )
                except KeyError: # else use simplified data (one value only)
                    ghg_production_any = self.envelope_lookup.get_item_value(
                        code=self.envelope[type_str], field="GHG_kgCO2m2"
                    )
                    ghg_recycling_any = 0.0

                biogenic_any = self.envelope_lookup.get_item_value(
                    code=self.envelope[type_str], field="GHG_biogenic_kgCO2m2"
                )
                if (
                    lifetime_any is None
                    or ghg_production_any is None
                    or ghg_recycling_any is None
                    or biogenic_any is None
                ):
                    raise ValueError(
                        f"Envelope database returned None for one of the required fields for item {self.envelope[type_str]}."
                    )
                lifetime = int(lifetime_any)
                production = float(ghg_production_any)
                biogenic = float(biogenic_any)
                demolition = float(ghg_recycling_any)
            self.log_emissions(area, production, biogenic, demolition, lifetime, key)

    def fill_pv_embodied_emissions(self, pv_codes: list[str]) -> None:
        """Initialize the PV system in the building emission timeline.
        It reads the area of each PV type from the building properties,
        and adds the corresponding columns to the timeline DataFrame.

        Note: PV file existence is already checked in total_yearly() before calling this method.
        """
        self.check_demolished()
        pv_db = pd.read_csv(self.locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS"), index_col='code')

        for pv_code in pv_codes:
            if pv_code not in pv_db.index:
                raise ValueError(f"PV type {pv_code} not found in the PV database.")

            district_pv_area = pd.read_csv(self.locator.PV_total_buildings(pv_code), index_col='name') # indexed with building name
            try:
                pv_area = cast(float, district_pv_area.at[self.name, 'area_PV_m2'])
            except KeyError:
                pv_area = 0.0
            lifetime = cast(int, pv_db.loc[pv_code, 'LT_yr'])
            pv_type_str = f"PV_{pv_code}"
            self.surface_area[f"APV_{pv_code}"] = pv_area
            for emission_type in self._EMISSION_TYPES:
                col_name = f"{emission_type}_{pv_type_str}_kgCO2e"
                if col_name not in self.timeline.columns:
                    self.timeline[col_name] = 0.0
                else:
                    raise ValueError(f"Column {col_name} already exists in the timeline, check for duplicate PV codes.")
            # Log embodied emissions for PV system
            embodied_intensity = cast(float, pv_db.loc[pv_code, 'module_embodied_kgco2m2'])
            self.log_emissions(pv_area, embodied_intensity, 0.0, 0.0, lifetime, pv_type_str)

    def discount_over_year(
        self,
        base: pd.Series,
        ref_year: int,
        tar_year: int,
        tar_fraction: float,
    ) -> pd.Series:
        """Apply a piecewise-linear discount to a yearly Series over this timeline's years.

        Rules:
        - Before ref_year: factor = 1.0
        - Between ref_year..tar_year (inclusive): linearly interpolate to tar_fraction
        - After tar_year: factor = tar_fraction (flat)

        Inputs/contract:
        - base: Series indexed by this timeline's index (e.g., 'Y_2020', ...). Values are yearly amounts.
        - ref_year < tar_year, tar_fraction >= 0

        Returns a Series aligned to the timeline index with the discount applied.
        """
        if tar_year <= ref_year:
            raise ValueError("Target year must be greater than reference year.")
        if tar_fraction < 0:
            raise ValueError("Target fraction must be non-negative.")

        # Ensure alignment to the timeline index
        idx = self.timeline.index
        series = base.reindex(idx).astype(float)

        # Convert 'Y_YYYY' index to integer years
        years: list[int] = []
        for label in idx:
            s = str(label)
            if s.startswith("Y_"):
                s = s[2:]
                years.append(int(s))

        years_arr = np.array(years, dtype=int)
        factors = np.ones(len(idx), dtype=float)
        # Linear segment (inclusive)
        mask_linear = (years_arr >= int(ref_year)) & (years_arr <= int(tar_year))
        if mask_linear.any():
            n = int(mask_linear.sum())
            factors[mask_linear] = np.linspace(1.0, float(tar_fraction), n)
        # After target
        factors[years_arr > int(tar_year)] = float(tar_fraction)

        return series * factors

    # ---- helpers for operational emissions -----------------------------------------

    def _read_operational_timeseries(self) -> tuple[OperationalHourlyTimeline, pd.DataFrame]:
        """Load the hourly operational timeline for this building and drop non-emission columns."""
        operational = OperationalHourlyTimeline.from_result(self.locator, self.name)
        df = operational.operational_emission_timeline.copy()
        if "date" in df.columns:
            df = df.drop(columns=["date"])  # keep only emission columns
        return operational, df

    @staticmethod
    def _build_expected_cols(df: pd.DataFrame, demand_types: list[str], feedstocks: list[str]) -> list[str]:
        cols: list[str] = []
        for d in demand_types:
            for fs in feedstocks:
                col = f"{d}_{fs}_kgCO2e"
                if col in df.columns:
                    cols.append(col)
        return cols

    def _tile_yearly(self, yearly: pd.Series) -> pd.DataFrame:
        idx = self.timeline.index
        return pd.DataFrame(
            np.tile(yearly.to_numpy(dtype=float), (len(idx), 1)), index=idx, columns=yearly.index
        )

    def _apply_feedstock_policies(
        self,
        operational_multi_years: pd.DataFrame,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
        feedstocks: list[str],
        demand_types: list[str],
    ) -> None:
        """Apply per-feedstock policies in-place (if any) to discounted per-feedstock columns."""
        for raw_key, raw_policy in (feedstock_policies or {}).items():
            if not (isinstance(raw_policy, tuple) and len(raw_policy) == 3):
                raise ValueError(
                    f"Policy for '{raw_key}' must be a tuple (reference_year, target_year, target_fraction)."
                )
            try:
                ref = int(raw_policy[0])
                tgt = int(raw_policy[1])
                frac = float(raw_policy[2])
            except (TypeError, ValueError):
                raise ValueError(
                    f"Policy for '{raw_key}' must contain (int, int, float): got {raw_policy}."
                )
            if not tgt > ref:
                raise ValueError(
                    f"Policy for '{raw_key}' target year must be greater than reference year."
                )
            if frac < 0:
                raise ValueError(
                    f"Policy for '{raw_key}' target fraction must be non-negative."
                )
            fs_key_upper = str(raw_key).strip().upper()
            matching_fs = [fs for fs in feedstocks if str(fs).strip().upper() == fs_key_upper]
            if not matching_fs:
                continue
            for fs in matching_fs:
                for d in demand_types:
                    col = f"{d}_{fs}_kgCO2e"
                    if col in operational_multi_years.columns:
                        operational_multi_years[col] = self.discount_over_year(operational_multi_years[col], ref, tgt, frac)

    def _apply_pv_offset_decarbonization(
        self,
        operational_multi_years: pd.DataFrame,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
    ) -> list[str]:
        """Apply GRID policy in-place (if any) to PV offset/export columns, and return the column names."""
        list_final_pv_cols: list[str] = []
        for col in operational_multi_years.columns:
            # Include PV offset and export columns
            if col.startswith("PV_") and col.endswith("_kgCO2e"):
                # Columns look like: PV_{pv_code}_GRID_offset_kgCO2e or PV_{pv_code}_GRID_export_kgCO2e
                if feedstock_policies and "GRID" in feedstock_policies:
                    ref, tgt, frac = feedstock_policies["GRID"]
                    operational_multi_years[col] = self.discount_over_year(
                        operational_multi_years[col], ref, tgt, frac
                    )
                list_final_pv_cols.append(col)
        return list_final_pv_cols

    @staticmethod
    def _aggregate_by_demand(
        timeline: pd.DataFrame, demand_types: list[str]
    ) -> pd.DataFrame:
        idx = timeline.index
        out = pd.DataFrame(index=idx)
        for d in demand_types:
            cols_d = [c for c in timeline.columns if c.startswith(f"{d}_") and c.endswith("_kgCO2e")]
            out[f"operation_{d}_kgCO2e"] = timeline[cols_d].sum(axis=1) if cols_d else 0.0
        return out

    def fill_operational_emissions(
        self,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
        *,
        apply_decarbonisation: bool = True,
        include_pv_offset: bool = True,
    ) -> None:
        """Fill operational emissions into the timeline, with optional per-feedstock discounting.

        Final logic:
        1) Sum the hourly operational dataframe to a yearly total (one row of per-feedstock columns).
        2) Duplicate the yearly totals down the whole emission timeline length.
        3) For each column, if its feedstock is in the policy, call discount_over_year on that Series.
        4) Aggregate per-feedstock columns back to per-technology yearly totals and write into self.timeline.

        Column convention assumed: `{demand_type}_{feedstock}_kgCO2e` where demand_type is one of
        {Qhs_sys, Qww_sys, Qcs_sys, E_sys} and feedstock is in the feedstock database (plus 'NONE').
        """
        self.check_demolished()
        self.fill_operational_emissions_for_building(
            locator=self.locator,
            building_name=self.name,
            feedstock_db=self.feedstock_db,
            feedstock_policies=feedstock_policies,
            apply_decarbonisation=apply_decarbonisation,
            include_pv_offset=include_pv_offset,
        )

    def demolish(self, demolition_year: int) -> None:
        """
        1. Erase all future emissions after demolition year, including operational emissions.
        2. Log demolition emissions in the demolition year.

        :param demolition_year: the year, after end of which the building does not exist anymore.
        :type demolition_year: int
        """
        self.check_demolished()
        # if demolition_year < self.geometry["year"], raise error
        if demolition_year < self.typology["year"]:
            raise ValueError(
                "Demolition year must be greater than or equal to the construction year."
            )

        # Convert demolition_year to string format for comparison with timeline index
        demolition_year_str = f"Y_{demolition_year}"
        self.timeline.loc[self.timeline.index >= demolition_year_str, :] = 0.0
        for key, value in _MAPPING_DICT.items():
            type_str = f"type_{value}"
            try:
                demolition_any = self.envelope_lookup.get_item_value(
                    code=self.envelope[type_str], field="GHG_recycling_kgCO2m2"
                )
            except KeyError:  # if detailed LCA data not available, use simplified
                demolition_any = 0.0

            if demolition_any is not None:
                demolition = float(demolition_any)
            else:
                raise ValueError(
                    f"Recycling column exists but without meaningful data for item {self.envelope[type_str]}."
                )
            
            area: float = self.surface_area[f"A{key}"]
            # Convert max year to int for comparison
            max_year_str = self.timeline.index.max()
            max_year = int(str(max_year_str).replace("Y_", ""))
            # if demolition_year > max_year, do nothing
            if demolition_year <= max_year:
                self._log_emission_in_timeline(
                    emission=demolition * area,
                    year=demolition_year,
                    col=f"demolition_{key}_kgCO2e",
                )
        self._is_demolished = True

    def initialize_timeline(self, end_year: int) -> pd.DataFrame:
        """Initialize the timeline as a dataframe of `0.0`s,
        indexed by year, for the building emissions.

        :param end_year: The year to end the timeline.
        :type end_year: int
        :raises ValueError: If the start year is not less than the end year.
        :return: The initialized timeline DataFrame.
        :rtype: pd.DataFrame
        """
        start_year = self.typology["year"]
        if start_year >= end_year:
            raise ValueError("The starting year must be less than the ending year.")

        timeline = pd.DataFrame(
            {
                "period": [f"Y_{year}" for year in range(start_year, end_year + 1)],
                **{
                    f"{emission}_{component}_kgCO2e": 0.0
                    for emission in self._EMISSION_TYPES
                    for component in list(_MAPPING_DICT.keys())
                    + ["technical_systems"]
                },
                **{col: 0.0 for col in self._OPERATIONAL_COLS},
            }
        )
        timeline['name'] = self.name  # add building name column for easier identification
        timeline.set_index("period", inplace=True)
        self._is_demolished = False
        return timeline

    def _log_emission_with_lifetime(
        self, emission: float, lifetime: int, col: str
    ) -> None:
        """The function logs emission once every "lifetime" years in the desired column.

        :param emission: The amount of emission to log.
        :type emission: float
        :param lifetime: The lifetime of the component in years. Minimum 1.
        :type lifetime: int
        :param col: The column to log the emission in.
        :type col: str
        """
        if lifetime < 1:
            raise ValueError("Lifetime must be at least 1 year.")

        # Extract numeric year from string format Y_XXXX
        start_year = self.typology["year"]
        max_year_str = self.timeline.index.max()
        max_year = int(str(max_year_str).replace("Y_", ""))

        numeric_years = list(range(start_year, max_year + 1, lifetime))
        # Convert back to string format
        years = [f"Y_{year}" for year in numeric_years]
        self._log_emission_in_timeline(emission, years, col)

    def _log_emission_in_timeline(
        self, emission: float, year: int | list[int] | str | list[str], col: str, additive: bool = True
    ) -> None:
        self.log(emission=emission, year=year, col=col, additive=additive)

    def get_component_quantity(self, building_properties: BuildingProperties) -> dict[str, float]:
        """
        Get the area for each building component.
        During Daysim simulation, the types of surfaces are categorized in detail,
        so we need the radiation results
        to extract surface area information, as done in demand calculation as well.
        The radiation results are stored in `building_properties.rc_model._rc_model_props`.
        A lot of fields exist, but the useful ones are:
        - `GFA_m2`: total floor area of building
        - `Awall_ag`: total area of external walls above ground
        - `Awin_ag`: total area of windows
        - `Aroof`: total area of roof
        - `Aunderside`: total area of bottom surface, if the bottom surface is above ground level.
            In case where building touches the ground, this value is zero.
        - `footprint`: the area of the building footprint, equivalent to `Abase`.

        Calculated area:
        - `Awall_bg`: total area of below-ground walls
        - `Awall_part`: total area of partition walls. Currently dummy value 0.0
        - `Aupperside`: total area of upper side. Currently not available in Daysim
            radiation results, so this value is set to `0.0`.
        - `Afloor`: total area of internal floors.
            If the floor area is neither touching the ground nor the outside air,
            it should be internal. Therefore, the calculation formula thus is:
            `Afloor = GFA_m2 - Aunderside - footprint`
        - `Atechnical_systems`: total area of technical systems. Same as GFA.

        :param building_properties: The building properties object containing results
            for all buildings in the district. Two attributes are relevant
            for the surface area calculation: the `rc_model` and `geometry` attributes.

            The `geometry` attribute simply returns what's inside the `zone.shp` file,
            along with the footprint and perimeter;
            The `rc_model` attribute contains the areas along with other parameters.
            Whole list of parameters (details see `BuildingRCModel.calc_prop_rc_model`)
        :type building_properties: BuildingProperties

        :return: A dictionary with the area of each building component.
        :rtype: dict[str, float]
        """
        rc_model_props = building_properties.rc_model[self.name]
        envelope_props = building_properties.envelope[self.name]

        surface_area = {}
        surface_area["Awall_ag"] = envelope_props["Awall_ag"]
        surface_area["Awall_bg"] = (
            self.geometry["perimeter"] * self.geometry["height_bg"]
        )
        surface_area["Awall_part"] = rc_model_props["GFA_m2"] * CONVERSION_AREA_TO_FLOOR_AREA_RATIO
        surface_area["Awin_ag"] = envelope_props["Awin_ag"]

        # calculate the area of each component
        # horizontal: roof, floor, underside, upperside (not implemented), base
        # vertical: wall_ag, wall_bg, wall_part (not implemented), win_ag
        surface_area["Aroof"] = envelope_props["Aroof"]
        surface_area["Aupperside"] = 0.0  # not implemented
        surface_area["Aunderside"] = envelope_props["Aunderside"]
        # internal floors that are not base, not upperside and not underside

        # check if building ever have base
        if self.geometry["floors_bg"] == 0 and self.geometry["void_deck"] > 0:
            # building is completely floating and does not have a base
            area_base = 0.0
        else:
            area_base = float(rc_model_props["footprint"])
        surface_area["Afloor"] = max(
            0.0,
            rc_model_props[
                "GFA_m2"
            ]  # GFA = footprint * (floor_ag + floor_bg - void_deck)
            - surface_area["Aunderside"]
            - area_base,
        )
        surface_area["Abase"] = area_base
        surface_area["Atechnical_systems"] = rc_model_props["GFA_m2"]
        return surface_area


def get_building_names_from_zone(locator):
    """
    Get building names from zone geometry.

    Parameters
    ----------
    locator : InputLocator
        File path resolver

    Returns
    -------
    pd.DataFrame
        Zone geometry with 'Name' or 'name' column (caller should check both)
    """
    import geopandas as gpd

    from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

    zone_path = locator.get_zone_geometry()
    crs = get_geographic_coordinate_system()
    zone_df = gpd.read_file(zone_path).to_crs(crs)

    return zone_df