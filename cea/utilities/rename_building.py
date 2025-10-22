"""
A simple CEA script that renames a building in the input files - NOTE: you'll have to re-run the simulation and
analysis scripts to get the changes as only the files defined in ``inputs.yml`` (the files you see in the CEA Dashboard
input editor) are changed.

This is the script behind ``cea rename-building --old <building> --new <building>``
"""





import os
import cea.config
import cea.inputlocator
from cea.interfaces.dashboard.api.inputs import get_input_database_schemas

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config: cea.config.Configuration):
    old_building_name = config.rename_building.old
    new_building_name = config.rename_building.new

    if not new_building_name.strip():
        print("Please specify a new name for the building.")
        return

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    for input_name, input_schema in get_input_database_schemas().items():
        # checked, this is true for all input tables.
        location = input_schema["location"]
        schemas_io = getattr(locator, location)
        file_path = schemas_io()

        if not os.path.exists(file_path):
            print("Skipping input file {file_path} (not found)".format(file_path=file_path))
            continue

        print("Processing input file {file_path}".format(file_path=file_path))

        df = schemas_io.read()
        df.loc[df["name"] == old_building_name, "name"] = new_building_name

        schemas_io.write(df)


if __name__ == '__main__':
    main(cea.config.Configuration())
