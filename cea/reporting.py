"""
===============================
Functions for Report generation
===============================
File history and credits:
G. Happle   ... 13.05.2016
D. Thomas, 18.05.2016: refactoring
"""

import pandas as pd
import datetime
import xlwt
import os


def full_report_to_xls(template, variables, output_folder, basename, gv):

    """ this function is to write a full report to an *.xls file containing all intermediate and final results of a
    single building thermal loads calculation"""

    # TODO: get names of used functions from glovalvars for report
    # TODO: write units to column names
    # TODO: split outputs into more work sheets, e.g. one for water, electricity, etc

    # get variables from local
    report_template = gv.report_variables[template]

    # create excel work book and work sheets
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    output_path = os.path.join(output_folder, "%(basename)s-%(timestamp)s.xls" % locals())
    wb = xlwt.Workbook()
    for sheet in report_template.keys():
        wb.add_sheet(sheet)
    wb.save(output_path)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(output_path, engine='xlwt')

    # create data frames
    for sheet in report_template.keys():
        df = pd.DataFrame({v: variables[v] for v in report_template[sheet]})
        # write data frames to excel work sheet
        df.to_excel(writer, sheet_name=sheet, na_rep='NaN')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    writer.close()
