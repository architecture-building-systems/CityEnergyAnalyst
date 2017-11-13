"""
Use the py:mod:`cea.utilities.dbfreader` module to convert a dbf file to an excel file.
"""
from __future__ import division

import os
import cea.config
import cea.inputlocator
import cea.utilities.dbfreader


def main(config):
    """
    Convert a DBF file (*.dbf) to an Excel file (*.xls). The configuration uses the section ``dbf-tools`` with
    the parameters ``dbf-file`` (path to the output) and ``excel-file`` (path to the input)

    :param config: uses ``config.dbf_tools.excel_file`` and ``config.dbf_tools.dbf_file``
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.dbf_tools.dbf_file), 'Input file not found: %s' % config.dbf_tools.dbf_file



    # print out all configuration variables used by this script
    print("Running excel-to-dbf with dbf-file = %s" % config.dbf_tools.dbf_file)
    print("Running excel-to-dbf with excel-file = %s" % config.dbf_tools.excel_file)

    cea.utilities.dbfreader.dbf_to_xls(input_path=config.dbf_tools.dbf_file,
                                       output_path=config.dbf_tools.excel_file)


if __name__ == '__main__':
    main(cea.config.Configuration())
