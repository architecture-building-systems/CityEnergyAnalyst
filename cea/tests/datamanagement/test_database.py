import os
import shutil
import tempfile
import unittest

import pandas as pd

from cea.databases import CEADatabase, databases_folder_path
from cea.inputlocator import InputLocator

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create dummy scenario in temporary directory
        self.locator = InputLocator(self.temp_dir.name)
        database_path = self.locator.get_db4_folder()
        os.makedirs(database_path, exist_ok=True)

        # Copy the CH database files into the temporary directory
        shutil.copytree(os.path.join(databases_folder_path, "CH"), database_path, dirs_exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _get_db_dict(self):
        """Helper method to get a database dictionary for testing."""
        db = CEADatabase.from_locator(locator=self.locator)
        return db.to_dict()

    def test_from_locator(self):

        # Initialize the database
        db = CEADatabase.from_locator(locator=self.locator)

        # Check if the database components are initialized correctly
        self.assertIsNotNone(db.archetypes)
        self.assertIsNotNone(db.assemblies)
        self.assertIsNotNone(db.components)

        # Check if the to_dict method returns a dictionary
        db_dict = db.to_dict()
        self.assertIsInstance(db_dict, dict)

    def test_from_dict(self):
        db_dict = self._get_db_dict()

        db = CEADatabase.from_dict(db_dict)
        self.assertIsNotNone(db.archetypes)
        self.assertIsNotNone(db.assemblies)
        self.assertIsNotNone(db.components)


    def test_materials_round_trip(self):
        """MATERIALS.csv survives load -> dict -> save with every column intact.

        The schemas.yml `columns` list is the write-time whitelist, so an incomplete one
        silently drops columns from the user's file.
        """
        source = os.path.join(
            databases_folder_path, "CH", "COMPONENTS", "MATERIALS", "MATERIALS.csv"
        )
        before = pd.read_csv(source)

        CEADatabase.from_dict(self._get_db_dict()).save(self.locator)
        after = pd.read_csv(self.locator.get_database_components_materials())

        self.assertEqual(set(before.columns), set(after.columns))
        self.assertEqual(len(before), len(after))
        # Some CH densities are ranges ("1'400 - 1'500"); typing them as float in
        # schemas.yml would mangle them, so compare the column verbatim.
        pd.testing.assert_series_equal(
            before.set_index("name")["density"].sort_index(),
            after.set_index("name")["density"].sort_index(),
        )

    def test_database_without_materials(self):
        """Regions that ship no MATERIALS.csv must still load.

        Uses SG rather than deleting the file from CH: CH's envelope rows are defined by
        material layers, so removing MATERIALS.csv makes every ENVELOPE row unresolvable.
        SG defines its envelope by direct properties and genuinely has no materials file.
        """
        with tempfile.TemporaryDirectory() as tmp:
            locator = InputLocator(tmp)
            os.makedirs(locator.get_db4_folder(), exist_ok=True)
            shutil.copytree(
                os.path.join(databases_folder_path, "SG"),
                locator.get_db4_folder(),
                dirs_exist_ok=True,
            )
            self.assertFalse(os.path.exists(locator.get_database_components_materials()))

            db = CEADatabase.from_locator(locator=locator)
            self.assertIsNone(db.components.materials.materials)

            # Still serialises, and the key is present-but-null so the editor renders the
            # dataset and can offer the import action.
            db_dict = db.to_dict()
            self.assertIn("materials", db_dict["components"])
            self.assertIsNone(db_dict["components"]["materials"]["materials"])

    def test_schema(self):
        schema = CEADatabase.schema()
        self.assertIsInstance(schema, dict)

    def test_locator_mapping(self):
        locator_mapping = CEADatabase._locator_mappings()

        self.assertIsInstance(locator_mapping, dict)
        self.assertIn('archetypes', locator_mapping)
        self.assertIn('assemblies', locator_mapping)
        self.assertIn('components', locator_mapping)

    def test_schema_replacement(self):
        schema = CEADatabase.schema(replace_locator_refs=True)
        self.assertIsInstance(schema, dict)
        self.assertIn('archetypes', schema)
        self.assertIn('assemblies', schema)
        self.assertIn('components', schema)
