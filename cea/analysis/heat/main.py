"""
Anthropogenic Heat Assessment - Main Entry Point

Calculates heat rejection to environment from building energy systems.
Similar structure to system-costs but focused on heat emissions.
"""
import os
import cea.config
import cea.inputlocator
from cea.analysis.heat.heat_rejection import anthropogenic_heat_main

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config: cea.config.Configuration):
    """
    Main entry point for anthropogenic-heat script.

    Calculates heat rejection to environment from:
    - Building-scale systems (standalone buildings)
    - District-scale systems (central plants)

    Outputs:
    - heat_rejection_buildings.csv: Summary by building/plant
    - heat_rejection_components.csv: Detailed component breakdown
    - heat_rejection_hourly_spatial.csv: Hourly time series with coordinates

    :param config: Configuration object
    """
    locator = cea.inputlocator.InputLocator(config.scenario)
    anthropogenic_heat_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
