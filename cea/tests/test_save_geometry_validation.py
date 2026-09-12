"""Geometry is checked before `save_all_inputs` writes anything.

The save rebuilds each shapefile from the geojson features it is sent, so a payload that is
wrong in the right way corrupts the scenario rather than failing: a row with no feature is
dropped from the file, and two rows sharing a name collapse into one. Neither leaves a trace.
"""

import unittest

from shapely.geometry import Polygon

from cea.interfaces.dashboard.api.inputs import shapefile_payload_problems

SQUARE = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
OTHER_SQUARE = Polygon([(2, 2), (2, 3), (3, 3), (3, 2)])
# Crosses itself, so `is_valid` is False. What dragging a vertex past an edge produces.
BOWTIE = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])


def feature(name, geometry):
    return {
        'type': 'Feature',
        'properties': {'name': name},
        'geometry': None if geometry is None else geometry.__geo_interface__,
    }


def geojson(*features):
    return {'type': 'FeatureCollection', 'features': list(features)}


def table(*names):
    return {name: {'height_ag': 10.0} for name in names}


class TestShapefilePayloadProblems(unittest.TestCase):
    def test_valid_payload_has_no_problems(self):
        problems = shapefile_payload_problems(
            'zone',
            table('B1000', 'B1001'),
            geojson(feature('B1000', SQUARE), feature('B1001', OTHER_SQUARE)),
        )
        self.assertEqual([], problems)

    def test_self_intersecting_polygon_is_rejected(self):
        problems = shapefile_payload_problems(
            'zone', table('B1000'), geojson(feature('B1000', BOWTIE)))

        self.assertEqual(1, len(problems))
        self.assertIn('malformed', problems[0])
        self.assertIn('B1000', problems[0])

    def test_duplicated_name_is_rejected(self):
        # Both rows survive into the geojson, but the write does `set_index('name')`, so only
        # one would reach the file.
        problems = shapefile_payload_problems(
            'zone',
            table('B1000'),
            geojson(feature('B1000', SQUARE), feature('B1000', OTHER_SQUARE)),
        )

        self.assertEqual(1, len(problems))
        self.assertIn('more than one row is named B1000', problems[0])

    def test_row_without_a_feature_is_rejected(self):
        # The live case: `df_to_json` drops null-geometry rows for display while the table
        # keeps them, so the save would quietly delete B1001 from zone.shp.
        problems = shapefile_payload_problems(
            'zone', table('B1000', 'B1001'), geojson(feature('B1000', SQUARE)))

        self.assertEqual(1, len(problems))
        self.assertIn('B1001', problems[0])
        self.assertIn('would be deleted', problems[0])
        self.assertNotIn('B1000', problems[0].split(':')[1])

    def test_message_is_singular_for_one_row_and_plural_for_several(self):
        one = shapefile_payload_problems(
            'zone', table('B1000', 'B1001'), geojson(feature('B1000', SQUARE)))[0]
        self.assertIn('1 row has no footprint', one)
        self.assertIn('delete the row', one)

        several = shapefile_payload_problems(
            'zone',
            table('B1000', 'B1001', 'B1002'),
            geojson(feature('B1000', SQUARE)),
        )[0]
        self.assertIn('2 rows have no footprint', several)
        self.assertIn('delete the rows', several)

    def test_null_geometry_feature_is_rejected(self):
        problems = shapefile_payload_problems(
            'zone',
            table('B1000', 'B1001'),
            geojson(feature('B1000', SQUARE), feature('B1001', None)),
        )

        self.assertEqual(1, len(problems))
        self.assertIn('no geometry at all', problems[0])
        self.assertIn('B1001', problems[0])

    def test_several_problems_are_all_reported(self):
        # One save, one list: fixing them one round-trip at a time would be miserable.
        problems = shapefile_payload_problems(
            'zone',
            table('B1000', 'B1001', 'B9999'),
            geojson(feature('B1000', BOWTIE), feature('B1001', SQUARE),
                    feature('B1001', OTHER_SQUARE)),
        )

        self.assertEqual(3, len(problems))
        self.assertTrue(any('malformed' in p for p in problems))
        self.assertTrue(any('more than one row is named' in p for p in problems))
        self.assertTrue(any('B9999' in p for p in problems))

    def test_payload_without_geometry_is_left_to_the_caller(self):
        # `save_all_inputs` skips these with a warning rather than failing the whole save --
        # the geometry file failed to load, which is not something the user did in the editor.
        self.assertEqual([], shapefile_payload_problems('zone', table('B1000'), None))
        self.assertEqual([], shapefile_payload_problems('zone', table('B1000'), {}))
        self.assertEqual([], shapefile_payload_problems('zone', table('B1000'), geojson()))

    def test_unreadable_geometry_is_reported_not_raised(self):
        # A malformed payload must come back as a 400 with a reason, not a 500 traceback.
        problems = shapefile_payload_problems(
            'zone', table('B1000'), {'features': [{'not': 'a feature'}]})

        self.assertEqual(1, len(problems))
        self.assertIn('could not be read', problems[0])

    def test_empty_geometry_is_treated_as_missing(self):
        # `POLYGON EMPTY` passes both `isna` and `is_valid`, but a shapefile write turns it
        # into a null geometry on read-back -- the exact corruption this guards against.
        problems = shapefile_payload_problems(
            'zone',
            table('B1000'),
            {'type': 'FeatureCollection',
             'features': [{'type': 'Feature', 'properties': {'name': 'B1000'},
                           'geometry': {'type': 'Polygon', 'coordinates': None}}]},
        )

        self.assertEqual(1, len(problems))
        self.assertIn('no geometry at all', problems[0])
        self.assertIn('B1000', problems[0])

    def test_unparseable_geometry_type_is_reported_not_raised(self):
        # shapely raises `GeometryTypeError`, which is neither TypeError nor ValueError. It has
        # to come back as a problem, not escape as a 500.
        problems = shapefile_payload_problems(
            'zone',
            table('B1000'),
            {'type': 'FeatureCollection',
             'features': [{'type': 'Feature', 'properties': {'name': 'B1000'},
                           'geometry': {'type': 'Wobble', 'coordinates': [[0, 0]]}}]},
        )

        self.assertEqual(1, len(problems))
        self.assertIn('could not be read', problems[0])

    def test_features_without_a_name_column_are_still_geometry_checked(self):
        # `streets` has no `name`; the geometry check must still apply, and the name-based
        # checks must not raise on its absence.
        problems = shapefile_payload_problems(
            'streets',
            {},
            {'type': 'FeatureCollection',
             'features': [{'type': 'Feature', 'properties': {},
                           'geometry': BOWTIE.__geo_interface__}]},
        )

        self.assertEqual(1, len(problems))
        self.assertIn('malformed', problems[0])


if __name__ == '__main__':
    unittest.main()
