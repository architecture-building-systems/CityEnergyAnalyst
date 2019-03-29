"""
This script extracts streets from Open street maps
"""
from __future__ import division
from __future__ import print_function

import os

import osmnx as ox
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


def calc_bounding_box(shapefile):
    data = Gdf.from_file(shapefile)
    data = data.to_crs(get_geographic_coordinate_system())
    result = data.total_bounds  # in float
    result = [str(x) for x in result]  # in string
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

    #get the bounding box coordinates
    if list_of_bounding_box == []:
        # the list is empty, we then revert to get the bounding box for the district
        assert os.path.exists(
            locator.get_district_geometry()), 'Get district geometry file first or the coordinates of the area where to extract the streets from in the next format: lon_min, lat_min, lon_max, lat_max: %s'
        print("generating streets from District Geometry")
        bounding_box_district_file = calc_bounding_box(locator.get_district_geometry())
        lon_min = bounding_box_district_file[0]
        lat_min = bounding_box_district_file[1]
        lon_max = bounding_box_district_file[2]
        lat_max = bounding_box_district_file[3]
        crs = get_geographic_coordinate_system()
    elif len(list_of_bounding_box) == 4:
        print("generating streets from your bounding box")
        # the list is not empty, the user has indicated a specific set of coordinates
        lon_min = list_of_bounding_box[0]
        lat_min = list_of_bounding_box[1]
        lon_max = list_of_bounding_box[2]
        lat_max = list_of_bounding_box[3]
    elif len(list_of_bounding_box) != 4:
        raise ValueError(
            "Please indicate the coordinates of the area where to extract the streets from in the next format: lon_min, lat_min, lon_max, lat_max")

    #get and clean the streets
    G = ox.graph_from_bbox(north=float(lat_max), south=float(lat_min), east=float(lon_max), west=float(lon_min),
                           network_type=type_of_streets)
    data = ox.save_load.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    #project coordinate system
    data = data.to_crs(get_projected_coordinate_system(float(lat_min), float(lon_min)))

    #clean data and save to shapefile
    data.loc[:, "highway"] = [x[0] if type(x) == list else x for x in data["highway"].values]
    data.loc[:, "name"] = [x[0] if type(x) == list else x for x in data["name"].values]
    data.fillna(value="Unknown", inplace=True)
    data[['geometry', "name", "highway"]].to_file(shapefile_out_path)

    ##THIS IS ONE METHOD KEEP IT JUST IN CASE. IT IS FUNCTIONAL, BUT LESS EFECTIVE THAN THE ONE ABOVE
    # bounding_box = 'way(' + lat_min + ',' + lon_min + ',' + lat_max + ',' + lon_max + ')'
    # query = bounding_box + '["highway"];(._;>;);out body;'
    # api = overpy.Overpass()
    # # fetch all ways and nodes
    # result = api.query(query)
    # schema = {'geometry': 'LineString', 'properties': {'Name': 'str:80'}}
    # with fiona.open(shapefile_out_path, 'w', crs=crs,
    #                 driver='ESRI Shapefile', schema=schema) as output:
    #     for way in result.ways:
    #         # the shapefile geometry use (lon,lat)
    #         line = {'type': 'LineString', 'coordinates': [(node.lon, node.lat) for node in way.nodes]}
    #         prop = {'Name': way.tags.get("name", "n/a")}
    #         output.write({'geometry': line, 'properties': prop})
    # #project coordinates
    # data = Gdf.from_file(shapefile_out_path)
    # data = data.to_crs(get_projected_coordinate_system(float(lat_min), float(lon_min)))
    # data.to_file(shapefile_out_path)

    # get_projected_coordinate_system(float(lat_min), float(lon_min))


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

    geometry_extractor_osm(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
