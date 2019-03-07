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
                        relative_filename = relative_filename.replace(building, 'buildings[0]')
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

    meta_to_json(meta_set, config.trace_inputlocator.meta_output_file)
    create_graphviz_output(viz_set, config.trace_inputlocator.graphviz_output_file)
    print 'Trace Complete'


def meta_to_json(meta_set, meta_output_file):

    import pandas
    import json
    locator_meta = {}

    for locator_method, filename in meta_set:


        description = eval('cea.inputlocator.InputLocator(cea.config).' + str(
            locator_method) + '.__doc__')
        file_type = os.path.basename(filename).split('.')[1]

        if os.path.isfile(filename):

            location = os.path.dirname(filename.replace('\\', '/'))
            description = eval('cea.inputlocator.InputLocator(config.Configuration().scenario).' + str(
                locator_method) + '.__doc__')

            if file_type == 'xls' or file_type == 'xlsx':

                xls = pandas.ExcelFile(filename, on_demand=True)
                contents = dict((k, {}) for k in xls.sheet_names)

                for sheet in contents:
                    db = pandas.read_excel(filename, sheet_name=sheet, on_demand=True)

                    # if the xls appears to be row indexed
                    if 'Unnamed: 1' in db.columns:
                        db = db.T
                        new_cols = []
                        for i in db.columns:
                            if i == i:
                                new_cols.append(i)
                        db.index = range(len(db))
                        db = db[new_cols]

                    attributes = dict((k, ()) for k in db)

                    for attr in attributes.keys():

                        dtype = set()

                        for data in zip(db[attr]):
                            for i in range(0, len(data)):
                                dtype.add(type(data[i]).__name__)

                            attributes[attr] = (data[0], list(dtype))

                    contents[sheet] = attributes

            if file_type == 'csv':
                db = pandas.read_csv(filename)
                contents = {}
                attributes = dict((k, ()) for k in db)

                for attr in attributes.keys():
                    dtype = set()
                    for data in zip(db[attr]):
                        for i in range(0, len(data)):
                            dtype.add(type(data[i]).__name__)
                        attributes[attr] = (data[0], list(dtype))

                contents['Sheet1'] = attributes

            if file_type == 'dbf':
                import pysal.core
                db = pysal.open(filename, 'r')
                contents = {}
                attributes = dict((k, ()) for k in db.header)
                dtype = set()

                for attr in attributes.keys():
                    data = db.by_col(attr)
                    for i in data:
                        dtype.add(type(i).__name__)

                    attributes[attr] = (data[0], list(dtype))
                contents['Sheet1'] = attributes

            if file_type == 'json':

                with open(filename, 'r') as f:
                    db = json.load(f)
                    contents = {}
                    attributes = dict((k, ()) for k in db.keys())

                    for attr in attributes.keys():
                        dtype = set()
                        for data in zip(db[attr]):
                            dtype.add(type(data[0]).__name__)
                            attributes[attr] = (data[0], list(dtype))
                contents['Sheet1'] = attributes

            if file_type == 'shp':
                import geopandas
                db = geopandas.read_file(filename)
                contents = {}
                attributes = dict((k, ()) for k in db.keys())

                for attr in attributes.keys():

                    dtype = set()
                    for data in zip(db[attr]):
                        for i in range(0, len(data)):
                            dtype.add(type(data[i]).__name__)
                        if attr == 'geometry':
                            attributes[attr] = ('((x1 y1, x2 y2, ...))', list(dtype))
                        else:
                            attributes[attr] = (data[0], list(dtype))
                contents['Sheet1'] = attributes

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

                attributes = dict((k, ()) for k in epw_labels)
                db = pandas.read_csv(filename, skiprows=8, header=None, names=epw_labels)
                contents = {}


        db_info = (description, filename, file_type, contents)
        locator_meta[locator_method] = db_info

    # methods = sorted(set([ms[0] for ms in meta_set]))
    #
    # if os.path.exists(meta_output_file):
    #     # merge existing data
    #     with open(meta_output_file, 'r') as f:
    #         old_meta_data = json.load(f)
    #     for method in old_meta_data.keys():
    #         if not method in methods:
    #             # make sure not to overwrite newer data!
    #             locator_meta[method] = old_meta_data[method]

    with open(meta_output_file, 'w') as fp:
        json.dump(locator_meta, fp, indent=4)


def create_graphviz_output(viz_set, graphviz_output_file):
    # creating new variable to preserve original viz_set used by other methods
    tracedata = set(sorted(viz_set))

    # replacing any relative paths outside the case dir with the last three dirs in the path
    # this prevents long path names in digraph clusters
    for i, (direction, script, method, path, file) in enumerate(tracedata):
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

if __name__ == '__main__':
    main(cea.config.Configuration())