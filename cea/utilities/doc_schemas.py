"""
Create a schemas.yml-compatible entry given a locator method by reading the file from the current scenario.

NOTE: This is meant to help _write_ the schemas.yml file, not to CREATE it - you'll have to edit constraints and types
      by hand too!
"""





import os
import yaml
import json
import pandas as pd
from pandas.errors import EmptyDataError
import dateutil.parser
import cea.config
import cea.schemas
import cea.inputlocator
import cea.utilities.dbf
import geopandas

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_schema(scenario, locator_method, args=None):
    if not args:
        args = {}
    abs_path = read_path(args, locator_method, scenario)
    file_type = read_file_type(abs_path)

    buildings = cea.inputlocator.InputLocator(scenario).get_zone_building_names()

    return {
        locator_method: {
            "file_path": read_file_path(abs_path, scenario, args),
            "file_type": file_type,
            "schema": read_schema_details(abs_path, file_type, buildings),
        }
    }


def read_schema_details(abs_path, file_type, buildings):
    """
    Returns schema as a dict, based on file_type

    :return: schema of each file. E.g., schema = {columns : {Hs: {...}, Ns: {...}, ...}
    :rtype: dict
    """
    schema_readers = {
        "xls": get_xls_schema,
        "xlsx": get_xls_schema,
        "tif": get_tif_schema,
        "tiff": get_tif_schema,
        "csv": get_csv_schema,
        "json": get_json_schema,
        "epw": get_epw_schema,
        "dbf": get_dbf_schema,
        "shp": get_shp_schema,
        "html": get_html_schema,
    }
    return schema_readers[file_type](abs_path, buildings)


def read_file_type(abs_path):
    # removes "." at the beginning of extension
    _, ext = os.path.splitext(abs_path)
    if ext.startswith("."):
        ext = ext[1:]
    return ext


def read_path(args, locator_method, scenario):
    """Returns the path, as returned by the locator method"""
    locator = cea.inputlocator.InputLocator(scenario=scenario)
    method = getattr(locator, locator_method)
    path = method(**args)
    return path


def read_file_path(abs_path, scenario, args):
    """
    Returns the path relative to scenario, with arguments replaced. This assumes that the values in args
    were substituted. this ends up in the "file_path" key in the schema
    """
    file_path = os.path.relpath(abs_path, scenario)
    for k, v in args.items():
        if v in file_path:
            file_path = file_path.replace(v, "{%s}" % k)
    return file_path.replace("\\", "/")


def get_csv_schema(filename, buildings):
    try:
        df = pd.read_csv(filename)
    except EmptyDataError:
        # csv file is empty
        return None
    schema = {"columns": {}}
    for column_name in df.columns:
        column_name = replace_repetitive_column_names(column_name, buildings)
        schema["columns"][column_name] = get_column_schema(df[column_name])
    return schema


def replace_repetitive_column_names(column_name, buildings):
    """
    Returns column_name _unless_ it's one of a few special cases (building names, PIPE names, NODE names, srf names)
    :param str column_name: the name of the column
    :return: column_name or similar (for repetitive column names)
    """
    if column_name.startswith('srf'):
        column_name = "srf0"
    if column_name.startswith('PIPE'):
        column_name = "PIPE0"
    if column_name.startswith('NODE'):
        column_name = "NODE0"
    if column_name in buildings:
        column_name = buildings[0]
    return column_name


def get_json_schema(filename, buildings):
    schema = {}
    with open(filename, 'r') as f:
        json_file = json.load(f)
        try:
            df = pd.DataFrame(json_file)
            for column_name in df.columns:
                column_name = replace_repetitive_column_names(column_name, buildings)
                schema[column_name.encode('ascii', 'ignore')] = get_column_schema(df[column_name])
        except Exception:
            # in case json file has an odd shape, get a simplified schema
            for key in json_file.keys():
                print(type(json_file[key]).__name__)
                schema[key] = {'type': type(json_file[key]).__name__}
    return schema


def get_epw_schema(filename, _):
    epw_labels = ['year (index = 0)', 'month (index = 1)', 'day (index = 2)', 'hour (index = 3)',
                  'minute (index = 4)', 'datasource (index = 5)', 'drybulb_C (index = 6)',
                  'dewpoint_C (index = 7)',
                  'relhum_percent (index = 8)', 'atmos_Pa (index = 9)', 'exthorrad_Whm2 (index = 10)',
                  'extdirrad_Whm2 (index = 11)', 'horirsky_Whm2 (index = 12)',
                  'glohorrad_Whm2 (index = 13)',
                  'dirnorrad_Whm2 (index = 14)', 'difhorrad_Whm2 (index = 15)',
                  'glohorillum_lux (index = 16)',
                  'dirnorillum_lux (index = 17)', 'difhorillum_lux (index = 18)',
                  'zenlum_lux (index = 19)',
                  'winddir_deg (index = 20)', 'windspd_ms (index = 21)',
                  'totskycvr_tenths (index = 22)',
                  'opaqskycvr_tenths (index = 23)', 'visibility_km (index = 24)',
                  'ceiling_hgt_m (index = 25)',
                  'presweathobs (index = 26)', 'presweathcodes (index = 27)',
                  'precip_wtr_mm (index = 28)',
                  'aerosol_opt_thousandths (index = 29)', 'snowdepth_cm (index = 30)',
                  'days_last_snow (index = 31)', 'Albedo (index = 32)',
                  'liq_precip_depth_mm (index = 33)',
                  'liq_precip_rate_Hour (index = 34)']

    db = pd.read_csv(filename, skiprows=8, header=None, names=epw_labels)
    schema = {}
    for attr in db:
        schema[attr] = get_column_schema(db[attr])
    return schema


def get_dbf_schema(filename, buildings):
    db = cea.utilities.dbf.dbf_to_dataframe(filename)
    return extract_df_schema(db, buildings)


def extract_df_schema(df, scenario):
    schema = {"columns": {}}
    for attr in df:
        attr = replace_repetitive_column_names(attr, scenario)
        meta = get_column_schema(df[attr])
        if attr == 'geometry':
            meta['sample_data'] = '((x1 y1, x2 y2, ...))'
        schema["columns"][attr] = meta
    return schema


def get_shp_schema(filename, scenario):
    df = geopandas.read_file(filename)
    return extract_df_schema(df, scenario)


def get_xls_schema(filename, _):
    sheets = pd.read_excel(filename, sheet_name=None)
    schema = {}
    for sheet in sheets.keys():
        sheet_schema = {"columns": {}}
        sheet_df = sheets[sheet]
        # if xls seems to have row attributes
        if 'Unnamed: 1' in sheets[sheet].keys():
            sheet_df = sheet_df.T
            # filter the nans
            new_columns = []
            for column_name in sheet_df.columns:
                if column_name:
                    new_columns.append(column_name)
            # change index to numbered
            sheet_df.index = range(len(sheet_df))
            # select only non-nan columns
            sheet_df = sheet_df[new_columns]
        for column_name in sheet_df.columns:
            sheet_schema["columns"][column_name] = get_column_schema(sheet_df[column_name])
        schema[sheet] = sheet_schema
    return schema


def get_tif_schema(_, __):
    return {
        'raster_value': {
            'sample_data': 1.0,
            'types_found': [float]
        }}


def get_html_schema(_, __):
    """We don't need to keep a schema of html files - these are outputs anyway"""
    return None


def get_column_schema(df_series):
    """
    Returns schema of each column as a dict

    :return: schema of each column. E.g., column_schema = {pandas: {desc: ... , kind: f, type: float64},
    sample_data: 0.16, type: float, types_found: [float, ...]}
    :rtype: dict
    """
    types_found = set()
    column_schema = {}
    for value in df_series:
        if value == value:
            column_schema['sample_data'] = value
            if is_date(value):
                types_found.add('date')
            elif isinstance(value, str):
                # column_schema['sample_data'] = value.encode('ascii', 'ignore') # TODO: remove if not use
                types_found.add('string')
            else:
                types_found.add(type(value).__name__)
        # declare nans
        if value != value:
            types_found.add(None)
    column_schema['types_found'] = list(types_found)
    column_schema["pandas"] = {
        "type": df_series.dtype.name,
        "kind": df_series.dtype.kind,
    }
    if df_series.dtype.kind in {"f", "i"}:
        column_schema["pandas"]["desc"] = df_series.describe().to_dict()

    column_type = lookup_column_type(df_series)
    column_schema["type"] = column_type
    return column_schema


def lookup_column_type(df_series):
    kind_map = {"f": "float", "i": "int", "s": "string", "O": "object", "b": "boolean"}
    column_type = kind_map[df_series.dtype.kind]
    if column_type == "object":
        column_type = type(df_series.values[0]).__name__
    return column_type


def is_date(value):
    if not isinstance(value, str):
        return False
    try:
        dateutil.parser.parse(value)
        return True
    except ValueError:
        return False



def main(config: cea.config.Configuration):
    """
    Read the schema entry for a locator method, compare it to the current entry and print out a new, updated version.
    """
    print(yaml.safe_dump(read_schema(config.scenario, config.schemas.locator_method, config.schemas.args), default_flow_style=False))


if __name__ == '__main__':
    main(cea.config.Configuration())
