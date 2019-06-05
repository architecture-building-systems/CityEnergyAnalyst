"""
doc.py

The main module for cea-dev doc tool.
"""

import cea.inputlocator
import os
import cea.utilities.doc_update_naming as update_naming_csv
import cea.utilities.doc_glossary as create_glossary_rst
import cea.utilities.doc_graphviz as create_graphviz_rst
import cea.utilities.doc_html as create_docs_html_files

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

locator = cea.inputlocator.InputLocator(cea.config.Configuration().scenario)
all_scripts = list(script.name for script in cea.scripts.list_scripts())
schema = cea.scripts.schemas()
schema_variables = cea.scripts.get_schema_variables()

def main():
    update_naming_csv.main(
        naming_csv_file=locator.get_naming(),
        schema_variables=schema_variables
    )
    # todo replace naming_csv_file when naming_new.csv is obsolete
    create_glossary_rst.main(
        documentation_dir=locator.get_docs_folder(),
        schema_variables=schema_variables,
        schema_data=schema,
        naming_csv_file=os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv')
    )
    create_graphviz_rst.main(
        schema=schema,
        documentation_dir=locator.get_docs_folder()
    )
    # create_docs_html_files.main(
    #     documentation_dir=locator.get_docs_folder()
    # )


if __name__ == '__main__':
    main()