from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

from cea.datamanagement.database import BaseDatabase, BaseDatabaseCollection

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

        # Try to load material database (KBOB) via locator; if not available, skip transformation
        kbob_df = None
        try:
            kbob_path = locator.get_database_assemblies_envelope_material_database()
            kbob_df = pd.read_csv(kbob_path)
        except Exception:
            kbob_df = None

        def _to_float(value: Any) -> float | None:
            """Safely parse numeric value to float or None when missing/NaN/invalid."""
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            try:
                return float(value)
            except Exception:
                return None

        def _calc_u(materials: list[dict[str, Any]]) -> float | None:
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
            return 1.0 / total_thermal_resistance

        def _calc_ghg(
            materials: list[dict[str, Any]],
        ) -> tuple[float | None, float | None]:
            """Compute total and biogenic GHG per m² for kg-based entries.

            Uses mass_per_m2 = density * thickness. Raises if any unit is 'm2'.
            Returns (total, biogenic) or (None, None) if data insufficient.
            """
            total_emissions = 0.0
            biogenic_emissions = 0.0
            has_any_values = False
            for m in materials:
                unit = m.get("unit")
                density_value = _to_float(m.get("density"))
                ghg_total_value = _to_float(m.get("GHG_emission_total"))
                bio_carbon_value = _to_float(m.get("biogenic_carbon_in_product")) or 0.0
                thickness_value = _to_float(m.get("thickness"))

                if unit == "kg":
                    if (
                        density_value is not None
                        and ghg_total_value is not None
                        and thickness_value is not None
                        and thickness_value > 0
                    ):
                        mass_per_m2 = density_value * thickness_value
                        total_emissions += ghg_total_value * mass_per_m2
                        biogenic_emissions += bio_carbon_value * mass_per_m2
                        has_any_values = True
                elif unit == "m2":
                    # Disallow m2 unit entries in material database
                    raise ValueError(
                        "Material unit 'm2' is not supported. Please provide entries with unit 'kg'."
                    )
                else:
                    # Unknown unit: skip
                    pass
            if not has_any_values:
                return (None, None)
            return (total_emissions, biogenic_emissions)

        def _transform(
            df: pd.DataFrame, kind: Literal["floor", "roof", "wall"]
        ) -> pd.DataFrame:
            """Transform material-defined constructions to legacy schema for kind.

            Enforces required columns and units, aggregates validation errors per row,
            and preserves description/code plus reference-like columns.
            """
            if kbob_df is None:
                return df
            # Detect material-based schema and enforce required columns
            required_cols = {
                "material_name_1",
                "material_name_2",
                "material_name_3",
                "thickness_1_m",
                "thickness_2_m",
                "thickness_3_m",
            }
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols.difference(set(df.columns))
                raise ValueError(
                    f"Material-based envelope '{kind}' requires columns: {sorted(required_cols)}. Missing: {sorted(missing)}"
                )

            # Build materials list per row
            out_rows: list[dict[str, Any]] = []
            for _, row in df.iterrows():
                mats: list[dict[str, Any]] = []
                errors: list[str] = []
                for i in (1, 2, 3):
                    name_col = f"material_name_{i}"
                    thick_col = f"thickness_{i}_m"
                    name = row.get(name_col)
                    thickness = row.get(thick_col)
                    if pd.isna(name) or name is None:
                        errors.append(f"Missing material_name_{i}")
                        continue
                    if thickness is None or pd.isna(thickness):
                        errors.append(f"Missing thickness_{i}_m")
                        continue
                    # Lookup in KBOB by 'name'
                    kb_match = kbob_df[kbob_df["name"] == name]
                    mat: dict[str, Any] = {
                        "name": name,
                        "thickness": thickness,
                        "thermal_conductivity": None,
                        "density": None,
                        "unit": None,
                        "GHG_emission_total": None,
                        "biogenic_carbon_in_product": None,
                    }
                    if not kb_match.empty:
                        rec = kb_match.iloc[0]
                        mat["thermal_conductivity"] = rec.get("thermal_conductivity")
                        mat["density"] = rec.get("density")
                        mat["unit"] = rec.get("unit")
                        mat["GHG_emission_total"] = rec.get("GHG_emission_total")
                        mat["biogenic_carbon_in_product"] = rec.get(
                            "biogenic_carbon_in_product"
                        )
                        if str(mat["unit"]).lower() == "m2":
                            errors.append(
                                f"Material '{name}' has unsupported unit 'm2'"
                            )
                    else:
                        errors.append(f"Material '{name}' not found in KBOB database")
                    mats.append(mat)

                # Aggregate validation: must have exactly three layers with defined thickness (>= 0)
                def _thickness_defined(m_: dict[str, Any]) -> bool:
                    thickness_val = _to_float(m_.get("thickness"))
                    return thickness_val is not None and thickness_val >= 0

                valid_layers = [m for m in mats if _thickness_defined(m)]
                if len(valid_layers) != 3:
                    errors.append(
                        "Exactly three layers with defined thickness (>= 0) are required"
                    )

                if errors:
                    code_val = row.get("code")
                    raise ValueError(
                        f"Envelope {kind} definition for code '{code_val}' invalid: "
                        + ", ".join(errors)
                    )

                u_val = _calc_u(mats)
                ghg_total, ghg_bio = _calc_ghg(mats)

                # Map to legacy columns by kind
                base: dict[str, Any] = {
                    "description": row.get("description"),
                    "code": row.get("code"),
                }
                if kind == "floor":
                    base.update(
                        {
                            "U_base": u_val,
                            "GHG_floor_kgCO2m2": ghg_total,
                            "GHG_biogenic_floor_kgCO2m2": ghg_bio,
                            "Service_Life_floor": row.get("Service_Life_floor"),
                            "Reference": row.get("Reference"),
                        }
                    )
                elif kind == "roof":
                    base.update(
                        {
                            "U_roof": u_val,
                            "GHG_roof_kgCO2m2": ghg_total,
                            "GHG_biogenic_roof_kgCO2m2": ghg_bio,
                            "Service_Life_roof": row.get("Service_Life_floor")
                            or row.get("Service_Life_roof"),
                            "Reference Service life": row.get("Reference"),
                        }
                    )
                elif kind == "wall":
                    base.update(
                        {
                            "U_wall": u_val,
                            "GHG_wall_kgCO2m2": ghg_total,
                            "GHG_biogenic_wall_kgCO2m2": ghg_bio,
                            "Service_Life_wall": row.get("Service_Life_wall"),
                            "Reference": row.get("Reference"),
                        }
                    )
                else:
                    # default mapping uses a generic U value and GHG columns
                    base.update(
                        {
                            "U": u_val,
                            "GHG_kgCO2m2": ghg_total,
                            "GHG_biogenic_kgCO2m2": ghg_bio,
                        }
                    )

                # Pass-through only reference-related additional columns
                material_cols_prefixes = {"material_name_", "thickness_"}
                for col in df.columns:
                    # Skip material/thickness definition columns
                    if any(col.startswith(prefix) for prefix in material_cols_prefixes):
                        continue
                    # Only include columns that look like references; keep description/code already set
                    if "reference" in col.lower():
                        base[col] = row.get(col)

                out_rows.append(base)

            out_df = pd.DataFrame(out_rows)
            out_df = out_df.set_index(cls._index)
            return out_df

        # Transform material-based sheets to legacy format for floor, roof, wall only
        for kind, df in list(frames.items()):
            if df is None:
                continue
            if kind not in {"floor", "roof", "wall"}:
                # Skip mass, shading, tightness, window
                continue
            try:
                frames[kind] = _transform(df, kind)  # type: ignore[arg-type]
            except Exception:
                # If transformation fails, keep original
                frames[kind] = df

        return cls(**frames)

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
