"""
Contains some helper methods for working with glossary.csv
"""
from __future__ import print_function
from __future__ import division

import os
import csv
import pandas as pd

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_glossary_df():
    """Returns the glossary as a DataFrame"""
    glossary_df = pd.read_csv(_path_to_glossary_csv(), sep=',')
    glossary_df['key'] = glossary_df['FILE_NAME'] + '!!!' + glossary_df['VARIABLE']
    glossary_df = glossary_df.set_index(['key'])
    glossary_df = glossary_df.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])
    return glossary_df


def read_glossary_dicts():
    """Returns the glossary as a list of dicts"""
    with open(_path_to_glossary_csv()) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def _path_to_glossary_csv():
    return os.path.join(os.path.dirname(__file__), 'glossary.csv')