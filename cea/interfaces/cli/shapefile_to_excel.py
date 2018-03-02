"""
Implements the CEA script ``shapefile-to-excel`` - simpilar how ``dbf-to-excel`` takes a dBase database file (*.dbf) and
converts that to Excel format, this does the same with a Shapefile.

It uses the ``geopandas.GeoDataFrame`` class to read in the shapefile. And serializes the ``geometry`` column to
Excel as well as a serialized list of tuples.
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


def shapefile_to_excel(shapefile, excel_file, index=None):
    """Expects shapefile to be the path to an ESRI Shapefile with the geometry column called ``geometry``."""
    gdf = gpd.GeoDataFrame.from_file(shapefile)
    if index:
        gdf = gdf.set_index(index)
    df = pd.DataFrame(gdf.copy().drop('geometry', axis=1))
    df['geometry'] = gdf.geometry.apply(serialize_geometry)
    df.to_excel(excel_file)


def serialize_geometry(geometry):
    """Take a shapely.geometry.polygon.Polygon and represent it as a string of tuples (x, y)
    :param geometry: a polygon or polyline to extract the points from and represent as a json object
    :type geometry: shapely.geometry.polygon.Polygon
    """
    if isinstance(geometry, shapely.geometry.polygon.Polygon):
        points = list(geometry.exterior.coords)
    elif isinstance(geometry, shapely.geometry.LineString):
        points = list(geometry.coords)
    else:
        raise ValueError("Expected either a Polygon or a LineString, got %s" % type(geometry))
    return json.dumps(points)


def main(config):
    """
    Run :py:func:`shapefile_to_excel` with the values from the configuration file, section `[shapefile-tools]`.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.shapefile_tools.shapefile), (
        'Shapefile not found: %s' % config.shapefile_tools.shapefile)

    # print out all configuration variables used by this script
    print("Running shapefile-to-excel with shapefile = %s" % config.shapefile_tools.shapefile)
    print("Running shapefile-to-excel with excel-file = %s" % config.shapefile_tools.excel_file)
    print("Running shapefile-to-excel with index = %s" % config.shapefile_tools.index)
    print("Running shapefile-to-excel with crs = %s" % config.shapefile_tools.crs)

    shapefile_to_excel(shapefile=config.shapefile_tools.shapefile, excel_file=config.shapefile_tools.excel_file,
                       index=config.shapefile_tools.index)

    print("done.")


if __name__ == '__main__':
    main(cea.config.Configuration())
