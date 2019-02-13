"""
This file implements the ``cea`` command line interface script. Basically, it uses the first argument passed to
it to look up a module to import in ``scripts.yml``, imports that and then calls the ``main`` function on that module.

The rest of the command line arguments are passed to the ``cea.config.Configuration`` object for processing.
"""

import sys
import os
import importlib
import datetime
import ConfigParser
import cea.config
import cea.scripts
import cea.datamanagement.copy_default_databases


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
    config.restrict_to(cea_script.parameters)
    config.apply_command_line_args(args, cea_script.parameters)

    # save the updates to the configuration file (re-running the same tool will result in the
    # same parameters being set)
    config.save(cea.config.CEA_CONFIG)

    cea_script.print_script_configuration(config)

    # FIXME: remove this after Executive Course
    # <--
    config.restrict_to(['general:scenario', 'general:region'] + cea_script.parameters)
    cea.datamanagement.copy_default_databases.copy_default_databases(
        locator=cea.inputlocator.InputLocator(config.scenario), region=config.region)
    config.restrict_to(cea_script.parameters)
    # -->

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
    """Print out the help message for the ``cea`` command line interface"""
    if remaining_args:
        default_config = cea.config.Configuration(config_file=cea.config.DEFAULT_CONFIG)
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
            print("    (default: %s)" % default_config.get(parameter.fqname))
    else:
        print("usage: cea SCRIPT [OPTIONS]")
        print("       to run a specific script")
        print("usage: cea --help SCRIPT")
        print("       to get additional help specific to a script")
        print_valid_script_names()


def print_valid_script_names():
    import textwrap
    print("")
    print(textwrap.fill("SCRIPT can be one of: %s" % ', '.join(s.name for s in sorted(cea.scripts.for_interface('cli'))),
                        subsequent_indent='    ', break_on_hyphens=False))


if __name__ == '__main__':
    main(cea.config.Configuration())