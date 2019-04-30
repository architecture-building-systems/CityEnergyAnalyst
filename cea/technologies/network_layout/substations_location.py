"""
This script calculates the location of substations in case we do not have it.
it is estimated as the centroid of buildings.
"""

from __future__ import division

from geopandas import GeoDataFrame as gdf
import pandas as pd

from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_substation_location(input_buildings_shp, output_substations_shp, connected_buildings, consider_only_buildings_with_demand=False, type_network="DH", total_demand=False):
    # # get coordinate system and project to WSG 84
    poly = gdf.from_file(input_buildings_shp)
    if connected_buildings != []:
        # get only buildings described
        poly = poly.loc[poly['Name'].isin(connected_buildings)]
        poly = poly.reset_index(drop=True)

    # get only buildings with a demand, send out a message if there are less than 2 buildings.
    if consider_only_buildings_with_demand:
        total_demand = pd.read_csv(total_demand)
        if type_network == "DH":
            field = "QH_sys_MWhyr"
        elif type_network == "DC":
            field = "QC_sys_MWhyr"
        buildings_with_load_df = total_demand[total_demand[field] > 0.0]
        if buildings_with_load_df.shape[0] >= 2:
            buildings_with_load = buildings_with_load_df['Name'].tolist()
            poly = poly.loc[poly['Name'].isin(buildings_with_load)]
            poly = poly.reset_index(drop=True)
        else:
            raise Exception("We could not find two or more buildings with thermal energy deamand for cooling or heating,"
                      " the network layout will not work unless the buildings_with_demand parameter is set to False")

    poly = poly.to_crs(get_geographic_coordinate_system())
    lon = poly.geometry[0].centroid.coords.xy[0][0]
    lat = poly.geometry[0].centroid.coords.xy[1][0]

    # get coordinate system and re project to UTM
    poly = poly.to_crs(get_projected_coordinate_system(lat, lon))

    # create points
    points = poly.copy()
    points.geometry = poly['geometry'].centroid

    # saving result
    points.to_file(output_substations_shp, driver='ESRI Shapefile')

    return points, poly
