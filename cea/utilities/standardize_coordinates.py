import warnings

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
    # get coordinate system and project to WSG 84
    data = geopandas.read_file(shapefile_path)
    lat, lon = get_lat_lon_projected_shapefile(data)

    # get coordinate system and re project to UTM
    data = data.to_crs(get_projected_coordinate_system(lat, lon))

    return data, lat, lon


def raster_to_WSG_and_UTM(raster_path, lat, lon):
    raster = None
    try:
        raster = gdal.Open(raster_path)
        if raster is None:
            raise ValueError(f"Could not open raster file: {raster_path}")
            
        source_projection_wkt = raster.GetProjection()
        inSRS_converter = osr.SpatialReference()
        inSRS_converter.ImportFromProj4(get_projected_coordinate_system(lat, lon))
        target_projection_wkt = inSRS_converter.ExportToWkt()
        
        new_raster = gdal.AutoCreateWarpedVRT(raster, source_projection_wkt, target_projection_wkt,
                                              gdal.GRA_NearestNeighbour)
        return new_raster
    finally:
        # Properly close the source raster
        if raster is not None:
            raster = None


def get_geographic_coordinate_system():
    return CRS.from_epsg(4326).to_wkt()


def get_projected_coordinate_system(lat, lon):
    easting, northing, zone_number, zone_letter = utm.from_latlon(lat, lon)

    # Calculate EPSG code
    # UTM North zones: 32601-32660
    # UTM South zones: 32701-32760

    is_northern = zone_letter is not None and zone_letter >= 'N'
    epsg = f"326{zone_number:02d}" if is_northern else f"327{zone_number:02d}"

    return CRS.from_epsg(int(epsg)).to_wkt()


def crs_to_epsg(crs: str) -> int:
    epsg = CRS.from_string(crs).to_epsg()
    if epsg is None:
        raise ValueError(f"Could not determine EPSG code for CRS: {crs}")
    return epsg


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
