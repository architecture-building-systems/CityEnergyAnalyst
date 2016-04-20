"""
============================================
Window Generator
============================================

@author: happle@arch.ethz.ch

April 2016

"""

from __future__ import division
import geopandas
import rtree

from geopandas import GeoDataFrame as gpdf
import descartes
from matplotlib import pyplot

import gdal
import struct

from shapely.geometry import Polygon, Point
from rtree import index

import arcpy


def building_footprint_real_to_box(building_footprint_real ):

    # building_footprint_real: shape file containing building real footprint

    footprint_box = building_footprint_real.geometry.envelope
    # TODO: find smallest box with real orientation

    building_footprint_box = building_footprint_real # copy shape file
    building_footprint_box.geometry = footprint_box # change geometry from real footprint to box

    return building_footprint_box

def building_centroid_DEM_height( building, dem ):

    # code inspired by: http://www.gis.usu.edu/~chrisg/python/2009/lectures/ospy_slides4.pdf


    building_centroid = building.geometry.centroid

    # get dem raster size
    size_x = dem.RasterXSize
    size_y = dem.RasterYSize

    # get geo reference matrix
    georef = dem.GetGeoTransform()
    origin_x = georef[0]
    origin_y = georef[3]
    pixel_width = georef[1]
    pixel_height = georef[5]

    # for all building footprint centroids
    for i in range(0,building_centroid.size):

        # get centroid coordinates
        x = building_centroid.get_value(i).x
        y = building_centroid.get_value(i).y

        # compute pixel offset
        offset_x = int((x - origin_x) / pixel_width)
        offset_y = int((y - origin_y) / pixel_height)

        # read the height at the building centroid
        data = band.ReadAsArray(offset_x, offset_y, 1, 1)
        value = data[0, 0]

        print(value)


    return





# TESTING
if __name__ == '__main__':

    # testing building file read
    # **************************
    path_geometry = 'C:/reference-case/baseline/1-inputs/1-buildings/building_geometry.shp'

    building_geometry = gpdf.from_file(path_geometry)

    path_dem = 'C:/reference-case/baseline/1-inputs/2-terrain/terrain/w001001.adf'

    gdal_layer = gdal.Open(path_dem) # http://www.itopen.it/how-to-read-a-raster-cell-with-python-qgis-and-gdal/

    print(gdal_layer.GetMetadata())

    gt = gdal_layer.GetGeoTransform() # get geo transform matrix

    print(gt)

    # get image size
    rows = gdal_layer.RasterYSize
    cols = gdal_layer.RasterXSize
    bands = gdal_layer.RasterCount
    print(rows, cols, bands)

    xo, xs, xr, yo, yr, ys = gt
    band = gdal_layer.GetRasterBand(1)
    gdal_value = struct.unpack('f', band.ReadRaster(1, 1, 1, 1, buf_type=band.DataType))[0]


    print(gdal_value)

    building_geometry

    print(building_geometry.head(1))

    print(building_geometry.get_value(0, 'geometry'))

    building_footprint_box = building_footprint_real_to_box(building_geometry)

    print(building_footprint_box.get_value(0, 'geometry'))
    print(building_footprint_box.head(1))

    building_centroid_DEM_height(building_footprint_box, gdal_layer)

    building_geometry.plot()

    # testing some code with rtree from stackoverflow
    # ***********************************************

    # List of non-overlapping polygons
    polygons = [
        Polygon([(0, 0), (0, 1), (1, 1), (0, 0)]),
        Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
    ]

    # Populate R-tree index with bounds of polygons
    idx = index.Index()
    for pos, poly in enumerate(polygons):
        idx.insert(pos, poly.bounds)

    # Query a point to see which polygon it is in
    # using first Rtree index, then Shapely geometry's within
    point = Point(0.5, 0.2)
    poly_idx = [i for i in idx.intersection((point.coords[0]))
                if point.within(polygons[i])]
    for num, idx in enumerate(poly_idx, 1):
        print("%d:%d:%s" % (num, idx, polygons[idx]))
