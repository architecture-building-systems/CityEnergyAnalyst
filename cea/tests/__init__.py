"""
Run the CEA unit tests and integration tests.
"""

import os
import cea.config
from cea.tests.test_workflow import TestWorkflows

try:
    import pytest
except ImportError:
    raise ImportError("The 'pytest' package is required to run the CEA tests. Please install it via 'pip install pytest'.")

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config: cea.config.Configuration):
    test_type = config.test.type

    if test_type == "unittest":
        exit_code = pytest.main([os.path.dirname(__file__)])
        if exit_code != 0:
            raise AssertionError("Tests failed.")

    elif test_type == "integration":
        TestWorkflows()._test_workflows()

    else:
        raise Exception(f"Test type '{test_type}' not supported")


if __name__ == '__main__':
    main(cea.config.Configuration())
