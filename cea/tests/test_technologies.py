"""
Test cea.technologies
"""

import unittest
import numpy as np
import ConfigParser
import json
import os
from cea.technologies.cooling_tower import calc_CT_partload_factor, calc_CT
from cea.tests.test_schedules import get_test_config_path

class TestCoolingTower(unittest.TestCase):
    def test_CT_partload_factor(self):
        """Make sure the partload factor is always positive."""
        partload_ratios = np.arange(0.0, 1.1, 0.1)
        partload_factors = np.vectorize(calc_CT_partload_factor)(partload_ratios)
        self.assertGreaterEqual(partload_factors.all(), 0.0)

    def test_calc_CT(self):
        """Make sure the calculation method remains the same."""
        q_hot_Wh = np.arange(0.0, 1E6, 1E5)
        Q_nom_W = max(q_hot_Wh)
        el_W = np.vectorize(calc_CT)(q_hot_Wh, Q_nom_W)

        config = ConfigParser.SafeConfigParser()
        config.read(get_test_config_path())
        reference_results = json.loads(config.get('test_calc_CT', 'expected_results'))
        np.testing.assert_allclose(el_W, reference_results)



def get_test_config_path():
    """return the path to the test data configuration file (``cea/tests/test_schedules.config``)"""
    return os.path.join(os.path.dirname(__file__), 'test_technologies.config')


if __name__ == "__main__":
    unittest.main()