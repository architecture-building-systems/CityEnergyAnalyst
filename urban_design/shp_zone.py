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



# define the function to check if a folder exists.
# If so, delete it and make a new one.
# If not, make one.

def mkdir(path):

    import os
    import shutil

    isExists = os.path.exists(path)

    #if the folder not exists, make the folder
    if not isExists:
        os.makedirs(path)

    #if the folder exists, delete is and make a new one
    else:
        shutil.rmtree(path)
        os.makedirs(path)

if __name__ == '__main__':

    import os

    # make folder "reference-case-test"
    mkpath = "C:/reference-case-test/"
    mkdir(mkpath)

    # make the scenario folder tree
    os.makedirs("C:/reference-case-test/baseline/inputs/building-geometry")
    os.makedirs("C:/reference-case-test/baseline/inputs/building-metering")
    os.makedirs("C:/reference-case-test/baseline/inputs/building-properties")
    os.makedirs("C:/reference-case-test/baseline/inputs/topography")

dataframe_with_gis_info = gdf.from_file(r'F:\Random\reference-case-open\reference-case-open\baseline\inputs\building-geometry/zone.shp')

print dataframe_with_gis_info



# Create an empty geopandas GeoDataFrame
zone = gpd.GeoDataFrame()

# Create columns called 'geometry', 'height_ag', and 'height_bg" to the GeoDataFrame
zone['geometry'] = None
zone['height_ag'] = None
zone['height_bg'] = None

# Coordinates of the building footprints
coordinates = [(24.950899, 60.169158), (24.953492, 60.169158), (24.953510, 60.170104), (24.950958, 60.169990)]

# Create a Shapely polygon from the coordinate-tuple list
poly = Polygon(coordinates)

# Insert the polygon into 'geometry' -column at index 0
zone.loc[0, 'geometry'] = poly

# Insert number into 'height_ag' -column at index 0
zone.loc[0, 'height_ag'] = '25.0'

# Insert number into 'height_bg' -column at index 0
zone.loc[0, 'height_bg'] = '3.571429'

print zone

# Create an output path for the data to zone.shp
out_zone=r"C:/reference-case-test/baseline/inputs/building-geometry/zone.shp"

# Write zone.shp
dataframe_with_gis_info.to_file(out_zone, driver='ESRI Shapefile')