import unittest
from cea.technologies.load_distribution import calc_averaged_PLF, calc_available_capacity, calc_PLF


class TestLoadDistribution(unittest.TestCase):
    def test_calc_averaged_PLF(self):
        result = calc_averaged_PLF(0, 0, 0, 0, 0, 0, "BUILDING")
        self.assertEqual(True, False)

    def test_calc_averaged_PLF_bad_scale(self):
        # are we passing in correct scale values?
        result = calc_averaged_PLF(0, 0, 0, 0, 0, 0, "")
        result = calc_averaged_PLF(0, 0, 0, 0, 0, 0, "WHAT???")
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
