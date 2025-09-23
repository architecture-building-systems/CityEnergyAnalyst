import unittest

import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal
from shapely import Point, Polygon

from cea.datamanagement import zone_helper

class TestCleanGeometries(unittest.TestCase):

    def assertGeoDataFrameEqual(self, a, b, msg, *kwargs):
        try:
            assert_geodataframe_equal(a, b, *kwargs)
        except AssertionError as e:
            raise self.failureException(msg) from e
    
    def setUp(self):
        self.addTypeEqualityFunc(gpd.GeoDataFrame, self.assertGeoDataFrameEqual)

    def test_clean_geometries(self):
        raw_geometries = gpd.GeoDataFrame(
            {
                "geometry": [Point(0,0), Polygon([(0,0), (0,1), (1,0)])]
            }
        )
        expected_output = gpd.GeoDataFrame(
            {
                "geometry": [Polygon([(0,0), (0,1), (1,0)])]
            }
        )
        output = zone_helper.clean_geometries(raw_geometries).reset_index(drop=True)
        self.assertEqual(output, expected_output)