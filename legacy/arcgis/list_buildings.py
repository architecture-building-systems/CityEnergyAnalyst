"""
List all the buildings in a scenario (using the locator)

The reason for this script is that the ArcGIS interface is running with a different python and therefore we can't
just use that locator - it does not have access to the geopandas library.
"""
from __future__ import print_function

import sys
import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(scenario):
    locator = cea.inputlocator.InputLocator(scenario)
    print(', '.join(locator.get_zone_building_names()))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(cea.config.Configuration().scenario)