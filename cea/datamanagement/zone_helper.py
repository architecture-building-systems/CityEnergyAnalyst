"""
This is a template script - an example of how a CEA script should be set up.
NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""
from __future__ import division
from __future__ import print_function


from geopandas import GeoDataFrame as Gdf
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system
import osmnx as ox

import os
import cea.config
import cea.inputlocator
from cea.datamanagement.district_geometry_helper import clean_attributes

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def poly_to_zone(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """
    # local variables:
    poly = Gdf.from_file("C:\Stash\polygon\polygon_selection.shp")
    buildings_height = config.zone_helper.height_ag
    buildings_floors = config.zone_helper.floors_ag
    shapefile_out_path = locator.get_zone_geometry()
    #
    # test = Gdf.from_file("C:\Stash\polygon\polygon_selection.shp")
    #
    # print(test.geometry[0])

    poly = poly.to_crs(get_geographic_coordinate_system())
    lon = poly.geometry[0].centroid.coords.xy[0][0]
    lat = poly.geometry[0].centroid.coords.xy[1][0]
    poly = poly.to_crs(get_projected_coordinate_system(float(lat), float(lon)))


    # get footprints of all the district
    poly = ox.footprints.create_footprints_gdf(polygon=poly['geometry'].values[0])

    # clean attributes of height, name and number of floors
    result = clean_attributes(poly, buildings_height, buildings_floors)
    result = result.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # save to shapefile
    result.to_file(shapefile_out_path)


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.
    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    poly_to_zone(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
