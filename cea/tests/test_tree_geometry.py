"""Trees are extruded with the same `process_geometries` the buildings use, so they have to
follow its signature: a tree is one solid from the ground to the top of its canopy."""

import geopandas as gpd
import numpy as np
from osgeo import gdal, osr
from shapely.geometry import box

from cea.resources.radiation.geometry_generator import tree_geometry_generator

EPSG = 32632


def flat_terrain(size=20, cell=5.0, elevation=10.0):
    raster = gdal.GetDriverByName('MEM').Create('', size, size, 1, gdal.GDT_Float32)
    raster.SetGeoTransform((0.0, cell, 0.0, size * cell, 0.0, -cell))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    raster.SetProjection(srs.ExportToWkt())
    band = raster.GetRasterBand(1)
    band.SetNoDataValue(-9999.0)
    band.WriteArray(np.full((size, size), elevation, dtype=np.float32))
    return raster


def test_each_tree_becomes_a_closed_set_of_surfaces():
    trees = gpd.GeoDataFrame(
        {'height_tc': [6.0, 9.0]},
        geometry=[box(40, 40, 44, 44), box(60, 60, 63, 63)],
        crs=f'EPSG:{EPSG}',
    )

    surfaces = tree_geometry_generator(trees, flat_terrain())

    assert len(surfaces) == 2
    # a box extruded from the ground to the canopy top: 4 sides + top + bottom
    assert all(len(faces) == 6 for faces in surfaces)


def test_a_tree_of_no_height_is_skipped():
    trees = gpd.GeoDataFrame(
        {'height_tc': [0.0, 6.0]},
        geometry=[box(40, 40, 44, 44), box(60, 60, 63, 63)],
        crs=f'EPSG:{EPSG}',
    )
    assert len(tree_geometry_generator(trees, flat_terrain())) == 1
