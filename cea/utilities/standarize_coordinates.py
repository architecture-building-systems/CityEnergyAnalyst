from __future__ import division
import utm
import gdal
import osr
from geopandas import GeoDataFrame as gdf

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def shapefile_to_WSG_and_UTM(shapefile_path):

    #read the CPG and repalce whateever is there with ISO, and save
    cpg_file_path = shapefile_path.split('.shp', 1)[0] + '.CPG'
    cpg_file = open(cpg_file_path, "w")
    cpg_file.write("ISO-8859-1")
    cpg_file.close()

    # get coordinate system and project to WSG 84
    data = gdf.from_file(shapefile_path)
    data = data.to_crs(get_geographic_coordinate_system())
    data = data.to_crs(get_projected_coordinate_system())

    return data

def raster_to_WSG_and_UTM(raster_path):

    raster = gdal.Open(raster_path)
    source_projection_wkt = raster.GetProjection()
    inSRS_converter = osr.SpatialReference()
    inSRS_converter.ImportFromProj4(get_projected_coordinate_system())
    target_projection_wkt = inSRS_converter.ExportToWkt()
    new_raster = gdal.AutoCreateWarpedVRT(raster, source_projection_wkt, target_projection_wkt,
                                          gdal.GRA_NearestNeighbour)
    return new_raster

def get_geographic_coordinate_system():
    return "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

def get_projected_coordinate_system():
    return "+proj=merc +a=6378137.0 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +ellps=WGS84 +datum=WGS84 +units=m +nadgrids=@null +wktext  +no_defs"