from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Literal, NamedTuple
import os

import pandas as pd

from cea.datamanagement.database import BaseDatabase, BaseDatabaseCollection

# Surface heat transfer coefficients (internal/external) per element
# Values in m2·K/W. Adjust as needed to match standards used.
SURFACE_RESISTANCES: dict[str, dict[str, float]] = {
    "wall": {"internal": 1.0 / 8.0, "external": 1.0 / 25.0},
    "roof": {"internal": 1.0 / 10.0, "external": 1.0 / 25.0},
    "floor": {"internal": 1.0 / 6.0, "external": 1.0 / 25.0},
}

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


# --- Envelope derivation -------------------------------------------------------------
# Material layers are canonical: U and the GHG columns are derived from them. These live
# at module level because both reading (Envelope.from_locator) and writing (the database
# editor, via apply_material_derivation) must derive identically -- a second copy of this
# arithmetic would drift from the first.

def _to_float(value: Any) -> float | None:
    """Safely parse numeric value to float or None when missing/NaN/invalid."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _calc_u(materials: list[dict[str, Any]], kind: Literal["floor", "roof", "wall"]) -> float | None:
    """Compute U-value as 1 / sum(thickness_i / conductivity_i).

    Returns None if any layer lacks required data or resistance is zero.
    """
    total_thermal_resistance = 0.0
    has_conductivity_values = False
    for m in materials:
        conductivity_value = _to_float(m.get("thermal_conductivity"))
        thickness_value = _to_float(m.get("thickness"))
        # Skip if missing; allow zero thickness (contributes zero resistance)
        if conductivity_value is None or thickness_value is None:
            continue
        if conductivity_value <= 0:
            continue
        total_thermal_resistance += thickness_value / conductivity_value
        has_conductivity_values = True
    if not has_conductivity_values or total_thermal_resistance == 0:
        return None
    # add internal and external surface resistances based on element type
    coeffs = SURFACE_RESISTANCES.get(kind, {"internal": 0.0, "external": 0.0})
    total_thermal_resistance += coeffs["internal"] + coeffs["external"]
    return 1.0 / total_thermal_resistance


def _calc_ghg(
    materials: list[dict[str, Any]],
) -> tuple[float | None, float | None, float | None, float | None]:
    """Compute GHG per m2 for kg-based entries.

    Uses mass_per_m2 = density * thickness (m, kg/m3 → kg/m2).
    Disallows any material with unit 'm2'.
    Returns tuple: (total, production, demolition, biogenic). Each may be None if
    insufficient data. The demolition term comes from the material's end-of-life column,
    `GHG_emission_recycling`, which keeps the name KBOB publishes it under.
    """
    total_emissions = 0.0
    production_emissions = 0.0
    demolition_emissions = 0.0
    biogenic_emissions = 0.0

    any_total = False
    any_production = False
    any_demolition = False
    any_biogenic = False

    for m in materials:
        unit = m.get("unit")
        density_value = _to_float(m.get("density"))
        ghg_total_value = _to_float(m.get("GHG_emission_total"))
        ghg_production_value = _to_float(m.get("GHG_emission_production"))
        ghg_demolition_value = _to_float(m.get("GHG_emission_recycling"))
        bio_carbon_value = _to_float(m.get("biogenic_carbon_in_product"))
        thickness_value = _to_float(m.get("thickness"))

        if unit == "kg":
            if density_value is None or thickness_value is None or thickness_value < 0:
                continue
            mass_per_m2 = density_value * thickness_value
            if ghg_total_value is not None:
                total_emissions += ghg_total_value * mass_per_m2
                any_total = True
            if ghg_production_value is not None:
                production_emissions += ghg_production_value * mass_per_m2
                any_production = True
            if ghg_demolition_value is not None:
                demolition_emissions += ghg_demolition_value * mass_per_m2
                any_demolition = True
            if bio_carbon_value is not None:
                biogenic_emissions += bio_carbon_value * mass_per_m2
                any_biogenic = True
        elif str(unit).lower() == "m2":
            # Disallow m2 unit entries in material database
            raise ValueError(
                "Material unit 'm2' is not supported. Please provide entries with unit 'kg'."
            )
        else:
            # Unknown unit: skip
            continue

    return (
        total_emissions if any_total else None,
        production_emissions if any_production else None,
        demolition_emissions if any_demolition else None,
        biogenic_emissions if any_biogenic else None,
    )


MATERIAL_COLS = (
    "material_name_1", "thickness_1_m",
    "material_name_2", "thickness_2_m",
    "material_name_3", "thickness_3_m",
)


class DerivedValues(NamedTuple):
    """The direct properties a row's material layers produce.

    Named rather than a bare tuple because the columns are written by zipping this against
    `DERIVED_COLS_BY_KIND`; with five like-typed floats, a positional slip would silently
    file embodied carbon under the wrong phase.
    """

    u: float | None
    ghg_total: float | None
    ghg_biogenic: float | None
    ghg_production: float | None
    ghg_demolition: float | None


class DerivedColumns(NamedTuple):
    """The column names holding those properties, per envelope kind."""

    u: str
    ghg_total: str
    ghg_biogenic: str
    ghg_production: str
    ghg_demolition: str


# Values and columns are zipped together, so the two must stay in the same field order.
assert DerivedColumns._fields == DerivedValues._fields

# `GHG_*_kgCO2m2` is the whole lifecycle; production and demolition split it and are
# optional -- a database with no MATERIALS.csv carries the total alone. Only `u` and
# `ghg_total` are ever required of a database; the rest are derived, which is why they are
# read by name rather than by position.
DERIVED_COLS_BY_KIND: dict[str, DerivedColumns] = {
    "floor": DerivedColumns(
        u="U_base",
        ghg_total="GHG_floor_kgCO2m2",
        ghg_biogenic="GHG_biogenic_floor_kgCO2m2",
        ghg_production="GHG_production_floor_kgCO2m2",
        ghg_demolition="GHG_demolition_floor_kgCO2m2",
    ),
    "roof": DerivedColumns(
        u="U_roof",
        ghg_total="GHG_roof_kgCO2m2",
        ghg_biogenic="GHG_biogenic_roof_kgCO2m2",
        ghg_production="GHG_production_roof_kgCO2m2",
        ghg_demolition="GHG_demolition_roof_kgCO2m2",
    ),
    "wall": DerivedColumns(
        u="U_wall",
        ghg_total="GHG_wall_kgCO2m2",
        ghg_biogenic="GHG_biogenic_wall_kgCO2m2",
        ghg_production="GHG_production_wall_kgCO2m2",
        ghg_demolition="GHG_demolition_wall_kgCO2m2",
    ),
}

# The `EnvelopeLookup` field names for everything materials derive. Anything that copies an
# envelope row and edits its layers must blank these, or the copy keeps values describing the
# previous composition and the loader's cross-check rejects it (issue #4059).
DERIVED_LOOKUP_FIELDS = (
    "U",
    "GHG_kgCO2m2",
    "GHG_biogenic_kgCO2m2",
    "GHG_production_kgCO2m2",
    "GHG_demolition_kgCO2m2",
)


CROSS_CHECK_REL_TOLERANCE = 0.01  # 1% drift between materials-derived and on-disk


def _is_blank_name(name: Any) -> bool:
    return name is None or pd.isna(name) or str(name).strip() == ""


def _row_has_usable_material_layer(row: pd.Series) -> bool:
    """A row is usable iff at least one layer pairs a material name with a
    positive thickness. A slot with no thickness, or a thickness of zero, is unused --
    the remaining slots do not have to be filled in. A positive thickness with no
    material name is malformed, not unused: silently dropping that layer would
    understate the construction.
    """
    usable_layers = 0
    for i in (1, 2, 3):
        t = _to_float(row.get(f"thickness_{i}_m"))
        if t is None or t <= 0:
            continue
        if _is_blank_name(row.get(f"material_name_{i}")):
            return False
        usable_layers += 1
    return usable_layers >= 1


def _row_has_complete_direct_set(row: pd.Series, kind: str) -> bool:
    # Biogenic carbon was added after the rest of the legacy schema; v3 datasets
    # (e.g. the migrated reference-case-open) ship without it. Require only U and
    # GHG total; biogenic defaults to 0 below when missing, and the production/demolition
    # split is only ever derived, never demanded of a database.
    cols = DERIVED_COLS_BY_KIND[kind]
    return (
        _to_float(row.get(cols.u)) is not None
        and _to_float(row.get(cols.ghg_total)) is not None
    )


def _check_direct_split_sums(row: pd.Series, kind: str, code: str) -> str | None:
    """Does a hand-supplied production/demolition split agree with the total it splits?

    Only applies to values already on disk: derived rows get both parts from the same
    calculation, so they agree by construction. Returns a message, or None when the row
    carries no split (the common case) or the split adds up.
    """
    cols = DERIVED_COLS_BY_KIND[kind]
    total = _to_float(row.get(cols.ghg_total))
    production = _to_float(row.get(cols.ghg_production))
    demolition = _to_float(row.get(cols.ghg_demolition))
    if total is None or production is None or demolition is None:
        return None

    drift = _relative_drift(total, production + demolition)
    if drift <= CROSS_CHECK_REL_TOLERANCE:
        return None
    return (
        f"  row '{code}': {cols.ghg_production} + {cols.ghg_demolition} = "
        f"{production + demolition:.4g} but {cols.ghg_total} = {total:.4g} "
        f"(relative drift={drift * 100:.2f}%, tolerance "
        f"{CROSS_CHECK_REL_TOLERANCE * 100:.1f}%). The split must add up to the total."
    )


def _gather_materials_for_row(row: pd.Series, material_db: pd.DataFrame | None) -> list[dict[str, Any]] | None:
    """Return list of layer dicts joined with MATERIALS.csv, or None if any layer fails to resolve."""
    if material_db is None:
        return None
    mats: list[dict[str, Any]] = []
    for i in (1, 2, 3):
        name = row.get(f"material_name_{i}")
        thickness = _to_float(row.get(f"thickness_{i}_m"))
        if thickness is None or thickness <= 0:
            # Unused slot (blank or zero thickness): contributes nothing; skip joining
            continue
        if _is_blank_name(name):
            return None
        kb_match = material_db[material_db["name"] == name]
        if kb_match.empty:
            return None
        rec = kb_match.iloc[0]
        mats.append({
            "name": name,
            "thickness": thickness,
            "thermal_conductivity": rec.get("thermal_conductivity"),
            "density": rec.get("density"),
            "unit": rec.get("unit"),
            "GHG_emission_total": rec.get("GHG_emission_total"),
            "GHG_emission_production": rec.get("GHG_emission_production"),
            "GHG_emission_recycling": rec.get("GHG_emission_recycling"),
            "biogenic_carbon_in_product": rec.get("biogenic_carbon_in_product"),
        })
    return mats


def _derive_row_values(
    row: pd.Series,
    kind: Literal["floor", "roof", "wall"],
    material_db: pd.DataFrame | None,
) -> DerivedValues | None:
    """The direct properties a row's material layers produce.

    ``None`` when the row has no usable layer, or a layer that does not resolve against the
    material database. Ordered to match ``DERIVED_COLS_BY_KIND[kind]``.
    """
    if not _row_has_usable_material_layer(row):
        return None
    materials = _gather_materials_for_row(row, material_db)
    if not materials:
        return None
    ghg_total, ghg_production, ghg_demolition, ghg_biogenic = _calc_ghg(materials)
    return DerivedValues(
        u=_calc_u(materials, kind),
        ghg_total=ghg_total,
        ghg_biogenic=ghg_biogenic,
        ghg_production=ghg_production,
        ghg_demolition=ghg_demolition,
    )


def _relative_drift(disk: float, derived: float) -> float:
    denom = max(abs(disk), abs(derived), 1e-9)
    return abs(derived - disk) / denom


class BaseAssemblyDatabase(BaseDatabase):
    _index: str = 'code'
    
    @classmethod
    def from_locator(cls, locator: InputLocator):
        return cls(**cls._read_mapping(locator, cls._locator_mapping()))

    @classmethod
    def from_dict(cls, data: dict):
        init_args = dict()
        for field in fields(cls):
            value = data.get(field.name, None)
            if value is None:
                init_args[field.name] = None
                continue
            df = pd.DataFrame.from_dict(value, orient='index')
            df.index.name = cls._index
            init_args[field.name] = df
        return cls(**init_args)

    def to_dict(self):
        return self.dataclass_to_dict()
    
    @classmethod
    def _read_mapping(cls, locator: InputLocator, mapping: dict[str, str]) -> dict[str, pd.DataFrame | None]:
        """
        Helper to read multiple CSVs using a mapping {attr_name: locator_method_name}.
        Returns a dict of {attr_name: DataFrame} ready to be passed to the dataclass constructor.
        """
        frames = {}
        for attr, locator_method in mapping.items():
            if isinstance(locator_method, str):
                try:
                    path = getattr(locator, locator_method)()
                except AttributeError:
                    raise ValueError(f"Locator method for {attr} not found: {locator_method}")
            else:
                raise ValueError(f"Locator method for {attr} must be a string label, got {type(locator_method)}")

            try:
                frames[attr] = pd.read_csv(path).set_index(cls._index)
            except FileNotFoundError:
                frames[attr] = None
        return frames


@dataclass
class Envelope(BaseAssemblyDatabase):
    floor: pd.DataFrame | None
    mass: pd.DataFrame | None
    roof: pd.DataFrame | None
    shading: pd.DataFrame | None
    tightness: pd.DataFrame | None
    wall: pd.DataFrame | None
    window: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "floor": "get_database_assemblies_envelope_floor",
            "mass": "get_database_assemblies_envelope_mass",
            "roof": "get_database_assemblies_envelope_roof",
            "shading": "get_database_assemblies_envelope_shading",
            "tightness": "get_database_assemblies_envelope_tightness",
            "wall": "get_database_assemblies_envelope_wall",
            "window": "get_database_assemblies_envelope_window",
        }

    @classmethod
    def from_locator(cls, locator: InputLocator, strict: bool = True):
        """Read the envelope tables.

        With ``strict`` (the default) a row that neither derives from materials nor carries the
        direct properties, or whose cached values contradict its materials, raises. The
        database editor reads with ``strict=False``: refusing to load is right for a
        simulation, but it would leave the user unable to open the only tool that can fix the
        offending row. The problems are still reported, by the database verifier.
        """
        frames = cls._read_mapping(locator, cls._locator_mapping())

        # Record original columns so saving can preserve the on-disk schema.
        # We intentionally avoid a dataclass field to keep the public API stable.
        original_columns: dict[str, list[str]] = {}
        for kind, df in frames.items():
            if isinstance(df, pd.DataFrame):
                original_columns[kind] = list(df.columns)

        # Try to load the material database via locator; if not available, we still
        # keep the raw material-based schema and just cannot derive legacy U/GHG values.
        material_db: pd.DataFrame | None
        try:
            material_db_path = locator.get_database_components_materials()
            material_db = pd.read_csv(material_db_path)
        except (AttributeError, FileNotFoundError):
            material_db = None

        def _ensure_legacy_columns_exist(
            df: pd.DataFrame,
            kind: Literal["floor", "roof", "wall"],
            envelope_ref: str,
        ) -> pd.DataFrame:
            """Per-row dispatch:
            - Material-complete row -> derive U/GHG; if on-disk values also present and drift > 1%, raise.
            - Direct-property-complete row -> leave as-is.
            - Neither -> raise: malformed row.
            """
            df = df.copy()
            derived_cols = DERIVED_COLS_BY_KIND[kind]

            # Make sure derived columns exist so downstream readers never KeyError. Hold them
            # as float: a column read as all-zero ints cannot take a derived value in place.
            for c in derived_cols:
                if c not in df.columns:
                    df[c] = None
                else:
                    df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)

            # Make sure material columns exist (as object/None) so per-row checks don't KeyError.
            for c in MATERIAL_COLS:
                if c not in df.columns:
                    df[c] = None

            drift_errors: list[str] = []
            split_errors: list[str] = []
            malformed: list[str] = []

            for code, row in df.iterrows():
                code_str = str(code)
                has_materials = _row_has_usable_material_layer(row)
                has_direct = _row_has_complete_direct_set(row, kind)

                if not has_materials and not has_direct:
                    malformed.append(code_str)
                    continue

                if not has_materials:
                    # Direct-property only. Fill in a missing biogenic value (legacy schema)
                    # with 0 so downstream readers always get a defined number. The
                    # production/demolition split is left absent rather than invented -- the
                    # timeline reads the total and reports no demolition for such a row.
                    if _to_float(row.get(derived_cols.ghg_biogenic)) is None:
                        df.loc[code_str, derived_cols.ghg_biogenic] = 0.0
                    split_error = _check_direct_split_sums(row, kind, code_str)
                    if split_error:
                        split_errors.append(split_error)
                    continue

                try:
                    derived_values = _derive_row_values(row, kind, material_db)
                except ValueError:
                    # A material this row references cannot be interpreted (an unsupported
                    # unit, say). Fatal for a simulation, but the editor has to open or the
                    # user cannot reach the row to fix it; the verifier reports the problem.
                    if strict:
                        raise
                    continue

                if derived_values is None:
                    # Materials referenced but MATERIALS.csv missing or layer unresolved.
                    # If direct-property is also complete, fall back to it silently.
                    if has_direct:
                        continue
                    malformed.append(code_str)
                    continue

                # Cross-check every on-disk value that is present, column by column. A row
                # that fills in only some of the direct properties is not a complete direct
                # set, but the values it does carry are still claims about this construction
                # -- comparing only complete sets would let them be overwritten in silence.
                conflicting: set[str] = set()
                for col, derived in zip(derived_cols, derived_values):
                    if derived is None:
                        continue
                    disk = _to_float(row.get(col))
                    if disk is None:
                        continue
                    drift = _relative_drift(disk, derived)
                    if drift > CROSS_CHECK_REL_TOLERANCE:
                        conflicting.add(col)
                        drift_errors.append(
                            f"  {envelope_ref} row '{code_str}': column '{col}' "
                            f"on-disk={disk:.4g} but derived-from-materials={derived:.4g} "
                            f"(relative drift={drift * 100:.2f}%, tolerance {CROSS_CHECK_REL_TOLERANCE * 100:.1f}%). "
                            f"Materials are canonical. Refresh the on-disk cache or correct the material composition."
                        )

                # Materials win: write derived values (overwriting any stale cache within
                # tolerance). A conflicting value is left as it is on disk -- in strict mode
                # the raise below stops the load anyway, and in lenient mode the editor must
                # show what the file actually holds rather than a silently corrected number.
                for col, derived in zip(derived_cols, derived_values):
                    if derived is not None and col not in conflicting:
                        df.loc[code_str, col] = derived

            if not strict:
                # Leave the offending rows exactly as they are on disk: no raise, so the editor
                # can open a database that needs fixing. The verifier still reports them.
                return df

            if split_errors:
                raise ValueError(
                    f"Envelope {kind} ({envelope_ref}) has {len(split_errors)} row(s) whose "
                    f"production/demolition split does not add up:\n" + "\n".join(split_errors)
                )

            if drift_errors:
                raise ValueError(
                    f"Envelope cross-check failed for {kind} ({len(drift_errors)} row(s) out of tolerance):\n"
                    + "\n".join(drift_errors)
                )
            if malformed:
                raise ValueError(
                    f"Envelope {kind} ({envelope_ref}) has {len(malformed)} malformed row(s) — "
                    f"each row must have either the full direct-property set "
                    f"({derived_cols.u}, {derived_cols.ghg_total}) "
                    f"or at least one material layer "
                    f"(a material_name_N with a thickness_N_m greater than zero). "
                    f"Affected codes: {', '.join(malformed)}"
                )

            return df

        # Add derived columns in-memory for compatibility; keep the original schema for saving.
        locator_methods = cls._locator_mapping()
        for kind, df in list(frames.items()):
            if df is None or kind not in DERIVED_COLS_BY_KIND:
                continue
            try:
                envelope_ref = getattr(locator, locator_methods[kind])()
            except Exception:
                envelope_ref = f"<{kind}>"
            frames[kind] = _ensure_legacy_columns_exist(df, kind, envelope_ref)  # type: ignore[arg-type]

        env = cls(**frames)
        setattr(env, "_original_columns", original_columns)
        # Stored material database used for deriving legacy values (if available).
        setattr(env, "_material_db", material_db)
        return env

    def apply_material_derivation(
        self, material_db: pd.DataFrame | None
    ) -> list[dict[str, Any]]:
        """Recompute U/GHG from the material layers, and report what that overwrites.

        Materials are canonical, so any row with a usable layer has its derived columns
        rewritten here. Without this, saving an edited layer keeps the U/GHG that described
        the *previous* composition, and the file no longer loads.

        Returns one entry per column whose stored value disagreed with the layers by more
        than the cross-check tolerance. Values that were empty, or already agreed, are not
        reported -- filling a blank or confirming a match is not something to warn about.
        """
        if material_db is None:
            return []
        # Read from a CSV, `name` is a column; rebuilt from the editor payload it is the
        # index. The layer lookup needs the column form.
        if "name" not in material_db.columns and material_db.index.name == "name":
            material_db = material_db.reset_index()

        conflicts: list[dict[str, Any]] = []
        for kind, derived_cols in DERIVED_COLS_BY_KIND.items():
            df = getattr(self, kind, None)
            if df is None:
                continue
            # Up front, not per row: a table with no layers at all still gains the columns,
            # and creating one mid-iteration would modify the frame being walked.
            for col in derived_cols:
                if col not in df.columns:
                    df[col] = None

            for code, row in df.iterrows():
                derived_values = _derive_row_values(row, kind, material_db)
                if derived_values is None:
                    continue

                for col, derived in zip(derived_cols, derived_values):
                    if derived is None:
                        continue
                    stored = _to_float(row.get(col))
                    if (
                        stored is not None
                        and _relative_drift(stored, derived) > CROSS_CHECK_REL_TOLERANCE
                    ):
                        conflicts.append({
                            "table": kind,
                            "code": str(code),
                            "column": col,
                            "stored": stored,
                            "derived": derived,
                        })
                    df.loc[code, col] = derived

        return conflicts

    def save(self, locator: InputLocator) -> None:
        """Save envelope databases while preserving the on-disk schema.

        `BaseDatabase.save` trims columns to the (legacy) schema in `cea.schemas`, which
        would drop material-based columns. For Envelope, we instead persist the columns that
        were present when the CSV was loaded, plus the values derived from the material
        layers -- writing those back is what lets a reader see the production/demolition
        split without re-deriving it.
        """
        mapping = self._locator_mapping()
        original_columns: dict[str, list[str]] = getattr(self, "_original_columns", {})

        for kind, locator_method in mapping.items():
            df = getattr(self, kind)
            if df is None:
                continue

            try:
                path = getattr(locator, locator_method)()
            except AttributeError:
                raise ValueError(f"Locator method for {kind} not found: {locator_method}")

            out = df.copy()
            cols = original_columns.get(kind)
            if cols:
                # Ensure all original columns exist (fill missing with None)
                for c in cols:
                    if c not in out.columns:
                        out[c] = None
                # Append the derived columns the file did not have, keeping their declared
                # order rather than whatever order they were added to the frame.
                derived = [
                    c
                    for c in DERIVED_COLS_BY_KIND.get(kind, ())
                    if c not in cols and c in out.columns
                ]
                out = out[cols + derived]

            os.makedirs(os.path.dirname(path), exist_ok=True)
            out.to_csv(path)

@dataclass
class HVAC(BaseAssemblyDatabase):
    controller: pd.DataFrame | None
    cooling: pd.DataFrame | None
    heating: pd.DataFrame | None
    hot_water: pd.DataFrame | None
    ventilation: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "controller": "get_database_assemblies_hvac_controller",
            "cooling": "get_database_assemblies_hvac_cooling",
            "heating": "get_database_assemblies_hvac_heating",
            "hot_water": "get_database_assemblies_hvac_hot_water",
            "ventilation": "get_database_assemblies_hvac_ventilation",
        }

@dataclass
class Supply(BaseAssemblyDatabase):
    cooling: pd.DataFrame | None
    heating: pd.DataFrame | None
    hot_water: pd.DataFrame | None
    electricity: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "cooling": "get_database_assemblies_supply_cooling",
            "heating": "get_database_assemblies_supply_heating",
            "hot_water": "get_database_assemblies_supply_hot_water",
            "electricity": "get_database_assemblies_supply_electricity",
        }

@dataclass
class Assemblies(BaseDatabaseCollection):
    envelope: Envelope
    hvac: HVAC
    supply: Supply

    @classmethod
    def from_locator(cls, locator: InputLocator, strict: bool = True):
        return cls(
            envelope=Envelope.from_locator(locator, strict=strict),
            hvac=HVAC.from_locator(locator),
            supply=Supply.from_locator(locator)
        )

    def to_dict(self):
        return self.dataclass_to_dict()
