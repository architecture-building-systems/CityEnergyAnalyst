from __future__ import print_function
from __future__ import division


"""
A collection of utility functions for working with ``*.DBF`` (dBase database) files.

"""

import numpy as np
import pandas as pd
import os
import cea.config

# import PySAL without the warning
import warnings
warnings.simplefilter('ignore', np.VisibleDeprecationWarning)
import pysal

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
    np.bool_: ('L', 1, 0)}


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

    # handle case of strings that are longer than 25 characters (e.g. for the "Name" column)
    for i in range(len(specs)):
        t, l, d = specs[i]  # type, length, decimals
        if t == 'C':
            l = max(l, df[df.columns[i]].apply(len).max())
            specs[i] = t, l, d

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


def xls_to_dbf(input_file, output_path, output_file_name):
    df = pd.read_excel(input_file)
    output_file = os.path.join(output_path, output_file_name+".dbf")
    dataframe_to_dbf(df, output_file)


def dbf_to_xls(input_file, output_path, output_file_name):
    df = dbf_to_dataframe(input_file)
    df.to_excel(os.path.join(output_path, output_file_name+".xlsx"), index=False)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    input_file = config.dbf_tools.input_file
    output_file_name = config.dbf_tools.output_file_name
    output_path = config.dbf_tools.output_path

    if input_file.endswith('.dbf'):
        dbf_to_xls(input_file=input_file, output_path=output_path, output_file_name=output_file_name)
    elif input_file.endswith('.xls') or input_file.endswith('.xlsx'):
        xls_to_dbf(input_file=input_file, output_path=output_path, output_file_name=output_file_name)
    else:
        print('input file type not supported')

if __name__ == '__main__':
    main(cea.config.Configuration())

