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
from cea.analysis.lca.primary_energy_calculator import calculate_primary_energy, calculate_normalized_metrics


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

    print(f"Calculating primary energy for {len(building_names)} buildings...")

    # Calculate primary energy for each building
    results = []
    for i, building in enumerate(building_names, 1):
        print(f"  [{i}/{len(building_names)}] {building}")
        try:
            building_result = calculate_primary_energy(locator, building, config)
            building_result_normalized = calculate_normalized_metrics(building_result)
            results.append(building_result_normalized)
        except Exception as e:
            print(f"    WARNING: Failed to calculate primary energy for {building}: {e}")
            continue

    if not results:
        print("ERROR: No buildings successfully calculated")
        return

    # Combine results into DataFrame
    results_df = pd.DataFrame(results)

    # Ensure output folder exists
    output_folder = locator.get_primary_energy_folder()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Write annual results
    output_path = locator.get_primary_energy_annual()
    results_df.to_csv(output_path, index=False)

    print(f"\nResults saved to: {output_path}")
    print(f"Total buildings: {len(results_df)}")

    # Print summary
    print("\n=== Primary Energy Summary ===")
    print(f"Total PE (all carriers): {results_df[[col for col in results_df.columns if col.startswith('PE_') and col.endswith('_MJyr')]].sum().sum() / 1000:.0f} GJ/yr")
    print(f"Total PE NetGRID: {results_df['PE_NetGRID_MJyr'].sum() / 1000:.0f} GJ/yr")

    if config.primary_energy.include_pv:
        print(f"Total PV generation: {results_df['PV_generation_MJyr'].sum() / 1000:.0f} GJ/yr")


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
