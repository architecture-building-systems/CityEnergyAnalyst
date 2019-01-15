"""
Use the py:mod:`cea.utilities.dbf` module to convert an excel file to a dbf file.
"""
from __future__ import division

import os
import cea.config
import cea.inputlocator
import cea.utilities.dbf


def main(config):
    """
    Convert an Excel file (*.xls) to a DBF file (*.dbf). The configuration uses the section ``dbf-tools`` with
    the parameters ``excel-file`` (path to the input) and ``dbf-file`` (path to the output)

    :param config: uses ``config.dbf_tools.excel_file`` and ``config.dbf_tools.dbf_file``
    :type config: cea.config.Configuration
    :return:
    """
    input_file = config.dbf_tools.input_file
    output_file_name = config.dbf_tools.output_file_name
    output_path = config.dbf_tools.output_path

    assert os.path.exists(input_file), 'Input file not found: %s' % input_file

    # print out all configuration variables used by this script
    print("Running excel-to-dbf with excel-file = %s" % input_file)

    cea.utilities.dbf.xls_to_dbf(input_file=input_file, output_path=output_path, output_file_name=output_file_name)


if __name__ == '__main__':
    main(cea.config.Configuration())
