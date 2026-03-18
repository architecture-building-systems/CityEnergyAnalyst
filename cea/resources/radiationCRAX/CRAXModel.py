import os
import sys
import subprocess
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

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

WINDOWS_RUNTIME_DLL_PATTERNS = (
    "arrow*.dll",
    "libprotobuf*.dll",
    "libzstd.dll",
    "msvcp140*.dll",
    "parquet.dll",
    "snappy.dll",
    "vcomp140.dll",
    "vcruntime140*.dll",
    "zstd.dll",
)


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

    @staticmethod
    def _get_runtime_search_paths() -> list[Path]:
        python_prefix = Path(sys.prefix)
        return [python_prefix, python_prefix / "Library" / "bin"]

    @staticmethod
    def _get_runtime_root() -> Path:
        override = os.environ.get("CEA_CRAX_RUNTIME_DIR")
        if override:
            return Path(override)

        if sys.platform == "win32":
            app_data = os.environ.get("APPDATA")
            if not app_data:
                app_data = str(Path.home() / "AppData" / "Roaming")
            return Path(app_data) / "CityEnergyAnalyst" / "crax-runtime"

        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "CityEnergyAnalyst" / "crax-runtime"

        return Path.home() / ".local" / "share" / "CityEnergyAnalyst" / "crax-runtime"

    def _copy_runtime_files(self, runtime_dir: Path):
        """Stage local DLLs so Windows prefers the Pixi runtime over System32."""
        seen: set[str] = set()

        for source_dir in self._get_runtime_search_paths():
            if not source_dir.is_dir():
                continue

            for pattern in WINDOWS_RUNTIME_DLL_PATTERNS:
                for source in source_dir.glob(pattern):
                    key = source.name.lower()
                    if key in seen:
                        continue

                    shutil.copy2(source, runtime_dir / source.name)
                    seen.add(key)

    @contextmanager
    def _get_execution_context(self, exe_name: str) -> Iterator[tuple[str, str, dict[str, str]]]:
        exe_dir = Path(self.crax_exe_dir)
        exe_path = exe_dir / exe_name
        env = os.environ.copy()

        if self.is_windows:
            runtime_root = self._get_runtime_root()
            runtime_root.mkdir(parents=True, exist_ok=True)
            runtime_dir = runtime_root / f"cea_crax_runtime_{uuid.uuid4().hex}"
            runtime_dir.mkdir()
            try:
                shutil.copy2(exe_path, runtime_dir / exe_name)
                self._copy_runtime_files(runtime_dir)
                yield str(runtime_dir / exe_name), str(runtime_dir), env
            finally:
                shutil.rmtree(runtime_dir, ignore_errors=True)
            return

        python_prefix = Path(sys.prefix)
        if self.is_mac:
            lib_path = python_prefix / "lib"
            env["DYLD_LIBRARY_PATH"] = f"{lib_path}:{env.get('DYLD_LIBRARY_PATH', '')}"
        else:
            lib_path = python_prefix / "lib"
            env["LD_LIBRARY_PATH"] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}"

        yield str(exe_path), str(exe_dir), env

    def run_mesh_generation(self, json_file: str):
        """
        Execute the mesh-generation executable with a JSON input file.

        :param json_file: The full path to the JSON file to be used as input.
        """
        exe_name = "mesh-generation.exe" if self.is_windows else "mesh-generation"

        with self._get_execution_context(exe_name) as (exe_path, working_dir, env):
            cmd = [exe_path, json_file]

            try:
                result = subprocess.run(cmd, capture_output=True, env=env, cwd=working_dir, text=True)
                result.check_returncode()  # This will raise an error if the command failed
                print(result.stdout)
                return result.stdout
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or e.stdout
                raise RuntimeError(
                    f"Error running mesh-generation (exited with code {e.returncode}):\n{error_output}"
                )

    def run_radiation(self, json_file: str):
        """
        Execute the radiation executable with a JSON input file.

        On Windows, stage the executable beside the Pixi runtime DLLs so the bundled
        C/C++ runtime is preferred over incompatible System32 copies.

        :param json_file: The full path to the JSON file to be used as input.
        :return: The output from the radiation executable.
        """
        exe_name = "radiation.exe" if self.is_windows else "radiation"

        with self._get_execution_context(exe_name) as (exe_path, working_dir, env):
            cmd = [exe_path, json_file]

            try:
                result = subprocess.run(cmd, capture_output=True, env=env, cwd=working_dir, text=True)
                result.check_returncode()  # This will raise an error if the command failed
                print(result.stdout)
                return result.stdout
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or e.stdout
                raise RuntimeError(f"Error running radiation (exited with code {e.returncode}):\n{error_output}")


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
