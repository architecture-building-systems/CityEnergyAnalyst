"""
This is a template script - an example of how a CEA script should be set up.
NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

import math
import os
from typing import Union

import numpy as np
import osmnx
from geopandas import GeoDataFrame as Gdf
from shapely.geometry import Polygon
import pandas as pd

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import COLUMNS_ZONE
from cea.demand import constants
from cea.datamanagement.constants import OSM_BUILDING_CATEGORIES, OTHER_OSM_CATEGORIES_UNCONDITIONED, GRID_SIZE_M, EARTH_RADIUS_M
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system, \
    get_lat_lon_projected_shapefile

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
            match = re.match(separated_values.format(
                separator=separator), floors)
            if match:
                return max([float(x.strip() or 0) for x in floors.split(separator)])
        return np.nan
    else:
        return parsed_floors


def assign_attributes(shapefile, buildings_height, buildings_floors, buildings_height_below_ground,
                      buildings_floors_below_ground, key):
    # local variables
    no_buildings = shapefile.shape[0]
    list_of_columns = shapefile.columns
    if buildings_height is None and buildings_floors is None:
        print('Note that the number of floors is extracted from OpenStreetMap. '
              'If not found, CEA uses the median in the surroundings. '
              'When no data is available, CEA assumes 4 floors per building (3 above, 1 below ground). '
              'Ensure the number of floors is accurate before proceeding with any simulations.')

        print('Note that CEA assumes the floor height is 3 meters. '
              'Modify before proceeding with any simulations.')

        # Make sure relevant OSM parameters (if available) are passed as floats, not strings
        OSM_COLUMNS = ['building:min_level', 'min_height', 'building:levels', 'height']
        shapefile[[c for c in OSM_COLUMNS if c in list_of_columns]] = \
            shapefile[[c for c in OSM_COLUMNS if c in list_of_columns]].fillna(1) \
                .apply(lambda x: pd.to_numeric(x, errors='coerce'))

        # Check which attributes OSM has (sometimes it does not have any) and indicate the data source
        if 'building:levels' not in list_of_columns or pd.isnull(shapefile['building:levels']).all():
            # if 'building:levels' is not in the database, make an assumption
            # if 'building:levels' are all NaN, make an assumption
            shapefile['building:levels'] = 3 * no_buildings
            shapefile['reference'] = ["CEA Assumption"] * no_buildings
        elif 'height' in list_of_columns:
            # if either the 'building:levels' or the building 'height' are available, take them from OSM
            shapefile['reference'] = ["OSM - as it is" if x else "OSM - median values of all buildings" for x in
                                      (~shapefile['building:levels'].isna()) | (shapefile['height'] > 0)]
        else:
            # if only the 'building:levels' are available, take them from OSM
            shapefile['reference'] = ["OSM - as it is" if x else "OSM - median values of all buildings" for x in
                                      ~shapefile['building:levels'].isna()]
        if 'roof:levels' not in list_of_columns:
            shapefile['roof:levels'] = 0

        # get the median from the area:
        data_osm_floors1 = shapefile['building:levels'].fillna(0)
        data_osm_floors2 = shapefile['roof:levels'].fillna(0)
        data_floors_sum = [x + y for x, y in zip([parse_building_floors(x) for x in data_osm_floors1],
                                                 [parse_building_floors(y) for y in data_osm_floors2])]
        data_floors_sum_with_nan = [np.nan if x <
                                    1.0 else x for x in data_floors_sum]
        data_osm_floors_joined = math.ceil(
            np.nanmedian(data_floors_sum_with_nan))  # median so we get close to the worse case
        shapefile["floors_ag"] = [int(x) if not np.isnan(x) else data_osm_floors_joined for x in
                                  data_floors_sum_with_nan]

        shapefile["void_deck"] = 0 # assume no void decks by default

        if 'height' in list_of_columns:
            #  Replaces 'nan' values with CEA assumption
            shapefile["height_ag"] = shapefile["height"].fillna(
                shapefile["floors_ag"] * constants.H_F).astype(float)
            #  Replaces values of height = 0 with CEA assumption
            # TODO: Check whether buildings with height between 0 and 1 meter are actually mostly underground
            #  These might not be errors, but rather partially or fully underground buildings. This should be verified.
            #  Also, the radiation script cannot process buildings with height 0 m at the moment.
            #  Once the radiation script can process underground buildings, this step might need to be revised.
            shapefile["height_ag"] = shapefile["height_ag"].where(shapefile["height_ag"] != 0,
                                                                  shapefile["floors_ag"] * constants.H_F).astype(float)
        else:
            shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F

        # make sure each floor is at least 1m
        # we assume floors_ag is accurate and adjust height_ag accordingly
        less_than_1m = shapefile['height_ag'] < shapefile['floors_ag']
        shapefile.loc[less_than_1m, ['height_ag']] = shapefile[less_than_1m]['floors_ag']

        # add fields for floors and height below ground
        shapefile["height_bg"] = pd.Series(np.nan)
        shapefile["floors_bg"] = pd.Series(np.nan)

        # Correct levels below ground if a minimum floor level or height is indicated
        if 'building:min_level' in list_of_columns:
            has_min_floor = shapefile["building:min_level"] == shapefile["building:min_level"]
            shapefile[has_min_floor].floors_bg = [- int(x) for x in shapefile[has_min_floor]["building:min_level"]]
            shapefile[has_min_floor].height_bg = shapefile[has_min_floor].floors_bg * constants.H_F
        if 'min_height' in list_of_columns:
            has_min_height = shapefile["min_height"] == shapefile["min_height"]
            shapefile[has_min_height].height_bg = [- int(x) for x in shapefile[has_min_height]["min_height"]]
        # add missing floors and height below ground
        shapefile.loc[shapefile.height_bg.isna(), "height_bg"] = [buildings_height_below_ground] * no_buildings
        shapefile.loc[shapefile.floors_bg.isna(), "floors_bg"] = [buildings_floors_below_ground] * no_buildings
        shapefile["floors_bg"] = shapefile["floors_bg"].astype(int)
    else:
        shapefile['reference'] = "User - assumption"
        if buildings_height is None and buildings_floors is not None:
            shapefile["floors_ag"] = [buildings_floors] * no_buildings
            shapefile["height_ag"] = shapefile["floors_ag"] * constants.H_F
        elif buildings_height is not None and buildings_floors is None:
            shapefile["height_ag"] = [buildings_height] * no_buildings
            shapefile["floors_ag"] = [
                int(math.floor(x)) for x in shapefile["height_ag"] / constants.H_F]
        else:  # both are not none
            shapefile["height_ag"] = [buildings_height] * no_buildings
            shapefile["floors_ag"] = [buildings_floors] * no_buildings
        # add fields for floors and height below ground
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
        in_categories = shapefile['amenity'].isin(
            OSM_BUILDING_CATEGORIES.keys())
        shapefile.loc[in_categories, 'use_type1'] = shapefile[in_categories]['amenity'].map(
            OSM_BUILDING_CATEGORIES)

    shapefile["name"] = [key + str(x + 1000) for x in
                         range(no_buildings)]  # start in a big number to avoid potential confusion
    shapefile.reset_index(inplace=True, drop=True)

    return shapefile

def assign_attributes_additional(shapefile):
    """
    This script fills the zone.shp file with additional information from OSM,
    including house number, street name, postcode, if HDB (for Singapore), city, country
    """
    # TODO: include different terms used by OSM in different countries
    #  As of 19 Sept 2023, this function works fine in Switzerland and Singapore

    # local variables
    no_buildings = shapefile.shape[0]
    list_of_columns = shapefile.columns

    # Check which attributes OSM has (sometimes it does not have any) and create the column if missing
    if 'addr:city' not in list_of_columns:
        shapefile['addr:city'] = [''] * no_buildings
    if 'addr:country' not in list_of_columns:
        shapefile['addr:country'] = [''] * no_buildings
    if 'addr:postcode' not in list_of_columns:
        shapefile['addr:postcode'] = [''] * no_buildings
    if 'addr:street' not in list_of_columns:
        shapefile['addr:street'] = [''] * no_buildings
    if 'addr:housename' not in list_of_columns:
        shapefile['addr:housename'] = [''] * no_buildings
    if 'addr:housenumber' not in list_of_columns:
        shapefile['addr:housenumber'] = [''] * no_buildings
    if 'residential' not in list_of_columns:
        shapefile['residential'] = [''] * no_buildings     #not HDB

    # Assign the cea-formatted columns with attributes
    shapefile['house_no'] = shapefile['addr:housenumber']
    shapefile['street'] = shapefile['addr:street']
    shapefile['postcode'] = shapefile['addr:postcode']
    shapefile['house_name'] = shapefile['addr:housename']
    shapefile['resi_type'] = shapefile['residential']
    shapefile['city'] = shapefile['addr:city']
    shapefile['country'] = shapefile['addr:country']

    return shapefile


def fix_overlapping_geoms(buildings, zone):
    """
    This function eliminates overlapping geometries. To decide which portions of two overlapping geometries to
    eliminate, the functions abides by the following rules:
        1. If two buildings' footprints overlap, check if they also overlap vertically, i.e. height of ground surface
            of building A < height of roof of building B (this is only really relevant for buildings that have
            'floating' elements, e.g. Marina Bay Sands 'boat').
        2. If they also overlap vertically, cut the overlapping portion of the taller building's footprint out of the
            lower building's footprint-polygon.

    As a preprocessing step the OSM-information on "min_heights" and "min_levels" gets assigned to the building's
    height and levels below ground (introduced in the zone-helper.assign_attributes() function) as negative values.
    """
    # PREPROCESSING OF BUILDING ATTRIBUTES
    # get zone's geometry
    geometries = buildings.geometry

    # CREATE GRID TO PARTITION THE BUILDINGS (more efficient - hopefully)
    # calculate grid-parameters based on the zone polygon dimensions
    [[west_bound_long, south_bound_lat, east_bound_long,
        north_bound_lat]] = zone.bounds.to_numpy()
    [(centroid_long, centroid_lat)] = zone.centroid.get(0).coords[:]
    grid_size_long = 180 * GRID_SIZE_M / \
        (np.pi * EARTH_RADIUS_M * np.cos(centroid_lat * np.pi / 180))
    grid_size_lat = 180 * GRID_SIZE_M / (np.pi * EARTH_RADIUS_M)
    n_grid_cells_long = math.ceil(
        (east_bound_long - west_bound_long) / grid_size_long)
    n_grid_cells_lat = math.ceil(
        (north_bound_lat - south_bound_lat) / grid_size_lat)
    grid_cells = []

    # create 500m * 500m grid
    for i in range(n_grid_cells_lat):
        for j in range(n_grid_cells_long):
            dx_0 = j * grid_size_long
            dx_1 = (j + 1) * grid_size_long
            dy_0 = i * grid_size_lat
            dy_1 = (i+1) * grid_size_lat
            cell_vertices = [(west_bound_long + dx_0, north_bound_lat - dy_0),
                             (west_bound_long + dx_1, north_bound_lat - dy_0),
                             (west_bound_long + dx_1, north_bound_lat - dy_1),
                             (west_bound_long + dx_0, north_bound_lat - dy_1),
                             (west_bound_long + dx_0, north_bound_lat - dy_0)]
            grid_cells.append(Polygon(cell_vertices))
    grid = Gdf(geometry=grid_cells, crs="EPSG:4326")

    # FIX OVERLAYS IN THE BUILDING GEOMETRIES
    # overlay the grid with the zone polygon, retaining the overlapping grid cells, and ...
    grid = zone.to_crs(grid.crs).overlay(grid, how="intersection")

    # iterate through the grid cells, overlaying them with the buildings, retaining the buildings
    for cell_index in range(grid.geometry.size):
        cell = Gdf(geometry=[grid.geometry[cell_index]], crs="EPSG:4326")
        is_intersecting = geometries.intersects(cell.geometry[0])
        buildings_in_cell = buildings[is_intersecting]

        # check each building for intersections with other buildings - if intersection is found:
        for building_index in buildings_in_cell.index:
            is_overlapping = buildings_in_cell.geometry.intersects(
                buildings_in_cell.geometry[building_index])
            overlapping_buildings = buildings_in_cell[is_overlapping]
            # check if all overlapping buildings have building use type information from OSM, if not assign mode of all overlapping buildings
            critical_columns = ['building', 'amenity', "description", "category"]
            appearing_critical_columns = [col for col in critical_columns if col in overlapping_buildings.columns]
            for col in appearing_critical_columns:
                if np.any(overlapping_buildings[col].isna()) & ~np.all(overlapping_buildings[col].isna()):
                    buildings.loc[overlapping_buildings.loc[overlapping_buildings[col].isna()].index, col] = \
                        overlapping_buildings[col].dropna().mode()[0]
            # cut out the higher building's footprint-polygon out the lower buildings footprint-polygon
            for ovrlp_bldg_index in overlapping_buildings.index:
                if ovrlp_bldg_index == building_index:
                    pass  # same building -> doesn't count as overlap
                elif (buildings.height_ag[ovrlp_bldg_index] <= -buildings.height_bg[building_index]) or \
                    (buildings.height_ag[building_index] <= -buildings.height_bg[ovrlp_bldg_index]):
                    pass  # no vertical overlap
                elif (buildings.reference[ovrlp_bldg_index] == "OSM - as it is") & \
                     (buildings.reference[building_index] != "OSM - as it is"):  # Give OSM priority
                    buildings.geometry[building_index] = \
                        buildings.geometry[building_index].difference(buildings.geometry[ovrlp_bldg_index])
                elif (buildings.reference[building_index] == "OSM - as it is") & \
                     (buildings.reference[ovrlp_bldg_index] != "OSM - as it is"):  # Give OSM priority
                    buildings.geometry[ovrlp_bldg_index] = \
                        buildings.geometry[ovrlp_bldg_index].difference(buildings.geometry[building_index])
                elif (buildings.height_ag[building_index] + buildings.height_bg[building_index]) <= \
                        (buildings.height_ag[ovrlp_bldg_index] + buildings.height_bg[ovrlp_bldg_index]):
                    buildings.geometry[building_index] = \
                        buildings.geometry[building_index].difference(
                            buildings.geometry[ovrlp_bldg_index])
                elif (buildings.height_ag[building_index] + buildings.height_bg[building_index]) > \
                        (buildings.height_ag[ovrlp_bldg_index] + buildings.height_bg[ovrlp_bldg_index]):
                    buildings.geometry[ovrlp_bldg_index] = \
                        buildings.geometry[ovrlp_bldg_index].difference(
                            buildings.geometry[building_index])

    return buildings


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
    include_building_parts = config.zone_helper.include_building_parts
    fix_overlapping = config.zone_helper.fix_overlapping_geometries
    zone_output_path = locator.get_zone_geometry()

    # ensure folders exist
    locator.ensure_parent_folder_exists(zone_output_path)

    # get zone.shp file and save in folder location
    zone_df = polygon_to_zone(buildings_floors, buildings_floors_below_ground, buildings_height,
                              buildings_height_below_ground,
                              fix_overlapping, include_building_parts,
                              poly)

    # USE_A zone.shp file contents to get the contents of occupancy.dbf and age.dbf
    typology_df = calculate_typology_file(
        locator, zone_df, year_construction, occupancy_type)

    # write zone.shp file
    write_zone_shp(typology_df, poly, locator)

def calc_category(standard_db, year_array):
    def category_assignment(year):
        within_year = (standard_db['year_start'] <= year) & (
            standard_db['year_end'] >= year)
        standards = standard_db.const_type.values

        # Filter standards if found
        if within_year.any():
            standards = standards[within_year]

        # Just return first value
        return standards[0]

    category = np.array([category_assignment(y) for y in year_array])
    return category


def calculate_typology_file(locator, zone_df, year_construction, occupancy_type):
    """
    This script fills in the typology.dbf file with one occupancy type
    :param zone_df:
    :param occupancy_type:
    :return:
    """

    # calculate construction year
    typology_df = calculate_age(zone_df, year_construction)

    # calculate the most likely construction standard
    standard_database = pd.read_csv(
        locator.get_database_archetypes_construction_type())
    typology_df['const_type'] = calc_category(
        standard_database, typology_df['year'].values)

    # Calculate the most likely use type
    typology_df['use_type1'] = "NONE"
    typology_df['use_type1r'] = 1.0
    typology_df['use_type2'] = "NONE"
    typology_df['use_type2r'] = 0.0
    typology_df['use_type3'] = "NONE"
    typology_df['use_type3r'] = 0.0
    if occupancy_type == "Get it from open street maps":
        # for OSM building/amenity types with a clear CEA use type, this use type is assigned
        in_categories = zone_df['category'].isin(OSM_BUILDING_CATEGORIES.keys())
        zone_df.loc[in_categories, 'use_type1'] = zone_df[in_categories]['category'].map(OSM_BUILDING_CATEGORIES)
        if 'amenity' in zone_df.columns:
            # assign use type by building category first, then by amenity (more specific)
            in_categories = zone_df['amenity'].isin(OSM_BUILDING_CATEGORIES.keys())
            zone_df.loc[in_categories, 'use_type1'] = zone_df[in_categories]['amenity'].map(OSM_BUILDING_CATEGORIES)

        # for un-conditioned OSM building categories without a clear CEA use type, "PARKING" is assigned
        if 'amenity' in zone_df.columns:
            in_unconditioned_categories = zone_df['category'].isin(
                OTHER_OSM_CATEGORIES_UNCONDITIONED) | zone_df['amenity'].isin(OTHER_OSM_CATEGORIES_UNCONDITIONED)
        else:
            in_unconditioned_categories = zone_df['category'].isin(
                OTHER_OSM_CATEGORIES_UNCONDITIONED)
        zone_df.loc[in_unconditioned_categories, 'use_type1'] = "PARKING"
    else:
        typology_df['use_type1'] = occupancy_type

    # all remaining building use types are assigned by the mode of the use types in the entire case study
    try:
        typology_df.loc[typology_df['use_type1'] == "NONE", 'use_type1'] = \
            typology_df.loc[~typology_df['use_type1'].isin(['NONE', 'PARKING']), 'use_type1'].mode()[0]
    except KeyError:
        print('No building type could be found in the OSM-database for the selected zone. '
              'Applying `MULTI_RES` as default type.')
        typology_df.loc[typology_df['use_type1'] == "NONE", 'use_type1'] = "MULTI_RES"

    return typology_df

def write_zone_shp(typology_df, poly, locator):

    # get the projected coordinate system
    poly = poly.to_crs(get_geographic_coordinate_system())
    lat, lon = get_lat_lon_projected_shapefile(poly)

    # clean up attributes
    cleaned_shapefile = typology_df[COLUMNS_ZONE]
    cleaned_shapefile = cleaned_shapefile.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # save shapefile to zone.shp
    cleaned_shapefile.to_file(locator.get_zone_geometry())


def parse_year(year: Union[str, int]) -> int:
    import re
    # `start-date` formats can be found here https://wiki.openstreetmap.org/wiki/Key:start_date#Formatting
    if isinstance(year, str):
        # For year in "century" format e.g. `C19`
        century_year = re.search(r'C(\d{2})', year)
        if century_year:
            return int(f"{century_year.group(1)}00")

        # For any four digits in a string e.g. `1860s` or `late 1920s`
        four_digit = re.search(r'\d{4}', year)
        if four_digit:
            return int(four_digit.group(0))

        # Finally try to cast string to int
        try:
            return int(year)
        except ValueError:
            # Raise error later
            pass

        raise ValueError(f"Invalid year format found `{year}`")
    else:
        return year


def calculate_age(zone_df, year_construction):
    """
    This script fills in the age.dbf file with one year of construction
    :param zone_df:
    :param year_construction:
    :param age_output_path:
    :return:
    """
    if year_construction is None:
        print('Note that CEA is importing data from OpenStreetMap. '
              'If data unavailable for some buildings, CEA uses the median in the surroundings, '
              'If data unavailable for all buildings, CEA assumes all buildings were constructed in 2020.')
        list_of_columns = zone_df.columns
        if "start_date" not in list_of_columns:  # this field describes the construction year of buildings
            zone_df["start_date"] = 2000

        data_age = [np.nan if x is np.nan else parse_year(
            x) for x in zone_df['start_date']]
        # median so we get close to the worse case
        data_osm_floors_joined = int(math.ceil(np.nanmedian(data_age)))
        zone_df["year"] = [
            int(x) if x is not np.nan else data_osm_floors_joined for x in data_age]
    else:
        zone_df['year'] = year_construction

    return zone_df


def polygon_to_zone(buildings_floors, buildings_floors_below_ground, buildings_height, buildings_height_below_ground,
                    fix_overlapping, include_building_parts, poly):

    # get all footprints in the district tagged as 'building' or 'building:part' in OSM
    shapefile = osmnx.features_from_polygon(polygon=poly['geometry'].values[0], tags={"building": True})
    if include_building_parts:
        try:
            # get all footprints in the district tagged as 'building' or 'building:part' in OSM
            building_parts = osmnx.features_from_polygon(polygon=poly['geometry'].values[0],
                                                         tags={"building": ["part"]})
            shapefile = pd.concat([shapefile, building_parts], ignore_index=True)
            # using building:part tags requires fixing overlapping polygons
            if not fix_overlapping:
                print('Building parts included, fixing overlapping geometries activated.')
                fix_overlapping = True
        except osmnx._errors.InsufficientResponseError:
            pass

    # clean geometries
    shapefile = clean_geometries(shapefile)

    # clean attributes of height, name and number of floors
    shapefile = assign_attributes(shapefile, buildings_height, buildings_floors,
                                 buildings_height_below_ground, buildings_floors_below_ground, key="B")

    # adding additional information from OSM
    # (e.g. house number, street number, postcode, if HDB for Singapore buildings)
    shapefile = assign_attributes_additional(shapefile)

    # fix geometries of buildings with overlapping polygons
    if fix_overlapping is True:
        print("Fixing overlapping geometries.")
        shapefile = fix_overlapping_geoms(shapefile, poly)

        # Clean up geometries that are no longer in use (i.e. buildings that have empty geometry)
        shapefile = shapefile[~shapefile.geometry.is_empty]
        # Pass the Gdf back to flatten_geometries to split MultiPolygons that might have been created due to one
        # building cutting another one into pieces and remove any unusable geometry types (e.g., LineString)
        shapefile = flatten_geometries(shapefile)
        # reassign building names to account for exploded MultiPolygons
        shapefile["name"] = ["B" + str(x + 1000) for x in range(shapefile.shape[0])]

    return shapefile


def clean_geometries(gdf):
    """
    Takes in a GeoPandas DataFrame and making sure all geometries are of type 'Polygon' and remove any entries that do
    not have any geometries
    :param gdf: GeoPandas DataFrame containing geometries
    :return:
    """
    gdf = flatten_geometries(gdf)
    gdf = gdf[gdf.geometry.notnull()]  # remove None geometries

    return gdf

def flatten_geometries(gdf):
    """
    Flatten polygon collections into a single polygon by using their union
    :param gdf: GeoDataFrame
    :return:
    """
    from shapely.ops import unary_union
    DISCARDED_GEOMETRY_TYPES = ['Point', 'LineString']

    # Explode MultiPolygons and GeometryCollections
    gdf = gdf.explode(index_parts=True)
    # Drop geometry types that cannot be processed by CEA
    gdf = gdf.loc[~ gdf.geometry.geom_type.isin(DISCARDED_GEOMETRY_TYPES)]
    # Process individual geometries in MultiPolygon and GeometryCollection data types
    for i in gdf.loc[gdf.index.get_level_values(1) == 1].index.get_level_values(0):
        # if polygons can be joined into one Polygon, keep the joined Polygon
        if unary_union(list(gdf.loc[gdf.index.get_level_values(0) == i].geometry)) == 'Polygon':
            gdf.loc[gdf.index.get_level_values(0) == i].geometry = unary_union(list(
                gdf.loc[gdf.index.get_level_values(0) == i].geometry))
            gdf.drop(gdf.loc[(gdf.index.get_level_values(0) == i) &
                             (gdf.index.get_level_values(1) == 0)].index, inplace=True)
        # else, polygons are joined into a MultiPolygon, keep each individual Polygon as a separate building
    # rename buildings
    gdf = gdf.reset_index(drop=True)

    return gdf

def main(config):
    """
    This script gets a polygon and calculates the zone.shp and the occupancy.dbf and age.dbf inputs files for CEA
    """
    assert os.path.exists(
        config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    zone_helper(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
