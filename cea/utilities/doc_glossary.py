"""
doc_glossary.py

Builds input_files.rst and output_files.rst using a jinja 2 template located in docs/templates. Both input_files.rst
and output_files.rst are referenced by glossary.rst.

"""

import os
import cea.config
import cea.scripts
import cea.glossary
from jinja2 import Template

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def main(_):
    schema = cea.scripts.schemas()
    schema_variables = cea.scripts.get_schema_variables(schema)
    documentation_dir = os.path.join(os.path.dirname(cea.config.__file__), '..', 'docs')

    # import glossary.csv and the relevant information from schema.yml
    glossary_df = cea.glossary.read_glossary_df()

    # create a set of documentation relevant input_locator_methods and output_locator_methods
    # create a set of extra details (the scripts the file is used_by)
    # create a set of variable specific tuples from the naming.csv table (glossary_data)
    input_locator_methods = set()
    output_locator_methods = set()
    details = set()
    glossary_data = set()

    for locator_method in schema:
        for variable, LOCATOR_METHOD, script, file_name in schema_variables:
            if locator_method == LOCATOR_METHOD:
                details.add((locator_method, file_name))
        # if the locator_method references an input file
        # it should have been created by no script (i.e. used_by = empty list)
        if schema[locator_method]['created_by'] == []:
            input_locator_methods.add((locator_method, '-' * len(locator_method),str(schema[locator_method]['used_by'])))
        # otherwise the locator_method references an output file
        else:
            output_locator_methods.add((locator_method, '-' * len(locator_method), str(schema[locator_method]['used_by'])))

    input_locator_methods = sorted(input_locator_methods)
    output_locator_methods = sorted(output_locator_methods)
    details = sorted(details)

    # todo this can probably be moved to a module containing all schema checking methods
    redundant_methods = set()
    for variable, locator_method, script, file_name in schema_variables:
        key = file_name + '!!!' + variable
        if key in list(glossary_df.index):
            if glossary_df.loc[key].size == len(glossary_df.columns):
                glossary_data.add(tuple(glossary_df.loc[key]))
            # in case there are multiple inputlocator methods which service the same file
            else:
                for number in range(glossary_df.loc[key].size/len(glossary_df.columns)):
                    glossary_data.add(tuple(glossary_df.loc[key].iloc[number-1]))
                    redundant_methods.add((locator_method, file_name))

    print '\n             !!! Redundancy Found !!! \n' \
          'The following inputlocator methods service similar files:'
    for locator_method, file_name in redundant_methods:
        print 'O   ' + locator_method + '   --->   ' + file_name

    glossary_data = sorted(glossary_data)

    # create the input_files.rst based of jinja2 template in docs/templates
    template_path = os.path.join(documentation_dir, 'templates', 'glossary.rst')
    template = Template(open(template_path, 'r').read())
    output = template.render(headers=input_locator_methods, tuples=glossary_data, details=details)
    with open(os.path.join(documentation_dir,'input_methods.rst'), 'w') as gloss:
        gloss.write(output)

    # create the output_files.rst based of jinja2 template in docs/templates
    template_path = os.path.join(documentation_dir, 'templates', 'glossary.rst')
    template = Template(open(template_path, 'r').read())
    output = template.render(headers=output_locator_methods, tuples=glossary_data, details=details)
    with open(os.path.join(documentation_dir,'output_methods.rst'), 'w') as gloss:
        gloss.write(output)

    print '\n ~~~~~~~~ Glossary files updated ~~~~~~~~\n'