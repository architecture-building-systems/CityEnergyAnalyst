"""
Create a new conda environment named "cea-{version}". If such an environment already exists,
use that.
Install the current repository into it (``pip install --force-reinstall --no-deps .``)
"""

import json
import os
import subprocess

import cea
import cea.api
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


def main(config):
    """
    Create a new conda environment based on the current cea version.
    """
    repo_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    env_name = "cea-{version}".format(version=cea.__version__)
    if not conda_env_exists(config, env_name):
        conda_env_create(config, env_name, os.path.join(repo_folder, "environment.yml"))

    pip_install(config, repo_folder)


def conda():
    """
    Return the path to the ``conda.bat`` file that will locate the real ``conda.bat`` and activate the base
    environment.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "conda.bat"))


def conda_env_exists(config, env_name):
    """Run ``conda env list`` and figure out if ``env_name`` already exists"""
    command = [conda(), "env", "list", "--json"]
    print("RUN: {command}".format(command=" ".join(command)))
    completed_process = subprocess.run(command, capture_output=True, check=True, env=get_env(config), shell=True)
    stdout = completed_process.stdout.decode()
    # BUGFIX: noticed that stdout contained information after the last "}" character (\x1b[m... stuff)
    stdout = stdout[:stdout.rindex("}") + 1]
    return any(e.endswith(env_name) for e in json.loads(stdout)["envs"])


def get_env(config):
    env = {k: v for k, v in os.environ.items()}
    env["CEA_CONDA_PATH"] = config.development.conda
    return env


def conda_env_create(config, env_name, environment_yml):
    print("CREATE conda environment: {env_name}".format(env_name=env_name))
    command = [conda(), "env", "create", "--name", env_name, "--file", environment_yml]
    print("RUN: {command}".format(command=" ".join(command)))
    completed_process = subprocess.run(command, capture_output=False, check=True, env=get_env(config), shell=True)
    print("DONE")



def pip_install(config, repo_folder):
    pass


if __name__ == '__main__':
    main(cea.config.Configuration())
