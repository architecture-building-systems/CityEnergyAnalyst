import os
import cea.config as config
import cea.inputlocator
import pandas
import csv
import numpy

locator = cea.inputlocator.InputLocator(config.Configuration().scenario)
NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__),'plots/naming.csv')
with open(NAMING_FILE_PATH) as naming_file:
    NAMING = {row['VARIABLE']: (row['SHORT_DESCRIPTION'],row['UNIT']) for row in csv.DictReader(naming_file)}


trace_data=[('input', 'demand', 'get_archetypes_properties', 'databases/CH/archetypes', 'construction_properties.xlsx'), ('input', 'demand', 'get_archetypes_schedules', 'databases/CH/archetypes', 'occupancy_schedules.xlsx'), ('input', 'demand', 'get_archetypes_system_controls', 'databases/CH/archetypes', 'system_controls.xlsx'), ('input', 'demand', 'get_building_age', 'inputs/building-properties', 'age.dbf'), ('input', 'demand', 'get_building_architecture', 'inputs/building-properties', 'architecture.dbf'), ('input', 'demand', 'get_building_comfort', 'inputs/building-properties', 'indoor_comfort.dbf'), ('input', 'demand', 'get_building_hvac', 'inputs/building-properties', 'technical_systems.dbf'), ('input', 'demand', 'get_building_internal', 'inputs/building-properties', 'internal_loads.dbf'), ('input', 'demand', 'get_building_occupancy', 'inputs/building-properties', 'occupancy.dbf'), ('input', 'demand', 'get_building_supply', 'inputs/building-properties', 'supply_systems.dbf'), ('input', 'demand', 'get_envelope_systems', 'databases/CH/systems', 'envelope_systems.xls'), ('input', 'demand', 'get_life_cycle_inventory_supply_systems', 'databases/CH/lifecycle', 'LCA_infrastructure.xlsx'), ('input', 'demand', 'get_radiation_building', 'outputs/data/solar-radiation', '{BUILDING}_insolation_Whm2.json'), ('input', 'demand', 'get_radiation_metadata', 'outputs/data/solar-radiation', '{BUILDING}_geometry.csv'), ('input', 'demand', 'get_technical_emission_systems', 'databases/CH/systems', 'emission_systems.xls'), ('input', 'demand', 'cea/databases/weather', '../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather', 'Zug.epw'), ('input', 'demand', 'get_zone_geometry', 'inputs/building-geometry', 'zone.shp'), ('output', 'demand', 'get_demand_results_file', 'outputs/data/demand', '{BUILDING}.csv'), ('output', 'demand', 'get_total_demand', 'outputs/data/demand', 'Total_demand.csv')]
results_set = set([('get_building_restrictions', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\restrictions.dbf'), ('get_building_hvac', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\technical_systems.dbf'), ('get_building_comfort', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\indoor_comfort.dbf'), ('get_building_internal', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\internal_loads.dbf'), ('get_building_occupancy', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\occupancy.dbf'), ('get_building_supply', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\supply_systems.dbf'), ('get_archetypes_properties', 'C:\\reference-case-open\\baseline\\databases\\CH\\archetypes\\construction_properties.xlsx'), ('find_db_path', 'c:\\users\\jack\\documents\\github\\cityenergyanalyst\\cea\\databases'), ('get_building_age', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\age.dbf'), ('get_archetypes_schedules', 'C:\\reference-case-open\\baseline\\databases\\CH\\archetypes\\occupancy_schedules.xlsx'), ('get_building_properties_folder', 'C:\\reference-case-open\\baseline\\inputs\\building-properties'), ('get_building_architecture', 'C:\\reference-case-open\\baseline\\inputs\\building-properties\\architecture.dbf')])


locator_metadata = {}  # {method_name : db_info }
# db_info = ()  # (description, file_name, file_type, location, contents)
contents = {}  # {sheet_name : var_dict}
var_dict = {}  # {var_name : var_details}
var_details = ()  # (description, dtype, unit)
# dev_defined_details = {}

for locator_method, filename in results_set:

    if os.path.isdir(filename):
        continue
    if locator_method == 'get_temporary_file':
        # this file is probably already deleted (hopefully?)
        continue

    # create new method separating trace_data used for graphviz and results_set used for metadata
    if os.path.isfile(filename):
        file_name = os.path.basename(filename).split('.')[0]
        file_type = filename.split('.')[1]
        location = os.path.dirname(filename.replace('\\', '/'))
        description = eval('cea.inputlocator.InputLocator(config.Configuration().scenario).' + str(
            locator_method) + '.__doc__')

        if file_type == 'xls' or file_type == 'xlsx':


        ## create and call new methods for each file type
            xls = pandas.ExcelFile(filename, on_demand=True)
            contents = dict((k, {}) for k in xls.sheet_names)
            print '~~~~~'+filename+'~~~~~'
            for sheet in contents:
                print '...'+sheet+'...'
                db = pandas.read_excel(filename, sheet_name=sheet, on_demand=True)

                attributes = dict((k,()) for k in db)

                # if the xls appears to be row indexed
                if 'Unnamed: 1' in attributes:


                    # save the unicode titles of any entry in the named original index
                    titles = []
                    for attr in db.columns:

                        if attr.find('Unnamed:') == -1:
                            title = db[attr].values.tolist()

                            for i in range(0, len(title)):
                                if type(title[i]) == unicode:
                                    titles.append(title[i])

                    row_index = db.index

                    # db.set_index(row_index.tolist()[0], drop=True)
                    print row_index


                    # print db

                for attr in attributes.keys():
                    dtype = set()


                    # if attr.find('Unnamed:') != -1:
                        # linear_index = list(db[attr].index)
                        # extension = list(db[attr].values)
                        # del attributes

                    for data in zip(db[attr]):
                        for i in range(0,len(data)):
                            dtype.add(type(data[i]))
                        # print data
                        attributes[attr] = (data[0], dtype)

                # print attributes










                # ref = dict(db[attributes.keys()])
                # dtype = set()
                # desc = set()
                # unit= set()
                #
                # for attr in ref:
                #     for data in zip(db[attr]):
                #         for i in range(0,len(data)):
                #             dtype.add(type(data[i]))
                #
                #         # if sample[0] in NAMING.keys():
                #         #     # print sample[0]
                #         desc = 'lalala'
                #         unit = 'fuckin wat'
                #         attributes[attr] = (data[0], dtype, unit, desc)
                #
                #
                #
                #



