"""
This file implements the ``cea`` command line interface script. Basically, it uses the first argument passed to
it to look up a module to import in ``cli.config``, imports that and then calls the ``main`` function on that module.

The rest of the command line arguments are passed to the ``cea.config.Configuration`` object for processing.
"""

import sys
import os
import importlib
import ConfigParser
import cea.config



def main(config=None):
    if not config:
        config = cea.config.Configuration()

    cli_config = get_cli_config()

    # handle arguments
    args = sys.argv[1:]  # drop the script name from the arguments
    if not len(args) or args[0].lower() == '--help':
        print_help(config, cli_config, args[1:])
        sys.exit(1)
    script_name = args.pop(0)
    option_list = cli_config.get('config', script_name).split()
    config.apply_command_line_args(args, option_list)

    # save the updates to the configuration file (re-running the same tool will result in the
    # same parameters being set)
    config.save(cea.config.CEA_CONFIG)

    print_script_configuration(config, script_name, option_list)

    module_path = cli_config.get('scripts', script_name)
    script_module = importlib.import_module(module_path)
    try:
        script_module.main(config)
    except cea.ConfigError as config_error:
        print('ERROR: %s' % config_error)
        sys.exit(config_error.rc)
    except:
        raise


def print_script_configuration(config, script_name, option_list):
    """
    Print a list of script parameters being used for this run of the tool. Historically, each tool
    was responsible for printing their own parameters, but that requires manually keeping track of these
    parameters.
    """
    print("Running `cea %(script_name)s` with the following parameters:" % locals())
    for section, parameter in config.matching_parameters(option_list):
        section_name = section.name
        parameter_name = parameter.name
        parameter_value = parameter.get()
        print("- %(section_name)s:%(parameter_name)s = %(parameter_value)s" % locals())

def get_cli_config():
    """Return a ConfigParser object for the ``cli.config`` file used to configure the scripts known to the
    ``cea`` command line interface and the parameters accepted by each script"""

    cli_config = ConfigParser.SafeConfigParser()
    cli_config.read(os.path.join(os.path.dirname(__file__), 'cli.config'))
    return cli_config


def print_help(config, cli_config, remaining_args):
    """Print out the help message for the ``cea`` command line interface"""
    if remaining_args:
        script_name = remaining_args[0]
        try:
            module_path = cli_config.get('scripts', script_name)
            option_list = cli_config.get('config', script_name).split()
        except:
            print("Invalid value for SCRIPT.")
            print_valid_script_names(cli_config)
            return
        script_module = importlib.import_module(module_path)
        print(script_module.__doc__)
        print("")
        print("OPTIONS for %s:" % script_name)
        for _, parameter in config.matching_parameters(option_list):
            print("--%s: %s" % (parameter.name, parameter.get()))
            print("    %s" % parameter.help)
    else:
        print("usage: cea SCRIPT [OPTIONS]")
        print("       to run a specific script")
        print("usage: cea --help SCRIPT")
        print("       to get additional help specific to a script")
        print_valid_script_names(cli_config)


def print_valid_script_names(cli_config):
    import textwrap
    print("")
    print(textwrap.fill("SCRIPT can be one of: %s" % ', '.join(sorted(cli_config.options('scripts'))),
                        subsequent_indent='    ', break_on_hyphens=False))


if __name__ == '__main__':
    main(cea.config.Configuration())