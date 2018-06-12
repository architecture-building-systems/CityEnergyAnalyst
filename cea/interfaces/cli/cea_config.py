"""
Update the user configuration file and show the current settings.
"""

from __future__ import division
from __future__ import print_function

import sys
import cea.config
import cea.inputlocator

from cea.interfaces.cli.cli import get_cli_config, print_script_configuration

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def main(config=None):
    """

    :param cea.config.Configuration config: the configuration file to use (instead of creating a new one)
    :return:
    """
    if not config:
        config = cea.config.Configuration()


    cli_config = get_cli_config()

    # handle arguments
    args = sys.argv[1:]  # drop the script name from the arguments
    if not len(args) or args[0].lower() == '--help':
        print_help()
        sys.exit(1)
    script_name = args.pop(0)
    option_list = cli_config.get('config', script_name).split()
    config.restrict_to(option_list)
    config.apply_command_line_args(args, option_list)

    # save the updates to the configuration file (re-running the same tool will result in the
    # same parameters being set)
    config.save(cea.config.CEA_CONFIG)
    print_script_configuration(config, script_name, option_list)


def print_help():
    """Print out the help message for the ``cea-config`` tool"""
    print("usage: cea-config SCRIPT [OPTIONS]")

if __name__ == '__main__':
    main(cea.config.Configuration())