"""
This is a template script - an example of how a CEA script should be set up.
NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

import math
import os

import numpy as np
import osmnx.footprints
from geopandas import GeoDataFrame as Gdf
import pandas as pd

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import COLUMNS_ZONE_TYPOLOGY
from cea.demand import constants
from cea.datamanagement.constants import OSM_BUILDING_CATEGORIES, OTHER_OSM_CATEGORIES_UNCONDITIONED
from cea.utilities.dbf import dataframe_to_dbf
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca", "Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def parse_building_floors(floors):
    """
    Tries to parse string of `building:levels` from OSM data to get the number of floors as a float.
    If the string is a list of numerical values separated by commas or semicolons, it will return the maximum value.
    It returns NaN if it is unable to parse the value.

    :param str floors: String representation of number of floors from OSM
    :return: Number of floors as a float or NaN
    """
    import re
    try:
        parsed_floors = float(floors)  # Try casting string to float
    except ValueError:
        separators = [',', ';']  # Try matching with different separators
        separated_values = r'^(?:\d+(?:\.\d+)?(?:{separator}\s?)?)+$'
        for separator in separators:
            match = re.match(separated_values.format(separator=separator), floors)
            if match:
                return max([float(x.strip() or 0) for x in floors.split(separator)])
        return np.nan
    else:
        return parsed_floors



def clean_attributes(shapefile, buildings_height, buildings_floors, buildings_height_below_ground,
                     buildings_floors_below_ground, key):
    # local variables
    no_buildings = shapefile.shape[0]
    list_of_columns = shapefile.columns
    if buildings_height is None and buildings_floors is None:
        print('Warning! you have not indicated a height or number of floors above ground for the buildings, '
              'we are reverting to data stored in Open Street Maps (It might not be accurate at all),'
              'if we do not find data in OSM for a particular building, we get the median in the surroundings, '
              'if we do not get any data we assume 4 floors per building')

        # Check which attributes the OSM has, Sometimes it does not have any and indicate the data source
        if 'building:levels' not in list_of_columns:
            shapefile['building:levels'] = [3] * no_buildings
            shapefile['REFERENCE'] = "CEA - assumption"
        elif pd.isnull(shapefile['building:levels']).all():
            shapefile['building:levels'] = [3] * no_buildings
            shapefile['REFERENCE'] = "CEA - assumption"
        else:
            shapefile['REFERENCE'] = ["OSM - median values of all buildings" if x is np.nan else "OSM - as it is" for x
                                      in shapefile['building:levels']]
        if 'roof:levels' not in list_of_columns:
            shapefile['roof:levels'] = 0

        # get the median from the area:
        data_osm_floors1 = shapefile['building:levels'].fillna(0)
        data_osm_floors2 = shapefile['roof:levels'].fillna(0)
        data_floors_sum = [x + y for x, y in zip([parse_building_floors(x) for x in data_osm_floors1],
                                                 [parse_building_floors(x) for x in data_osm_floors2])]
        data_floors_sum_with_nan = [np.nan if x < 1.0 else x for x in data_floors_sum]
        data_osm_floors_joined = math.ceil(
            np.nanmedian(data_floors_sum_with_nan))  # median so we get close to the worse case
        shapefile["floors_ag"] = [int(x) if not np.isnan(x) else data_osm_floors_joined for x in
                                  data_floors_sum_with_nan]
        shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F
    else:
        shapefile['REFERENCE'] = "User - assumption"
        if buildings_height is None and buildings_floors is not None:
            shapefile["floors_ag"] = [buildings_floors] * no_buildings
            shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F
        elif buildings_height is not None and buildings_floors is None:
            shapefile["height_ag"] = [buildings_height] * no_buildings
            shapefile["floors_ag"] = [int(math.floor(x)) for x in shapefile["height_ag"] / constants.H_F]
        else:  # both are not none
            shapefile["height_ag"] = [buildings_height] * no_buildings
            shapefile["floors_ag"] = [buildings_floors] * no_buildings

    # add fields for floorsa and height below ground
    shapefile["height_bg"] = [buildings_height_below_ground] * no_buildings
    shapefile["floors_bg"] = [buildings_floors_below_ground] * no_buildings

    # add description
    if "description" in list_of_columns:
        shapefile["description"] = shapefile['description']
    elif 'addr:housename' in list_of_columns:
        shapefile["description"] = shapefile['addr:housename']
    elif 'amenity' in list_of_columns:
        shapefile["description"] = shapefile['amenity']
    else:
        shapefile["description"] = [np.nan] * no_buildings

    shapefile["category"] = shapefile['building']
    if 'amenity' in list_of_columns:
        # in OSM, "amenities" (where available) supersede "building" categories
        in_categories = shapefile['amenity'].isin(OSM_BUILDING_CATEGORIES.keys())
        shapefile.loc[in_categories, '1ST_USE'] = shapefile[in_categories]['amenity'].map(OSM_BUILDING_CATEGORIES)

    shapefile["Name"] = [key + str(x + 1000) for x in
                         range(no_buildings)]  # start in a big number to avoid potential confusion
    cleaned_shapefile = shapefile[
        ["Name", "height_ag", "floors_ag", "height_bg", "floors_bg", "description", "category", "geometry",
         "REFERENCE"]]

    cleaned_shapefile.reset_index(inplace=True, drop=True)
    shapefile.reset_index(inplace=True, drop=True)

    return cleaned_shapefile, shapefile


def zone_helper(locator, config):
    """
    This script gets a polygon and calculates the zone.shp and the occupancy.dbf and age.dbf inputs files for CEA
    :param locator:
    :param config:
    :return:
    """
    # local variables:
    poly = Gdf.from_file(locator.get_site_polygon())
    buildings_height = config.zone_helper.height_ag
    buildings_floors = config.zone_helper.floors_ag
    buildings_height_below_ground = config.zone_helper.height_bg
    buildings_floors_below_ground = config.zone_helper.floors_bg
    occupancy_type = config.zone_helper.occupancy_type
    year_construction = config.zone_helper.year_construction
    zone_output_path = locator.get_zone_geometry()
    typology_output_path = locator.get_building_typology()

    # ensure folders exist
    locator.ensure_parent_folder_exists(zone_output_path)
    locator.ensure_parent_folder_exists(typology_output_path)

    # get zone.shp file and save in folder location
    zone_df = polygon_to_zone(buildings_floors, buildings_floors_below_ground, buildings_height,
                              buildings_height_below_ground,
                              poly, zone_output_path)

    # USE_A zone.shp file contents to get the contents of occupancy.dbf and age.dbf
    calculate_typology_file(locator, zone_df, year_construction, occupancy_type, typology_output_path)


def calc_category(standard_DB, year_array):
    def category_assignment(year):
        return (standard_DB[(standard_DB['YEAR_START'] <= year) & (standard_DB['YEAR_END'] >= year)].STANDARD.values[0])

    category = np.vectorize(category_assignment)(year_array)
    return category


def calculate_typology_file(locator, zone_df, year_construction, occupancy_type, occupancy_output_path):
    """
    This script fills in the occupancy.dbf file with one occupancy type
    :param zone_df:
    :param occupancy_type:
    :param occupancy_output_path:
    :return:
    """
    # calculate construction year
    typology_df = calculate_age(zone_df, year_construction)
    
    # calculate the most likely construction standard
    standard_database = pd.read_excel(locator.get_database_construction_standards(), sheet_name='STANDARD_DEFINITION')
    typology_df['STANDARD'] = calc_category(standard_database, typology_df['YEAR'].values)

    # Calculate the most likely use type
    typology_df['1ST_USE'] = 'MULTI_RES'
    typology_df['1ST_USE_R'] = 1.0
    typology_df['2ND_USE'] = "NONE"
    typology_df['2ND_USE_R'] = 0.0
    typology_df['3RD_USE'] = "NONE"
    typology_df['3RD_USE_R'] = 0.0
    if occupancy_type == "Get it from open street maps":
        # for OSM building/amenity types with a clear CEA use type, this use type is assigned
        in_categories = zone_df['category'].isin(OSM_BUILDING_CATEGORIES.keys())
        zone_df.loc[in_categories, '1ST_USE'] = zone_df[in_categories]['category'].map(OSM_BUILDING_CATEGORIES)

        # for un-conditioned OSM building categories without a clear CEA use type, "PARKING" is assigned
        if 'amenity' in zone_df.columns:
            in_unconditioned_categories = zone_df['category'].isin(OTHER_OSM_CATEGORIES_UNCONDITIONED) | zone_df['amenity'].isin(OTHER_OSM_CATEGORIES_UNCONDITIONED)
        else:
            in_unconditioned_categories = zone_df['category'].isin(OTHER_OSM_CATEGORIES_UNCONDITIONED)
        zone_df.loc[in_unconditioned_categories, '1ST_USE'] = "PARKING"

    fields = COLUMNS_ZONE_TYPOLOGY
    dataframe_to_dbf(typology_df[fields + ['REFERENCE']], occupancy_output_path)


def parse_year(year):
    import re
    # `start-date` formats can be found here https://wiki.openstreetmap.org/wiki/Key:start_date#Formatting
    if type(year) == str:
        # For year in `C19`
        century_year = re.search(r'C(\d{2})', year)
        if century_year:
            return "{}00".format(century_year.group(1))
        # For any four digits
        four_digit = re.search(r'\d{4}', year)
        if four_digit:
            return four_digit.group(0)
    else:
        return year
    raise ValueError("We could not cast the value", year)


def calculate_age(zone_df, year_construction):
    """
    This script fills in the age.dbf file with one year of construction
    :param zone_df:
    :param year_construction:
    :param age_output_path:
    :return:
    """
    if year_construction is None:
        print('Warning! you have not indicated a year of construction for the buildings, '
              'we are reverting to data stored in Open Street Maps (It might not be accurate at all),'
              'if we do not find data in OSM for a particular building, we get the median in the surroundings, '
              'if we do not get any data we assume all buildings being constructed in the year 2000')
        list_of_columns = zone_df.columns
        if "start_date" not in list_of_columns:  # this field describes the construction year of buildings
            zone_df["start_date"] = 2000
            zone_df['REFERENCE'] = "CEA - assumption"
        else:
            zone_df['REFERENCE'] = ["OSM - median" if x is np.nan else "OSM - as it is" for x in zone_df['start_date']]

        data_age = [np.nan if x is np.nan else int(parse_year(x)) for x in zone_df['start_date']]
        data_osm_floors_joined = int(math.ceil(np.nanmedian(data_age)))  # median so we get close to the worse case
        zone_df["YEAR"] = [int(x) if x is not np.nan else data_osm_floors_joined for x in data_age]
    else:
        zone_df['YEAR'] = year_construction
        zone_df['REFERENCE'] = "CEA - assumption"

    return zone_df


def polygon_to_zone(buildings_floors, buildings_floors_below_ground, buildings_height, buildings_height_below_ground,
                    poly, zone_out_path):
    poly = poly.to_crs(get_geographic_coordinate_system())
    lon = poly.geometry[0].centroid.coords.xy[0][0]
    lat = poly.geometry[0].centroid.coords.xy[1][0]
    # get footprints of all the district
    poly = osmnx.footprints.footprints_from_polygon(polygon=poly['geometry'].values[0])

    # clean geometries
    poly = clean_geometries(poly)

    # clean attributes of height, name and number of floors
    cleaned_shapefile, shapefile = clean_attributes(poly, buildings_height, buildings_floors,
                                                    buildings_height_below_ground,
                                                    buildings_floors_below_ground, key="B")
    cleaned_shapefile = cleaned_shapefile.to_crs(get_projected_coordinate_system(float(lat), float(lon)))
    # save shapefile to zone.shp
    cleaned_shapefile.to_file(zone_out_path)

    return shapefile


def clean_geometries(gdf):
    """
    Takes in a GeoPandas DataFrame and making sure all geometries are of type 'Polygon' and remove any entries that do
    not have any geometries
    :param gdf: GeoPandas DataFrame containing geometries
    :return:
    """
    def flatten_geometries(geometry):
        """
        Flatten polygon collections into a single polygon by using their union
        :param geometry: Type of Shapely geometry
        :return:
        """
        from shapely.ops import unary_union
        if geometry.type == 'Polygon':  # ignore Polygons
            return geometry
        elif geometry.type in ['Point', 'LineString']:
            print(f'Discarding geometry of type: {geometry.type}')
            return None # discard geometry if it is a Point or LineString
        else:
            joined = unary_union(list(geometry))
            if joined.type == 'MultiPolygon':  # some Multipolygons could not be combined
                return joined[0]  # just return first polygon
            elif joined.type != 'Polygon':  # discard geometry if it is still not a Polygon
                print('Discarding geometry of type: {geometry_type}'.format(geometry_type=joined.type))
                return None
            else:
                return joined
    gdf.geometry = gdf.geometry.map(flatten_geometries)
    gdf = gdf[gdf.geometry.notnull()]  # remove None geometries

    return gdf


def main(config):
    """
    This script gets a polygon and calculates the zone.shp and the occupancy.dbf and age.dbf inputs files for CEA
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    zone_helper(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
