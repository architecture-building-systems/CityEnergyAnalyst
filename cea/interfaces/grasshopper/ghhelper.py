"""
A library of helper-functions for working with the CEA from grasshopper. Install this with ``cea install-grasshopper``.

The main function used is ``run`` which runs a CEA script (as defined in the ``cli.config``)

.. note:: This module is meant to be run from grasshopper, which uses an IronPython interpreter. PyCharm will have a
    hard time with some of the imports here.
"""

import subprocess
import os
import tempfile
import ConfigParser

import cea.config

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# IronPython doesn't define this?
subprocess.STARTF_USESHOWWINDOW = 1


def run(script, args):
    """Run a script, given a config file.

    :param script: a script name, as defined in the ``cli.config`` file
    :type script: basestring

    :param args: a dictionary consisting of ``name = value`` pairs, one per line, for each parameter to override
        the value should be formatted as it would be in the config file.
    :type args: dict[str, str]
    """
    config = cea.config.Configuration()
    parameters = {}
    for p in get_parameters(script, config):
        if p.name in args:
            parameters[p.name] = args[p.name]
        else:
            parameters[p.name] = p.encode(p.get())

    run_cli(script, **parameters)


def run_cli(script_name, **parameters):
    """Run the CLI in a subprocess without showing windows"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-u', '-m', 'cea.interfaces.cli.cli', script_name]
    for parameter_name, parameter_value in parameters.items():
        parameter_name = parameter_name.replace('_', '-')
        command.append('--' + parameter_name)
        command.append(str(parameter_value))
    print('Executing: ' + ' '.join(command))
    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=tempfile.gettempdir())
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        print(next_line.rstrip())
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)
    if process.returncode != 0:
        raise Exception('Tool did not run successfully')


def get_parameters(cea_tool, config):
    """Return a list of cea.config.Parameter objects for each parameter associated with the tool."""
    cli_config = ConfigParser.SafeConfigParser()
    cli_config.read(os.path.join(os.path.dirname(__file__), '..', 'cli', 'cli.config'))
    option_list = cli_config.get('config', cea_tool).split()
    for _, parameter in config.matching_parameters(option_list):
        yield parameter


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
            return python_exe
    except:
        raise AssertionError("Could not find 'cea_python.pth' in home directory.")