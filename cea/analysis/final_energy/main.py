"""
Final Energy Calculation - Main Entry Point

This module calculates final energy consumption (energy by carrier) for buildings and district plants.
Outputs hourly timeseries and annual summaries organized by what-if scenario.

Based on IMPLEMENTATION_PLAN.md and BACKEND_PLAN.md
"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


import os
import pandas as pd
from typing import Optional

import cea.config
import cea.inputlocator


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
    try:
        import geopandas as gpd
        zone_gdf = gpd.read_file(locator.get_zone_geometry())
        buildings = zone_gdf['name'].tolist()
    except Exception:
        # Fallback: try reading from demand results folder
        import glob
        demand_folder = locator.get_demand_results_folder()
        demand_files = glob.glob(os.path.join(demand_folder, '*.csv'))
        buildings = [os.path.splitext(os.path.basename(f))[0] for f in demand_files]

    print(f"Processing {len(buildings)} buildings")

    # Step 4: Calculate final energy for each building
    print("\nCalculating building final energy...")
    building_dfs = {}
    building_configs = {}

    for building in buildings:
        try:
            from cea.analysis.final_energy.calculation import (
                calculate_building_final_energy,
                load_supply_configuration
            )

            # Load supply configuration
            supply_config = load_supply_configuration(building, locator, config)
            building_configs[building] = supply_config

            # Calculate final energy for this building
            final_energy_df = calculate_building_final_energy(building, locator, config)

            # Save individual building file
            output_file = locator.get_final_energy_building_file(building, whatif_name)
            locator.ensure_parent_folder_exists(output_file)
            final_energy_df.to_csv(output_file, index=False, float_format='%.3f')

            # Store for aggregation
            building_dfs[building] = final_energy_df

            print(f"  ✓ {building}")

        except Exception as e:
            print(f"  ✗ {building}: {str(e)}")

    # Step 5: Calculate for district plants (placeholder)
    plant_dfs = {}
    network_name = config.final_energy.network_name
    if network_name:
        print(f"\nDistrict network: {network_name}")
        print("  - District plant calculations: Not yet implemented")
        # TODO: Implement calculate_plant_final_energy()
    else:
        print("\nNo district network selected (standalone buildings only)")

    # Step 6-7: Generate compilation files
    print("\nGenerating compilation files...")

    if building_dfs:
        from cea.analysis.final_energy.calculation import (
            aggregate_buildings_summary,
            create_final_energy_breakdown
        )
        import json
        from datetime import datetime

        try:
            # Generate buildings summary
            summary_df = aggregate_buildings_summary(building_dfs, plant_dfs, locator)
            summary_file = locator.get_final_energy_buildings_file(whatif_name)
            locator.ensure_parent_folder_exists(summary_file)
            summary_df.to_csv(summary_file, index=False, float_format='%.3f')
            print(f"  ✓ final_energy_buildings.csv ({len(summary_df)} rows)")

        except Exception as e:
            print(f"  ✗ final_energy_buildings.csv: {str(e)}")

        try:
            # Generate detailed breakdown
            breakdown_df = create_final_energy_breakdown(
                building_dfs, plant_dfs, building_configs, locator, config
            )
            breakdown_file = locator.get_final_energy_file(whatif_name)
            locator.ensure_parent_folder_exists(breakdown_file)
            breakdown_df.to_csv(breakdown_file, index=False, float_format='%.3f')
            print(f"  ✓ final_energy.csv ({len(breakdown_df)} rows)")

        except Exception as e:
            print(f"  ✗ final_energy.csv: {str(e)}")

        try:
            # Generate supply configuration JSON
            config_data = {
                'metadata': {
                    'whatif_name': whatif_name,
                    'mode': 'whatif' if config.final_energy.overwrite_supply_settings else 'production',
                    'timestamp': datetime.now().isoformat(),
                    'network_name': config.final_energy.network_name,
                },
                'buildings': building_configs
            }

            config_file = locator.get_final_energy_supply_configuration_file(whatif_name)
            locator.ensure_parent_folder_exists(config_file)
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            print(f"  ✓ supply_configuration.json")

        except Exception as e:
            print(f"  ✗ supply_configuration.json: {str(e)}")
    else:
        print("  - No buildings processed, skipping compilation files")

    print("\n" + "=" * 80)
    print("FINAL ENERGY CALCULATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main(cea.config.Configuration())
