"""
Create a graph of function calls as an overview of the CEA software.

In a first step, this only runs on the demand script and just logs which functions call which other functions.

The strategy used is to provide a handler for `sys.settrace` and log the "call" events as a tuple in a set:

    (caller, callee)

This tuple is then used to produce a GraphViz digraph that is saved to the filie "%TEMP%\demand_function_graph.gv"
"""
import os
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


def trace_demand():
    """Extract the ninecubes.zip reference-case to a temporary directory and run the demand script on it
    with a default weather file, collecting trace information of each function called."""
    caller_callee_pairs = set()
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    print(root)

    def trace_calls(frame, event, arg):
        """handle trace events and update the caller_callee_pairs set of tuples"""
        if event != 'call':
            return
        if hasattr(frame, 'f_code'):
            co = frame.f_code
            func_filename = co.co_filename
            if not 'CEAforArcGIS' in func_filename:
                return
            func_name = co.co_name
            callee = os.path.join(os.path.relpath(func_filename, root), func_name)
        else:
            return

        if hasattr(frame, 'f_back'):
            caller_frame = frame.f_back
            caller_name = caller_frame.f_code.co_name
            caller_filename = caller_frame.f_code.co_filename
            if not 'CEAforArcGIS' in func_filename:
                return
            caller = os.path.join(os.path.relpath(caller_filename, root), caller_name)
        else:
            return

        if func_name == 'write':
            # Ignore write() calls from print statements
            return

        caller_callee_pairs.add((caller, callee))
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
    return caller_callee_pairs


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


def print_digraph(caller_callee_pairs):
    with open(os.path.join(tempfile.gettempdir(), 'demand_function_graph.gv'), 'w') as f:
        f.write('digraph demand_function_graph {\n')
        f.write('  node [shape=box]\n')
        f.write('  rankdir=LR\n')
        for caller, callee in caller_callee_pairs:
            caller = caller.replace('\\', '.')
            callee = callee.replace('\\', '.')
            f.write('  "%(caller)s" -> "%(callee)s";\n' % locals())
        f.write('}\n')

def create_function_graph():
    caller_callee_pairs = trace_demand()
    print_digraph(caller_callee_pairs)


if __name__ == '__main__':
    create_function_graph()
