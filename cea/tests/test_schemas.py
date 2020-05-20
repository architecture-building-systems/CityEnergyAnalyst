"""
Tests to make sure the schemas.yml file is structurally sound.
"""

import unittest

import os
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

        for method in extract_locator_methods(locator):
            self.assertIn(method, schemas.keys())

    def test_all_locator_methods_have_a_file_path(self):
        schemas = cea.schemas.schemas(plugins=[])

        for lm in schemas:
            self.assertIn("file_path", schemas[lm], "{lm} does not have a file_path".format(lm=lm))
            self.assertIsInstance(schemas[lm]["file_path"], basestring, "{lm} does not have a file_path".format(lm=lm))
            self.assertNotIn("\\", schemas[lm]["file_path"], "{lm} has backslashes in it's file_path".format(lm=lm))

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
                                      "Missing description for {lm}/{ws}/{col}".format(lm=lm, ws=ws, col=col))
            else:
                for col in schemas[lm]["schema"]["columns"]:
                    self.assertIn("description", schemas[lm]["schema"]["columns"][col],
                                  "Missing description for {lm}/{col}".format(lm=lm, col=col))

    def test_all_schemas_have_a_columns_entry(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            if lm == "get_database_standard_schedules_use":
                # the schema for schedules is non-standard
                continue
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schemas[lm]["schema"]:
                    self.assertIn("columns", schemas[lm]["schema"][ws], "Missing columns for {lm}/{ws}".format(
                        lm=lm, ws=ws))
            else:
                self.assertIn("columns", schemas[lm]["schema"], "Missing columns for {lm}".format(lm=lm))

    def test_all_schema_columns_documented(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas.keys():
            if lm in SKIP_LMS:
                # these can't be documented properly due to the file format
                continue
            schema = schemas[lm]["schema"]
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schema.keys():
                    ws_schema = schema[ws]["columns"]
                    for col in ws_schema.keys():
                        self.assertNotEqual(ws_schema[col]["description"].strip(), "TODO",
                                            "Missing description for {lm}/{ws}/{col}/description".format(
                                                lm=lm, ws=ws, col=col))
                        self.assertNotEqual(ws_schema[col]["unit"].strip(), "TODO",
                                            "Missing description for {lm}/{ws}/{col}/unit".format(
                                                lm=lm, ws=ws, col=col))
                        self.assertNotEqual(ws_schema[col]["values"].strip(), "TODO",
                                            "Missing description for {lm}/{ws}/{col}/description".format(
                                                lm=lm, ws=ws, col=col))
            elif schemas[lm]["file_type"] in {"shp", "dbf", "csv"}:
                for col in schema["columns"].keys():
                    try:
                        self.assertNotEqual(schema["columns"][col]["description"].strip(), "TODO",
                                            "Missing description for {lm}/{col}/description".format(
                                                lm=lm, col=col))
                        self.assertNotEqual(schema["columns"][col]["unit"].strip(), "TODO",
                                            "Missing description for {lm}/{col}/description".format(
                                                lm=lm, col=col))
                        self.assertNotEqual(schema["columns"][col]["values"].strip(), "TODO",
                                            "Missing description for {lm}/{col}/description".format(
                                                lm=lm, col=col))
                    except BaseException as e:
                        self.fail("Problem with lm={lm}, col={col}, message: {m}".format(lm=lm, col=col, m=e.message))

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
                                      "Missing type definition for {lm}/{ws}/{col}".format(
                                                lm=lm, ws=ws, col=col))
                        col_type = ws_schema[col]["type"]
                        self.assertIn(col_type, valid_types,
                                      "Invalid type definition for {lm}/{ws}/{col}: {type}".format(
                                                lm=lm, ws=ws, col=col, type=col_type))
            elif schemas[lm]["file_type"] in {"shp", "dbf", "csv"}:
                for col in schema["columns"].keys():
                    self.assertIn("type", schema["columns"][col],
                                  "Missing type definition for {lm}/{col}".format(lm=lm, col=col))
                    col_type = schema["columns"][col]["type"]
                    self.assertIn(col_type, valid_types,
                                  "Invalid type definition for {lm}/{col}: {type}".format(lm=lm, col=col, type=col_type))

    def test_each_lm_has_created_by(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            self.assertIn("created_by", schemas[lm], "{lm} missing created_by entry".format(lm=lm))
            self.assertIsInstance(schemas[lm]["created_by"], list,
                                  "created_by entry of {lm} must be a list".format(lm=lm))

    def test_each_lm_has_used_by(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            self.assertIn("used_by", schemas[lm], "{lm} missing used_by entry".format(lm=lm))
            self.assertIsInstance(schemas[lm]["used_by"], list,
                                  "used_by entry of {lm} must be a list".format(lm=lm))

    def test_each_lm_has_method(self):
        schemas = cea.schemas.schemas(plugins=[])
        locator = cea.inputlocator.InputLocator(None)
        for lm in schemas:
            self.assertIn(lm, dir(locator),
                          "schemas.yml contains {lm} but no corresponding method in InputLocator".format(lm=lm))

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
                }
                for p in list(parameters.keys()):
                    if not p in method.__code__.co_varnames:
                        del parameters[p]
                folder = method(**parameters)
                folder = os.path.normcase(os.path.normpath(os.path.abspath(folder)))
                self.assertNotIn(folder, folders,
                                 "{attrib} duplicates the result of {prev}".format(
                                     attrib=attrib, prev=folders.get(folder, None)))
                folders[folder] = attrib

    def test_scripts_use_underscores_not_hyphen(self):
        schemas = cea.schemas.schemas(plugins=[])
        for lm in schemas:
            used_by = schemas[lm]["used_by"]
            created_by = schemas[lm]["created_by"]
            for script in used_by:
                self.assertNotIn("-", script, "{lm} used_by script {script} contains hyphen".format(**locals()))
            for script in created_by:
                self.assertNotIn("-", script, "{lm} created_by script {script} contains hyphen".format(**locals()))

    def test_read_glossary_df(self):
        import cea.glossary
        cea.glossary.read_glossary_df(plugins=[])

    def test_units(self):
        """The units and the column names should match"""
        schemas = cea.schemas.schemas(plugins=[])

        def compare_column_to_unit(column_name, unit):
            if column_name in {"m_cw", "m_hw", "s_e", "PV_Bref", "PV_noct", "PV_th", "C_eff", "Cp_fluid", "c1", "c2",
                               "cap_max", "cap_min", "x_int"}:
                # excluding these - manually checked
                return True
            if unit in {"NA", "[-]", "[datetime]", "[DD|MM]", "[m2/m2]"}:
                # ignore these columns, manually tested
                return True
            unit_from_col = "[{unit}]".format(unit=column_name.split("_")[-1])
            if unit == "[%]":
                return unit_from_col == "[pc]"
            if column_name.startswith("dT_"):
                return unit == "[C]"
            if column_name.startswith("dP"):
                return unit == "[Pa/m2]"
            if column_name.startswith("cap_"):
                return unit == "[W]"
            if column_name.endswith("_USD"):
                return unit == "[$USD(2015)/yr]"
            if unit == "[kg CO2-eq/m2.yr]":
                return column_name.endswith("kgCO2m2")
            if unit.startswith("[$USD(2015)/"):
                return column_name.endswith("_cost_" + unit.split("/")[1].replace(".", "").replace("]", ""))
            if "/" in unit:
                return unit_from_col in {unit.replace("/", ""), unit.replace("/", "per")}
            else:
                return unit_from_col == unit

        for lm in schemas:
            if lm in SKIP_LMS or lm.startswith("get_database_"):
                continue
            schema = schemas[lm]["schema"]
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schema.keys():
                    ws_schema = schema[ws]["columns"]
                    for col in ws_schema.keys():
                        self.assertIn("unit", ws_schema[col],
                                      "Missing unit definition for {lm}/{ws}/{col}".format(
                                                lm=lm, ws=ws, col=col))
                        col_unit = ws_schema[col]["unit"]
                        self.assertTrue(compare_column_to_unit(column_name=col, unit=col_unit),
                                        "Unit mismatch for {lm}/{ws}/{col}: expected {unit}".format(
                                            lm=lm, ws=ws, col=col, unit=col_unit))
            elif schemas[lm]["file_type"] in {"shp", "dbf", "csv"}:
                for col in schema["columns"].keys():
                    self.assertIn("unit", schema["columns"][col],
                                  "Missing unit definition for {lm}/{col}".format(lm=lm, col=col))
                    col_unit = schema["columns"][col]["unit"]
                    self.assertTrue(compare_column_to_unit(column_name=col, unit=col_unit),
                                      "Unit mismatch for {lm}/{col}: expected {unit}".format(lm=lm, col=col,
                                                                                             unit=col_unit))


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
        "get_predefined_hourly_setpoints",  # TODO: remove this when we know how
        "get_timeseries_plots_file",  # TODO: remove this when we know how
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


if __name__ == '__main__':
    unittest.main()
