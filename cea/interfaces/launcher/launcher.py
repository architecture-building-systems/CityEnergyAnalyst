"""
Provide a graphical user interface (GUI) to the user for launching CEA scripts.
"""
from __future__ import division
from __future__ import print_function

import os
import sys
import json
import base64
import subprocess
import tempfile
import htmlPy
import cea.config
import cea.interfaces.cli.cli

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Backend(htmlPy.Object):
    """Contains the backend functions, callable from the GUI."""

    def __init__(self, config):
        super(Backend, self).__init__()
        # Initialize the class here, if required.
        self.config = config

    @htmlPy.Slot(str, str, result=None)
    def run_script(self, script, json_data):
        print("Running script: %s" % script)
        values = json.loads(json_data)
        print('json_data: %s' % values)

        parameters = parameters_for_script(script, self.config)
        run_cli(script, **{p.name: p.encode(values[p.name]) for p in parameters})
        return

    @htmlPy.Slot(str, result=str)
    def get_parameters(self, script):
        """Returns a dictionary mapping all parameters for a script to the respective parameter type name"""
        result = json.dumps({p.name: p.typename for p in parameters_for_script(script, self.config)})
        return result


def parameters_for_script(script, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    cli_config = cea.interfaces.cli.cli.get_cli_config()
    parameters = [p for s, p in config.matching_parameters(cli_config.get('config', script).split())]
    return parameters


def add_message(script, message):
    """Append a message to the output div of a script"""
    if len(message) < 1:
        return
    print("%(script)s: %(message)s" % locals())
    message = base64.b64encode(message + '\n')
    app.evaluate_javascript("add_message_js('%(script)s', '%(message)s');" % locals())


def run_cli(script, **parameters):
    """Run the CLI in a subprocess without showing windows"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [sys.executable, '-u', '-m', 'cea.interfaces.cli.cli', script]
    for parameter_name, parameter_value in parameters.items():
        parameter_name = parameter_name.replace('_', '-')
        command.append('--' + parameter_name)
        command.append(str(parameter_value))
    add_message(script, 'Executing: ' + ' '.join(command))
    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=get_environment(), cwd=tempfile.gettempdir())
    while True:
        next_line = process.stdout.readline()
        next_err_line = process.stderr.readline()
        if next_line == '' and next_err_line == '' and process.poll() is not None:
            break
        add_message(script, next_line.rstrip())
        add_message(script, next_err_line.rstrip())
    stdout, stderr = process.communicate()
    add_message(script, stdout)
    add_message(script, stderr)
    if process.returncode != 0:
        raise Exception('Tool did not run successfully')
    add_message(script, script + ' completed.')


def get_environment():
    """Return the system environment to use for the execution - this is based on the location of the python
    interpreter in ``get_python_exe``"""
    root_dir = os.path.dirname(sys.executable)
    scripts_dir = os.path.join(root_dir, 'Scripts')
    env = os.environ.copy()
    env['PATH'] = ';'.join((root_dir, scripts_dir, os.environ['PATH']))
    return os.environ


def main(config):
    """
    Start up the editor to edit the configuration file.

    :param config: the configuration file wrapper object
    :type config: cea.config.Configuration
    :return:
    """
    global app
    app = htmlPy.AppGUI(title=u"CEA Launcher", maximized=False, developer_mode=True)

    app.template_path = os.path.join(BASE_DIR, 'templates')
    app.static_path = os.path.join(BASE_DIR, 'static')

    cli_config = cea.interfaces.cli.cli.get_cli_config()
    scripts = sorted(cli_config.options('scripts'))
    parameters = {script_name: parameters_for_script(script_name, config)
                  for script_name in scripts}

    app.template = ("launcher.html", {"config": config, "scripts": scripts, "parameters": parameters})
    app.bind(Backend(config), variable_name='backend')
    app.start()


if __name__ == '__main__':
    main(cea.config.Configuration())
