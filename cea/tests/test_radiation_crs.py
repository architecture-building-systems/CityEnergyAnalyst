import json
import os

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import Polygon

from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output
from cea.resources.radiationCRAX.main import generate_general_building_data_for_CRAX, add_terrain_elevation
from cea.utilities.standardize_coordinates import get_projected_coordinate_system

# a footprint near Zurich (47.18N, 8.51E) in UTM 32N, wrongly tagged as UTM 32S as seen in some scenarios
NORTH_CRS = "EPSG:32632"
SOUTH_CRS = "EPSG:32732"
X0, Y0 = 463100.0, 5224800.0


def _footprint(x0, y0):
    return Polygon([(x0, y0), (x0 + 20, y0), (x0 + 20, y0 + 20), (x0, y0 + 20)])


def _write_zone(path):
    north = gpd.GeoDataFrame({"name": ["B1"], "height_ag": [10.0], "floors_ag": [3]},
                             geometry=[_footprint(X0, Y0)], crs=NORTH_CRS)
    north.to_crs(SOUTH_CRS).to_file(path)  # same place, stored in the wrong-hemisphere CRS


def test_crax_building_data_follows_requested_crs(tmp_path):
    zone_path = str(tmp_path / "zone.shp")
    _write_zone(zone_path)
    crs = get_projected_coordinate_system(47.18, 8.51)

    csv = generate_general_building_data_for_CRAX(zone_path, str(tmp_path), "zone.csv", crs)

    base = eval(pd.read_csv(csv).loc[0, "BuildingBase"])
    xs, ys = zip(*base)
    assert min(ys) == pytest.approx(Y0, abs=0.5)
    assert min(xs) == pytest.approx(X0, abs=0.5)


def _write_terrain(path, crs, x_left, y_top, elevation):
    data = np.full((60, 60), elevation, dtype="float32")
    with rasterio.open(path, "w", driver="GTiff", height=60, width=60, count=1, dtype="float32", crs=crs,
                       transform=from_origin(x_left, y_top, 5, 5), nodata=-9999) as dst:
        dst.write(data, 1)


def test_crax_terrain_elevation_matches_across_crs(tmp_path):
    crs = get_projected_coordinate_system(47.18, 8.51)
    building_csv = tmp_path / "buildings.csv"

    # same terrain in the matching CRS, and re-tagged in the wrong-hemisphere CRS
    matching_tif = str(tmp_path / "matching.tif")
    _write_terrain(matching_tif, NORTH_CRS, X0 - 100, Y0 + 200, 400.0)
    transformer = Transformer.from_crs(NORTH_CRS, SOUTH_CRS, always_xy=True)
    x_south, y_south = transformer.transform(X0 - 100, Y0 + 200)
    mismatched_tif = str(tmp_path / "mismatched.tif")
    _write_terrain(mismatched_tif, SOUTH_CRS, x_south, y_south, 400.0)

    for tif in (matching_tif, mismatched_tif):
        pd.DataFrame({"BuildingBase": [str(list(_footprint(X0, Y0).exterior.coords))]}).to_csv(building_csv,
                                                                                               index=False)
        add_terrain_elevation(tif, str(building_csv), crs)
        assert pd.read_csv(building_csv).loc[0, "TerrainElevation"] == pytest.approx(400.0)


class _DummyLayer(MapLayer):
    name = "dummy"
    label = "Dummy"
    description = "Dummy layer for cache key tests"
    category = None

    def __init__(self, project, input_file):
        self.project = project
        self.input_file = input_file
        self.calls = 0

    @classmethod
    def expected_parameters(cls):
        return {}

    @classmethod
    def file_requirements(cls):
        return []

    def get_required_files_with_metadata(self, parameters):
        return {self.input_file: False}

    @cache_output
    def generate_data(self, parameters):
        self.calls += 1
        return {"calls": self.calls}


class _VersionedLayer(_DummyLayer):
    cache_version = "2"


def _cache_files(project):
    folder = os.path.join(project, ".cache", "map_layers", "dummy")
    return sorted(os.listdir(folder))


def test_cache_key_changes_with_cache_version_and_is_stable_otherwise(tmp_path):
    input_file = str(tmp_path / "input.txt")
    open(input_file, "w").close()
    project = str(tmp_path)
    parameters = {"period": [0, 10]}

    layer = _DummyLayer(project, input_file)
    layer.generate_data(parameters)
    layer.generate_data(parameters)
    assert layer.calls == 1  # second call is served from the cache
    assert len(_cache_files(project)) == 1

    _VersionedLayer(project, input_file).generate_data(parameters)
    assert len(_cache_files(project)) == 2  # a different cache_version does not reuse the entry

    with open(os.path.join(project, ".cache", "map_layers", "dummy", _cache_files(project)[0])) as f:
        assert isinstance(json.load(f), dict)
