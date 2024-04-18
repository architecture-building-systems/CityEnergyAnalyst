


import os
from collections import OrderedDict

from flask_restx import Namespace, Resource, abort
import pandas as pd

from cea.databases import get_regions, get_database_tree, databases_folder_path
from cea.utilities.schedule_reader import schedule_to_dataframe

api = Namespace("Databases", description="Database data for technologies in CEA")

DATABASES_SCHEMA_KEYS = {
    "CONSTRUCTION_STANDARD": ["get_database_construction_standards"],
    "USE_TYPES": ["get_database_standard_schedules_use", "get_database_use_types_properties"],
    "SUPPLY": ["get_database_supply_assemblies"],
    "HVAC": ["get_database_air_conditioning_systems"],
    "ENVELOPE": ["get_database_envelope_systems"],
    "CONVERSION": ["get_database_conversion_systems"],
    "DISTRIBUTION": ["get_database_distribution_systems"],
    "FEEDSTOCKS": ["get_database_feedstocks"],
    "ENERGY_CARRIERS": ["get_database_energy_carriers"],

    # TODO: Remove after databases are merged
    "SUPPLY_NEW": ["get_database_supply_assemblies_new"],
    "CONVERSION_NEW": ["get_database_conversion_systems_new"]
}


# FIXME: Using OrderedDict here due to Python2 unordered dict insertion, change when using Python3
def database_to_dict(db_path):
    out = OrderedDict()
    xls = pd.ExcelFile(db_path)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, keep_default_na=False)
        out[sheet] = df.to_dict(orient='records', into=OrderedDict)
    return out


def schedule_to_dict(schedule_path):
    out = OrderedDict()
    schedule_df = schedule_to_dataframe(schedule_path)
    for df_name, df in schedule_df.items():
        out[df_name] = df.to_dict(orient='records', into=OrderedDict)
    return out


def read_all_databases(database_path):
    out = OrderedDict()
    db_info = get_database_tree(database_path)
    for category in db_info['categories'].keys():
        out[category] = OrderedDict()
        for db_name in db_info['categories'][category]['databases']:
            db_files = db_info['databases'][db_name]['files']
            if db_name == 'USE_TYPES':
                out[category][db_name] = OrderedDict()
                out[category][db_name]['SCHEDULES'] = OrderedDict()
                for db_file in db_files:
                    # Use type property file
                    if db_file['name'] == 'USE_TYPE_PROPERTIES':
                        out[category][db_name]['USE_TYPE_PROPERTIES'] = database_to_dict(db_file['path'])
                    # Schedule files
                    elif db_file['extension'] == '.csv':
                        out[category][db_name]['SCHEDULES'][db_file['name']] = schedule_to_dict(db_file['path'])
            else:
                for db_file in db_files:
                    out[category][db_name] = database_to_dict(db_file['path'])
    return out


@api.route("/region")
class DatabaseRegions(Resource):
    def get(self):
        return {'regions': get_regions()}


@api.route("/region/<string:region>")
class DatabaseRegion(Resource):
    def get(self, region):
        regions = get_regions()
        if region not in regions:
            abort(400, "Could not find '{}' region. Try instead {}".format(region, ", ".join(regions)))
        return {"categories": get_database_tree(os.path.join(databases_folder_path, region))['categories']}


@api.route("/region/<string:region>/databases")
class DatabaseData(Resource):
    def get(self, region):
        regions = get_regions()
        if region not in regions:
            abort(400, "Could not find '{}' region. Try instead {}".format(region, ", ".join(regions)))
        try:
            return read_all_databases(os.path.join(databases_folder_path, region))
        except IOError as e:
            print(e)
            abort(500, str(e))


def convert_path_to_name(schema_dict):
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator('')
    for sheet_name, sheet_info in schema_dict.items():
        for variable_name, schema in sheet_info['columns'].items():
            if 'choice' in schema and 'lookup' in schema['choice']:
                database_path = locator.__getattribute__(schema['choice']['lookup']['path'])()
                schema['choice']['lookup']['database_category'] = os.path.basename(os.path.dirname(database_path))
                schema['choice']['lookup']['database_name'] = os.path.basename(os.path.splitext(database_path)[0])
    return schema_dict


@api.route("/schema")
class DatabaseSchema(Resource):
    def get(self):
        import cea.scripts
        schemas = cea.schemas.schemas(plugins=[])
        out = {}
        for db_name, db_schema_keys in DATABASES_SCHEMA_KEYS.items():
            out[db_name] = {}
            for db_schema_key in db_schema_keys:
                try:
                    out[db_name].update(convert_path_to_name(schemas[db_schema_key]['schema']))
                except KeyError as ex:
                    raise KeyError(f"Could not convert_path_to_name for {db_name}/{db_schema_key}. {ex}")
        return out
