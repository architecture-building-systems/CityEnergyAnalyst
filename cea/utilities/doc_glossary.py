from __future__ import print_function

"""
doc_glossary.py

Builds input_files.rst and output_files.rst using a jinja 2 template located in docs/templates. Both input_files.rst
and output_files.rst are referenced by glossary.rst.

"""

import os
import cea.config
import cea.scripts
import cea.glossary
from jinja2 import Template, environment

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def add_backticks(s):
    """
    Adds double-backticks to the beginning and end of s for mono-spaced rst output.

    e.g.: add_backticks("zone_helper") -> "``zone_helper``"
    """
    return "``{s}``".format(s=s)


def main(_=None):
    schemas = cea.scripts.schemas()
    documentation_dir = os.path.join(os.path.dirname(cea.config.__file__), '..', 'docs')
    environment.DEFAULT_FILTERS['add_backticks'] = add_backticks
    template_path = os.path.join(documentation_dir, 'templates', 'glossary.rst')
    template = Template(open(template_path, 'r').read())


    input_locators = {lm: schemas[lm] for lm in schemas if not schemas[lm]['created_by']}
    with open(os.path.join(documentation_dir, "input_methods.rst"), "w") as input_methods_fp:
        input_methods_fp.write(template.render(schemas=input_locators))

    output_locators = {lm: schemas[lm] for lm in schemas if not schemas[lm]['created_by']}
    with open(os.path.join(documentation_dir, "output_methods.rst"), "w") as output_methods_fp:
        output_methods_fp.write(template.render(schemas=output_locators))


if __name__ == "__main__":
    main()