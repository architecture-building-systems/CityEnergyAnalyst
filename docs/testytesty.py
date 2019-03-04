import os
import sys
import cea.config as config
import cea.inputlocator
import pandas

locator = cea.inputlocator.InputLocator(config.Configuration().scenario)

trace_data=[('input', 'demand', 'get_archetypes_properties', 'databases/CH/archetypes', 'construction_properties.xlsx'), ('input', 'demand', 'get_archetypes_schedules', 'databases/CH/archetypes', 'occupancy_schedules.xlsx'), ('input', 'demand', 'get_archetypes_system_controls', 'databases/CH/archetypes', 'system_controls.xlsx'), ('input', 'demand', 'get_building_age', 'inputs/building-properties', 'age.dbf'), ('input', 'demand', 'get_building_architecture', 'inputs/building-properties', 'architecture.dbf'), ('input', 'demand', 'get_building_comfort', 'inputs/building-properties', 'indoor_comfort.dbf'), ('input', 'demand', 'get_building_hvac', 'inputs/building-properties', 'technical_systems.dbf'), ('input', 'demand', 'get_building_internal', 'inputs/building-properties', 'internal_loads.dbf'), ('input', 'demand', 'get_building_occupancy', 'inputs/building-properties', 'occupancy.dbf'), ('input', 'demand', 'get_building_supply', 'inputs/building-properties', 'supply_systems.dbf'), ('input', 'demand', 'get_envelope_systems', 'databases/CH/systems', 'envelope_systems.xls'), ('input', 'demand', 'get_life_cycle_inventory_supply_systems', 'databases/CH/lifecycle', 'LCA_infrastructure.xlsx'), ('input', 'demand', 'get_radiation_building', 'outputs/data/solar-radiation', '{BUILDING}_insolation_Whm2.json'), ('input', 'demand', 'get_radiation_metadata', 'outputs/data/solar-radiation', '{BUILDING}_geometry.csv'), ('input', 'demand', 'get_technical_emission_systems', 'databases/CH/systems', 'emission_systems.xls'), ('input', 'demand', 'cea/databases/weather', '../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather', 'Zug.epw'), ('input', 'demand', 'get_zone_geometry', 'inputs/building-geometry', 'zone.shp'), ('output', 'demand', 'get_demand_results_file', 'outputs/data/demand', '{BUILDING}.csv'), ('output', 'demand', 'get_total_demand', 'outputs/data/demand', 'Total_demand.csv')]

# abs_path = cea.config.Configuration().scenario.replace('\\', '/')
abs_path = 'C:/reference-case-open/baseline'
db_set = {}
db_info = () # file_type, file_path, description, contents
sheet_names = {}

for direction, script, method, path, file in trace_data:
    db_set.add((abs_path+str('/')+path+str('/')+file))
    description = 'cea.inputlocator.InputLocator(config.Configuration().scenario)'+'.'+ str(method)+'.__doc__'
    eval(description)

for db_file in db_set:
    if db_file.find('{BUILDING}') != -1:
        db_file = db_file.replace('{BUILDING}',cea.inputlocator.get)

    if os.path.isfile(db_file):
        file = os.path.basename(db_file)
        db_info[file]=(sheet_names)
        #print db_info
        file = file.split('.')
        file_name= file[0]
        file_type = file[1]

        if file_type == 'xls' or file_type == 'xlsx':

            xls = pandas.ExcelFile(db_file, on_demand= True)

            sheet_names = dict((k,{}) for k in xls.sheet_names)

            for sheet in sheet_names:
                db = pandas.read_excel(db_file, sheet_name=sheet, nrows=2, on_demand= True)
                db_contents = db.dtypes.to_dict()
                sheet_names[sheet] = (db_contents)















        else:
            print('')