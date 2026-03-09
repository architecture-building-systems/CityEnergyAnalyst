"""
Shared orchestration logic for simplified and detailed thermal network entry points.
"""

import os
import traceback


def validate_and_resolve_mode(config, locator, section=None):
    """
    Validate network count vs multi_phase_mode and return (network_name, network_names).

    Returns (network_name, None) for single-phase mode.
    Returns (None, network_names) for multi-phase mode.
    Raises ValueError on invalid configuration.

    :param section: config section to read network_name from (defaults to config.thermal_network)
    """
    if section is None:
        section = config.thermal_network
    network_names = section.network_name  # List
    multi_phase_mode = config.thermal_network_phasing.multi_phase_mode  # Boolean
    num_networks = len(network_names)

    if num_networks == 0:
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
        print("\n" + "=" * 80)
        print("SINGLE-PHASE THERMAL NETWORK SIMULATION")
        print("=" * 80)
        return network_names[0], None

    elif num_networks > 1 and not multi_phase_mode:
        raise ValueError(
            f"Multiple networks selected ({num_networks}) but multi-phase-mode is False.\n"
            f"Resolution: Set thermal-network-phasing:multi-phase-mode = true\n"
            f"           or select only ONE network for single-phase simulation."
        )

    elif num_networks == 1 and multi_phase_mode:
        raise ValueError(
            "Multi-phase mode enabled but only 1 network selected.\n"
            "Resolution: Select MULTIPLE networks (e.g., phase1, phase2, phase3)\n"
            "           or set thermal-network-phasing:multi-phase-mode = false"
        )

    else:  # num_networks > 1 and multi_phase_mode
        print("\n" + "=" * 80)
        print("MULTI-PHASE THERMAL NETWORK SIMULATION")
        print("=" * 80)
        return None, network_names


def validate_network_name(locator, network_name):
    """
    Legacy compatibility check: raise helpful error if network_name is empty.
    """
    if not network_name:
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


def run_network_types_loop(config, locator, network_name, run_single_network_type, model_label,
                           section=None):
    """
    Iterate over network_type, call run_single_network_type for each,
    accumulate errors, and print a summary.

    :param run_single_network_type: callable(locator, config, network_type, network_name)
    :param model_label: label string for display (e.g. "Simplified" or "Detailed")
    :param section: config section to read network_type from (defaults to config.thermal_network)
    """
    if section is None:
        section = config.thermal_network
    network_types = section.network_type
    errors = {}
    succeeded = []

    for network_type in network_types:
        print(f"\n{'=' * 60}")
        print(f"{network_type} Network {model_label} Model")
        print(f"{'=' * 60}")

        try:
            run_single_network_type(locator, config, network_type, network_name)
            print(f"{network_type} network processing completed.")
            succeeded.append(network_type)
        except (ValueError, FileNotFoundError) as e:
            print(f"An error occurred while processing the {network_type} network")
            traceback.print_exc()
            errors[network_type] = e

    if errors:
        print(f"\n{'=' * 60}")
        print("Errors occurred during processing:")
        print(f"{'=' * 60}")
        for network_type, error in errors.items():
            print(f"{network_type} network error\n")
            print(error)
            print(f"{'-' * 60}")

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
