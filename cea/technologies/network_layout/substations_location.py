"""
This script calculates the location of substations in case we do not have it.
it is estimated as the centroid of buildings.
"""





import pandas as pd
from geopandas import GeoDataFrame as gdf
from shapely import Point
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_lat_lon_projected_shapefile
from cea.constants import SHAPEFILE_TOLERANCE
__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_building_centroids(input_buildings_shp,
                            list_district_scale_buildings,
                            plant_buildings,
                            consider_only_buildings_with_demand=False,
                            type_network="DH",
                            total_demand=False):
    # # get coordinate system and project to WSG 84
    zone_df = gdf.from_file(input_buildings_shp)
    zone_df = zone_df.loc[zone_df['name'].isin(list_district_scale_buildings + plant_buildings)]
    zone_df = zone_df.reset_index(drop=True)

    # get only buildings with a demand, send out a message if there are less than 2 buildings.
    if consider_only_buildings_with_demand:
        total_demand = pd.read_csv(total_demand)
        if type_network == "DH":
            field = "QH_sys_MWhyr"
        elif type_network == "DC":
            field = "QC_sys_MWhyr"
        buildings_with_load = total_demand[total_demand[field] > 0.0].name.tolist()
        selected_buildings = list(set(buildings_with_load).union(set(plant_buildings)))
        if len(selected_buildings) >= 2:
            zone_df = zone_df.loc[zone_df['name'].isin(selected_buildings)]
            zone_df = zone_df.reset_index(drop=True)
        else:
            raise Exception("We could not find two or more buildings with thermal energy demand the network layout "
                            "will not work unless the consider_only_buildings_with_demand parameter is set to False")

    # get coordinate system and re project to UTM
    lat, lon = get_lat_lon_projected_shapefile(zone_df)
    zone_df = zone_df.to_crs(get_projected_coordinate_system(lat, lon))

    # create points with centroid
    points = zone_df.copy()
    points.geometry = zone_df['geometry'].centroid

    # # decrease the number of units of the points
    building_centroids_df = simplify_points_accurracy(points, SHAPEFILE_TOLERANCE, points.crs)

    return building_centroids_df

def simplify_points_accurracy(buiding_centroids, decimals, crs):
    new_points = []
    names = []
    for point, name in zip(buiding_centroids.geometry, buiding_centroids.name):
        x = round(point.x, decimals)
        y = round(point.y, decimals)
        new_points.append(Point(x, y))
        names.append(name)
    df = gdf(geometry=new_points, crs=crs)
    df["name"] = names
    return df
