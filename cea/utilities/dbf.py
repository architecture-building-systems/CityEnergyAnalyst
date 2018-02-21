from __future__ import print_function
from __future__ import division

"""
A collection of utility functions for working with ``*.DBF`` (dBase database) files.

This code is based on a script by Clayton Miller in 2014 and further work by Jimeno A. Fonseca in 2016.
"""

import pysal
import numpy as np
import pandas as pd
import os

__author__ = "Clayton Miller"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Clayton Miller", "Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

TYPE_MAPPING = {
    int: ('N', 20, 0),
    np.int64: ('N', 20, 0),
    float: ('N', 36, 15),
    np.float64: ('N', 36, 15),
    unicode: ('C', 25, 0),
    str: ('C', 25, 0),
    np.bool_: ('L',1,0)}


def dataframe_to_dbf(df, dbf_path, specs=None):
    """Given a pandas Dataframe, write a dbase database to ``dbf_path``.

    :type df: pandas.Dataframe
    :type dbf_path: basestring
    :param specs: A list of column specifications for the dbase table. Each column is specified by a tuple (datatype,
        size, decimal) - we support ``datatype in ('N', 'C')`` for strings, integers and floating point numbers, if
        no specs are provided (see ``TYPE_MAPPING``)
    :type specs: list[tuple(basestring, int, int)]
    """
    if specs is None:
        types = [type(df[i].iloc[0]) for i in df.columns]
        specs = [TYPE_MAPPING[t] for t in types]
    dbf = pysal.open(dbf_path, 'w', 'dbf')
    dbf.header = list(df.columns)
    dbf.field_spec = specs
    for row in range(len(df)):
        dbf.write(df.iloc[row])
    dbf.close()
    return dbf_path


def dbf_to_dataframe(dbf_path, index=None, cols=False, include_index=False):
    db = pysal.open(dbf_path)
    if cols:
        if include_index:
            cols.append(index)
        vars_to_read = cols
    else:
        vars_to_read = db.header
    data = dict([(var, db.by_col(var)) for var in vars_to_read])
    if index:
        index = db.by_col(index)
        db.close()
        return pd.DataFrame(data, index=index)
    else:
        db.close()
        return pd.DataFrame(data)


def xls_to_dbf(input_path, output_path):
    if not (input_path.endswith('.xls') or input_path.endswith('.xlsx')):
        raise ValueError('Excel input file should have *.xls or *.xlsx extension')

    if not os.path.exists(input_path):
        raise ValueError('Excel input file does not exist')

    if not output_path.endswith('.dbf'):
        raise ValueError('DBF output file should have *.dbf extension')

    df = pd.read_excel(input_path)
    dataframe_to_dbf(df, output_path)


def dbf_to_xls(input_path, output_path):
    if not input_path.endswith('.dbf'):  # check if the extension of the input is dbf
        raise ValueError('DBF input file should have *.dbf extension')

    if not os.path.exists(input_path):
        raise ValueError('DBF input file does not exist')

    if not output_path.endswith('.xls'):  # check if the extension of the input is xls
        raise ValueError('Excel output file should have *.xls extension')

    df = dbf_to_dataframe(input_path)
    df.to_excel(output_path)


def run_as_script(input_path, output_path):
    if input_path.endswith('.dbf'):
        dbf_to_xls(input_path=input_path, output_path=output_path)
    elif input_path.endswith('.xls'):
        xls_to_dbf(input_path=input_path, output_path=output_path)
    else:
        print('input file type not supported')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path')
    parser.add_argument('--output-path')
    args = parser.parse_args()
    run_as_script(input_path=args.input_path, output_path=args.output_path)
