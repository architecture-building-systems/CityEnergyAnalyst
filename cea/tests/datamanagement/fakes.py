"""
Offline stand-ins for the network services used by the zone, surroundings, streets and terrain helpers.
"""
from contextlib import contextmanager
from unittest.mock import patch

import numpy as np
from rasterio import MemoryFile
from rasterio.transform import from_bounds

TILE_SIZE = 16
WEB_MERCATOR_HALF_WORLD = 20037508.342789244


def tile_bounds(zoom: int, x: int, y: int):
    """Bounds (minx, miny, maxx, maxy) of a slippy map tile in EPSG:3857."""
    span = 2 * WEB_MERCATOR_HALF_WORLD / (2 ** zoom)
    minx = -WEB_MERCATOR_HALF_WORLD + x * span
    maxy = WEB_MERCATOR_HALF_WORLD - y * span
    return minx, maxy - span, minx + span, maxy


def tile_bytes(zoom: int, x: int, y: int) -> bytes:
    """A small GeoTIFF covering exactly the given slippy tile, with a gentle slope as elevation."""
    minx, miny, maxx, maxy = tile_bounds(zoom, x, y)
    data = np.tile(np.linspace(400.0, 500.0, TILE_SIZE, dtype="float32"), (TILE_SIZE, 1))
    with MemoryFile() as memfile:
        with memfile.open(driver="GTiff", height=TILE_SIZE, width=TILE_SIZE, count=1, dtype="float32",
                          crs="EPSG:3857", transform=from_bounds(minx, miny, maxx, maxy, TILE_SIZE, TILE_SIZE),
                          nodata=-32768.0) as dst:
            dst.write(data, 1)
        return memfile.read()


class FakeTileResponse:
    headers = {"x-amz-meta-x-imagery-sources": "fake-source", "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"}

    def __init__(self, url: str, fail: bool = False):
        zoom, x, y = self._parse(url)
        self.content = tile_bytes(zoom, x, y)
        self._fail = fail

    @staticmethod
    def _parse(url: str):
        zoom, x, file_name = url.rsplit("/", 3)[1:]
        return int(zoom), int(x), int(file_name.split(".")[0])

    def raise_for_status(self):
        if self._fail:
            raise RuntimeError("fake HTTP error")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@contextmanager
def fake_terrain_tiles(fail: bool = False):
    """Patch ``terrain_helper.requests.get`` so tile downloads are served from memory.

    Yields the list of requested URLs.
    """
    requested = []

    def fake_get(url, *args, **kwargs):
        requested.append(url)
        return FakeTileResponse(url, fail=fail)

    with patch("cea.datamanagement.terrain_helper.requests.get", side_effect=fake_get):
        yield requested


def osm_buildings(geometries, **columns):
    """An OSM-style ``features_from_polygon`` result in EPSG:4326 (``building`` defaults to ``yes``)."""
    import geopandas as gpd

    data = {"building": ["yes"] * len(geometries)}
    data.update(columns)
    return gpd.GeoDataFrame(data, geometry=list(geometries), crs="EPSG:4326")


def fake_features_from_polygon(responses):
    """A stand-in for ``osmnx.features_from_polygon`` serving ``responses`` in call order.

    A response that is an exception instance is raised instead of returned.
    """
    remaining = list(responses)

    def fake(*args, **kwargs):
        response = remaining.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response.copy()

    return fake
