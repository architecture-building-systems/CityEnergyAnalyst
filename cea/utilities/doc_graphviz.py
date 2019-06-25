"""
doc_graphviz.py

Creates the graphviz output used to visualize script dependencies.
This file relies on the schema.yml to create the graphviz plots.

"""

import os
import cea.config
import cea.scripts
from jinja2 import Template
import os

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_graphviz_files(graphviz_data, documentation_dir):
    for script in graphviz_data:
        # creating new variable to preserve original trace_data used by other methods
        tracedata = sorted(graphviz_data[script])
        # replacing any relative paths outside the case dir with the last three dirs in the path
        # this prevents long path names in digraph clusters
        for i, (direction, Script, method, path, db) in enumerate(tracedata):
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
        width = 5

        # jinja2 template setup and execution
        template_path = os.path.join(documentation_dir, 'templates/graphviz_template.gv')
        template = Template(open(template_path, 'r').read())
        digraph = template.render(tracedata=tracedata, scripts=scripts, db_group=db_group, width=width)
        digraph = '\n'.join([line for line in digraph.split('\n') if len(line.strip())])
        with open(os.path.join(documentation_dir, 'graphviz/%s.gv' % script), 'w') as f:
            f.write(digraph)


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
    import cea
    schema = cea.scripts.schemas()
    schema_scripts = cea.scripts.get_schema_scripts(schema)
    documentation_dir = os.path.join(os.path.dirname(cea.config.__file__), '..', 'docs')

    graphviz_data = {}

    for script in schema_scripts:
        trace_data = set()
        for locator_method in schema:
            file_path = schema[locator_method]['file_path'].replace('\\', '/')
            file_name = file_path.rsplit('/', 1)[1]
            path = file_path.rsplit('/', 1)[0]
            if script in schema[locator_method]['created_by']:
                trace_data.add(('output', script, locator_method, path, file_name))
            elif schema[locator_method]['created_by'] == []:
                trace_data.add(('input', script, locator_method, path, file_name))
            if script in schema[locator_method]['used_by']:
                trace_data.add(('input', script, locator_method, path, file_name))
        graphviz_data[script] = trace_data

    create_graphviz_files(graphviz_data, documentation_dir)
    list_of_digraphs = get_list_of_digraphs(documentation_dir=documentation_dir, schema_scripts=schema_scripts)

    template_path = os.path.join(documentation_dir, 'templates/graphviz_template.rst')
    template = Template(open(template_path, 'r').read())

    output = template.render(list_of_digraphs=list_of_digraphs)

    with open(os.path.join(documentation_dir,'script-data-flow.rst'), 'w') as cea:
        cea.write(output)

    print '~~~~~~~~ script-data-flow.rst updated ~~~~~~~~\n'

if __name__ == '__main__':
    main(cea.config.Configuration(), cea.scripts.schemas())
