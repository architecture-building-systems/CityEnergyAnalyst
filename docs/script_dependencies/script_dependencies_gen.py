"""
Script to generate script-input-outputs.rst
"""

import cea.scripts
from jinja2 import Template
import os

all_scripts = cea.scripts.list_scripts()


def get_script_dependencies():
    dependencies = []
    for script in sorted(all_scripts):
        viz_file = os.path.join(os.path.curdir, (script.name + '.gv'))
        if os.path.isfile(viz_file):
            with open(viz_file) as viz:
                digraph = viz.read()
                underline = '-'*len(script.name)
            contents = [[script.name, underline, digraph]]
            dependencies.extend(contents)
    return dependencies

template_path = os.path.join(os.path.dirname(__file__), 'script_dependencies_template.rst')
template = Template(open(template_path, 'r').read())
dependencies = get_script_dependencies()
output = template.render(dependencies=dependencies)

os.chdir(os.path.join('..\\', os.curdir))

with open('script-input-outputs.rst', 'w') as cea:
    cea.write(output)
