"""
Primary Energy Calculation Tool

Calculates primary energy consumption for buildings in a scenario using
Primary Energy Factors (PEF) with optional PV offsetting.

Part of Life Cycle Analysis family.
"""

import os
import pandas as pd
from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from cea.analysis.lca.primary_energy_calculator import (
    calculate_primary_energy,
    calculate_normalized_metrics,
    calculate_hourly_primary_energy
)


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def main(config):
    """
    Calculate primary energy for all buildings in scenario.

    Parameters
    ----------
    config : Configuration
        CEA configuration with primary-energy section

    Outputs
    -------
    Creates CSV files:
    - {scenario}/outputs/data/primary-energy/Total_annual_primary_energy.csv
    """
    locator = InputLocator(config.scenario)

    # Get list of buildings
    building_names = config.primary_energy.buildings
    if not building_names:
        # Use all buildings in zone
        zone_df = get_building_names_from_zone(locator)
        building_names = zone_df['Name'].tolist()

    # Check PV requirements BEFORE processing any buildings
    include_pv = config.primary_energy.include_pv
    if include_pv:
        pv_codes_param = config.primary_energy.pv_codes
        # Handle both string (CLI) and list (GUI) input
        if isinstance(pv_codes_param, list):
            pv_codes = pv_codes_param if pv_codes_param else None
        elif isinstance(pv_codes_param, str):
            pv_codes = [code.strip() for code in pv_codes_param.split(',')] if pv_codes_param else None
        else:
            pv_codes = None

        if pv_codes and building_names:
            # Check if PV files exist for the first building
            first_building = building_names[0]
            missing_panels = []
            for pv_code in pv_codes:
                pv_path = locator.PV_results(first_building, pv_code)
                if not os.path.exists(pv_path):
                    missing_panels.append(pv_code)

            if missing_panels:
                missing_list = ', '.join(missing_panels)
                error_msg = (
                    f"PV electricity results missing for panel type(s): {missing_list}. "
                    f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
                )
                print(f"ERROR: {error_msg}")
                raise FileNotFoundError(error_msg)

    # Ensure output folders exist BEFORE processing buildings
    output_folder = locator.get_primary_energy_folder()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    hourly_folder = locator.get_primary_energy_hourly_folder()
    if not os.path.exists(hourly_folder):
        os.makedirs(hourly_folder)

    print(f"Calculating primary energy for {len(building_names)} buildings...")

    # Calculate primary energy for each building
    annual_results = []
    district_hourly_results = []

    for i, building in enumerate(building_names, 1):
        print(f"  [{i}/{len(building_names)}] {building}")
        try:
            # Annual totals
            building_result = calculate_primary_energy(locator, building, config)
            building_result_normalized = calculate_normalized_metrics(building_result)
            annual_results.append(building_result_normalized)

            # Hourly timeseries (GRID + PV only)
            hourly_result = calculate_hourly_primary_energy(locator, building, config)

            # Round numeric columns to 2 decimals
            numeric_columns = hourly_result.select_dtypes(include=['float64', 'int64']).columns
            hourly_result[numeric_columns] = hourly_result[numeric_columns].round(2)

            # Save per-building hourly file
            building_hourly_path = locator.get_primary_energy_hourly_building(building)
            hourly_result.to_csv(building_hourly_path, index=False)
            print(f"    Saved: {building_hourly_path}")

            # Add building name for district aggregation
            hourly_result_with_name = hourly_result.copy()
            hourly_result_with_name.insert(0, 'Name', building)
            district_hourly_results.append(hourly_result_with_name)

        except Exception as e:
            print(f"    WARNING: Failed to calculate primary energy for {building}: {e}")
            continue

    if not annual_results:
        print("ERROR: No buildings successfully calculated")
        return

    # === Save Annual Results ===
    annual_df = pd.DataFrame(annual_results)

    # Round all numeric columns to 2 decimals
    numeric_columns = annual_df.select_dtypes(include=['float64', 'int64']).columns
    annual_df[numeric_columns] = annual_df[numeric_columns].round(2)

    # Write annual results
    annual_output_path = locator.get_primary_energy_annual()
    annual_df.to_csv(annual_output_path, index=False)

    print(f"\nAnnual results saved to: {annual_output_path}")
    print(f"Total buildings: {len(annual_df)}")

    # === Save District-Level Hourly Results ===
    if district_hourly_results:
        # Sum across all buildings for each hour
        # Remove 'Name' column from each building's data before summing
        hourly_data_without_name = [df.drop(columns=['Name']) for df in district_hourly_results]

        # Sum all buildings hour by hour
        district_hourly_df = hourly_data_without_name[0].copy()
        for df in hourly_data_without_name[1:]:
            # Sum all numeric columns
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            district_hourly_df[numeric_cols] = district_hourly_df[numeric_cols] + df[numeric_cols]

        # Round to 2 decimals
        numeric_cols = district_hourly_df.select_dtypes(include=['float64', 'int64']).columns
        district_hourly_df[numeric_cols] = district_hourly_df[numeric_cols].round(2)

        # Write district hourly results
        district_hourly_path = locator.get_primary_energy_hourly_district()
        district_hourly_df.to_csv(district_hourly_path, index=False)

        print("\nHourly results:")
        print(f"  Per-building files: {len(district_hourly_results)} buildings")
        print(f"  District aggregation (8760 hours): {district_hourly_path}")

    # Print summary
    print("\n=== Primary Energy Summary ===")

    # Sum base PE carriers (exclude NetGRID variations)
    base_pe_cols = [col for col in annual_df.columns
                    if col.startswith('PE_') and col.endswith('_MJyr')
                    and 'NetGRID' not in col]
    if base_pe_cols:
        print(f"Total PE (all carriers): {annual_df[base_pe_cols].sum().sum() / 1000:.0f} GJ/yr")

    if config.primary_energy.include_pv:
        # Find all NetGRID columns
        netgrid_cols = [col for col in annual_df.columns if col.startswith('PE_NetGRID_') and col.endswith('_MJyr')]
        for col in netgrid_cols:
            pv_code = col.replace('PE_NetGRID_', '').replace('_MJyr', '')
            pv_gen_col = f'PV_{pv_code}_generation_MJyr'
            print(f"Total PE NetGRID ({pv_code}): {annual_df[col].sum() / 1000:.0f} GJ/yr")
            if pv_gen_col in annual_df.columns:
                print(f"Total PV generation ({pv_code}): {annual_df[pv_gen_col].sum() / 1000:.0f} GJ/yr")


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
        Zone geometry with 'Name' column
    """
    import geopandas as gpd

    zone_path = locator.get_zone_geometry()
    crs = get_geographic_coordinate_system()
    zone_df = gpd.read_file(zone_path).to_crs(crs)

    return zone_df


if __name__ == '__main__':
    config = Configuration()
    main(config)
