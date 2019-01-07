from __future__ import division
from __future__ import print_function


COLUMNS_ZONE_GEOMETRY = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
COLUMNS_DISTRICT_GEOMETRY = ['Name', 'height_ag', 'floors_ag', 'floors_bg']
COLUMNS_ZONE_AGE = ['built', 'roof', 'windows', 'partitions', 'basement', 'HVAC', 'envelope']
COLUMNS_ZONE_OCCUPANCY = ['MULTI_RES', 'OFFICE', 'RETAIL', 'SCHOOL', 'HOTEL', 'GYM', 'HOSPITAL', 'INDUSTRIAL',
                          'RESTAURANT','SINGLE_RES', 'SERVERROOM', 'SWIMMING', 'FOODSTORE', 'LIBRARY', 'COOLROOM', 'PARKING']


def assert_columns_names(zone_df, columns):

    try:
        zone_test = zone_df[columns]
    except ValueError:
        print("one or more columns in the Zone or District input files is not compatible with CEA, please ensure the column" +
              " names comply with:", columns)

def assert_input_geometry_acceptable_values_floor_height(zone_df):

    # Rule 0. nothing can be negative
    rule0 = zone_df.where(zone_df < 0.0).any().any()
    if rule0:
        raise Exception('There are negative values in your geometry. This is not possible to simulate in CEA at the moment'
                        ' Please verify your Zone or District shapefile file')

    # Rule 1. Floors above ground cannot be less than 1 or negative.
    rule1_1 = zone_df['floors_ag'].where(zone_df['floors_ag'] < 1).any()
    rule1_2 = zone_df['height_ag'].where(zone_df['height_ag'] < 1.0).any()
    if rule1_1 or rule1_2:
        raise Exception('one of more buildings have less than one floor above ground or the height above ground is less than 1 meter.'
                        ' This is not possible to simulate in CEA at the moment. Please verify your Zone or District shapefile file')

    # Rule 2. Where floor height is less than 1m on average above ground.
    zone_df['rule2'] = zone_df['height_ag'] / zone_df['floors_ag']
    rule2 = zone_df['rule2'].where(zone_df['rule2'] <= 1.0).any()
    if rule2:
        raise Exception('one of more buildings have less report less than 1m height per floor. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or District shapefile file')

    # Rule 3. floors below ground cannot be negative
    rule3 = zone_df['floors_bg'].where(zone_df['floors_bg'] < 0).any()
    if rule3:
        raise Exception('one of more buildings have a negative floor below ground. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or District file')


def verify_input_geometry_zone(zone_df):

    # Verification 1. verify if all the column names are correct
    assert_columns_names(zone_df, COLUMNS_ZONE_GEOMETRY)

    # Verification 2. verify if the floor_height ratio is correct
    assert_input_geometry_acceptable_values_floor_height(zone_df)

def verify_input_geometry_district(district_df):

    # Verification 1. verify if all the column names are correct
    assert_columns_names(district_df, COLUMNS_DISTRICT_GEOMETRY)

    # Verification 2. verify if the floor_height ratio is correct
    assert_input_geometry_acceptable_values_floor_height(district_df)

def verify_input_occupancy(occupancy_df):

    # Verification 1. verify if all the column names are correct
    assert_columns_names(occupancy_df, COLUMNS_ZONE_OCCUPANCY)

def verify_input_age(age_df):

    # Verification 1. verify if all the column names are correct
    assert_columns_names(age_df, COLUMNS_ZONE_AGE)

def verify_input_terrain(terrain_raster):

    # Verification 1. verify that we can create the geometry
    if terrain_raster == None:
        raise Exception("Yout input terrain file is corrupted. Please verify that you have a non-null raster,"
                         "and that the grid of it be at least 5 X 5 meters, smaller grid sizes will drastically"
                         "make the solar radiation engine slow")


