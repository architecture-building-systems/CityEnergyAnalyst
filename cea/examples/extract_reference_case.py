"""
Extract the reference case (``cea/examples/reference-case-open.zip``).
"""




import os
import zipfile
import cea.examples
import cea.config
import cea.inputlocator

# list the sections in the configuration file that are used by this script
# this value is used to generate the help menu for the command-line interface
CEA_CONFIG_SECTIONS = ['extract-reference-case']


def main(config: cea.config.Configuration):
    """
    Extract the reference case in ``reference-case-open.zip`` to the destination folder.

    :param config: Contains the PathParameter ``config.extract_reference_case.destination``
    :type config: cea.config.Configuration
    :return:
    """
    reference_case = 'reference-case-{case}.zip'.format(case=config.extract_reference_case.case)
    archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), reference_case))
    archive.extractall(config.extract_reference_case.destination)


if __name__ == '__main__':
    main(cea.config.Configuration())
