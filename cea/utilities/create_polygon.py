"""
Creates a polygon shapefile from a list of comma-separated coordinate tuples and places it in building geometry folder
"""

import os

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

import geopandas as gpd
from shapely import Polygon

__author__ = "Reynold Mok"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_polygon(coordinate_tuple_list, output_path, filename):
    poly = Polygon(coordinate_tuple_list)
    gdf = gpd.GeoDataFrame([{'geometry': poly}])
    gdf.crs = get_geographic_coordinate_system()
    # Make sure directory exists
    os.makedirs(output_path, exist_ok=True)
    gdf.to_file(os.path.join(output_path, '{filename}.shp'.format(filename=filename)))
    print('Polygon `{filename}` created in {output_path}'.format(filename=filename, output_path=output_path))


def main(config: cea.config.Configuration):
    coordinate_tuple_list = config.create_polygon.coordinates
    filename = config.create_polygon.filename

    locator = cea.inputlocator.InputLocator(config.scenario)
    output_path = locator.get_building_geometry_folder()

    create_polygon(coordinate_tuple_list, output_path, filename)


if __name__ == '__main__':
    main(cea.config.Configuration())