import os
import glob
from collections import OrderedDict

from flask_restplus import Namespace, Resource, abort
import pandas

import cea.databases
import cea.scripts
from cea.utilities.schedule_reader import read_cea_schedule


api = Namespace("Databases", description="Database data for technologies in CEA")
database_path = os.path.dirname(cea.databases.__file__)

SCHEMA_KEY = {
    "schedules": 'get_database_standard_schedules_use',
    "construction_properties": "get_archetypes_properties",
    "lca_buildings": "get_database_lca_buildings",
    "lca_mobility": "get_database_lca_mobility",
    "air_conditioning_systems": 'get_database_air_conditioning_systems',
    "envelope_systems": "get_database_envelope_systems",
    "supply_systems": "get_database_supply_systems",
    # Not found in `schemas.yml`
    # "uncertainty_distributions": None
}


def get_regions():
    return [folder for folder in os.listdir(database_path) if folder != "weather"
            and os.path.isdir(os.path.join(database_path, folder))]


# FIXME: Temp solution for database locators for shipped databases
def database_paths(region):
    region_path = os.path.join(database_path, region)
    DATABASE_TYPES = {
        "archetypes": os.path.join(region_path, "archetypes"),
        "lifecycle": os.path.join(region_path, "lifecycle"),
        "systems": os.path.join(region_path, "systems"),
        # Not found in `schemas.yml`
        # "uncertainty": os.path.join(region_path, "uncertainty")
    }

    DATABASES = {
        "schedules": os.path.join(DATABASE_TYPES["archetypes"], "schedules"),
        "construction_properties": os.path.join(DATABASE_TYPES["archetypes"], "construction_properties.xlsx"),
        "lca_buildings": os.path.join(DATABASE_TYPES["lifecycle"], "lca_buildings.xlsx"),
        "lca_mobility": os.path.join(DATABASE_TYPES["lifecycle"], "lca_mobility.xls"),
        "air_conditioning_systems": os.path.join(DATABASE_TYPES["systems"], "air_conditioning_systems.xls"),
        "envelope_systems": os.path.join(DATABASE_TYPES["systems"], "envelope_systems.xls"),
        "supply_systems": os.path.join(DATABASE_TYPES["systems"], "supply_systems.xls"),
        # Not found in `schemas.yml`
        # "uncertainty_distributions": os.path.join(DATABASE_TYPES["uncertainty"], "uncertainty_distributions.xls")
    }
    return DATABASES


def get_schedules_dict(schedule_path):
    out = {}
    schedule_files = glob.glob(os.path.join(schedule_path, "*.csv"))
    for schedule_file in schedule_files:
        archetype = os.path.splitext(os.path.basename(schedule_file))[0]
        schedule_data, schedule_complementary_data = read_cea_schedule(os.path.join(schedule_path, schedule_file))
        df = pandas.DataFrame(schedule_data).set_index(["DAY", "HOUR"])
        out[archetype] = {schedule_type: {day: df.loc[day][schedule_type].values.tolist() for day in df.index.levels[0]}
                          for schedule_type in df.columns}
        out.update(schedule_complementary_data)
    return out


def get_database_dict(path, db):
    if db == "schedules":
        return get_schedules_dict(path)
    else:
        out = OrderedDict()
        xls = pandas.ExcelFile(path)
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            # Replace NaN with null to prevent JSON errors
            out[sheet] = df.where(pandas.notnull(df), None).to_dict(orient='records', into=OrderedDict)
        return out


@api.route("/")
class DatabaseRegion(Resource):
    def get(self):
        return {'regions': get_regions(), 'databases': SCHEMA_KEY.keys()}


@api.route("/<string:region>/<string:db>")
class Database(Resource):
    def get(self, region, db):
        regions = get_regions()
        if region not in regions:
            abort(400, "Could not find '{}' region. Try instead {}".format(region, ", ".join(regions)))
        locator = database_paths(region)
        db_names = locator.keys()
        try:
            if db == 'all':
                out = OrderedDict()
                for db_name in db_names:
                    out[db_name] = get_database_dict(locator[db_name], db_name)
                return out
            elif db in db_names:
                return get_database_dict(locator[db], db)
            else:
                abort(400, "Could not find '{}' database. Try instead {}".format(db, ", ".join(db_names)))
        except IOError as e:
            print(e)
            abort(500, e.message)


@api.route("/schema/<string:db>")
class DatabaseSchema(Resource):
    def get(self, db):
        schemas = cea.scripts.schemas()
        db_names = SCHEMA_KEY.keys()
        if db == 'all':
            out = {}
            for db_name in db_names:
                out[db_name] = schemas[SCHEMA_KEY[db_name]]['schema']
            return out
        elif db in db_names:
            db_schema = schemas[SCHEMA_KEY[db]]['schema']
            return db_schema
        else:
            abort(400, "Could not find '{}' database. Try instead {}".format(db, ", ".join(db_names)))
