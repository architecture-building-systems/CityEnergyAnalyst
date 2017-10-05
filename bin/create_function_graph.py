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

FUNCTIONS = ["benchmark_graphs", "data_helper", "demand_graphs", "demand", "embodied_energy", "emissions", "heatmaps",
             "mobility", "radiation", "scenario_plots"]


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


def trace_function(function_to_trace):
    """Extract the ninecubes.zip reference-case to a temporary directory and run the script 'function_to_trace' on it
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
        # print('call_dst: %s' % call_dst)

        call_src = find_last_cea(frame)
        # print ('call_src: %s -- %s' % (call_src, trace_data))
        if call_src and not (call_src.fqname, call_dst.fqname) in uniques:
            trace_data.append((call_src, call_dst))
            uniques.add((call_src.fqname, call_dst.fqname))
            print(call_src, call_dst)
        return

    import cea.globalvar
    import cea.config

    scenario_path = extract_ninecubes()
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    gv = cea.globalvar.GlobalVariables()
    config = cea.config.Configuration(scenario_path=scenario_path)
    config._parser.set('global', 'multiprocessing', False)
    config.save()
    download_radiation(locator)
    weather_path = locator.get_default_weather()

    sys.settrace(trace_calls)
    function_to_trace(gv, locator, weather_path)
    sys.settrace(None)

    return trace_data


def find_last_cea(frame):
    """"Search through the stack frame for the last origination of a call from cea code"""
    if not hasattr(frame, 'f_back') or frame.f_back is None:
        # print('frame has no attr f_back')
        return None
    call_src = TraceDataInfo(frame.f_back)
    if call_src.name == 'trace_demand':
        # print('call_src.name == trace_demand')
        return None

    if call_src.is_cea():
        return call_src
    else:
        # print('call_src is not cea: %s' % call_src)
        # print('  frame.f_back: %s' % frame.f_back)
        return find_last_cea(frame.f_back)


def extract_ninecubes():
    extraction_location = os.path.join(tempfile.gettempdir(), 'ninecubes')
    scenario_path = os.path.join(extraction_location, 'nine cubes', 'baseline')

    if not os.path.exists(scenario_path):
        ninecubes_src = os.path.join(os.path.dirname(__file__), '..', 'examples', 'ninecubes.zip')
        ninecubes_dst = os.path.join(tempfile.gettempdir(), 'ninecubes.zip')
        shutil.copyfile(ninecubes_src, ninecubes_dst)
        archive = zipfile.ZipFile(ninecubes_dst)
        archive.extractall(extraction_location)
    return scenario_path


def remove_ninecubes():
    """delete the ninecubes stuff from the temp directory"""
    ninecubes_zip = os.path.join(tempfile.gettempdir(), 'ninecubes.zip')
    if os.path.exists(ninecubes_zip):
        os.remove(ninecubes_zip)

    ninecubes_dir = os.path.join(tempfile.gettempdir(), 'ninecubes')
    if os.path.exists(ninecubes_dir):
        shutil.rmtree(ninecubes_dir)


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
                'cea.demand.demand_writers.HourlyDemandWriter',
                'cea.demand.thermal_loads.BuildingPropertiesRow']
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
        "  node [shape=plaintext, ranksep=0.7, nodesep=0.7, fontsize=10, fontname=monospace, color=none];\n",
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


def create_module_overview(trace_data):
    """Compress the list of connections in the trace_data to only the modules. So instead of tracing function
    calls, trace module-to-module calls. This can give more overview of the code as it is higher level.
    """

    class OverviewTraceDataInfo(object):
        """Imitate a TDI, but only sets the fqname attribute"""

        def __init__(self, fqname):
            self.fqname = fqname

    module_calls = set()  # list of (src_module, dst_module)
    for tdi_src, tdi_dst in filter_trace_data(trace_data):
        src_module = extract_namespace(tdi_src.fqname)
        dst_module = extract_namespace(tdi_dst.fqname)
        if src_module == dst_module:
            # skip self-references
            continue
        module_calls.add((src_module, dst_module))
    return [(OverviewTraceDataInfo(src_module), OverviewTraceDataInfo(dst_module))
            for src_module, dst_module in module_calls]


def get_function_to_trace(function):
    functions = {
        "benchmark_graphs": run_benchmark_graphs,
        "data_helper": run_data_helper,
        "demand_graphs": run_demand_graphs,
        "demand": run_demand,
        "embodied_energy": run_embodied_energy,
        "emissions": run_emissions,
        "heatmaps": run_heatmaps,
        "mobility": run_mobility,
        "radiation": None,
        "scenario_plots": None}
    return functions[function]


def run_benchmark_graphs(gv, locator, weather_path):
    import cea.analysis.benchmark
    locator_list = [locator]
    output_file = tempfile.mktemp(suffix='.pdf')
    cea.analysis.benchmark.benchmark(locator_list=locator_list, output_file=output_file)


def run_demand_graphs(gv, locator, weather_path):
    import cea.plots.graphs_demand
    analysis_fields = ["Ealf_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    cea.plots.graphs_demand.graphs_demand(locator=locator, analysis_fields=analysis_fields, gv=gv)


def run_data_helper(gv, locator, weather_path):
    import cea.demand.preprocessing.properties
    cea.demand.preprocessing.properties.properties(locator=locator, prop_thermal_flag=True, prop_architecture_flag=True,
                                                   prop_hvac_flag=True, prop_comfort_flag=True,
                                                   prop_internal_loads_flag=True, gv=gv)


def run_demand(gv, locator, weather_path):
    import cea.demand.demand_main
    cea.demand.demand_main.demand_calculation(locator=locator, weather_path=weather_path, gv=gv)


def run_embodied_energy(gv, locator, weather_path):
    import cea.analysis.lca.embodied
    cea.analysis.lca.embodied.lca_embodied(year_to_calculate=2014, locator=locator, gv=gv)


def run_emissions(gv, locator, weather_path):
    import cea.analysis.lca.operation
    cea.analysis.lca.operation.lca_operation(locator=locator, Qww_flag=(True), Qhs_flag=(True), Qcs_flag=(True),
                                             Qcdata_flag=(True), Qcrefri_flag=(True), Eal_flag=(True), Eaux_flag=(True),
                                             Epro_flag=(True), Edata_flag=(True))


def run_heatmaps(gv, locator, weather_path):
    import cea.plots.heatmaps
    file_to_analyze = locator.get_total_demand()
    analysis_fields = ["Qhsf_MWhyr", "Qcsf_MWhyr"]
    path_results = locator.get_heatmaps_demand_folder()
    cea.plots.heatmaps.heatmaps(locator=locator, analysis_fields=analysis_fields, path_results=path_results,
                                file_to_analyze=file_to_analyze)


def run_mobility(gv, locator, weather_path):
    import cea.analysis.lca.mobility
    cea.analysis.lca.mobility.lca_mobility(locator=locator)


def create_function_graph(input=None, output=None, save_trace_data=None, module_overview=False, function_name='demand'):
    if input:
        # create a graph using trace data that was previously saved to a file
        with open(input, 'r') as f:
            trace_data = pickle.load(f)
    else:
        # run function to create trace data
        trace_data = trace_function(get_function_to_trace(function_name))

    if save_trace_data:
        # save a copy of the trace data to a file for later retrieval
        with open(save_trace_data, 'w') as f:
            pickle.dump(trace_data, f)

    if output:
        # write out a GraphViz graph to this file
        if module_overview:
            trace_data = create_module_overview(trace_data)
        with open(output, 'w') as f:
            print_digraph(trace_data, f)


def parse_arguments(argv):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--save-trace-data', help='Save trace data to file', default=None)
    parser.add_argument('-i', '--input', help='Load trace data from file', default=None)
    parser.add_argument('-o', '--output', help='Save graphviz output to this file', default=None)
    parser.add_argument('-m', '--module-overview', help='Create a module overview', action='store_true')
    parser.add_argument('-f', '--function', help='Function to run', default="demand", choices=FUNCTIONS)
    args = parser.parse_args(argv)
    return args


if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])
    create_function_graph(input=args.input, output=args.output, save_trace_data=args.save_trace_data,
                          module_overview=args.module_overview, function_name=args.function)
