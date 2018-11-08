
from __future__ import division

import os

from cea.analysis.lca.embodied import lca_embodied
from cea.analysis.lca.operation import lca_operation
from cea.analysis.lca.mobility import lca_mobility

import cea.config
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def emissions_main(locator, config):

    #embodied emissions
    year_to_calculate = config.emissions.year_to_calculate
    lca_embodied(year_to_calculate, locator, config)

    #operation emissions
    lca_operation(locator, config)

    #mobility emissions
    lca_mobility(locator, config)

def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running emissions with scenario = %s' % config.scenario)

    emissions_main(locator=locator, config=config)

if __name__ == '__main__':
    main(cea.config.Configuration())
