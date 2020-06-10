"""
Run all the unit tests in the cea/tests folder
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import unittest
import cea.config
import cea.workflows.workflow

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(_):
    test_suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
    result = unittest.TextTestRunner(verbosity=1).run(test_suite)

    if not result.wasSuccessful():
        raise AssertionError("Unittests failed.")


if __name__ == "__main__":
    main(cea.config.Configuration)