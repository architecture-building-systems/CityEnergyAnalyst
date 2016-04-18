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

from shapely.geometry import Polygon, Point
from rtree import index

# TESTING
if __name__ == '__main__':

    # testing building file read
    # **************************
    path_geometry = 'C:/reference-case/baseline/1-inputs/1-buildings/building_geometry.shp'

    building_geometry = gpdf.from_file(path_geometry)

    building_geometry

    print(building_geometry.get_value(0, 'geometry'))

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
