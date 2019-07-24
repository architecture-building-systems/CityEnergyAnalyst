"""
A simple CEA script that renames a building in the input files - NOTE: you'll have to re-run the simulation and
analysis scripts to get the changes as only the files defined in ``inputs.yml`` (the files you see in the CEA Dashboard
input editor) are changed.

This is the script behind ``cea rename-building --old <building> --new <building>``
"""

from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
import cea.interfaces.dashboard.inputs
import yaml
import geopandas
import cea.utilities.dbf as dbf

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def rename_shp_file(path, pk, old, new):
    df = geopandas.GeoDataFrame.from_file(path)
    df.loc[df[pk] == old, pk] = new
    df.to_file(path)


def rename_dbf_file(path, pk, old, new):
    df = dbf.dbf_to_dataframe(path)
    df.loc[df[pk] == old, pk] = new
    dbf.dataframe_to_dbf(df, path)


def main(config):
    old = config.rename_building.old
    new = config.rename_building.new

    if not new.strip():
        print("Please specify a new name for the building.")
        return

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # read in the list of input files (same metadata as used by dashboard building_properties)
    inputs_yml = os.path.join(os.path.dirname(cea.interfaces.dashboard.inputs.__file__), "inputs.yml")
    with open(inputs_yml, 'r') as inputs_fp:
        inputs_dict = yaml.load(inputs_fp)

    for input_name, input_data in inputs_dict.items():
        pk = input_data["pk"]
        file_type = input_data["type"]  # "shp" or "dbf"
        location = input_data["location"]
        file_path = getattr(locator, location)()

        if not os.path.exists(file_path):
            print("Skipping input file {file_path} (not found)".format(file_path=file_path))
            continue

        print("Processing input file {file_path}".format(file_path=file_path))

        if file_type == "shp":
            rename_shp_file(file_path, pk, old, new)
        elif file_type == "dbf":
            rename_dbf_file(file_path, pk, old, new)
        else:
            raise ValueError("Unexpected type for {input} in inputs.yml: {file_type}".format(
                input=input_name, file_type=file_type))


if __name__ == '__main__':
    main(cea.config.Configuration())