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

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def full_report_to_xls(template, variables, output_folder, basename, gv):
    """ this function is to write a full report to an *.xls file containing all intermediate and final results of a
    single building thermal loads calculation"""

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
        # log missing variables
        missing_variables = [v for v in report_template[sheet] if v not in variables]
        # try to add them from the `tds` variable:
        if 'tsd' in variables:
            for key in missing_variables:
                if key in variables['tsd'].keys():
                    variables[key] = variables['tsd'][key]
        missing_variables = [v for v in report_template[sheet] if v not in variables]
        if missing_variables:
            gv.log("cannot report following variables: %s" % ', '.join(missing_variables))

        df = pd.DataFrame({v: variables[v] for v in report_template[sheet] if v in variables},
                          index=pd.date_range(gv.date_start, periods=8760, freq='H'))
        # write data frames to excel work sheet
        df.to_excel(writer, sheet_name=sheet, na_rep='NaN')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    writer.close()
