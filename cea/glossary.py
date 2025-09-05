"""
Contains some helper methods for working with glossary data
"""




import cea.schemas
import pandas as pd

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

__glossary_df = None  # keep a copy of this as it won't be changed during runtime. ever.


def read_glossary_df(plugins):
    """Returns the glossary as a DataFrame, created from the schemas.yml file. NOTE: This is used by the GUI."""
    global __glossary_df
    if __glossary_df is None:
        schemas = cea.schemas.schemas(plugins)
        glossary_df = pd.DataFrame(columns=["SCRIPT", "LOCATOR_METHOD", "WORKSHEET", "VARIABLE",
                                            "DESCRIPTION", "UNIT", "VALUES", "TYPE", "COLOR", "FILE_NAME"])
        rows = []
        for lm in schemas:
            if lm == "get_database_standard_schedules_use":
                # the schema for schedules is non-standard
                continue
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

        glossary_df = pd.concat([glossary_df, pd.DataFrame(rows)], ignore_index=True)
        glossary_df['key'] = glossary_df['FILE_NAME'] + '!!!' + glossary_df['VARIABLE']
        glossary_df = glossary_df.set_index(['key'])
        glossary_df = glossary_df.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])
        __glossary_df = glossary_df
    return __glossary_df


def glossary_row(script, file_path, col, lm, cd, worksheet):
    try:
        return {
            "SCRIPT": script,
            "LOCATOR_METHOD": lm,
            "WORKSHEET": worksheet,
            "VARIABLE": col,
            "DESCRIPTION": cd["description"],
            "UNIT": cd.get("unit"),
            "VALUES": cd.get("values"),
            "TYPE": cd["type"],
            "COLOR": "",
            "FILE_NAME": ":".join((file_path, worksheet)) if worksheet else file_path
        }
    except KeyError as ex:
        raise KeyError(f"Failed to create glossary_row({script}, {file_path}, {col}, {lm}, {cd}, {worksheet}): {ex}")


if __name__ == "__main__":
    print(read_glossary_df(plugins=[]))
