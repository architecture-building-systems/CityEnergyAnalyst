from __future__ import annotations
import os
import numpy as np
import pandas as pd
from cea.constants import (
    SERVICE_LIFE_OF_TECHNICAL_SYSTEMS,
    CONVERSION_AREA_TO_FLOOR_AREA_RATIO,
    EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator
    from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
    from cea.demand.building_properties import BuildingProperties


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
    COLUMN_MAPPING = {
        "heating_kgCO2e": "operation_heating_kgCO2e",
        "cooling_kgCO2e": "operation_cooling_kgCO2e",
        "hot_water_kgCO2e": "operation_hot_water_kgCO2e",
        "electricity_kgCO2e": "operation_electricity_kgCO2e"
    }
    _OPERATIONAL_COLS = list(COLUMN_MAPPING.values())
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
        # self.building_properties = building_properties
        self.envelope_lookup = envelope_lookup
        self.geometry = building_properties.geometry[self.name]
        self.typology = building_properties.typology[self.name]
        self.envelope = building_properties.envelope[self.name]
        self.surface_area = self.get_component_quantity(building_properties)
        self.timeline = self.initialize_timeline(end_year)

    def fill_timeline(self) -> None:
        """Fills up the timeline with emissions data, both embodied and operational.
        """
        self.fill_embodied_emissions()
        self.fill_operational_emissions()

    def save_timeline(self):
        """Save the timeline DataFrame to a CSV file.
        If the folder does not exist, it will be created.
        """
        # first, check if timeline folder exist, if not create it
        if not os.path.exists(self.locator.get_lca_timeline_folder()):
            os.makedirs(self.locator.get_lca_timeline_folder())

        self.timeline.to_csv(self.locator.get_lca_timeline_building(self.name), float_format='%.2f')

    def fill_embodied_emissions(self) -> None:
        """
        Log the embodied emissions for the building components for
        the beginning construction year into the timeline,
        and whenever any component needs to be renovated.
        """

        def log_emissions(area, ghg, biogenic, demolition, lifetime, key):
            self.log_emission_with_lifetime(
                emission=ghg * area, lifetime=lifetime, col=f"production_{key}_kgCO2e"
            )
            self.log_emission_with_lifetime(
                emission=-biogenic * area,
                lifetime=lifetime,
                col=f"biogenic_{key}_kgCO2e",
            )
            self.log_emission_with_lifetime(
                emission=demolition * area,
                lifetime=lifetime,
                col=f"demolition_{key}_kgCO2e",
            )
            self.log_emission_in_timeline(
                emission=0.0,  # when building is first built, no demolition emission
                year=self.typology["year"],
                col=f"demolition_{key}_kgCO2e",
                additive=False,
            )

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

            log_emissions(area, ghg, biogenic, demolition, lifetime, key)

    def fill_operational_emissions(
        self,
        reference_year: int | None = None,
        target_year: int | None = None,
        discount_rate: float | None = None,
    ) -> None:
        """Fill operational emissions into the timeline, optionally applying a discount to grid-related emissions.

        If reference_year, target_year, and discount_rate are all provided, grid-related emissions are linearly
        discounted from 1.0 (at reference_year) to discount_rate (at target_year) and held at discount_rate thereafter.
        Non-grid emissions are not discounted.

        :param reference_year: start of discounting period, if None, no discounting applied
        :type reference_year: int | None
        :param target_year: end of discounting period, if None, no discounting applied
        :type target_year: int | None
        :param discount_rate: discount rate to apply at target_year, if None, no discounting applied
        :type discount_rate: float | None
        :raises ValueError: if operational emission file does not have 8760 rows
        :raises ValueError: if target_year < reference_year
        :raises ValueError: if discount_rate < 0
        :raises ValueError: if reference_year, target_year, discount_rate are not all provided or all None
        :return: None
        """

        def _validate_discount_inputs(
            reference_year: int, target_year: int, discount_rate: float
        ) -> None:
            if target_year < reference_year:
                raise ValueError(
                    "Target year must be greater than or equal to reference year."
                )
            if discount_rate < 0:
                raise ValueError("Discount rate must be non-negative.")

        def _build_discount_factors(
            reference_year: int, target_year: int, discount_rate: float, interp: str="linear"
        ) -> pd.Series:
            """Linear factors from 1.0@reference_year to discount_rate@target_year inclusive."""
            years = [f"Y_{y}" for y in range(reference_year, target_year + 1)]
            if interp == "linear":
                return pd.Series(
                    np.linspace(1.0, float(discount_rate), len(years)), index=years
                )
            else:
                raise ValueError(f"Unknown interpolation method: {interp}")

        def _discount_grid_only(
            yearly_split: pd.Series, factors: pd.Series
        ) -> pd.DataFrame:
            """Tile yearly split across years and multiply GRID columns by discount factors."""
            # Create a constant-by-row DataFrame from the yearly split
            df = pd.DataFrame(
                np.tile(yearly_split.to_numpy(dtype=float), (len(factors), 1)),
                index=factors.index,
                columns=yearly_split.index,
            )
            grid_cols = [c for c in df.columns if c.endswith("_from_GRID_kgCO2e")]
            if grid_cols:
                df[grid_cols] = df[grid_cols].mul(factors, axis=0)
            return df

        operational = pd.read_csv(
            self.locator.get_lca_operational_hourly_building(self.name),
            index_col="hour",
        ).rename(columns=self.COLUMN_MAPPING)
        if len(operational) != 8760:
            raise ValueError(
                f"Operational emission timeline expected 8760 rows, got {len(operational)} rows. Please check file integrity!"
            )

        # 2) First, log the baseline (non-discounted) yearly totals to all years
        baseline_yearly = operational[self._OPERATIONAL_COLS].sum(axis=0)
        # avoid inplace "+=" for better typing compatibility
        self.timeline.loc[:, self._OPERATIONAL_COLS] = self.timeline.loc[
            :, self._OPERATIONAL_COLS
        ].add(baseline_yearly, axis=1)

        # 3) Decide whether to apply discounting
        all_none = (
            reference_year is None and target_year is None and discount_rate is None
        )
        all_provided = (
            reference_year is not None
            and target_year is not None
            and discount_rate is not None
        )

        if all_none:
            return  # nothing else to do
        if not all_provided:
            raise ValueError(
                "Either provide all of reference_year, target_year, discount_rate or none of them."
            )

        # 4) Validate inputs and prepare discount factors
        # Narrow types after validation
        assert (
            reference_year is not None
            and target_year is not None
            and discount_rate is not None
        )
        _validate_discount_inputs(reference_year, target_year, discount_rate)
        r_year, t_year, d_rate = (
            int(reference_year),
            int(target_year),
            float(discount_rate),
        )

        yearly_split, tech_names = self._yearly_operational_split_grid_non_grid(
            operational
        )
        discount_factors = _build_discount_factors(r_year, t_year, d_rate)

        # 5) Apply discount to grid-only columns and collapse back to per-tech totals
        discounted = _discount_grid_only(yearly_split, discount_factors)
        for tech_name in tech_names:
            discounted[f"operation_{tech_name}_kgCO2e"] = (
                discounted[f"operation_{tech_name}_from_others_kgCO2e"]
                + discounted[f"operation_{tech_name}_from_GRID_kgCO2e"]
            )

        # 6) Write discounted values back to the timeline (only for applicable years)
        self._write_discounted_operational_to_timeline(discounted, (r_year, t_year))

    # -------------------------
    # Helper methods (readability)
    # -------------------------

    def _yearly_operational_split_grid_non_grid(
        self, operational: pd.DataFrame
    ) -> tuple[pd.Series, list[str]]:
        """Return yearly sums split into GRID vs non-GRID per tech (heating/cooling/hot_water, etc.)."""
        from cea.datamanagement.database.components import Feedstocks
        from cea.analysis.lca.hourly_operational_emission import _tech_name_mapping

        feedstock_db = Feedstocks.from_locator(self.locator)
        feedstock_names = list(feedstock_db._library.keys())
        feedstocks_wo_grid = [name for name in feedstock_names if name != "GRID"]

        # Build per-tech split columns on-the-fly
        for tech_name, (demand_col, _supply_type) in _tech_name_mapping.items():
            other_col = f"operation_{tech_name}_from_others_kgCO2e"
            grid_col = f"operation_{tech_name}_from_GRID_kgCO2e"
            operational[other_col] = 0.0
            operational[grid_col] = 0.0

            # Sum all non-grid feedstocks into _from_others_
            for fs in feedstocks_wo_grid:
                col_name = f"{demand_col}_{fs}_kgCO2e"
                if col_name in operational.columns:
                    operational[other_col] += operational[col_name]

            # Put grid feedstock into _from_GRID_
            grid_src = f"{demand_col}_GRID_kgCO2e"
            if grid_src in operational.columns:
                operational[grid_col] = operational[grid_src]

        # Final list of split columns to sum per year
        cols_split = [
            f"operation_{tech}_from_others_kgCO2e" for tech in _tech_name_mapping.keys()
        ] + [f"operation_{tech}_from_GRID_kgCO2e" for tech in _tech_name_mapping.keys()]

        yearly_split = operational[cols_split].sum(axis=0)
        tech_names = list(_tech_name_mapping.keys())
        return yearly_split, tech_names

    def _write_discounted_operational_to_timeline(
        self, discounted: pd.DataFrame, r_t: tuple[int, int]
    ) -> None:
        """Write discounted values back to the timeline for matching years and extend beyond target year.

        For years after target_year, use the target year's discounted values. Years before reference_year are untouched.
        """
        reference_year, target_year = r_t
        # Intersection years to override
        years_to_override = discounted.index.intersection(self.timeline.index)
        if len(years_to_override) > 0:
            discounted_subset = discounted.loc[years_to_override]
            self.timeline.loc[years_to_override, self._OPERATIONAL_COLS] = (
                discounted_subset[self._OPERATIONAL_COLS].to_numpy()
            )

        # Years after target_year take the target year's values
        target_year_key = f"Y_{target_year}"
        if target_year_key in discounted.index:
            after_target = self.timeline.index[self.timeline.index > target_year_key]
            if len(after_target) > 0:
                target_row = discounted.loc[target_year_key]
                target_vals = target_row[self._OPERATIONAL_COLS].to_numpy()
                # broadcast target values to all years after target
                self.timeline.loc[after_target, self._OPERATIONAL_COLS] = np.tile(
                    target_vals, (len(after_target), 1)
                )

        # Warn if some discount years are not present in the building timeline
        missing = discounted.index.difference(self.timeline.index)
        if len(missing) > 0:
            span = f"{reference_year}-{target_year}"
            missing_str = ", ".join(missing.tolist())
            print(
                f"Warning: Years {missing_str} in discount range {span} are not in the building {self.name}'s timeline; skipping those years."
            )

    def demolish(self, demolition_year: int) -> None:
        """
        1. Erase all future emissions after demolition year, including operational emissions.
        2. Log demolition emissions in the demolition year.

        :param demolition_year: the year, after end of which the building does not exist anymore.
        :type demolition_year: int
        """
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
            max_year = int(max_year_str.replace("Y_", ""))
            # if demolition_year > max_year, do nothing
            if demolition_year <= max_year:
                self.log_emission_in_timeline(
                    emission=demolition * area,
                    year=demolition_year,
                    col=f"demolition_{key}_kgCO2e",
                )

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
        return timeline

    def log_emission_with_lifetime(
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
        max_year = int(max_year_str.replace("Y_", ""))

        numeric_years = list(range(start_year, max_year + 1, lifetime))
        # Convert back to string format
        years = [f"Y_{year}" for year in numeric_years]
        self.log_emission_in_timeline(emission, years, col)

    def log_emission_in_timeline(
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
