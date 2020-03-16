"""
Create a schemas.yml-compatible entry given a locator method by reading the file from the current scenario.
"""

from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_schema(scenario, locator_method, args=None):
    print(args)
    if not args:
        args = []
    locator = cea.inputlocator.InputLocator(scenario=scenario)
    method = getattr(locator, locator_method)
    path = method(*args)
    return path


def main(config):
    """
    Read the schema entry for a locator method, compare it to the current entry and print out a new, updated version.
    """
    print(read_schema(config.scenario, config.schemas.locator_method, config.schemas.args))


if __name__ == '__main__':
    main(cea.config.Configuration())
