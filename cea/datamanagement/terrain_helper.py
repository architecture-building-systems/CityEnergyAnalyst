import math
import os
from typing import Iterable, Tuple, Dict, Union

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS
from rasterio import MemoryFile
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, Resampling, reproject
from shapely import box

import cea.config
import cea.inputlocator

URL_FORMAT = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff/{zoom}/{x}/{y}.tif"
TILE_CRS = CRS.from_epsg(3857)
DEFAULT_CRS = CRS.from_epsg(4326)


def get_tile_number(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    """
    Converts latitude and longitude to slippy map tile coordinates.
    Reference: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    """
    lat_rad = math.radians(lat)

    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x_tile, y_tile


def get_all_tile_numbers(min_x: float, min_y: float, max_x: float, max_y: float,
                         zoom: int) -> Iterable[Tuple[int, int]]:
    """
    Gets tile numbers based on given bounds.
    """
    # Get tile numbers of bounds
    tile_numbers = {get_tile_number(min_y, min_x, zoom),
                    get_tile_number(min_y, max_x, zoom),
                    get_tile_number(max_y, max_x, zoom),
                    get_tile_number(max_y, min_x, zoom)}

    # Get max and min of tile numbers
    min_x_tile, min_y_tile, max_x_tile, max_y_tile = (None, None, None, None)
    for i, tile_number in enumerate(tile_numbers):
        if i == 0:
            min_x_tile = tile_number[0]
            max_x_tile = tile_number[0]

            min_y_tile = tile_number[1]
            max_y_tile = tile_number[1]

        min_x_tile = min(min_x_tile, tile_number[0])
        max_x_tile = max(max_x_tile, tile_number[0])

        min_y_tile = min(min_y_tile, tile_number[1])
        max_y_tile = max(max_y_tile, tile_number[1])

    # Generate all required tile numbers
    all_tile_numbers = []
    for x in range(min_x_tile, max_x_tile + 1):
        for y in range(min_y_tile, max_y_tile + 1):
            all_tile_numbers.append((x, y))

    return all_tile_numbers


def merge_raster_tiles(tile_urls: Iterable[str]) -> Tuple[np.ndarray, rasterio.Affine, Dict]:
    """
    Merge raster files from tile urls into a single raster.
    """
    rasters = []
    try:
        for tile_url in tile_urls:
            rasters.append(rasterio.open(tile_url))

        # Merge rasters
        dest, transform = merge(rasters)
        meta = rasters[0].meta.copy()
        meta.update({
            "driver": "GTiff",
            "height": dest.shape[1],
            "width": dest.shape[2],
            "transform": transform,
        })
    finally:
        for raster in rasters:
            raster.close()

    return dest, transform, meta


def reproject_raster_array(src_array: np.ndarray, src_transform, meta: Dict,
                           dst_crs: Union[CRS, dict]) -> Tuple[np.ndarray, rasterio.Affine, Dict]:
    """
    Reproject raster array to specified CRS.
    """
    # Get bounds from transform
    minx, miny = src_transform * (0, src_array.shape[2])
    maxx, maxy = src_transform * (src_array.shape[1], 0)

    transform, width, height = calculate_default_transform(
        meta["crs"], dst_crs, src_array.shape[2], src_array.shape[1],
        minx, miny, maxx, maxy
    )

    new_meta = meta.copy()
    new_meta.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })

    dst_array = np.empty((src_array.shape[0], height, width), dtype=src_array.dtype)
    for i in range(src_array.shape[0]):
        reproject(
            source=src_array[i],
            destination=dst_array[i],
            src_transform=src_transform,
            src_crs=meta["crs"],
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )

    return dst_array, transform, new_meta


def fetch_tiff(min_x: float, min_y: float, max_x: float, max_y: float, zoom: int = 12) -> Tuple[np.ndarray, rasterio.Affine, Dict]:

    tile_numbers = get_all_tile_numbers(min_x, min_y, max_x, max_y, zoom)

    # Get merged raster array
    dest, transform, meta = merge_raster_tiles(URL_FORMAT.format(zoom=zoom, x=x, y=y) for x, y in tile_numbers)

    # Reproject raster array to bounds crs
    dest, transform, meta = reproject_raster_array(dest, transform, meta, DEFAULT_CRS)

    # Crop raster based on bounds
    with MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(dest)

            bounding_box = box(min_x, min_y, max_x, max_y)

            out_dest, out_transform = mask(dataset, [bounding_box], crop=True)
            out_meta = dataset.meta.copy()
            out_meta.update({
                "height": out_dest.shape[1],
                "width": out_dest.shape[2],
                "transform": out_transform
            })

    return out_dest, out_transform, out_meta


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # Get total bounds
    zone_df = gpd.read_file(locator.get_zone_geometry())
    surroundings_df = gpd.read_file(locator.get_surroundings_geometry()).to_crs(zone_df.crs)
    total_df = pd.concat([zone_df, surroundings_df])
    total_bounds = total_df.to_crs(DEFAULT_CRS).total_bounds

    dest, transform, meta = fetch_tiff(*total_bounds)

    # Write to disk
    os.makedirs(os.path.dirname(locator.get_terrain()), exist_ok=True)
    with rasterio.open(locator.get_terrain(), "w", **meta) as f:
        f.write(dest)


if __name__ == '__main__':
    main(cea.config.Configuration())
