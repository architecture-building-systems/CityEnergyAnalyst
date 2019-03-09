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

    config.restricted_to = None

    meta_to_yaml(viz_set, meta_set, config.trace_inputlocator.meta_output_file)
    create_graphviz_output(viz_set, config.trace_inputlocator.graphviz_output_file)
    print 'Trace Complete'

def get_updated_dependencies(viz_set, meta_output_file):
    import yaml
    dependencies = {}

    for direction, script, locator_method, path, file in viz_set:
        parent = []
        child = []
        if direction == 'output':
            parent.append(script)
        if direction == 'input':
            child.append(script)
        dependencies[locator_method] = {
            'created_by': parent,
            'used_by': child
        }

    methods = sorted(set([lm[2] for lm in viz_set]))

    if os.path.exists(meta_output_file):
        # merge existing data
        with open(meta_output_file, 'r') as f:
            old_dep_data = yaml.load(f)
        for method in old_dep_data:
            if method in methods:
                if old_dep_data[method]['created_by']:
                    for i in range(len(old_dep_data[method]['created_by'])):
                        dependencies[method]['created_by'].append(old_dep_data[method]['created_by'][i])
                if old_dep_data[method]['used_by']:
                    for i in range(len(old_dep_data[method]['used_by'])):
                        dependencies[method]['used_by'].append(old_dep_data[method]['used_by'][i])
            if method not in methods:
                # make sure not to overwrite newer data!
                dependencies[method] = old_dep_data[method]
    return dependencies


def meta_to_yaml(viz_set, meta_set, meta_output_file):

    import pandas
    locator_meta = {}
    dependencies = get_updated_dependencies(viz_set, meta_output_file)

    for locator_method, filename in meta_set:
        file_type = os.path.basename(filename).split('.')[1]

        if os.path.isfile(filename):

            if file_type == 'csv':
                db = pandas.read_csv(filename)
                locator_meta[locator_method] = get_meta(db, filename, file_type, dependencies[locator_method])

            if file_type == 'json':

                with open(filename, 'r') as f:
                    import json
                    db = json.load(f)
                    locator_meta[locator_method] = get_meta(db, filename, file_type, dependencies[locator_method])

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
                locator_meta[locator_method] = get_meta(db, filename, file_type, dependencies[locator_method])

            if file_type == 'xls' or file_type == 'xlsx':

                xls = pandas.ExcelFile(filename, on_demand=True)
                schema = dict((k, {}) for k in xls.sheet_names)

                for sheet in schema:
                    db = pandas.read_excel(filename, sheet_name=sheet, on_demand=True)
                    # if the xls appears to have row keys
                    if 'Unnamed: 1' in db.columns:
                        db = db.T
                        # filter the goddamn nans
                        new_cols = []
                        for i in db.columns:
                            if i == i:
                                new_cols.append(i)
                        db.index = range(len(db))
                        db = db[new_cols]

                    for attr in db:
                        dtype = set()
                        for data in db[attr]:
                            # sample_data only to contain valid values
                            if data == data:
                                sample_data = data
                                # change unicode to SQL 'str'
                                if type(data) == unicode:
                                    dtype.add('str')
                                else:
                                    dtype.add(type(data).__name__)
                            # declare nans
                            if data != data:
                                dtype.add(None)

                        schema[sheet][attr] = {
                                'sample_value': sample_data,
                                'types_found': list(dtype)
                            }

                    details = {
                    'file_path' : filename,
                    'file_type' : file_type,
                    'schema' : schema,
                    'created_by': dependencies[locator_method]['created_by'],
                    'used_by': dependencies[locator_method]['used_by']
                    }
                    locator_meta[locator_method] = details

            if file_type == 'dbf':
                import pysal
                db = pysal.open(filename, 'r')
                schema = dict((k, ()) for k in db.header)
                dtype = set()

                for attr in schema:
                    for data in db.by_col(attr):
                        if data == data:
                            sample_data = data
                            if type(data) == unicode:
                                dtype.add('str')
                            else:
                                dtype.add(type(data).__name__)
                        # declare nans
                        if data != data:
                            dtype.add(None)
                        schema[attr] = {
                                'sample_value': sample_data,
                                'types_found': list(dtype)
                            }
                details = {
                    'file_path': filename,
                    'file_type': file_type,
                    'schema': schema,
                    'created_by': dependencies[locator_method]['created_by'],
                    'used_by': dependencies[locator_method]['used_by']
                }
                locator_meta[locator_method] = details

            if file_type == 'shp':
                import geopandas
                db = geopandas.read_file(filename)
                schema = {}
                for attr in db:
                    dtype = set()
                    for data in db[attr]:
                        if data == data:
                            if attr == 'geometry':
                                sample_data = '((x1 y1, x2 y2, ...))'
                            else:
                                sample_data = data
                            if type(data) == unicode:
                                dtype.add('str')
                            else:
                                dtype.add(type(data).__name__)
                        # declare nans
                        if data != data:
                            dtype.add(None)
                        schema[attr] = {
                                'sample_value': sample_data,
                                'types_found': list(dtype)
                            }
                details = {
                    'file_path': filename,
                    'file_type': file_type,
                    'schema': schema,
                    'created_by': dependencies[locator_method]['created_by'],
                    'used_by': dependencies[locator_method]['used_by']
                }
                locator_meta[locator_method] = details

    methods = sorted(set([lm[0] for lm in meta_set]))
    import yaml
    if os.path.exists(meta_output_file):
        # merge existing data
        with open(meta_output_file, 'r') as f:
            old_loc_data = yaml.load(f)
        for method in old_loc_data:
            if method not in methods:
                # make sure not to overwrite newer data!
                locator_meta[method] = old_loc_data[method]

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


def get_meta(db, filename, file_type, dependencies):
    schema = {}
    for attr in db:
        dtype = set()
        for data in db[attr]:
            # ensure sample_data is not nan
            if data == data:
                sample_data = data
                if type(data) == unicode:
                    dtype.add('str')
                else:
                    dtype.add(type(data).__name__)
            # declare nans
            if data != data:
                dtype.add(None)
            schema[attr] = {
                'sample_value': sample_data,
                'types_found': list(dtype)
            }
    details = {
        'file_path': filename,
        'file_type': file_type,
        'schema': schema,
        'created_by': dependencies['created_by'],
        'used_by': dependencies['used_by']
    }
    return details

if __name__ == '__main__':
    main(cea.config.Configuration())