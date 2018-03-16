"""
Tests for the ``cea.technologies.thermal_network.thermal_network_matrix``
"""
import unittest
import cea.config
import cea.inputlocator
from cea.technologies.thermal_network.thermal_network_matrix import *

class TestThermalNetworkMatrix(unittest.TestCase):
    def test_calc_max_edge_flowrate_t_8759(self):
        network_type = 'DH'
        network_name = ''
        file_type = 'shp'

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        locator = cea.inputlocator.InputLocator(config.scenario)

        thermal_network = ThermalNetwork(locator, network_type, network_name, file_type)
        calc_max_edge_flowrate(locator, thermal_network, set_diameter=True)