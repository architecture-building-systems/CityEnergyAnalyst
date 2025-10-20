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

if TYPE_CHECKING:
    from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
    from cea.demand.building_properties import BuildingProperties
    from cea.inputlocator import InputLocator


class BuildingEmissionTimeline:
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

    Finally, the yearly operational emission `operational` is also tracked
    in the timeline.
    """

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
    # Per-technology operational columns stored in the yearly timeline
    _OPERATIONAL_COLS = [f"operation_{demand_type}_kgCO2e" for demand_type in _tech_name_mapping.keys()]
    # Mapping from hourly demand aggregation names to timeline names
    _COLUMN_MAPPING = {f"{d}_kgCO2e": f"operation_{d}_kgCO2e" for d in _tech_name_mapping.keys()}
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
        self.timeline = self.initialize_timeline(end_year)

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
        
        for key, value in self._MAPPING_DICT.items():
            area: float = self.surface_area[f"A{key}"]

            if key == "technical_systems":
                lifetime = SERVICE_LIFE_OF_TECHNICAL_SYSTEMS
                ghg = EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS
                biogenic = 0.0
                demolition = 0.0  # dummy value, not implemented yet
            else:
                type_str = f"type_{value}"
                lifetime_any = self.envelope_lookup.get_item_value(
                    code=self.envelope[type_str], field="Service_Life"
                )
                ghg_any = self.envelope_lookup.get_item_value(
                    code=self.envelope[type_str], field="GHG_kgCO2m2"
                )
                biogenic_any = self.envelope_lookup.get_item_value(
                    code=self.envelope[type_str], field="GHG_biogenic_kgCO2m2"
                )
                if lifetime_any is None or ghg_any is None or biogenic_any is None:
                    raise ValueError(
                        f"Envelope database returned None for one of the required fields for item {self.envelope[type_str]}."
                    )
                lifetime = int(float(lifetime_any))
                ghg = float(ghg_any)
                biogenic = float(biogenic_any)
                demolition: float = 0.0  # dummy value, not implemented yet

            self.log_emissions(area, ghg, biogenic, demolition, lifetime, key)

    def fill_pv_embodied_emissions(self, pv_codes: list[str]) -> None:
        """Initialize the PV system in the building emission timeline.
        It reads the area of each PV type from the building properties, 
        and adds the corresponding columns to the timeline DataFrame.
        """
        self.check_demolished()
        pv_db = pd.read_csv(self.locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS"), index_col='code')
        for pv_code in pv_codes:
            if pv_code not in pv_db.index:
                raise ValueError(f"PV type {pv_code} not found in the PV database.")
            
            district_pv_area = pd.read_csv(self.locator.PV_total_buildings(pv_code), index_col='name') # indexed with building name
            pv_area = cast(float, district_pv_area.at[self.name, 'area_PV_m2'])
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
        discounted: pd.DataFrame,
        feedstock_policies: Mapping[str, tuple[int, int, float]],
        feedstocks: list[str],
        demand_types: list[str],
    ) -> None:
        """Apply per-feedstock policies in-place to discounted per-feedstock columns."""
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
            fs_key_upper = str(raw_key).strip().upper()
            matching_fs = [fs for fs in feedstocks if str(fs).strip().upper() == fs_key_upper]
            if not matching_fs:
                continue
            for fs in matching_fs:
                for d in demand_types:
                    col = f"{d}_{fs}_kgCO2e"
                    if col in discounted.columns:
                        discounted[col] = self.discount_over_year(discounted[col], ref, tgt, frac)

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
    ) -> None:
        """Fill operational emissions into the timeline, with optional per-feedstock discounting.

        Final logic:
        1) Sum the hourly operational dataframe to a yearly total (one row of per-feedstock columns).
        2) Duplicate the yearly totals down the whole emission timeline length.
        3) For each column, if its feedstock is in the policy, call discount_over_year on that Series.
        4) Aggregate per-feedstock columns back to per-technology yearly totals and write into self.timeline.

        Column convention assumed: `{demand_type}_{feedstock}_kgCO2e` where demand_type is one of
        {heating, hot_water, cooling, appliance} and feedstock is in the feedstock database (plus 'NONE').
        """
        self.check_demolished()
        # 1) Read hourly operational emissions and drop non-emission columns
        operational, operational_timeseries = self._read_operational_timeseries()

        # Fast path: no policies provided -> aggregate by demand type and assign
        if not feedstock_policies:
            # Use the helper from OperationalHourlyTimeline for robust demand aggregation
            op_by_demand = operational.emission_by_demand.copy().rename(columns=self._COLUMN_MAPPING)
            baseline_agg = op_by_demand.sum(axis=0)
            self.timeline.loc[:, self._OPERATIONAL_COLS] = baseline_agg.to_numpy(dtype=float)
            return

        feedstocks = list(self.feedstock_db._library.keys()) + ["NONE"]
        demand_types = list(_tech_name_mapping.keys())  # ['heating', 'hot_water', 'cooling', 'appliance']

        yearly_sum = operational_timeseries.sum(axis=0)
        operational_multiyrs = self._tile_yearly(yearly_sum)

        self._apply_feedstock_policies(operational_multiyrs, feedstock_policies, feedstocks, demand_types)
        out = self._aggregate_by_demand(operational_multiyrs, demand_types)

        self.timeline.loc[:, self._OPERATIONAL_COLS] = out[self._OPERATIONAL_COLS].to_numpy(dtype=float)

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
        for key, value in self._MAPPING_DICT.items():
            demolition: float = 0.0  # dummy value, not implemented yet
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
                    for component in list(self._MAPPING_DICT.keys())
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
        # Normalize to list[str] in Y_XXXX format for consistent indexing behavior
        if isinstance(year, int):
            years_list: list[str] = [f"Y_{year}"]
        elif isinstance(year, str):
            years_list = [year]
        elif isinstance(year, list) and len(year) > 0 and isinstance(year[0], int):
            years_list = [f"Y_{y}" for y in year]
        else:
            # If it's a list[str], keep; if empty or unknown, set empty list
            if isinstance(year, list) and (len(year) == 0 or isinstance(year[0], str)):
                years_list = list(year)  # type: ignore[arg-type]
            else:
                years_list = []

        if additive:
            # Add emission to all selected years (vectorized)
            current = self.timeline.loc[years_list, col]
            self.timeline.loc[years_list, col] = current.astype(float).add(float(emission))
        else:
            # Set emission for all selected years
            self.timeline.loc[years_list, col] = float(emission)

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
