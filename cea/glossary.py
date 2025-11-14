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


def _generate_values_display(column_def):
    """
    Generate the VALUES display string for glossary based on column type.

    Auto-generates appropriate display strings based on type:
    - int/float: Range from min/max (e.g., "{0.0...n}", "{0...100}")
    - boolean: "{true, false}"
    - string: "alphanumeric" or "text"
    - date/datetime: Date format string
    - choice: List of valid choices if defined

    Args:
        column_def: Column definition dict from schema

    Returns:
        String representation of valid values for display
    """
    col_type = column_def.get("type")

    # Check if this is a choice type with explicit values
    choice_def = column_def.get("choice", {})
    if "values" in choice_def:
        # Return the list of valid choices as a formatted string
        values_list = choice_def["values"]
        if isinstance(values_list, list):
            return "{" + ", ".join(str(v) for v in values_list) + "}"
        return str(values_list)

    # Also check choice_properties for backward compatibility
    choice_properties = column_def.get("choice_properties", {})
    if choice_properties and "values" in choice_properties:
        # Return the list of valid choices as a formatted string
        values = choice_properties["values"]
        if isinstance(values, list):
            return "{" + ", ".join(str(v) for v in values) + "}"
        # Handle non-list inputs by coercing to an iterable of strings
        return "{" + ", ".join(str(v) for v in [values]) + "}"

    # Generate values based on type
    if col_type == "boolean":
        return "{true, false}"

    elif col_type in ["int", "float"]:
        # Auto-generate from min/max
        min_val = column_def.get("min")
        max_val = column_def.get("max")

        # Format min value
        if min_val is None:
            min_str = "n"
        elif col_type == "float":
            min_str = str(float(min_val))
        else:
            min_str = str(int(min_val))

        # Format max value
        if max_val is None:
            max_str = "n"
        elif col_type == "float":
            max_str = str(float(max_val))
        else:
            max_str = str(int(max_val))

        return f"{{{min_str}...{max_str}}}"

    elif col_type == "string":
        # Check if there's a pattern or format hint
        if "pattern" in column_def:
            return f"pattern: {column_def['pattern']}"
        # Note: Before the values property was removed, some string columns
        # had discrete value lists (e.g., {water, air, brine}) that weren't
        # moved to choice.values. These are now lost, but the columns should
        # ideally be updated to use choice.values for dropdown validation.
        return "alphanumeric"

    elif col_type == "date":
        return "YYYY-MM-DD"

    elif col_type == "datetime":
        return "YYYY-MM-DD HH:MM:SS"

    elif col_type == "time":
        return "HH:MM:SS"

    # For unknown types or TODO placeholders, return None
    return None


def glossary_row(script, file_path, col, lm, cd, worksheet):
    try:
        # Auto-generate VALUES from min/max for numerical types, or use explicit values for choice types
        values_display = _generate_values_display(cd)

        return {
            "SCRIPT": script,
            "LOCATOR_METHOD": lm,
            "WORKSHEET": worksheet,
            "VARIABLE": col,
            "DESCRIPTION": cd["description"],
            "UNIT": cd.get("unit"),
            "VALUES": values_display,
            "TYPE": cd["type"],
            "COLOR": "",
            "FILE_NAME": ":".join((file_path, worksheet)) if worksheet else file_path
        }
    except KeyError as ex:
        raise KeyError(f"Failed to create glossary_row({script}, {file_path}, {col}, {lm}, {cd}, {worksheet}): {ex}")


if __name__ == "__main__":
    print(read_glossary_df(plugins=[]))
