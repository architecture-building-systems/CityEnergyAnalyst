import unittest
import os
import cea.inputlocator

class TestInputLocator(unittest.TestCase):

    def test_weather_names(self):
        locator = cea.inputlocator.InputLocator(None)
        self.assertTrue(len(locator.get_weather_names()) > 0)

    def test_weather(self):
        locator = cea.inputlocator.InputLocator(None)
        weather = locator.get_weather_names()[0]
        self.assertTrue(os.path.exists(locator.get_weather(weather)))
