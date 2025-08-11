"""
construction_helper
====================

Purpose
-------
Create simple, user-driven envelope constructions (wall, roof, floor) and append them to a
scenario's ENVELOPE databases. The goal is to let urban designers specify only high-level
choices (prefix, database region, structure, insulation type and thickness, cladding), while
the tool deterministically assembles a 3-layer wall, a roof, and a floor, and computes a
single embodied GHG value per m² for each construction.

Scope and behavior
------------------
- Currently supports the Swiss KBOB dataset (region = "Switzerland").
- Picks representative materials by keyword search in KBOB and computes GHG/m² from
    material GHG intensities, density and assumed thicknesses.
- Appends exactly one line each to ENVELOPE_WALL.csv, ENVELOPE_ROOF.csv and ENVELOPE_FLOOR.csv
    in the active scenario via InputLocator.
- Writes concise descriptions logging the materials chosen. U-values are placeholder heuristics
    and may be refined later.

Extensibility
-------------
The selection and unit handling are contained in small helpers so that new regions/databases
with different column names or units can be added by implementing alternative pickers and
converters and branching on the config's database-region.

Usage
-----
This module is registered as a CEA script (construction-helper). When called, it reads
the [construction-helper] section of the config and appends the new constructions to the
scenario DBs.
"""

import os
import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator


def _read_csv_safely(path: str) -> pd.DataFrame:
    """Read a CSV file from a path and return a DataFrame.

    :param path: Absolute path to the CSV file.
    :type path: str
    :raises FileNotFoundError: If the file does not exist.
    :returns: The parsed CSV as a DataFrame.
    :rtype: pandas.DataFrame
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _save_csv(df: pd.DataFrame, path: str) -> None:
    """Write a DataFrame to CSV, creating parent folders if needed.

    :param df: Data to save.
    :type df: pandas.DataFrame
    :param path: Absolute path where to write the CSV.
    :type path: str
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def _load_fallback_material_db() -> pd.DataFrame:
    """Load the built-in fallback material thermal properties database.

    Columns: key, name, k_W_mK, density_kg_m3, cp_J_kgK
    """
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
    path = os.path.join(base, "material_thermal_properties.csv")
    return pd.read_csv(path)


def _map_kbob_to_material_key(name_en: str | None) -> str | None:
    """Map a KBOB English name to our fallback material key.

    Very lightweight keyword rules; returns None if unknown.
    """
    if not name_en:
        return None
    n = name_en.lower()
    # Insulations
    if "xps" in n or "extruded polystyrene" in n:
        return "XPS"
    if "eps" in n or "expanded polystyrene" in n:
        return "EPS"
    if "polyurethane" in n or "pur" in n:
        return "PUR"
    if "rock wool" in n or "stone wool" in n or "steinwolle" in n:
        return "rock_wool"
    if "glass wool" in n or "glaswolle" in n:
        return "glass_wool"
    if "hemp" in n:
        return "hemp"
    # Structures / claddings
    if "concrete" in n or "beton" in n:
        return "concrete"
    if "brick" in n or "backstein" in n:
        return "brick"
    if "sand-lime" in n or "kalksandstein" in n:
        return "masonry_sand_lime"
    if "spruce" in n or "wood" in n or "holz" in n:
        return "wood"
    if "aluminum" in n or "aluminium" in n:
        return "aluminium"
    if "steel" in n:
        return "steel"
    if "plaster" in n or "putz" in n or "gips" in n:
        return "plaster"
    if "glass" in n:
        return "glass"
    if "stone" in n or "limestone" in n or "naturstein" in n:
        return "stone"
    return None


def _u_value_from_layers(layers: list[tuple[str, float]], mat_db: pd.DataFrame) -> float:
    """Compute U-value [W/m2K] from layers using fallback material k values.

    layers: list of (material_key, thickness_m). Unknown keys are ignored.
    Adds internal/external surface resistances (Rsi ~0.13, Rse ~0.04) for walls/roofs; for floors, caller may adjust.
    """
    # Surface resistances typical for vertical surfaces; caller can override post-multiply for roofs/floors if needed
    Rsi = 0.13
    Rse = 0.04
    R_tot = Rsi + Rse
    # Build quick lookup
    db = {row["key"]: float(row["k_W_mK"]) for _, row in mat_db.iterrows()}
    for key, t in layers:
        if not key or not isinstance(t, (int, float)) or t <= 0:
            continue
        k = db.get(key)
        if k and k > 0:
            R_tot += t / k
    if R_tot <= 0:
        return 5.0
    return round(1.0 / R_tot, 3)


def _pick_material_rows_kbob(
    kbob: pd.DataFrame, insulation: str, cladding: str, structure: str
) -> tuple[pd.Series | None, pd.Series | None, pd.Series | None]:
    """Pick representative KBOB materials for insulation, cladding, and structure by keyword search.

    :param kbob: KBOB materials table.
    :type kbob: pandas.DataFrame
    :param insulation: Insulation type requested (e.g., "EPS", "XPS", "PUR", "rock wool").
    :type insulation: str
    :param cladding: Cladding type requested (e.g., "plaster", "aluminium", "none").
    :type cladding: str
    :param structure: Structural type requested (e.g., "concrete", "masonry", "wood", "steel").
    :type structure: str
    :returns: A tuple (insulation_row, cladding_row, structure_row) with the first match per category, or None if not found.
    :rtype: tuple[pandas.Series | None, pandas.Series | None, pandas.Series | None]
    """

    def pick_by_keywords(keywords):
        mask = pd.Series(False, index=kbob.index)
        for col in ["NameEnglish", "name", "NameGerman"]:
            if col in kbob.columns:
                for kw in keywords:
                    mask = mask | kbob[col].fillna("").str.contains(
                        kw, case=False, na=False, regex=False
                    )
        row = kbob[mask].head(1)
        return row.iloc[0] if len(row) else None

    ins_map: dict[str, tuple[str, ...]] = {
        "EPS": ("Polystyrene expands (EPS)", "Polystyrol expandiert (EPS)"),
        "XPS": ("Polystyrene extruded (XPS)", "Polystyrol extrudiert (XPS)"),
        "PUR": ("Polyurethane (PUR", "Polyurethan (PUR"),
        "rock wool": ("Rock wool", "Steinwolle"),
        "glass wool": ("Glass wool", "Glaswolle"),
        "hemp": ("Hemp fibre", "Hanf"),
    }

    clad_map: dict[str, tuple[str, ...]] = {
        "plaster": ("Cement plaster", "Gips", "Putz"),
        "aluminium": ("Aluminum sheet", "Aluminiumblech", "Facade plate, aluminum"),
        "steel": ("Steel sheet", "Stahlblech"),
        "glass": ("Flat glass",),
        "stone": ("Limestone slab", "Natursteinplatte"),
        "brick": ("Brick", "Backstein"),
        "wood": ("3-layer solid wood panel", "Massivholz"),
        "none": tuple(),
    }

    struct_map: dict[str, tuple[str, ...]] = {
        "concrete": ("Building construction concrete", "Beton"),
        "steel": ("Steel profile", "Stahlprofil"),
        "wood": ("Solid wood spruce", "Massivholz Fichte"),
        "masonry": ("Brick", "Backstein", "Sand-lime brick", "Kalksandstein"),
    }

    ins = (
        pick_by_keywords(ins_map.get(insulation, (insulation,))) if insulation else None
    )
    cld = (
        None
        if cladding == "none"
        else pick_by_keywords(clad_map.get(cladding, (cladding,)))
    )
    stc = (
        pick_by_keywords(struct_map.get(structure, (structure,))) if structure else None
    )
    return ins, cld, stc


def _ghg_layer_components_per_m2(
    row: pd.Series | None,
    material_key: str | None,
    thickness_m: float,
    mat_db: pd.DataFrame,
) -> tuple[float, float]:
    """Compute production+disposal and biogenic GHG per m² for a layer using fallback densities.

    - Uses KBOB's GHGEmbodied (production) and GHGEoL (disposal) factors.
    - Interprets the base unit via row["DensityUnit"], but never uses KBOB density values.
    - Converts to per-m² using fallback density when needed.

    Returns (total_ghg, biogenic_ghg) per m². If biogenic not available, returns 0.0 for it.
    """
    if row is None or pd.isna(thickness_m) or thickness_m <= 0:
        return 0.0, 0.0
    ghg_prod = float(row.get("GHGEmbodied", 0) or 0)
    ghg_eol = float(row.get("GHGEoL", 0) or 0)
    base_unit = str(row.get("DensityUnit", "")).strip().lower()

    # Lookup fallback density
    rho = None
    if material_key:
        rec = mat_db.loc[mat_db["key"] == material_key]
        if not rec.empty:
            rho = float(rec.iloc[0]["density_kg_m3"])

    def to_m2(value: float) -> float:
        if value == 0:
            return 0.0
        if base_unit in ("kg",):
            if rho and rho > 0:
                mass_per_m2 = rho * thickness_m  # kg/m3 * m = kg/m2
                return value * mass_per_m2
            return 0.0
        if base_unit in ("m3",):
            return value * thickness_m
        if base_unit in ("m2",):
            return value
        # Unknown base; assume per m2
        return value

    total = to_m2(ghg_prod) + to_m2(ghg_eol)
    biogenic = 0.0  # Not available in KBOB file
    return float(total), float(biogenic)


def _compose_wall_ghg(
    kbob: pd.DataFrame,
    insulation: str,
    cladding: str,
    structure: str,
    ins_thickness: float,
    structure_thickness: float,
) -> tuple[float, float, str]:
    """Compose a 3-layer wall (cladding, insulation, structure) and compute GHG/m².

    :param kbob: KBOB materials table.
    :type kbob: pandas.DataFrame
    :param insulation: Insulation type key.
    :type insulation: str
    :param cladding: Cladding type key ("none" allowed).
    :type cladding: str
    :param structure: Structural type key.
    :type structure: str
    :param ins_thickness: Insulation thickness in meters.
    :type ins_thickness: float
    :param structure_thickness: Structure thickness in meters.
    :type structure_thickness: float
    :returns: Tuple of (GHG_wall_kgCO2e_per_m2, description_string).
    :rtype: tuple[float, str]
    """
    ins, cld, stc = _pick_material_rows_kbob(kbob, insulation, cladding, structure)
    mat_db = _load_fallback_material_db()
    # Map to fallback material keys
    ins_key = _map_kbob_to_material_key(_kbob_row_name(ins)) if ins is not None else None
    cld_key = _map_kbob_to_material_key(_kbob_row_name(cld)) if cld is not None else None
    stc_key = _map_kbob_to_material_key(_kbob_row_name(stc)) if stc is not None else None

    ghg, bio = 0.0, 0.0
    g, b = _ghg_layer_components_per_m2(ins, ins_key, ins_thickness, mat_db)
    ghg += g; bio += b
    g, b = _ghg_layer_components_per_m2(cld, cld_key, 0.01, mat_db)
    ghg += g; bio += b
    g, b = _ghg_layer_components_per_m2(stc, stc_key, structure_thickness, mat_db)
    ghg += g; bio += b
    desc_parts = [
        f"cladding={_kbob_row_name(cld)}" if cld is not None else "cladding=none",
        (
            f"insulation={_kbob_row_name(ins)} {ins_thickness*100:.0f}mm"
            if ins is not None
            else "insulation=none"
        ),
        (
            f"structure={_kbob_row_name(stc)} {structure_thickness*100:.0f}mm"
            if stc is not None
            else "structure=none"
        ),
    ]
    return float(ghg), float(bio), ", ".join(desc_parts)


def _compose_roof_ghg(
    kbob: pd.DataFrame,
    insulation: str,
    structure: str,
    ins_thickness: float,
    structure_thickness: float,
) -> tuple[float, float, str]:
    """Compose a roof (insulation + structure) and compute GHG/m².

    :param kbob: KBOB materials table.
    :type kbob: pandas.DataFrame
    :param insulation: Insulation type key.
    :type insulation: str
    :param structure: Structural type key.
    :type structure: str
    :param ins_thickness: Insulation thickness in meters.
    :type ins_thickness: float
    :param structure_thickness: Structural thickness in meters.
    :type structure_thickness: float
    :returns: Tuple of (GHG_roof_kgCO2e_per_m2, description_string).
    :rtype: tuple[float, str]
    """
    ins, _, stc = _pick_material_rows_kbob(kbob, insulation, "none", structure)
    mat_db = _load_fallback_material_db()
    ins_key = _map_kbob_to_material_key(_kbob_row_name(ins)) if ins is not None else None
    stc_key = _map_kbob_to_material_key(_kbob_row_name(stc)) if stc is not None else None
    ghg, bio = 0.0, 0.0
    g, b = _ghg_layer_components_per_m2(ins, ins_key, ins_thickness, mat_db)
    ghg += g; bio += b
    g, b = _ghg_layer_components_per_m2(stc, stc_key, structure_thickness, mat_db)
    ghg += g; bio += b
    desc = []
    if ins is not None:
        desc.append(f"insulation={_kbob_row_name(ins)} {ins_thickness*100:.0f}mm")
    if stc is not None:
        desc.append(f"structure={_kbob_row_name(stc)} {structure_thickness*100:.0f}mm")
    return float(ghg), float(bio), ", ".join(desc)


def _compose_floor_ghg(
    kbob: pd.DataFrame,
    structure: str,
    structure_thickness: float,
    insulation: str,
    ins_thickness: float,
) -> tuple[float, float, str]:
    """Compose a floor (structure + insulation) and compute GHG/m².

    :param kbob: KBOB materials table.
    :type kbob: pandas.DataFrame
    :param structure: Structural type key to use.
    :type structure: str
    :param structure_thickness: Floor structural thickness in meters.
    :type structure_thickness: float
    :param insulation: Insulation type key.
    :type insulation: str
    :param ins_thickness: Insulation thickness in meters.
    :type ins_thickness: float
    :returns: Tuple of (GHG_floor_kgCO2e_per_m2, GHG_biogenic_floor_kgCO2e_per_m2, description_string).
    :rtype: tuple[float, float, str]
    """
    ins_row, _, stc = _pick_material_rows_kbob(
        kbob, insulation=insulation, cladding="none", structure=structure
    )
    mat_db = _load_fallback_material_db()
    ins_key = _map_kbob_to_material_key(_kbob_row_name(ins_row)) if ins_row is not None else None
    stc_key = _map_kbob_to_material_key(_kbob_row_name(stc)) if stc is not None else None
    ghg, bio = 0.0, 0.0
    # insulation (smaller than wall) + structure
    g, b = _ghg_layer_components_per_m2(ins_row, ins_key, ins_thickness, mat_db)
    ghg += g; bio += b
    g, b = _ghg_layer_components_per_m2(stc, stc_key, structure_thickness, mat_db)
    ghg += g; bio += b
    parts = []
    if ins_row is not None and ins_thickness > 0:
        parts.append(f"insulation={_kbob_row_name(ins_row)} {ins_thickness*100:.0f}mm")
    if stc is not None:
        parts.append(f"structure={_kbob_row_name(stc)} {structure_thickness*100:.0f}mm")
    desc = ", ".join(parts) if parts else "structure=none"
    return float(ghg), float(bio), desc


def _thickness_from_choice(choice: str, base_mm: tuple[int, int, int, int]) -> float:
    """Map an insulation thickness choice string to meters using a base tuple.

    :param choice: One of "thick (around 20 cm)", "medium (around 10 cm)", "thin (around 5 cm)", "none".
    :type choice: str
    :param base_mm: A tuple of (thick_mm, medium_mm, thin_mm, none_mm) used to translate the labels.
    :type base_mm: tuple[int, int, int, int]
    :returns: Thickness in meters.
    :rtype: float
    """
    mapping = {
        "thick (around 20 cm)": base_mm[0] / 1000.0,
        "medium (around 10 cm)": base_mm[1] / 1000.0,
        "thin (around 5 cm)": base_mm[2] / 1000.0,
        "none": 0.0,
    }
    return mapping.get(choice, base_mm[1] / 1000.0)


def _kbob_row_name(row: pd.Series | None) -> str:
    """Return a robust display name for a KBOB row supporting multiple column labels."""
    if row is None:
        return ""
    for col in ("NameEnglish", "name", "NameGerman"):
        try:
            if col in row and pd.notna(row[col]):
                return str(row[col])
        except Exception:
            continue
    # Fallback to first non-null string value
    for val in row.values:
        if isinstance(val, str) and val:
            return val
    return ""


def _compute_u_values(
    kbob_df: pd.DataFrame,
    mat_db: pd.DataFrame,
    wall_ins_t: float,
    wall_struct_t: float,
    roof_ins_t: float,
    roof_struct_t: float,
    floor_struct_t: float,
    floor_ins_t: float,
    insulation_type: str,
    cladding_type: str,
    structure_type: str,
) -> tuple[float, float, float]:
    """Derive U-values for wall, roof, floor using material picks mapped to fallback DB.

    Falls back to heuristic bounds if mapping fails.
    """
    # Pick rows to map names to keys
    ins_row, cld_row, stc_row = _pick_material_rows_kbob(
        kbob_df, insulation_type, cladding_type, structure_type
    )
    ins_key = _map_kbob_to_material_key(_kbob_row_name(ins_row)) if ins_row is not None else None
    cld_key = _map_kbob_to_material_key(_kbob_row_name(cld_row)) if cld_row is not None else None
    stc_key = _map_kbob_to_material_key(_kbob_row_name(stc_row)) if stc_row is not None else None

    # Layers for wall: cladding (~10mm), insulation, structure
    wall_layers: list[tuple[str, float]] = []
    if cld_key:
        wall_layers.append((cld_key, 0.01))
    if ins_key:
        wall_layers.append((ins_key, wall_ins_t))
    if stc_key:
        wall_layers.append((stc_key, wall_struct_t))
    u_wall = _u_value_from_layers(wall_layers, mat_db) if wall_layers else 0.8

    # Layers for roof: insulation + structure; reduce with different surface resistances (Rsi~0.10, Rse~0.04)
    roof_layers: list[tuple[str, float]] = []
    if ins_key:
        roof_layers.append((ins_key, roof_ins_t))
    if stc_key:
        roof_layers.append((stc_key, roof_struct_t))
    u_roof = _u_value_from_layers(roof_layers, mat_db) if roof_layers else 0.6
    # For roofs, apply slightly higher surface resistance -> lower U. Approx adjust by 0.9 factor
    u_roof = round(u_roof * 0.9, 3)

    # Floor: insulation (smaller than wall) + structure
    floor_layers: list[tuple[str, float]] = []
    if ins_key and floor_ins_t > 0:
        floor_layers.append((ins_key, floor_ins_t))
    if stc_key:
        floor_layers.append((stc_key, floor_struct_t))
    u_floor = _u_value_from_layers(floor_layers, mat_db) if floor_layers else 0.25
    # Floors to ground often have additional contact resistance; nudge down a bit
    u_floor = max(0.1, round(u_floor * 0.8, 3))

    # Boundaries according to schemas (min 0.1)
    u_wall = max(0.1, round(u_wall, 3))
    u_roof = max(0.1, round(u_roof, 3))
    return u_wall, u_roof, u_floor


def construction_helper(config: Configuration, locator: InputLocator):
    """Entry point for the Construction Helper script.

    Reads the user's high-level choices from the [construction-helper] section, composes wall/roof/floor
    constructions, estimates embodied GHG per m², and appends one row to each ENVELOPE database CSV.

    :param config: Loaded CEA configuration.
    :type config: cea.config.Configuration
    :param locator: Input locator for the active scenario.
    :type locator: cea.inputlocator.InputLocator
    :raises ValueError: If the construction-prefix is missing.
    :raises NotImplementedError: If the selected database-region is not supported yet.
    """
    # Read user intents from config
    section = config.sections["construction-helper"]
    prefix = section.parameters["construction-prefix"].get()
    region = section.parameters["database-region"].get()
    structure_type = section.parameters["building-structure-type"].get()
    insulation_type = section.parameters["insulation-type"].get()
    insulation_thickness_choice = section.parameters["insulation-thickness"].get()
    cladding_type = section.parameters["cladding-type"].get()

    if not prefix:
        raise ValueError("construction-prefix must be set.")

    if region != "Switzerland":
        raise NotImplementedError(f"Region '{region}' not yet supported.")

    kbob_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "analysis",
            "lca",
            "data",
            "kbob_material.csv",
        )
    )
    kbob_df = pd.read_csv(kbob_path)

    wall_ins_t = _thickness_from_choice(
        insulation_thickness_choice, (200, 100, 50, 0)
    )
    roof_ins_t = min(0.4, wall_ins_t * 1.5)  # roof should be thicker than walls

    if structure_type == "concrete":
        wall_struct_t = roof_struct_t = floor_struct_t = 0.20
        structure_for_floor = "concrete"
    elif structure_type == "masonry":
        wall_struct_t = 0.37
        roof_struct_t = 0.30 # concrete roof thicker than floor
        floor_struct_t = 0.20 # concrete floor
        structure_for_floor = "concrete"
    elif structure_type == "wood":
        wall_struct_t = 0.05 # equivalent thickness of a wooden spruce of 100x200 cm and a distance of 60 cm
        roof_struct_t = 0.12 # equivalent thickness of a wooden spruce of 150x400 cm with a distance of 60 cm
        floor_struct_t = 0.09 # equivalent thickness of a wooden spruce of 150x300 cm with a distance of 60 cm plus wood finishing
        structure_for_floor = "wood"
    else:
        wall_struct_t = roof_struct_t = floor_struct_t = 0.20
        structure_for_floor = "concrete"

    wall_ghg, wall_bio_ghg, wall_desc = _compose_wall_ghg(
        kbob_df,
        insulation_type,
        cladding_type,
        structure_type,
        wall_ins_t,
        wall_struct_t,
    )
    roof_ghg, roof_bio_ghg, roof_desc = _compose_roof_ghg(
        kbob_df, insulation_type, structure_type, roof_ins_t, roof_struct_t
    )
    # Floor insulation smaller than wall insulation (e.g., 50%)
    floor_ins_t = max(0.0, wall_ins_t * 0.5)
    floor_ghg, floor_bio_ghg, floor_desc = _compose_floor_ghg(
        kbob_df, structure_for_floor, floor_struct_t, insulation_type, floor_ins_t
    )
    # Compute U-values using fallback material database
    mat_db = _load_fallback_material_db()
    u_wall, u_roof, u_floor = _compute_u_values(
        kbob_df,
        mat_db,
        wall_ins_t,
        wall_struct_t,
        roof_ins_t,
        roof_struct_t,
        floor_struct_t,
        floor_ins_t,
        insulation_type,
        cladding_type,
        structure_type,
    )

    roof_csv = locator.get_database_assemblies_envelope_roof()
    wall_csv = locator.get_database_assemblies_envelope_wall()
    floor_csv = locator.get_database_assemblies_envelope_floor()

    roof_df = _read_csv_safely(roof_csv)
    wall_df = _read_csv_safely(wall_csv)
    floor_df = _read_csv_safely(floor_csv)

    def unique_code(df: pd.DataFrame, col: str, base: str) -> str:
        code = base
        i = 1
        while col in df.columns and (df[col] == code).any():
            i += 1
            code = f"{base}_{i}"
        return code

    roof_code = unique_code(roof_df, "code", f"{prefix}_ROOF")
    wall_code = unique_code(wall_df, "code", f"{prefix}_WALL")
    floor_code = unique_code(floor_df, "code", f"{prefix}_FLOOR")

    roof_row = {
        "description": f"{prefix}: {roof_desc}",
        "code": roof_code,
        "U_roof": u_roof,
        "a_roof": 0.5,
        "e_roof": 0.9,
        "r_roof": 0.5,
    "GHG_roof_kgCO2m2": round(roof_ghg, 2),
    "GHG_biogenic_roof_kgCO2m2": round(roof_bio_ghg, 2),
        "Service_Life_roof": 60,
        "Reference Service life": f"construction-helper ({region})",
        "Reference U-Value": "",
    }

    wall_row = {
        "description": f"{prefix}: {wall_desc}",
        "code": wall_code,
        "U_wall": u_wall,
        "a_wall": 0.3,
        "e_wall": 0.9,
        "r_wall": 0.7,
    "GHG_wall_kgCO2m2": round(wall_ghg, 2),
    "GHG_biogenic_wall_kgCO2m2": round(wall_bio_ghg, 2),
        "Service_Life_wall": 30,
        "Reference Service life": f"construction-helper ({region})",
        "Reference U-Value": "",
    }

    floor_row = {
        "description": f"{prefix}: {floor_desc}",
        "code": floor_code,
        "U_base": u_floor,
    "GHG_floor_kgCO2m2": round(floor_ghg, 2),
    "GHG_biogenic_floor_kgCO2m2": round(floor_bio_ghg, 2),
        "Service_Life_floor": 60,
        "Reference": f"construction-helper ({region})",
    }

    roof_df = pd.concat([roof_df, pd.DataFrame([roof_row])], ignore_index=True)
    wall_df = pd.concat([wall_df, pd.DataFrame([wall_row])], ignore_index=True)
    floor_df = pd.concat([floor_df, pd.DataFrame([floor_row])], ignore_index=True)

    _save_csv(roof_df, roof_csv)
    _save_csv(wall_df, wall_csv)
    _save_csv(floor_df, floor_csv)

    print(f"Appended constructions: {wall_code}, {roof_code}, {floor_code}")


def main(config: Configuration):
    """Script runner wrapper.

    :param config: Loaded CEA configuration to pass to the helper.
    :type config: cea.config.Configuration
    """
    # Note: InputLocator expects a scenario path string, not a Configuration object
    locator = InputLocator(config.scenario)
    construction_helper(config, locator)


if __name__ == "__main__":
    main(Configuration())
