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

    def test_initialization(self):

        # Initialize the database
        db = CEADatabase(self.locator)

        # Check if the database components are initialized correctly
        self.assertIsNotNone(db.archetypes)
        self.assertIsNotNone(db.assemblies)
        self.assertIsNotNone(db.components)

        # Check if the to_dict method returns a dictionary
        db_dict = db.to_dict()
        self.assertIsInstance(db_dict, dict)

    def test_schema(self):
        schema = CEADatabase.schema()
        self.assertIsInstance(schema, dict)
