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
    # Check validity BEFORE transformation
    invalid_before = data[~data.geometry.is_valid]
    if not invalid_before.empty:
        invalid_names_before = []
        for idx, row in invalid_before.iterrows():
            name = row.get('name', row.get('Name', f'index_{idx}'))
            invalid_names_before.append(str(name))

        invalid_list = ', '.join(invalid_names_before[:10])
        if len(invalid_names_before) > 10:
            invalid_list += f' ... and {len(invalid_names_before) - 10} more'

        raise ValueError(
            f"These geometries must be fixed in the source file: {invalid_list}"
            f"Invalid geometries found in the original shapefile (before CRS transformation). "
        )

    # Transform to WGS84
    data = data.to_crs(get_geographic_coordinate_system())
    valid_geometries = data[data.geometry.is_valid]

    if valid_geometries.empty:
        # All geometries became invalid during transformation
        # This suggests CRS issues or precision problems
        all_names = []
        for idx, row in data.iterrows():
            name = row.get('name', row.get('Name', f'index_{idx}'))
            all_names.append(str(name))

        name_list = ', '.join(all_names[:10])
        if len(all_names) > 10:
            name_list += f' ... and {len(all_names) - 10} more'

        raise ValueError(
            f"All geometries became invalid after CRS transformation to WGS84. "
            f"This typically indicates: (1) missing or incorrect CRS in the shapefile, "
            f"(2) complex geometries with precision issues, or (3) projection distortion. "
            f"Affected geometries: {name_list}. "
            f"Original CRS: {data.crs if hasattr(data, 'crs') else 'Unknown'}"
        )
    elif len(data) != len(valid_geometries):
        # Some geometries became invalid during transformation
        invalid_after = data[~data.geometry.is_valid]
        invalid_names = []
        for idx, row in invalid_after.iterrows():
            name = row.get('name', row.get('Name', f'index_{idx}'))
            invalid_names.append(str(name))

        invalid_list = ', '.join(invalid_names[:10])
        if len(invalid_names) > 10:
            invalid_list += f' ... and {len(invalid_names) - 10} more'

        warnings.warn(
            f"{len(invalid_names)} geometries became invalid after CRS transformation to WGS84 "
            f"(out of {len(data)} total). This may indicate precision issues or projection distortion. "
            f"Invalid geometries: {invalid_list}. Using the first valid geometry for coordinate reference."
        )

    # Use the first valid geometry as representative point
    representative_point = valid_geometries.iloc[0].geometry.representative_point()

    lon = representative_point.x
    lat = representative_point.y

    return lat, lon


def validate_crs_uses_meters(gdf: geopandas.GeoDataFrame, operation: str = "distance calculations") -> None:
    """
    Validate that a GeoDataFrame uses a projected CRS with meter units.
    
    :param gdf: GeoDataFrame to validate
    :param operation: Description of operation requiring meters (for error message)
    :raises ValueError: If CRS is geographic or doesn't use meters
    """
    if gdf.crs is None:
        raise ValueError(f'The GeoDataFrame has no CRS defined. A projected CRS with meter units is required for {operation}.')

    if gdf.crs.is_geographic:
        raise ValueError(
            f'The CRS ({gdf.crs.name}) is geographic (lat/lon). '
            f'A projected CRS with meter units is required for {operation}.'
        )
    
    # Check that units are meters (GeoPandas exposes pyproj's axis_info)
    if not gdf.crs.axis_info:
        raise ValueError(
            f'The CRS does not have axis information defined. '
            f'Current CRS: {gdf.crs.name}. '
            f'Please use a standard projected CRS with meter units (e.g., UTM zone for your region).'
        )

    axis_unit = gdf.crs.axis_info[0].unit_name.lower()
    if axis_unit not in {'metre', 'meter', 'm'}:
        raise ValueError(
            f'The CRS must use meters as its unit for distance calculations. '
            f'Current CRS: {gdf.crs.name}, Unit: {axis_unit}. '
            f'Please reproject to a meter-based CRS (e.g., UTM zone for your region).'
        )
