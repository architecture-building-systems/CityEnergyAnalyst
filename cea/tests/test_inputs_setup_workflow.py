import os
import tempfile
import unittest

import cea.config
from cea.utilities import create_polygon
from cea.datamanagement import zone_helper, surroundings_helper, terrain_helper, streets_helper, database_helper, \
    archetypes_mapper

# Zug site coordinates
POLYGON_COORDINATES = [(8.513465734818856, 47.178027239429234), (8.515472027162078, 47.177895971877604),
                       (8.515214535096632, 47.175496635565885), (8.513139577193424, 47.175600066313542),
                       (8.513465734818856, 47.178027239429234)]


class TestInputSetupWorkflowCase(unittest.TestCase):
    def setUp(self):
        self.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        self.config.project = os.path.join(tempfile.gettempdir(), "reference-case-open")

    def test_input_setup_workflow(self):
        self.config.create_polygon.coordinates = POLYGON_COORDINATES
        self.config.create_polygon.filename = 'site'

        database_helper.main(self.config)
        create_polygon.main(self.config)
        # TODO: Mock osmnx.footprints_from_polygon
        zone_helper.main(self.config)
        surroundings_helper.main(self.config)
        terrain_helper.main(self.config)
        streets_helper.main(self.config)
        archetypes_mapper.main(self.config)


if __name__ == '__main__':
    unittest.main()
