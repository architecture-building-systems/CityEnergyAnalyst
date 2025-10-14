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
    "electricity": ("E_sys", "el"),
}
class OperationalHourlyTimeline:
    def __init__(
        self,
        locator: InputLocator,
        bpr: BuildingPropertiesRow,
        feedstock_db: Feedstocks,
    ):
        self.locator = locator
        self.bpr = bpr
        self.feedstock_db = feedstock_db
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
        obj._if_emission_calculated = True
        return obj
    
    def create_operational_timeline(self, n_hours: int) -> pd.DataFrame:
        """
        Create an operational timeline DataFrame with four columns:
        - `date`: date column from demand timeseries
        - `heating_kgCO2e`: emission for heating supply
        - `cooling_kgCO2e`: emission for cooling supply
        - `hot_water_kgCO2e`: emission for hot water supply
        - `electricity_kgCO2e`: emission for electricity supply
        The dataframe should have 8760 rows, one for each hour of the year, indexed by hour.

        :return: A DataFrame with 8760 rows and emission columns plus date column indexed by hours of the year,
            representing the operational emission timeline.
        :rtype: pd.DataFrame
        """
        timeline = pd.DataFrame(
            index=range(n_hours),
            columns=["date"] + [f"{key}_kgCO2e" for key in _tech_name_mapping.keys()]
            + [
                f"{tech_tuple[0]}_{feedstock}_kgCO2e"
                for tech_tuple in _tech_name_mapping.values()
                for feedstock in list(self.feedstock_db._library.keys()) + ["NONE"]
            ],
        )
        timeline.loc[:, :] = 0.0  # Initialize all values to zero
        timeline.index.name = "hour"

        # Add the date column from demand_timeseries
        date_col = next((col for col in self.demand_timeseries.columns if col.lower() == 'date'), None)
        if date_col:
            timeline['date'] = self.demand_timeseries[date_col].values
        else:
            raise ValueError("Date column not found in demand timeseries.")
        self._if_emission_calculated = False  # reset the flag when creating a new timeline
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
        type_pv: str,
        allocation_priority: list[str] | None = None,
        allow_techs: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Allocate on-site PV generation to offset hourly GRID electricity consumption across technologies,
        mutate the demand timeseries accordingly, and return a compact allocation summary per hour.

        :param type_pv: Key used with the locator to find the PV hourly results for this building.
        :type type_pv: str
        :param allocation_priority: Explicit priority order for technologies (keys of _tech_name_mapping) that are eligible for
            PV allocation. The first item gets PV first in each hour. If None, defaults to
            `["electricity", "heating", "hot_water", "cooling"]`.
            If the list contains less than 4 items, the remaining eligible technologies will still be appended.
        :type allocation_priority: list[str] | None, optional
        :param allow_techs: Optional whitelist of technologies (`heating`, `hot_water`, `cooling`, `electricity`)
            to which PV can be allocated.
            If None, all technologies are allowed.
        :type allow_techs: list[str] | None, optional
        :return: A DataFrame with hourly PV allocation summary including:
            - `E_PV_gen_kWh`: Total PV generation in kWh (same as `E_PV_gen_kWh` in the original PV results).
            - `E_PV_gen_used_kWh`: Total PV generation used in kWh.
            - `E_PV_gen_kWh_leftover`: Total PV generation leftover in kWh.
            - `avoided_emission_kgCO2e`: Total avoided emissions in kgCO2e.
            plus one column per allowed tech: `PV_to_{tech}_kWh_input` representing PV electricity
            input allocated to that tech in each hour.
        :rtype: pd.DataFrame

        Notes
        -----
        - Must be called before `calculate_operational_emission()`; this function mutates
          the demand timeseries, so it must be called before calculating emissions.
        - Surplus PV is assumed exported (not credited toward operational emission reduction here).
        - Avoided emissions are calculated using the hourly GRID emission intensity timeline.
        """
        # ensure the results file exists
        if self._if_emission_calculated:
            raise RuntimeError(
                "PV contributions updates current demand timeseries. Please run this before calculating "
                "emissions or reset the timeline using create_operational_timeline()."
            )

        # Priority and whitelist handling
        all_tech_keys = list(_tech_name_mapping.keys())
        default_priority = ["electricity", "heating", "hot_water", "cooling"]
        if allocation_priority is None:
            allocation_priority = default_priority
        allocation_priority = [t for t in allocation_priority if t in all_tech_keys]
        if not allocation_priority:
            allocation_priority = default_priority

        allowed_set = set(all_tech_keys) if allow_techs is None else set(allow_techs) & set(all_tech_keys)
        ordered_techs = [t for t in allocation_priority if t in allowed_set]
        ordered_techs += [t for t in all_tech_keys if t in allowed_set and t not in ordered_techs]

        pv_results_path = self.locator.PV_results(self.bpr.name, type_pv)
        if not os.path.exists(pv_results_path):
            raise FileNotFoundError(f"PV results file not found for {type_pv} at {pv_results_path}.")

        pv_hourly_results = pd.read_csv(pv_results_path, index_col=None)
        if len(pv_hourly_results) != HOURS_IN_YEAR:
            raise ValueError(
                f"PV results for {type_pv} should have {HOURS_IN_YEAR} rows, but got {len(pv_hourly_results)} rows."
            )
        # Align to demand index for label-safe arithmetic
        pv_hourly_results.index = self.demand_timeseries.index

        if 'E_PV_gen_kWh' not in pv_hourly_results.columns:
            raise ValueError(f"Expected column 'E_PV_gen_kWh' not found in PV results for {type_pv}.")

        # Validate GRID emission intensity availability
        if 'GRID' not in self.emission_intensity_timeline.columns:
            raise ValueError("'GRID' emission intensity timeline is missing.")
        if len(self.emission_intensity_timeline) != len(self.demand_timeseries):
            raise ValueError("Emission intensity timeline length does not match demand timeline length.")

        pv_hourly_results["E_PV_gen_kWh_leftover"] = pv_hourly_results["E_PV_gen_kWh"].astype(float)

        # Initialize per-tech allocation trackers (electricity input basis)
        per_tech_allocation = {f"PV_to_{t}_kWh_input": pd.Series(0.0, index=self.demand_timeseries.index) for t in allowed_set}

        # Allocate PV following explicit order
        for demand_type in ordered_techs:
            demand_col_name, supply_type_name = _tech_name_mapping[demand_type]
            demand_col = f"{demand_col_name}_kWh"

            feedstock: str = self.bpr.supply[f"source_{supply_type_name}"]
            if feedstock != 'GRID':
                continue
            if demand_col not in self.demand_timeseries.columns:
                raise ValueError(f"Expected demand column '{demand_col}' not found in demand timeseries.")

            eff: float = self.bpr.supply[f"eff_{supply_type_name}"]
            eff = eff if eff > 0 else 1.0  # avoid division by zero

            elec_input_demand = self.demand_timeseries[demand_col].astype(float) / eff
            pv_left = pv_hourly_results["E_PV_gen_kWh_leftover"].to_numpy(dtype=float)
            req = elec_input_demand.to_numpy(dtype=float)
            pv_deduction = np.minimum(pv_left, req)

            # Reduce end-use demand by PV input * eff, clip at 0
            self.demand_timeseries[demand_col] = (
                self.demand_timeseries[demand_col].astype(float) - pv_deduction * eff
            ).clip(lower=0)

            # Update leftover PV
            pv_hourly_results["E_PV_gen_kWh_leftover"] = (
                pv_hourly_results["E_PV_gen_kWh_leftover"].astype(float) - pv_deduction
            ).clip(lower=0)

            # Track allocation to this tech
            per_tech_allocation[f"PV_to_{demand_type}_kWh_input"] = pd.Series(pv_deduction, index=self.demand_timeseries.index)

        # Warn on surplus
        if pv_hourly_results["E_PV_gen_kWh_leftover"].sum() > 0:
            warnings.warn(
                f"There is leftover PV generation for {type_pv} in building {self.bpr.name} after covering all GRID electricity demands. "
                f"This is because in some hours, PV generation exceeds the total GRID electricity demand and there's no battery to store excess generation. "
                f"Leftover PV generation will not be accounted for in the current operational emission calculation, "
                f"because it is assumed to be exported back to the grid. "
                f"Total yearly leftover PV generation: {pv_hourly_results['E_PV_gen_kWh_leftover'].sum():.2f} kWh.",
                RuntimeWarning,
            )

        # Used PV and avoided emissions
        pv_hourly_results["E_PV_gen_used_kWh"] = (
            pv_hourly_results["E_PV_gen_kWh"].astype(float)
            - pv_hourly_results["E_PV_gen_kWh_leftover"].astype(float)
        )
        pv_hourly_results["avoided_emission_kgCO2e"] = (
            pv_hourly_results["E_PV_gen_used_kWh"].to_numpy(dtype=float)
            * self.emission_intensity_timeline["GRID"].to_numpy(dtype=float)
        )

        # Prepare compact output with per-tech columns in the chosen order
        base_cols = [
            "E_PV_gen_kWh",
            "E_PV_gen_used_kWh",
            "E_PV_gen_kWh_leftover",
            "avoided_emission_kgCO2e",
        ]
        tech_cols = [f"PV_to_{t}_kWh_input" for t in ordered_techs if f"PV_to_{t}_kWh_input" in per_tech_allocation]
        alloc_df = pd.DataFrame(per_tech_allocation)
        alloc_df.index = pv_hourly_results.index
        out_df = pd.concat([pv_hourly_results[base_cols], alloc_df[tech_cols]], axis=1)
        out_df.index.name = "hour"
        return out_df

    def calculate_operational_emission(self) -> None:
        """
        This function calculates the emission timeline for heating,
        domestic hot water, cooling and electrical supply.
        """
        for demand_type, tech_tuple in _tech_name_mapping.items():
            eff: float = self.bpr.supply[f"eff_{tech_tuple[1]}"]
            eff = eff if eff > 0 else 1.0  # avoid division by zero
            feedstock: str = self.bpr.supply[f"source_{tech_tuple[1]}"]
            self.operational_emission_timeline[f"{tech_tuple[0]}_{feedstock}_kgCO2e"] = (
                self.demand_timeseries[f"{tech_tuple[0]}_kWh"]  # kWh
                / eff
                * self.emission_intensity_timeline[feedstock]  # kgCO2/kWh
            )
            self.operational_emission_timeline[f"{demand_type}_kgCO2e"] = (
                self.operational_emission_timeline[f"{tech_tuple[0]}_{feedstock}_kgCO2e"]
            )
        self._if_emission_calculated = True

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
