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

var_dec_path = os.path.join(os.path.dirname(cea.config.__file__), 'tests/variable_declaration.csv')
variable_declaration = pandas.read_csv(var_dec_path).set_index(['VARIABLE'])

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


    viz_set = set()  # set used for graphviz output -> {(direction, script, locator_method, path, file)}
    meta_set = set() # set used for locator_meta dict -> {locator_method : (description, filename, file_type, contents)}
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
                        meta_set.add((locator_method, filename))
                if filename not in building_specific_files:
                    meta_set.add((locator_method, filename))

            relative_filename = str(relative_filename)
            file_path = os.path.dirname(relative_filename)
            file_name = os.path.basename(relative_filename)
            if script_start < mtime:
                viz_set.add(('output', script_name, locator_method, file_path, file_name))
            else:
                viz_set.add(('input', script_name, locator_method, file_path, file_name))
    print viz_set
    config.restricted_to = None

    meta_to_yaml(viz_set, meta_set, config.trace_inputlocator.meta_output_file)
    create_graphviz_output(viz_set, config.trace_inputlocator.graphviz_output_file)
    print 'Trace Complete'

def meta_to_yaml(viz_set, meta_set, meta_output_file):

    locator_meta = {}
    for locator_method, filename in meta_set:
        file_type = os.path.basename(filename).split('.')[1]

        if os.path.isfile(filename):
            locator_meta[locator_method] = {}
            locator_meta[locator_method]['schema'] = get_schema(r'%s' %filename, file_type)
            locator_meta[locator_method]['file_path'] = filename
            locator_meta[locator_method]['file_type'] = file_type
            locator_meta[locator_method]['description'] = eval('cea.inputlocator.InputLocator(cea.config).' + str(
                    locator_method) + '.__doc__')


    #get the dependencies from viz_set
    for direction, script, locator_method, path, files in viz_set:
        outputs = set()
        inputs = set()
        if direction == 'output':
            outputs.add(script)
        if direction == 'input':
            inputs.add(script)
        locator_meta[locator_method]['created_by'] = list(outputs)
        locator_meta[locator_method]['used_by'] = list(inputs)

    # merge existing data
    methods = sorted(set([lm[2] for lm in viz_set]))
    if os.path.exists(meta_output_file):
        with open(meta_output_file, 'r') as f:
            old_meta_data = yaml.load(f)
        for method in old_meta_data:
            if method in methods:
                new_outputs = set(locator_meta[method]['created_by'])
                old_outputs = set(old_meta_data[method]['created_by'])
                locator_meta[method]['created_by'] = list(new_outputs.union(old_outputs))

                new_inputs = set(locator_meta[method]['created_by'])
                old_inputs = set(old_meta_data[method]['used_by'])
                locator_meta[method]['used_by'] = list(new_inputs.union(old_inputs))
            else:
                # make sure not to overwrite newer data!
                locator_meta[method] = old_meta_data[method]

    with open(meta_output_file, 'w') as fp:
        yaml.dump(locator_meta, fp, indent=4)

def create_graphviz_output(viz_set, graphviz_output_file):
    # creating new variable to preserve original viz_set used by other methods
    tracedata = sorted(viz_set)
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
    # TODO replace hardcoded with a reference file
    codes = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12', 'T13', 'T14', 'T15'
             'T16', 'T17', 'T18', 'T19', 'T20', 'T21', 'T22', 'T23', 'T24', 'T25']
    if type(data) == unicode and data not in codes:
        try:
            parse(data)
            return True
        except ValueError:
            return False

def replace_repetitive_attr(attr):
    scenario = cea.config.Configuration('general:scenario').__getattr__('scenario')
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


def get_meta(df_series, attribute_name, variable_declaration):
    types_found = set()
    meta = {}
    for data in df_series:
        sample_data = data
        if data == data:
            # sample_data = data
            if is_date(data):
                types_found.add('date')
            elif isinstance(data, basestring):
                sample_data = data.encode('ascii', 'ignore')
                types_found.add('string')
            else:
                types_found.add(type(data).__name__)
        # declare nans
        if data != data:
            types_found.add(None)
        if attribute_name in variable_declaration.index.values:
            description = variable_declaration.loc[attribute_name, 'DESCRIPTION']
            values = variable_declaration.loc[attribute_name, 'VALUES']
            types_declared = variable_declaration.loc[attribute_name, 'TYPE']
        else:
            description = 'Not in variable_declaration.csv'
            values = 'TODO'
            types_declared = 'TODO'

        meta = {
            'sample_data': sample_data,
            'description': description,
            'types_found': list(types_found),
            'types_declared': types_declared,
            'values': values
        }
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
                meta[attr.encode('ascii', 'ignore')] = get_meta(nested_df[attr], attr, variable_declaration)
            schema[sheet.encode('ascii', 'ignore')] = meta
        return schema

    if file_type == 'csv':
        db = pandas.read_csv(filename)
        for attr in db:
            attr = replace_repetitive_attr(attr)
            schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr], attr, variable_declaration)
        return schema

    if file_type == 'json':
        with open(filename, 'r') as f:
            import json
            db = json.load(f)
        for attr in db:
            attr = replace_repetitive_attr(attr)
            schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr], attr, variable_declaration)
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
            schema[attr.encode('ascii', 'ignore')] = get_meta(db[attr], attr, variable_declaration)
        return schema

    if file_type == 'dbf':
        import pysal
        db = pysal.open(filename, 'r')
        for attr in db.header:
            schema[attr.encode('ascii', 'ignore')] = get_meta(db.by_col(attr), attr, variable_declaration)
        return schema

    if file_type == 'shp':
        import geopandas
        db = geopandas.read_file(filename)
        for attr in db:
            attr = replace_repetitive_attr(attr)
            meta = get_meta(db[attr], attr, variable_declaration)
            if attr == 'geometry':
                meta['sample_data'] = '((x1 y1, x2 y2, ...))'
            schema[attr.encode('ascii', 'ignore')] = meta
    return schema

if __name__ == '__main__':
    main(cea.config.Configuration())