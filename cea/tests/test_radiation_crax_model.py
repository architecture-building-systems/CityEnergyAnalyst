import os
import shutil
from pathlib import Path

from cea.resources.radiationCRAX.CRAXModel import CRAX


def test_get_execution_context_stages_windows_runtime_dlls(monkeypatch):
    workspace_tmp = Path(os.getcwd()) / "tmp"
    workspace_tmp.mkdir(exist_ok=True)
    test_root = workspace_tmp / "crax_model_test"
    shutil.rmtree(test_root, ignore_errors=True)
    test_root.mkdir()

    try:
        exe_dir = test_root / "bin"
        exe_dir.mkdir()
        (exe_dir / "mesh-generation.exe").write_text("exe", encoding="utf-8")

        prefix_dir = test_root / "prefix"
        library_bin_dir = prefix_dir / "Library" / "bin"
        library_bin_dir.mkdir(parents=True)

        (prefix_dir / "msvcp140.dll").write_text("msvcp", encoding="utf-8")
        (library_bin_dir / "arrow.dll").write_text("arrow", encoding="utf-8")
        (library_bin_dir / "vcomp140.dll").write_text("vcomp", encoding="utf-8")

        monkeypatch.setattr("cea.resources.radiationCRAX.CRAXModel.sys.prefix", str(prefix_dir))
        monkeypatch.setattr(
            "cea.resources.radiationCRAX.CRAXModel.CRAX._get_runtime_root",
            staticmethod(lambda: test_root / "runtime-root"),
        )

        model = CRAX(str(exe_dir))
        model.is_windows = True
        model.is_mac = False

        with model._get_execution_context("mesh-generation.exe") as (exe_path, working_dir, _env):
            runtime_dir = Path(working_dir)
            assert runtime_dir == Path(exe_path).parent
            assert (runtime_dir / "mesh-generation.exe").exists()
            assert (runtime_dir / "msvcp140.dll").exists()
            assert (runtime_dir / "arrow.dll").exists()
            assert (runtime_dir / "vcomp140.dll").exists()
    finally:
        shutil.rmtree(test_root, ignore_errors=True)
