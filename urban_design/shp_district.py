# coding=utf-8
"""
Create shapefile from Rhino
"""
from __future__ import division
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from geopandas import GeoDataFrame as gdf


import fiona
import shapely
import gdal

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT ??"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


dataframe_with_gis_info = gdf.from_file(r'F:\Random\reference-case-open\reference-case-open\baseline\inputs\building-geometry/district.shp')

print dataframe_with_gis_info

# Create an empty geopandas GeoDataFrame
district = gpd.GeoDataFrame()

# Create columns called 'geometry', 'height_ag', and 'height_bg" to the GeoDataFrame
district['geometry'] = None
district['height_ag'] = None
district['height_bg'] = None

# Coordinates of the building footprints
coordinates = [(24.950899, 60.169158), (24.953492, 60.169158), (24.953510, 60.170104), (24.950958, 60.169990)]

# Create a Shapely polygon from the coordinate-tuple list
poly = Polygon(coordinates)

# Insert the polygon into 'geometry' -column at index 0
district.loc[0, 'geometry'] = poly

# Insert number into 'height_ag' -column at index 0
district.loc[0, 'height_ag'] = '25.0'

# Insert number into 'height_bg' -column at index 0
district.loc[0, 'height_bg'] = '3.571429'

print district

# Create an output path for the data to zone.shp
out_district=r"C:/reference-case-test/baseline/inputs/building-geometry/district.shp"

# Write zone.shp
dataframe_with_gis_info.to_file(out_district, driver='ESRI Shapefile')