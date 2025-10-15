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
    
    def log_pv_contribution(self, type_pv: str) -> tuple[list[float], list[float]]:
        # ensure the results file exists
        if self._if_emission_calculated:
            raise RuntimeError("PV contributions updates current demand timeseries. Please run this before calculating emissions or reset the timeline using create_operational_timeline().")
        
        pv_results_path = self.locator.PV_results(self.bpr.name, type_pv)
        if not os.path.exists(pv_results_path):
            raise FileNotFoundError(f"PV results file not found for {type_pv} at {pv_results_path}.")

        pv_hourly_results = pd.read_csv(pv_results_path, index_col=None)
        if len(pv_hourly_results) != HOURS_IN_YEAR:
            raise ValueError(f"PV results for {type_pv} should have {HOURS_IN_YEAR} rows, but got {len(pv_hourly_results)} rows.")
        # use the same index as demand timeseries
        pv_hourly_results.index = self.demand_timeseries.index

        if 'E_PV_gen_kWh' not in pv_hourly_results.columns:
            raise ValueError(f"Expected column 'E_PV_gen_kWh' not found in PV results for {type_pv}.")

        pv_hourly_results["E_PV_gen_kWh_leftover"] = pv_hourly_results["E_PV_gen_kWh"].copy()
        
        # then check all the techs that use electricity and deduct the demand from PV generation, and update the leftover pv generation
        for _, tech_tuple in _tech_name_mapping.items():
            eff: float = self.bpr.supply[f"eff_{tech_tuple[1]}"]
            eff = eff if eff > 0 else 1.0  # avoid division by zero
            feedstock: str = self.bpr.supply[f"source_{tech_tuple[1]}"]
            if feedstock == 'GRID':
                # only consider the techs that use grid electricity
                demand_col = f"{tech_tuple[0]}_kWh"
                
                if demand_col not in self.demand_timeseries.columns:
                    raise ValueError(f"Expected demand column '{demand_col}' not found in demand timeseries.")
                
                electricity_demand = self.demand_timeseries[demand_col].copy() / eff  # kWh
                pv_deduction = np.minimum(pv_hourly_results["E_PV_gen_kWh_leftover"], electricity_demand)
                self.demand_timeseries[demand_col] -= pv_deduction * eff
                self.demand_timeseries[demand_col] = self.demand_timeseries[demand_col].clip(lower=0)
                pv_hourly_results["E_PV_gen_kWh_leftover"] -= pv_deduction
                pv_hourly_results["E_PV_gen_kWh_leftover"] = pv_hourly_results["E_PV_gen_kWh_leftover"].clip(lower=0)
        # after processing all techs, check if there is any leftover pv generation
        if pv_hourly_results["E_PV_gen_kWh_leftover"].sum() > 0:
            warnings.warn(
                f"There is leftover PV generation for {type_pv} in building {self.bpr.name} after covering all GRID electricity demands. "
                f"This is because in some hours, PV generation exceeds the total GRID electricity demand and there's no battery to store excess generation. "
                f"Leftover PV generation will not be accounted for in the current operational emission calculation, "
                f"because it is assumed to be exported back to the grid. "
                f"Total yearly leftover PV generation: {pv_hourly_results['E_PV_gen_kWh_leftover'].sum():.2f} kWh.",
                RuntimeWarning,
            )
        pv_hourly_results["E_PV_gen_used_kWh"] = pv_hourly_results["E_PV_gen_kWh"] - pv_hourly_results["E_PV_gen_kWh_leftover"]
        pv_gen_used_kWh: list[float] = pv_hourly_results["E_PV_gen_used_kWh"].to_numpy(dtype=float).tolist()
        pv_avoided_emission_arr = pv_hourly_results["E_PV_gen_used_kWh"].to_numpy(dtype=float) * self.emission_intensity_timeline["GRID"].to_numpy(dtype=float)
        pv_avoided_emission_kgCO2e: list[float] = pv_avoided_emission_arr.tolist()
        return pv_gen_used_kWh, pv_avoided_emission_kgCO2e

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
