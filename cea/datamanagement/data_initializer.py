"""
Initializes the database of cea
"""

# HISTORY:
# J. A. Fonseca  script development          03.02.20

from __future__ import absolute_import
from __future__ import division

import warnings

import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea import InvalidOccupancyNameException
from cea.datamanagement.schedule_helper import calc_mixed_schedule
from cea.datamanagement.databases_verification import COLUMNS_ZONE_OCCUPANCY
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_initializer(locator, region):
    technology_database_template = locator.get_technology_template_for_region(region)
    print("Copying technology databases from {source}".format(source=technology_database_template))
    output_directory = locator.get_databases_folder()

    from distutils.dir_util import copy_tree
    copy_tree(technology_database_template, output_directory)


def main(config):
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """

    print('Running data-intializer with scenario = %s' % config.scenario)
    locator = cea.inputlocator.InputLocator(config.scenario)
    data_initializer(locator=locator, region=config.data_initializer.region)


if __name__ == '__main__':
    main(cea.config.Configuration())
