import csv
import os
from typing import Any
from cea.datamanagement.database.assemblies import SURFACE_RESISTANCES
import pulp  # type: ignore


def read_materials(materials_csv: str) -> list[dict[str, Any]]:
    materials: list[dict[str, Any]] = []
    with open(materials_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Keep only rows with numeric thermal conductivity and density and unit=kg
            unit = (row.get("unit") or "").strip()

            # Safely parse floats; skip if missing
            def _f(x: Any) -> float:
                try:
                    return float(x)
                except (TypeError, ValueError):
                    return float("nan")

            k = _f(row.get("thermal_conductivity"))
            rho = _f(row.get("density"))
            ghg_per_unit = _f(row.get("GHG_emission_total"))
            if any(map(lambda v: v != v, [k, rho, ghg_per_unit])):  # check NaN
                continue
            if unit != "kg":
                continue
            materials.append(
                {
                    "name": row.get("name") or row.get("ID") or "material",
                    "k": k,
                    "rho": rho,
                    "ghg_per_kg": ghg_per_unit,
                }
            )
    # Sort by thermal conductivity to prefer insulators and structural materials variety
    return materials


def read_envelope_targets(
    envelope_csv: str, u_key: str, ghg_key: str, extra_keys: list[str] | None = None
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    with open(envelope_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("code")
            if not code:
                continue

            def _f(x: Any) -> float:
                try:
                    return float(x)
                except (TypeError, ValueError):
                    return float("nan")

            u_target = _f(row.get(u_key))
            ghg_target = _f(row.get(ghg_key))
            if any(map(lambda v: v != v, [u_target, ghg_target])):
                continue
            entry: dict[str, Any] = {
                "code": code,
                "description": row.get("description", ""),
                "U": u_target,
                "GHG": ghg_target,
            }
            if extra_keys:
                for k in extra_keys:
                    entry[k] = row.get(k)
            targets.append(entry)
    return targets


def compute_u(thicknesses: list[float], ks: list[float], kind: str) -> float:
    # assemblies SURFACE_RESISTANCES stores internal/external resistances
    coeffs = SURFACE_RESISTANCES.get(kind, {"internal": 0.0, "external": 0.0})
    Rsi = coeffs["internal"]
    Rse = coeffs["external"]
    R_layers = sum((t / k) if k > 0 else 0.0 for t, k in zip(thicknesses, ks))
    R_total = Rsi + R_layers + Rse
    return 1.0 / R_total if R_total > 0 else float("inf")


def compute_ghg_per_m2(
    thicknesses: list[float], rhos: list[float], ghg_per_kg: list[float]
) -> float:
    # Per m2: mass per m2 = rho * thickness; emissions = mass * ghg_per_kg
    return sum(rho * t * g for t, rho, g in zip(thicknesses, rhos, ghg_per_kg))


def optimize_three_layer_milp(
    materials: list[dict[str, Any]],
    U_target: float,
    GHG_target: float,
    kind: str,
    max_materials: int = 40,
    required_material_name: str | None = None,
    weight_u: float = 0.8,
    weight_ghg: float = 0.2,
    min_required_thickness: float = 0.1,
) -> tuple[list[dict[str, Any]], list[float], float, float]:
    """select exactly 3 materials and thicknesses to match U_target while minimising GHG deviation.

    Linearization uses R_layers = sum(t_i / k_i) and constraint Rsi + R_layers + Rse = 1/U_target.
    """
    # Require PuLP to be available
    if not hasattr(pulp, "LpProblem"):
        raise RuntimeError("PuLP is required for material envelope optimisation.")

    mats_sorted = sorted(materials, key=lambda m: float(m["k"]))
    low = mats_sorted[: max_materials // 2]
    high = list(reversed(mats_sorted))[: max_materials // 2]
    candidates = (low + high)[:max_materials]

    n = len(candidates)
    k_vals = [float(m["k"]) for m in candidates]
    rho_vals = [float(m["rho"]) for m in candidates]
    ghg_vals = [float(m["ghg_per_kg"]) for m in candidates]

    prob = pulp.LpProblem("Envelope3LayerMILP", pulp.LpMinimize)
    y = [pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1, cat=pulp.LpBinary) for i in range(n)]
    M = 1.0
    t = [pulp.LpVariable(f"t_{i}", lowBound=0, upBound=M) for i in range(n)]

    # Exactly 3 materials
    prob += pulp.lpSum(y) == 3
    # Link selection to thickness
    for i in range(n):
        prob += t[i] <= M * y[i]

    # Required material presence
    if required_material_name:
        req = required_material_name.lower()
        req_idxs = [i for i, m in enumerate(candidates) if req in str(m.get("name") or "").lower()]
        if req_idxs:
            prob += pulp.lpSum([y[i] for i in req_idxs]) >= 1
            # Enforce minimum thickness for any selected required material
            for i in req_idxs:
                prob += t[i] >= min_required_thickness * y[i]

    coeffs = SURFACE_RESISTANCES.get(kind, {"internal": 0.0, "external": 0.0})
    Rsi, Rse = coeffs["internal"], coeffs["external"]
    R_target = max(0.0, 1.0 / max(U_target, 1e-6) - Rsi - Rse)
    # U deviation variables (lexicographic-style priority via weights), normalised by target
    r_pos = pulp.LpVariable("r_pos", lowBound=0)
    r_neg = pulp.LpVariable("r_neg", lowBound=0)
    sR = max(R_target, 1e-6)
    prob += pulp.lpSum([(1.0 / k_vals[i]) * t[i] for i in range(n)]) - R_target == sR * (r_pos - r_neg)

    # GHG expression and absolute deviation
    ghg_expr = pulp.lpSum([rho_vals[i] * t[i] * ghg_vals[i] for i in range(n)])
    d_pos = pulp.LpVariable("d_pos", lowBound=0)
    d_neg = pulp.LpVariable("d_neg", lowBound=0)
    sG = max(1.0, abs(GHG_target))
    prob += ghg_expr - GHG_target == sG * (d_pos - d_neg)
    # Prioritise U via large multiplier; both terms are now dimensionless
    U_PRIORITY = 1000.0
    prob += U_PRIORITY * max(1e-6, weight_u) * (r_pos + r_neg) + max(1e-6, weight_ghg) * (d_pos + d_neg)

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    sel: list[int] = []
    for i in range(n):
        v_raw: Any = getattr(y[i], "varValue", None)
        if v_raw is None:
            try:
                v_raw = y[i].value()
            except Exception:
                v_raw = 0.0
        try:
            v = float(v_raw or 0.0)
        except Exception:
            v = 0.0
        if v > 0.5:
            sel.append(i)
    if len(sel) != 3:
        # Fallback: pick top-3 by selection value to keep PuLP-only behaviour
        scored = sorted(
            [(i, float(getattr(y[i], "varValue", 0.0) or 0.0)) for i in range(n)],
            key=lambda t: t[1],
            reverse=True,
        )
        sel = [i for i, _ in scored[:3]]

    combo = [candidates[i] for i in sel]
    ts = [float(t[i].value() or 0.0) for i in sel]
    U = compute_u(ts, [float(m["k"]) for m in combo], kind)
    GHG = sum(float(m["rho"]) * ts[idx] * float(m["ghg_per_kg"]) for idx, m in enumerate(combo))
    return combo, ts, U, GHG


def _process_targets(
    base_dir: str,
    kind: str,
    envelope_dir: str,
    out_dir: str,
    materials: list[dict[str, Any]],
    u_key: str,
    ghg_key: str,
    extra_keys: list[str],
    required_rule: Any,
    weight_u: float,
    weight_ghg: float,
    min_required_thickness: float,
) -> None:
    targets = read_envelope_targets(
        os.path.join(envelope_dir, f"ENVELOPE_{kind.upper()}.csv"), u_key, ghg_key, extra_keys=extra_keys
    )
    results = []
    for tgt in targets:
        req_name = required_rule(tgt)
        combo, ts, u, ghg = optimize_three_layer_milp(
            materials,
            float(tgt["U"]),
            float(tgt["GHG"]),
            kind=kind,
            required_material_name=req_name,
            weight_u=weight_u,
            weight_ghg=weight_ghg,
            min_required_thickness=min_required_thickness,
        )
        try:
            print(
                f"[{kind}] {tgt['code']}: target U={float(tgt['U']):.3f}, GHG={float(tgt['GHG']):.2f}; "
                f"achieved U={float(u):.3f}, GHG={float(ghg):.2f}"
            )
        except Exception:
            pass
        results.append((tgt, ts, {"materials": combo, "U": u, "GHG": ghg}))
    write_material_based_csv(os.path.join(out_dir, f"ENVELOPE_{kind.upper()}.csv"), kind, results)


def write_material_based_csv(
    output_csv: str,
    kind: str,
    results: list[tuple[dict[str, Any], list[float], dict[str, Any]]],
) -> None:
    # results: list of (target, thicknesses, meta) per envelope code
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    if kind == "floor":
        fieldnames = [
            "description",
            "code",
            "material_name_1",
            "thickness_1_m",
            "material_name_2",
            "thickness_2_m",
            "material_name_3",
            "thickness_3_m",
            "Service_Life_floor",
            "Reference",
            "Unnamed: 7",
        ]
    elif kind == "roof":
        fieldnames = [
            "description",
            "code",
            "material_name_1",
            "thickness_1_m",
            "material_name_2",
            "thickness_2_m",
            "material_name_3",
            "thickness_3_m",
            "a_roof",
            "e_roof",
            "r_roof",
            "Service_Life_roof",
            "Reference",
        ]
    else:  # wall
        fieldnames = [
            "description",
            "code",
            "material_name_1",
            "thickness_1_m",
            "material_name_2",
            "thickness_2_m",
            "material_name_3",
            "thickness_3_m",
            "a_wall",
            "e_wall",
            "r_wall",
            "Service_Life_wall",
            "Reference",
        ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for target, ts, meta in results:
            m1, m2, m3 = meta["materials"]
            row = {
                "description": target["description"],
                "code": target["code"],
                "material_name_1": m1.get("name"),
                "thickness_1_m": round(ts[0], 3),
                "material_name_2": m2.get("name"),
                "thickness_2_m": round(ts[1], 3),
                "material_name_3": m3.get("name"),
                "thickness_3_m": round(ts[2], 3),
            }
            row["Reference"] = f"artificial construction with U value and GHG emission matched with original code {target['code']}. Material selection does not have any physical meaning. Original reference: {target.get('Reference')}"
            # Copy service life field depending on kind if present in target
            if kind == "floor":
                row["Service_Life_floor"] = target.get("Service_Life_floor")
                row["Unnamed: 7"] = ""
            elif kind == "roof":
                row["Service_Life_roof"] = target.get("Service_Life_roof")                # pass through radiative properties
                row["a_roof"] = target.get("a_roof")
                row["e_roof"] = target.get("e_roof")
                row["r_roof"] = target.get("r_roof")
            else:
                row["Service_Life_wall"] = target.get("Service_Life_wall")
                row["a_wall"] = target.get("a_wall")
                row["e_wall"] = target.get("e_wall")
                row["r_wall"] = target.get("r_wall")
            writer.writerow(row)


def run(
    base_dir: str,
    country: str = "CH",
    weight_u: float = 0.6,
    weight_ghg: float = 0.4,
    min_required_thickness: float = 0.1,
) -> None:
    # Paths
    materials_csv = os.path.join(
        base_dir,
        "cea",
        "databases",
        country,
        "COMPONENTS",
        "MATERIALS",
        "MATERIALS.csv",
    )
    envelope_dir = os.path.join(
        base_dir, "cea", "databases", country, "ASSEMBLIES", "ENVELOPE"
    )
    out_dir = os.path.join(
        base_dir, "cea", "databases", country, "ASSEMBLIES", "ENVELOPE_material_based"
    )

    materials = read_materials(materials_csv)
    if not materials:
        raise RuntimeError(
            "No suitable materials found (require kg unit, k, density, GHG)."
        )

    # Floor
    _process_targets(
        base_dir,
        kind="floor",
        envelope_dir=envelope_dir,
        out_dir=out_dir,
        materials=materials,
        u_key="U_base",
        ghg_key="GHG_floor_kgCO2m2",
        extra_keys=["Service_Life_floor", "Reference"],
        required_rule=lambda tgt: (
            "concrete_1_percent_steel_reinforcement"
            if "concrete" in (str(tgt.get("description") or "")).lower()
            else None
        ),
        weight_u=weight_u,
        weight_ghg=weight_ghg,
        min_required_thickness=min_required_thickness,
    )

    # Roof
    _process_targets(
        base_dir,
        kind="roof",
        envelope_dir=envelope_dir,
        out_dir=out_dir,
        materials=materials,
        u_key="U_roof",
        ghg_key="GHG_roof_kgCO2m2",
        extra_keys=["a_roof", "e_roof", "r_roof", "Service_Life_roof", "Reference"],
        required_rule=lambda tgt: (
            "concrete" if "concrete" in (str(tgt.get("description") or "")).lower() else None
        ),
        weight_u=weight_u,
        weight_ghg=weight_ghg,
        min_required_thickness=min_required_thickness,
    )

    # Wall
    _process_targets(
        base_dir,
        kind="wall",
        envelope_dir=envelope_dir,
        out_dir=out_dir,
        materials=materials,
        u_key="U_wall",
        ghg_key="GHG_wall_kgCO2m2",
        extra_keys=["a_wall", "e_wall", "r_wall", "Service_Life_wall", "Reference"],
        required_rule=lambda tgt: (
            "concrete"
            if "concrete" in (str(tgt.get("description") or "")).lower()
            else ("brick" if "brick" in (str(tgt.get("description") or "")).lower() else None)
        ),
        weight_u=weight_u,
        weight_ghg=weight_ghg,
        min_required_thickness=min_required_thickness,
    )


if __name__ == "__main__":
    # Default to repo root two levels up from this file
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    run(repo_root)
