import os
import pickle
import tempfile
import unittest
from unittest.mock import patch

import osmnx

import cea.config
from cea.datamanagement import (
    archetypes_mapper,
    database_helper,
    streets_helper,
    surroundings_helper,
    terrain_helper,
    zone_helper,
)
from cea.utilities import create_polygon

# Zug site coordinates
POLYGON_COORDINATES = [(8.513465734818856, 47.178027239429234), (8.515472027162078, 47.177895971877604),
                       (8.515214535096632, 47.175496635565885), (8.513139577193424, 47.175600066313542),
                       (8.513465734818856, 47.178027239429234)]

# Recorded once against the real Overpass API (see scripts/record_osm_fixtures.py) for this
# exact polygon, so the workflow doesn't depend on live network access in CI -- overpass-api.de
# has repeatedly timed out from GitHub-hosted runners even though the API itself is fine.
# The workflow calls osmnx.features_from_polygon / osmnx.graph_from_bbox in a fixed order for
# a fixed input, so replaying the recorded calls by position reproduces the same run.
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "osm_zug")


def _load_fixture(name, index):
    path = os.path.join(FIXTURES_DIR, f"{name}_{index}.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)


def _replayed(name):
    calls = {"count": 0}

    def wrapper(*args, **kwargs):
        result = _load_fixture(name, calls["count"])
        calls["count"] += 1
        # A call that raised during recording (e.g. InsufficientResponseError for a sparse
        # building-parts query) is pickled as the exception itself -- reraise it here rather
        # than serving it as a plain OSM result.
        if isinstance(result, BaseException):
            raise result
        return result

    return wrapper


class TestInputSetupWorkflowCase(unittest.TestCase):
    def setUp(self):
        self.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        self.config.project = os.path.join(tempfile.gettempdir(), "reference-case-open")

    @patch.object(osmnx, "features_from_polygon", new_callable=lambda: _replayed("features_from_polygon"))
    @patch.object(osmnx, "graph_from_bbox", new_callable=lambda: _replayed("graph_from_bbox"))
    def test_input_setup_workflow(self, _mock_graph_from_bbox, _mock_features_from_polygon):
        self.config.create_polygon.coordinates = POLYGON_COORDINATES
        self.config.create_polygon.filename = 'site'

        database_helper.main(self.config)
        create_polygon.main(self.config)
        zone_helper.main(self.config)
        surroundings_helper.main(self.config)
        terrain_helper.main(self.config)
        streets_helper.main(self.config)
        archetypes_mapper.main(self.config)


if __name__ == '__main__':
    unittest.main()
