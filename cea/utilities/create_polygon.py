"""
Creates a polygon shapefile from a list of comma-separated coordinate tuples and places it in building geometry folder
"""

import os
import pandas as pd

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

import geopandas as gpd
from shapely.geometry import Polygon

__author__ = "Reynold Mok"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_polygon(hapefile_df, output_path, filename):

    # Create polygons based on coordinates and zone information for the attribute table
    coordinate_tuple_list = hapefile_df['coordinate'].values.tolist()
    poly = Polygon(coordinate_tuple_list)
    gdf = gpd.GeoDataFrame(hapefile_df, geometry=poly, crs="EPSG:4326")
    # gdf.crs = get_geographic_coordinate_system()

    # Make sure directory exists
    os.makedirs(output_path, exist_ok=True)
    gdf.to_file(os.path.join(output_path, '{filename}.shp'.format(filename=filename)))
    print('Polygon `{filename}` created in {output_path}'.format(filename=filename, output_path=output_path))


def main(config):
    excel_path = config.shapefile_tools.excel_file
    shapefile_df = pd.read_excel(excel_path)

    filename = config.shapefile_tools.filename
    output_path = config.shapefile_tools.shapefile


    create_polygon(shapefile_df, output_path, filename)


if __name__ == '__main__':
    main(cea.config.Configuration())
