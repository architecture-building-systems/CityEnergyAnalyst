"""One-off script: run the input-setup workflow for real against Overpass, recording
every osmnx.features_from_polygon / osmnx.graph_from_bbox call (in order) to
cea/tests/fixtures/osm_zug/ so test_inputs_setup_workflow.py can replay them offline.

Not part of the test suite itself -- run manually whenever the recorded calls need
refreshing (e.g. the workflow starts calling osmnx differently).
"""
import os
import pickle
import tempfile

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

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "cea", "tests", "fixtures", "osm_zug")

POLYGON_COORDINATES = [(8.513465734818856, 47.178027239429234), (8.515472027162078, 47.177895971877604),
                       (8.515214535096632, 47.175496635565885), (8.513139577193424, 47.175600066313542),
                       (8.513465734818856, 47.178027239429234)]

_counters = {"features_from_polygon": 0, "graph_from_bbox": 0}
_real_features_from_polygon = osmnx.features_from_polygon
_real_graph_from_bbox = osmnx.graph_from_bbox


def _record(name, real_fn):
    def wrapper(*args, **kwargs):
        idx = _counters[name]
        _counters[name] += 1
        path = os.path.join(FIXTURES_DIR, f"{name}_{idx}.pkl")
        try:
            result = real_fn(*args, **kwargs)
        except Exception as e:
            # Record the failure itself (e.g. osmnx._errors.InsufficientResponseError for a
            # sparse building-parts query) so replay reproduces it instead of silently
            # serving the next call's fixture in its place.
            with open(path, "wb") as f:
                pickle.dump(e, f)
            print(f"Recorded {name} call #{idx} -> {path} (raised {type(e).__name__})")
            raise
        with open(path, "wb") as f:
            pickle.dump(result, f)
        print(f"Recorded {name} call #{idx} -> {path}")
        return result
    return wrapper


def main():
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    osmnx.features_from_polygon = _record("features_from_polygon", _real_features_from_polygon)
    osmnx.graph_from_bbox = _record("graph_from_bbox", _real_graph_from_bbox)
    # zone_helper/surroundings_helper/streets_helper imported osmnx as a module and call
    # osmnx.features_from_polygon / osmnx.graph_from_bbox through that module reference, so
    # patching the attributes on the osmnx module itself (above) is visible to them too.

    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = os.path.join(tempfile.gettempdir(), "reference-case-open-record")
    config.create_polygon.coordinates = POLYGON_COORDINATES
    config.create_polygon.filename = 'site'

    database_helper.main(config)
    create_polygon.main(config)
    zone_helper.main(config)
    surroundings_helper.main(config)
    terrain_helper.main(config)
    streets_helper.main(config)
    archetypes_mapper.main(config)

    print("Call counts:", _counters)


if __name__ == "__main__":
    main()
