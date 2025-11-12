"""
Run the CEA scripts and unit tests as part of our CI efforts (cf. The Jenkins)
"""

import os
import unittest

import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.tests.test_workflow import TestWorkflows


def main(config: cea.config.Configuration):
    test_type = config.test.type

    if test_type == "unittest":
        test_suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
        result = unittest.TextTestRunner().run(test_suite)

        if not result.wasSuccessful():
            raise AssertionError("Unittests failed.")

    elif test_type == "integration":
        TestWorkflows()._test_workflows()

    else:
        raise Exception(f"Test type '{test_type}' not supported")


if __name__ == '__main__':
    main(cea.config.Configuration())
