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
    # Always use what-if-name for output folder name (both modes)
    whatif_name = config.final_energy.what_if_name
    if not whatif_name:
        raise ValueError(
            "what-if-name is required. Please set final-energy:what-if-name parameter."
        )

    if config.final_energy.overwrite_supply_settings:
        # What-if mode
        print(f"Mode: What-if scenario '{whatif_name}'")
    else:
        # Production mode
        network_name_value = config.final_energy.network_name
        if network_name_value:
            print(f"Mode: Production (what-if: {whatif_name}, network: {network_name_value})")
        else:
            print(f"Mode: Production (what-if: {whatif_name}, no district networks)")

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

    # Step 3.5: Early validation - check supply.csv matches network connectivity (production mode only)
    if not config.final_energy.overwrite_supply_settings:
        print("\nValidating supply configuration against network connectivity...")
        from cea.analysis.final_energy.calculation import validate_supply_network_consistency
        try:
            validate_supply_network_consistency(
                buildings=buildings,
                network_name=config.final_energy.network_name,
                locator=locator
            )
            print("  ✓ Supply configuration matches network connectivity")
        except ValueError as e:
            print(f"\n❌ Validation failed:\n{e}")
            raise

    # Step 4: Calculate final energy for each building
    print("\nCalculating building final energy...")
    building_dfs = {}
    building_configs = {}

    # Validation will be done after all buildings are processed
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

    # Step 4b: Validate district assembly consistency (what-if mode only)
    if config.final_energy.overwrite_supply_settings and building_configs:
        try:
            from cea.analysis.final_energy.calculation import validate_district_assembly_consistency
            validate_district_assembly_consistency(building_configs)
        except ValueError as e:
            print(f"\n❌ Validation Error: {str(e)}")
            raise

    # Step 5: Calculate for district plants
    plant_dfs = {}
    network_name = config.final_energy.network_name
    if network_name:
        print(f"\nDistrict network: {network_name}")
        print("Calculating district plant final energy...")

        from cea.analysis.final_energy.calculation import calculate_plant_final_energy

        # Determine which network types to process
        network_types = []
        if 'DH' in building_configs and any(
            cfg.get('space_heating') and cfg['space_heating']['scale'] == 'DISTRICT'
            for cfg in building_configs.values()
        ):
            network_types.append('DH')
        if 'DC' in building_configs and any(
            cfg.get('space_cooling') and cfg['space_cooling']['scale'] == 'DISTRICT'
            for cfg in building_configs.values()
        ):
            network_types.append('DC')

        # If no district buildings found, try to detect from network files
        if not network_types:
            # Check if DH network exists
            dh_folder = locator.get_output_thermal_network_type_folder('DH', network_name)
            if os.path.exists(dh_folder):
                network_types.append('DH')

            # Check if DC network exists
            dc_folder = locator.get_output_thermal_network_type_folder('DC', network_name)
            if os.path.exists(dc_folder):
                network_types.append('DC')

        # Calculate for each network type
        for network_type in network_types:
            try:
                # Read metadata to find plant nodes
                network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
                metadata_file = os.path.join(
                    network_folder,
                    f'{network_type}_{network_name}_metadata_nodes.csv'
                )

                if not os.path.exists(metadata_file):
                    print(f"  ✗ {network_type}: Metadata file not found")
                    continue

                metadata_df = pd.read_csv(metadata_file)
                plant_nodes = metadata_df[metadata_df['type'].str.startswith('PLANT')]

                if len(plant_nodes) == 0:
                    print(f"  ✗ {network_type}: No plant nodes found in network")
                    continue

                # Calculate for each plant
                for _, plant_row in plant_nodes.iterrows():
                    plant_name = plant_row['name']
                    try:
                        plant_df = calculate_plant_final_energy(
                            network_name, network_type, plant_name, locator, config
                        )

                        # Save individual plant file
                        output_file = locator.get_final_energy_plant_file(
                            network_name, network_type, plant_name, whatif_name
                        )
                        locator.ensure_parent_folder_exists(output_file)
                        plant_df.to_csv(output_file, index=False, float_format='%.3f')

                        # Store for aggregation
                        plant_key = f"{network_type}_{plant_name}"
                        plant_dfs[plant_key] = plant_df

                        print(f"  ✓ {network_type} plant {plant_name}")

                    except Exception as e:
                        print(f"  ✗ {network_type} plant {plant_name}: {str(e)}")

            except Exception as e:
                print(f"  ✗ {network_type} network: {str(e)}")
    else:
        print("\nNo district network selected (standalone buildings only)")

    # Step 6-7: Generate compilation files
    print("\nGenerating compilation files...")

    summary_df = None
    breakdown_df = None

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

    # Step 8: Print summary statistics
    if building_dfs:
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)

        # Count buildings processed
        total_buildings = len(buildings)
        successful_buildings = len(building_dfs)
        failed_buildings = total_buildings - successful_buildings

        print(f"\nBuildings processed: {successful_buildings}/{total_buildings}")
        if failed_buildings > 0:
            print(f"Failed: {failed_buildings}")

        # Calculate total energy by carrier
        total_final = 0.0
        if summary_df is not None:
            print("\nTotal Final Energy by Carrier:")
            for carrier in ['NATURALGAS', 'OIL', 'COAL', 'WOOD', 'GRID', 'DH', 'DC', 'SOLAR']:
                carrier_col = f'{carrier}_MWh'
                if carrier_col in summary_df.columns:
                    total = summary_df[carrier_col].sum()
                    if total > 0:
                        print(f"  {carrier}: {total:,.2f} MWh/year")

            total_final = summary_df['TOTAL_MWh'].sum()
            print(f"  TOTAL: {total_final:,.2f} MWh/year")

        # Calculate total demand
        total_demand = sum([
            df['Qhs_sys_kWh'].sum() + df['Qww_sys_kWh'].sum() +
            df['Qcs_sys_kWh'].sum() + df['E_sys_kWh'].sum()
            for df in building_dfs.values()
        ]) / 1000.0  # kWh -> MWh

        print(f"\nTotal System Demand: {total_demand:,.2f} MWh/year")

        if summary_df is not None and total_demand > 0 and total_final > 0:
            avg_efficiency = total_demand / total_final
            print(f"Average System Efficiency: {avg_efficiency:.2%}")

        print(f"\nOutput folder: {output_folder}")

    print("\n" + "=" * 80)
    print("FINAL ENERGY CALCULATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main(cea.config.Configuration())
