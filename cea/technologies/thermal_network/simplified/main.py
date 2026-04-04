"""
Entry point for the simplified thermal network simulation.
"""

import os
import json

import cea.config
import cea.inputlocator
from cea.technologies.thermal_network.common.run_loop import (
    validate_and_resolve_mode,
    validate_network_name,
    run_network_types_loop,
)


def main(config: cea.config.Configuration):
    """
    Run Thermal Network Part 2: Flow & Sizing (Simplified Model)

    Supports both single-phase and multi-phase modes based on configuration.
    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_name, network_names = validate_and_resolve_mode(config, locator)

    if network_names is not None:  # multi-phase
        from cea.technologies.thermal_network.common.phasing import run_multi_phase
        return run_multi_phase(config, locator, network_names, model_type='simplified')

    validate_network_name(locator, network_name)

    def run_simplified(locator, config, network_type, network_name):
        from cea.technologies.thermal_network.simplified.model import thermal_network_simplified

        connectivity_json_path = locator.get_network_connectivity_file(network_name)
        per_building_services = None

        if os.path.exists(connectivity_json_path):
            with open(connectivity_json_path, 'r') as f:
                connectivity_data = json.load(f)

            if network_type in connectivity_data.get('networks', {}):
                network_data = connectivity_data['networks'][network_type]
                per_building_services_dict = network_data.get('per_building_services', {})

                if per_building_services_dict:
                    per_building_services = {
                        building: set(services)
                        for building, services in per_building_services_dict.items()
                    }
                    print("  Per-building service configuration loaded from connectivity.json")

        thermal_network_simplified(locator, config, network_type, network_name,
                                   per_building_services=per_building_services)

    for network in network_name:
        run_network_types_loop(config, locator, network, run_simplified, "Simplified")


if __name__ == '__main__':
    main(cea.config.Configuration())
