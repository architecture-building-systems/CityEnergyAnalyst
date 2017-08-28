"""
Functions for Report generation
"""

import pandas as pd
import datetime
import os

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def full_report_to_xls(tsd, output_folder, basename, gv):
    """ this function is to write a full report to an ``*.xls`` file containing all intermediate and final results of a
    single building thermal loads calculation"""

    df = pd.DataFrame(tsd)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    #timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #output_path = os.path.join(output_folder,"%(basename)s-%(timestamp)s.xls" % locals())
    output_path = os.path.join(output_folder, "%(basename)s.xls" % locals())
    writer = pd.ExcelWriter(output_path, engine='xlwt')

    df.to_excel(writer, na_rep='NaN')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    writer.close()
