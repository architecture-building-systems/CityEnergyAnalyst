"""
doc_glossary.py

Builds input_files.rst and output_files.rst using a jinja 2 template located in docs/templates. Both input_files.rst
and output_files.rst are referenced by glossary.rst.

"""

import os

from jinja2 import Template, environment

import cea.config
import cea.schemas

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


def sort_dict(_dict):
    """
    Sort dicts according to keys. Works with keys of mixed type i.e int and str, by casting it to str (ignoring case)

    :param dict _dict: dict to be sorted
    :return: sorted dict by keys
    """
    return {key: _dict[key] for key in sorted(_dict.keys(),
                                              key=lambda v: (
                                                  isinstance(v, str), v.lower() if isinstance(v, str) else v))}


def main(_=None):
    schemas = cea.schemas.schemas(plugins=[])
    documentation_dir = os.path.join(os.path.dirname(cea.config.__file__), '..', 'docs')
    environment.DEFAULT_FILTERS['add_backticks'] = add_backticks
    environment.DEFAULT_FILTERS['sort_dict'] = sort_dict
    template_path = os.path.join(documentation_dir, 'templates', 'glossary.rst')
    template = Template(open(template_path, 'r').read())

    # write input_methods
    input_locators = {lm: schemas[lm] for lm in schemas if not schemas[lm]['created_by']}
    with open(os.path.join(documentation_dir, "input_methods.rst"), "w") as input_methods_fp:
        input_methods_fp.write(template.render(schemas=input_locators))
    # write intermediate_input_methods
    intermediate_input_locators = {lm: schemas[lm] for lm in schemas if
                                   'database_helper' in schemas[lm]['created_by'] or 'archetypes_mapper' in
                                   schemas[lm]['created_by']}
    with open(os.path.join(documentation_dir, "intermediate_input_methods.rst"), "w") as intermediate_input_methods_fp:
        intermediate_input_methods_fp.write(template.render(schemas=intermediate_input_locators))
    # write output_methods
    output_locators = {lm: schemas[lm] for lm in schemas if
                       lm not in input_locators and lm not in intermediate_input_locators}
    with open(os.path.join(documentation_dir, "output_methods.rst"), "w") as output_methods_fp:
        output_methods_fp.write(template.render(schemas=output_locators))
    # error check
    if len(schemas) - (len(input_locators) + len(intermediate_input_locators) + len(output_locators)) > 0:
        raise ('Number of locators not matched! Please review lines before this error message in doc_glossray.py.')


if __name__ == "__main__":
    main()
