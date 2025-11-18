from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.database.components import Feedstocks, Conversion
from cea.demand.building_properties import BuildingProperties
from cea.utilities import epwreader

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import (
        BuildingPropertiesRow,
    )
    from cea.inputlocator import InputLocator

_tech_name_mapping = {
    # tech_name: (<demand_col_name>, <supply_type_name>)
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
        self.conversion_db = Conversion.from_locator(locator)
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
        offset_building: bool = True,
        allowed_components: list[str] | None = None,
        credit_export: bool = True,
    ) -> None:
        """
        Calculate PV emission offsets for GRID electricity components and grid export.

        PV is allocated to building GRID components in the order specified by allowed_components.
        Emission offsets are calculated per component and for grid export.

        :param pv_codes: List of PV panel codes to process
        :type pv_codes: list[str]
        :param offset_building: If True, PV offsets building GRID demand before being exported.
            If False, all PV is treated as export to grid (no building offset).
        :type offset_building: bool
        :param allowed_components: Ordered list of GRID components that PV can offset.
            Valid values: ['GRID_a', 'GRID_l', 'GRID_v', 'GRID_ve', 'GRID_data', 'GRID_pro',
                           'GRID_aux', 'GRID_cdata', 'GRID_cre', 'GRID_hs', 'GRID_cs', 'GRID_ww']
            The ORDER determines allocation priority. PV offsets the first component fully before
            moving to the second, and so on.
            Only used when offset_building=True. If None or empty when offset_building=True,
            all GRID components will be used in default order.
        :type allowed_components: list[str] | None
        :param credit_export: If True, surplus PV exported to grid is credited as avoided emissions.
            If False, export offset is zero (conservative approach).
        :type credit_export: bool

        Notes
        -----
        - All emission offsets are negative by convention (emissions avoided)
        - Components are only offset if they exist in the demand file and have non-zero demand
        - Per-component offsets are stored in PV_{code}_offset_{component}_kgCO2e columns
        - Grid export offset is stored in PV_{code}_offset_grid_export_kgCO2e column
        - Total offset is sum of all per-component and export offsets

        Examples
        --------
        >>> # Offset lighting first, then appliances, export surplus
        >>> hourly_timeline.log_pv_contribution(
        ...     pv_codes=['PV1'],
        ...     offset_building=True,
        ...     allowed_components=['GRID_l', 'GRID_a'],
        ...     credit_export=True
        ... )

        >>> # Export all PV to grid without offsetting building
        >>> hourly_timeline.log_pv_contribution(
        ...     pv_codes=['PV1'],
        ...     offset_building=False,
        ...     credit_export=True
        ... )

        >>> # Offset building with all components, don't credit export (conservative)
        >>> hourly_timeline.log_pv_contribution(
        ...     pv_codes=['PV1'],
        ...     offset_building=True,
        ...     allowed_components=None,
        ...     credit_export=False
        ... )
        """
        if len(pv_codes) == 0:
            raise ValueError("pv_codes must contain at least one PV panel code.")

        # Validate and prepare allowed components (preserves order)
        # Note: CEA's MultiChoiceParameter returns ALL choices when parameter is empty
        # So allowed_components will be a full list when user leaves pv-offset-allowance empty
        if not offset_building:
            # If not offsetting building, set ordered_components to empty
            ordered_components = []
        elif allowed_components is None:
            # If offset_building=True and allowed_components=None, use all components in default order
            ordered_components = list(_GRID_COMPONENTS)
        else:
            # Keep only valid components, preserving user-specified order
            ordered_components = [c for c in allowed_components if c in _GRID_COMPONENTS]

            # Warn about invalid components
            invalid = set(allowed_components) - set(_GRID_COMPONENTS)
            if invalid:
                warnings.warn(
                    f"Invalid GRID components in pv-offset-allowance will be ignored: {invalid}. "
                    f"Valid components are: {_GRID_COMPONENTS}",
                    RuntimeWarning
                )

        for pv_code in pv_codes:
            pv_hourly = self._load_pv_hourly(pv_code)
            pv_gen = pv_hourly['E_PV_gen_kWh'].to_numpy(dtype=float)
            pv_remaining = pv_gen.copy()  # Track remaining PV for sequential allocation

            grid_intensity = self.grid_intensity  # kgCO2e/kWh

            # Initialize per-component emission offsets (all 12 components)
            component_offsets = {comp: np.zeros(HOURS_IN_YEAR) for comp in _GRID_COMPONENTS}

            # Add PV columns to operational_emission_timeline if they don't exist yet
            # This ensures columns are only created when consider-pv-contributions is True
            pv_columns_to_add = []
            for comp in _GRID_COMPONENTS:
                col_name = f'PV_{pv_code}_offset_{comp}_kgCO2e'
                if col_name not in self.operational_emission_timeline.columns:
                    pv_columns_to_add.append(col_name)

            for col_name in [f'PV_{pv_code}_offset_grid_export_kgCO2e', f'PV_{pv_code}_offset_total_kgCO2e']:
                if col_name not in self.operational_emission_timeline.columns:
                    pv_columns_to_add.append(col_name)

            # Add demand-type summary columns
            for demand_type in ['E_sys', 'Qww_sys', 'Qhs_sys', 'Qcs_sys']:
                col_name = f'{demand_type}_{pv_code}_offset_kgCO2e'
                if col_name not in self.operational_emission_timeline.columns:
                    pv_columns_to_add.append(col_name)

            # Add all new PV columns at once (more efficient than one by one)
            if pv_columns_to_add:
                for col in pv_columns_to_add:
                    self.operational_emission_timeline[col] = 0.0

            # Allocate PV to components in user-specified priority order
            for comp in ordered_components:
                comp_col = f'{comp}_kWh'

                # Skip if component doesn't exist in demand file
                if comp_col not in self.demand_timeseries.columns:
                    continue

                comp_demand = self.demand_timeseries[comp_col].to_numpy(dtype=float)

                # Allocate as much PV as possible to this component
                pv_to_comp = np.minimum(pv_remaining, comp_demand)

                # Calculate emission offset for this component (negative = avoided emissions)
                component_offsets[comp] = -pv_to_comp * grid_intensity

                # Reduce remaining PV
                pv_remaining -= pv_to_comp

            # Remaining PV is exported to grid
            pv_to_grid_export = pv_remaining

            # Calculate grid export offset
            if credit_export:
                offset_grid_export_kgCO2e = -pv_to_grid_export * grid_intensity
            else:
                offset_grid_export_kgCO2e = np.zeros_like(pv_to_grid_export)

                # Log uncredited surplus per-hour
                if pv_to_grid_export.sum() > 0:
                    total_uncredited_kwh = pv_to_grid_export.sum()
                    total_uncredited_kgCO2e = (pv_to_grid_export * grid_intensity).sum()
                    warnings.warn(
                        f"PV panel {pv_code} in building {self.bpr.name}: "
                        f"pv-credit-grid-export is False. "
                        f"Total yearly uncredited export: {total_uncredited_kwh:.2f} kWh "
                        f"({total_uncredited_kgCO2e:.2f} kgCO2e potential offset not counted). "
                        f"Per-hour export logged in PV_{pv_code}_offset_grid_export_kgCO2e (all zeros).",
                        RuntimeWarning
                    )

            # Calculate total offset (sum of all component offsets + export offset)
            offset_total_kgCO2e = sum(component_offsets.values()) + offset_grid_export_kgCO2e

            # Store in operational_emission_timeline
            # Per-component offsets
            for comp in _GRID_COMPONENTS:
                self.operational_emission_timeline[f'PV_{pv_code}_offset_{comp}_kgCO2e'] = component_offsets[comp]

            # Summary offsets
            self.operational_emission_timeline[f'PV_{pv_code}_offset_grid_export_kgCO2e'] = offset_grid_export_kgCO2e
            self.operational_emission_timeline[f'PV_{pv_code}_offset_total_kgCO2e'] = offset_total_kgCO2e

            # Demand-type summary offsets (aggregated by end-use category)
            # E_sys: Pure electrical loads (7 components)
            e_sys_components = ['GRID_a', 'GRID_l', 'GRID_v', 'GRID_ve',
                                'GRID_data', 'GRID_pro', 'GRID_aux']
            self.operational_emission_timeline[f'E_sys_{pv_code}_offset_kgCO2e'] = sum(
                component_offsets[comp] for comp in e_sys_components
            )

            # Qww_sys: Hot water (1 component)
            self.operational_emission_timeline[f'Qww_sys_{pv_code}_offset_kgCO2e'] = \
                component_offsets['GRID_ww']

            # Qhs_sys: Space heating (1 component)
            self.operational_emission_timeline[f'Qhs_sys_{pv_code}_offset_kgCO2e'] = \
                component_offsets['GRID_hs']

            # Qcs_sys: Cooling (3 components)
            qcs_components = ['GRID_cs', 'GRID_cdata', 'GRID_cre']
            self.operational_emission_timeline[f'Qcs_sys_{pv_code}_offset_kgCO2e'] = sum(
                component_offsets[comp] for comp in qcs_components
            )

            # Store detailed allocation for internal tracking (power in kWh for validation/debugging)
            # This is NOT saved to output CSV, only kept in memory
            pv_allocations_kwh = {}
            for comp in _GRID_COMPONENTS:
                # Reverse-calculate kWh from emission offset
                # offset = -kwh * intensity, so kwh = -offset / intensity
                # Handle zero intensity to avoid division by zero
                pv_allocations_kwh[f'E_PV_to_{comp}_kWh'] = np.where(
                    grid_intensity != 0,
                    -component_offsets[comp] / grid_intensity,
                    0.0
                )

            self._pv_allocation[pv_code] = pd.DataFrame({
                'E_PV_gen_kWh': pv_gen,
                'E_PV_to_building_kWh': sum(pv_allocations_kwh.values()),
                'E_PV_to_grid_kWh': pv_to_grid_export,
                **pv_allocations_kwh,
            }, index=self.demand_timeseries.index)

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

        pv_by_type = net_energy_annual['PV_by_type']
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

        # Get total GRID demand hourly
        grid_intensity = self.emission_intensity_timeline["GRID"].to_numpy(dtype=float)
        grid_demand_hourly = np.zeros(HOURS_IN_YEAR)
        for comp in _GRID_COMPONENTS:
            col_name = f'{comp}_kgCO2e'
            if col_name in self.operational_emission_timeline.columns:
                # Convert emissions back to kWh using grid intensity
                grid_demand_hourly += self.operational_emission_timeline[col_name].to_numpy(dtype=float) / grid_intensity

        # Track remaining grid demand for sequential allocation
        remaining_grid_demand = grid_demand_hourly.copy()

        # Process each PV panel
        for pv_code in available_panels:
            pv_df = self._load_pv_hourly(pv_code)
            pv_generation_hourly = pv_df['E_PV_gen_kWh'].to_numpy(dtype=float)

            # Calculate offset (on-site use) and export for this panel
            # Offset = min(PV generation, remaining grid demand)
            # Export = PV generation - offset
            offset_hourly = np.minimum(pv_generation_hourly, remaining_grid_demand)
            export_hourly = pv_generation_hourly - offset_hourly

            # Update remaining grid demand
            remaining_grid_demand -= offset_hourly

            # Convert to emissions (both negative = emission reductions)
            offset_emissions = -offset_hourly * grid_intensity
            export_emissions = -export_hourly * grid_intensity

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
    test_timeline = OperationalHourlyTimeline(locator, bpr)
    test_timeline.calculate_operational_emission()
    test_timeline.save_results()
