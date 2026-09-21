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
from scipy.spatial import cKDTree

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


COORDS = ["Xcoor", "Ycoor", "Zcoor"]


def _nearest(a: pd.DataFrame, b: pd.DataFrame):
    """Distance and index of the nearest sensor in ``b`` for every sensor in ``a`` (order-independent)."""
    if b.empty:
        return np.full(len(a), np.inf), np.zeros(len(a), dtype=int)
    dist, idx = cKDTree(b[COORDS].to_numpy()).query(a[COORDS].to_numpy())
    return dist, idx


def _compare_geometry(ref: pd.DataFrame, other: pd.DataFrame):
    """Match each ref sensor to its nearest sensor on the other OS; identical if within tolerance and same area."""
    dist, idx = _nearest(ref, other)
    same_area = np.isclose(ref["AREA_m2"].to_numpy(), other["AREA_m2"].to_numpy()[idx], atol=1e-6)
    identical = (dist <= COORD_TOLERANCE_M) & same_area
    moved = ~identical
    return {"identical": int(identical.sum()), "moved": int(moved.sum()),
            "max_displacement": float(dist[moved].max()) if moved.any() else 0.0}


def _only_in(a: pd.DataFrame, b: pd.DataFrame) -> int:
    """Number of sensors in ``a`` with no sensor of ``b`` at the same position."""
    return int((_nearest(a, b)[0] > COORD_TOLERANCE_M).sum())


def _read(path: Path):
    return pd.read_csv(path) if path.exists() else None


def _selected(pv: pd.DataFrame) -> pd.DataFrame:
    """PV sensors CSV holds zero-filled placeholder rows when a building has no PV sensors."""
    return pv[pv["area_installed_module_m2"] > 0]


def compare(artifacts_dir: Path) -> str:
    lines = ["## Cross-OS radiation comparison", "",
             f"Reference: `{REFERENCE_OS}`. Sensors are matched by nearest XYZ position, not row order "
             f"(coordinate tolerance {COORD_TOLERANCE_M} m, area tolerance 1e-6 m²); a sensor is *moved* if no sensor "
             f"on the other OS sits within tolerance with the same area. PV selection is compared by position too. "
             f"Advisory only.", ""]
    oses = sorted(p.name.removeprefix("radiation-") for p in artifacts_dir.iterdir() if p.is_dir())
    ref_root = artifacts_dir / f"radiation-{REFERENCE_OS}"
    if not ref_root.is_dir():
        return "\n".join(lines + [f"Reference artifact for `{REFERENCE_OS}` not found; nothing to compare."])

    for other_os in [o for o in oses if o != REFERENCE_OS]:
        other_root = artifacts_dir / f"radiation-{other_os}"
        lines += [f"### {other_os} vs {REFERENCE_OS}", "",
                  "| Scenario | Building | Sensors (ref/other) | Identical | Moved | Max displacement m | "
                  "PV sensors selected (ref/other) | PV selected only ref/other | PV installed area m² (ref/other) |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for ref_geom in sorted(ref_root.glob("*/outputs/data/solar-radiation/*_geometry.csv")):
            rel = ref_geom.relative_to(ref_root)
            scenario, building = rel.parts[0], ref_geom.name.removesuffix("_geometry.csv")
            ref_df, other_df = _read(ref_geom), _read(other_root / rel)
            if other_df is None:
                lines.append(f"| {scenario} | {building} | missing on {other_os} | | | | | | |")
                continue
            geom = _compare_geometry(ref_df, other_df)
            pv_rel = Path(scenario) / "outputs" / "data" / "potentials" / "solar" / "sensors" / f"{building}_PV_sensors.csv"
            ref_pv, other_pv = _read(ref_root / pv_rel), _read(other_root / pv_rel)
            pv_cells = ["", "", ""]
            if ref_pv is not None and other_pv is not None:
                ref_pv, other_pv = _selected(ref_pv), _selected(other_pv)
                pv_cells = [f"{len(ref_pv)}/{len(other_pv)}",
                            f"{_only_in(ref_pv, other_pv)}/{_only_in(other_pv, ref_pv)}",
                            f"{ref_pv['area_installed_module_m2'].sum():.1f}/"
                            f"{other_pv['area_installed_module_m2'].sum():.1f}"]
            lines.append(f"| {scenario} | {building} | {len(ref_df)}/{len(other_df)} | {geom['identical']} | "
                         f"{geom['moved']} | {geom['max_displacement']:.3f} | " + " | ".join(pv_cells) + " |")
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
