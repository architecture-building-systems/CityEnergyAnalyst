"""
Building geometry properties
"""
from __future__ import annotations
from geopandas import GeoDataFrame as Gdf

from cea.datamanagement.databases_verification import COLUMNS_ZONE_GEOMETRY
from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingGeometry:
    """
    Groups building geometry properties used for the calc-thermal-loads functions.
    Stores the full DataFrame for each of the building properties and provides methods for indexing them by name.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building geometry properties from input shape files and construct a new BuildingGeometry object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        prop_geometry = Gdf.from_file(locator.get_zone_geometry())[COLUMNS_ZONE_GEOMETRY + ['geometry']].set_index('name').loc[building_names]

        # reproject to projected coordinate system (in meters) to calculate area
        lat, lon = get_lat_lon_projected_shapefile(prop_geometry)
        target_crs = get_projected_coordinate_system(float(lat), float(lon))
        prop_geometry = prop_geometry.to_crs(target_crs)

        # TODO: Check usage of footprint and perimeter in other parts of the code
        prop_geometry['footprint'] = prop_geometry.area
        prop_geometry['perimeter'] = prop_geometry.length
        prop_geometry['Blength'], prop_geometry['Bwidth'] = self.calc_bounding_box_geom(prop_geometry)

        self._prop_geometry = prop_geometry

    @staticmethod
    def calc_bounding_box_geom(gdf: Gdf) -> tuple[list[float], list[float]]:
        """
        Calculate bounding box dimensions (length and width) for each geometry in the GeoDataFrame.

        :param gdf: A GeoDataFrame containing building geometries.
        :return: Two lists, one for bounding box lengths and another for widths.
        """
        bwidth = []
        blength = []

        for geom in gdf.geometry:
            if geom.is_empty:
                bwidth.append(0)
                blength.append(0)
                continue

            # Get bounding box (xmin, ymin, xmax, ymax)
            xmin, ymin, xmax, ymax = geom.bounds
            delta1 = abs(xmax - xmin)  # Horizontal length
            delta2 = abs(ymax - ymin)  # Vertical width

            # Determine which is length and which is width
            if delta1 >= delta2:
                bwidth.append(delta2)
                blength.append(delta1)
            else:
                bwidth.append(delta1)
                blength.append(delta2)

        return blength, bwidth

    def __getitem__(self, building_name: str) -> dict:
        """Get geometry of a building by name"""
        if building_name not in self._prop_geometry.index:
            raise KeyError(f"Building geometry properties for {building_name} not found")
        return self._prop_geometry.loc[building_name].to_dict()
