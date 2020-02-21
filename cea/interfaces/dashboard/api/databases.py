import os
import glob
from collections import OrderedDict

from flask_restplus import Namespace, Resource, abort
import pandas

import cea.databases
import cea.scripts
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule

api = Namespace("Databases", description="Database data for technologies in CEA")
cea_database_path = os.path.dirname(cea.databases.__file__)

DATABASES = OrderedDict([
    ("archetypes", OrderedDict([
        ("CONSTRUCTION_STANDARDS", {
            "filename": "CONSTRUCTION_STANDARDS.xlsx",
            "schema_key": "get_database_construction_standards"
        }),
        # FIXME: Find a way to include schema info
        ("USE_TYPES", None)  # Handle manually
    ])),
    ("assemblies", OrderedDict([
        ("SUPPLY", {
            "filename": "SUPPLY.xls",
            "schema_key": "get_database_supply_assemblies"
        }),
        ("HVAC", {
            "filename": "HVAC.xls",
            "schema_key": "get_database_air_conditioning_systems"
        }),
        ("ENVELOPE", {
            "filename": "ENVELOPE.xls",
            "schema_key": "get_database_envelope_systems"
        }),
    ])),
    ("components", OrderedDict([
        ("CONVERSION", {
            "filename": "CONVERSION.xls",
            "schema_key": "get_database_conversion_systems"
        }),
        ("DISTRIBUTION", {
            "filename": "DISTRIBUTION.xls",
            "schema_key": "get_database_distribution_systems"
        }),
        ("FEEDSTOCKS", {
            "filename": "FEEDSTOCKS.xls",
            "schema_key": "get_database_feedstocks"
        })
    ]))
])

DATABASES_TYPE_MAP = {db_name: db_type for db_type, db_dict in DATABASES.items() for db_name in db_dict}
DATABASE_NAMES = DATABASES_TYPE_MAP.keys()


def get_regions():
    return [folder for folder in os.listdir(cea_database_path) if folder != "weather"
            and os.path.isdir(os.path.join(cea_database_path, folder))]


def get_database_path(region, db_name):
    db_type = DATABASES_TYPE_MAP[db_name]
    return os.path.join(cea_database_path, region, db_type, DATABASES[db_type][db_name]['filename'])


def get_schedules_folder_path(region):
    return os.path.join(cea_database_path, region, 'archetypes', 'use_types')


def get_use_type_properties_path(region):
    return os.path.join(cea_database_path, region, 'archetypes', 'use_types', 'use_types_properties.xlsx')


def get_all_schedules_dict(schedules_folder):
    """Read all schedules in schedules folder to a dict with their names as keys"""
    out = {}
    schedule_files = glob.glob(os.path.join(schedules_folder, "*.csv"))
    for schedule_file in schedule_files:
        archetype = os.path.splitext(os.path.basename(schedule_file))[0]
        schedule_path = os.path.join(schedules_folder, schedule_file)
        out[archetype] = schedule_to_dict(schedule_path)
    return out


def schedule_to_dict(schedule_path):
    schedule_data, schedule_complementary_data = read_cea_schedule(schedule_path)
    df = pandas.DataFrame(schedule_data).set_index(['DAY', 'HOUR'])
    out = {'SCHEDULES': {schedule_type: {day: df.loc[day][schedule_type].values.tolist() for day in df.index.levels[0]}
                         for schedule_type in df.columns}}
    out.update(schedule_complementary_data)
    return out


def schedule_dict_to_file(schedule_dict, schedule_path):
    schedule_data = schedule_dict['SCHEDULES']
    schedule_complementary_data = {'MONTHLY_MULTIPLIER': schedule_dict['MONTHLY_MULTIPLIER'],
                                   'METADATA': schedule_dict['METADATA']}

    data = pandas.DataFrame()
    for day in ['WEEKDAY', 'SATURDAY', 'SUNDAY']:
        df = pandas.DataFrame({'HOUR': range(1, 25), 'DAY': [day] * 24})
        for schedule_type, schedule in schedule_data.items():
            df[schedule_type] = schedule[day]
        data = data.append(df, ignore_index=True)
    save_cea_schedule(data.to_dict('list'), schedule_complementary_data, schedule_path)
    print('Schedule file written to {}'.format(schedule_path))


def use_type_properties_to_dict(db_path):
    out = OrderedDict()
    xls = pandas.ExcelFile(db_path)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, keep_default_na=False).set_index('code').round(1)
        out[sheet] = df.to_dict(orient='index', into=OrderedDict)
    return out


def use_type_properties_dict_to_file(db_dict, db_path):
    with pandas.ExcelWriter(db_path) as writer:
        for sheet_name, data in db_dict.items():
            df = pandas.DataFrame.from_dict(data, orient='index').dropna(axis=0, how='all').reindex(data.keys())
            df.index.name = 'code'
            df.to_excel(writer, sheet_name=sheet_name)


def database_to_dict(db_path):
    out = OrderedDict()
    xls = pandas.ExcelFile(db_path)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, keep_default_na=False)
        out[sheet] = df.to_dict(orient='records', into=OrderedDict)
    return out


def database_dict_to_file(db_dict, db_path):
    with pandas.ExcelWriter(db_path) as writer:
        for sheet_name, data in db_dict.items():
            df = pandas.DataFrame(data).dropna(axis=0, how='all')
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print('Database file written to {}'.format(db_path))


@api.route("/")
class DatabaseInfo(Resource):
    def get(self):
        databases = OrderedDict((db_type, [db_name for db_name in db_dict]) for db_type, db_dict in DATABASES.items())
        return {'regions': get_regions(), 'databases': databases}


@api.route("/<string:region>/all")
class DatabaseAll(Resource):
    def get(self, region):
        regions = get_regions()
        if region not in regions:
            abort(400, "Could not find '{}' region. Try instead {}".format(region, ", ".join(regions)))
        try:
            out = OrderedDict()
            for db_type, db_dict in DATABASES.items():
                out[db_type] = OrderedDict()
                for db_name in db_dict:
                    if db_name == 'USE_TYPES':
                        out[db_type][db_name] = {}
                        out[db_type][db_name]['SCHEDULES'] = get_all_schedules_dict(get_schedules_folder_path(region))
                        out[db_type][db_name]['USE_TYPE_PROPERTIES'] = use_type_properties_to_dict(
                            get_use_type_properties_path(region))
                    else:
                        db_path = get_database_path(region, db_name)
                        out[db_type][db_name] = database_to_dict(db_path)
            return out
        except IOError as e:
            print(e)
            abort(500, e.message)


@api.route("/<string:region>/<string:db>")
class Database(Resource):
    def get(self, region, db):
        regions = get_regions()
        if region not in regions:
            abort(400, "Could not find '{}' region. Try instead {}".format(region, ", ".join(regions)))
        try:
            if db in DATABASE_NAMES:
                if db == 'USE_TYPES':
                    out = OrderedDict()
                    out['SCHEDULES'] = get_all_schedules_dict(get_schedules_folder_path(region))
                    out['USE_TYPE_PROPERTIES'] = use_type_properties_to_dict(
                        get_use_type_properties_path(region))
                    return out
                else:
                    db_path = get_database_path(region, db)
                    return database_to_dict(db_path)
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
                    if db_name == 'USE_TYPES':
                        out[db_type][db_name] = schemas['get_database_standard_schedules_use']['schema']
                    else:
                        out[db_type][db_name] = schemas[db_props['schema_key']]['schema']
            return out
        elif db in DATABASE_NAMES:
            if db == 'USE_TYPES':
                return schemas['get_database_standard_schedules_use']['schema']
            else:
                db_type = DATABASES_TYPE_MAP[db]
                db_schema = schemas[DATABASES[db_type][db]['schema_key']]['schema']
                return db_schema
        else:
            abort(400, "Could not find '{}' database. Try instead {}".format(db, ", ".join(DATABASE_NAMES)))
