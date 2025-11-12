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
import shutil
import subprocess
import tarfile

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


def main(config: cea.config.Configuration):
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
    conda_pack(config, env_name, repo_folder)
    extract_tar_file(repo_folder)
    python_setup_py_sdist(config, env_name, repo_folder)
    yarn_package(config, repo_folder)
    make_nsis(config, repo_folder)


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
    env = get_env(config, "base")

    try:
        completed_process = subprocess.run(command, capture_output=True, check=True, env=env, shell=True)
    except subprocess.CalledProcessError as cpe:
        print(cpe.output)
        print(cpe.stderr)
        raise

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
    print("INSTALL mamba")
    command = [conda(), "conda", "install", "mamba", "-c", "conda-forge", "-y"]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, "base"), shell=True)

    print("CREATE conda environment: {env_name}".format(env_name=env_name))
    command = [conda(), "mamba", "env", "create", "--name", env_name, "--file", environment_yml]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, "base"), shell=True)
    print("DONE")


def python_setup_py_sdist(config, env_name, repo_folder):
    print(f"CREATE sdist of CEA: (repo_folder={repo_folder})")
    command = [conda(), "python", "setup.py", "sdist"]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, env_name), shell=True,
                   cwd=repo_folder)
    # collect output and copy to setup/Dependencies
    version = cea.__version__
    shutil.copyfile(os.path.join(repo_folder, "dist", f"cityenergyanalyst-{version}.tar.gz"),
                    os.path.join(repo_folder, "setup", "Dependencies", "cityenergyanalyst.tar.gz"))


def conda_pack(config, env_name, repo_folder):
    print("Make sure conda-pack is installed")
    command = [conda(), "conda", "install", "conda-pack", "-y"]
    print("RUN: {command}".format(command=" ".join(command)))
    subprocess.run(command, capture_output=False, check=True, env=get_env(config, "base"), shell=True)

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


def check_yarn_exists(yarn_location):
    try:
        subprocess.run([yarn_location, "-v"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def yarn_package(config, repo_folder):
    cea_gui_folder = config.development.gui
    if not os.path.exists(os.path.join(cea_gui_folder, "package.json")):
        raise ValueError("Please configure the path to the CityEnergyAnalyst-GUI repository ({development:gui})")
    if not config.development.yarn or not check_yarn_exists(config.development.yarn):
        raise ValueError("Please configure the path to yarn ({development:yarn})")

    print("RUN yarn")
    subprocess.run([config.development.yarn], cwd=cea_gui_folder)
    print("RUN yarn package")
    subprocess.run([config.development.yarn, "package"], cwd=cea_gui_folder, check=True)
    print("COPY CityEnergyAnalyst-GUI-win32-x64 to setup/CityEnergyAnalyst-GUI-win32-x64")
    destination = os.path.join(repo_folder, "setup", "CityEnergyAnalyst-GUI-win32-x64")
    shutil.rmtree(destination, ignore_errors=True, onerror=None)
    shutil.copytree(os.path.join(cea_gui_folder, "out", "CityEnergyAnalyst-GUI-win32-x64"), destination)


def make_nsis(config, repo_folder):
    if not os.path.exists(config.development.nsis):
        raise ValueError("Please configure the path to the makensis.exe ({development:nsis})")
    if not os.path.exists(os.path.join(repo_folder, "setup", "Output")):
        os.mkdir(os.path.join(repo_folder, "setup", "Output"))
    command = [config.development.nsis, os.path.join(repo_folder, "setup", "cityenergyanalyst.nsi")]
    print("RUN {command}".format(command=" ".join(command)))
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main(cea.config.Configuration())
