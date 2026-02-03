"""
Final Energy Calculation - Main Entry Point

This module calculates final energy consumption (energy by carrier) for buildings and district plants.
Outputs hourly timeseries and annual summaries organized by what-if scenario.

Based on IMPLEMENTATION_PLAN.md and BACKEND_PLAN.md
"""

import os
import pandas as pd
from typing import Optional

import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe


def main(config: cea.config.Configuration):
    """
    Main entry point for final-energy script.

    Steps:
    1. Determine mode (production vs what-if)
    2. Get whatif_name from config
    3. Get list of buildings from zone.shp
    4. Calculate final energy for each building
    5. If network selected, calculate for district plants
    6. Save individual hourly files
    7. Generate compilation files
    8. Print summary statistics
    """
    print("=" * 80)
    print("FINAL ENERGY CALCULATION")
    print("=" * 80)

    locator = cea.inputlocator.InputLocator(config.scenario)

    # Step 1: Determine mode and whatif_name
    if config.final_energy.overwrite_supply_settings:
        # What-if mode
        whatif_name = config.final_energy.what_if_name
        if not whatif_name:
            raise ValueError(
                "What-if mode enabled (overwrite-supply-settings=True) but no what-if-name specified. "
                "Please set final-energy:what-if-name parameter."
            )
        print(f"Mode: What-if scenario '{whatif_name}'")
    else:
        # Production mode
        whatif_name = "baseline"
        print(f"Mode: Production (baseline)")

    # Step 2: Create output folder
    output_folder = locator.get_final_energy_folder(whatif_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Step 3: Get list of buildings
    zone_df = dbf_to_dataframe(locator.get_zone_geometry())
    buildings = zone_df['Name'].tolist()
    print(f"Processing {len(buildings)} buildings")

    # Step 4: Calculate final energy for each building (placeholder)
    print("\nCalculating building final energy...")
    for building in buildings:
        print(f"  - {building}: Not yet implemented")
        # TODO: Implement calculate_building_final_energy()

    # Step 5: Calculate for district plants (placeholder)
    network_name = config.final_energy.network_name
    if network_name:
        print(f"\nDistrict network: {network_name}")
        print("  - District plant calculations: Not yet implemented")
        # TODO: Implement calculate_plant_final_energy()
    else:
        print("\nNo district network selected (standalone buildings only)")

    # Step 6-7: Generate compilation files (placeholder)
    print("\nGenerating compilation files...")
    print("  - final_energy_buildings.csv: Not yet implemented")
    print("  - final_energy.csv: Not yet implemented")
    print("  - supply_configuration.json: Not yet implemented")

    print("\n" + "=" * 80)
    print("FINAL ENERGY CALCULATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main(cea.config.Configuration())
