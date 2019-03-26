import sys
import os
import cea.api
import cea.config as config
from datetime import datetime
from jinja2 import Template
import cea.inputlocator
import pandas
import yaml
from dateutil.parser import parse

locator = cea.inputlocator.InputLocator(config.Configuration().scenario)

viz_set = set([('input', 'demand', 'get_archetypes_schedules', 'databases/CH/archetypes', 'occupancy_schedules.xlsx'), ('input', 'demand', 'get_archetypes_properties', 'databases/CH/archetypes', 'construction_properties.xlsx'), ('input', 'demand', 'get_envelope_systems', 'databases/CH/systems', 'envelope_systems.xls'), ('input', 'demand', 'get_building_hvac', 'inputs/building-properties', 'technical_systems.dbf'), ('input', 'demand', 'get_technical_emission_systems', 'databases/CH/systems', 'emission_systems.xls'), ('input', 'demand', 'get_building_internal', 'inputs/building-properties', 'internal_loads.dbf'), ('input', 'demand', 'get_zone_geometry', 'inputs/building-geometry', 'zone.shp'), ('input', 'demand', 'get_radiation_building', 'outputs/data/solar-radiation', 'B001_insolation_Whm2.json'), ('input', 'demand', 'get_weather', '../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather', 'Singapore.epw'), ('input', 'demand', 'get_life_cycle_inventory_supply_systems', 'databases/CH/lifecycle', 'LCA_infrastructure.xlsx'), ('input', 'demand', 'get_building_occupancy', 'inputs/building-properties', 'occupancy.dbf'), ('input', 'demand', 'get_building_supply', 'inputs/building-properties', 'supply_systems.dbf'), ('input', 'demand', 'get_building_architecture', 'inputs/building-properties', 'architecture.dbf'), ('input', 'demand', 'get_archetypes_system_controls', 'databases/CH/archetypes', 'system_controls.xlsx'), ('input', 'demand', 'get_building_age', 'inputs/building-properties', 'age.dbf'), ('output', 'demand', 'get_total_demand', 'outputs/data/demand', 'Total_demand.csv'), ('input', 'demand', 'get_radiation_metadata', 'outputs/data/solar-radiation', 'B001_geometry.csv'), ('output', 'demand', 'get_demand_results_file', 'outputs/data/demand', 'B001.csv'), ('input', 'demand', 'get_building_comfort', 'inputs/building-properties', 'indoor_comfort.dbf')])
# viz_set = set([('input', 'radiation-daysim', 'get_zone_geometry', 'inputs/building-geometry', 'zone.shp'), ('output', 'radiation-daysim', 'get_radiation_metadata', 'outputs/data/solar-radiation', 'B001_geometry.csv'), ('input', 'radiation-daysim', 'get_building_architecture', 'inputs/building-properties', 'architecture.dbf'), ('input', 'radiation-daysim', 'get_envelope_systems', 'databases/CH/systems', 'envelope_systems.xls'), ('output', 'radiation-daysim', 'get_radiation_building', 'outputs/data/solar-radiation', 'B001_insolation_Whm2.json'), ('input', 'radiation-daysim', 'get_district_geometry', 'inputs/building-geometry', 'district.shp'), ('input', 'radiation-daysim', 'get_terrain', 'inputs/topography', 'terrain.tif'), ('input', 'radiation-daysim', 'get_weather', '../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather', 'Singapore.epw'), ('input', 'radiation-daysim', 'get_weather', '../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather', 'Zug.epw')])

def meta_to_yaml(trace_data, meta_output_file):

    locator_meta = {}

    for direction, script, locator_method, path, files in trace_data:
        filename = os.path.join(cea.config.Configuration().__getattr__('scenario'), path, files)
        file_type = os.path.basename(files).split('.')[1]
        if os.path.isfile(filename):
            locator_meta[locator_method] = {}
            locator_meta[locator_method]['created_by'] = []
            locator_meta[locator_method]['used_by'] = []
            locator_meta[locator_method]['schema'] = get_schema(r'%s' % filename, file_type)
            locator_meta[locator_method]['file_path'] = filename
            locator_meta[locator_method]['file_type'] = file_type
            locator_meta[locator_method]['description'] = eval('cea.inputlocator.InputLocator(cea.config).' + str(
                    locator_method) + '.__doc__')

    #get the dependencies from trace_data
    for direction, script, locator_method, path, files in trace_data:
        outputs = set()
        inputs = set()
        if direction == 'output':
            outputs.add(script)
        if direction == 'input':
            inputs.add(script)
        locator_meta[locator_method]['created_by'] = list(outputs)
        locator_meta[locator_method]['used_by'] = list(inputs)

    # merge existing data
    methods = sorted(set([lm[2] for lm in trace_data]))
    if os.path.exists(meta_output_file):
        with open(meta_output_file, 'r') as f:
            old_meta_data = yaml.load(f)
        for method in old_meta_data:
            if method in methods:
                new_outputs = set(locator_meta[method]['created_by'])
                old_outputs = set(old_meta_data[method]['created_by'])
                locator_meta[method]['created_by'] = list(new_outputs.union(old_outputs))

                new_inputs = set(locator_meta[method]['used_by'])
                old_inputs = set(old_meta_data[method]['used_by'])
                locator_meta[method]['used_by'] = list(new_inputs.union(old_inputs))
            else:
                # make sure not to overwrite newer data!
                locator_meta[method] = old_meta_data[method]

    with open(meta_output_file, 'w') as fp:
        yaml.dump(locator_meta, fp, indent=4)

def create_graphviz_output(trace_data, graphviz_output_file):
    # creating new variable to preserve original trace_data used by other methods
    tracedata = sorted(trace_data)
    # replacing any relative paths outside the case dir with the last three dirs in the path
    # this prevents long path names in digraph clusters
    for i, (direction, script, method, path, db) in enumerate(tracedata):
        if path.split('/')[0] == '..':
            path = path.rsplit('/', 3)
            del path[0]
            path = '/'.join(path)
            tracedata[i] = list(tracedata[i])
            tracedata[i][3] = path
            tracedata[i] = tuple(tracedata[i])

    # set of unique scripts
    scripts = sorted(set([td[1] for td in tracedata]))

    # set of common dirs for each file accessed by the script(s)
    db_group = sorted(set(td[3] for td in tracedata))

    # float containing the node width for the largest file name
    if max(len(td[4]) for td in tracedata)*0.113 > 3.5:
        width = max(len(td[4]) for td in tracedata)*0.113
    else:
        width = 3.5

    # jinja2 template setup and execution
    template_path = os.path.join(os.path.dirname(__file__), 'trace_inputlocator.template.gv')
    template = Template(open(template_path, 'r').read())
    digraph = template.render(tracedata=tracedata, scripts=scripts, db_group=db_group, width=width)
    digraph = '\n'.join([line for line in digraph.split('\n') if len(line.strip())])
    with open(graphviz_output_file, 'w') as f:
        f.write(digraph)


def is_date(data):
    # TODO replace hardcoded with a reference
    codes = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12', 'T13', 'T14', 'T15'
             'T16', 'T17', 'T18', 'T19', 'T20', 'T21', 'T22', 'T23', 'T24', 'T25']
    if type(data) == unicode and data not in codes:
        try:
            parse(data)
            return True
        except ValueError:
            return False

def replace_repetitive_attr(attr):
    scenario = cea.config.Configuration().__getattr__('scenario')
    buildings = cea.inputlocator.InputLocator(scenario).get_zone_building_names()
    if attr.find('srf') != -1:
        attr = attr.replace(attr, 'srf0')
    if attr.find('PIPE') != -1:
        attr = attr.replace(attr, 'PIPE0')
    if attr.find('NODE') != -1:
        attr = attr.replace(attr, 'NODE0')
    if attr in buildings:
        attr = attr.replace(attr, 'B01')
    return attr


def get_meta(df_series, attribute_name):
    types_found = set()
    meta = {}
    for data in df_series:
        if data == data:
            meta['sample_data'] = data
            if is_date(data):
                types_found.add('date')
            elif isinstance(data, basestring):
                meta['sample_data'] = data.encode('ascii', 'ignore')
                types_found.add('string')
            else:
                types_found.add(type(data).__name__)
        # declare nans
        if data != data:
            types_found.add(None)
    meta['types_found'] = list(types_found)
    return meta


def get_schema(filename, file_type):
    schema = {}
    if file_type == 'xlsx' or file_type == 'xls':
        db = pandas.read_excel(filename, sheet_name=None)
        for sheet in db:
            meta = {}
            nested_df = db[sheet]
            # if xls seems to have row attributes
            if 'Unnamed: 1' in db[sheet].keys():
                nested_df = db[sheet].T
                # filter the goddamn nans
                new_cols = []
                for col in nested_df.columns:
                    if col == col:
                        new_cols.append(col)
                # change index to numbered
                nested_df.index = range(len(nested_df))
                # select only non-nan columns
                nested_df = nested_df[new_cols]
            for attr in nested_df:
                meta[attr.encode('ascii', 'ignore')] = get_meta(nested_df[attr], attr)
            schema[sheet.encode('ascii', 'ignore')] = meta
        return schema

    if file_type == 'csv':
        db = pandas.read_csv(filename)
        for attr in db:
            attr = replace_repetitive_attr(attr)
            schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr], attr)
        return schema

    if file_type == 'json':
        with open(filename, 'r') as f:
            import json
            db = json.load(f)
        for attr in db:
            attr = replace_repetitive_attr(attr)
            schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr], attr)
        return schema

    if file_type == 'epw':
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

        db = pandas.read_csv(filename, skiprows=8, header=None, names=epw_labels)
        for attr in db:
            schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr], attr)
        return schema

    if file_type == 'dbf':
        import pysal
        db = pysal.open(filename, 'r')
        for attr in db.header:
            schema[attr.encode('ascii', 'ignore')] = get_meta(db.by_col(attr), attr)
        return schema

    if file_type == 'shp':
        import geopandas
        db = geopandas.read_file(filename)
        for attr in db:
            attr = replace_repetitive_attr(attr)
            meta = get_meta(db[attr], attr)
            if attr == 'geometry':
                meta['sample_data'] = '((x1 y1, x2 y2, ...))'
            schema[attr.encode('ascii', 'ignore')] = meta
    return schema


meta_to_yaml(viz_set,r'C:\reference-case-open\WTP_CBD_h\outputs\trace_inputlocator.output.yml')














