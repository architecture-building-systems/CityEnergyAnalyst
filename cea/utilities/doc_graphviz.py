"""
doc_graphviz.py

Creates the graphviz output used to visualize script dependencies.
This file relies on the schemas.yml to create the graphviz plots.
"""

from __future__ import print_function
from __future__ import division

import os
import cea.config
import cea.scripts
from jinja2 import Template

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_graphviz_files(graphviz_data, documentation_dir):
    """
    :param dict graphviz_data: maps script names to a set of
                               (input/output, script, locator_method, folder_name, file_name)
    :param documentation_dir: folder with the documentation in it ($repo/docs)
    :return: None
    """
    if os.path.exists(os.path.join(documentation_dir, "graphviz")):
        for fname in os.listdir(os.path.join(documentation_dir, "graphviz")):
            print("deleting {fname}".format(fname=fname))
            os.remove(os.path.join(documentation_dir, "graphviz", fname))

    for script_name in graphviz_data:
        # creating new variable to preserve original trace_data used by other methods
        trace_data = shorten_trace_data_paths(sorted(graphviz_data[script_name]))

        # set of unique scripts
        scripts = sorted(set([td[1] for td in trace_data]))

        # set of common dirs for each file accessed by the script(s)
        db_group = sorted(set(td[3] for td in trace_data))

        # float containing the node width for the largest file name
        width = 5

        # jinja2 template setup and execution
        template_path = os.path.join(documentation_dir, "templates", "graphviz_template.gv")
        template = Template(open(template_path, 'r').read())
        digraph = template.render(tracedata=trace_data, script_name=script_name, scripts=scripts, db_group=db_group,
                                  width=width)
        digraph = remove_extra_lines(digraph)
        with open(os.path.join(documentation_dir, "graphviz", "{script}.gv".format(script=script_name)), 'w') as f:
            f.write(digraph)


def remove_extra_lines(digraph):
    digraph = "\n".join([line for line in digraph.split('\n') if len(line.strip())])
    return digraph


def shorten_trace_data_paths(trace_data):
    """
    Shorten the paths in trace_data to max 3 components
    :param trace_data:
    :return:
    """
    for i, (direction, _script, method, path, db) in enumerate(trace_data):
        path = "/".join(path.rsplit('/')[-3:])  # only keep max last 3 components
        trace_data[i] = (direction, _script, method, path, db)
    return trace_data


def get_list_of_digraphs(documentation_dir, schema_scripts):
    list_of_digraphs = []
    for script in schema_scripts:

        graphviz_file = os.path.join(documentation_dir, 'graphviz/%s.gv' % script)
        if os.path.isfile(graphviz_file):
            underline = '-' * len(script)
            with open(graphviz_file) as viz:
                digraph = viz.read()
            contents = [[script, underline, digraph]]
            list_of_digraphs.extend(contents)
    return list_of_digraphs


def main(_):
    schemas = cea.scripts.schemas()
    schema_scripts = cea.scripts.get_schema_scripts()
    documentation_dir = os.path.join(os.path.dirname(cea.config.__file__), '..', 'docs')

    graphviz_data = {}

    for script in schema_scripts:
        trace_data = set()
        for locator_method in schemas:
            file_path = schemas[locator_method]['file_path']
            file_name = os.path.basename(file_path)
            folder_name = os.path.dirname(file_path)
            if script in schemas[locator_method]['created_by']:
                trace_data.add(('output', script, locator_method, folder_name, file_name))
            if script in schemas[locator_method]['used_by']:
                trace_data.add(('input', script, locator_method, folder_name, file_name))
        graphviz_data[script] = trace_data

    create_graphviz_files(graphviz_data, documentation_dir)
    list_of_digraphs = get_list_of_digraphs(documentation_dir=documentation_dir, schema_scripts=schema_scripts)

    template_path = os.path.join(documentation_dir, "templates", "graphviz_template.rst")
    template = Template(open(template_path, 'r').read())

    with open(os.path.join(documentation_dir,'script-data-flow.rst'), 'w') as fp:
        fp.write(template.render(list_of_digraphs=list_of_digraphs))


if __name__ == '__main__':
    main(cea.config.Configuration())
