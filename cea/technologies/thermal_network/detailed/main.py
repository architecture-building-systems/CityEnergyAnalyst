"""
Entry point for the detailed thermal network simulation.
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
    Run Thermal Network Part 2: Flow & Sizing (Detailed Model)

    Supports both single-phase and multi-phase modes based on configuration.
    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_name, network_names = validate_and_resolve_mode(config, locator)

    if network_names is not None:  # multi-phase
        from cea.technologies.thermal_network.common.phasing import run_multi_phase
        return run_multi_phase(config, locator, network_names, model_type='detailed')

    validate_network_name(locator, network_name)

    def run_detailed(locator, config, network_type, network_name):
        from cea.technologies.thermal_network.detailed.model import (
            check_heating_cooling_demand, ThermalNetwork, thermal_network_main
        )

        check_heating_cooling_demand(locator, config)

        class NetworkConfig:
            def __init__(self, base_config, network_type_override):
                self.network_type = network_type_override
                for attr in ['network_names', 'file_type',
                             'load_max_edge_flowrate_from_previous_run', 'start_t', 'stop_t',
                             'use_representative_week_per_month', 'minimum_mass_flow_iteration_limit',
                             'minimum_edge_mass_flow', 'diameter_iteration_limit',
                             'substation_cooling_systems', 'substation_heating_systems',
                             'network_temperature_dh', 'network_temperature_dc',
                             'dh_temperature_mode',
                             'temperature_control', 'plant_supply_temperature', 'equivalent_length_factor']:
                    if hasattr(base_config, attr):
                        setattr(self, attr, getattr(base_config, attr))

        per_network_config = NetworkConfig(config.thermal_network_detailed, network_type)
        thermal_network = ThermalNetwork(locator, network_name, per_network_config)
        thermal_network_main(locator, thermal_network, processes=config.get_number_of_processes())

    run_network_types_loop(config, locator, network_name, run_detailed, "Detailed")


if __name__ == '__main__':
    main(cea.config.Configuration())
