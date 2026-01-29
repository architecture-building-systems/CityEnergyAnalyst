import os
import sys
import subprocess

__author__ = "Xiaoyu Wang"
__copyright__ = ["Copyright 2025, Architecture and Building Systems - ETH Zurich"], \
    ["Copyright 2025, College of Architecture and Urban Planning (CAUP) - Tongji University"]
__credits__ = ["Xiaoyu Wang"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = [""]
__email__ = ["cea@arch.ethz.ch", "wanglittlerain@163.com"]
__status__ = "Production"

from cea.resources.utils import get_radiation_bin_path

# Define the list of required CRAX executables (without extension)
REQUIRED_CRAX_BINARIES = [
    "radiation", "mesh-generation"
]


class CRAX:
    """
    A class to execute the CRAX model workflow. It can run one or more of the following stages:
      1. mesh-generation.exe (or Linux equivalent) to generate mesh files.
      2. radiation.exe (or Linux equivalent) to compute radiation values.
      3. write-radiation-results.exe (or Linux equivalent) to output the radiation results.

    The outputs are handled internally by the executables.
    """

    def __init__(self, crax_exe_dir: str):
        """
        Initialize the CRAXModel.
        :param crax_exe_dir: Directory where the CRAX executables are located.
        """
        self.crax_exe_dir = crax_exe_dir
        self.is_windows = sys.platform == "win32"
        self.is_mac = sys.platform == "darwin"

    def run_mesh_generation(self, json_file: str):
        """
        Execute the mesh-generation executable with a JSON input file.

        :param json_file: The full path to the JSON file to be used as input.
        """
        exe_name = "mesh-generation.exe" if self.is_windows else "mesh-generation"
        exe_dir = self.crax_exe_dir  # Directory containing both radiation.exe and arrow.dll

        env = os.environ.copy()

        # Command to run the exe
        cmd = [os.path.join(exe_dir, exe_name), json_file]

        # Run the command with cwd set to exe_dir and using the modified env
        try:
            result = subprocess.run(cmd, capture_output=True, env=env, cwd=exe_dir, text=True)
            result.check_returncode()  # This will raise an error if the command failed
            print(result.stdout)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running mesh-generation (exited with code {e.returncode}):\n{e.stderr}")

    def run_radiation(self, json_file: str):
        """
        Execute the radiation executable with a JSON input file.

        Tries to load the required shared arrow library from conda environment if available.

        On Windows, the command is prefixed with a PATH assignment so that the folder
        containing arrow.dll (i.e. self.crax_exe_dir) is included in the environment for
        the execution of the command.

        :param json_file: The full path to the JSON file to be used as input.
        :return: The output from the radiation executable.
        """
        exe_name = "radiation.exe" if self.is_windows else "radiation"
        exe_dir = self.crax_exe_dir  # Directory containing both radiation.exe and arrow.dll

        # Setting dynamic library paths is required for CRAX to find its dependencies in python env e.g. arrow
        env = os.environ.copy()
        python_prefix = sys.prefix
        if self.is_windows:
            lib_path = os.path.join(python_prefix, 'Library', 'bin')
            env["PATH"] = f"{lib_path};{env['PATH']}"
        elif self.is_mac:
            lib_path = os.path.join(python_prefix, 'lib')
            env["DYLD_LIBRARY_PATH"] = f"{lib_path}:{env.get('DYLD_LIBRARY_PATH', '')}"
        else:
            lib_path = os.path.join(python_prefix, 'lib')
            env["LD_LIBRARY_PATH"] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}"
        
        # Command to run the exe
        cmd = [os.path.join(exe_dir, exe_name), json_file]

        # Run the command with cwd set to exe_dir and using the modified env
        try:
            result = subprocess.run(cmd, capture_output=True, env=env, cwd=exe_dir, text=True)
            result.check_returncode()  # This will raise an error if the command failed
            print(result.stdout)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running radiation (exited with code {e.returncode}):\n{e.stderr}")


def check_crax_exe_directory() -> str:
    """
    Check the directory for required CRAX executables and return the path to the binaries.
    If the required executables are not found, a ValueError is raised.

    Checks the external tools package (cea_external_tools) for binaries.

    :return: Path to the directory containing CRAX executables.
    """
    print("Platform:", sys.platform)

    def contains_binaries(path: str) -> bool:
        """Check if the required binaries exist in the given path."""
        try:
            files = set(os.listdir(path))
        except OSError:
            return False

        for binary in REQUIRED_CRAX_BINARIES:
            expected = binary + (".exe" if sys.platform == "win32" else "")
            if expected not in files:
                return False
        return True

    # Check external tools package location (where binaries are installed)
    external_tools_path = get_radiation_bin_path()
    if external_tools_path:
        bin_path = os.path.abspath(os.path.normpath(external_tools_path))

        if os.path.isdir(bin_path) and contains_binaries(bin_path):
            print(f"Found CRAX executables in: {bin_path}")
            return bin_path

        # Check 'bin' subdirectory if the main directory doesn't contain the binaries
        sub_bin = os.path.join(bin_path, "bin")
        if os.path.isdir(sub_bin) and contains_binaries(sub_bin):
            print(f"Found CRAX executables in subfolder: {sub_bin}")
            return sub_bin

    raise ValueError("Could not find CRAX executables. Please install cea-external-tools package.")
