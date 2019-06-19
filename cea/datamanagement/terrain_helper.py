"""
This script extracts terrain elevation from NASA - SRTM
https://www2.jpl.nasa.gov/srtm/
"""
from __future__ import division
from __future__ import print_function

import os

import gdal
import numpy as np
import pandas as pd
import requests
from geopandas import GeoDataFrame as Gdf
from osgeo import ogr
from osgeo import osr
from shapely.geometry import Polygon

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def request_elevation(lon, lat):
    # script for returning elevation from lat, long, based on open elevation data
    # which in turn is based on SRTM
    query = ('https://api.open-elevation.com/api/v1/lookup?locations=' + str(lat) + ',' + str(lon))
    r = requests.get(query).json()  # json object, various ways you can extract value
    # one approach is to use pandas json functionality:
    elevation = pd.io.json.json_normalize(r, 'results')['elevation'].values[0]
    return elevation


def calc_bounding_box_projected_coordinates(shapefile_zone, shapefile_district):

    #connect both files and avoid repetition
    data_zone = Gdf.from_file(shapefile_zone)
    data_dis = Gdf.from_file(shapefile_district)
    data_dis = data_dis.loc[~data_dis["Name"].isin(data_zone["Name"])]
    data = data_dis.append(data_zone, ignore_index = True, sort=True)
    data = data.to_crs(get_geographic_coordinate_system())
    lon = data.geometry[0].centroid.coords.xy[0][0]
    lat = data.geometry[0].centroid.coords.xy[1][0]
    crs = get_projected_coordinate_system(float(lat), float(lon))
    data = data.to_crs(get_projected_coordinate_system(float(lat), float(lon)))
    result = data.total_bounds
    result = [np.float32(x) for x in result]  # in float32 so the raster works
    return result, crs, lon, lat


def terrain_elevation_extractor(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    elevation = config.terrain_helper.elevation
    grid_size = config.terrain_helper.grid_size
    extra_border = np.float32(30)  # adding extra 30 m to avoid errors of no data
    raster_path = locator.get_terrain()

    # get the bounding box coordinates
    assert os.path.exists(
        locator.get_district_geometry()), 'Get district geometry file first or the coordinates of the area where' \
                                          ' to extract the terrain from in the next format: lon_min, lat_min, lon_max, lat_max'
    print("generating terrain from District area")
    bounding_box_district_file, crs, lon, lat = calc_bounding_box_projected_coordinates(locator.get_district_geometry(), locator.get_zone_geometry())
    x_min = bounding_box_district_file[0] - extra_border
    y_min = bounding_box_district_file[1] - extra_border
    x_max = bounding_box_district_file[2] + extra_border
    y_max = bounding_box_district_file[3] + extra_border

    # make sure output is a whole number when min-max is divided by grid size
    x_extra = grid_size - ((x_max - x_min) % grid_size)/2
    y_extra = grid_size - ((y_max - y_min) % grid_size)/2
    x_min -= x_extra
    y_min -= y_extra
    x_max += x_extra
    y_max += y_extra

    ##TODO: get the elevation from satellite data. Open-elevation was working, but the project is dying.
    # if elevation is None:
    #     print('extracting elevation from satellite data, this needs connection to the internet')
    #     elevation = request_elevation(lon, lat)
    #     print("Proceeding to calculate terrain file with fixed elevation in m of ", elevation)
    # else:
    #     print("Proceeding to calculate terrain file with fixed elevation in m of ",elevation)

    print("Proceeding to calculate terrain file with fixed elevation in m of ", elevation)

    # now calculate the raster with the fixed elevation
    calc_raster_terrain_fixed_elevation(crs, elevation, grid_size, raster_path, locator,
                                        x_max, x_min, y_max, y_min)


def calc_raster_terrain_fixed_elevation(crs, elevation, grid_size, raster_path, locator, x_max, x_min, y_max,
                                        y_min):
    # local variables:
    temp_shapefile = locator.get_temporary_file("terrain.shp")
    cols = int((x_max - x_min) / grid_size)
    rows = int((y_max - y_min) / grid_size)
    shapes = Polygon([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max], [x_min, y_min]])
    geodataframe = Gdf(index=[0], crs=crs, geometry=[shapes])
    geodataframe.to_file(temp_shapefile)
    # 1) opening the shapefile
    source_ds = ogr.Open(temp_shapefile)
    source_layer = source_ds.GetLayer()
    target_ds = gdal.GetDriverByName('GTiff').Create(raster_path, cols, rows, 1, gdal.GDT_Float32)  ##COMMENT 2
    target_ds.SetGeoTransform((x_min, grid_size, 0, y_max, 0, -grid_size))  ##COMMENT 3
    # 5) Adding a spatial reference ##COMMENT 4
    target_dsSRS = osr.SpatialReference()
    target_dsSRS.ImportFromProj4(crs)
    target_ds.SetProjection(target_dsSRS.ExportToWkt())
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(-9999)  ##COMMENT 5
    gdal.RasterizeLayer(target_ds, [1], source_layer, burn_values=[elevation])  ##COMMENT 6
    target_ds = None  # closing the file


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    terrain_elevation_extractor(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
