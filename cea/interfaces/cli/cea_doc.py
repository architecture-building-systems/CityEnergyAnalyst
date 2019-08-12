"""
Run documentation scripts
"""

from __future__ import division
from __future__ import print_function

import sys
import datetime
import importlib
import cea.config
import cea.inputlocator
import cea.scripts
from cea import ScriptNotFoundException

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
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
    t0 = datetime.datetime.now()
    if not config:
        config = cea.config.Configuration()

    # handle arguments
    args = sys.argv[1:]  # drop the script name from the arguments
    if not len(args) or args[0].lower() == '--help':
        print_help(config, args[1:])
        sys.exit(1)
    script_name = args.pop(0)
    cea_script = cea.scripts.by_name(script_name)
    if not 'doc' in cea_script.interfaces:
        print('Invalid script for cea-doc')
        print_valid_script_names()
        sys.exit(ScriptNotFoundException.rc)
    config.restrict_to(cea_script.parameters)
    config.apply_command_line_args(args, cea_script.parameters)

    script_module = importlib.import_module(cea_script.module)
    try:
        script_module.main(config)
        print("Execution time: %.2fs" % (datetime.datetime.now() - t0).total_seconds())
    except cea.ConfigError as config_error:
        print('ERROR: %s' % config_error)
        sys.exit(config_error.rc)
    except cea.CustomDatabaseNotFound as error:
        print('ERROR: %s' % error)
        sys.exit(error.rc)
    except:
        raise


def print_help(config, remaining_args):
    """Print out the help message for the ``cea-doc`` command line interface"""
    if remaining_args:
        script_name = remaining_args[0]
        try:
            cea_script = cea.scripts.by_name(script_name)
        except:
            print("Invalid value for SCRIPT.")
            print_valid_script_names()
            return
        script_module = importlib.import_module(cea_script.module)
        print(script_module.__doc__)
        print("")
        print("OPTIONS for %s:" % script_name)
        for _, parameter in config.matching_parameters(cea_script.parameters):
            print("--%s: %s" % (parameter.name, parameter.get()))
            print("    %s" % parameter.help)
            print("    (default: %s)" % parameter.default)
    else:
        print("usage: cea SCRIPT [OPTIONS]")
        print("       to run a specific script")
        print("usage: cea --help SCRIPT")
        print("       to get additional help specific to a script")
        print_valid_script_names()


def print_valid_script_names():
    """Print out the list of scripts by category."""
    import textwrap
    import itertools
    print("")
    print("SCRIPT can be one of:")
    scripts = sorted(cea.scripts.for_interface('doc'), key=lambda s: s.category)
    for category, group in itertools.groupby(scripts, lambda s: s.category):
        print(textwrap.fill("[%s]:  %s" % (category, ', '.join(s.name for s in sorted(group, key=lambda s: s.name))),
                            subsequent_indent='    ', break_on_hyphens=False))


if __name__ == '__main__':
    main(cea.config.Configuration())