"""
Create a schemas.yml-compatible entry given a locator method by reading the file from the current scenario.
"""

from __future__ import division
from __future__ import print_function

import os
import yaml
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


def read_schema(scenario, locator_method, args=None):
    if not args:
        args = {}
    absolute_path = read_path(args, locator_method, scenario)

    return {
        locator_method: {
            "file_path": read_file_path(absolute_path, scenario, args),
        }
    }


def read_path(args, locator_method, scenario):
    """Return the path, as returned by the locator method"""
    locator = cea.inputlocator.InputLocator(scenario=scenario)
    method = getattr(locator, locator_method)
    path = method(**args)
    return path


def read_file_path(absolute_path, scenario, args):
    """
    returns the path relative to scenario, with arguments replaced. This assumes that the values in args
    were substituted. this ends up in the "file_path" key in the schema
    """
    file_path = os.path.relpath(absolute_path, scenario)
    for k, v in args.items():
        if v in file_path:
            file_path = file_path.replace(v, "{%s}" % k.replace("_", "-"))
    return file_path


def main(config):
    """
    Read the schema entry for a locator method, compare it to the current entry and print out a new, updated version.
    """
    print(yaml.safe_dump(read_schema(config.scenario, config.schemas.locator_method, config.schemas.args), default_flow_style=False))


if __name__ == '__main__':
    main(cea.config.Configuration())
