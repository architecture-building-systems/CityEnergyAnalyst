"""
Trace the InputLocator calls in a selection of scripts.
"""
import sys
import os
import cea.config
import cea.api
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
    trace_data = set()  # {(direction, script, locator_method, path, file)}
    locator = cea.inputlocator.InputLocator(config.scenario)

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
                # this file is probably already deleted (hopefully?)
                continue
            print("{}, {}".format(locator_method, filename))
            mtime = datetime.fromtimestamp(os.path.getmtime(filename))
            relative_filename = os.path.relpath(filename, config.scenario).replace('\\', '/')
            for building in locator.get_zone_building_names():
                # remove "B01", "B02" etc. from filenames -> "BXX"
                relative_filename = relative_filename.replace(building, '{BUILDING}')
            relative_filename = str(relative_filename)
            file_path = os.path.dirname(relative_filename)
            file_name = os.path.basename(relative_filename)
            if script_start < mtime:
                trace_data.add(('output', script_name, locator_method, file_path, file_name))
            else:
                trace_data.add(('input', script_name, locator_method, file_path, file_name))


    config.restricted_to = None
    create_graphviz_output(trace_data, config.trace_inputlocator.graphviz_output_file)
    create_yaml_output(trace_data, config.trace_inputlocator.yaml_output_file)


def create_graphviz_output(trace_data, graphviz_output_file):
    # creating new variable to preserve original trace_data used by other methods
    tracedata = sorted(trace_data)

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
    print(digraph)
    with open(graphviz_output_file, 'w') as f:
        f.write(digraph)


def create_yaml_output(trace_data, yaml_output_file):
    """Create a yml-style output of the trace-data for further processing"""
    import yaml
    scripts = sorted(set([td[1] for td in trace_data]))
    yml_data = {}  # script -> inputs, outputs
    for direction, script, locator, path, file in trace_data:
        yml_data[script] = yml_data.get(script, {'input': [], 'output': []})
        yml_data[script][direction].append((locator, path, file))
    for script in scripts:
        yml_data[script]['input'] = sorted(yml_data[script]['input'])
        yml_data[script]['output'] = sorted(yml_data[script]['output'])

    if os.path.exists(yaml_output_file):
        # merge existing data
        with open(yaml_output_file, 'r') as f:
            old_yml_data = yaml.load(f)
        for script in old_yml_data.keys():
            if not script in scripts:
                # make sure not to overwrite newer data!
                yml_data[script] = old_yml_data[script]

    with open(yaml_output_file, 'w') as f:
        yaml.dump(yml_data, f, default_flow_style=False)


if __name__ == '__main__':
    main(cea.config.Configuration())