"""
Emissions analysis (LCA)
This script is used to calculate the LCA
"""





import os

from cea.analysis.lca.embodied import lca_embodied
from cea.analysis.lca.emission_time_dependent import operational_hourly, total_yearly
from cea.analysis.lca.operation import lca_operation


import cea.config
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def emissions_simplified(locator, config):

    # Force the simplified embodied and operation to be true
    # embodied = config.emissions.embodied
    # operation = config.emissions.operational
    embodied = True
    operation = True

    # embodied emissions
    if embodied:
        year_to_calculate = config.emissions.year_to_calculate
        if year_to_calculate is None:
            year_to_calculate = 2025
        lca_embodied(year_to_calculate, locator)

    # operation emissions
    if operation:
        lca_operation(locator)

def emissions_detailed(config):
    if config.emissions.include_emission_timeline:
        operational_hourly(config)
        total_yearly(config)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running emissions with scenario = %s' % config.scenario)

    # Calculate the simplified-aggregated
    emissions_simplified(locator=locator, config=config)

    # Calculate the hourly and timeline
    emissions_detailed(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
