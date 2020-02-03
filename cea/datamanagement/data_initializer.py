"""
Initializes the database of cea
"""

# HISTORY:
# J. A. Fonseca  script development          03.02.20

from __future__ import absolute_import
from __future__ import division

import cea.config
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_initializer(locator, databases_path):
    print("Copying technology databases from {source}".format(source=databases_path))

    output_directory = locator.get_databases_folder()

    from distutils.dir_util import copy_tree
    copy_tree(databases_path, output_directory)


def main(config):
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """

    print('Running data-intializer with scenario = %s' % config.scenario)
    print('Running data-intializer with databases located in = %s' % config.data_initializer.databases_path)
    locator = cea.inputlocator.InputLocator(config.scenario)
    data_initializer(locator=locator, region=config.data_initializer.databases_path)


if __name__ == '__main__':
    main(cea.config.Configuration())
