"""
Build a new CEA installer for the current version. This script runs a bunch of commands necessary to create a new
CEA installer - it will run a long time. It _expects_ to be run in a development version of CEA (i.e. ``pip install -e``
was used to install cityenergyanalyst from the repo.

- create a conda environment for the version (unless already exists, then use that)
    - install cea to that environment
    - (bonus points: install a default list of cea plugins)
- conda-pack that environment to the setup Dependencies folder
- yarn dist:dir the GUI
"""
import json
import os
import subprocess
import tarfile

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
    Create a new conda environment based on the current cea version. install cea into it, conda-pack it
    and place it in the setup/Dependencies/Python folder ready for the installer to compress.
    """
    repo_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    env_name = "cea-{version}".format(version=cea.__version__)
    if not conda_env_exists(config, env_name):
        conda_env_create(config, env_name, os.path.join(repo_folder, "environment.yml"))
    else:
        print("NOTE: Using existing conda environment {env_name}".format(env_name=env_name))
    pip_install(config, env_name, repo_folder)
    conda_pack(config, env_name, repo_folder)
    extract_tar_file(repo_folder)


def conda():
    """
    Return the path to the ``conda.bat`` file that will locate the real ``conda.bat`` and activate the base
    environment.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "conda.bat"))


def conda_env_exists(config, env_name):
    """Run ``conda env list`` and figure out if ``env_name`` already exists"""
    command = [conda(), "conda", "env", "list", "--json"]
    print("RUN: {command}".format(command=" ".join(command)))
    env = get_env(config, env_name)
    completed_process = subprocess.run(command, capture_output=True, check=True, env=env, shell=True)
    stdout = completed_process.stdout.decode()
    # BUGFIX: noticed that stdout contained information after the last "}" character (\x1b[m... stuff)
    stdout = stdout[:stdout.rindex("}") + 1]
    try:
        env_names = json.loads(stdout)["envs"]
        return any(e.endswith(env_name) for e in env_names)
    except json.decoder.JSONDecodeError:
        print("----")
        print(stdout)
        print("----")
        raise


def get_env(config, conda_env):
    env = {k: v for k, v in os.environ.items()}
    env["CEA_CONDA_PATH"] = config.development.conda
    env["CEA_CONDA_ENV"] = conda_env
    return env


def conda_env_create(config, env_name, environment_yml):
    print("CREATE conda environment: {env_name}".format(env_name=env_name))
    command = [conda(), "conda", "env", "create", "--name", env_name, "--file", environment_yml]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, "base"), shell=True)
    print("DONE")


def pip_install(config, env_name, repo_folder):
    print("INSTALL cea to conda environment: {env_name} (repo={repo})".format(env_name=env_name, repo=repo_folder))
    command = [conda(), "pip", "install", "--force-reinstall", "--no-deps", repo_folder]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, env_name), shell=True)


def conda_pack(config, env_name, repo_folder):
    print("CONDA-PACK to Dependencies folder: {env_name}".format(env_name=env_name))
    output_path = os.path.join(repo_folder, "setup", "Dependencies", "Python.tar")
    command = [conda(), "conda-pack", "--name", env_name, "--output", output_path, "--n-threads", "-1", "--force"]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, "base"), shell=True)


def extract_tar_file(repo_folder):
    python_tar = os.path.join(repo_folder, "setup", "Dependencies", "Python.tar")
    print(f"EXTRACT tar file {python_tar}")
    tf = tarfile.open(python_tar, "r")
    try:
        tf.extractall(os.path.join(repo_folder, "setup", "Dependencies", "Python"))
    finally:
        tf.close()
    os.unlink(python_tar)


if __name__ == '__main__':
    main(cea.config.Configuration())