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
    validate_geometries_before_crs_transform(data, shapefile_name="shapefile")

    # Transform to WGS84
    original_crs = data.crs
    data = data.to_crs(get_geographic_coordinate_system())

    # Check validity AFTER transformation (returns filtered GeoDataFrame if some are invalid)
    data = validate_geometries_after_crs_transform(data, original_crs, shapefile_name="shapefile")

    if data.empty:
        raise ValueError("No valid geometries remain in shapefile after CRS transformation and filtering.")

    # Use the first valid geometry as representative point
    representative_point = data.iloc[0].geometry.representative_point()

    lon = representative_point.x
    lat = representative_point.y

    return lat, lon


def validate_geometries_before_crs_transform(gdf: geopandas.GeoDataFrame, shapefile_name: str = "shapefile") -> None:
    """
    Validate that all geometries are valid before CRS transformation.

    :param gdf: GeoDataFrame to validate
    :param shapefile_name: Name of shapefile for error messages (e.g., "zone", "streets")
    :raises ValueError: If any geometries are invalid
    """
    invalid_before = gdf[~gdf.geometry.is_valid]
    if not invalid_before.empty:
        invalid_names_before = []
        for idx, row in invalid_before.iterrows():
            name = row.get('name', row.get('Name', f'index_{idx}'))
            invalid_names_before.append(str(name))

        # Show all geometry names
        invalid_list = ', '.join(invalid_names_before)

        raise ValueError(
            f"Invalid geometries found in the original {shapefile_name} (before CRS transformation). "
            f"{len(invalid_names_before)} geometries must be fixed in the source file:\n{invalid_list}"
        )


def validate_geometries_after_crs_transform(gdf: geopandas.GeoDataFrame, original_crs, shapefile_name: str = "shapefile") -> geopandas.GeoDataFrame:
    """
    Validate geometries after CRS transformation and handle invalid cases.

    :param gdf: GeoDataFrame after CRS transformation
    :param original_crs: Original CRS before transformation (for error messages)
    :param shapefile_name: Name of shapefile for error messages (e.g., "zone", "streets")
    :return: GeoDataFrame with only valid geometries (may be filtered)
    :raises ValueError: If all geometries became invalid after transformation
    """
    valid_geometries = gdf.geometry.is_valid

    if not valid_geometries.any():
        # All geometries became invalid during transformation
        all_names = []
        for idx, row in gdf.iterrows():
            name = row.get('name', row.get('Name', f'index_{idx}'))
            all_names.append(str(name))

        # Show all geometry names
        name_list = ', '.join(all_names)

        raise ValueError(
            f"All {len(all_names)} geometries in {shapefile_name} became invalid after CRS transformation. "
            f"This typically indicates: (1) missing or incorrect CRS in the shapefile, "
            f"(2) complex geometries with precision issues, or (3) projection distortion. "
            f"Original CRS: {original_crs}. "
            f"Affected geometries:\n{name_list}"
        )
    elif len(gdf) != valid_geometries.sum():
        # Some geometries became invalid during transformation
        invalid_after = gdf[~gdf.geometry.is_valid]
        invalid_names = []
        for idx, row in invalid_after.iterrows():
            name = row.get('name', row.get('Name', f'index_{idx}'))
            invalid_names.append(str(name))

        # Show all geometry names
        invalid_list = ', '.join(invalid_names)

        warnings.warn(
            f"{len(invalid_names)} geometries in {shapefile_name} became invalid after CRS transformation "
            f"(out of {len(gdf)} total). This may indicate precision issues or projection distortion. "
            f"Invalid geometries:\n{invalid_list}\n"
            f"Discarding invalid geometries and continuing."
        )
        gdf = gdf[gdf.geometry.is_valid]

    return gdf


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
