"""
Update the user configuration file and show the current settings.
"""

import sys

import cea.config
import cea.scripts
from cea.plugin import instantiate_plugin
from cea.utilities import parse_string_to_list

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(args=None):
    """
    :param List[str] args: the arguments to use - when not running from the command line, for testing.
    :return:
    """
    if args is None:
        args = sys.argv[1:]  # drop the script name from the arguments

    config = cea.config.Configuration()

    # handle arguments
    if not len(args) or args[0].lower() == '--help':
        print_help()
        sys.exit(1)
    script_name = args.pop(0)
    if script_name == "write":
        for fqname, value in cea.config.parse_command_line_args(args).items():
            parameter = config.get_parameter(fqname)
            parameter.set(parameter.decode(parameter.replace_references(value)))
    elif script_name == "read":
        for fqname in args:
            parameter = config.get_parameter(fqname)
            print("- {fqname} = {parameter_value}".format(fqname=fqname, parameter_value = parameter.get()))
            print("  (default: {default})".format(default=parameter.default))
    elif script_name == "add-plugins":
        plugins_fqname = "general:plugins"
        parameter = config.get_parameter(plugins_fqname)
        plugins = parse_string_to_list(parameter.encode(parameter.get()))

        new_plugins = [p for p in args if p not in plugins]  # filter existing plugins
        valid_plugins = [p for p in new_plugins if instantiate_plugin(p) is not None]

        if valid_plugins:
            print(f"Adding valid plugins {','.join(valid_plugins)}")
            plugins.extend(valid_plugins)
            parameter.set(plugins)
        else:
            print('No plugins to add')

    else:
        cea_script = cea.scripts.by_name(script_name, plugins=config.plugins)
        config.restrict_to(cea_script.parameters)
        config.apply_command_line_args(args, cea_script.parameters)
        cea_script.print_script_configuration(config, verb='Configuring')

    # save the updates to the configuration file (re-running the same tool will result in the
    # same parameters being set)
    config.save(cea.config.CEA_CONFIG)


def print_help():
    """Print out the help message for the ``cea-config`` tool"""
    print("usage: cea-config SCRIPT [OPTIONS]")


if __name__ == '__main__':
    main(args=["write", "--general:plugins", "cea_plugin_template.DemandSummaryPlugin"])