"""
Initializes the database of cea
"""

# HISTORY:
# J. A. Fonseca  script development          03.02.20


from shutil import copytree

import cea.config
import cea.inputlocator
import os

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def database_helper(locator,
                     databases_path,
                     initialize_archetypes_database=True,
                     initialize_components_database=True,
                     initialize_assemblies_database=True,
                     ):

    output_directory = locator.get_databases_folder()
    print("Copying databases from {source}".format(source=databases_path))
    print("Copying databases to {path}".format(path=output_directory))

    if initialize_archetypes_database:
        complete_databases_path = os.path.join(databases_path, 'ARCHETYPES')
        complete_output_directory = locator.get_db4_archetypes_folder()
        copytree(complete_databases_path, complete_output_directory, dirs_exist_ok=True)

    if initialize_components_database:
        complete_databases_path = os.path.join(databases_path, 'COMPONENTS')
        complete_output_directory = locator.get_db4_components_folder()
        copytree(complete_databases_path, complete_output_directory, dirs_exist_ok=True)

    if initialize_assemblies_database:
        complete_databases_path = os.path.join(databases_path, 'ASSEMBLIES')
        complete_output_directory = locator.get_db4_assemblies_folder()
        copytree(complete_databases_path, complete_output_directory, dirs_exist_ok=True)


def main(config: cea.config.Configuration):
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """

    print('Running database-helper with scenario = %s' % config.scenario)
    print('Running database-helper with databases located in = %s' % config.database_helper.databases_path)
    locator = cea.inputlocator.InputLocator(config.scenario)

    initialize_archetypes_database = 'archetypes' in config.database_helper.databases
    initialize_components_database = 'components' in config.database_helper.databases
    initialize_assemblies_database = 'assemblies' in config.database_helper.databases

    database_helper(locator=locator,
                     databases_path=config.database_helper.databases_path,
                     initialize_archetypes_database=initialize_archetypes_database,
                     initialize_components_database=initialize_components_database,
                     initialize_assemblies_database=initialize_assemblies_database
                     )


if __name__ == '__main__':
    main(cea.config.Configuration())
