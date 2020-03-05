"""
This script checks a scenario for v2.29.0 format and migrates the input tables it to the v2.31.1 format.

NOTE: You'll still need to run the archetypes-mapper after this script has run.
"""

from __future__ import division
from __future__ import print_function

import os
import cea
import pandas as pd
import collections

import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def find_migrators(scenario):
    """
    Add new migrations here as they become necessary
    the database-migrator will run these in sequence starting from the first migrator found
    (NOTE: I've added a dummy migration - 2.31 - 2.31.1 - to show how the principle works)
    """
    migrations = collections.OrderedDict()
    migrations["v2.29.0 - v2.31.0"] = (is_2_29, migrate_2_29_to_2_31)
    migrations["v2.31.0 - v2.31.1"] = (is_2_31, migrate_2_31_to_2_31_1)

    for key, migration_info in migrations.items():
        identifier, migrator = migration_info
        if identifier(scenario):
            yield key, migrator


def is_2_29(scenario):
    if not os.path.exists(os.path.join(scenario, "inputs", "building-properties", "age.dbf")):
        return False
    if not os.path.exists(os.path.join(scenario, "inputs", "building-properties", "occupancy.dbf")):
        return False
    if os.path.exists(os.path.join(scenario, "inputs", "building-properties", "typology.dbf")):
        # avoid migrating multiple times
        return False
    return True


def migrate_2_29_to_2_31(scenario):
    def lookup_standard(year, standards_df):
        # find first standard that is similar to the year
        standard = standards_df[(standards_df.YEAR_START < year) & (year < standards_df.YEAR_END)].iloc[0]
        return standard.STANDARD

    def convert_occupancy(name, occupancy_dbf):
        row = occupancy_dbf[occupancy_dbf.Name == name].iloc[0]
        uses = set(row.to_dict().keys()) - {"Name", "REFERENCE"}
        uses = sorted(uses, cmp=lambda a, b: cmp(float(row[a]), float(row[b])), reverse=True)
        result = {
            "1ST_USE": uses[0],
            "1ST_USE_R": float(row[uses[0]]),
            "2ND_USE": uses[1],
            "2ND_USE_R": float(row[uses[1]]),
            "3RD_USE": uses[2],
            "3RD_USE_R": float(row[uses[2]])}
        if pd.np.isclose(result["2ND_USE_R"], 0.0):
            result["1ST_USE_R"] = 1.0
            result["2ND_USE_R"] = 0.0
            result["3RD_USE_R"] = 0.0
            result["2ND_USE"] = "NONE"
            result["3RD_USE"] = "NONE"
        elif pd.np.isclose(result["3RD_USE_R"], 0.0):
            result["1ST_USE_R"] = 1.0 - result["2ND_USE_R"]
            result["3RD_USE_R"] = 0.0
            result["3RD_USE"] = "NONE"

        result["1ST_USE_R"] = 1.0 - result["2ND_USE_R"] - result["3RD_USE_R"]
        return result

    def merge_age_and_occupancy_to_typology(age_dbf, occupancy_dbf, standards_df):
        # merge age.dbf and occupancy.dbf to typology.dbf
        typology_dbf_columns = ["Name", "YEAR", "STANDARD", "1ST_USE", "1ST_USE_R", "2ND_USE", "2ND_USE_R", "3RD_USE",
                                "3RD_USE_R"]
        typology_dbf = pd.DataFrame(columns=typology_dbf_columns)

        for rindex, row in age_dbf.iterrows():
            typology_row = {
                "Name": row.Name,
                "YEAR": row.built,
                "STANDARD": lookup_standard(row.built, standards_df)}
            typology_row.update(convert_occupancy(row.Name, occupancy_dbf))

            typology_dbf = typology_dbf.append(typology_row, ignore_index=True)

        return typology_dbf

    age_dbf_path = os.path.join(scenario, "inputs", "building-properties", "age.dbf")
    occupancy_dbf_path = os.path.join(scenario, "inputs", "building-properties", "occupancy.dbf")

    age_df = dbf_to_dataframe(age_dbf_path)
    occupancy_df = dbf_to_dataframe(occupancy_dbf_path)

    locator = cea.inputlocator.InputLocator(scenario=scenario)
    standards_df = pd.read_excel(locator.get_database_construction_standards(), "STANDARD_DEFINITION")
    typology_df = merge_age_and_occupancy_to_typology(age_df, occupancy_df, standards_df)

    print("- writing typology.dbf")
    dataframe_to_dbf(typology_df, locator.get_building_typology())
    print("- removing occupancy.dbf and age.dbf")
    os.remove(age_dbf_path)
    os.remove(occupancy_dbf_path)
    print("- removing invalid input-tables (NOTE: run archetypes-mapper again)")
    for fname in {"supply_systems.dbf", "internal_loads.dbf", "indoor_comfort.dbf",
                  "air_conditioning_systems.dbf", "architecture.dbf"}:
        fpath = os.path.join(scenario, "inputs", "building-properties", fname)
        if os.path.exists(fpath):
            print("  - removing {fname}".format(fname=fname))
            os.remove(fpath)
    print("- done")
    print("- NOTE: You'll need to run the archetpyes-mapper tool after this migration!")


def is_2_31(scenario):
    # NOTE: these checks can get more extensive when migrations get more intricate... this is just an example
    return os.path.exists(os.path.join(scenario, "inputs", "building-properties", "typology.dbf"))


def migrate_2_31_to_2_31_1(scenario):
    # nothing needs to be done. this is just an example of a migration - add your own in this fashion
    print("- (nothing to do)")


def main(config):
    for key, migrator in find_migrators(config.scenario):
        print("Performing migration {key}".format(key=key))
        migrator(config.scenario)


if __name__ == "__main__":
    main(cea.config.Configuration())