import unittest
import numpy as np

from cea.technologies.chiller_vapor_compression import calc_averaged_PLF, calc_available_capacity, calc_PLF


class TestLoadDistribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configuration values for WATER, CENTRIFUGAL
        cls.qs = {'q_a': -0.29861976, 'q_b': 0.02996076, 'q_c': -0.00080125,
                  'q_d': 0.01736268, 'q_e': -0.00032606, 'q_f': 0.00063139}

        cls.plfs = {'plf_a': 0.17149273, 'plf_b': 0.58820208, 'plf_c': 0.23737257}

        cls.

    def test_calc_averaged_PLF(self):
        # FIXME: Use python mock in python3
        class dummy_VCC_chiller(object):
            def __init__(self):
                self.scale = "DISTRICT"

            def configuration_values(self, _source_type, _compressor_type):
                return dummy_configuration_values

        dummy_configuration_values = {'Qs': self.qs, 'PLFs': self.plfs}
        VCC_chiller = dummy_VCC_chiller()

        result = calc_averaged_PLF(40000000, 25000000, 279.15, 301.15, VCC_chiller)
        self.assertAlmostEqual(0.9735208306617418, result)

    def test_calc_available_capacity(self):
        result = calc_available_capacity(13333333.3333333, self.qs, 279.15, 301.15)
        self.assertAlmostEqual(12793205.269333301, result)

    def test_calc_PLF(self):
        result = calc_PLF(np.array([1.00000, 0.95416, 0.00000]), self.plfs)
        self.assertEqual(np.array([0.99707, 0.94884, 0.17149]).all(), result.all())


if __name__ == '__main__':
    unittest.main()
