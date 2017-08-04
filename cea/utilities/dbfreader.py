from __future__ import print_function

import sys

"""
===========================
DBF and DF file reader
===========================
File history and credits:
C. Miller script development               10.08.14
J. A. Fonseca  adaptation for CEA tool     25.05.16

"""

import pysal
import numpy as np
import pandas as pd
import os


def dataframe_to_dbf(df, dbf_path, specs=None):
    if specs is None:
        type2spec = {int: ('N', 20, 0),
                     np.int64: ('N', 20, 0),
                     float: ('N', 36, 15),
                     np.float64: ('N', 36, 15),
                     unicode: ('C', 25, 0),
                     str: ('C', 25, 0)
                     }
        types = [type(df[i].iloc[0]) for i in df.columns]
        specs = [type2spec[t] for t in types]
    dbf = pysal.open(dbf_path, 'w', 'dbf')
    dbf.header = list(df.columns)
    dbf.field_spec = specs
    df_transpose = df.T
    length = len(df_transpose.columns)
    for row in range(length):
        dbf.write(df_transpose[row])
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
    if not input_path.endswith('.xls'):
        raise ValueError('Excel input file should have *.xls extension')

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
