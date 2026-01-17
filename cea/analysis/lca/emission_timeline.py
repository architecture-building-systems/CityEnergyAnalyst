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
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup

__author__ = "Yiqiao Wang, Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Yiqiao Wang", "Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


if TYPE_CHECKING:
    from cea.demand.building_properties import BuildingProperties
    from cea.inputlocator import InputLocator


COMPONENT_TO_SRC_COMPONENT: dict[str, str] = {
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

# Backwards-compatible alias (internal name used throughout this module).
_MAPPING_DICT = COMPONENT_TO_SRC_COMPONENT


# Mirror the per-component naming used by the existing CEA emissions timelines.
# Kept as a separate constant so other modules can reuse the canonical order.
TIMELINE_COMPONENTS: tuple[str, ...] = tuple(_MAPPING_DICT.keys())


def get_component_quantities(
    building_properties: BuildingProperties, building_name: str
) -> dict[str, float]:
    """
    Return the area/quantity mapping used by emissions timelines.
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
    name = str(building_name)
    rc_model_props = building_properties.rc_model[name]
    envelope_props = building_properties.envelope[name]
    geometry_props = building_properties.geometry[name]

    surface_area: dict[str, float] = {}
    surface_area["Awall_ag"] = float(envelope_props["Awall_ag"])
    surface_area["Awall_bg"] = float(geometry_props["perimeter"]) * float(geometry_props["height_bg"])
    surface_area["Awall_part"] = float(rc_model_props["GFA_m2"]) * float(CONVERSION_AREA_TO_FLOOR_AREA_RATIO)
    surface_area["Awin_ag"] = float(envelope_props.get("Awin_ag", 0.0))

    surface_area["Aroof"] = float(envelope_props["Aroof"])
    surface_area["Aupperside"] = 0.0
    surface_area["Aunderside"] = float(envelope_props.get("Aunderside", 0.0))

    if float(geometry_props["floors_bg"]) == 0 and float(geometry_props.get("void_deck", 0)) > 0:
        area_base = 0.0
    else:
        area_base = float(rc_model_props["footprint"])

    surface_area["Abase"] = float(area_base)
    surface_area["Afloor"] = max(
        0.0,
        float(rc_model_props["GFA_m2"]) - float(surface_area["Aunderside"]) - float(surface_area["Abase"]),
    )
    surface_area["Atechnical_systems"] = float(rc_model_props["GFA_m2"])
    return surface_area


def normalise_years(year: int | list[int] | str | list[str]) -> list[str]:
    """Normalise year inputs to a list of timeline index labels (`Y_YYYY`).

    Accepted inputs:
    - `int` (e.g., 2020)
    - `list[int]`
    - `str` (already formatted label, e.g., `Y_2020`)
    - `list[str]`
    """
    if isinstance(year, int):
        return [f"Y_{int(year)}"]
    if isinstance(year, str):
        return [year]
    if isinstance(year, list):
        if len(year) == 0:
            return []
        if isinstance(year[0], int):
            return [f"Y_{int(y)}" for y in cast(list[int], year)]
        if isinstance(year[0], str):
            return list(cast(list[str], year))
    raise ValueError(f"Year must be int, str, list[int], or list[str]; got {type(year)}.")


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
    """
    The discount follows a linear interpolation from 1.0 at `ref_year` to `tar_fraction` at `tar_year`,
    and remains constant at `tar_fraction` thereafter.

    It identifies the years that needs to be discounted and generates a discount series, 
    then do elementwise multiplication with the base series to get the discounted series.

    For example:
        base: 
            ```
            Y_2020    100
            Y_2021    100
            Y_2022    100
            Y_2023    100
            Y_2024    100
            ```
        ref_year: 
            `2021`
        tar_year: 
            `2023`
        tar_fraction: 
            `0.5`
        calculated factor:
            ```
            Y_2020    1.0
            Y_2021    1.0
            Y_2022    0.75
            Y_2023    0.5
            Y_2024    0.5
            ```
        result:
            ```
            Y_2020    100.0
            Y_2021    100.0
            Y_2022     75.0
            Y_2023     50.0
            Y_2024     50.0
            ```

    Args:
        base (pd.Series): The base series to discount. Typically yearly operational emissions. 
            Indexed by years (e.g., `Y_2020`, `Y_2021`, ...).
        ref_year (int): The reference year where discounting starts.
        tar_year (int): The target year where the target fraction is reached.
        tar_fraction (float): The target fraction of the base value at the target year.
    Returns:
        pd.Series: The discounted series.
    """
    if tar_year <= ref_year:
        raise ValueError("Target year must be greater than reference year.")
    if tar_fraction < 0:
        raise ValueError("Target fraction must be non-negative.")

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


def apply_feedstock_policies_inplace(
    operational_multi_years: pd.DataFrame,
    *,
    feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
    available_feedstocks: list[str],
    demand_types: list[str],
) -> None:
    """
    Apply per-feedstock policies in-place (if any) to per-feedstock operational columns.
    Args:
        operational_multi_years (pd.DataFrame): The multi-year operational emissions DataFrame.
        feedstock_policies (Mapping[str, tuple[int, int, float]] | None):
            The feedstock policies to apply. Keys are feedstock names, values are tuples of
            (reference_year, target_year, target_fraction). Example:
                ```
                {
                "GRID":         (2020, 2030, 0.2),
                "NATURALGAS":   (2020, 2025, 0.5)
                }
                ```
            If the feedstock here is not available in the DataFrame columns, it is ignored.
        available_feedstocks (list[str]): The list of feedstocks present in the DataFrame.
        demand_types (list[str]): The list of demand types present in the DataFrame.
    """
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
        matching_fs = [
            fs for fs in available_feedstocks if str(fs).strip().upper() == fs_key_upper
        ]
        if not matching_fs:
            matching_fs = []
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

        # PV offset/export emissions are always tied to GRID electricity intensity.
        # if the feedstock being discounted is GRID, apply to PV columns too.
        # Columns look like: PV_{pv_code}_GRID_offset_kgCO2e or PV_{pv_code}_GRID_export_kgCO2e
        if fs_key_upper == "GRID":
            for col in operational_multi_years.columns:
                if (
                    isinstance(col, str)
                    and col.startswith("PV_")
                    and col.endswith("_kgCO2e")
                ):
                    operational_multi_years[col] = discount_over_year_indexed(
                        operational_multi_years[col],
                        ref_year=ref,
                        tar_year=tgt,
                        tar_fraction=frac,
                    )


class BaseYearlyEmissionTimeline:
    """Base class for *yearly* emissions timelines.

    Owns only:
    - the timeline DataFrame indexed by `Y_YYYY`
    - consistent logging semantics (add vs overwrite)
    - optional operational filling (including decarbonisation + PV offset)

    Subclasses provide domain-specific behaviour (lifetime scheduling, event/material deltas, etc.).
    """

    def __init__(
        self,
        *,
        name: str,
        locator: InputLocator,
        timeline: pd.DataFrame | None = None,
    ):
        self.name = str(name)
        self.locator = locator
        self.envelope_lookup: EnvelopeLookup = EnvelopeLookup.from_locator(self.locator)
        self.feedstock_db: Feedstocks = Feedstocks.from_locator(self.locator)
        self.timeline = timeline if isinstance(timeline, pd.DataFrame) else pd.DataFrame()

    def get_available_feedstocks(self) -> list[str]:
        return list(self.feedstock_db._library.keys()) + ["NONE"]

    @classmethod
    def empty_timeline_df(
        cls,
        *,
        start_year: int,
        end_year: int,
        columns: list[str],
        index_name: str = "period",
    ) -> pd.DataFrame:
        """Create an all-zero yearly timeline DataFrame indexed by `Y_YYYY` labels."""
        idx = [f"Y_{int(y)}" for y in range(int(start_year), int(end_year) + 1)]
        df = pd.DataFrame(index=idx)
        df.index.name = index_name
        for c in columns:
            df[c] = 0.0
        return df

    def log(
        self,
        *,
        emission: float,
        year: int | list[int] | str | list[str],
        col: str,
        additive: bool = True,
    ) -> None:
        years_list = normalise_years(year)
        if not years_list:
            return

        if additive:
            current = self.timeline.loc[years_list, col]
            self.timeline.loc[years_list, col] = current.astype(float).add(float(emission))
        else:
            self.timeline.loc[years_list, col] = float(emission)

    def add_phase_component(self, *, year: int, phase: str, component: str, value_kgco2e: float) -> None:
        self.log(
            emission=float(value_kgco2e),
            year=f"Y_{int(year)}",
            col=f"{phase}_{component}_kgCO2e",
            additive=True,
        )

    def fill_operational_emissions_for_building(
        self,
        *,
        locator: "InputLocator",
        building_name: str,
        feedstocks: list[str],
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
        apply_decarbonisation: bool = True,
        include_pv_offset: bool = True,
    ) -> None:
        # Keep operational fill logic close to call sites (avoid jumping through helpers).
        demand_types = list(_tech_name_mapping.keys())

        # Validate timeline index once (keeps later logic simpler).
        years_from_index(self.timeline.index)

        operational = OperationalHourlyTimeline.from_result(locator, building_name)
        operational_timeseries = operational.operational_emission_timeline.copy()
        if "date" in operational_timeseries.columns:
            operational_timeseries = operational_timeseries.drop(columns=["date"])

        yearly_sum = operational_timeseries.sum(axis=0)
        operational_multi_years = pd.DataFrame(
            np.tile(yearly_sum.to_numpy(dtype=float), (len(self.timeline.index), 1)),
            index=self.timeline.index,
            columns=yearly_sum.index,
        ) # each row is a year, each column is a demand+feedstock

        if apply_decarbonisation:
            apply_feedstock_policies_inplace(
                operational_multi_years,
                feedstock_policies=feedstock_policies,
                available_feedstocks=feedstocks,
                demand_types=demand_types,
            )

        # Aggregate per-feedstock columns back into per-demand totals.
        for d in demand_types:
            cols_d = [
                c
                for c in operational_multi_years.columns
                if isinstance(c, str) and c.startswith(f"{d}_") and c.endswith("_kgCO2e")
            ]
            out_col = f"operation_{d}_kgCO2e"
            values = operational_multi_years[cols_d].sum(axis=1).to_numpy(dtype=float) if cols_d else 0.0
            if out_col in self.timeline.columns:
                self.timeline.loc[:, out_col] = values
            else:
                self.timeline[out_col] = values

        if not include_pv_offset:
            return

        pv_cols = [
            c
            for c in operational_multi_years.columns
            if isinstance(c, str) and c.startswith("PV_") and c.endswith("_kgCO2e")
        ]
        for c in pv_cols:
            self.timeline[c] = operational_multi_years[c].to_numpy(dtype=float)


class BuildingYearlyEmissionTimeline(BaseYearlyEmissionTimeline):
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
        building_name: str,
        locator: InputLocator,
        end_year: int,
    ):
        """Initialize the BuildingEmissionTimeline object.

        :param building_properties: the BuildingProperties object containing the geometric,
            envelope and database data for all buildings in the district.
        :type building_properties: BuildingProperties
        :param building_name: the name of the building.
        :type building_name: str
        :param locator: the InputLocator object to locate input files.
        :type locator: InputLocator
        :param end_year: The last year that should exist in the building timeline.
        :type end_year: int
        """
        super().__init__(name=building_name, locator=locator)

        self._is_demolished = False
        self.geometry = building_properties.geometry[self.name]
        self.typology = building_properties.typology[self.name]
        self.envelope = building_properties.envelope[self.name]
        self.surface_area = get_component_quantities(building_properties, self.name)
        self.timeline = self.initialize_timeline(end_year)
        self._append_note(year=int(self.typology["year"]), message="Constructed")

    def _append_note(self, *, year: int, message: str) -> None:
        """Append a note message for a specific year to the `Note` column."""
        label = f"Y_{int(year)}"
        if "Note" not in self.timeline.columns:
            # Defensive: should always exist from initialize_timeline.
            self.timeline["Note"] = ""
        if label not in self.timeline.index:
            return
        current = str(self.timeline.at[label, "Note"] or "").strip()
        msg = str(message).strip()
        if not msg:
            return
        if not current:
            self.timeline.at[label, "Note"] = msg
        elif msg not in current:
            self.timeline.at[label, "Note"] = f"{current} | {msg}"

    def check_demolished(self):
        if self._is_demolished:
            raise RuntimeError(f"Building {self.name} has been logged as demolished before; no further emissions can be logged.")

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
        note_detail: str | None = None,
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
        self.log(
            emission=0.0,  # when building is first built, no demolition emission
            year=self.typology["year"],
            col=f"demolition_{key}_kgCO2e",
            additive=False,
        )

        # Notes: avoid listing details in the construction year (use the generic 'Constructed' message).
        start_year = int(self.typology["year"])
        max_year = max(years_from_index(self.timeline.index))
        if lifetime > 0 and max_year >= start_year + lifetime:
            renovation_years = list(range(start_year + int(lifetime), int(max_year) + 1, int(lifetime)))
            if renovation_years:
                detail = f" ({note_detail})" if note_detail else ""
                for y in renovation_years:
                    self._append_note(year=int(y), message=f"Service life reached: {key}{detail}")

    def fill_embodied_emissions(self) -> None:
        """
        Log the embodied emissions for the building components for
        the beginning construction year into the timeline,
        and whenever any component needs to be renovated.
        """
        self.check_demolished()
        
        for key, value in _MAPPING_DICT.items():
            area: float = self.surface_area[f"A{key}"]
            code_for_note: str | None = None

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
                code_for_note = str(self.envelope[type_str])
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
            self.log_emissions(area, production, biogenic, demolition, lifetime, key, note_detail=code_for_note)

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
            self.log_emissions(pv_area, embodied_intensity, 0.0, 0.0, lifetime, pv_type_str, note_detail=pv_code)

    def fill_operational_emissions(
        self,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None = None,
        *,
        apply_decarbonisation: bool = True,
        include_pv_offset: bool = True,
    ) -> None:
        """Fill operational emissions into the timeline, with optional per-feedstock discounting.

        Final logic:
        1) Sum the hourly operational emissions table to a yearly total (one row of per-feedstock columns).
        2) Duplicate the yearly totals down the whole emission timeline length.
        3) If `apply_decarbonisation` is enabled, apply per-feedstock policies as a year-indexed discount.
           (PV offset/export columns are discounted only when a GRID policy is present.)
        4) Aggregate per-feedstock columns back to per-demand yearly totals and write into the timeline.

        Column convention assumed: `{demand_type}_{feedstock}_kgCO2e` where demand_type is one of
        {Qhs_sys, Qww_sys, Qcs_sys, E_sys} and feedstock is in the feedstock database (plus 'NONE').
        """
        self.check_demolished()
        feedstocks = self.get_available_feedstocks()
        self.fill_operational_emissions_for_building(
            locator=self.locator,
            building_name=self.name,
            feedstocks=feedstocks,
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
        demolition_year_str = f"Y_{int(demolition_year)}"
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
            max_year = max(years_from_index(self.timeline.index))
            # if demolition_year > max_year, do nothing
            if demolition_year <= max_year:
                self.log(
                    emission=demolition * area,
                    year=demolition_year,
                    col=f"demolition_{key}_kgCO2e",
                )
            self._append_note(year=int(demolition_year), message="Demolished")
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

        cols = [
            f"{emission}_{component}_kgCO2e"
            for emission in self._EMISSION_TYPES
            for component in _MAPPING_DICT.keys()
        ]
        cols.extend(self._OPERATIONAL_COLS)

        timeline = self.empty_timeline_df(
            start_year=int(start_year),
            end_year=int(end_year),
            columns=cols,
            index_name="period",
        )
        timeline["name"] = self.name  # add building name column for easier identification
        timeline["Note"] = ""
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

        start_year = self.typology["year"]
        max_year = max(years_from_index(self.timeline.index))

        if max_year < start_year:
            return

        numeric_years = list(range(int(start_year), int(max_year) + 1, int(lifetime)))
        years = [f"Y_{int(year)}" for year in numeric_years]
        self.log(emission=emission, year=years, col=col)
