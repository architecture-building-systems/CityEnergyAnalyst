"""
Emissions analysis (LCA)
This script is used to calculate the LCA
"""

import datetime

from cea.analysis.lca.embodied import lca_embodied
from cea.analysis.lca.emission_time_dependent import operational_hourly, total_yearly, calculate_emissions_for_whatif
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


def emissions_simplified(locator):
    # embodied emissions
    # get current year
    year_to_calculate = datetime.datetime.now().year
    print(f'Running embodied emissions for year {year_to_calculate}')
    lca_embodied(year_to_calculate, locator)

    # operation emissions
    lca_operation(locator)

def emissions_detailed(config):
    operational_hourly(config)
    total_yearly(config)


def main(config: cea.config.Configuration):
    print('Running emissions with scenario = %s' % config.scenario)

    whatif_names = getattr(config.emissions, 'what_if_name', [])
    if whatif_names:
        for whatif_name in whatif_names:
            calculate_emissions_for_whatif(whatif_name, config)
    else:
        # Legacy path: compute from demand results (no what-if scenario)
        emissions_detailed(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
