"""
Trace the InputLocator calls in a selection of scripts.
"""




import sys
import os
import cea.api
from datetime import datetime
import cea.inputlocator
import yaml
import cea.utilities.doc_schemas

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
            # descend into the stack...
            return trace_function
        elif event == 'return':
            if isinstance(arg, str) and 'inputlocator' in filename.lower() and not func_name.startswith('_'):
                results_set.add((func_name, arg))
                # print('%s => %s' % (func_name, arg))
        return
    return trace_function


def main(config: cea.config.Configuration):
    # force single-threaded execution, see settrace docs for why
    config.multiprocessing = False
    locator = cea.inputlocator.InputLocator(config.scenario)

    trace_data = set()  # set used for graphviz output -> {(direction, script, locator_method, path, file)}

    for script_name in config.trace_inputlocator.scripts:
        script_func = getattr(cea.api, script_name.replace('-', '_'))
        script_start = datetime.now()
        results_set = set()  # {(locator_method, filename)}

        orig_trace = sys.gettrace()
        sys.settrace(create_trace_function(results_set))
        script_func(config)  # <------------------------------ this is where we run the script!
        sys.settrace(orig_trace)

        update_trace_data(config, locator, results_set, script_name,
                          script_start, trace_data)
    print(trace_data)
    # scripts = sorted(set([td[1] for td in trace_data]))
    config.restricted_to = None

    meta_to_yaml(config, trace_data, config.trace_inputlocator.meta_output_file)
    print('Trace Complete')


def update_trace_data(config, locator, results_set, script_name, script_start,
                      trace_data):
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
                    filename = filename.replace(building, buildings[0])
                    relative_filename = relative_filename.replace(building, buildings[0])

        relative_filename = str(relative_filename)
        file_path = os.path.dirname(relative_filename)
        file_name = os.path.basename(relative_filename)
        if script_start < mtime:
            trace_data.add(('output', script_name, locator_method, file_path, file_name))
        else:
            trace_data.add(('input', script_name, locator_method, file_path, file_name))


def meta_to_yaml(config, trace_data, meta_output_file):
    buildings = cea.inputlocator.InputLocator(config.scenario).get_zone_building_names()

    locator_meta = {}

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
            print("Getting schema for {file_full_path}".format(file_full_path=file_full_path))
            locator_meta[locator_method]['schema'] = cea.utilities.doc_schemas.read_schema_details(file_full_path, file_type, buildings)
            locator_meta[locator_method]['file_path'] = file_full_path
            locator_meta[locator_method]['file_type'] = file_type
            locator_meta[locator_method]['description'] = eval('cea.inputlocator.InputLocator(cea.config).' + str(
                locator_method) + '.__doc__')

    # get the dependencies from trace_data
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
            old_meta_data = yaml.load(f, Loader=yaml.BaseLoader)
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


if __name__ == '__main__':
    main(cea.config.Configuration())
