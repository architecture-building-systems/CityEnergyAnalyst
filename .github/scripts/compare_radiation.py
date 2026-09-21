"""Collect and compare radiation/PV sensor outputs produced by the CI integration tests on each OS.

Usage:
    python compare_radiation.py collect <out_dir>        # per-OS job: copy small radiation/PV outputs
    python compare_radiation.py compare <artifacts_dir>  # compare job: artifacts_dir/<os>/<scenario>/...

Advisory only: writes a markdown report to $GITHUB_STEP_SUMMARY (or stdout) and never fails the build.
"""
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REFERENCE_OS = "ubuntu-latest"
COORD_TOLERANCE_M = 1e-3
SCENARIOS = ("zug_heating", "sg_cooling")


def _find_scenarios():
    """Yield (project_label, scenario_dir) for test projects (at most 2 levels below home) with radiation outputs."""
    home = Path.home()
    for project in [*home.glob("*"), *home.glob("*/*")]:
        if project.name in SCENARIOS and project.is_dir():
            for radiation_dir in project.rglob("solar-radiation"):
                if radiation_dir.parent.name == "data" and radiation_dir.parent.parent.name == "outputs":
                    yield project.name, radiation_dir.parents[2]


def collect(out_dir: Path):
    """Copy geometry and PV sensor CSVs (skips the large insolation feather files)."""
    found = False
    for label, scenario in _find_scenarios():
        found = True
        patterns = ["outputs/data/solar-radiation/*_geometry.csv",
                    "outputs/data/potentials/solar/sensors/*_PV_sensors.csv"]
        for pattern in patterns:
            for src in scenario.glob(pattern):
                dst = out_dir / label / src.relative_to(scenario)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    if not found:
        print(f"WARNING: no radiation outputs found under {Path.home()}")


def _compare_geometry(ref: pd.DataFrame, other: pd.DataFrame):
    """Return (n_ref, n_other, identical_count, moved_count) comparing sensors row by row, then by area."""
    if len(ref) != len(other):
        return len(ref), len(other), None, None
    coords = ["Xcoor", "Ycoor", "Zcoor"]
    dist = np.linalg.norm(ref[coords].to_numpy() - other[coords].to_numpy(), axis=1)
    same_area = np.isclose(ref["AREA_m2"].to_numpy(), other["AREA_m2"].to_numpy(), atol=1e-6)
    identical = int(((dist <= COORD_TOLERANCE_M) & same_area).sum())
    return len(ref), len(other), identical, len(ref) - identical


def _read(path: Path):
    return pd.read_csv(path) if path.exists() else None


def compare(artifacts_dir: Path) -> str:
    lines = ["## Cross-OS radiation comparison", "",
             f"Reference: `{REFERENCE_OS}`. Sensors are matched by row order within each building "
             f"(coordinate tolerance {COORD_TOLERANCE_M} m, area tolerance 1e-6 m²). Advisory only.", ""]
    oses = sorted(p.name.removeprefix("radiation-") for p in artifacts_dir.iterdir() if p.is_dir())
    ref_root = artifacts_dir / f"radiation-{REFERENCE_OS}"
    if not ref_root.is_dir():
        return "\n".join(lines + [f"Reference artifact for `{REFERENCE_OS}` not found; nothing to compare."])

    for other_os in [o for o in oses if o != REFERENCE_OS]:
        other_root = artifacts_dir / f"radiation-{other_os}"
        lines += [f"### {other_os} vs {REFERENCE_OS}", "",
                  "| Scenario | Building | Sensors (ref/other) | Identical positions | Moved | "
                  "PV sensors selected (ref/other) | PV selected only ref/other | PV installed area m² (ref/other) |",
                  "|---|---|---|---|---|---|---|---|"]
        for ref_geom in sorted(ref_root.glob("*/outputs/data/solar-radiation/*_geometry.csv")):
            rel = ref_geom.relative_to(ref_root)
            scenario, building = rel.parts[0], ref_geom.name.removesuffix("_geometry.csv")
            other_geom = other_root / rel
            ref_df, other_df = _read(ref_geom), _read(other_geom)
            if other_df is None:
                lines.append(f"| {scenario} | {building} | missing on {other_os} | | | | | |")
                continue
            n_ref, n_other, identical, moved = _compare_geometry(ref_df, other_df)
            pv_rel = Path(scenario) / "outputs" / "data" / "potentials" / "solar" / "sensors" / f"{building}_PV_sensors.csv"
            ref_pv, other_pv = _read(ref_root / pv_rel), _read(other_root / pv_rel)
            pv_cells = ["", "", ""]
            if ref_pv is not None and other_pv is not None:
                ref_idx, other_idx = set(ref_pv.iloc[:, 0]), set(other_pv.iloc[:, 0])
                pv_cells = [f"{len(ref_idx)}/{len(other_idx)}",
                            f"{len(ref_idx - other_idx)}/{len(other_idx - ref_idx)}",
                            f"{ref_pv['area_installed_module_m2'].sum():.1f}/{other_pv['area_installed_module_m2'].sum():.1f}"]
            lines.append(f"| {scenario} | {building} | {n_ref}/{n_other} | "
                         f"{'n/a' if identical is None else identical} | {'n/a' if moved is None else moved} | "
                         + " | ".join(pv_cells) + " |")
        lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("collect", "compare"):
        sys.exit(__doc__)
    target = Path(sys.argv[2])
    if sys.argv[1] == "collect":
        collect(target)
        return
    report = compare(target)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
