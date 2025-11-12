"""
Databases verification
This tool is used as to check the format of each database
"""

from cea.schemas import schemas
import pandas as pd
import re

from cea.utilities import simple_memoize
from cea.utilities.schedule_reader import get_all_schedule_names

COLUMNS_ZONE_GEOMETRY = ['name', 'floors_bg', 'floors_ag', 'void_deck', 'height_bg', 'height_ag']
COLUMNS_SURROUNDINGS_GEOMETRY = ['name', 'height_ag', 'floors_ag']
COLUMNS_ZONE_TYPOLOGY = ['name', 'year', 'const_type',
                         'use_type1', 'use_type1r', 'use_type2', 'use_type2r', 'use_type3', 'use_type3r']
NAME_COLUMN = 'name'
COLUMNS_ZONE = ['name', 'floors_bg', 'floors_ag', 'void_deck', 'height_bg', 'height_ag', 'reference', 'geometry',
                'year', 'const_type', 'use_type1', 'use_type1r', 'use_type2', 'use_type2r', 'use_type3', 'use_type3r',
                'house_no', 'street', 'postcode', 'house_name', 'resi_type', 'city', 'country']


def assert_columns_names(dataframe: pd.DataFrame, columns):
    try:
        dataframe[columns]
    except ValueError:
        print(
            "one or more columns in the Zone or Surroundings input files is not compatible with CEA, please ensure the column" +
            " names comply with:", columns)


def assert_input_geometry_acceptable_values_floor_height(zone_df: pd.DataFrame):
    # Rule 0. nothing can be negative
    numeric_dtypes = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    zone_df_data = zone_df.select_dtypes(include=numeric_dtypes)
    rule0 = (zone_df_data < 0.0).any().any()
    if rule0:
        raise Exception("There are negative values in your geometry. This is not possible to simulate in CEA at the "
                        "moment Please verify your Zone or Surroundings shapefile file")

    # Rule 1. Floors above ground cannot be less than 1 or negative.
    rule1_1 = (zone_df['floors_ag'] < 1).any()
    rule1_2 = (zone_df['height_ag'] < 1.0).any()
    if rule1_1 or rule1_2:
        raise Exception("one of more buildings have less than one floor above ground or the height above ground is "
                        "less than 1 meter. This is not possible to simulate in CEA at the moment. Please verify your "
                        "Zone or Surroundings shapefile file")

    # Rule 2. Where floor height is less than 1m on average above ground.
    rule2 = (zone_df['height_ag'] < zone_df['floors_ag']).any()
    if rule2:
        raise Exception('one of more buildings report less than 1m height per floor. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or Surroundings shapefile file')

    # Rule 3. floors below ground cannot be negative
    rule3 = (zone_df['floors_bg'] < 0).any()
    if rule3:
        raise Exception('one of more buildings have a negative floor below ground. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or Surroundings file')


def assert_input_geometry_acceptable_values_floor_height_surroundings(surroundings_df):
    # Rule 0. nothing can be negative
    numeric_dtypes = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    surroundings_df_data = surroundings_df.select_dtypes(include=numeric_dtypes)
    rule0 = surroundings_df_data.where(surroundings_df_data < 0.0).any().any()
    if rule0:
        raise Exception("There are negative values in your geometry. This is not possible to simulate in CEA at the "
                        "moment Please verify your Zone or Surroundings shapefile file")

    # Rule 1. Floors above ground cannot be less than 1 or negative.
    rule1_1 = surroundings_df['floors_ag'].where(surroundings_df['floors_ag'] < 1).any()
    rule1_2 = surroundings_df['height_ag'].where(surroundings_df['height_ag'] < 1.0).any()
    if rule1_1 or rule1_2:
        raise Exception("one of more buildings have less than one floor above ground or the height above ground is "
                        "less than 1 meter. This is not possible to simulate in CEA at the moment. Please verify your "
                        "Zone or Surroundings shapefile file")

    # Rule 2. Where floor height is less than 1m on average above ground.
    floor_height_check = surroundings_df['height_ag'] / surroundings_df['floors_ag']
    rule2 = (floor_height_check <= 1.0).any()
    if rule2:
        raise Exception('one of more buildings have less report less than 1m height per floor. This is not possible'
                        'to simulate in CEA at the moment. Please verify your Zone or Surroundings shapefile file')


def assert_input_geometry_only_polygon(buildings_df):
    not_polygon = buildings_df.geometry.type != 'Polygon'
    invalid_buildings = buildings_df[not_polygon]['name'].values
    if len(invalid_buildings):
        raise Exception(
            'Some buildings are not of type "Polygon": {buildings}'.format(buildings=', '.join(invalid_buildings)))


def check_duplicated_names(df):
    duplicated_names = df[NAME_COLUMN].duplicated()
    if duplicated_names.any():
        raise Exception(
            'Duplicated names in the input file: {names}'.format(names=', '.join(df[duplicated_names][NAME_COLUMN].values)))


def check_na_values(df, columns=None):
    if columns is not None:
        df = df[columns]

    na_columns = df.columns[df.isna().any()].tolist()
    if na_columns:
        raise ValueError(f'There are NA values detected in the following required columns: {", ".join(na_columns)}')
    
def check_void_deck_values(df):
    """
    void_deck should exist in the zone geometry file. If not, create a new column with void_deck = 0 and print a warning.
    If void_deck exists, check if it's >= 0 and is a integer.
    """

    # Check if void_deck contains integer-like values (handles both int and float dtypes from shapefiles)
    if not pd.api.types.is_integer_dtype(df['void_deck']):
        # If it's float, check if all values are whole numbers
        if pd.api.types.is_float_dtype(df['void_deck']):
            if not (df['void_deck'] % 1 == 0).all():
                raise ValueError('The void_deck column should contain only integer values (no decimals). Please check your zone geometry file.')
            # Convert to integer type if all values are whole numbers
            df['void_deck'] = df['void_deck'].astype(int)
        else:
            raise ValueError('The void_deck column should be of integer type. Please check your zone geometry file.')

    if (df['void_deck'] < 0).any():
        raise ValueError('The void_deck column should not contain negative values. Please check your zone geometry file.')

    if (df['void_deck'] > df['floors_ag']).any():
        raise ValueError('The void_deck column should not contain values greater than the number of floors above ground. '
                         'Please check your zone geometry file.')

def verify_input_geometry_zone(zone_df):
    # TODO: remove this when void_deck always exist in geometry
    not_exist_before = False
    if 'void_deck' not in zone_df.columns:
        # add void_deck to pass the verification first
        Warning('The void_deck column should always exist in the zone geometry file. ')
        zone_df['void_deck'] = 0
        not_exist_before = True
        
    # Verification 1. verify if all the column names are correct
    assert_columns_names(zone_df, COLUMNS_ZONE_GEOMETRY)

    # Verification 2. verify if the floor_height ratio is correct
    assert_input_geometry_acceptable_values_floor_height(zone_df)

    # Verification 3. verify geometries only contain Polygon
    assert_input_geometry_only_polygon(zone_df)

    check_na_values(zone_df, columns=COLUMNS_ZONE_GEOMETRY)

    check_duplicated_names(zone_df)

    check_void_deck_values(zone_df)

    if not_exist_before:
        # delete the void_deck column if it was not exist before
        zone_df.drop(columns=['void_deck'], inplace=True)

def verify_input_geometry_surroundings(surroundings_df):
    # Verification 1. verify if all the column names are correct
    assert_columns_names(surroundings_df, COLUMNS_SURROUNDINGS_GEOMETRY)

    # Verification 2. verify if the floor_height ratio is correct
    assert_input_geometry_acceptable_values_floor_height_surroundings(surroundings_df)

    # Verification 3. verify geometries only contain Polygon
    assert_input_geometry_only_polygon(surroundings_df)


def verify_input_typology(typology_df):
    # Verification 1. verify if all the column names are correct
    assert_columns_names(typology_df, COLUMNS_ZONE_TYPOLOGY)

    check_na_values(typology_df, columns=COLUMNS_ZONE_TYPOLOGY)

    check_duplicated_names(typology_df)


def verify_input_terrain(terrain_raster):
    # Verification 1. verify that we can create the geometry
    if terrain_raster is None:
        raise Exception("Your input terrain file is corrupted. Please verify that you have a non-null raster,"
                        "and that the grid of it be at least 5 X 5 meters, smaller grid sizes will drastically"
                        "make the solar radiation engine slow")


class InputFileValidator(object):
    def __init__(self, input_locator=None, plugins=None):
        # Need locator to read other files if lookup choice values
        self.locator = input_locator
        self.plugins = plugins if plugins is not None else []

    def validate(self, data, data_schema):
        """
        Takes a dataframe and validates it based on the schema provided from schemas.yml file
        :param data: Dataframe of data to be tested
        :param data_schema: Schema of dataframe
        :return: list of errors where errors are represented as [dict(), str()] being location and message of the error
        """
        file_type = data_schema['file_type']
        errors = []
        if file_type in ['xlsx', 'xls', 'schedule']:
            for sheet, _data in data.items():
                sheet_errors = self._run_all_tests(_data, data_schema['schema'][sheet])
                if sheet_errors:
                    errors.append([{"sheet": str(sheet)}, sheet_errors])
        else:
            errors = self._run_all_tests(data, data_schema['schema'])

        return errors

    def _run_all_tests(self, data, data_schema):
        """
        Runs all tests and reduce errors to a single list
        :param data: Dataframe of data to be tested
        :param data_schema: Schema for dataframe
        :return: list of errors
        """
        return sum([self.assert_columns_names(data, data_schema),
                    self.assert_column_values(data, data_schema),
                    self.assert_constraints(data, data_schema)], [])

    def assert_columns_names(self, data, data_schema):
        """
        Check if column names in schema are found in data
        :param data: Dataframe of data to be tested
        :param data_schema: Schema for dataframe
        :return: list of errors
        """
        columns = data_schema['columns'].keys()
        missing_columns = [col for col in columns if col not in data.columns]
        extra_columns = [col for col in data.columns if col not in columns]
        return [[{'column': str(col)}, 'Column is missing'] for col in missing_columns] + \
            [[{'column': str(col)}, 'Column is not in schema'] for col in extra_columns]

    def assert_column_values(self, data, data_schema):
        """
        Run validation on data column values based on column value types in specified in schema
        :param data: Dataframe of data to be tested
        :param data_schema: Schema for dataframe
        :return: list of errors
        """
        columns = data_schema['columns'].keys()
        # Only loop through valid columns that exist
        filter_columns = [col for col in columns if col in data.columns]
        errors = []
        for column in filter_columns:
            col_schema = data_schema['columns'][column]
            if 'choice' in col_schema:
                lookup_data = self._get_choice_lookup_data(col_schema)
                column_errors = data[column].apply(ChoiceTypeValidator(col_schema, lookup_data).validate).dropna()
            else:
                column_errors = data[column].apply(get_validator_func(col_schema)).dropna()
            for index, error in column_errors.items():
                errors.append([{'row': int(index) + 1, 'column': str(column)}, error])

            # Make sure values are unique
            if 'primary' in col_schema:
                duplicates = data[column][data[column].duplicated(keep=False)]
                for index, col_value in duplicates.items():
                    errors.append(
                        [{'row': int(index) + 1, 'column': str(column)}, 'value is not unique: {}'.format(col_value)])
        return errors

    def assert_constraints(self, data, data_schema):
        """
        Check if columns fit constraints (row-based only) specified in schema
        :param data: Dataframe of data to be tested
        :param data_schema: Schema for dataframe
        :return: list of errors
        """
        constraints = data_schema.get('constraints')
        errors = []
        if constraints:
            for name, constraint in constraints.items():
                try:
                    result = data.eval(constraint)
                    # Only process
                    if isinstance(result, pd.Series) and result.dtype == 'bool':
                        for index, error in result[~result].items():
                            errors.append([{'row': int(index) + 1}, 'failed constraint: {}'.format(constraint)])
                except Exception as e:
                    print(e)
        return errors

    def _get_choice_lookup_data(self, schema):
        lookup_prop = schema['choice'].get('lookup')
        if self.locator and lookup_prop:
            locator_method_name = lookup_prop['path']
            file_type = schemas(self.plugins)[locator_method_name]['file_type']
            data = self._read_lookup_data_file(locator_method_name, file_type)
            return data[lookup_prop['sheet']][lookup_prop['column']].tolist() if data else None
        return None

    @simple_memoize
    def _read_lookup_data_file(self, locator_method_name, file_type):
        if file_type in ['xlsx', 'xls']:
            return pd.read_excel(self.locator.__getattribute__(locator_method_name)(), sheet_name=None)
        return None


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
            return 'value cannot be null or empty: got {}'.format(value)


class ChoiceTypeValidator(BaseTypeValidator):
    def __init__(self, schema, choices):
        super(ChoiceTypeValidator, self).__init__(schema)
        self.choice_properties = schema['choice']
        self.choices = choices
        self.values = self.choice_properties.get('values')

    def validate(self, value):
        errors = super(ChoiceTypeValidator, self).validate(value)
        if errors:
            return errors
        if self.choices and value not in self.choices or self.values and value not in self.values:
            return 'value must be from choices {} : got {}'.format(
                [str(choice) for choice in self.choices or self.values], value)
        return None


class StringTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(StringTypeValidator, self).__init__(schema)
        self.regex = schema.get('regex')

    def validate(self, value):
        errors = super(StringTypeValidator, self).validate(value)
        if errors:
            return errors
        if self.regex is not None and not re.search(self.regex, value):
            return 'value is not in the proper format regex {} : got {}'.format(self.regex, value)


class NumericTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(NumericTypeValidator, self).__init__(schema)
        self.min = schema.get('min')
        self.max = schema.get('max')

    def validate(self, value):
        errors = super(NumericTypeValidator, self).validate(value)
        if errors:
            return errors
        if self.min is not None and value < self.min or self.max is not None and value > self.max:
            return 'value must be in range {}, {}: got {}'.format('[' + str(self.min)
                                                                  if self.min is not None else '(-inf',
                                                                  str(self.max) + ']'
                                                                  if self.max is not None else 'inf)',
                                                                  value)


class IntegerTypeValidator(NumericTypeValidator):
    def __init__(self, schema):
        super(IntegerTypeValidator, self).__init__(schema)

    def validate(self, value):
        if not isinstance(value, int):
            return 'value must be of type integer: got {}'.format(value)
        return super(IntegerTypeValidator, self).validate(value)


class FloatTypeValidator(NumericTypeValidator):
    def __init__(self, schema):
        super(FloatTypeValidator, self).__init__(schema)

    def validate(self, value):
        if not isinstance(value, float):
            return 'value must be of type float: got {}'.format(value)
        return super(FloatTypeValidator, self).validate(value)


class BooleanTypeValidator(BaseTypeValidator):
    def __init__(self, schema):
        super(BooleanTypeValidator, self).__init__(schema)

    def validate(self, value):
        errors = super(BooleanTypeValidator, self).validate(value)
        if errors:
            return errors
        if not isinstance(value, bool):
            return 'value can only be True or False: got {}'.format(value)


def main():
    import cea.config
    import cea.inputlocator
    from cea.utilities.schedule_reader import schedule_to_dataframe
    import pprint

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    _schemas = schemas(plugins=[])
    validator = InputFileValidator(locator, plugins=config.plugins)
    locator_methods = ['get_database_construction_standards',
                       'get_database_use_types_properties',
                       'get_database_supply_assemblies',
                       'get_database_air_conditioning_systems',
                       'get_database_envelope_systems',
                       'get_database_conversion_systems',
                       'get_database_distribution_systems',
                       'get_database_feedstocks']

    for locator_method in locator_methods:
        db_path = locator.__getattribute__(locator_method)()
        df = pd.read_excel(db_path, sheet_name=None)
        print('Validating {}'.format(db_path))
        schema = _schemas[locator_method]
        errors = validator.validate(df, schema)
        if errors:
            pprint.pprint(errors)
        else:
            print("No errors found")

    for use_types in get_all_schedule_names(locator.get_database_use_types_folder()):
        db_path = locator.get_database_standard_schedules_use(use_types)
        df = schedule_to_dataframe(db_path)
        print('Validating {}'.format(db_path))
        schema = _schemas['get_database_standard_schedules_use']
        errors = validator.validate(df, schema)
        if errors:
            pprint.pprint(errors)
        else:
            print("No errors found")


if __name__ == '__main__':
    main()
