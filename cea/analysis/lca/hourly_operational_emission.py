from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.database.components import Feedstocks
from cea.demand.building_properties import BuildingProperties
from cea.utilities import epwreader

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import (
        BuildingPropertiesRow,
    )
    from cea.inputlocator import InputLocator

_tech_name_mapping = {
    # tech_name: (<demand_col_name>, <supply_type_name>)
    "heating": ("Qhs_sys", "hs"),
    "hot_water": ("Qww_sys", "dhw"),
    "cooling": ("Qcs_sys", "cs"),
    "appliances": ("E_sys", "el"),
}
class OperationalHourlyTimeline:
    def __init__(
        self,
        locator: InputLocator,
        bpr: BuildingPropertiesRow,
        feedstock_db: Feedstocks,
    ):
        self._is_emission_calculated = False
        self.locator = locator
        self.bpr = bpr
        self.feedstock_db = feedstock_db
        # Track which per-tech PV allocation columns were added per PV code for traceability
        self._pv_allocation: dict[str, pd.DataFrame] = {}
        self.emission_intensity_timeline = self.expand_feedstock_emissions()
        self.demand_timeseries = pd.read_csv(locator.get_demand_results_file(self.bpr.name))
        self.operational_emission_timeline = self.create_operational_timeline(n_hours=HOURS_IN_YEAR)

    @classmethod
    def from_result(cls, locator: InputLocator, building_name: str):
        hourly_results_csv = locator.get_lca_operational_hourly_building(building_name)
        if not os.path.exists(hourly_results_csv):
            raise FileNotFoundError(f"Operational emission results file not found for building {building_name} at {hourly_results_csv}. Please run the calculation first.")
        feedstock_db = Feedstocks.from_locator(locator)
        weather_path = locator.get_weather_file()
        weather_data = epwreader.epw_reader(weather_path)[
            ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
        ]
        bpr = BuildingProperties(locator, weather_data, [building_name])[building_name]
        obj = cls(locator, bpr, feedstock_db)
        obj.operational_emission_timeline = pd.read_csv(hourly_results_csv, index_col='hour')
        obj._is_emission_calculated = True
        return obj
    
    def create_operational_timeline(self, n_hours: int) -> pd.DataFrame:
        """
        Create an operational timeline DataFrame containing:
        - `date`: date column from demand timeseries
        - per-tech emissions: one column per technology and feedstock combination,
          e.g., `appliance_GRID_kgCO2e`, `heating_NG_kgCO2e`, etc., initialized to zero.

        The dataframe should have 8760 rows, one for each hour of the year, indexed by hour.

        :return: A DataFrame with 8760 rows and emission columns plus date column indexed by hours of the year,
            representing the operational emission timeline.
        :rtype: pd.DataFrame
        """
        base_cols = ["date"] + [
            f"{key}_{feedstock}_kgCO2e"
            for key in _tech_name_mapping.keys()
            for feedstock in list(self.feedstock_db._library.keys()) + ["NONE"]
        ]
        # No PV columns are pre-created; PV offsets are added per scenario during calculation with suffixed names
        timeline = pd.DataFrame(index=range(n_hours), columns=base_cols)
        timeline.loc[:, :] = 0.0  # Initialize all values to zero
        timeline.index.name = "hour"

        # Add the date column from demand_timeseries
        date_col = next((col for col in self.demand_timeseries.columns if col.lower() == 'date'), None)
        if date_col:
            timeline['date'] = self.demand_timeseries[date_col].values
        else:
            raise ValueError("Date column not found in demand timeseries.")
        self._is_emission_calculated = False
        return timeline

    def expand_feedstock_emissions(self) -> pd.DataFrame:
        """
        generate a hourly timeline of feedstock emission intensity
        by repeating the hourly values in the feedstock database.

        For example, the original feedstock database might have 24 rows,
        one for each hour of the day; or it could have 168 rows,
        one for each hour of the week. The values in the database represents a repetitive
        pattern of emissions throughout the `nrows` hours of a year, starting from hour 0.

        :param feedstock_db: The feedstock database containing hourly emission values.
            It has a `_library` attribute which is a dictionary of DataFrames,
            each representing the emissions for a specific feedstock type.
        :type feedstock_db: Feedstocks
        :return: A DataFrame with 8760 rows and columns of feedstocks indexed by hours of the year,
            representing the expanded feedstock emissions timeline, each value in unit of kgCO2/MJ.
        :rtype: pd.DataFrame
        """
        # The emission in feedstock databases are recorded for example in hours of a day.
        # To match the yearly operational timeline, expanded emission intensity timeline
        expanded_timeline = pd.DataFrame(
            index=range(HOURS_IN_YEAR), columns=list(self.feedstock_db._library.keys())
        )
        for feedstock, df in self.feedstock_db._library.items():
            # if original timeline is not n * 24 hours, throw warning that definition might be problematic
            if len(df) % 24 != 0:
                warnings.warn(
                    f"{feedstock} timeline is not n * 24 hours. The definition will not repeat on a daily basis.",
                    RuntimeWarning,
                )
            expanded_timeline[feedstock] = np.resize(
                df["GHG_kgCO2MJ"].to_numpy(), len(expanded_timeline)
            )
            expanded_timeline[feedstock] = expanded_timeline[feedstock].astype(float)
            expanded_timeline[feedstock] *= 3.6  # convert from kgCO2/MJ to kgCO2/kWh

        expanded_timeline["NONE"] = 0.0

        return expanded_timeline
    
    def log_pv_contribution(
        self,
        pv_codes: list[str],
        allocation_priority: list[str] | None = None,
        allowed_demands: list[str] | None = None,
    ) -> None:
        """
        Allocate on-site PV generation to offset hourly GRID electricity consumption across technologies,
        without mutating the original demand timeseries. Supports one or multiple PV types as separate
        scenarios; stores each allocation under its PV name and returns a dict mapping PV name to its
        allocation DataFrame.

        :param pv_codes: List of PV type names. Each is used with the locator
            to find the PV hourly results for this building.
        :type pv_codes: list[str]
        :param allocation_priority: Explicit priority order for technologies (keys of _tech_name_mapping) that are eligible for
            PV allocation. The first item gets PV first in each hour. If None, defaults to
            `["appliance", "heating", "hot_water", "cooling"]`.
            If the list contains less than 4 items, the remaining eligible technologies will still be appended.
        :type allocation_priority: list[str] | None, optional
        :param allow_techs: Optional whitelist of technologies (`heating`, `hot_water`, `cooling`, `appliance`)
            to which PV can be allocated.
            If None, all technologies are allowed.
        :type allow_techs: list[str] | None, optional
        

        Notes
        -----
        - Must be called before `calculate_operational_emission()`; calculation will materialize PV offset columns
        for all logged PV scenarios (suffixed with `__{pv_name}`), leaving base emission columns unchanged.
            - Surplus PV is assumed exported (not credited toward operational emission reduction here).
            - PV offsets are calculated using the hourly GRID emission intensity timeline and are negative by convention.

        - For each PV type, four types of columns are added to the timeline:
            - `PV_{pv_code}_E_PV_gen` columns: how much of PV is sold, how much is used
            - `PV_to_{demand}` columns: for each demand, how much PV did it use
            - `PV_offset_{demand}` columns: for each demand, how much GRID emissions were avoided from using PV (negative)
            - `PV_offset_total_kgCO2e`: total GRID emissions avoided from using PV (negative)
        """
        if len(pv_codes) == 0:
            raise ValueError("pv_codes must contain at least one PV type name.")

        ordered_demands = self._order_demands(allocation_priority, allowed_demands)

        for pv_code in pv_codes:
            pv_hourly_raw = self._load_pv_hourly(pv_code) # E_PV_gen_kWh, E_PV_gen_kWh_leftover
            pv_hourly_allocated, added_cols = self._allocate_pv_to_techs(pv_hourly_raw, ordered_demands, self.grid_intensity)

            self._warn_leftover(pv_hourly_allocated, pv_code)
            pv_hourly_final = self._aggregate_pv_emissions(pv_hourly_allocated)

            power_allo_cols = [
                self._PV_GEN_COL, self._PV_USED_COL, self._PV_LEFTOVER_COL,
            ] + [
                f"PV_to_{t}_kWh_input"
                for t in ordered_demands
                if f"PV_to_{t}_kWh_input" in added_cols
            ]
            emission_offset_cols = [
                f"PV_offset_{t}_kgCO2e"
                for t in ordered_demands
                if f"PV_offset_{t}_kgCO2e" in pv_hourly_final.columns
            ] + [self._PV_OFFSET_TOTAL_COL]

            suffixed_for_emission = pv_hourly_final[emission_offset_cols].rename(
                columns={
                    c: c.replace("PV_", f"PV_{pv_code}_") for c in emission_offset_cols
                }
            )

            self.operational_emission_timeline.loc[:, suffixed_for_emission.columns] = (
                suffixed_for_emission.to_numpy(dtype=float)
            )
            self._pv_allocation[pv_code] = pv_hourly_final[power_allo_cols]

    # ---- PV helpers (internal) -----------------------------------------------------

    _PV_GEN_COL = "E_PV_gen_kWh"
    _PV_LEFTOVER_COL = "E_PV_gen_kWh_leftover"
    _PV_USED_COL = "E_PV_gen_used_kWh"
    _PV_OFFSET_TOTAL_COL = "PV_offset_total_kgCO2e"

    @property
    def grid_intensity(self) -> np.ndarray:
        if 'GRID' not in self.emission_intensity_timeline.columns:
            raise ValueError("'GRID' emission intensity timeline is missing.")
        return self.emission_intensity_timeline["GRID"].to_numpy(dtype=float)

    def _order_demands(self, allocation_priority: list[str] | None, allow_demands: list[str] | None) -> list[str]:
        all_demands = list(_tech_name_mapping.keys())
        default_priority = ["appliance", "heating", "hot_water", "cooling"]
        prioritized_demands = list(allocation_priority) if allocation_priority else default_priority
        prioritized_demands = [demand for demand in prioritized_demands if demand in all_demands]
        if not prioritized_demands:
            prioritized_demands = default_priority
        allowed_set = set(all_demands) if allow_demands is None else (set(allow_demands) & set(all_demands))
        ordered = [t for t in prioritized_demands if t in allowed_set]
        ordered += [t for t in all_demands if t in allowed_set and t not in ordered]
        return ordered

    def _load_pv_hourly(self, pv_code: str) -> pd.DataFrame:
        pv_results_path = self.locator.PV_results(self.bpr.name, pv_code)
        if not os.path.exists(pv_results_path):
            raise FileNotFoundError(f"PV results file not found for {pv_code} at {pv_results_path}.")
        df = pd.read_csv(pv_results_path, index_col=None)
        if len(df) != HOURS_IN_YEAR:
            raise ValueError(
                f"PV results for {pv_code} should have {HOURS_IN_YEAR} rows, but got {len(df)} rows."
            )
        df.index = self.demand_timeseries.index  # align to demand index
        if self._PV_GEN_COL not in df.columns:
            raise ValueError(f"Expected column '{self._PV_GEN_COL}' not found in PV results for {pv_code}.")
        df[self._PV_LEFTOVER_COL] = df[self._PV_GEN_COL].astype(float)
        return df

    def _allocate_pv_to_techs(
        self,
        pv_hourly_results: pd.DataFrame,
        ordered_demands: list[str],
        grid_intensity: np.ndarray,
    ) -> tuple[pd.DataFrame, list[str]]:
        """Allocate PV to GRID-supplied technologies in the given order, adding per-tech columns and offsets.

        Returns
        -------
        (updated_df, added_cols)
            updated_df: New DataFrame with E_PV_gen_kWh_leftover updated and per-tech columns (PV_to_*) and
                per-demand offset columns (PV_offset_*) added.
            added_cols: List of newly added per-tech PV_to_* column names (in demand priority order).
        """
        pv_df = pv_hourly_results.copy()
        added_cols: list[str] = []
        for demand_type in ordered_demands:
            demand_col_name, supply_type_name = _tech_name_mapping[demand_type]
            demand_col = f"{demand_col_name}_kWh"

            feedstock: str = self.bpr.supply[f"source_{supply_type_name}"]
            if feedstock != 'GRID':
                continue
            if demand_col not in self.demand_timeseries.columns:
                raise ValueError(f"Expected demand column '{demand_col}' not found in demand timeseries.")

            eff: float = self.bpr.supply[f"eff_{supply_type_name}"]
            eff = eff if eff > 0 else 1.0  # avoid division by zero

            # Electricity input required to supply this end-use demand via GRID
            elec_input_demand = self.demand_timeseries[demand_col].astype(float) / eff
            pv_left = pv_df[self._PV_LEFTOVER_COL].to_numpy(dtype=float)
            req = elec_input_demand.to_numpy(dtype=float)
            pv_deduction = np.minimum(pv_left, req)

            # Update leftover PV in the new copy
            pv_df[self._PV_LEFTOVER_COL] = (
                pv_df[self._PV_LEFTOVER_COL].astype(float) - pv_deduction
            ).clip(lower=0)

            col_name = f"PV_to_{demand_type}_kWh_input"
            pv_df[col_name] = pd.Series(pv_deduction, index=self.demand_timeseries.index)
            added_cols.append(col_name)
            # Per-demand negative offsets directly from allocation
            pv_df[f"PV_offset_{demand_type}_kgCO2e"] = -(
                pv_df[col_name].to_numpy(dtype=float) * grid_intensity
            ).astype(float)
        return pv_df, added_cols

    def _aggregate_pv_emissions(self, pv_hourly_results: pd.DataFrame) -> pd.DataFrame:
        """Compute used PV and total offsets (sum of per-demand offsets), returning a new DataFrame.
        """
        pv_df = pv_hourly_results.copy()
        pv_df[self._PV_USED_COL] = (
            pv_df[self._PV_GEN_COL].astype(float)
            - pv_df[self._PV_LEFTOVER_COL].astype(float)
        )
        # Total negative PV offset is the sum of per-demand offsets (already negative)
        per_demand_cols = [
            f"PV_offset_{d}_kgCO2e" for d in _tech_name_mapping.keys() if f"PV_offset_{d}_kgCO2e" in pv_df.columns
        ]
        if per_demand_cols:
            pv_df[self._PV_OFFSET_TOTAL_COL] = pv_df[per_demand_cols].sum(axis=1).astype(float)
        else:
            pv_df[self._PV_OFFSET_TOTAL_COL] = 0.0
        return pv_df

    def _warn_leftover(self, pv_hourly_results: pd.DataFrame, pv_code: str) -> None:
        total_leftover = float(pv_hourly_results[self._PV_LEFTOVER_COL].sum())
        if total_leftover > 0:
            warnings.warn(
                f"There is leftover PV generation for {pv_code} in building {self.bpr.name} after covering all electricity demands from GRID. "
                f"This is because in some hours, PV generation exceeds the total electricity demand from GRID and there's no battery to store excess generation. "
                f"Leftover PV generation will not be accounted for in the current operational emission calculation, "
                f"because it is assumed to be exported back to the grid. "
                f"Total yearly leftover PV generation: {total_leftover:.2f} kWh.",
                RuntimeWarning,
            )

    def calculate_operational_emission(self) -> None:
        """
        This function calculates the emission timeline for heating,
        domestic hot water, cooling and electrical supply.
        
        Behavior with PV scenarios
        --------------------------
        - Base emission columns (per-tech and per-supply) are computed from demand and feedstock intensities and
            are NOT altered by PV.
        - For each logged PV scenario (via `log_pv_contribution`), per-tech PV offset columns
            `PV_offset_{tech}_kgCO2e__{pv}` and a total `PV_offset_total_kgCO2e__{pv}` are added to the timeline.
        - No unsuffixed PV columns are written; all PV offsets carry the scenario suffix to avoid ambiguity.
        """
        for demand_type, tech_tuple in _tech_name_mapping.items():
            eff: float = self.bpr.supply[f"eff_{tech_tuple[1]}"]
            eff = eff if eff > 0 else 1.0  # avoid division by zero
            feedstock: str = self.bpr.supply[f"source_{tech_tuple[1]}"]
            self.operational_emission_timeline[f"{demand_type}_{feedstock}_kgCO2e"] = (
                self.demand_timeseries[f"{tech_tuple[0]}_kWh"]  # kWh
                / eff
                * self.emission_intensity_timeline[feedstock]  # kgCO2/kWh
            )
        self._is_emission_calculated = True

    @property
    def total_operational_emission(self) -> pd.Series:
        """
        Calculate the total operational emission across all technologies and feedstocks.

        :return: A Series representing the total operational emission per hour in kgCO2e.
        :rtype: pd.Series
        """
        if not self._is_emission_calculated:
            raise RuntimeError("Operational emissions have not been calculated yet. Please call calculate_operational_emission() first.")
        emission_cols = [
            col for col in self.operational_emission_timeline.columns
            if col != 'date'
        ]
        total_emission = self.operational_emission_timeline[emission_cols].sum(axis=1)
        return total_emission
    
    @property
    def emission_by_demand(self) -> pd.DataFrame:
        """
        Get a DataFrame summarizing total operational emissions by demand type.

        :return: A DataFrame with total emissions per demand type in kgCO2e.
        :rtype: pd.DataFrame
        """
        if not self._is_emission_calculated:
            raise RuntimeError("Operational emissions have not been calculated yet. Please call calculate_operational_emission() first.")
        data = {}
        for demand_type, _ in _tech_name_mapping.items():
            demand_cols = [
                col for col in self.operational_emission_timeline.columns
                if col.startswith(f"{demand_type}_")
            ]
            data[demand_type] = self.operational_emission_timeline[demand_cols].sum(axis=1)
        return pd.DataFrame(data)

    @property
    def emission_by_feedstock(self) -> pd.DataFrame:
        """
        Get a DataFrame summarizing total operational emissions by feedstock type.

        :return: A DataFrame with total emissions per feedstock type in kgCO2e.
        :rtype: pd.DataFrame
        """
        if not self._is_emission_calculated:
            raise RuntimeError("Operational emissions have not been calculated yet. Please call calculate_operational_emission() first.")
        data = {}
        feedstock_types = list(self.feedstock_db._library.keys()) + ["NONE"]
        for feedstock in feedstock_types:
            feedstock_cols = [
                col for col in self.operational_emission_timeline.columns
                if col.endswith(f"_{feedstock}_kgCO2e")
            ]
            data[feedstock] = self.operational_emission_timeline[feedstock_cols].sum(axis=1)
        return pd.DataFrame(data)
        

    def save_results(self) -> None:
        """
        Save the operational emission results to a CSV file.
        """
        if not os.path.exists(self.locator.get_lca_timeline_folder()):
            os.makedirs(self.locator.get_lca_timeline_folder())

        # Reset index to convert hour index to a column, then reorder columns
        df_to_save = self.operational_emission_timeline.reset_index()
        # Move hour column to the end, and ensure date column is first
        date_cols = ['date'] if 'date' in df_to_save.columns else []
        emission_cols = [col for col in df_to_save.columns if col not in ['hour', 'date']]
        hour_cols = ['hour']
        cols = date_cols + emission_cols + hour_cols
        df_to_save = df_to_save[cols]

        df_to_save.to_csv(
            self.locator.get_lca_operational_hourly_building(self.bpr.name),
            index=False, float_format='%.3f')


if __name__ == "__main__":
    from cea.config import Configuration
    from cea.datamanagement.database.components import Feedstocks
    from cea.demand.building_properties import BuildingProperties
    from cea.inputlocator import InputLocator
    from cea.utilities import epwreader

    config = Configuration()
    locator = InputLocator(config.scenario)
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    demand_cfg = getattr(config, 'demand')
    buildings = list(getattr(demand_cfg, 'buildings', []))
    if not buildings:
        raise SystemExit("No buildings configured for demand; cannot run standalone example.")
    building_properties = BuildingProperties(
        locator, weather_data, buildings
    )
    bpr = building_properties[buildings[0]]
    feedstock_db = Feedstocks.from_locator(locator)
    test_timeline = OperationalHourlyTimeline(locator, bpr, feedstock_db)
    test_timeline.calculate_operational_emission()
    test_timeline.save_results()
