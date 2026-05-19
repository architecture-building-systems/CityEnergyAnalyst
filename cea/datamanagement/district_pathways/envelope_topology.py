from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


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


ALL_MATERIAL_FIELDS: frozenset[str] = frozenset(
    {f"material_name_{i}" for i in (1, 2, 3)}
    | {f"thickness_{i}_m" for i in (1, 2, 3)}
)

# Recipe `component` keys that map to an envelope database. `base` is stored in floor.csv.
_COMPONENT_TO_DB: dict[str, str] = {
    "wall": "wall",
    "roof": "roof",
    "floor": "floor",
    "base": "floor",
}


def is_filled(value: Any) -> bool:
    """True iff value is non-None and not NaN."""
    return value is not None and not (isinstance(value, float) and pd.isna(value))


def row_has_full_material_set(row: pd.Series) -> bool:
    """True iff every material_name_i and thickness_i_m column is present and non-null on the row."""
    return all(col in row.index and is_filled(row.get(col)) for col in ALL_MATERIAL_FIELDS)


def extract_material_fields(fields: dict[str, Any] | None) -> set[str]:
    """Return the subset of ALL_MATERIAL_FIELDS that the recipe `fields` dict sets to non-None."""
    if not fields:
        return set()
    return {f for f, v in fields.items() if v is not None and f in ALL_MATERIAL_FIELDS}


def validate_recipe_against_envelope(
    locator: InputLocator,
    modifications: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    """Pre-flight check for a modification recipe against the scenario's envelope databases.

    For each (archetype, component) entry that touches material fields, look up the source
    envelope row referenced by the archetype's `type_<component>`. If the source row is
    direct-property only (no full material set), the modification must provide the full
    6-field material set — otherwise the modification would silently produce an inconsistent
    row at bake time. Returns a list of human-readable errors (empty list = recipe is valid).

    The same rule is enforced at apply time in
    `cea.datamanagement.district_pathways.pathway_state._apply_state_construction_changes`.
    This helper just catches the problem earlier (e.g. when saving an intervention template).
    """
    errors: list[str] = []

    try:
        archetype_df = pd.read_csv(
            locator.get_database_archetypes_construction_type(),
            index_col="const_type",
        )
    except Exception as exc:  # noqa: BLE001 - surface the underlying error verbatim
        errors.append(f"Cannot read CONSTRUCTION_TYPES.csv: {exc}")
        return errors

    envelope_paths = {
        "wall": locator.get_database_assemblies_envelope_wall(),
        "roof": locator.get_database_assemblies_envelope_roof(),
        "floor": locator.get_database_assemblies_envelope_floor(),
    }
    envelope_dfs: dict[str, pd.DataFrame] = {}
    for db_name, path in envelope_paths.items():
        try:
            envelope_dfs[db_name] = pd.read_csv(path, index_col="code")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Cannot read {db_name} envelope at {path}: {exc}")
            return errors

    for archetype, components in (modifications or {}).items():
        if archetype not in archetype_df.index:
            errors.append(
                f"Recipe references archetype '{archetype}' which is not in CONSTRUCTION_TYPES."
            )
            continue

        for component, fields in (components or {}).items():
            if component not in _COMPONENT_TO_DB:
                continue  # construction_type / supply / hvac edits — not envelope material rules

            material_fields_in_mod = extract_material_fields(fields)
            if not material_fields_in_mod:
                continue  # not a material intervention; nothing to check here

            envelope_df = envelope_dfs[_COMPONENT_TO_DB[component]]
            type_col = f"type_{component}"
            if type_col not in archetype_df.columns:
                errors.append(
                    f"CONSTRUCTION_TYPES has no '{type_col}' column "
                    f"(needed to resolve component '{component}' for archetype '{archetype}')."
                )
                continue

            source_code = archetype_df.at[archetype, type_col]
            if source_code not in envelope_df.index:
                errors.append(
                    f"Archetype '{archetype}' references envelope code '{source_code}' for "
                    f"component '{component}', but '{source_code}' is not in "
                    f"{_COMPONENT_TO_DB[component]}.csv."
                )
                continue

            if row_has_full_material_set(envelope_df.loc[source_code]):
                continue  # material-based source; partial layer overrides are valid

            missing = ALL_MATERIAL_FIELDS - material_fields_in_mod
            if missing:
                errors.append(
                    f"Archetype '{archetype}', component '{component}': source envelope row "
                    f"'{source_code}' is direct-property only, so any material intervention must "
                    f"provide the full 6-field material set. "
                    f"Provided: {sorted(material_fields_in_mod)}. "
                    f"Missing: {sorted(missing)}."
                )

    return errors
