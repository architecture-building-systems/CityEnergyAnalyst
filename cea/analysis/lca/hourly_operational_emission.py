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

__author__      = "Yiqiao Wang, Zhongming Shi"
__copyright__   = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__     = ["Yiqiao Wang", "Zhongming Shi"]
__license__     = "MIT"
__version__     = "0.1"
__maintainer__  = "Reynold Mok"
__email__       = "cea@arch.ethz.ch"
__status__      = "Production"

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import (
        BuildingPropertiesRow,
    )
    from cea.inputlocator import InputLocator

_tech_name_mapping = {
    "Qhs_sys": "hs",
    "Qww_sys": "dhw",
    "Qcs_sys": "cs",
    "E_sys": "el",
}

# All GRID components for PV allocation
_GRID_COMPONENTS = [
    'GRID_a',      # Appliances
    'GRID_l',      # Lighting
    'GRID_v',      # Ventilation
    'GRID_ve',     # Elevators
    'GRID_data',   # Data centers
    'GRID_pro',    # Industrial processes
    'GRID_aux',    # Auxiliary
    'GRID_cdata',  # Data center cooling
    'GRID_cre',    # Refrigeration cooling
    'GRID_hs',     # Heating
    'GRID_cs',     # Cooling
    'GRID_ww',     # Domestic hot water
]
class OperationalHourlyTimeline:
    def __init__(
        self,
        locator: InputLocator,
        bpr: BuildingPropertiesRow,
    ):
        self._is_emission_calculated = False
        self.locator = locator
        self.bpr = bpr
        self.feedstock_db = Feedstocks.from_locator(locator)
        # Track which per-tech PV allocation columns were added per PV code for traceability
        self._pv_allocation: dict[str, pd.DataFrame] = {}
        self.emission_intensity_timeline = self.expand_feedstock_emissions()
        self.demand_timeseries = pd.read_csv(locator.get_demand_results_file(self.bpr.name), index_col=None)
        self.demand_timeseries.index.set_names(['hour'], inplace=True)
        self.operational_emission_timeline = self.create_operational_timeline(n_hours=HOURS_IN_YEAR)

    @classmethod
    def from_result(cls, locator: InputLocator, building_name: str):
        hourly_results_csv = locator.get_lca_operational_hourly_building(building_name)
        if not os.path.exists(hourly_results_csv):
            raise FileNotFoundError(f"Operational emission results file not found for building {building_name} at {hourly_results_csv}. Please run the calculation first.")
        weather_path = locator.get_weather_file()
        weather_data = epwreader.epw_reader(weather_path)[
            ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
        ]
        bpr = BuildingProperties(locator, weather_data, [building_name])[building_name]
        obj = cls(locator, bpr)
        obj.operational_emission_timeline = pd.read_csv(hourly_results_csv, index_col='hour')
        obj._is_emission_calculated = True
        # delete the secondary columns (per-demand columns and per-feedstock columns)
        per_demand_cols = obj.emission_by_demand.columns.tolist()
        per_feedstock_cols = obj.emission_by_feedstock.columns.tolist()
        obj.operational_emission_timeline.drop(columns=per_demand_cols + per_feedstock_cols, inplace=True, errors='ignore')
        return obj
    
    def create_operational_timeline(self, n_hours: int) -> pd.DataFrame:
        """
        Create an operational timeline DataFrame containing:
        - `date`: date column from demand timeseries
        - per-tech emissions: one column per technology and feedstock combination,
          e.g., `E_sys_GRID_kgCO2e`, `Qhs_sys_NATURALGAS_kgCO2e`, etc., initialized to zero.
        - per-component PV emission offsets: one column per GRID component per PV code

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

        # PV emission offset columns are added dynamically in log_pv_contribution()
        # only when consider-pv-contributions is True

        timeline = pd.DataFrame(index=range(n_hours), columns=base_cols)
        timeline.loc[:, :] = 0.0  # Initialize all values to zero
        timeline.index.set_names(['hour'], inplace=True)

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
    
    # ---- PV helpers (internal) -----------------------------------------------------

    @property
    def grid_intensity(self) -> np.ndarray:
        if 'GRID' not in self.emission_intensity_timeline.columns:
            raise ValueError("'GRID' emission intensity timeline is missing.")
        return self.emission_intensity_timeline["GRID"].to_numpy(dtype=float)

    def _load_pv_hourly(self, pv_code: str) -> pd.DataFrame:
        pv_results_path = self.locator.PV_results(self.bpr.name, pv_code)
        if not os.path.exists(pv_results_path):
            error_msg = (
                f"PV electricity results missing for building {self.bpr.name}, panel type: {pv_code}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results. "
                f"Expected file: {pv_results_path}"
            )
            print(f"ERROR: {error_msg}")
            raise FileNotFoundError(error_msg)
        df = pd.read_csv(pv_results_path, index_col=None)
        if len(df) != HOURS_IN_YEAR:
            raise ValueError(
                f"PV results for {pv_code} should have {HOURS_IN_YEAR} rows, but got {len(df)} rows."
            )
        df.index = self.demand_timeseries.index  # align to demand index
        if 'E_PV_gen_kWh' not in df.columns:
            raise ValueError(f"Expected column 'E_PV_gen_kWh' not found in PV results for {pv_code}.")
        return df

    def apply_pv_offsetting(self, pv_codes: list[str] | None = None) -> None:
        """
        Apply simple net metering PV offsetting to GRID emissions.

        For each PV panel, calculates:
        - PV_{code}_GRID_offset_kgCO2e: Avoided emissions from on-site use (negative)
        - PV_{code}_GRID_export_kgCO2e: Avoided emissions from grid export (negative)

        Both columns are negative values representing emission reductions.

        Parameters
        ----------
        pv_codes : list[str] | None
            List of PV panel codes to include (e.g., ["PV1", "PV2"])
            If None, includes all available panels
        """
        from cea.analysis.lca.pv_offsetting import calculate_net_energy

        # Get annual net energy (this is just for logging)
        net_energy_annual = calculate_net_energy(
            self.locator,
            self.bpr.name,
            include_pv=True,
            pv_codes=pv_codes
        )

        pv_by_type: dict[str, float] = net_energy_annual['PV_by_type']
        pv_codes_used = list(pv_by_type.keys())

        if not pv_codes_used:
            warnings.warn(
                f"No PV panels found for building {self.bpr.name}. Skipping PV offsetting.",
                RuntimeWarning
            )
            return

        # Check which panels actually exist before processing
        missing_panels = []
        available_panels = []
        for pv_code in pv_codes_used:
            pv_path = self.locator.PV_results(self.bpr.name, pv_code)
            if os.path.exists(pv_path):
                available_panels.append(pv_code)
            else:
                missing_panels.append(pv_code)

        if missing_panels:
            missing_list = ', '.join(missing_panels)
            error_msg = (
                f"PV electricity results missing for building {self.bpr.name}, panel type(s): {missing_list}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
            )
            print(f"ERROR: {error_msg}")
            raise FileNotFoundError(error_msg)

        # Get GRID electricity demand from demand file
        if 'GRID_kWh' not in self.demand_timeseries.columns:
            raise ValueError(f"GRID_kWh column not found in demand timeseries for building {self.bpr.name}")

        grid_demand_hourly = self.demand_timeseries['GRID_kWh'].to_numpy(dtype=float)

        # Process each PV panel
        for pv_code in available_panels:
            pv_df = self._load_pv_hourly(pv_code)
            pv_generation_hourly = pv_df['E_PV_gen_kWh'].to_numpy(dtype=float)
            offset_hourly = np.minimum(pv_generation_hourly, grid_demand_hourly)
            export_hourly = pv_generation_hourly - offset_hourly

            # Convert to emissions (both negative = emission reductions)
            offset_emissions = -offset_hourly * self.grid_intensity
            export_emissions = -export_hourly * self.grid_intensity

            # Add columns to timeline
            self.operational_emission_timeline[f'PV_{pv_code}_GRID_offset_kgCO2e'] = offset_emissions
            self.operational_emission_timeline[f'PV_{pv_code}_GRID_export_kgCO2e'] = export_emissions

            # Log summary for this panel
            total_offset = offset_hourly.sum()
            total_export = export_hourly.sum()
            total_offset_emissions = offset_emissions.sum()
            total_export_emissions = export_emissions.sum()
            print(f"  PV panel {pv_code}: {total_offset:.0f} kWh offset on-site ({total_offset_emissions:.0f} kgCO2e avoided), "
                  f"{total_export:.0f} kWh exported to grid ({total_export_emissions:.0f} kgCO2e avoided)")

    def calculate_operational_emission(self) -> None:
        """
        This function calculates the emission timeline for heating,
        domestic hot water, cooling and electrical supply.
        
        Behavior with PV scenarios
        --------------------------
        - Base emission columns (per-tech and per-supply) are computed from demand and feedstock intensities and
            are NOT altered by PV.
        - For each logged PV scenario (via `log_pv_contribution`), per-demand PV offset columns  
          `PV_{pv_code}_offset_{demand}_kgCO2e` and a total `PV_{pv_code}_offset_total_kgCO2e` are added to the timeline.  
        - No unsuffixed PV columns are written. 
        """
        for demand_type, supply_type in _tech_name_mapping.items():
            eff: float = self.bpr.supply[f"eff_{supply_type}"]
            eff = eff if eff > 0 else 1.0  # avoid division by zero
            feedstock: str = self.bpr.supply[f"source_{supply_type}"]
            self.operational_emission_timeline[f"{demand_type}_{feedstock}_kgCO2e"] = (
                self.demand_timeseries[f"{demand_type}_kWh"]  # kWh
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
        for demand_type in _tech_name_mapping.keys():
            demand_cols = [
                col for col in self.operational_emission_timeline.columns
                if col.startswith(f"{demand_type}_") and col.endswith("_kgCO2e")
                and col != f"{demand_type}_kgCO2e"
                and "_PV" not in col  # Exclude PV offset columns
            ]
            data[f"{demand_type}_kgCO2e"] = self.operational_emission_timeline[demand_cols].sum(axis=1)
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
            data[f"{feedstock}_kgCO2e"] = self.operational_emission_timeline[feedstock_cols].sum(axis=1)
        return pd.DataFrame(data)

    @property
    def operational_emission_timeline_extended(self) -> pd.DataFrame:
        """
        Get the operational emission timeline extended with total emissions,
        per-demand emissions, and per-feedstock emissions.

        :return: A DataFrame representing the extended operational emission timeline.
        :rtype: pd.DataFrame
        """
        if not self._is_emission_calculated:
            raise RuntimeError("Operational emissions have not been calculated yet. Please call calculate_operational_emission() first.")
        df_extended = self.operational_emission_timeline.copy()
        df_extended = pd.concat(
            [df_extended, self.emission_by_demand, self.emission_by_feedstock],
            axis=1
        )
        return df_extended

    def save_results(self) -> None:
        """
        Save the operational emission results to a CSV file.
        """
        if not os.path.exists(self.locator.get_lca_operational_folder()):
            os.makedirs(self.locator.get_lca_operational_folder())

        # Reset index to convert hour index to a column, then reorder columns
        df_to_save = self.operational_emission_timeline
        # merge df_to_save with emission_by_demand, emission_by_feedstock and reset index
        df_to_save = pd.concat(
            [df_to_save, self.emission_by_demand, self.emission_by_feedstock],
            axis=1
        ).reset_index()
        # Move hour column to the end, and ensure date column is first
        date_cols = ['date'] if 'date' in df_to_save.columns else []
        emission_cols = [col for col in df_to_save.columns if col not in ['hour', 'date']]
        hour_cols = ['hour']
        cols = date_cols + emission_cols + hour_cols
        df_to_save = df_to_save[cols]

        df_to_save.to_csv(
            self.locator.get_lca_operational_hourly_building(self.bpr.name),
            index=False, float_format='%.2f')


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
    test_timeline = OperationalHourlyTimeline(locator, bpr)
    test_timeline.calculate_operational_emission()
    test_timeline.save_results()
