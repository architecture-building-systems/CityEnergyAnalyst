"""
Create a graph of function calls as an overview of the CEA software.

In a first step, this only runs on the demand script and just logs which functions call which other functions.

The strategy used is to provide a handler for `sys.settrace` and log the "call" events as a tuple in a set:

    (caller-function-name, caller-file, callee-function-name, callee-file)

This tuple is then used to produce a GraphViz digraph.
"""
import os
import pprint
import shutil
import tempfile
import zipfile
import sys


def trace_demand():
    """Extract the ninecubes.zip reference-case to a temporary directory and run the demand script on it
    with a default weather file, collecting trace information of each function called."""
    caller_callee_pairs = set()

    def trace_calls(frame, event, arg):
        """handle trace events and update the caller_callee_pairs set of tuples"""
        if event != 'call':
            return
        if hasattr(frame, 'f_code'):
            co = frame.f_code
            func_filename = co.co_filename
            func_name = co.co_name
        else:
            func_name = '<undefined>'
            func_filename = '<undefined>'

        if hasattr(frame, 'f_back'):
            caller = frame.f_back
            caller_name = caller.f_code.co_name
            caller_filename = caller.f_code.co_filename
        else:
            caller_name = '<undefined>'
            caller_filename = '<undefined>'

        if func_name == 'write':
            # Ignore write() calls from print statements
            return

        caller_callee_pairs.add((caller_name, caller_filename, func_name, func_filename))
        return

    try:
        scenario_path = extract_ninecubes()
        print(scenario_path)
        sys.settrace(trace_calls)

        import cea.demand.demand_main
        import cea.inputlocator
        import cea.globalvar

        locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
        weather_path = locator.get_default_weather()
        gv = cea.globalvar.GlobalVariables()
        gv.multiprocessing = False

        cea.demand.demand_main.demand_calculation(locator=locator, weather_path=weather_path, gv=gv)

        sys.settrace(None)
    finally:
        # make sure we clean up after ourselves...
        #remove_ninecubes()
        pass
    return caller_callee_pairs

def a():
    b()

def b():
    print('hello, world')


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
    pprint.pprint(caller_callee_pairs)


def create_function_graph():
    caller_callee_pairs = trace_demand()
    print_digraph(caller_callee_pairs)


if __name__ == '__main__':
    create_function_graph()
