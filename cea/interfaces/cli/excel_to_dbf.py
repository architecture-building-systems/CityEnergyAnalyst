"""
Use the py:mod:`cea.utilities.dbfreader` module to convert an excel file to a dbf file.
"""
from __future__ import division

import os
import cea.config
import cea.inputlocator
import cea.utilities.dbfreader


def main(config):
    """
    Convert an Excel file (*.xls) to a DBF file (*.dbf). The configuration uses the section ``dbf-tools`` with
    the parameters ``excel-file`` (path to the input) and ``dbf-file`` (path to the output)

    :param config: uses ``config.dbf_tools.excel_file`` and ``config.dbf_tools.dbf_file``
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.dbf_tools.excel_file), 'Input file not found: %s' % config.dbf_tools.excel_file



    # print out all configuration variables used by this script
    print("Running excel-to-dbf with excel-file = %s" % config.dbf_tools.excel_file)
    print("Running excel-to-dbf with dbf-file = %s" % config.dbf_tools.dbf_file)

    cea.utilities.dbfreader.xls_to_dbf(input_path=config.dbf_tools.excel_file,
                                       output_path=config.dbf_tools.dbf_file)


if __name__ == '__main__':
    main(cea.config.Configuration())
