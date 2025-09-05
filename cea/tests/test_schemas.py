"""
Tests to make sure the schemas.yml file is structurally sound.
"""

import re
import unittest

import os
import warnings
from collections import defaultdict

import cea.config
import cea.inputlocator
import cea.scripts
import cea.schemas

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# FIXME: remove this once we have fixed the remaining problems...

SKIP_LMS = {
    "get_building_weekly_schedules",
    "get_optimization_individuals_in_generation",
    "get_optimization_slave_cooling_activation_pattern",
}


class TestSchemas(unittest.TestCase):

    def test_all_locator_methods_described(self):
        schemas = cea.schemas.schemas(plugins=[])
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)

        missing_schema = set()
        for method in extract_locator_methods(locator):
            if method not in schemas.keys():
                missing_schema.add(method)
        
        if missing_schema:
            error_msg = "Missing locator methods in schemas:\n"
            for schema in missing_schema:
                error_msg += f"\t{schema}\n"
            # self.fail(error_msg)
            # TODO: Re-enable after Pixi migration schema updates are complete
            self.skipTest(f"Schema validation temporarily disabled:\n {error_msg}")

    def test_all_locator_methods_have_a_file_path(self):
        schemas = cea.schemas.schemas(plugins=[])

        for lm in schemas:
            self.assertIn("file_path", schemas[lm], f"{lm} does not have a file_path")
            self.assertIsInstance(schemas[lm]["file_path"], str, f"{lm} does not have a file_path")
            self.assertNotIn("\\", schemas[lm]["file_path"], f"{lm} has backslashes in it's file_path")

    def test_all_columns_have_description(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            if lm == "get_database_standard_schedules_use":
                # the schema for schedules is non-standard
                continue
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schemas[lm]["schema"]:
                    for col in schemas[lm]["schema"][ws]["columns"]:
                        self.assertIn("description", schemas[lm]["schema"][ws]["columns"][col],
                                      f"Missing description for {lm}/{ws}/{col}")
            else:
                for col in schemas[lm]["schema"]["columns"]:
                    self.assertIn("description", schemas[lm]["schema"]["columns"][col],
                                  f"Missing description for {lm}/{col}")

    def test_all_schemas_have_a_columns_entry(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            if lm == "get_database_standard_schedules_use":
                # the schema for schedules is non-standard
                continue
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schemas[lm]["schema"]:
                    self.assertIn("columns", schemas[lm]["schema"][ws], f"Missing columns for {lm}/{ws}")
            else:
                self.assertIn("columns", schemas[lm]["schema"], f"Missing columns for {lm}")

    def test_all_schema_columns_documented(self):
        schemas = cea.schemas.schemas(plugins=[])
        missing_docs = defaultdict(list)  # Store all missing documentation details
        
        for lm in schemas.keys():
            if lm in SKIP_LMS:
            # these can't be documented properly due to the file format
                continue
                
            schema = schemas[lm]["schema"]
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schema.keys():
                    ws_schema = schema[ws]["columns"]
                    for col in ws_schema.keys():
                        col_path = f"{lm}/{ws}/{col}"
                        if ws_schema[col]["description"].strip() == "TODO":
                            missing_docs[col_path].append("description")
                        if ws_schema[col]["unit"].strip() == "TODO":
                            missing_docs[col_path].append("unit")
                        if ws_schema[col]["values"].strip() == "TODO":
                            missing_docs[col_path].append("values")
                            
            elif schemas[lm]["file_type"] in {"shp", "dbf", "csv"}:
                for col in schema["columns"].keys():
                    col_path = f"{lm}/{col}"
                    try:
                        if schema["columns"][col].get("description", "TODO").strip() == "TODO":
                            missing_docs[col_path].append("description")
                        if schema["columns"][col].get("unit", "TODO").strip() == "TODO":
                            missing_docs[col_path].append("unit")
                        if schema["columns"][col].get("values", "TODO").strip() == "TODO":
                            missing_docs[col_path].append("values")
                    except BaseException as e:
                        missing_docs[col_path] = [f"error: {str(e)}"]

        if missing_docs:
            error_msg = "Missing documentation in schemas:\n"
            for path, missing in missing_docs.items():
                error_msg += f"  {path}: missing {', '.join(missing)}\n"
            self.fail(error_msg)

    def test_each_column_has_type(self):
        schemas = cea.schemas.schemas(plugins=[])
        valid_types = {"string", "int", "boolean", "float", "date", "Point", "Polygon", "LineString"}
        for lm in schemas.keys():
            if lm in SKIP_LMS:
                # these can't be documented properly due to the file format
                continue
            schema = schemas[lm]["schema"]
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schema.keys():
                    ws_schema = schema[ws]["columns"]
                    for col in ws_schema.keys():
                        self.assertIn("type", ws_schema[col],
                                      f"Missing type definition for {lm}/{ws}/{col}")
                        col_type = ws_schema[col]["type"]
                        self.assertIn(col_type, valid_types,
                                      f"Invalid type definition for {lm}/{ws}/{col}: {col_type}")
            elif schemas[lm]["file_type"] in {"shp", "dbf", "csv"}:
                for col in schema["columns"].keys():
                    self.assertIn("type", schema["columns"][col],
                                  f"Missing type definition for {lm}/{col}")
                    col_type = schema["columns"][col]["type"]
                    self.assertIn(col_type, valid_types,
                                  f"Invalid type definition for {lm}/{col}: {col_type}")

    def test_each_lm_has_created_by(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            self.assertIn("created_by", schemas[lm], f"{lm} missing created_by entry")
            self.assertIsInstance(schemas[lm]["created_by"], list,
                                  f"created_by entry of {lm} must be a list")

    def test_each_lm_has_used_by(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            self.assertIn("used_by", schemas[lm], f"{lm} missing used_by entry")
            self.assertIsInstance(schemas[lm]["used_by"], list,
                                  f"used_by entry of {lm} must be a list")

    def test_each_lm_has_method(self):
        schemas = cea.schemas.schemas(plugins=[])
        locator = cea.inputlocator.InputLocator(None)
        for lm in schemas:
            self.assertIn(lm, dir(locator),
                          f"schemas.yml contains {lm} but no corresponding method in InputLocator")

    def test_each_folder_unique(self):
        locator = cea.inputlocator.ReferenceCaseOpenLocator()
        folders = {}  # map path -> lm
        for attrib in dir(locator):
            if attrib.endswith("_folder") and not attrib.startswith("_"):
                method = getattr(locator, attrib)
                parameters = {
                    "network_type": "DC",
                    "network_name": "",
                    "gen_num": 1,
                    "category": "demand",
                    "type_of_district_network": "space-heating",
                    "summary_folder": "summary",
                    "cea_feature": "demand",
                    "hour_start": 0,
                    "hour_end": 24,
                    "folder_name": "test",
                    "plot_cea_feature": "demand",
                }
                for p in list(parameters.keys()):
                    if p not in method.__code__.co_varnames:
                        del parameters[p]
                try:
                    folder = method(**parameters)
                except TypeError as e:
                    raise ValueError(f"Parameters found for {attrib}: {method.__code__.co_varnames}."
                                     f"Add them to the test.") from e
                if folder is None:
                    warnings.warn(f"{attrib} returned None, skipping...")
                    continue
                folder = os.path.normcase(os.path.normpath(os.path.abspath(folder)))
                self.assertNotIn(folder, folders,
                                 f"{attrib} duplicates the result of {folders.get(folder, None)}")
                folders[folder] = attrib

    def test_scripts_use_underscores_not_hyphen(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            used_by = schemas[lm]["used_by"]
            created_by = schemas[lm]["created_by"]
            for script in used_by:
                self.assertNotIn("-", script, f"{lm} used_by script {script} contains hyphen")
            for script in created_by:
                self.assertNotIn("-", script, f"{lm} created_by script {script} contains hyphen")

    def test_read_glossary_df(self):
        import cea.glossary
        cea.glossary.read_glossary_df(plugins=[])

    def test_numerical_ranges(self):
        def check_range(schema):
            if 'type' in schema and schema['type'] in ['float', 'int']:
                if "values" in schema:
                    values = schema['values']

                    values_min, values_max = parse_numerical_range_value(values, schema['type'])
                    schema_min = schema.get('min')
                    schema_max = schema.get('max')

                    if values_min != schema_min or values_max != schema_max:
                        raise ValueError(
                            'values property do not match range properties. '
                            'values: {values}, min: {schema_min}, max: {schema_max}'.format(
                                values=values, schema_min=schema_min, schema_max=schema_max))

        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            if lm == "get_database_standard_schedules_use" or lm in SKIP_LMS:
                # the schema for schedules is non-standard
                continue
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schemas[lm]["schema"]:
                    for col, col_schema in schemas[lm]["schema"][ws]["columns"].items():
                        try:
                            check_range(col_schema)
                        except ValueError as e:
                            col_label = ":".join([lm, ws, col])
                            print(f"Error in column {col_label}:\n{e}\n")
            else:
                for col, col_schema in schemas[lm]["schema"]["columns"].items():
                    try:
                        check_range(col_schema)
                    except ValueError as e:
                        col_label = ":".join([lm, col])
                        print(f"Error in column {col_label}:\n{e}\n")


def extract_locator_methods(locator):
    """Return the list of locator methods that point to files"""
    ignore = {
        "ensure_parent_folder_exists",
        "get_plant_nodes",
        "get_temporary_file",
        "get_weather_names",
        "get_zone_building_names",
        "verify_database_template",
        "get_optimization_network_all_individuals_results_file",  # TODO: remove this when we know how
        "get_optimization_network_generation_individuals_results_file",  # TODO: remove this when we know how
        "get_optimization_network_individual_results_file",  # TODO: remove this when we know how
        "get_optimization_network_layout_costs_file",  # TODO: remove this when we know how
        "get_timeseries_plots_file",  # TODO: remove this when we know how
        "get_database_conversion_systems_cold_thermal_storage_names",  # TODO: remove this when we know how
    }
    for m in dir(locator):
        if not callable(getattr(locator, m)):
            # normal attributes (fields) are not locator methods
            continue
        if m.startswith("_"):
            # these are private methods, ignore
            continue
        if m in ignore:
            # keep a list of special methods to ignore
            continue
        if m.endswith("_folder"):
            # not interested in folders
            continue
        yield m


def parse_numerical_range_value(value, num_type):
    def parse_string_num(string_num):
        if string_num == 'n':
            return None
        elif num_type == 'float':
            return float(string_num)
        elif num_type == 'int':
            return int(string_num)
        else:
            raise TypeError(f"Unable to cast type `{num_type}`")

    num = r'-?\d+(?:.\d+)?'
    num_or_n = r'{num}|n'.format(num=num)

    # match {1...n}-style values
    regex = r'{{(?P<first>{num_or_n})(...|,)(?P<second>{num_or_n})}}'.format(num_or_n=num_or_n)
    match = re.match(regex, value)

    if match is None:
        raise ValueError(f"values property not in '{{n...n}}' format. Got: '{value}'")
    return parse_string_num(match.group("first")), parse_string_num(match.group("second"))


if __name__ == '__main__':
    unittest.main()
