"""
A collection of utility functions for working with ``*.DBF`` (dBase database) files.
"""

import numpy as np
import pandas as pd
import os
import cea.config
import pysal.lib
# import PySAL without the warning
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


__author__ = "Clayton Miller, Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Clayton Miller", "Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

TYPE_MAPPING = {
    int: ('N', 20, 0),
    np.int32: ('N', 20, 0),
    np.int64: ('N', 20, 0),
    float: ('N', 36, 15),
    np.float64: ('N', 36, 15),
    str: ('C', 25, 0),
    np.bool_: ('L', 1, 0)}


def dataframe_to_dbf(df, dbf_path, specs=None):
    """Given a pandas Dataframe, write a dbase database to ``dbf_path``.

    :type df: pandas.Dataframe
    :type dbf_path: str
    :param specs: A list of column specifications for the dbase table. Each column is specified by a tuple (datatype,
        size, decimal) - we support ``datatype in ('N', 'C')`` for strings, integers and floating point numbers, if
        no specs are provided (see ``TYPE_MAPPING``)
    :type specs: list[tuple(str, int, int)]
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

    dbf = pysal.lib.io.open(dbf_path, 'w', 'dbf')
    dbf.header = list(df.columns)
    dbf.field_spec = specs
    for row in range(len(df)):
        dbf.write(df.iloc[row])
    dbf.close()
    return dbf_path


def dbf_to_dataframe(dbf_path, index=None, cols=None, include_index=False):
    dbf = pysal.lib.io.open(dbf_path)
    if cols:
        if include_index:
            cols.append(index)
        vars_to_read = cols
    else:
        vars_to_read = dbf.header
    data = dict([(var, dbf.by_col(var)) for var in vars_to_read])
    if index:
        index = dbf.by_col(index)
        dbf.close()
        return pd.DataFrame(data, index=index)
    else:
        dbf.close()
        return pd.DataFrame(data)


def csv_xlsx_to_dbf(input_file, output_path, output_file_name):
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file, sep=None)
    if input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file)
    output_file = os.path.join(output_path, output_file_name)
    dataframe_to_dbf(df, output_file)


def dbf_to_csv_xlsx(input_file, output_path, output_file_name):
    df = dbf_to_dataframe(input_file)
    if output_file_name.endswith('.csv'):
        df.to_csv(os.path.join(output_path, output_file_name), index=False)
    if output_file_name.endswith('.xlsx'):
        df.to_excel(os.path.join(output_path, output_file_name), index=False)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    input_file = config.dbf_tools.input_file
    output_file_name = config.dbf_tools.output_file_name
    output_path = config.dbf_tools.output_path

    if input_file.endswith('.dbf'):
        dbf_to_csv_xlsx(input_file=input_file, output_path=output_path, output_file_name=output_file_name)
    elif input_file.endswith('.csv') or input_file.endswith('.xlsx'):
        csv_xlsx_to_dbf(input_file=input_file, output_path=output_path, output_file_name=output_file_name)
    else:
        raise ValueError("""Input file type is not supported. Only .dbf, .csv and .xlsx file types are supported.""")


if __name__ == '__main__':
    main(cea.config.Configuration())
