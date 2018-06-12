"""
Trace the InputLocator calls in a selection of scripts.
"""
import sys
import os

import cea.config
import cea.api
import pprint
from collections import defaultdict
from datetime import datetime
from jinja2 import Template


def create_trace_function(results_set):
    """results_set is a set of tuples (locator, filename)"""
    def trace_function(frame, event, arg):
        """Trace any calls to the InputLocator"""
        co = frame.f_code
        func_name = co.co_name
        if func_name == 'write':
            # Ignore write() calls from print statements
            return
        line_no = frame.f_lineno
        filename = co.co_filename
        if event == 'call':
            # decend into the stack...
            return trace_function
        elif event == 'return':
            if isinstance(arg, basestring) and 'inputlocator' in filename.lower() and not func_name.startswith('_'):
                results_set.add((func_name, arg))
                print('%s => %s' % (func_name, arg))
        return
    return trace_function


def main(config):
    # force single-threaded execution, see settrace docs for why
    config.multiprocessing = False
    script_func_list = [getattr(cea.api, script_name.replace('-', '_')) for script_name in config.trace_inputlocator.scripts]

    trace_data = set()  # {(direction, script, locator_method, file)}

    for script_func in script_func_list:
        script_start = datetime.now()
        results_set = set()  # {(locator_method, filename)}

        orig_trace = sys.gettrace()
        sys.settrace(create_trace_function(results_set))
        script_func(config)  # <------------------------------ this is where we run the script!
        sys.settrace(orig_trace)

        for locator_method, filename in results_set:
            if os.path.isdir(filename):
                continue
            print("{}, {}".format(locator_method, filename))
            mtime = datetime.fromtimestamp(os.path.getmtime(filename))
            relative_filename = os.path.relpath(filename, config.scenario).replace('\\', '/')
            for i in range(10):
                # remove "B01", "B02" etc. from filenames -> "BXX"
                relative_filename = relative_filename.replace('B%02d' % i, 'BXX')
            if script_start < mtime:
                trace_data.add(('output', script_name, locator_method, relative_filename))
            else:
                trace_data.add(('input', script_name, locator_method, relative_filename))

    create_graphviz_output(trace_data, config.trace_inputlocator.graphviz_output_file)
    create_yaml_output(trace_data, config.trace_inputlocator.yaml_output_file)


def create_graphviz_output(trace_data, graphviz_output_file):
    template_path = os.path.join(os.path.dirname(__file__), 'trace_inputlocator.template.gv')
    template = Template(open(template_path, 'r').read())
    scripts = sorted(set([td[1] for td in trace_data]))
    digraph = template.render(trace_data=trace_data, scripts=scripts)
    digraph = '\n'.join([line for line in digraph.split('\n') if len(line.strip())])
    print(digraph)
    with open(graphviz_output_file, 'w') as f:
        f.write(digraph)


def create_yaml_output(trace_data, yaml_output_file):
    """Create a yml-style output of the trace-data for further processing"""
    import yaml
    scripts = sorted(set([td[1] for td in trace_data]))
    yml_data = {}  # script -> inputs, outputs
    for direction, script, locator, file in trace_data:
        yml_data[script] = yml_data.get(script, {'input': [], 'output': []})
        yml_data[script][direction].append(file)
    for script in scripts:
        yml_data[script]['input'] = sorted(yml_data[script]['input'])
        yml_data[script]['output'] = sorted(yml_data[script]['output'])
    with open(yaml_output_file, 'w') as f:
        yaml.dump(yml_data, f, default_flow_style=False)


if __name__ == '__main__':
    main(cea.config.Configuration())