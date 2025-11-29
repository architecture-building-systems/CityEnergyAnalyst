"""
Baseline costs for supply systems - Main entry point.

This module provides the main entry point and orchestration logic for baseline
cost calculations. The detailed cost calculation functions are in supply_costs.py.
"""

import pandas as pd
from cea.inputlocator import InputLocator
import cea.config

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def validate_network_results_exist(locator, network_name, network_type):
    """
    Check if thermal-network results exist for the given network and type.

    :param locator: InputLocator instance
    :param network_name: Name of the network layout
    :param network_type: 'DH' or 'DC'
    :return: tuple of (is_valid: bool, error_message: str or None)
    """
    import os

    # Check for required thermal-network output files
    network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
    layout_folder = os.path.join(network_folder, 'layout')

    # Required files from thermal-network
    nodes_file = os.path.join(layout_folder, 'nodes.shp')
    edges_file = os.path.join(layout_folder, 'edges.shp')

    missing_files = []
    if not os.path.exists(nodes_file):
        missing_files.append(nodes_file)
    if not os.path.exists(edges_file):
        missing_files.append(edges_file)

    if missing_files:
        error_msg = f"Thermal-network results not found for network '{network_name}' ({network_type}).\n\n"
        error_msg += "Missing files:\n"
        for f in missing_files:
            error_msg += f"  - {f}\n"
        error_msg += "\nPlease run 'thermal-network' script (both part 1 and part 2) before running baseline-costs.\n"
        error_msg += "Alternatively, select a different network layout that has been completed."
        return False, error_msg

    return True, None


def merge_network_type_costs(all_results):
    """
    Merge heating and cooling costs for each building.

    :param all_results: dict of {network_type: {building_name: results}}
    :return: dict of {building_name: {network_type: results}}
    """
    merged = {}

    # Get all building names across all network types
    all_buildings = set()
    for network_type, results in all_results.items():
        all_buildings.update(results.keys())

    for building_name in all_buildings:
        merged[building_name] = {}
        for network_type, results in all_results.items():
            if building_name in results:
                merged[building_name][network_type] = results[building_name]

    return merged


def baseline_costs_main(locator, config):
    """
    Calculate baseline costs for heating and/or cooling systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with cost results
    """
    from cea.analysis.costs.supply_costs import (
        calculate_all_buildings_as_standalone,
        calculate_standalone_building_costs,
        calculate_costs_for_network_type
    )

    # Get network types (can be list like ['DH', 'DC'] or single value like 'DH')
    network_types = config.system_costs.network_type
    if isinstance(network_types, str):
        network_types = [network_types]

    # Get network name - can be None/empty to assess all buildings as standalone
    network_name = config.system_costs.network_name

    print(f"\n{'='*70}")
    print("BASELINE COSTS CALCULATION")
    print(f"{'='*70}")

    # Check if user selected "(none)" - assess all buildings as standalone
    if not network_name or network_name == '' or network_name == '(none)':
        print("Mode: STANDALONE ONLY (all buildings assessed as standalone systems)")
        print("District-scale supply systems will be treated as building-scale for cost calculations.")
        print(f"Network types (for supply system selection): {', '.join(network_types)}")

        # Calculate ALL buildings as standalone (ignore district-scale designation)
        all_results = calculate_all_buildings_as_standalone(locator, config, network_types)

        # Format using the same formatter as normal mode
        merged_results = merge_network_type_costs(all_results)
        from cea.analysis.costs.format_simplified import format_output_simplified
        final_results, detailed_results = format_output_simplified(merged_results, locator)

        # Save results
        print(f"\n{'-'*70}")
        print("Saving results...")
        locator.ensure_parent_folder_exists(locator.get_baseline_costs())
        final_results.to_csv(locator.get_baseline_costs(), index=False, float_format='%.2f', na_rep='nan')
        detailed_results.to_csv(locator.get_baseline_costs_detailed(), index=False, float_format='%.2f', na_rep='nan')

        print(f"\n{'='*70}")
        print("COMPLETED (Standalone Mode)")
        print(f"{'='*70}")
        print(f"Summary: {locator.get_baseline_costs()}")
        print(f"Detailed: {locator.get_baseline_costs_detailed()}")
        print(f"\nNote: Standalone-only mode provides simplified cost estimates")
        return

    print(f"Mode: NETWORK + STANDALONE")
    print(f"Network layout: {network_name}")
    print(f"Network types: {', '.join(network_types)}")

    # Validate that thermal-network part 2 has been run for each network type
    print(f"\n{'-'*70}")
    print("Validating thermal-network results...")
    validation_errors = {}
    valid_network_types = []

    for network_type in network_types:
        is_valid, error_msg = validate_network_results_exist(locator, network_name, network_type)
        if is_valid:
            print(f"  ✓ {network_type} network '{network_name}' results found")
            valid_network_types.append(network_type)
        else:
            validation_errors[network_type] = error_msg

    # If no network types passed validation, stop here
    if not valid_network_types:
        print(f"\n{'='*70}")
        print("VALIDATION ERRORS")
        print(f"{'='*70}")
        for network_type, error in validation_errors.items():
            print(f"\n{network_type} network:\n{error}\n")
        raise ValueError(
            f"All network types failed validation ({', '.join(network_types)}). "
            "See errors above."
        )

    # Show validation warnings for failed network types (but continue with valid ones)
    if validation_errors:
        print(f"\n{'-'*70}")
        print("VALIDATION WARNINGS")
        print(f"{'-'*70}")
        for network_type, error in validation_errors.items():
            print(f"\n{network_type} network:\n{error}\n")
        print(f"Continuing with valid network types: {', '.join(valid_network_types)}")

    all_results = {}

    # Calculate standalone building costs ONCE for all services (not per network_type)
    # Standalone buildings should show all their systems regardless of which networks are being analyzed
    print(f"\n{'-'*70}")
    print("Calculating standalone building costs...")
    standalone_results = calculate_standalone_building_costs(locator, config, network_name)

    # Calculate costs for each VALID network type
    calculation_errors = {}
    succeeded = []

    for network_type in valid_network_types:
        print(f"\n{'-'*70}")
        print(f"Calculating {network_type} district network costs...")
        try:
            results = calculate_costs_for_network_type(locator, config, network_type, network_name, standalone_results)
            all_results[network_type] = results
            succeeded.append(network_type)
        except ValueError as e:
            # Check if this is a "no demand" or "no supply system" error
            error_msg = str(e)
            if "None of the components chosen" in error_msg or "T30W" in error_msg or "T10W" in error_msg:
                # Show detailed error if it's an energy carrier mismatch
                if "ERROR: Insufficient capacity" in error_msg:
                    # This is our detailed error message - show it
                    print(error_msg)
                else:
                    # Generic message for simple cases
                    print(f"  ⚠ Skipping {network_type}: No valid supply systems")
                    print(f"    (Expected for scenarios with no {network_type} demand)")
                calculation_errors[network_type] = error_msg
                continue
            else:
                # Re-raise other errors
                raise

    # Check if we got any results
    if not all_results:
        print(f"\n{'='*70}")
        print("CALCULATION ERRORS")
        print(f"{'='*70}")
        for network_type, error in calculation_errors.items():
            print(f"\n{network_type} network:\n{error}\n")
        raise ValueError(
            "No valid supply systems found for any of the selected network types.\n"
            f"Selected network types: {', '.join(network_types)}\n\n"
            "Please check that:\n"
            "1. Buildings have supply systems configured in Building Properties/Supply settings\n"
            "2. The selected network type matches the building demands (DH for heating, DC for cooling)"
        )

    # Merge results from all network types (but don't format yet)
    merged_results = merge_network_type_costs(all_results)

    # Calculate solar panel costs
    print(f"\n{'-'*70}")
    print("Calculating solar panel costs...")
    from cea.analysis.costs.solar_costs import calculate_building_solar_costs, merge_solar_costs_to_buildings

    # Get list of all building names for solar calculation
    all_building_names = []
    for building_name in merged_results.keys():
        if building_name not in ['DC', 'DH']:  # Exclude network-level entries
            all_building_names.append(building_name)

    solar_details, solar_summary = calculate_building_solar_costs(config, locator, all_building_names)

    # Merge and format all results (after solar costs are calculated)
    print(f"\n{'-'*70}")
    print("Merging and formatting results...")
    from cea.analysis.costs.format_simplified import format_output_simplified
    final_results, detailed_results = format_output_simplified(merged_results, locator)

    # Append solar details to costs_components.csv
    if not solar_details.empty:
        detailed_results = pd.concat([detailed_results, solar_details], ignore_index=True)
        print(f"  Added {len(solar_details)} solar panel component rows")

    # Add/update solar costs in costs_buildings.csv
    if not solar_summary.empty:
        final_results = merge_solar_costs_to_buildings(final_results, solar_summary)
        print(f"  Updated costs for {len(solar_summary)} buildings with solar panels")

    # Sort results by building name
    final_results = final_results.sort_values('name').reset_index(drop=True)
    detailed_results = detailed_results.sort_values('name').reset_index(drop=True)

    # Save results
    print(f"\n{'-'*70}")
    print("Saving results...")
    locator.ensure_parent_folder_exists(locator.get_baseline_costs())
    final_results.to_csv(locator.get_baseline_costs(), index=False, float_format='%.2f', na_rep='nan')
    detailed_results.to_csv(locator.get_baseline_costs_detailed(), index=False, float_format='%.2f', na_rep='nan')

    # Show completion status based on success/failure
    all_errors = {**validation_errors, **calculation_errors}
    print(f"\n{'='*70}")
    if all_errors:
        print("PARTIALLY COMPLETED")
    else:
        print("COMPLETED")
    print(f"{'='*70}")
    print(f"Summary: {locator.get_baseline_costs()}")
    print(f"Detailed: {locator.get_baseline_costs_detailed()}")

    # Show summary of what succeeded and what failed (matching thermal-network behavior)
    if all_errors:
        failed_types = ', '.join(sorted(all_errors.keys()))
        succeeded_types = ', '.join(sorted(succeeded))
        print(f"\nCompleted: {succeeded_types}. Failed: {failed_types}.")
    else:
        print(f"\nAll network types completed successfully: {', '.join(sorted(succeeded))}")

    # Check if any networks were found
    has_networks = any(name.startswith('N') for name in final_results['name'])
    if has_networks:
        print("\nNote: Network costs include central plant equipment and piping.")
        print("      Variable energy costs (electricity, fuels) are NOT included.")
        print("  For complete costs including energy consumption, refer to optimisation results.")

    return final_results


def main(config: cea.config.Configuration):
    """
    Main entry point for baseline-costs script.

    :param config: Configuration instance
    """
    locator = InputLocator(config.scenario)
    baseline_costs_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
