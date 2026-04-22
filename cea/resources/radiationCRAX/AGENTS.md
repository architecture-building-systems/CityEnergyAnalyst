# radiationCRAX

## Main API
- `CRAX.run_mesh_generation(json_file: str) -> str` - Run `mesh-generation` with staged native runtimes.
- `CRAX.run_radiation(json_file: str) -> str` - Run `radiation` with the same runtime-staging rules.
- `check_crax_exe_directory() -> str` - Resolve the installed `cea_external_tools` binary directory.
- `main.main(config: Configuration) -> None` - Export CRAX inputs, optionally build sensors, then run mesh and radiation.

## Key Patterns
### DO: Stage Windows runtime DLLs beside the executable before launching CRAX
```python
with self._get_execution_context("mesh-generation.exe") as (exe_path, cwd, env):
    result = subprocess.run([exe_path, json_file], cwd=cwd, env=env, capture_output=True, text=True)
```
Stage under `_get_runtime_root()` and use `CEA_CRAX_RUNTIME_DIR` only as an override for debugging or constrained environments.

### DO: Reuse the same execution helper for both CRAX binaries
```python
with self._get_execution_context(exe_name) as (exe_path, cwd, env):
    subprocess.run([exe_path, json_file], cwd=cwd, env=env, ...)
```

### DON'T: Rely on `PATH` alone to override `System32` C++ runtimes on Windows
```python
# This can still load C:\Windows\System32\MSVCP140.dll before the Pixi runtime.
env["PATH"] = f"{lib_path};{env['PATH']}"
```

## Related Files
- `CRAXModel.py` - Native executable launch and runtime staging.
- `main.py` - CRAX input export and workflow orchestration.
- `../../tests/test_radiation_crax_model.py` - Regression coverage for runtime staging.
