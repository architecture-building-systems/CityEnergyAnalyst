"""
This script extracts streets from Open street maps
"""

import os

import osmnx
import osmnx.utils_graph
from geopandas import GeoDataFrame as Gdf

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_bounding_box(shapefile_surroundings, shapefile_zone):
    # connect both files and avoid repetition
    data_zone = Gdf.from_file(shapefile_zone)
    data_dis = Gdf.from_file(shapefile_surroundings)
    data_dis = data_dis.loc[~data_dis["Name"].isin(data_zone["Name"])]
    data = data_dis.append(data_zone, ignore_index=True, sort=True)
    data = data.to_crs(get_geographic_coordinate_system())
    result = data.total_bounds  # in float
    return result


def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    list_of_bounding_box = config.streets_helper.bbox
    type_of_streets = config.streets_helper.streets
    shapefile_out_path = locator.get_street_network()
    extra_border = 0.0010  # adding extra 150m (in degrees equivalent) to avoid errors of no data

    # get the bounding box coordinates
    if not list_of_bounding_box:
        # the list is empty, we then revert to get the bounding box for the district
        assert os.path.exists(
            locator.get_surroundings_geometry()), 'Get surroundings geometry file first or the coordinates of the area where to extract the streets from in the next format: lon_min, lat_min, lon_max, lat_max: %s'
        print("generating streets from Surroundings Geometry")
        bounding_box_surroundings_file = calc_bounding_box(locator.get_surroundings_geometry(),
                                                           locator.get_zone_geometry())
        lon_min = bounding_box_surroundings_file[0] - extra_border
        lat_min = bounding_box_surroundings_file[1] - extra_border
        lon_max = bounding_box_surroundings_file[2] + extra_border
        lat_max = bounding_box_surroundings_file[3] + extra_border
    elif len(list_of_bounding_box) == 4:
        print("generating streets from your bounding box")
        # the list is not empty, the user has indicated a specific set of coordinates
        lon_min = list_of_bounding_box[0] - extra_border
        lat_min = list_of_bounding_box[1] - extra_border
        lon_max = list_of_bounding_box[2] + extra_border
        lat_max = list_of_bounding_box[3] + extra_border
    else:
        raise ValueError("Please indicate the coordinates of the area where to extract the streets from in the next "
                         "format: lon_min, lat_min, lon_max, lat_max")

    # get and clean the streets
    G = osmnx.graph_from_bbox(north=lat_max, south=lat_min, east=lon_max, west=lon_min,
                              network_type=type_of_streets)
    data = osmnx.utils_graph.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    # project coordinate system
    data = data.to_crs(get_projected_coordinate_system(float(lat_min), float(lon_min)))
    data[['geometry']].to_file(shapefile_out_path)


def main(config):
    """
    Create the streets.shp file.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    geometry_extractor_osm(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
