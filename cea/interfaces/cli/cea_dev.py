"""
Some scripts to run for development

(will eventually replace ``cea-doc`` as well)

- cea-dev build: This is the one-stop command for creating a new cea release
  - cea/__init__.py:__version__ is the name of the release being created
    - NOTE: maybe add a ``--version`` argument?
    - NOTE: ``cea-dev version 3.10.0a0``
  - update ``CHANGELOG.md`` (prepend new text?)
    - NOTE: ``cea-dev changelog``
  - update ``CREDITS.md`` (I wonder if this should be automated?)
    - NOTE: ``cea-dev credits``
  - build the documentation (``cea-dev rtd``)
  - create a conda environment for the release (named ``cea-{version}``)
  - pip install to that environment, also pip install a list of standard plugins
  - conda-pack the environment
  - copy the environment to the setup/Dependencies/Python folder
  - yarn dist:dir the GUI (expect the repository to be checked out to ``../CityEnergyAnalyst-GUI``)
  - copy the GUI folder to the ``setup/CityEnergyAnalyst-GUI-win32-x64`` folder
  - run ``nsis`` to build the installer

  Bonus steps: (maybe this isn't super necessary?)
  - create a PR for the release with some text
  - create a release on GitHub?
  - update the cityenergyanalyst.com try-cea page?
"""

import sys
import datetime
import importlib
import cea.config
import cea.inputlocator
import cea.scripts
from cea import ScriptNotFoundException

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
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
    cea_script = cea.scripts.by_name(script_name, plugins=config.plugins)
    if 'dev' not in cea_script.interfaces:
        print('Invalid script for cea-dev')
        print_valid_script_names(config.plugins)
        sys.exit(ScriptNotFoundException.rc)
    config.restrict_to(cea_script.parameters)
    config.apply_command_line_args(args, cea_script.parameters)

    # save the updates to the configuration file (re-running the same tool will result in the
    # same parameters being set)
    config.save(cea.config.CEA_CONFIG)

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


def print_help(config, remaining_args):
    """Print out the help message for the ``cea-doc`` command line interface"""
    if remaining_args:
        script_name = remaining_args[0]
        try:
            cea_script = cea.scripts.by_name(script_name, plugins=config.plugins)
        except:
            print("Invalid value for SCRIPT.")
            print_valid_script_names(plugins=config.plugins)
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
        print("usage: cea-dev SCRIPT [OPTIONS]")
        print("       to run a specific script")
        print("usage: cea-dev --help SCRIPT")
        print("       to get additional help specific to a script")
        print_valid_script_names(plugins=config.plugins)


def print_valid_script_names(plugins):
    """Print out the list of scripts by category."""
    import textwrap
    import itertools
    print("")
    print("SCRIPT can be one of:")
    scripts = sorted(cea.scripts.for_interface('dev', plugins=plugins), key=lambda s: s.category)
    for category, group in itertools.groupby(scripts, lambda s: s.category):
        print(textwrap.fill("[%s]:  %s" % (category, ', '.join(s.name for s in sorted(group, key=lambda s: s.name))),
                            subsequent_indent='    ', break_on_hyphens=False))


if __name__ == '__main__':
    main(cea.config.Configuration())
