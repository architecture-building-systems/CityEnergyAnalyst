"""
Test the utilities/helpers.py file
"""

import unittest
import numpy as np


class TestHelpers(unittest.TestCase):
    def test_hours_of_year_calculations(self):
        import cea.globalvar
        import cea.utilities.helpers
        gv = cea.globalvar.GlobalVariables()
        # translate hours of year to hours relative to start of heating season
        a = np.vectorize(cea.utilities.helpers.hoy_2_seasonhour)(range(8760), gv)
        # translate back
        b = np.vectorize(cea.utilities.helpers.seasonhour_2_hoy)(a, gv)
        # compare
        self.assertTrue(np.array_equal(range(8760), b))

if __name__ == "__main__":
    unittest.main()

