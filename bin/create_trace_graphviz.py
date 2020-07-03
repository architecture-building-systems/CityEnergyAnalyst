"""
Read in the output from the trace-inputlocator script and create a GraphViz file.

Pass as input the path to the yaml output of the trace-inputlocator script via config file.
The output is written to the trace-inputlocator location.

WHY? because the trace-inputlocator only has the GraphViz output of the last call to the script. This
version re-creates the trace-data from the (merged) yaml file (the yaml output is merged if pre-existing in the output
file).
"""


import yaml
import cea.config
from cea.tests.trace_inputlocator import create_graphviz_output

def main(config):
    with open(config.trace_inputlocator.yaml_output_file, 'r') as f:
        yaml_data = yaml.safe_load(f)

    trace_data = []
    for script in yaml_data.keys():
        for direction in ('input', 'output'):
            for locator, file in yaml_data[script][direction]:
                trace_data.append((direction, script, locator, file))

    create_graphviz_output(trace_data, config.trace_inputlocator.graphviz_output_file)


if __name__ == '__main__':
    main(cea.config.Configuration())