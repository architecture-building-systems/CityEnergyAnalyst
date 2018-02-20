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


def excel_to_shapefile(excel_file, shapefile, index, crs, polygon=True):
    """Expects the Excel file to be in the format created by ``cea shapefile-to-excel``.
    :param polygon: Set this to ``False`` if the Excel file contains polyline data in the ``geometry`` column instead
                     of the default polygon data. (polylines are used for representing streets etc.)
    :type polygon: bool
    """
    df = pd.read_excel(excel_file)
    if polygon:
        geometry = [shapely.geometry.polygon.Polygon(json.loads(g)) for g in df.geometry]
    else:
        geometry = [shapely.geometry.LineString(json.loads(g)) for g in df.geometry]
    df.drop('geometry', axis=1)

    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf.to_file(shapefile, driver='ESRI Shapefile', encoding='ISO-8859-1')


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
    print("Running excel-to-shapefile with excel-file = %s" % config.shapefile_tools.excel_file)
    print("Running excel-to-shapefile with shapefile = %s" % config.shapefile_tools.shapefile)
    print("Running excel-to-shapefile with crs = %s" % config.shapefile_tools.crs)
    print("Running excel-to-shapefile with polygon = %s" % config.shapefile_tools.polygon)

    excel_to_shapefile(excel_file=config.shapefile_tools.excel_file, shapefile=config.shapefile_tools.shapefile,
                       index=config.shapefile_tools.index, crs=config.shapefile_tools.crs,
                       polygon=config.shapefile_tools.polygon)

    print("done.")


if __name__ == '__main__':
    main(cea.config.Configuration())
