"""
Tests to make sure the schemas.yml file is structurally sound.
"""

import unittest

import cea.config
import cea.inputlocator
import cea.scripts

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class TestSchemas(unittest.TestCase):

    def test_all_locator_methods_described(self):
        schemas = cea.scripts.schemas()
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)

        for method in extract_locator_methods(locator):
            self.assertIn(method, schemas.keys())

    def test_all_columns_have_description(self):
        schemas = cea.scripts.schemas()
        for lm in schemas:
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
        schemas = cea.scripts.schemas()
        for lm in schemas:
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schemas[lm]["schema"]:
                    self.assertIn("columns", schemas[lm]["schema"][ws], "Missing columns for {lm}/{ws}".format(
                        lm=lm, ws=ws))
            else:
                self.assertIn("columns", schemas[lm]["schema"], "Missing columns for {lm}".format(lm=lm))

    def fixme_test_all_schema_columns_documented(self):
        schemas = cea.scripts.schemas()
        for lm in schemas.keys():
            schema = schemas[lm]["schema"]
            if schemas[lm]["file_type"] in {"xls", "xlsx"}:
                for ws in schema.keys():
                    ws_schema = schema[ws]["columns"]
                    for col in ws_schema.keys():
                        self.assertNotEqual(ws_schema[col]["description"].strip(), "TODO",
                                            "Missing descriptiong for {lm}/{ws}/{col}/description".format(
                                                lm=lm, ws=ws, col=col))
                        self.assertNotEqual(ws_schema[col]["unit"].strip(), "TODO",
                                            "Missing descriptiong for {lm}/{ws}/{col}/unit".format(
                                                lm=lm, ws=ws, col=col))
                        self.assertNotEqual(ws_schema[col]["values"].strip(), "TODO",
                                            "Missing descriptiong for {lm}/{ws}/{col}/description".format(
                                                lm=lm, ws=ws, col=col))
            elif schemas[lm]["file_type"] in {"shp", "dbf", "csv"}:
                for col in schema["columns"].keys():
                    self.assertNotEqual(schema["columns"][col]["description"].strip(), "TODO",
                                        "Missing descriptiong for {lm}/{col}/description".format(
                                            lm=lm, col=col))
                    self.assertNotEqual(schema["columns"][col]["unit"].strip(), "TODO",
                                        "Missing descriptiong for {lm}/{col}/description".format(
                                            lm=lm, col=col))
                    self.assertNotEqual(schema["columns"][col]["values"].strip(), "TODO",
                                        "Missing descriptiong for {lm}/{col}/description".format(
                                            lm=lm, col=col))

    def test_each_lm_has_created_by(self):
        schemas = cea.scripts.schemas()
        for lm in schemas:
            self.assertIn("created_by", schemas[lm], "{lm} missing created_by entry".format(lm=lm))
            self.assertIsInstance(schemas[lm]["created_by"], list,
                                  "created_by entry of {lm} must be a list".format(lm=lm))

    def test_each_lm_has_used_by(self):
        schemas = cea.scripts.schemas()
        for lm in schemas:
            self.assertIn("used_by", schemas[lm], "{lm} missing used_by entry".format(lm=lm))
            self.assertIsInstance(schemas[lm]["used_by"], list,
                                  "used_by entry of {lm} must be a list".format(lm=lm))


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
