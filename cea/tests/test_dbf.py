"""
Test the utilities/dbf.py file
"""

import unittest
import tempfile
import pandas as pd
from pandas.testing import assert_frame_equal
import numpy as np
import cea.utilities.dbf as dbf

class TestDbf(unittest.TestCase):
    def test_roundtrip(self):
        """Make sure the roundtrip df -> dbf -> df keeps the data intact."""
        df = pd.DataFrame({'a': ['foo', 'bar', 'baz'], 'b': np.random.randn(3)})
        dbf_path = tempfile.mktemp(suffix='.dbf')
        dbf.dataframe_to_dbf(df, dbf_path)
        assert_frame_equal(df, dbf.dbf_to_dataframe(dbf_path))

if __name__ == "__main__":
    unittest.main()