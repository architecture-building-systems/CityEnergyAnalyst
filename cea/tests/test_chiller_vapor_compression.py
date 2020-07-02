import unittest
import numpy as np

from cea.technologies.chiller_vapor_compression import calc_averaged_PLF, calc_available_capacity, calc_PLF

class TestLoadDistribution(unittest.TestCase):
    def test_calc_averaged_PLF(self):
        class dummy_VCC_chiller(object):
            def __init__(self):
                self.max_VCC_capacity = 14000000
                self.min_VCC_capacity = 1758000
                self.scale = "DISTRICT"

        VCC_chiller = dummy_VCC_chiller()

        result = calc_averaged_PLF(40000000, 25000000, 279.15, 301.15, VCC_chiller)
        self.assertAlmostEqual(0.9735208306617418, result)

    def test_calc_available_capacity(self):
        result = calc_available_capacity(13333333.3333333, 'WATER', 'CENTRIFUGAL', 279.15, 301.15)
        self.assertAlmostEqual(12793205.269333301, result)

    def test_calc_PLF(self):
        result = calc_PLF(np.array([1.00000, 0.95416, 0.00000]), 'WATER', 'CENTRIFUGAL')
        self.assertEqual(np.array([0.99707, 0.94884, 0.17149]).all(), result.all())

if __name__ == '__main__':
    unittest.main()
