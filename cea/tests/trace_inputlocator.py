"""
Trace the InputLocator calls in a selection of scripts.
"""

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

__author__ = "Daren Thomas & Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_trace_function(results_set):
    """results_set is a set of tuples (locator, filename)"""
    def trace_function(frame, event, arg):
        """Trace any calls to the InputLocator"""
        co = frame.f_code
        func_name = co.co_name
        if func_name == 'write':
            # Ignore write() calls from print statements
            return
        filename = co.co_filename
        if event == 'call':
            # decend into the stack...
            return trace_function
        elif event == 'return':
            if isinstance(arg, basestring) and 'inputlocator' in filename.lower() and not func_name.startswith('_'):
                results_set.add((func_name, arg))
                # print('%s => %s' % (func_name, arg))
        return
    return trace_function


def main(config):
    # force single-threaded execution, see settrace docs for why
    config.multiprocessing = False
    locator = cea.inputlocator.InputLocator(config.scenario)


    trace_data = set()  # set used for graphviz output -> {(direction, script, locator_method, path, file)}
    building_specific_files = [] # list containing all building specific files e.g. B01.csv or B07_insolation.dbf


    for script_name in config.trace_inputlocator.scripts:
        script_func = getattr(cea.api, script_name.replace('-', '_'))
        script_start = datetime.now()
        results_set = set()  # {(locator_method, filename)}

        orig_trace = sys.gettrace()
        sys.settrace(create_trace_function(results_set))
        script_func(config)  # <------------------------------ this is where we run the script!
        sys.settrace(orig_trace)

        for locator_method, filename in results_set:
            if os.path.isdir(filename):
                continue
            if locator_method == 'get_temporary_file':
                # this file is probably already deleted (hopefully?) it's not
                continue

            mtime = datetime.fromtimestamp(os.path.getmtime(filename))
            relative_filename = os.path.relpath(filename, config.scenario).replace('\\', '/')

            if os.path.isfile(filename):
                buildings = locator.get_zone_building_names()
                for building in buildings:
                    if os.path.basename(filename).find(building) != -1:
                        building_specific_files.append(filename)
                        filename = filename.replace(building, buildings[0])
                        relative_filename = relative_filename.replace(building, buildings[0])

            relative_filename = str(relative_filename)
            file_path = os.path.dirname(relative_filename)
            file_name = os.path.basename(relative_filename)
            if script_start < mtime:
                trace_data.add(('output', script_name, locator_method, file_path, file_name))
            else:
                trace_data.add(('input', script_name, locator_method, file_path, file_name))
    print trace_data
    scripts = sorted(set([td[1] for td in trace_data]))
    config.restricted_to = None

    meta_to_yaml(config, trace_data, config.trace_inputlocator.meta_output_file)
    print 'Trace Complete'


def meta_to_yaml(config, trace_data, meta_output_file):

    locator_meta = {}

    schema = {
        'xls': get_xls_schema,
        'xlsx': get_xls_schema,
        'tif': get_tif_schema,
        'tiff': get_tif_schema,
        'csv': get_csv_schema,
        'json': get_json_schema,
        'epw': get_epw_schema,
        'dbf': get_dbf_schema,
        'shp': get_shp_schema,
        'html': get_html_schema,
        '': get_html_schema,
    }

    for direction, script, locator_method, folder_path, file_name in trace_data:
        file_full_path = os.path.join(config.scenario, folder_path, file_name)
        try:
            file_type = os.path.basename(file_name).split('.')[1]
        except IndexError:
            file_type = ''

        if os.path.isfile(file_full_path):
            locator_meta[locator_method] = {}
            locator_meta[locator_method]['created_by'] = []
            locator_meta[locator_method]['used_by'] = []
            locator_meta[locator_method]['schema'] = schema['%s' % file_type](file_full_path)
            locator_meta[locator_method]['file_path'] = file_full_path
            locator_meta[locator_method]['file_type'] = file_type
            locator_meta[locator_method]['description'] = eval('cea.inputlocator.InputLocator(cea.config).' + str(
                locator_method) + '.__doc__')

    #get the dependencies from trace_data
    for direction, script, locator_method, folder_path, file_name in trace_data:
        file_full_path = os.path.join(config.scenario, folder_path, file_name)
        if not os.path.isfile(file_full_path):
            # not interested in folders
            continue
        if direction == 'output':
            locator_meta[locator_method]['created_by'].append(script)
        if direction == 'input':
            locator_meta[locator_method]['used_by'].append(script)

    for locator_method in locator_meta.keys():
        locator_meta[locator_method]["created_by"] = list(locator_meta[locator_method]["created_by"])
        locator_meta[locator_method]["used_by"] = list(locator_meta[locator_method]["used_by"])

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


def is_date(data):
    # TODO replace hardcoded with a reference
    codes = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12', 'T13', 'T14', 'T15'
             'T16', 'T17', 'T18', 'T19', 'T20', 'T21', 'T22', 'T23', 'T24', 'T25','m','m2','m3']
    if isinstance(data, basestring) and data not in codes:
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
        attr = attr.replace(attr, buildings[0])
    return attr


def get_meta(df_series):
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


def get_xls_schema(filename):
    db = pandas.read_excel(filename, sheet_name=None)
    schema = {}
    for sheet in db:
        meta = {}
        nested_df = db[sheet]
        # if xls seems to have row attributes
        if 'Unnamed: 1' in db[sheet].keys():
            nested_df = db[sheet].T
            # filter the nans
            new_cols = []
            for col in nested_df.columns:
                if col == col:
                    new_cols.append(col)
            # change index to numbered
            nested_df.index = range(len(nested_df))
            # select only non-nan columns
            nested_df = nested_df[new_cols]
        for attr in nested_df:
            meta[attr.encode('ascii', 'ignore')] = get_meta(nested_df[attr])
        schema[sheet.encode('ascii', 'ignore')] = meta
    return schema


def get_tif_schema(filename):
    schema = {}
    schema['raster_value'] = {
        'sample_data': 1.0,
        'types_found': [float]
    }
    return schema


def get_csv_schema(filename):
    db = pandas.read_csv(filename)
    schema = {}
    for attr in db:
        attr = replace_repetitive_attr(attr)
        schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr])
    return schema


def get_json_schema(filename):
    with open(filename, 'r') as f:
        import json
        db = json.load(f)
    schema = {}
    for attr in db:
        attr = replace_repetitive_attr(attr)
        schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr])
    return schema


def get_epw_schema(filename):
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
    schema = {}
    for attr in db:
        schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr])
    return schema


def get_dbf_schema(filename):
    import pysal
    db = pysal.open(filename, 'r')
    schema = {}
    for attr in db.header:
        schema[attr.encode('ascii', 'ignore')] = get_meta(db.by_col(attr))
    return schema


def get_shp_schema(filename):
    import geopandas
    db = geopandas.read_file(filename)
    schema = {}
    for attr in db:
        attr = replace_repetitive_attr(attr)
        meta = get_meta(db[attr])
        if attr == 'geometry':
            meta['sample_data'] = '((x1 y1, x2 y2, ...))'
        schema[attr.encode('ascii', 'ignore')] = meta
    return schema


def get_html_schema(_):
    """We don't need to keep a schema of html files - these are outputs anyway"""
    return None


if __name__ == '__main__':
    main(cea.config.Configuration())
