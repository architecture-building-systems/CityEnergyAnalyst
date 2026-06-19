from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Literal
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
    def from_locator(cls, locator: InputLocator):
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
            Returns tuple: (total, production, recycling, biogenic). Each may be None if insufficient data.
            """
            total_emissions = 0.0
            production_emissions = 0.0
            recycling_emissions = 0.0
            biogenic_emissions = 0.0

            any_total = False
            any_production = False
            any_recycling = False
            any_biogenic = False

            for m in materials:
                unit = m.get("unit")
                density_value = _to_float(m.get("density"))
                ghg_total_value = _to_float(m.get("GHG_emission_total"))
                ghg_production_value = _to_float(m.get("GHG_emission_production"))
                ghg_recycling_value = _to_float(m.get("GHG_emission_recycling"))
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
                    if ghg_recycling_value is not None:
                        recycling_emissions += ghg_recycling_value * mass_per_m2
                        any_recycling = True
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
                recycling_emissions if any_recycling else None,
                biogenic_emissions if any_biogenic else None,
            )

        MATERIAL_COLS = (
            "material_name_1", "thickness_1_m",
            "material_name_2", "thickness_2_m",
            "material_name_3", "thickness_3_m",
        )

        # Per-component legacy (direct-property) columns that materials derive.
        DERIVED_COLS_BY_KIND: dict[str, tuple[str, str, str]] = {
            "floor": ("U_base", "GHG_floor_kgCO2m2", "GHG_biogenic_floor_kgCO2m2"),
            "roof": ("U_roof", "GHG_roof_kgCO2m2", "GHG_biogenic_roof_kgCO2m2"),
            "wall": ("U_wall", "GHG_wall_kgCO2m2", "GHG_biogenic_wall_kgCO2m2"),
        }

        CROSS_CHECK_REL_TOLERANCE = 0.01  # 1% drift between materials-derived and on-disk

        def _row_has_complete_material_set(row: pd.Series) -> bool:
            """A row is material-complete iff all 3 layers have both name and thickness,
            zero-thickness slots are allowed (with empty name) for up to 2 layers."""
            non_zero_count = 0
            for i in (1, 2, 3):
                name = row.get(f"material_name_{i}")
                thickness = row.get(f"thickness_{i}_m")
                t = _to_float(thickness)
                if t is None:
                    return False
                if t > 0:
                    if pd.isna(name) or name is None or str(name).strip() == "":
                        return False
                    non_zero_count += 1
                # t == 0 is allowed regardless of name
            return non_zero_count >= 1

        def _row_has_complete_direct_set(row: pd.Series, kind: str) -> bool:
            # Biogenic carbon was added after the rest of the legacy schema; v3 datasets
            # (e.g. the migrated reference-case-open) ship without it. Require only U and
            # GHG total; biogenic defaults to 0 below when missing.
            u_col, ghg_col, _bio_col = DERIVED_COLS_BY_KIND[kind]
            return (
                _to_float(row.get(u_col)) is not None
                and _to_float(row.get(ghg_col)) is not None
            )

        def _gather_materials_for_row(row: pd.Series) -> list[dict[str, Any]] | None:
            """Return list of layer dicts joined with MATERIALS.csv, or None if any layer fails to resolve."""
            if material_db is None:
                return None
            mats: list[dict[str, Any]] = []
            for i in (1, 2, 3):
                name = row.get(f"material_name_{i}")
                thickness = _to_float(row.get(f"thickness_{i}_m"))
                if thickness is None:
                    return None
                if thickness == 0:
                    # Zero-thickness slot: contributes nothing; skip joining
                    continue
                if pd.isna(name) or name is None:
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

        def _relative_drift(disk: float, derived: float) -> float:
            denom = max(abs(disk), abs(derived), 1e-9)
            return abs(derived - disk) / denom

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

            # Make sure derived columns exist so downstream readers never KeyError.
            for c in derived_cols:
                if c not in df.columns:
                    df[c] = None

            # Make sure material columns exist (as object/None) so per-row checks don't KeyError.
            for c in MATERIAL_COLS:
                if c not in df.columns:
                    df[c] = None

            drift_errors: list[str] = []
            malformed: list[str] = []

            for code, row in df.iterrows():
                code_str = str(code)
                has_materials = _row_has_complete_material_set(row)
                has_direct = _row_has_complete_direct_set(row, kind)

                if not has_materials and not has_direct:
                    malformed.append(code_str)
                    continue

                if not has_materials:
                    # Direct-property only. Fill in a missing biogenic value (legacy schema)
                    # with 0 so downstream readers always get a defined number.
                    bio_col = derived_cols[2]
                    if _to_float(row.get(bio_col)) is None:
                        df.loc[code_str, bio_col] = 0.0
                    continue

                mats = _gather_materials_for_row(row)
                if not mats:
                    # Materials referenced but MATERIALS.csv missing or layer unresolved.
                    # If direct-property is also complete, fall back to it silently.
                    if has_direct:
                        continue
                    malformed.append(code_str)
                    continue

                u_derived = _calc_u(mats, kind)
                ghg_total, _ghg_prod, _ghg_recyc, ghg_bio = _calc_ghg(mats)
                derived_values = (u_derived, ghg_total, ghg_bio)

                # Cross-check against on-disk values when present.
                if has_direct:
                    for col, derived in zip(derived_cols, derived_values):
                        if derived is None:
                            continue
                        disk = _to_float(row.get(col))
                        if disk is None:
                            continue
                        drift = _relative_drift(disk, derived)
                        if drift > CROSS_CHECK_REL_TOLERANCE:
                            drift_errors.append(
                                f"  {envelope_ref} row '{code_str}': column '{col}' "
                                f"on-disk={disk:.4g} but derived-from-materials={derived:.4g} "
                                f"(relative drift={drift * 100:.2f}%, tolerance {CROSS_CHECK_REL_TOLERANCE * 100:.1f}%). "
                                f"Materials are canonical. Refresh the on-disk cache or correct the material composition."
                            )

                # Materials win: write derived values (overwriting any stale cache within tolerance).
                for col, derived in zip(derived_cols, derived_values):
                    if derived is not None:
                        df.loc[code_str, col] = derived

            if drift_errors:
                raise ValueError(
                    f"Envelope cross-check failed for {kind} ({len(drift_errors)} row(s) out of tolerance):\n"
                    + "\n".join(drift_errors)
                )
            if malformed:
                raise ValueError(
                    f"Envelope {kind} ({envelope_ref}) has {len(malformed)} malformed row(s) — "
                    f"each row must have either the full direct-property set "
                    f"({', '.join(derived_cols)}) or the full material set "
                    f"({', '.join(MATERIAL_COLS)}). Affected codes: {', '.join(malformed)}"
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

    def save(self, locator: InputLocator) -> None:
        """Save envelope databases while preserving the on-disk schema.

        `BaseDatabase.save` trims columns to the (legacy) schema in `cea.schemas`, which
        would drop material-based columns. For Envelope, we instead persist only the
        columns that were present when the CSV was loaded.
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
                out = out[cols]

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
    def from_locator(cls, locator: InputLocator):
        return cls(
            envelope=Envelope.from_locator(locator),
            hvac=HVAC.from_locator(locator),
            supply=Supply.from_locator(locator)
        )

    def to_dict(self):
        return self.dataclass_to_dict()
