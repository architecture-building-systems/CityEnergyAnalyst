"""Geometry is checked before `save_all_inputs` writes anything.

The save rebuilds each shapefile from the geojson features it is sent, so a payload that is
wrong in the right way corrupts the scenario rather than failing: two rows sharing a name
collapse into one, and a self-intersecting footprint writes cleanly and fails much later.

A *missing* footprint is treated differently. The editor offers no way to draw one, so refusing
the save would leave deleting the row as the only escape -- the data loss the check exists to
prevent. Those rows are carried through the write by `restore_rows_without_geometry` instead,
and the banner in the editor says they are there.
"""

import unittest

import geopandas
from shapely.geometry import Polygon

from cea.interfaces.dashboard.api.inputs import (
    restore_rows_without_geometry,
    shapefile_payload_problems,
)

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
    return {name: {'name': name, 'height_ag': 10.0} for name in names}


class TestShapefilePayloadProblems(unittest.TestCase):
    """What must stop a save: things the user just did and can undo."""

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

    def test_several_problems_are_all_reported(self):
        # One save, one list: fixing them one round-trip at a time would be miserable.
        problems = shapefile_payload_problems(
            'zone',
            table('B1000', 'B1001'),
            geojson(feature('B1000', BOWTIE), feature('B1001', SQUARE),
                    feature('B1001', OTHER_SQUARE)),
        )

        self.assertEqual(2, len(problems))
        self.assertTrue(any('malformed' in p for p in problems))
        self.assertTrue(any('more than one row is named' in p for p in problems))

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

    def test_unparseable_geometry_type_is_reported_not_raised(self):
        # shapely raises `GeometryTypeError`, which is neither TypeError nor ValueError.
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


class TestMissingGeometryIsCarriedNotRejected(unittest.TestCase):
    """A footprint the user cannot supply must not block the save, or cost them the row."""

    def test_a_row_without_a_feature_is_not_rejected(self):
        problems = shapefile_payload_problems(
            'zone', table('B1000', 'B1001'), geojson(feature('B1000', SQUARE)))

        self.assertEqual([], problems)

    def test_a_null_geometry_feature_is_not_rejected(self):
        problems = shapefile_payload_problems(
            'zone',
            table('B1000', 'B1001'),
            geojson(feature('B1000', SQUARE), feature('B1001', None)),
        )

        self.assertEqual([], problems)

    def test_an_empty_geometry_is_not_rejected(self):
        # `POLYGON EMPTY` reads back from a shapefile as null, so it is the missing case.
        problems = shapefile_payload_problems(
            'zone',
            table('B1000'),
            {'type': 'FeatureCollection',
             'features': [{'type': 'Feature', 'properties': {'name': 'B1000'},
                           'geometry': {'type': 'Polygon', 'coordinates': None}}]},
        )

        self.assertEqual([], problems)


def frame(*names):
    """The frame the save builds from the payload's features."""
    return geopandas.GeoDataFrame(
        [{'name': name, 'height_ag': 10.0} for name in names],
        geometry=[SQUARE] * len(names),
        crs='EPSG:4326',
    )


class TestRestoreRowsWithoutGeometry(unittest.TestCase):
    def test_a_table_only_row_is_added_back_with_no_geometry(self):
        restored = restore_rows_without_geometry(
            frame('B1000'), table('B1000', 'B1001'))

        self.assertEqual(['B1000', 'B1001'], list(restored['name']))
        self.assertIsNone(restored.set_index('name').loc['B1001', 'geometry'])

    def test_the_restored_row_keeps_its_attributes(self):
        # The whole point: the row survives with its data, to be fixed or deleted later.
        restored = restore_rows_without_geometry(
            frame('B1000'), table('B1000', 'B1001')).set_index('name')

        self.assertEqual(10.0, restored.loc['B1001', 'height_ag'])

    def test_a_row_that_has_a_feature_is_not_duplicated(self):
        restored = restore_rows_without_geometry(
            frame('B1000', 'B1001'), table('B1000', 'B1001'))

        self.assertEqual(['B1000', 'B1001'], list(restored['name']))

    def test_nothing_to_restore_leaves_the_frame_alone(self):
        original = frame('B1000')
        restored = restore_rows_without_geometry(original, table('B1000'))

        self.assertEqual(1, len(restored))
        self.assertEqual(list(original.columns), list(restored.columns))

    def test_a_stray_key_in_the_table_cannot_add_a_column(self):
        # The written columns are whatever the features carried; a table row with extra keys
        # must not widen the shapefile.
        rows = table('B1000', 'B1001')
        rows['B1001']['not_a_real_column'] = 'x'

        restored = restore_rows_without_geometry(frame('B1000'), rows)

        self.assertNotIn('not_a_real_column', restored.columns)

    def test_a_frame_without_a_name_column_is_left_alone(self):
        streets = geopandas.GeoDataFrame(
            [{'height_ag': 1.0}], geometry=[SQUARE], crs='EPSG:4326')

        self.assertIs(streets, restore_rows_without_geometry(streets, {'a': {}}))

    def test_an_empty_table_is_left_alone(self):
        original = frame('B1000')

        self.assertIs(original, restore_rows_without_geometry(original, {}))
        self.assertIs(original, restore_rows_without_geometry(original, None))

    def test_the_restored_row_survives_a_shapefile_round_trip(self):
        """A shapefile stores a null geometry and reads it back as `None`.

        This is what makes carrying the row possible at all -- if the write dropped it, the
        save would still be deleting the building, just later.
        """
        import os
        import tempfile

        restored = restore_rows_without_geometry(
            frame('B1000'), table('B1000', 'B1001'))
        path = os.path.join(tempfile.mkdtemp(), 'zone.shp')
        restored.to_file(path, driver='ESRI Shapefile', encoding='ISO-8859-1')

        back = geopandas.read_file(path).set_index('name')
        self.assertIn('B1001', back.index)
        self.assertIsNone(back.loc['B1001', 'geometry'])
        self.assertEqual(10.0, back.loc['B1001', 'height_ag'])


if __name__ == '__main__':
    unittest.main()
