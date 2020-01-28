import os
import glob

from flask_restplus import Namespace, Resource
import pandas

import cea.databases
from cea.utilities.schedule_reader import read_cea_schedule


api = Namespace("Databases", description="Database data for technologies in CEA")
database_path = os.path.dirname(cea.databases.__file__)


# FIXME: Temp solution
def database_paths(region):
    region_path = os.path.join(database_path, region)
    DATABASE_TYPES = {
        "archetypes": os.path.join(region_path, "archetypes"),
        "lifecycle": os.path.join(region_path, "lifecycle"),
        "systems": os.path.join(region_path, "systems"),
        "uncertainty": os.path.join(region_path, "uncertainty")
    }

    DATABASES = {
        "schedules": os.path.join(DATABASE_TYPES["archetypes"], "schedules"),
        "construction_properties": os.path.join(DATABASE_TYPES["archetypes"], "construction_properties.xlsx"),
        "lca_buildings": os.path.join(DATABASE_TYPES["lifecycle"], "lca_buildings.xlsx"),
        "lca_mobility": os.path.join(DATABASE_TYPES["lifecycle"], "lca_mobility.xls"),
        "air_conditioning_systems": os.path.join(DATABASE_TYPES["systems"], "air_conditioning_systems.xls"),
        "envelope_systems": os.path.join(DATABASE_TYPES["systems"], "envelope_systems.xls"),
        "supply_systems": os.path.join(DATABASE_TYPES["systems"], "supply_systems.xls"),
        "uncertainty_distributions": os.path.join(DATABASE_TYPES["uncertainty"], "uncertainty_distributions.xls"),
    }
    return DATABASES


def get_schedules_dict(schedule_path):
    out = {}
    schedule_files = glob.glob(os.path.join(schedule_path, "*.csv"))
    print(schedule_files)
    for schedule_file in schedule_files:
        archetype = os.path.splitext(os.path.basename(schedule_file))[0]
        schedule_data, schedule_complementary_data = read_cea_schedule(os.path.join(schedule_path, schedule_file))
        df = pandas.DataFrame(schedule_data).set_index(["DAY", "HOUR"])
        out[archetype] = {schedule_type: {day: df.loc[day][schedule_type].values.tolist() for day in df.index.levels[0]}
                          for schedule_type in df.columns}
        out.update(schedule_complementary_data)
    return out


def get_database_dict(locator, db):
    if db in locator:
        if db == "schedules":
            return get_schedules_dict(locator["schedules"])
        else:
            out = {}
            db_path = locator[db]
            xls = pandas.ExcelFile(db_path)
            for sheet in xls.sheet_names:
                out[sheet] = xls.parse(sheet).to_dict(orient='records')
            return out
    else:
        return None

@api.route("/")
class DatabaseRegion(Resource):
    def get(self):
        return [folder for folder in os.listdir(database_path) if folder != "weather"
           and os.path.isdir(os.path.join(database_path, folder))]


@api.route("/<string:region>/<string:db>")
class Database(Resource):
    def get(self, region, db):
        locator = database_paths(region)
        if db == 'all':
            out = {}
            db_names = locator.keys()
            for db_name in db_names:
                out[db_name] = get_database_dict(locator, db_name)
            return out
        else:
            db_dict = get_database_dict(locator, db)
            if db_dict:
                return db_dict
            return {"message": "Could not find '{}' database. Try instead {}".format(db, ", ".join(locator.keys()))}