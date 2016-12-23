"""
Create a graph of function calls as an overview of the CEA software.

In a first step, this only runs on the demand script and just logs which functions call which other functions.

The strategy used is to provide a handler for `sys.settrace` and log the "call" events as a tuple in a set:

    (caller, callee)

This tuple is then used to produce a GraphViz digraph that is saved to the filie "%TEMP%\demand_function_graph.gv"
"""
import inspect
import os
import pickle
import shutil
import sys
import tempfile
import zipfile

import requests


def download_radiation(locator):
    """Download radiation and surface properties for running the demand on the nincubes samples"""
    data = {'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/NALgN4Tlhho6QEC/download',
            'radiation': 'https://shared.ethz.ch/owncloud/s/uF6f4EWhPF31ko4/download'}
    r = requests.get(data['properties_surfaces'])
    assert r.ok, 'could not download the properties_surfaces.csv file'
    with open(locator.get_surface_properties(), 'w') as f:
        f.write(r.content)
    r = requests.get(data['radiation'])
    assert r.ok, 'could not download the radiation.csv file'
    with open(locator.get_radiation(), 'w') as f:
        f.write(r.content)


class TraceDataInfo(object):
    """Collects data about a trace event's frame"""
    def __init__(self, frame):
        code = frame.f_code
        self.path = code.co_filename
        self.name = code.co_name
        self.module = ''

        # figure out fully qualified name (fqname)
        fqname_parts = []
        module = inspect.getmodule(code)
        if module:
            fqname_parts.append(module.__name__)
            self.module = module.__name__

        try:
            fqname_parts.append(frame.f_locals['self'].__class__.__name__)
        except (KeyError, AttributeError):
            pass

        fqname_parts.append(self.name)
        self.fqname = '.'.join(fqname_parts)

    def is_cea(self):
        return self.fqname.startswith('cea.')

    def __repr__(self):
        return self.fqname


def trace_demand():
    """Extract the ninecubes.zip reference-case to a temporary directory and run the demand script on it
    with a default weather file, collecting trace information of each function called."""
    trace_data = []
    uniques = set()  # of (src.fqname, dst.fqname)

    def trace_calls(frame, event, arg):
        """handle trace events and update the trace_data with information of the source and destination of the call"""
        if event != 'call':
            return

        call_dst = TraceDataInfo(frame)
        if not call_dst.is_cea():
            return
        #print('call_dst: %s' % call_dst)

        call_src = find_last_cea(frame)
        #print ('call_src: %s -- %s' % (call_src, trace_data))
        if call_src and not (call_src.fqname, call_dst.fqname) in uniques:
            trace_data.append((call_src, call_dst))
            uniques.add((call_src.fqname, call_dst.fqname))
            print(call_src, call_dst)
        return

    try:
        import cea.demand.demand_main
        import cea.inputlocator
        import cea.globalvar

        scenario_path = extract_ninecubes()
        locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
        download_radiation(locator)
        weather_path = locator.get_default_weather()
        gv = cea.globalvar.GlobalVariables()
        gv.multiprocessing = False

        sys.settrace(trace_calls)
        cea.demand.demand_main.demand_calculation(locator=locator, weather_path=weather_path, gv=gv)
        sys.settrace(None)

    finally:
        # make sure we clean up after ourselves...
        remove_ninecubes()
        pass
    return trace_data


def find_last_cea(frame):
    """"Search through the stack frame for the last origination of a call from cea code"""
    if not hasattr(frame, 'f_back'):
        #print('frame has no attr f_back')
        return None
    call_src = TraceDataInfo(frame.f_back)
    if call_src.name == 'trace_demand':
        #print('call_src.name == trace_demand')
        return None

    if call_src.is_cea():
        return call_src
    else:
        #print('call_src is not cea: %s' % call_src)
        return find_last_cea(frame.f_back)



def extract_ninecubes():
    ninecubes_src = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'ninecubes.zip')
    ninecubes_dst = os.path.join(tempfile.gettempdir(), 'ninecubes.zip')
    shutil.copyfile(ninecubes_src, ninecubes_dst)
    archive = zipfile.ZipFile(ninecubes_dst)
    extraction_location = os.path.join(tempfile.gettempdir(), 'ninecubes')
    archive.extractall(extraction_location)
    scenario_path = os.path.join(extraction_location, 'nine cubes', 'baseline')
    return scenario_path


def remove_ninecubes():
    """delete the ninecubes stuff from the temp directory"""
    os.remove(os.path.join(tempfile.gettempdir(), 'ninecubes.zip'))
    shutil.rmtree(os.path.join(tempfile.gettempdir(), 'ninecubes'))


def package_names(trace_data):
    """Extract the names of the packages from the (filtered?) trace_data."""
    return ('a', 'b')

def edge_names(trace_data_item):
    return ('a', 'b')


def extract_namespace(fqname):
    return fqname.rsplit('.', 1)[0]


def extract_function_name(fqname):
    return fqname.rsplit('.', 1)[1]


def filter_trace_data(trace_data):
    """remove calls to (and from) the namespaces in the stoplist.
    This should make the output easier to read.
    """
    stoplist = ['cea.inputlocator.InputLocator',
                'cea.utilities.helpers',
                'cea.demand.thermal_loads.BuildingProperties',
                'cea.globalvar.GlobalVariables',
                'cea.demand.demand_writers.HourlyDemandWriter']
    for tdi_src, tdi_dst in trace_data:
        if extract_namespace(tdi_src.fqname) in stoplist:
            continue
        elif extract_namespace(tdi_dst.fqname) in stoplist:
            continue
        yield (tdi_src, tdi_dst)


def print_digraph(trace_data, f):
    trace_data = list(filter_trace_data(trace_data))
    all_nodes = set(tdi.fqname for td in trace_data for tdi in td)
    namespaces = set(extract_namespace(node) for node in all_nodes)

    f.writelines([
        "digraph demand_function_graph {\n",
        "  rankdir=LR;\n",
        "  ratio=0.7072135785007072;\n",
        "  edge[weight=1.2];\n",
        "  node [shape=plaintext, ranksep=0.2, nodesep=0.2, fontsize=10, fontname=monospace, color=none];\n",
    ])

    for namespace in namespaces:
        node_names = '\n'.join('    "%s";' % extract_function_name(node) for node in all_nodes if
                               extract_namespace(node) == namespace)
        f.writelines([
            '  subgraph "cluster_%(namespace)s" {\n' % locals(),
            node_names,
            '\n',
            '    label="%(namespace)s";\n' % locals(),
            '  }\n',
        ])

    for src, dst in trace_data:
        f.write('  "%s" -> "%s";\n' % (extract_function_name(src.fqname), extract_function_name(dst.fqname)))

    f.write('}\n')


def create_function_graph():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--save-trace-data', help='Save trace data to file', default=None)
    parser.add_argument('-i', '--input', help='Load trace data from file', default=None)
    parser.add_argument('-o', '--output', help='Save graphviz output to this file', default=None)
    args = parser.parse_args()

    if args.save_trace_data:
        trace_data = trace_demand()
        with open(args.save_trace_data, 'w') as f:
            pickle.dump(trace_data, f)
    elif args.input:
        with open(args.input, 'r') as f:
            trace_data = pickle.load(f)
        with open(args.output, 'w') as f:
            print_digraph(trace_data, f)
    else:
        with open(args.output, 'w') as f:
            print_digraph(trace_demand(), f)

if __name__ == '__main__':
    create_function_graph()
