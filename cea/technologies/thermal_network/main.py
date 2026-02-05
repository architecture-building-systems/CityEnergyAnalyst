"""
Main entry point for thermal network simulation.

This module provides the main() function that orchestrates both simplified and detailed
thermal network solvers based on configuration.
"""

import os
import json
import cea.config
import cea.inputlocator


def main(config: cea.config.Configuration):
    """
    Run thermal network Part 2: Flow & Sizing

    Supports both single-phase and multi-phase modes based on configuration.
    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # MODE DETECTION & VALIDATION
    network_names = config.thermal_network.network_name  # List (NetworkLayoutMultiChoiceParameter)
    multi_phase_mode = config.thermal_network_phasing.multi_phase_mode  # Boolean

    num_networks = len(network_names)

    # Validate configuration and determine mode
    if num_networks == 0:
        # Get available network layouts to provide helpful error message
        try:
            network_folder = locator.get_thermal_network_folder()
            available_layouts = [name for name in os.listdir(network_folder)
                                if os.path.isdir(os.path.join(network_folder, name))
                                and name not in {'DH', 'DC'}]
            if available_layouts:
                raise ValueError(
                    f"Network name is required. Please select a network layout.\n"
                    f"Available layouts: {', '.join(available_layouts)}"
                )
            else:
                raise ValueError(
                    "Network name is required, but no network layouts found.\n"
                    "Please create or import a network layout using 'network-layout' script."
                )
        except FileNotFoundError:
            raise ValueError("Network name is required. Please select a network layout.")

    elif num_networks == 1 and not multi_phase_mode:
        # SINGLE-PHASE MODE
        print("\n" + "="*80)
        print("SINGLE-PHASE THERMAL NETWORK SIMULATION")
        print("="*80)
        # Continue with existing single-phase logic below
        network_name = network_names[0]

    elif num_networks > 1 and not multi_phase_mode:
        # ERROR: Multiple networks but multi-phase disabled
        raise ValueError(
            f"Multiple networks selected ({num_networks}) but multi-phase-mode is False.\n"
            f"Resolution: Set thermal-network-phasing:multi-phase-mode = true\n"
            f"           or select only ONE network for single-phase simulation."
        )

    elif num_networks == 1 and multi_phase_mode:
        # ERROR: Single network but multi-phase enabled
        raise ValueError(
            "Multi-phase mode enabled but only 1 network selected.\n"
            "Resolution: Select MULTIPLE networks (e.g., phase1, phase2, phase3)\n"
            "           or set thermal-network-phasing:multi-phase-mode = false"
        )

    elif num_networks > 1 and multi_phase_mode:
        # MULTI-PHASE MODE - Delegate to phasing module
        print("\n" + "="*80)
        print("MULTI-PHASE THERMAL NETWORK SIMULATION")
        print("="*80)
        from cea.technologies.thermal_network.common.phasing import run_multi_phase
        return run_multi_phase(config, locator, network_names)

    # Continue with existing single-phase logic
    network_model = config.thermal_network.network_model

    # Legacy compatibility check
    if not network_name:
        # Get available network layouts to provide helpful error message
        try:
            network_folder = locator.get_thermal_network_folder()
            available_layouts = [name for name in os.listdir(network_folder)
                                if os.path.isdir(os.path.join(network_folder, name))
                                and name not in {'DH', 'DC'}]
            if available_layouts:
                raise ValueError(
                    f"Network name is required. Please select a network layout.\n"
                    f"Available layouts: {', '.join(available_layouts)}"
                )
            else:
                raise ValueError(
                    "Network name is required, but no network layouts found.\n"
                    "Please create or import a network layout using 'thermal-network-layout'."
                )
        except Exception:
            raise ValueError("Network name is required. Please select a network layout.")

    network_types = config.thermal_network.network_type
    errors = {}
    succeeded = []
    for network_type in network_types:
        print(f"\n{'='*60}")
        print(f"{network_type} Network {network_model} Model")
        print(f"{'='*60}")

        try:
            if network_model == 'simplified':
                from cea.technologies.thermal_network.simplified.model import thermal_network_simplified

                # Read per-building service configuration from network layout metadata
                nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)
                metadata_path = os.path.join(os.path.dirname(nodes_path), 'building_services.json')
                per_building_services = None

                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    # Convert lists back to sets
                    per_building_services = {
                        building: set(services)
                        for building, services in metadata['per_building_services'].items()
                    }

                    print("  Per-building service configuration loaded from metadata")

                thermal_network_simplified(locator, config, network_type, network_name,
                                          per_building_services=per_building_services)
            elif network_model == 'detailed':
                from cea.technologies.thermal_network.detailed.model import (
                    check_heating_cooling_demand, ThermalNetwork, thermal_network_main
                )

                check_heating_cooling_demand(locator, config)
                # Create a per-network config section with the correct network_type
                # This is a simple namespace object that mimics the config section interface
                class NetworkConfig:
                    def __init__(self, base_config, network_type_override):
                        self.network_type = network_type_override
                        # Copy all other attributes from base config
                        for attr in ['network_names', 'file_type', 'set_diameter',
                                   'load_max_edge_flowrate_from_previous_run', 'start_t', 'stop_t',
                                   'use_representative_week_per_month', 'minimum_mass_flow_iteration_limit',
                                   'minimum_edge_mass_flow', 'diameter_iteration_limit',
                                   'substation_cooling_systems', 'substation_heating_systems',
                                   'temperature_control', 'plant_supply_temperature', 'equivalent_length_factor']:
                            if hasattr(base_config, attr):
                                setattr(self, attr, getattr(base_config, attr))

                per_network_config = NetworkConfig(config.thermal_network, network_type)
                thermal_network = ThermalNetwork(locator, network_name, per_network_config)
                thermal_network_main(locator, thermal_network, processes=config.get_number_of_processes())
            else:
                raise RuntimeError(f"Unknown network model: {network_model}")
            print(f"{network_type} network processing completed.")
            succeeded.append(network_type)
        except (ValueError, FileNotFoundError) as e:
            print(f"An error occurred while processing the {network_type} network")
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
            errors[network_type] = e

    if errors:
        print(f"\n{'='*60}")
        print("Errors occurred during processing:")
        print(f"{'='*60}")
        for network_type, error in errors.items():
            print(f"{network_type} network error\n")
            print(error)
            print(f"{'-'*60}")

        # Build summary message showing what succeeded vs failed
        failed_list = ', '.join(sorted(errors.keys()))
        if succeeded:
            succeeded_list = ', '.join(sorted(succeeded))
            raise ValueError(
                f"Completed: {succeeded_list}. Failed: {failed_list}. See errors above."
            )
        else:
            raise ValueError(
                f"All network types failed to process ({failed_list}). See errors above."
            )

if __name__ == '__main__':
    main(cea.config.Configuration())
