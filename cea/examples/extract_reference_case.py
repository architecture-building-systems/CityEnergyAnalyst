"""
Extract the reference case (``cea/examples/reference-case-open.zip``).
"""
from __future__ import division

import os
import zipfile
import cea.examples
import cea.config
import cea.inputlocator

# list the sections in the configuration file that are used by this script
# this value is used to generate the help menu for the command-line interface
CEA_CONFIG_SECTIONS = ['extract-reference-case']


def main(config):
    """
    Extract the reference case in ``reference-case-open.zip`` to the destination folder.

    :param config: Contains the PathParameter ``config.extract_reference_case.destination``
    :type config: cea.config.Configuration
    :return:
    """
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running extract-reference-case with destination =  %s" % config.extract_reference_case.destination)

    archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
    archive.extractall(config.extract_reference_case.destination)


if __name__ == '__main__':
    main(cea.config.Configuration())
