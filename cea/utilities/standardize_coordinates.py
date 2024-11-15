import warnings
import os

import geopandas
import utm
from osgeo import gdal, osr


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from pyproj import CRS


def shapefile_to_WSG_and_UTM(shapefile_path):

    # read the CPG and replace whatever is there with ISO, and save
    ensure_cpg_file(shapefile_path)

    # get coordinate system and project to WSG 84
    data = geopandas.read_file(shapefile_path)
    lat, lon = get_lat_lon_projected_shapefile(data)

    # get coordinate system and re project to UTM
    data = data.to_crs(get_projected_coordinate_system(lat, lon))

    return data, lat, lon


def ensure_cpg_file(shapefile_path):
    cpg_file_path = f"{os.path.splitext(shapefile_path)[0]}.cpg"

    if os.path.exists(cpg_file_path):
        with open(cpg_file_path, "r") as cpg_file:
            content = cpg_file.read()
            if content == "ISO-8859-1":
                # already set to ISO-8859-1, nothing to do
                return
    else:
        print(f"No .cpg file found at {cpg_file_path}, creating one")
        
    with open(cpg_file_path, "w") as cpg_file:
        cpg_file.write("ISO-8859-1")

def raster_to_WSG_and_UTM(raster_path, lat, lon):

    raster = gdal.Open(raster_path)
    source_projection_wkt = raster.GetProjection()
    inSRS_converter = osr.SpatialReference()
    inSRS_converter.ImportFromProj4(get_projected_coordinate_system(lat, lon))
    target_projection_wkt = inSRS_converter.ExportToWkt()
    new_raster = gdal.AutoCreateWarpedVRT(raster, source_projection_wkt, target_projection_wkt,
                                          gdal.GRA_NearestNeighbour)
    return new_raster


def get_geographic_coordinate_system():
    return CRS.from_epsg(4326).to_wkt()


def get_projected_coordinate_system(lat, lon):
    easting, northing, zone_number, zone_letter = utm.from_latlon(lat, lon)
    epsg = f"326{zone_number}" if lon >= 0 else f"327{zone_number}"

    return CRS.from_epsg(int(epsg)).to_wkt()


def crs_to_epsg(crs: str) -> int:
    return CRS.from_string(crs).to_epsg()


def get_lat_lon_projected_shapefile(data):
    data = data.to_crs(get_geographic_coordinate_system())
    valid_geometries = data[data.geometry.is_valid]

    if valid_geometries.empty:
        raise ValueError("No valid geometries found in the shapefile")
    elif len(data) != len(valid_geometries):
        warnings.warn("Invalid geometries found in the shapefile. Using the first valid geometry.")

    # Use the first valid geometry as representative point
    representative_point = valid_geometries.iloc[0].geometry.representative_point()

    lon = representative_point.x
    lat = representative_point.y

    return lat, lon
