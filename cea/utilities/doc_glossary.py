"""
doc_glossary.py

Builds input_files.rst and output_files.rst using a jinja 2 template located in docs/templates. Both input_files.rst and output_files.rst
 are referenced by glossary.rst.

"""

import os
import cea.inputlocator
import cea.config
import cea.scripts
import pandas
from jinja2 import Template

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


locator = cea.inputlocator.InputLocator(cea.config.Configuration().scenario)


def main(documentation_dir):
    # TODO replace once naming merge has been completed
    NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv')
    naming = pandas.read_csv(NAMING_FILE_PATH, sep=',')
    naming['key'] = naming['FILE_NAME'] + '!!!' + naming['VARIABLE']
    naming = naming.set_index(['key'])
    naming = naming.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])

    metadata = cea.scripts.schemas()
    META_VARIABLES = cea.scripts.get_schema_variables()


    input_locator_methods = set()
    details = set()
    output_locator_methods = set()
    glossary_data = set()

    for locator_method in metadata:
        for var, LOCATOR_METHOD, script, file_name in META_VARIABLES:
            if locator_method == LOCATOR_METHOD:
                details.add((locator_method, file_name))
        if metadata[locator_method]['created_by'] == []:
            input_locator_methods.add((locator_method, '-' * len(locator_method),str(metadata[locator_method]['used_by'])))
        else:
            output_locator_methods.add((locator_method, '-' * len(locator_method), str(metadata[locator_method]['used_by'])))

    input_locator_methods = sorted(input_locator_methods)
    output_locator_methods = sorted(output_locator_methods)
    details = sorted(details)


    redundant_methods = set()
    for var, locator_method, script, file_name in META_VARIABLES:
        key = file_name + '!!!' + var
        if key in list(naming.index):
            if naming.loc[key].size == 9:
                glossary_data.add(tuple(naming.loc[key]))

            # in case there are multiple inputlocator methods which service the same file
            else:
                for number in range(naming.loc[key].size/9):
                    glossary_data.add(tuple(naming.loc[key].iloc[number-1]))
                    redundant_methods.add((locator_method, file_name))

    print '             !!! Redundancy Found !!! \n' \
          'The following inputlocator methods service similar files:'
    for locator_method, file_name in redundant_methods:
        print 'O   ' + locator_method + '   --->   ' + file_name

    glossary_data = sorted(glossary_data)

    template_path = os.path.join(documentation_dir, 'templates\\gloss_template.rst')
    template = Template(open(template_path, 'r').read())
    output = template.render(headers=input_locator_methods, tuples=glossary_data, details=details)
    with open(os.path.join(documentation_dir,'input_files.rst'), 'w') as gloss:
        gloss.write(output)

    template_path = os.path.join(documentation_dir, 'templates\\gloss_template.rst')
    template = Template(open(template_path, 'r').read())
    output = template.render(headers=output_locator_methods, tuples=glossary_data, details=details)
    with open(os.path.join(documentation_dir,'output_files.rst'), 'w') as gloss:
        gloss.write(output)

    print '\n ~ Glossary files input_files.rst and output_files.rst have been generated in /docs'

if __name__ == '__main__':
    main(locator.get_docs_folder())