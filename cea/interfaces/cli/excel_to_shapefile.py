"""
Implements the CEA script ``excel-to-shapefile`` - simpilar how ``excel-to-dbf`` takes a dBase database file (*.dbf) and
converts that to Excel format, this does the same with a Shapefile.

It uses the ``geopandas.GeoDataFrame`` class to read in the shapefile. The geometry column is serialized to a nested
list of coordinates using the JSON notation.
"""
from __future__ import division
from __future__ import print_function

import os
import shapely
import json
import pandas as pd
import geopandas as gpd

import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def excel_to_shapefile(excel_file, shapefile, index, crs):
    """Expects the Excel file to be in the format created by ``cea shapefile-to-excel``."""
    df = pd.read_excel(excel_file).set_index(index)
    geometry = [shapely.geometry.polygon.Polygon(json.loads(g)) for g in df.geometry]
    df.drop('geometry', axis=1)

    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf.to_file(shapefile, driver='ESRI Shapefile')


def string_polygon(polygon):
    """Take a shapely.geometry.polygon.Polygon and represent it as a string of tuples (x, y)
    :param polygon: a polygon to extract the points from and represent as a json object
    :type polygon: shapely.geometry.polygon.Polygon
    """
    assert isinstance(polygon, shapely.geometry.polygon.Polygon)
    points = list(polygon.exterior.coords)
    return json.dumps(points)

def main(config):
    """
    Run :py:func:`excel_to_shapefile` with the values from the configuration file, section ``[shapefile-tools]``.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.shapefile_tools.excel_file), (
        'Excel file not found: %s' % config.shapefile_tools.shapefile)

    # print out all configuration variables used by this script
    print("Running shapefile-to-excel with shapefile = %s" % config.shapefile_tools.shapefile)
    print("Running shapefile-to-excel with excel-file = %s" % config.shapefile_tools.excel_file)
    print("Running shapefile-to-excel with index = %s" % config.shapefile_tools.index)
    print("Running shapefile-to-excel with crs = %s" % config.shapefile_tools.crs)

    excel_to_shapefile(excel_file=config.shapefile_tools.excel_file, shapefile=config.shapefile_tools.shapefile,
                       index=config.shapefile_tools.index, crs=config.shapefile_tools.crs)

    print("done.")


if __name__ == '__main__':
    main(cea.config.Configuration())
