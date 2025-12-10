import os
import warnings

import fiona
import geopandas as gpd
from osgeo import gdal, osr

import cea.config
import cea.inputlocator
from cea.schemas import schemas


def check_terrain_bounds(tree_geometries, terrain_raster):
    terrian_projection = terrain_raster.GetProjection()
    proj4_str = osr.SpatialReference(wkt=terrian_projection).ExportToProj4()

    # minx, miny, maxx, maxy
    geometry_bounds = tree_geometries.to_crs(proj4_str).total_bounds

    (upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = terrain_raster.GetGeoTransform()
    minx = upper_left_x
    maxy = upper_left_y
    maxx = minx + x_size * terrain_raster.RasterXSize
    miny = maxy + y_size * terrain_raster.RasterYSize

    if minx > geometry_bounds[0] or miny > geometry_bounds[1] or maxx < geometry_bounds[2] or maxy < \
            geometry_bounds[3]:
        warnings.warn("Terrain and trees geometries do not overlap. Please ")


def verify_tree_properties(tree_df):
    required_columns = schemas(plugins=[])["get_tree_geometry"]["schema"]["columns"].keys()
    diff = required_columns - tree_df.columns

    if len(diff) > 0:
        raise ValueError(f"{diff} columns are missing for tree properties.")


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(config.scenario)

    trees_df = gpd.read_file(config.trees_helper.trees)
    terrain_raster = gdal.Open(locator.get_terrain())

    # Set trees to zone crs
    with fiona.open(locator.get_zone_geometry(), 'r') as f:
        zone_crs = f.crs
    trees_df.to_crs(zone_crs, inplace=True)

    verify_tree_properties(trees_df)
    check_terrain_bounds(trees_df.geometry, terrain_raster)

    os.makedirs(locator.get_tree_geometry_folder(), exist_ok=True)
    trees_df.to_file(locator.get_tree_geometry())


if __name__ == '__main__':
    main(cea.config.Configuration())
