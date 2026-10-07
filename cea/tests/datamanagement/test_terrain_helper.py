import os

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from pyproj import CRS
from shapely import box

import cea.config
from cea.datamanagement import terrain_helper
from cea.inputlocator import InputLocator
from cea.tests.datamanagement.fakes import fake_terrain_tiles, tile_bytes

ZUG_LAT, ZUG_LON = 47.1767, 8.5143


def test_get_tile_number_known_values():
    assert terrain_helper.get_tile_number(0.0, 0.0, 1) == (1, 1)
    assert terrain_helper.get_tile_number(ZUG_LAT, ZUG_LON, 12) == (2144, 1437)


def test_get_all_tile_numbers_single_tile():
    tiles = terrain_helper.get_all_tile_numbers(8.5, 47.17, 8.51, 47.18, 12)
    assert list(tiles) == [(2144, 1437)]


def test_get_all_tile_numbers_spans_grid():
    tiles = list(terrain_helper.get_all_tile_numbers(8.0, 46.8, 9.0, 47.4, 10))
    xs = {x for x, _ in tiles}
    ys = {y for _, y in tiles}
    assert len(tiles) == len(xs) * len(ys)
    assert len(xs) > 1 and len(ys) > 1


def test_merge_raster_tiles_merges_and_reports_tile_info():
    urls = [terrain_helper.URL_FORMAT.format(zoom=12, x=x, y=1436) for x in (2145, 2146)]
    with fake_terrain_tiles() as requested:
        array, transform, meta, tile_info = terrain_helper.merge_raster_tiles(urls)
    assert requested == urls
    assert array.shape[0] == 1
    assert array.shape[2] == 2 * array.shape[1]
    assert [info["url"] for info in tile_info] == urls
    assert tile_info[0]["headers"]["x-amz-meta-x-imagery-sources"] == "fake-source"
    assert meta["crs"] == CRS.from_epsg(3857)


def test_merge_raster_tiles_propagates_http_errors():
    url = terrain_helper.URL_FORMAT.format(zoom=12, x=2145, y=1436)
    with fake_terrain_tiles(fail=True):
        with pytest.raises(RuntimeError):
            terrain_helper.merge_raster_tiles([url])


def test_reproject_raster_array_changes_crs_and_resolution():
    with rasterio.MemoryFile(tile_bytes(12, 2145, 1436)) as memfile, memfile.open() as src:
        array, meta, transform = src.read(), src.meta.copy(), src.transform
    utm = CRS.from_epsg(32632)
    dst_array, dst_transform, dst_meta = terrain_helper.reproject_raster_array(array, transform, meta, utm, 30)
    assert dst_meta["crs"] == utm
    assert abs(dst_transform.a) == pytest.approx(30)
    assert dst_array.shape == (1, dst_meta["height"], dst_meta["width"])
    assert np.nanmax(dst_array) <= 500.0


def test_fetch_tiff_crops_to_requested_bounds():
    bounds_gdf = gpd.GeoDataFrame(geometry=[box(8.505, 47.172, 8.52, 47.18)], crs="EPSG:4326")
    utm = bounds_gdf.estimate_utm_crs()
    min_x, min_y, max_x, max_y = bounds_gdf.to_crs(utm).total_bounds
    with fake_terrain_tiles() as requested:
        array, transform, meta, tile_info = terrain_helper.fetch_tiff(min_x, min_y, max_x, max_y,
                                                                      grid_size=30, src_crs=utm)
    assert len(requested) == len(tile_info) >= 1
    assert meta["crs"] == utm
    assert array.shape == (1, meta["height"], meta["width"])
    assert meta["width"] * 30 == pytest.approx(max_x - min_x, abs=60)
    assert meta["height"] * 30 == pytest.approx(max_y - min_y, abs=60)


def _scenario_with_geometry(tmp_path, with_trees):
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "baseline"
    locator = InputLocator(config.scenario)
    os.makedirs(locator.get_building_geometry_folder(), exist_ok=True)

    wgs84_zone = gpd.GeoDataFrame({"name": ["B1001"]}, geometry=[box(8.5135, 47.1755, 8.5150, 47.1780)],
                                  crs="EPSG:4326")
    wgs84_zone.to_file(locator.get_zone_geometry())
    wgs84_surroundings = gpd.GeoDataFrame({"name": ["CEA1001"]}, geometry=[box(8.5155, 47.1755, 8.5165, 47.1765)],
                                          crs="EPSG:4326")
    wgs84_surroundings.to_file(locator.get_surroundings_geometry())
    if with_trees:
        os.makedirs(locator.get_tree_geometry_folder(), exist_ok=True)
        gpd.GeoDataFrame({"name": ["T1"]}, geometry=[box(8.5120, 47.1750, 8.5125, 47.1755)],
                         crs="EPSG:4326").to_file(locator.get_tree_geometry())
    return config, locator


@pytest.mark.parametrize("with_trees", [False, True])
def test_main_writes_terrain_and_reference(tmp_path, with_trees):
    config, locator = _scenario_with_geometry(tmp_path, with_trees)

    with fake_terrain_tiles() as requested:
        terrain_helper.main(config)

    assert requested
    assert os.path.exists(locator.get_terrain())
    with rasterio.open(locator.get_terrain()) as terrain:
        assert terrain.count == 1
        assert terrain.res[0] == pytest.approx(config.terrain_helper.grid_size)
    reference = os.path.join(os.path.dirname(locator.get_terrain()), "reference.txt")
    with open(reference) as f:
        content = f.read()
    assert requested[0] in content
    assert "fake-source" in content
    assert terrain_helper.ATTRIBUTION_URL in content


def test_trees_extend_the_terrain_extent(tmp_path):
    config, locator = _scenario_with_geometry(tmp_path / "with", with_trees=True)
    config_without, locator_without = _scenario_with_geometry(tmp_path / "without", with_trees=False)
    with fake_terrain_tiles():
        terrain_helper.main(config)
        terrain_helper.main(config_without)
    with rasterio.open(locator.get_terrain()) as with_trees, rasterio.open(locator_without.get_terrain()) as without:
        assert with_trees.bounds.left < without.bounds.left
