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
import Queue
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

# map script to a queue of message to read
messages = {}

# map script name to POpen object
script_process = {}

# map script name to boolean: true, if the script is running, else false
script_running = {}

class Backend(htmlPy.Object):
    """Contains the backend functions, callable from the GUI."""

    def __init__(self, config):
        super(Backend, self).__init__()
        # Initialize the class here, if required.
        self.config = config

    @htmlPy.Slot(str, result=None)
    def log(self, text):
        print(text)

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

    @htmlPy.Slot(str, result=bool)
    def has_output(self, script):
        """True, if there is output available for the script. Output is saved in a Queue in the messages variable"""
        next_line = script_process[script].stdout.readline()
        if next_line:
            messages[script].put(next_line)

        result = not messages.get(script, Queue.Queue()).empty()
        print('has_output: %s' % result)
        return result

    @htmlPy.Slot(str, result=str)
    def next_output(self, script):
        """Return the next line of output for the script. assumes ``has_output`` was true"""
        next_line = messages[script].get()
        print('next_output: %s' + next_line)
        return next_line

    @htmlPy.Slot(str, result=bool)
    def is_script_running(self, script):
        """True, if the script is still running. Else false"""
        if not script in script_process:
            return False
        rc = script_process[script].poll()
        print('is_script_running(%s), rc=%s' % (script, rc))
        result = rc is None
        script_running[script] = result
        return result


def parameters_for_script(script, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    cli_config = cea.interfaces.cli.cli.get_cli_config()
    parameters = [p for s, p in config.matching_parameters(cli_config.get('config', script).split())]
    return parameters


def run_cli(script, **parameters):
    """Run the CLI in a subprocess without showing windows"""
    assert not script_running.get(script, False), 'Script already running %s' % script
    script_running[script] = True
    messages[script] = Queue.Queue()

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [sys.executable, '-u', '-m', 'cea.interfaces.cli.cli', script]
    for parameter_name, parameter_value in parameters.items():
        parameter_name = parameter_name.replace('_', '-')
        command.append('--' + parameter_name)
        command.append(str(parameter_value))
    messages[script].put('Executing: %s\n' % ' '.join(command))

    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=get_environment(), cwd=tempfile.gettempdir())
    script_process[script] = process


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
