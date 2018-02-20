"""
A tool to read the crs of a raster, then convert it json format, for the config file for shapefile generation
"""

from __future__ import division
from __future__ import print_function

import os

import cea.config
import cea.inputlocator
from geopandas import GeoDataFrame as Gdf
from cea.utilities.dbf import dataframe_to_dbf
import shutil
from osgeo import gdal
import pycrs
import pyproj
import osr



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


terrain_path = r'C:\B\baseline\inputs\topography\terrain.tif'

 #apply coordinate system of terrain and convert it to Proj4 format, then print

raster = gdal.Open(terrain_path)
inSRS_wkt = raster.GetProjection()
inSRS_converter = osr.SpatialReference()
inSRS_converter.ImportFromWkt(inSRS_wkt)  # populates the spatial ref object with our WKT SRS
projection_raster = inSRS_converter.ExportToProj4()
#hahaha=projection_raster.to_json()
#fromcrs_proj4 = projection_raster.to_proj4()


print (inSRS_wkt)
print (projection_raster)
#print (hahaha)
