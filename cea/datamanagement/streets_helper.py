"""
This script extracts streets from Open street maps
"""

import os

import osmnx
import osmnx.utils_graph
import networkx.exception
import pandas as pd

import cea.config
import cea.inputlocator
from cea.datamanagement.surroundings_helper import get_zone_and_surr_in_projected_crs
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_bounding_box(locator):
    # connect both files and avoid repetition
    data_zone, data_dis = get_zone_and_surr_in_projected_crs(locator)
    data_dis = data_dis.loc[~data_dis["name"].isin(data_zone["name"])]
    data = pd.concat([
        data_zone.to_crs(get_geographic_coordinate_system()),
        data_dis.to_crs(get_geographic_coordinate_system())
    ], ignore_index=True, sort=True)
    result = data.total_bounds  # in float
    return result


def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    bool_include_private_streets = config.streets_helper.include_private_streets
    shapefile_out_path = locator.get_street_network()

    # Determine to include private streets or not
    if bool_include_private_streets:
        type_streets = 'all'
    else:
        type_streets = 'all_public'

    # Get the bounding box coordinates
    assert os.path.exists(
        locator.get_surroundings_geometry()), 'Get surroundings geometry file first or the coordinates of the area where to extract the streets from in the next format: lon_min, lat_min, lon_max, lat_max: %s'
    print("generating streets from Surroundings Geometry")
    bounding_box_surroundings_file = calc_bounding_box(locator)
    lon_min = bounding_box_surroundings_file[0]
    lat_min = bounding_box_surroundings_file[1]
    lon_max = bounding_box_surroundings_file[2]
    lat_max = bounding_box_surroundings_file[3]

    # Get and clean the streets
    try:
        G = osmnx.graph_from_bbox(north=lat_max, south=lat_min, east=lon_max, west=lon_min,
                                  network_type=type_streets)
    except (ValueError, networkx.exception.NetworkXPointlessConcept):
        print("Unable to find streets in the area (empty graph returned from Open Street Maps). No streets will be extracted.")
        return
    
    data = osmnx.utils_graph.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    # Project coordinate system
    data = data.to_crs(get_projected_coordinate_system(float(lat_min), float(lon_min)))
    locator.ensure_parent_folder_exists(shapefile_out_path)
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
