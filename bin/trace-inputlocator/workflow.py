import sys
from datetime import datetime

import cea
from cea.workflows.workflow import run


def run_with_trace(config, script, **kwargs):
    """Same as run, but use the trace-inputlocator functionality to capture InputLocator calls"""
    from .trace_inputlocator import create_trace_function, update_trace_data, meta_to_yaml

    if "multiprocessing" in kwargs:
        # we can only trace single processes
        kwargs["multiprocessing"] = False

    # stuff needed for trace-inputlocator
    script_start = datetime.datetime.now()
    results_set = set()
    orig_trace = sys.gettrace()
    sys.settrace(create_trace_function(results_set))

    run(config, script, **kwargs)  # <------------------------------ this is where we run the script!

    sys.settrace(orig_trace)

    # update the trace data
    trace_data = set()
    update_trace_data(config, cea.inputlocator.InputLocator(config.scenario), results_set, script,
                      script_start, trace_data)
    meta_to_yaml(config, trace_data, config.trace_inputlocator.meta_output_file)