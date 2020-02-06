import os
import glob
from collections import OrderedDict

from flask_restplus import Namespace, Resource, abort
import pandas

import cea.databases
import cea.scripts
from cea.utilities.schedule_reader import read_cea_schedule

api = Namespace("Databases", description="Database data for technologies in CEA")
cea_database_path = os.path.dirname(cea.databases.__file__)

# FIXME: Should use inputlocator to find default databases instead? But still need a way to map database names to their locator method for schemas
# { db_type: { db_name: db_prop, ... }, ... }
DATABASES = OrderedDict([
    ("archetypes", {
        "construction_properties": {
            "file_ext": ".xlsx",
            "schema_key": "get_archetypes_properties"
        },
        "schedules": {
            "file_ext": "",  # Folder
            "schema_key": "get_database_standard_schedules_use"
        }
    }),
    ("lifecycle", {
        "lca_buildings": {
            "file_ext": ".xlsx",
            "schema_key": "get_database_lca_buildings"
        },
        "lca_mobility": {
            "file_ext": ".xls",
            "schema_key": "get_database_lca_mobility"
        }
    }),
    ("systems", {
        "air_conditioning_systems": {
            "file_ext": ".xls",
            "schema_key": "get_database_air_conditioning_systems"
        },
        "envelope_systems": {
            "file_ext": ".xls",
            "schema_key": "get_database_envelope_systems"
        },
        "supply_systems": {
            "file_ext": ".xls",
            "schema_key": "get_database_supply_systems"
        }
    })
])

DATABASES_TYPE_MAP = {db_name: db_type for db_type, db_dict in DATABASES.items() for db_name in db_dict}
DATABASE_NAMES = DATABASES_TYPE_MAP.keys()


def get_regions():
    return [folder for folder in os.listdir(cea_database_path) if folder != "weather"
            and os.path.isdir(os.path.join(cea_database_path, folder))]


# # FIXME: Temp solution for database locators for shipped databases
def get_database_path(region, db_name):
    db_type = DATABASES_TYPE_MAP[db_name]
    file_name = '{}{}'.format(db_name, DATABASES[db_type][db_name]['file_ext'])
    return os.path.join(cea_database_path, region, db_type, file_name)


def get_schedules_dict(schedule_path):
    out = {}
    schedule_files = glob.glob(os.path.join(schedule_path, "*.csv"))
    for schedule_file in schedule_files:
        archetype = os.path.splitext(os.path.basename(schedule_file))[0]
        schedule_data, schedule_complementary_data = read_cea_schedule(os.path.join(schedule_path, schedule_file))
        df = pandas.DataFrame(schedule_data).set_index(["DAY", "HOUR"])
        out[archetype] = {'SCHEDULES': {schedule_type: {day: df.loc[day][schedule_type].values.tolist()
                                                        for day in df.index.levels[0]}
                                        for schedule_type in df.columns}}
        out[archetype].update(schedule_complementary_data)
    return out


def get_database_dict(db_path):
    out = OrderedDict()
    xls = pandas.ExcelFile(db_path)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        # Replace NaN with null to prevent JSON errors
        out[sheet] = df.where(pandas.notnull(df), None).to_dict(orient='records', into=OrderedDict)
    return out

def write_database_dict(db_dict):


@api.route("/")
class DatabaseInfo(Resource):
    def get(self):
        databases = OrderedDict((db_type, [db_name for db_name in db_dict]) for db_type, db_dict in DATABASES.items())
        return {'regions': get_regions(), 'databases': databases}

# FIXME: Separate db equals 'all' logic. Too messy
@api.route("/<string:region>/<string:db>")
class Database(Resource):
    def get(self, region, db):
        regions = get_regions()
        if region not in regions:
            abort(400, "Could not find '{}' region. Try instead {}".format(region, ", ".join(regions)))
        try:
            if db == 'all':
                out = OrderedDict()
                for db_type, db_dict in DATABASES.items():
                    out[db_type] = OrderedDict()
                    for db_name in db_dict:
                        db_path = get_database_path(region, db_name)
                        if db_name == 'schedules':
                            out[db_type][db_name] = get_schedules_dict(db_path)
                        else:
                            out[db_type][db_name] = get_database_dict(db_path)
                return out
            elif db in DATABASE_NAMES:
                db_path = get_database_path(region, db)
                if db == 'schedules':
                    return get_schedules_dict(db_path)
                else:
                    return get_database_dict(db_path)
            else:
                abort(400, "Could not find '{}' database. Try instead {}".format(db, ", ".join(DATABASE_NAMES)))
        except IOError as e:
            print(e)
            abort(500, e.message)


@api.route("/schema/<string:db>")
class DatabaseSchema(Resource):
    def get(self, db):
        import cea.glossary
        schemas = cea.scripts.schemas()

        if db == 'all':
            out = {}
            for db_type, db_dict in DATABASES.items():
                out[db_type] = {}
                for db_name, db_props in db_dict.items():
                    out[db_type][db_name] = schemas[db_props['schema_key']]['schema']
            return out
        elif db in DATABASE_NAMES:
            db_type = DATABASES_TYPE_MAP[db]
            db_schema = schemas[DATABASES[db_type][db]['schema_key']]['schema']
            return db_schema
        else:
            abort(400, "Could not find '{}' database. Try instead {}".format(db, ", ".join(DATABASE_NAMES)))
