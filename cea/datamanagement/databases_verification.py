"""
Databases verification
This tool is used as to check the format of each database
"""
from __future__ import division
from __future__ import print_function
from cea.scripts import schemas
import pandas as pd
import re

COLUMNS_ZONE_GEOMETRY = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
COLUMNS_SURROUNDINGS_GEOMETRY = ['Name', 'height_ag', 'floors_ag']
COLUMNS_ZONE_TYPOLOGY = ['Name', 'STANDARD', 'YEAR', '1ST_USE', '1ST_USE_R', '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R']

def assert_columns_names(zone_df, columns):
    try:
        zone_test = zone_df[columns]
    except ValueError:
        print(
            "one or more columns in the Zone or Surroundings input files is not compatible with CEA, please ensure the column" +
            " names comply with:", columns)


def assert_input_geometry_acceptable_values_floor_height(zone_df):
    # Rule 0. nothing can be negative
    rule0 = zone_df.where(zone_df < 0.0).any().any()
    if rule0:
        raise Exception(
            'There are negative values in your geometry. This is not possible to simulate in CEA at the moment'
            ' Please verify your Zone or Surroundings shapefile file')

    # Rule 1. Floors above ground cannot be less than 1 or negative.
    rule1_1 = zone_df['floors_ag'].where(zone_df['floors_ag'] < 1).any()
    rule1_2 = zone_df['height_ag'].where(zone_df['height_ag'] < 1.0).any()
    if rule1_1 or rule1_2:
        raise Exception(
            'one of more buildings have less than one floor above ground or the height above ground is less than 1 meter.'
            ' This is not possible to simulate in CEA at the moment. Please verify your Zone or Surroundings shapefile file')

    # Rule 2. Where floor height is less than 1m on average above ground.
    zone_df['rule2'] = zone_df['height_ag'] / zone_df['floors_ag']
    rule2 = zone_df['rule2'].where(zone_df['rule2'] <= 1.0).any()
    if rule2:
        raise Exception('one of more buildings have less report less than 1m height per floor. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or Surroundings shapefile file')

    # Rule 3. floors below ground cannot be negative
    rule3 = zone_df['floors_bg'].where(zone_df['floors_bg'] < 0).any()
    if rule3:
        raise Exception('one of more buildings have a negative floor below ground. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or Surroundings file')


def assert_input_geometry_acceptable_values_floor_height_surroundings(surroundings_df):
    # Rule 0. nothing can be negative
    rule0 = surroundings_df.where(surroundings_df < 0.0).any().any()
    if rule0:
        raise Exception(
            'There are negative values in your geometry. This is not possible to simulate in CEA at the moment'
            ' Please verify your Zone or Surroundings shapefile file')

    # Rule 1. Floors above ground cannot be less than 1 or negative.
    rule1_1 = surroundings_df['floors_ag'].where(surroundings_df['floors_ag'] < 1).any()
    rule1_2 = surroundings_df['height_ag'].where(surroundings_df['height_ag'] < 1.0).any()
    if rule1_1 or rule1_2:
        raise Exception(
            'one of more buildings have less than one floor above ground or the height above ground is less than 1 meter.'
            ' This is not possible to simulate in CEA at the moment. Please verify your Zone or Surroundings shapefile file')

    # Rule 2. Where floor height is less than 1m on average above ground.
    surroundings_df['rule2'] = surroundings_df['height_ag'] / surroundings_df['floors_ag']
    rule2 = surroundings_df['rule2'].where(surroundings_df['rule2'] <= 1.0).any()
    if rule2:
        raise Exception('one of more buildings have less report less than 1m height per floor. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or Surroundings shapefile file')


def verify_input_geometry_zone(zone_df):
    # Verification 1. verify if all the column names are correct
    assert_columns_names(zone_df, COLUMNS_ZONE_GEOMETRY)

    # Verification 2. verify if the floor_height ratio is correct
    assert_input_geometry_acceptable_values_floor_height(zone_df)


def verify_input_geometry_surroundings(surroundings_df):
    # Verification 1. verify if all the column names are correct
    assert_columns_names(surroundings_df, COLUMNS_SURROUNDINGS_GEOMETRY)

    # Verification 2. verify if the floor_height ratio is correct
    assert_input_geometry_acceptable_values_floor_height_surroundings(surroundings_df)


def verify_input_typology(typology_df):
    # Verification 1. verify if all the column names are correct
    assert_columns_names(typology_df, COLUMNS_ZONE_TYPOLOGY)


def verify_input_terrain(terrain_raster):
    # Verification 1. verify that we can create the geometry
    if terrain_raster == None:
        raise Exception("Yout input terrain file is corrupted. Please verify that you have a non-null raster,"
                        "and that the grid of it be at least 5 X 5 meters, smaller grid sizes will drastically"
                        "make the solar radiation engine slow")


class InputFileValidator(object):
    def __init__(self, input_locator=None):
        # Need locator to read other files if lookup choice values
        self.locator = input_locator
        self.schemas = schemas()
        self._cache = {}

    def validate(self, data, locator_method_name):
        """
        Takes a dataframe and validates it based on the schema retrieved using the key i.e. locator_method_name
        from schemas.yml file
        :param data:
        :param locator_method_name:
        :return: list of errors where errors are represented as [dict(), str()]
        """
        df_schema = self.schemas[locator_method_name]
        file_type = df_schema['file_type']

        if file_type in ['xlsx', 'xls']:
            errors = []
            for sheet, _data in data.items():
                sheet_errors = self._run_all_tests(_data, df_schema['schema'][sheet], self.locator)
                if sheet_errors:
                    errors.append([{"sheet": str(sheet)}, sheet_errors])
            return errors

        return self._run_all_tests(data, df_schema['schema'], self.locator)

    def _run_all_tests(self, data, data_schema, locator):
        """
        Runs all tests and reduce errors to a single list
        :param data: Dataframe of data to be tested
        :param data_schema: Schema for dataframe
        :return: list of errors
        """
        return sum([self.assert_columns_names(data, data_schema),
                    self.assert_column_values(data, data_schema, locator)], [])

    @staticmethod
    def assert_columns_names(data, data_schema):
        columns = data_schema.keys()
        missing_columns = [col for col in columns if col not in data.columns]
        extra_columns = [col for col in data.columns if col not in columns]
        return [[{'column': str(col)}, 'Column is missing'] for col in missing_columns] + \
               [[{'column': str(col)}, 'Column is not in schema'] for col in extra_columns]

    @staticmethod
    def assert_column_values(data, data_schema, locator):

        columns = data_schema.keys()
        # Only loop through valid columns that exist
        filter_columns = [col for col in columns if col in data.columns]
        errors = []
        for column in filter_columns:
            col_schema = data_schema[column]
            if 'choice' in col_schema:
                pass
            else:
                column_errors = data[column].apply(get_validator_func(col_schema)).dropna()
                for index, error in column_errors.to_dict().items():
                    errors.append([{'row': int(index), 'column': str(column)}, error])
        return errors


def get_validator_func(col_schema):
    if col_schema['type'] == 'string':
        return StringTypeValidator(col_schema).validate
    if col_schema['type'] == 'int':
        return IntegerTypeValidator(col_schema).validate
    if col_schema['type'] == 'float':
        return FloatTypeValidator(col_schema).validate
    if col_schema['type'] == 'boolean':
        return BooleanTypeValidator(col_schema).validate
    return None


class BaseTypeValidator(object):
    def __init__(self, schema):
        self.nullable = schema.get('nullable', False)

    def validate(self, value):
        if not self.nullable and pd.isna(value):
            return 'value cannot be null or empty: {}'.format(value)


class ChoiceTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(ChoiceTypeValidator, self).__init__(schema)
        self.choice_properties = schema['choice']
        self.values = self.choice_properties.get('values')

    def validate(self, value):
        super(ChoiceTypeValidator, self).validate(value)
        if self.values is not None and value not in self.values:
            return 'value must be from choices {} : {}'.format(self.values, value)
        return None


class StringTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(StringTypeValidator, self).__init__(schema)
        self.regex = schema.get('regex')

    def validate(self, value):
        super(StringTypeValidator, self).validate(value)
        if self.regex is not None and not re.search(self.regex, value):
            return 'value is not in the proper format regex {} : {}'.format(self.regex, value)


class NumericTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(NumericTypeValidator, self).__init__(schema)
        self.min = schema.get('min')
        self.max = schema.get('max')

    def validate(self, value):
        super(NumericTypeValidator, self).validate(value)
        if self.min is not None and value < self.min or self.max is not None and value > self.max:
            return '{} must be in range {}, {}'.format(value, '[' + str(self.min) if self.min is not None else '(-inf',
                                                       str(self.max) + ']' if self.max is not None else 'inf)')


class IntegerTypeValidator(NumericTypeValidator):
    def __init__(self, schema):
        super(IntegerTypeValidator, self).__init__(schema)

    def validate(self, value):
        if not type(value) in (int, long):
            return 'value must be of type integer: {}'.format(value)
        super(IntegerTypeValidator, self).validate(value)


class FloatTypeValidator(NumericTypeValidator):
    def __init__(self, schema):
        super(FloatTypeValidator, self).__init__(schema)

    def validate(self, value):
        if not type(value) in (int, long, float):
            return 'value must be of type float: {}'.format(value)
        super(FloatTypeValidator, self).validate(value)


class BooleanTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(BooleanTypeValidator, self).__init__(schema)

    def validate(self, value):
        super(BooleanTypeValidator, self).validate(value)
        if not isinstance(value, bool):
            return 'value can only be True or False: {}'.format(value)


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator
    import cea.scripts
    import pprint

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    validator = InputFileValidator()
    locator_methods = ['get_database_construction_standards',
                       'get_database_use_types_properties',
                       'get_database_supply_assemblies',
                       'get_database_air_conditioning_systems',
                       'get_database_envelope_systems',
                       'get_database_conversion_systems',
                       'get_database_distribution_systems',
                       'get_database_feedstocks']
    for locator_method in locator_methods:
        df = pd.read_excel(locator.__getattribute__(locator_method)(), sheet_name=None)
        print('Validating {}'.format(locator_method))
        errors = validator.validate(df, locator_method)
        pprint.pprint(errors)

