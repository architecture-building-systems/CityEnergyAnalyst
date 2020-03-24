"""
Contains some helper methods for working with glossary data
"""
from __future__ import print_function
from __future__ import division

import os
import csv
import cea.scripts
import pandas as pd

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_glossary_df():
    """Returns the glossary as a DataFrame, created from the schemas.yml file."""
    schemas = cea.scripts.schemas()
    glossary_df = pd.DataFrame(columns=["SCRIPT", "LOCATOR_METHOD", "WORKSHEET", "VARIABLE",
                                        "DESCRIPTION", "UNIT", "VALUES", "TYPE", "COLOR", "FILE_NAME"])
    rows = []
    for lm in schemas:
        script = schemas[lm]["created_by"][0] if schemas[lm]["created_by"] else "-"
        file_path = schemas[lm]["file_path"]
        if schemas[lm]["file_type"] in {"xls", "xlsx"}:
            for ws in schemas[lm]["schema"]:  # ws: worksheet
                for col in schemas[lm]["schema"][ws]["columns"]:
                    cd = schemas[lm]["schema"][ws]["columns"][col]
                    rows.append(glossary_row(script, file_path, col, lm, cd, worksheet=ws))
        else:
            for col in schemas[lm]["schema"]["columns"]:
                cd = schemas[lm]["schema"]["columns"][col]  # cd: column definition
                rows.append(glossary_row(script, file_path, col, lm, cd, worksheet=""))

    glossary_df = glossary_df.append(rows, ignore_index=True)
    glossary_df['key'] = glossary_df['FILE_NAME'] + '!!!' + glossary_df['VARIABLE']
    glossary_df = glossary_df.set_index(['key'])
    glossary_df = glossary_df.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])
    return glossary_df


def glossary_row(script, file_path, col, lm, cd, worksheet):
    return {
        "SCRIPT": script,
        "LOCATOR_METHOD": lm,
        "WORKSHEET": worksheet,
        "VARIABLE": col,
        "DESCRIPTION": cd["description"],
        "UNIT": cd["unit"],
        "VALUES": cd["values"],
        "TYPE": cd["type"],
        "COLOR": "",
        "FILE_NAME": ":".join((file_path, worksheet)) if worksheet else file_path
    }


if __name__ == "__main__":
    print(read_glossary_df())