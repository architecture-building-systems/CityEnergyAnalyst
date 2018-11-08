
from pandas import pd

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

    # Rule 1. Floors above ground cannot be less than 1 or negative.
    rule1_1 = zone_df['floors_ag'].where(zone_df < 1).any()
    if rule1_1:
        raise Exception('one of more buildings have less than one floor above ground. This is not possible'
                        'to similute in CEA at the moment. Please verify your Zone or District file')

    # Rule 2. Where floor height is less than 1m on average above ground.
    zone_df['rule2'] = zone_df['height_ag'] / zone_df['floors_ag']
    rule2 = zone_df['rule2'].where(zone_df <= 1).any()
    if rule2:
        raise Exception('one of more buildings have less report less than 1m height per floor. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or District file')

    # Rule 3. floors below ground cannot be negative
    rule3 = zone_df['floors_bg'].where(zone_df < 0).any()
    if rule3:
        raise Exception('one of more buildings have a negative floor below ground. This is not possible'
                        'to similute in CEA at the moment. Please verify your Zone or District file')

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

    # Verification 2.

