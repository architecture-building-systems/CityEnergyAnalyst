import os
import shutil
import tempfile
import unittest

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
        return db_dict

    def test_from_dict(self):
        db_dict = self.test_from_locator()

        db = CEADatabase.from_dict(db_dict)
        self.assertIsNotNone(db.archetypes)
        self.assertIsNotNone(db.assemblies)
        self.assertIsNotNone(db.components)


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
