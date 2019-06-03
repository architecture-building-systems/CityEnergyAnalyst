"""
doc_clean.py

Deletes all documentation html files in docs/_build via the docs make.bat

"""

import cea.inputlocator
import os

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

locator = cea.inputlocator.InputLocator(cea.config.Configuration().scenario)


def main(docs_dir):
    os.chdir(docs_dir)
    os.system('make clean')


if __name__ == '__main__':
    main(locator.get_docs_folder())