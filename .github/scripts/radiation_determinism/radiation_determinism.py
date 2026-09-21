"""Is CEA radiation deterministic on one OS, and across OSes when DAYSIM gets identical inputs?

Subcommands (all run with the CEA environment, e.g. ``pixi run python``):

    pipeline-twice <scenario> <out.json>
        Run the full radiation script twice on this OS (OCC geometry -> DAYSIM) and compare the intermediate
        files and per-sensor results of the two runs.
    prepare <scenario> <inputs_dir>
        Run radiation once and keep the DAYSIM inputs (radiance material/geometry, sensor points, weather,
        radiance parameters), so the DAYSIM step can be replayed on other OSes without OCC in the loop.
    daysim <inputs_dir> <out.json>
        Replay DAYSIM (epw2wea, radfiles2daysim, gen_dc, ds_illum) twice on the given inputs.
    compare <artifacts_dir>
        Summarise ``pipeline-<os>/pipeline.json`` and ``daysim-<os>/daysim.json`` into $GITHUB_STEP_SUMMARY.

Results are compared bit for bit (SHA-256 of each sensor's hourly float32 row) and as % difference of annual sums.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from unittest import mock

import numpy as np

REFERENCE_OS = "ubuntu-latest"
RADIANCE_PARAMETERS = ["rad_ab", "rad_ad", "rad_as", "rad_ar", "rad_aa", "rad_lr", "rad_st", "rad_sj", "rad_lw",
                       "rad_dj", "rad_ds", "rad_dr", "rad_dp"]


def _sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_ill(path) -> np.ndarray:
    """Same parsing as ``DaySimProject.eval_ill``: rows are sensors, columns are hours."""
    with open(path) as f:
        return np.array([np.array(row[4:], dtype=np.float32) for row in csv.reader(f, delimiter=" ")]).T


def _summarise_ill(sensors_by_hour: np.ndarray) -> dict:
    return {"row_hashes": [hashlib.sha256(row.tobytes()).hexdigest()[:16] for row in sensors_by_hour],
            "annual_Whm2": sensors_by_hour.astype(np.float64).sum(axis=1).tolist()}


def _run_radiation(scenario: Path, stage: Path):
    """Run the radiation script but keep the DAYSIM staging folder (normally deleted on success) in ``stage``."""
    import cea.config
    from cea.inputlocator import InputLocator
    from cea.resources.radiation import main as radiation_main

    config = cea.config.Configuration()
    config.scenario = str(scenario)
    config.multiprocessing = False
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    with mock.patch.object(InputLocator, "get_temporary_folder", return_value=str(stage)), \
            mock.patch("shutil.rmtree"):
        radiation_main.main(config)
    return config


def _pipeline_products(stage: Path, scenario: Path) -> dict:
    staging = stage / "cea_radiation"
    files = {name: _sha256(staging / "common_inputs" / name)
             for name in ("radiance_material.rad", "radiance_geometry.rad")}
    ill = {}
    for chunk in sorted((staging / "projects").glob("chunk_*")):
        files[f"{chunk.name}/sensors.pts"] = _sha256(chunk / "sensors.pts")
        ill[chunk.name] = _summarise_ill(_read_ill(chunk / f"{chunk.name}.ill"))
    for path in sorted((scenario / "outputs" / "data" / "solar-radiation").glob("*_geometry.csv")):
        files[f"sensor grid csv/{path.name}"] = _sha256(path)
    return {"files": files, "ill": ill}


def _ill_stats(a: dict, b: dict) -> str:
    """Bit-identical sensor count and % difference of annual radiation between two result sets."""
    total = identical = 0
    pct = []
    for chunk in a:
        if chunk not in b or len(a[chunk]["row_hashes"]) != len(b[chunk]["row_hashes"]):
            return "sensor count differs"
        total += len(a[chunk]["row_hashes"])
        identical += sum(x == y for x, y in zip(a[chunk]["row_hashes"], b[chunk]["row_hashes"]))
        annual_a, annual_b = np.array(a[chunk]["annual_Whm2"]), np.array(b[chunk]["annual_Whm2"])
        with np.errstate(divide="ignore", invalid="ignore"):
            diff = np.abs(annual_b - annual_a) / annual_a * 100
        pct.append(diff[np.isfinite(diff)])
    pct = np.concatenate(pct) if pct else np.array([])
    if not len(pct):
        return f"{identical}/{total} bit-identical"
    return f"{identical}/{total} bit-identical; annual Δ mean {pct.mean():.3f}%, max {pct.max():.3f}%"


def _equal_files(a: dict, b: dict) -> str:
    same = sum(a.get(name) == b.get(name) for name in a)
    return f"{same}/{len(a)} identical"


def pipeline_twice(scenario: Path, out_json: Path):
    runs = []
    for i in (1, 2):
        stage = out_json.parent / "stage"
        print(f"=== radiation run {i} ===")
        _run_radiation(scenario, stage)
        runs.append(_pipeline_products(stage, scenario))
    out_json.write_text(json.dumps({"platform": platform.platform(), "runs": runs}))


def prepare(scenario: Path, inputs_dir: Path):
    from cea.inputlocator import InputLocator

    stage = inputs_dir.parent / "prepare_stage"
    config = _run_radiation(scenario, stage)
    inputs_dir.mkdir(parents=True, exist_ok=True)
    common = stage / "cea_radiation" / "common_inputs"
    for name in ("radiance_material.rad", "radiance_geometry.rad", "daysim_shading.rad"):
        if (common / name).exists():
            shutil.copy2(common / name, inputs_dir / name)
    for chunk in sorted((stage / "cea_radiation" / "projects").glob("chunk_*")):
        shutil.copy2(chunk / "sensors.pts", inputs_dir / f"sensors_{chunk.name}.pts")
    shutil.copy2(InputLocator(str(scenario)).get_weather_file(), inputs_dir / "weather.epw")
    parameters = {name: getattr(config.radiation, name) for name in RADIANCE_PARAMETERS}
    (inputs_dir / "inputs.json").write_text(json.dumps({"radiance_parameters": parameters}))


def daysim(inputs_dir: Path, out_json: Path, repeats: int = 2):
    from cea.resources.radiation import daysim as cea_daysim_module
    from cea.resources.radiation.radiance import CEADaySim

    parameters = json.loads((inputs_dir / "inputs.json").read_text())["radiance_parameters"]
    bin_path = cea_daysim_module.check_daysim_bin_directory()
    results = []
    for i in range(repeats):
        # fixed location so that any paths DAYSIM embeds in its files are the same between repeats
        stage = out_json.parent / "daysim_stage"
        if stage.exists():
            shutil.rmtree(stage)
        print(f"=== DAYSIM repeat {i + 1} ===")
        cea_daysim = CEADaySim(str(stage), bin_path)
        shutil.copy2(inputs_dir / "radiance_material.rad", cea_daysim.rad_material_path)
        shutil.copy2(inputs_dir / "radiance_geometry.rad", cea_daysim.rad_geometry_path)
        if (inputs_dir / "daysim_shading.rad").exists():
            shutil.copy2(inputs_dir / "daysim_shading.rad", cea_daysim.daysim_shading_path)
        cea_daysim.execute_epw2wea(str(inputs_dir / "weather.epw"))
        cea_daysim.execute_radfiles2daysim()
        run = {"stage_files": {Path(p).name: _sha256(p) for p in (cea_daysim.daysim_material_path,
                                                                 cea_daysim.daysim_geometry_path,
                                                                 cea_daysim.wea_weather_path)},
               "chunks": {}}
        for pts in sorted(inputs_dir.glob("sensors_chunk_*.pts")):
            name = pts.stem.removeprefix("sensors_")
            rows = [[float(v) for v in line.split()] for line in pts.read_text().splitlines() if line.strip()]
            project = cea_daysim.initialize_daysim_project(name)
            project.create_sensor_input_file([r[:3] for r in rows], [r[3:] for r in rows])
            if _sha256(project.sensor_path) != _sha256(pts):
                raise RuntimeError(f"Rewritten sensor file differs from the prepared one for {name}")
            project.write_radiance_parameters(**parameters)
            project.execute_gen_dc()
            project.execute_ds_illum()
            chunk = _summarise_ill(project.eval_ill())
            # best effort: daylight coefficient files may embed paths, so treat a mismatch with care
            chunk["dc_files"] = {str(p.relative_to(project.project_path)): _sha256(p)
                                 for p in sorted(Path(project.project_path).rglob("*.dc"))}
            run["chunks"][name] = chunk
        results.append(run)
    out_json.write_text(json.dumps({"platform": platform.platform(), "runs": results}))


def _load(artifacts_dir: Path, prefix: str, filename: str) -> dict:
    return {path.parent.name.removeprefix(f"{prefix}-"): json.loads(path.read_text())
            for path in sorted(artifacts_dir.glob(f"{prefix}-*/{filename}"))}


def compare(artifacts_dir: Path) -> str:
    pipeline = _load(artifacts_dir, "pipeline", "pipeline.json")
    replay = _load(artifacts_dir, "daysim", "daysim.json")
    lines = ["## Radiation determinism experiment", ""]

    lines += ["### A. Same OS, full radiation script run twice (OCC geometry + DAYSIM)", "",
              "| OS | Intermediate files identical | Sensor results, run 1 vs run 2 |", "|---|---|---|"]
    for os_name, data in pipeline.items():
        first, second = data["runs"]
        lines.append(f"| {os_name} | {_equal_files(first['files'], second['files'])} | "
                     f"{_ill_stats(first['ill'], second['ill'])} |")

    lines += ["", "### B. Same OS, DAYSIM run twice on identical input files", "",
              "| OS | Converted DAYSIM inputs identical | `.dc` files identical | Sensor results, repeat 1 vs 2 |",
              "|---|---|---|---|"]
    for os_name, data in replay.items():
        first, second = data["runs"]
        dc_first = {f"{c}/{k}": v for c, d in first["chunks"].items() for k, v in d["dc_files"].items()}
        dc_second = {f"{c}/{k}": v for c, d in second["chunks"].items() for k, v in d["dc_files"].items()}
        lines.append(f"| {os_name} | {_equal_files(first['stage_files'], second['stage_files'])} | "
                     f"{_equal_files(dc_first, dc_second)} | {_ill_stats(first['chunks'], second['chunks'])} |")

    lines += ["", f"### C. Different OSes, DAYSIM on identical input files (vs `{REFERENCE_OS}`)", "",
              "| OS | Converted DAYSIM inputs identical | `.dc` files identical | Sensor results |",
              "|---|---|---|---|"]
    reference = replay.get(REFERENCE_OS)
    for os_name, data in replay.items():
        if os_name == REFERENCE_OS or reference is None:
            continue
        ref_run, run = reference["runs"][0], data["runs"][0]
        dc_ref = {f"{c}/{k}": v for c, d in ref_run["chunks"].items() for k, v in d["dc_files"].items()}
        dc_run = {f"{c}/{k}": v for c, d in run["chunks"].items() for k, v in d["dc_files"].items()}
        lines.append(f"| {os_name} | {_equal_files(ref_run['stage_files'], run['stage_files'])} | "
                     f"{_equal_files(dc_ref, dc_run)} | {_ill_stats(ref_run['chunks'], run['chunks'])} |")

    lines += ["", ("`.dc` hashes are best effort (the files may embed absolute paths, which differ between OSes). "
                   "Bit-identical means the SHA-256 of a sensor's hourly float32 row matches.")]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("pipeline-twice", "prepare", "daysim", "compare"):
        p = sub.add_parser(name)
        p.add_argument("source", type=Path)
        if name != "compare":
            p.add_argument("target", type=Path)
    args = parser.parse_args()

    if args.command == "pipeline-twice":
        args.target.parent.mkdir(parents=True, exist_ok=True)
        pipeline_twice(args.source, args.target)
    elif args.command == "prepare":
        prepare(args.source, args.target)
    elif args.command == "daysim":
        args.target.parent.mkdir(parents=True, exist_ok=True)
        daysim(args.source, args.target)
    else:
        report = compare(args.source)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as f:
                f.write(report + "\n")
        print(report)


if __name__ == "__main__":
    sys.exit(main())
