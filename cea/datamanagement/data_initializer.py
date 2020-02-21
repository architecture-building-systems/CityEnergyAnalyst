"""
Initializes the database of cea
"""

# HISTORY:
# J. A. Fonseca  script development          03.02.20

from __future__ import absolute_import
from __future__ import division

import cea.config
import cea.inputlocator
import os
from distutils.dir_util import copy_tree

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_initializer(locator,
                     databases_path,
                     initialize_archetypes_database=True,
                     initialize_components_database=True,
                     initialize_assemblies_database=True,
                     ):

    output_directory = locator.get_databases_folder()
    print("Copying databases from {source}".format(source=databases_path))
    print("Copying databases to {path}".format(path=output_directory))

    if initialize_archetypes_database:
        try:
            complete_databases_path = os.path.join(databases_path, 'archetypes')
            complete_output_directory = locator.get_databases_archetypes_folder()
            copy_tree(complete_databases_path, complete_output_directory)
        except:
            raise Exception("we could not find the 'archetypes' database in the path you indicated, please check the spelling")

    if initialize_components_database:
        try:
            complete_databases_path = os.path.join(databases_path, 'components')
            complete_output_directory = locator.get_databases_systems_folder()
            copy_tree(complete_databases_path, complete_output_directory)
        except:
            raise Exception("we could not find the 'components' database in the path you indicated, please check the spelling")

    if initialize_assemblies_database:
        try:
            complete_databases_path = os.path.join(databases_path, 'assemblies')
            complete_output_directory = locator.get_databases_assemblies_folder()
            copy_tree(complete_databases_path, complete_output_directory)
        except:
            raise Exception("we could not find the 'assemblies' database in the path you indicated, please check the spelling")

def main(config):
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """

    print('Running data-intializer with scenario = %s' % config.scenario)
    print('Running data-intializer with databases located in = %s' % config.data_initializer.databases_path)
    locator = cea.inputlocator.InputLocator(config.scenario)

    initialize_archetypes_database = 'archetypes' in config.data_initializer.databases
    initialize_components_database = 'components' in config.data_initializer.databases
    initialize_assemblies_database = 'assemblies' in config.data_initializer.databases

    data_initializer(locator=locator,
                     databases_path=config.data_initializer.databases_path,
                     initialize_archetypes_database=initialize_archetypes_database,
                     initialize_components_database=initialize_components_database,
                     initialize_assemblies_database=initialize_assemblies_database
                     )


if __name__ == '__main__':
    main(cea.config.Configuration())
