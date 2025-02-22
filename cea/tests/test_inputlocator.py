


import unittest
import os
import pickle
import cea.inputlocator

class TestInputLocator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

    def test_weather_names(self):
        self.assertTrue(len(self.locator.get_weather_names()) > 0)

    def test_weather(self):
        for weather in self.locator.get_weather_names():
            self.assertTrue(os.path.exists(self.locator.get_weather(weather)))

    def test_get_archetypes_properties(self):
        archetypes_properties = self.locator.get_database_archetypes_construction_type()
        self.assertTrue(os.path.exists(archetypes_properties))
        self.assertTrue(os.path.realpath(archetypes_properties).startswith(
            os.path.realpath(self.locator.scenario)), msg='Path not in scenario: %s' % archetypes_properties)

    def test_get_supply_systems_cost(self):
        supply_systems_cost = self.locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
        self.assertTrue(os.path.exists(supply_systems_cost))
        self.assertTrue(os.path.realpath(supply_systems_cost).startswith(
            os.path.realpath(self.locator.scenario)), msg='Path not in scenario: %s' % supply_systems_cost)

    def test_pickle_inputlocator(self):
        """Make sure the InputLocator can be pickled - we need this, e.g. for multiprocessing"""
        locator = pickle.loads(pickle.dumps(self.locator))
        self.assertEqual(locator.scenario, self.locator.scenario)
        self.assertEqual(locator.get_total_demand(), self.locator.get_total_demand())
