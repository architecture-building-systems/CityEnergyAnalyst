"""
Entry point for the simplified thermal network simulation.
"""

import cea.config
import cea.inputlocator
from cea.technologies.thermal_network.common.run_loop import (
    validate_and_resolve_mode,
    validate_network_name,
    run_network_types_loop,
)


def main(config: cea.config.Configuration):
    """
    Entry point for Part 2a (single-phase). Each selected network-name
    is run as an independent single-phase simulation.

    Part 2b (multi-phase) has its own entry point in
    ``main_multi_phase.py`` that delegates back here with
    ``multi_phase=True``; the two scripts share ``_run``.
    """
    return _run(config, multi_phase=False)


def _run(config: cea.config.Configuration, *, multi_phase: bool):
    """
    Shared simplified-model runner. Dispatches to the multi-phase
    pipeline or the single-phase network_types loop based on the
    caller's explicit intent (``multi_phase``), not on ambient config
    state.
    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_name, network_names = validate_and_resolve_mode(
        config, locator, multi_phase=multi_phase,
    )

    if network_names is not None:  # multi-phase (Part 2b)
        from cea.technologies.thermal_network.common.phasing import run_multi_phase
        return run_multi_phase(config, locator, network_names, model_type='simplified')

    validate_network_name(locator, network_name)

    def run_simplified(locator, config, network_type, network_name):
        from cea.technologies.thermal_network.simplified.model import thermal_network_simplified

        connectivity_data = locator.read_network_connectivity(network_name)
        per_building_services = None

        if connectivity_data and network_type in connectivity_data.get('networks', {}):
            network_data = connectivity_data['networks'][network_type]
            per_building_services_dict = network_data.get('per_building_services', {})

            if per_building_services_dict:
                per_building_services = {
                    building: set(services)
                    for building, services in per_building_services_dict.items()
                }
                print("  Per-building service configuration loaded from connectivity file")

        thermal_network_simplified(locator, config, network_type, network_name,
                                   per_building_services=per_building_services)

    for network in network_name:
        run_network_types_loop(config, locator, network, run_simplified, "Simplified")


if __name__ == '__main__':
    main(cea.config.Configuration())
