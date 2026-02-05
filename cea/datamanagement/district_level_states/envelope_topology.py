from __future__ import annotations

from typing import Any

import pandas as pd


def validate_three_layer_topology(
    row: pd.Series,
    *,
    year_of_state: int,
    archetype: str,
    component: str,
    envelope_ref: str,
) -> list[str]:
    """Validate the fixed 3-slot layer topology in an envelope DB row.

    Invariant:
    - There are always 3 layer slots (`material_name_1..3`, `thickness_1_m..3`).
    - At least one slot must have `thickness_i_m > 0` (i.e., at most two zeros).
    - If `thickness_i_m > 0`, `material_name_i` must be non-empty.

    Args:
        row: A row from an envelope DB (typically indexed by `code`).
        year_of_state: State year being checked / materialised.
        archetype: Archetype / construction standard key.
        component: Component key from YAML / archetype DB (e.g., `wall`, `roof`, `base`).
        envelope_ref: Human-readable reference to where the row came from (path, DB name, etc).

    Returns:
        List of human-readable errors (empty list means valid).
    """

    errors: list[str] = []

    required_cols = [
        "material_name_1",
        "thickness_1_m",
        "material_name_2",
        "thickness_2_m",
        "material_name_3",
        "thickness_3_m",
    ]
    missing = [c for c in required_cols if c not in row.index]
    if missing:
        errors.append(
            f"year {year_of_state}, archetype '{archetype}', component '{component}': "
            f"missing required layer columns {missing} in {envelope_ref}"
        )
        return errors

    thicknesses: list[float] = []
    for idx in (1, 2, 3):
        t_raw: Any = row.get(f"thickness_{idx}_m")
        if pd.isna(t_raw):
            errors.append(
                f"year {year_of_state}, archetype '{archetype}', component '{component}': "
                f"thickness_{idx}_m is NaN in {envelope_ref}"
            )
            continue

        try:
            t = float(t_raw)
        except (TypeError, ValueError):
            errors.append(
                f"year {year_of_state}, archetype '{archetype}', component '{component}': "
                f"thickness_{idx}_m='{t_raw}' is not numeric in {envelope_ref}"
            )
            continue

        if t < 0.0:
            errors.append(
                f"year {year_of_state}, archetype '{archetype}', component '{component}': "
                f"thickness_{idx}_m={t} must be >= 0 in {envelope_ref}"
            )

        thicknesses.append(t)

        if t > 0.0:
            name_raw = row[f"material_name_{idx}"]  
            name = "" if pd.isna(name_raw) else str(name_raw).strip() 
            if not name:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': "
                    f"material_name_{idx} is empty but thickness_{idx}_m={t} in {envelope_ref}"
                )

    if thicknesses and sum(1 for t in thicknesses if t > 0.0) < 1:
        errors.append(
            f"year {year_of_state}, archetype '{archetype}', component '{component}': "
            "expected at least one non-zero thickness (at most two zeros), "
            f"got thicknesses={thicknesses} in {envelope_ref}"
        )

    return errors
