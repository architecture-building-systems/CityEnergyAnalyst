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
import shutil
import pandas as pd

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

    # Step 2: Create output folder. If the what-if analysis folder already
    # exists, remove it entirely (the frontend confirmation modal has
    # already been accepted by the user at this point).
    analysis_folder = locator.get_analysis_folder(whatif_name)
    if os.path.isdir(analysis_folder):
        print(f"Removing existing analysis folder: {analysis_folder}")
        shutil.rmtree(analysis_folder)
    analysis_folder_is_new = True

    output_folder = locator.get_final_energy_folder(whatif_name)
    os.makedirs(output_folder, exist_ok=True)
    print(f"Created output folder: {output_folder}")

    try:
        _run(config, locator, whatif_name, output_folder, buildings=None)
    except Exception:
        # Always remove the final-energy output folder on failure — it may be partial.
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
            print(f"Removed output folder due to error: {output_folder}")
        # If the analysis folder was newly created this run, remove it entirely.
        if analysis_folder_is_new and os.path.exists(analysis_folder):
            shutil.rmtree(analysis_folder)
            print(f"Removed analysis folder due to error: {analysis_folder}")
        raise


def _group_errors_by_pattern(errors):
    """Group building errors by message pattern, stripping building-specific details.

    Returns dict mapping pattern description → list of building names.
    """
    grouped = {}
    for building, msg in errors.items():
        first_line = msg.split('\n')[0]
        # Extract text before ' for building' as the pattern key
        pattern = first_line.split(' for building')[0] if ' for building' in first_line else first_line
        # Append action hint from second line if present
        lines = msg.split('\n')
        if len(lines) > 1 and lines[1].strip().startswith('Please'):
            pattern += f"\n    {lines[1].strip()}"
        if pattern not in grouped:
            grouped[pattern] = []
        grouped[pattern].append(building)
    return grouped


def _run(config, locator, whatif_name, output_folder, buildings):
    """Inner implementation called by main() so folder cleanup can wrap it cleanly."""

    # Step 3: Get list of buildings
    if buildings is None:
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

    # Step 3.5: Pre-flight configuration validation
    if config.final_energy.overwrite_supply_settings:
        # What-if mode: verify all required assembly params are explicitly set
        print("\nChecking what-if assembly parameters...")
        from cea.analysis.final_energy.supply_validation import validate_whatif_params
        try:
            validate_whatif_params(locator, config)
            print("  All assembly parameters are set.")
        except ValueError as e:
            print(f"\n{e}")
            raise
    else:
        # Production mode: verify supply.csv matches network connectivity
        print("\nChecking supply system configuration...")
        from cea.analysis.final_energy.supply_validation import validate_supply_consistency
        try:
            validate_supply_consistency(locator, config)
            print("  Supply system configuration is consistent.")
        except ValueError as e:
            print(f"\n{e}")
            raise

    # Step 3.6: Validate plant temperature vs network simulation results
    _network_name = config.final_energy.network_name
    if _network_name:
        print("\nChecking plant temperature compatibility...")
        from cea.analysis.final_energy.supply_validation import validate_plant_temperature_vs_network_results
        try:
            validate_plant_temperature_vs_network_results(locator, _network_name, config)
            print("  Plant temperature is compatible with network.")
        except ValueError as e:
            print(f"\n{e}")
            raise

    # Step 3.7: Validate booster configuration (both modes, when network is selected)
    if _network_name:
        print("\nChecking booster configuration...")
        from cea.analysis.final_energy.supply_validation import (
            validate_booster_configuration, validate_booster_temperature_compatibility,
            load_network_connectivity
        )
        try:
            connectivity = load_network_connectivity(locator, _network_name)
            if 'DH' in connectivity.get('networks', {}):
                validate_booster_configuration(
                    connectivity['networks']['DH'], _network_name, locator, config
                )
                validate_booster_temperature_compatibility(
                    connectivity['networks']['DH'], _network_name, locator, config
                )
            print("  Booster configuration is valid.")
        except ValueError as e:
            print(f"\n{e}")
            raise

    # Step 4: Calculate final energy for each building
    print("\nCalculating building final energy...")
    building_dfs = {}
    building_configs = {}

    from cea.analysis.final_energy.calculation import (
        calculate_building_final_energy,
        load_supply_configuration,
        parse_solar_panel_configuration,
    )
    solar_panel_config = parse_solar_panel_configuration(config)
    solar_buildings = set(config.solar_technology.buildings) if config.solar_technology.buildings else set()

    errors = {}
    for building in buildings:
        try:
            # Load supply configuration
            supply_config = load_supply_configuration(building, locator, config)
            # Only attach solar config for buildings in solar-technology:buildings
            if building in solar_buildings:
                supply_config['solar'] = solar_panel_config
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
            errors[building] = str(e)
    
    if errors:
        # Group errors by message pattern (strip building-specific details)
        grouped = _group_errors_by_pattern(errors)
        print(f"\n{len(errors)} buildings failed final energy calculation:")
        for pattern, building_list in grouped.items():
            print(f"\n  {pattern} ({len(building_list)} buildings):")
            print(f"    {', '.join(sorted(building_list))}")
        raise Exception(f"{len(errors)} buildings failed final energy calculation.")

    # Step 4b: Validate district assembly consistency (what-if mode only)
    if config.final_energy.overwrite_supply_settings and building_configs:
        try:
            from cea.analysis.final_energy.calculation import validate_district_assembly_consistency
            validate_district_assembly_consistency(building_configs, locator)
        except ValueError as e:
            print(f"\n❌ Validation Error: {str(e)}")
            raise

    # Step 5: Calculate for district plants
    plant_dfs = {}
    plant_configs = {}
    network_name = config.final_energy.network_name
    if network_name:
        print(f"\nDistrict network: {network_name}")
        print("Calculating district plant final energy...")

        from cea.analysis.final_energy.calculation import (
            calculate_plant_final_energy,
            derive_plant_config,
        )

        # Determine which network types to process
        network_types = []
        if any(
            (cfg.get('space_heating') or {}).get('carrier') == 'DH' or
            (cfg.get('hot_water') or {}).get('carrier') == 'DH'
            for cfg in building_configs.values()
        ):
            network_types.append('DH')
        if any(
            (cfg.get('space_cooling') or {}).get('carrier') == 'DC'
            for cfg in building_configs.values()
        ):
            network_types.append('DC')

        # If no district buildings found, try to detect from network files
        if not network_types:
            dh_folder = locator.get_output_thermal_network_type_folder('DH', network_name)
            if os.path.exists(dh_folder):
                network_types.append('DH')

            dc_folder = locator.get_output_thermal_network_type_folder('DC', network_name)
            if os.path.exists(dc_folder):
                network_types.append('DC')

        # Derive plant configs per network type (same config for all plants of same type)
        plant_configs_by_type = {}
        for network_type in network_types:
            pc = derive_plant_config(building_configs, network_type, locator)
            if pc:
                plant_configs_by_type[network_type] = pc

        # Collect plant results per plant_name (may have both DH and DC columns)
        plant_results_by_name = {}  # plant_name → [df, df, ...]

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

                type_pc = plant_configs_by_type.get(network_type)

                # Calculate for each plant
                for _, plant_row in plant_nodes.iterrows():
                    plant_name = plant_row['name']
                    try:
                        plant_df = calculate_plant_final_energy(
                            network_name, network_type, plant_name, locator, config,
                            plant_config=type_pc
                        )

                        # Collect for merging by plant_name
                        if plant_name not in plant_results_by_name:
                            plant_results_by_name[plant_name] = []
                        plant_results_by_name[plant_name].append(plant_df)

                        # Store for aggregation (keyed by network_type for downstream)
                        plant_key = f"{network_type}_{plant_name}"
                        plant_dfs[plant_key] = plant_df

                        # Register per-plant config keyed by plant_name
                        if type_pc:
                            plant_configs[plant_name] = {**type_pc, 'network_type': network_type}

                        print(f"  ✓ {network_type} plant {plant_name}")

                    except Exception as e:
                        print(f"  ✗ {network_type} plant {plant_name}: {str(e)}")

            except Exception as e:
                print(f"  ✗ {network_type} network: {str(e)}")

        # Save merged plant files (one file per plant_name with DH + DC columns)
        for plant_name, dfs in plant_results_by_name.items():
            if len(dfs) == 1:
                merged_df = dfs[0]
            else:
                # Merge on 'date' column; for non-date columns that overlap, keep both
                merged_df = dfs[0]
                for extra_df in dfs[1:]:
                    # Find new columns (exclude date and columns already present)
                    new_cols = [c for c in extra_df.columns if c not in merged_df.columns]
                    if new_cols:
                        merged_df = pd.concat([merged_df, extra_df[new_cols]], axis=1)

            output_file = locator.get_final_energy_plant_file(
                network_name, '', plant_name, whatif_name
            )
            locator.ensure_parent_folder_exists(output_file)
            merged_df.to_csv(output_file, index=False, float_format='%.3f')
    else:
        print("\nNo district network selected (standalone buildings only)")

    # Step 6-7: Generate compilation files
    print("\nGenerating compilation files...")

    summary_df = None

    if building_dfs:
        from cea.analysis.final_energy.calculation import (
            aggregate_buildings_summary,
            create_hourly_timeseries_aggregation,
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
            # Generate hourly timeseries aggregation (8760 rows)
            timeseries_df = create_hourly_timeseries_aggregation(
                building_dfs, plant_dfs
            )
            timeseries_file = locator.get_final_energy_file(whatif_name)
            locator.ensure_parent_folder_exists(timeseries_file)
            timeseries_df.to_csv(timeseries_file, index=False, float_format='%.3f')
            print(f"  ✓ final_energy.csv ({len(timeseries_df)} rows)")

        except Exception as e:
            print(f"  ✗ final_energy.csv: {str(e)}")

        try:
            # Generate supply configuration file
            config_data = {
                'metadata': {
                    'whatif_name': whatif_name,
                    'mode': 'whatif' if config.final_energy.overwrite_supply_settings else 'production',
                    'timestamp': datetime.now().isoformat(),
                    'network_name': config.final_energy.network_name,
                },
                'buildings': building_configs,
                'plants': plant_configs,
            }

            locator.write_analysis_configuration(whatif_name, config_data)
            print("  ✓ configuration.yml")

        except Exception as e:
            print(f"  ✗ configuration.yml: {str(e)}")
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
        if summary_df is not None:
            print("\nTotal Final Energy by Carrier:")
            total_final = 0.0
            for carrier in ['NATURALGAS', 'OIL', 'COAL', 'WOOD', 'GRID', 'DH', 'DC']:
                carrier_col = f'{carrier}_MWh'
                if carrier_col in summary_df.columns:
                    total = summary_df[carrier_col].sum()
                    if total > 0:
                        print(f"  {carrier}: {total:,.2f} MWh/year")
                        total_final += total
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
