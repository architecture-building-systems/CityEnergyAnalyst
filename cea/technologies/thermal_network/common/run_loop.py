"""
Shared orchestration logic for simplified and detailed thermal network entry points.
"""

import os
import traceback


def validate_and_resolve_mode(config, locator, *, multi_phase, section=None):
    """
    Resolve the run mode from the caller's explicit intent and return
    ``(network_name, network_names)``.

    Returns ``(network_names, None)`` for single-phase mode (Part 2a).
    Returns ``(None, network_names)`` for multi-phase mode (Part 2b).
    Raises ``ValueError`` on invalid configuration.

    :param multi_phase: Required. ``False`` when called from the
        single-phase entry point (Part 2a); each selected network runs
        as its own independent single-phase simulation. ``True`` when
        called from the multi-phase entry point (Part 2b); the selected
        networks are treated as phases of one evolving network, and the
        ``thermal-network-phasing:sizing-strategy`` config is consumed
        by the downstream multi-phase runner. Must be ≥ 2 networks.
    :param section: config section to read ``network-name`` from
        (defaults to ``config.thermal_network``).
    """
    if section is None:
        section = config.thermal_network
    network_names = section.network_name  # List
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

    if not multi_phase:
        # Part 2a — each selected network runs as its own independent
        # single-phase simulation. `thermal-network-phasing:sizing-strategy`
        # is not consulted here; it only governs cross-phase behaviour.
        print("\n" + "=" * 80)
        print("SINGLE-PHASE THERMAL NETWORK SIMULATION")
        print("=" * 80)
        return network_names, None

    # Part 2b — multi-phase requires ≥ 2 networks (one per phase).
    if num_networks == 1:
        raise ValueError(
            "Multi-phase (Part 2b) requires at least 2 network names "
            "(one per phase). You selected only one. Either select more "
            "phases, or run Part 2a (single-phase) instead."
        )

    sizing_strategy = config.thermal_network_phasing.sizing_strategy
    print("\n" + "=" * 80)
    print(f"MULTI-PHASE THERMAL NETWORK SIMULATION (sizing strategy: {sizing_strategy})")
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
