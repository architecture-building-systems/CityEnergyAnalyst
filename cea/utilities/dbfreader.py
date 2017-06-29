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

def df2dbf(df, dbf_path, my_specs=None):

    if my_specs:
        specs = my_specs
    else:
        type2spec = {int: ('N', 20, 0),
                     np.int64: ('N', 20, 0),
                     float: ('N', 36, 15),
                     np.float64: ('N', 36, 15),
                     unicode: ('C', 25, 0),
                     str: ('C', 25, 0)
                     }
        types = [type(df[i].iloc[0]) for i in df.columns]
        specs = [type2spec[t] for t in types]
    db = pysal.open(dbf_path, 'w', 'dbf')
    db.header = list(df.columns)
    db.field_spec = specs
    df_transpose = df.T
    length = len(df_transpose.columns)
    for row in range(length):
        db.write(df_transpose[row])
    db.close()
    return dbf_path

def dbf2df(dbf_path, index=None, cols=False, incl_index=False):
    db = pysal.open(dbf_path)
    if cols:
        if incl_index:
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


def xls_dbf_xls(input_path,output_path):
    if input_path.endswith('.xls'):     # check if the extension of the input is xls
        df=pd.read_excel(input_path)
        df2dbf(df,output_path)
    elif input_path.endswith('.dbf'):   # check if the extension of the input is dbf
        df=dbf2df(input_path)
        df.to_excel(output_path)
    else:
        print 'input file type not supported'

def run_as_script(parameters):
    input_path=parameters[0]
    output_path=parameters[1]
    xls_dbf_xls(input_path=input_path, output_path=output_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('parameters')
    args = parser.parse_args()
    run_as_script(parameters=args.parameters)