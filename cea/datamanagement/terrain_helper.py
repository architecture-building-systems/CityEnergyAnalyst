import datetime
import io
import math
import os
from typing import Iterable, Tuple, Dict, Union, List

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from pyproj import CRS
from rasterio import MemoryFile
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.transform import array_bounds
from rasterio.warp import calculate_default_transform, Resampling, reproject
from shapely import box

import cea.config
import cea.inputlocator

URL_FORMAT = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff/{zoom}/{x}/{y}.tif"
TILE_CRS = CRS.from_epsg(3857)
DEFAULT_CRS = CRS.from_epsg(4326)

DATA_SOURCE_URL = "https://github.com/tilezen/joerd/blob/master/docs/data-sources.md"
ATTRIBUTION_URL = "https://github.com/tilezen/joerd/blob/master/docs/attribution.md"

ATTRIBUTION = """
* ArcticDEM terrain data DEM(s) were created from DigitalGlobe, Inc., imagery and
  funded under National Science Foundation awards 1043681, 1559691, and 1542736;
* Australia terrain data © Commonwealth of Australia (Geoscience Australia) 2017;
* Austria terrain data © offene Daten Österreichs – Digitales Geländemodell (DGM)
  Österreich;
* Canada terrain data contains information licensed under the Open Government
  Licence – Canada;
* Europe terrain data produced using Copernicus data and information funded by the
  European Union - EU-DEM layers;
* Global ETOPO1 terrain data U.S. National Oceanic and Atmospheric Administration
* Mexico terrain data source: INEGI, Continental relief, 2016;
* New Zealand terrain data Copyright 2011 Crown copyright (c) Land Information New
  Zealand and the New Zealand Government (All rights reserved);
* Norway terrain data © Kartverket;
* United Kingdom terrain data © Environment Agency copyright and/or database right
  2015. All rights reserved;
* United States 3DEP (formerly NED) and global GMTED2010 and SRTM terrain data
  courtesy of the U.S. Geological Survey.
"""


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


def merge_raster_tiles(tile_urls: Iterable[str]) -> Tuple[np.ndarray, rasterio.Affine, Dict, List[Dict]]:
    """
    Merge raster files from tile urls into a single raster.
    """
    rasters = []
    tile_info = []
    try:
        for tile_url in tile_urls:
            with requests.get(tile_url, stream=True) as r:
                r.raise_for_status()
                data = io.BytesIO(r.content)

            # Load raster data using rasterio
            raster = rasterio.open(data)
            rasters.append(raster)

            # Store tile info
            tile_info.append({
                "url": tile_url,
                "headers": r.headers
            })

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

    return dest, transform, meta, tile_info


def reproject_raster_array(src_array: np.ndarray, src_transform, meta: Dict,
                           dst_crs: Union[CRS, dict], grid_size: int) -> Tuple[np.ndarray, rasterio.Affine, Dict]:
    """
    Reproject raster array to specified CRS.
    """
    # Get bounds from transform
    minx, miny, maxx, maxy = array_bounds(src_array.shape[1], src_array.shape[2], src_transform)

    transform, width, height = calculate_default_transform(
        meta["crs"], dst_crs, src_array.shape[2], src_array.shape[1],
        minx, miny, maxx, maxy,
        resolution=grid_size
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
            resampling=Resampling.nearest,
            src_nodata=meta["nodata"],
            dst_nodata=meta["nodata"],
        )

    return dst_array, transform, new_meta


def fetch_tiff(min_x: float, min_y: float, max_x: float, max_y: float, zoom: int = 12, grid_size: int = 30,
               src_crs: Union[CRS, dict] = DEFAULT_CRS) -> Tuple[np.ndarray, rasterio.Affine, Dict, List[Dict]]:
    """
    Fetch raster data array based on bounds in the given source CRS (Default: lat, lon).
    The resulting raster data would also be in the given source CRS.
    Also returns the info of the tile that were fetched.
    """

    bounding_box = gpd.GeoDataFrame(geometry=[box(min_x, min_y, max_x, max_y)], crs=src_crs)
    print(f"Generating raster based on bounds: ({min_x}, {min_y}, {max_x}, {max_y}), {src_crs}")

    # Fetch tile numbers based on lat lon bounds
    reprojected_bounds = bounding_box.to_crs(DEFAULT_CRS).total_bounds
    tile_numbers = get_all_tile_numbers(*reprojected_bounds, zoom)

    # Get merged raster array
    tile_urls = [URL_FORMAT.format(zoom=zoom, x=x, y=y) for x, y in tile_numbers]
    dest, transform, meta, tile_info = merge_raster_tiles(tile_urls)

    # Reproject raster array to bounds crs
    dest, transform, meta = reproject_raster_array(dest, transform, meta, src_crs, grid_size)

    # Crop raster based on bounds
    with MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(dest)

            out_dest, out_transform = mask(dataset, bounding_box.geometry, crop=True)
            out_meta = dataset.meta.copy()
            out_meta.update({
                "height": out_dest.shape[1],
                "width": out_dest.shape[2],
                "transform": out_transform
            })

    return out_dest, out_transform, out_meta, tile_info


def main(config: cea.config.Configuration):
    grid_size = config.terrain_helper.grid_size
    buffer = config.terrain_helper.buffer
    locator = cea.inputlocator.InputLocator(config.scenario)

    # Get total bounds
    zone_df = gpd.read_file(locator.get_zone_geometry())
    surroundings_df = gpd.read_file(locator.get_surroundings_geometry()).to_crs(zone_df.crs)
    trees_df = gpd.read_file(locator.get_tree_geometry()).to_crs(zone_df.crs) if (
        os.path.exists(locator.get_tree_geometry())
    ) else gpd.GeoDataFrame(geometry=[], crs=zone_df.crs)
    total_df = gpd.GeoDataFrame(pd.concat([zone_df.geometry, surroundings_df.geometry, trees_df.geometry]))
    total_bounds = total_df.total_bounds

    # Add buffer to bounds in meters (using projected crs), to ensure overlap
    projected_crs = total_df.estimate_utm_crs()
    reprojected_bounds_df = gpd.GeoDataFrame(geometry=[box(*total_bounds)], crs=zone_df.crs).to_crs(projected_crs)
    buffer_df = reprojected_bounds_df.buffer(buffer)
    min_x, min_y, max_x, max_y = buffer_df.total_bounds

    # Fetch tiff data
    dest, transform, meta, tile_info = fetch_tiff(min_x, min_y, max_x, max_y,
                                                  grid_size=grid_size, src_crs=buffer_df.crs)

    os.makedirs(os.path.dirname(locator.get_terrain()), exist_ok=True)
    # Write reference file
    reference_file = os.path.join(os.path.dirname(locator.get_terrain()), "reference.txt")
    tile_info_string = '\n'.join([
        f"url: {info['url']}\n"
        f"data sources: {info['headers']['x-amz-meta-x-imagery-sources']}\n"
        f"last modified: {info['headers']['Last-Modified']}\n" for info in tile_info
    ])
    content = (f"Citation:\n"
               f"Terrain Tiles was accessed on {datetime.datetime.now().date()} "
               f"from https://registry.opendata.aws/terrain-tiles.\n"
               f"\n"
               f"Information of tiles used:\n"
               f"{tile_info_string}\n"
               f"Acknowledgement of Data Sources:"
               f"{ATTRIBUTION}\n"
               f"For more information about the data:\n"
               f"Data sources: {DATA_SOURCE_URL}\n"
               f"Attribution: {ATTRIBUTION_URL}\n")

    with open(reference_file, "w") as f:
        f.write(content)
    print(f"\n{content}")
    print(f"Reference file is written to: {reference_file}")

    # Write to disk
    with rasterio.open(locator.get_terrain(), "w", **meta) as f:
        f.write(dest)


if __name__ == '__main__':
    main(cea.config.Configuration())
