from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast
import pandas as pd

from dataclasses import fields as dataclass_fields
from cea.datamanagement.database.assemblies import Envelope

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class EnvelopeLookup:
    """Lookup helper over an :class:`Envelope` instance.

    Instead of decomposing the envelope into an internal ``_dfs`` dict, this refactored version keeps a direct
    reference to ``self.envelope`` and accesses the DataFrames via their attribute names (``envelope.wall``,
    ``envelope.roof`` etc.). This reduces indirection and makes subsequent operations (updates, inspection)
    simpler and more explicit.

    A code ownership map (``_owner``) is constructed once at initialization by iterating over the dataclass
    fields of :class:`Envelope` and collecting all codes (index values) from non-empty DataFrames. Duplicate
    codes are rejected both within a DataFrame and across DataFrames to avoid ambiguous lookups.
    """

    # Mapping for dynamic column suffix resolution for shared envelope fields
    _SUFFIX = {"wall": "wall", "roof": "roof", "floor": "floor", "window": "win", "base": "floor"}
    _INT_FIELDS = {"Service_Life"}
    _FLOAT_FIELDS = {
        "U",
        "GHG_kgCO2m2",
        "GHG_biogenic_kgCO2m2",
        "G_win",
        "e_win",
        "F_F",
        "n50",
        "rf_sh",
        "Cm_af",
    }

    def __init__(self, envelope: Envelope):
        self.envelope = envelope
        # Build owner map directly from envelope attributes
        self._owner: dict[str, str] = {}
        dups: dict[str, list[str]] = {}
        any_loaded = False
        for f in dataclass_fields(Envelope):
            name = f.name
            df: pd.DataFrame | None = getattr(envelope, name)
            if df is None:
                continue
            any_loaded = True
            if df.index.duplicated().any():
                dup_in = sorted(set(df.index[df.index.duplicated()].astype(str)))
                raise ValueError(f"Duplicate codes within DB '{name}': {dup_in}")
            for code in df.index.astype(str):
                if code in self._owner:
                    dups.setdefault(code, [self._owner[code]]).append(name)
                else:
                    self._owner[code] = name
        if not any_loaded:
            raise ValueError("No envelope databases loaded.")
        if dups:
            details = "; ".join(f"{c}: {sorted(dbset)}" for c, dbset in dups.items())
            raise ValueError(f"Duplicate codes across DBs are not allowed: {details}")

    # --- helpers -----------------------------------------------------------------
    def _df_for(self, db_name: str) -> pd.DataFrame:
        """Return the DataFrame for a given envelope DB name or raise if missing/None."""
        if not hasattr(self.envelope, db_name):
            raise ValueError(f"Envelope has no attribute '{db_name}'.")
        df = getattr(self.envelope, db_name)
        if df is None:
            raise ValueError(f"Envelope DataFrame '{db_name}' is None (not loaded).")
        return df

    @property
    def databases(self) -> list[str]:
        """List of database names present (non-empty DataFrames)."""
        out = []
        for f in dataclass_fields(Envelope):
            df = getattr(self.envelope, f.name)
            if isinstance(df, pd.DataFrame) and not df.empty:
                out.append(f.name)
        return out

    @classmethod
    def from_locator(cls, locator: InputLocator) -> "EnvelopeLookup":
        env = Envelope.from_locator(locator)  # uses your BaseAssemblyDatabase loader
        return cls(env)

    def get_item_value(self, code: str, field: str) -> int | float | str | None:
        """Return value for (code, field).
        User-facing fields (exactly as listed):
        - `U`                       (wall, floor, roof, window)
        - `GHG_kgCO2m2`             (wall, floor, roof, window)
        - `GHG_biogenic_kgCO2m2`    (wall, floor, roof, window)
        - `Service_Life`            (wall, floor, roof, window)
        - `description`
        - `Reference`
        - `G_win`, `e_win`, `F_F`   (window only)
        - `n50`                     (tightness)
        - `rf_sh`                   (shading)
        - `Cm_af`                   (mass)

        :param code: the code of the envelope element, e.g., `WALL_AS03`
        :type code: str
        :param field: the field to retrieve, e.g., `U`, `GHG_kgCO2m2`, etc.
        :type field: str
        :raises ValueError: if the code is not found in any database
        :raises KeyError: if the field is not found in the database for the given code
        :return: the value of the specified field for the given code
        :rtype: int | float | str | None
        """
        code = str(code)
        if code not in self._owner:
            raise ValueError(f"Code '{code}' not found in any database.")
        db = self._owner[code]
        df = self._df_for(db)

        col = self._col(db, field)
        if col not in df.columns:
            raise KeyError(
                f"Column '{col}' not found in '{db}' for code '{code}'. "
                f"Available: {', '.join(map(str, df.columns))}"
            )

        val = df.loc[code, col]
        if pd.isna(val):
            return None
        if field in self._INT_FIELDS:
            try:
                return int(float(cast(Any, val)))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Cannot convert value '{val}' to integer for field '{field}' "
                    f"in database '{db}' for code '{code}'. Original error: {e}"
                )
        if field in self._FLOAT_FIELDS:
            try:
                return float(cast(Any, val))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Cannot convert value '{val}' to float for field '{field}' "
                    f"in database '{db}' for code '{code}'. Please check the envelope "
                    f"database file for malformed numeric values. Original error: {e}"
                )
        # textual fields
        if field in {"description", "Reference"}:
            return str(val)
        # fallback
        return cast(int | float | str | None, val)

    def _col(self, db: str, field: str) -> str:
        # Common envelope fields (dynamic per-component suffix)
        if field in {"U", "GHG_kgCO2m2", "GHG_biogenic_kgCO2m2", "Service_Life"}:
            if db not in self._SUFFIX:
                raise ValueError(
                    f"Field '{field}' valid only for wall/roof/floor/window; code is in '{db}'."
                )
            suf = self._SUFFIX[db]
            if field == "U":
                return f"U_{suf}"
            if field == "GHG_kgCO2m2":
                return f"GHG_{suf}_kgCO2m2"
            if field == "GHG_biogenic_kgCO2m2":
                return f"GHG_biogenic_{suf}_kgCO2m2"
            # Service_Life
            return f"Service_Life_{suf}"

        # Window-only extras
        if field in {"G_win", "e_win", "F_F"}:
            if db != "window":
                raise ValueError(
                    f"Field '{field}' only exists in 'window' DB; code is in '{db}'."
                )
            return field

        # Other DBs
        if field == "n50":
            if db != "tightness":
                raise ValueError("Field 'n50' only exists in 'tightness' DB.")
            return "n50"
        if field == "rf_sh":
            if db != "shading":
                raise ValueError("Field 'rf_sh' only exists in 'shading' DB.")
            return "rf_sh"
        if field == "Cm_af":
            if db != "mass":
                raise ValueError("Field 'Cm_af' only exists in 'mass' DB.")
            return "Cm_af"

        # Shared columns
        if field in {"description", "Reference"}:
            return field

        raise KeyError(
            f"Unsupported field '{field}'. Allowed: U, GHG_kgCO2m2, GHG_biogenic_kgCO2m2, Service_Life, "
            "description, Reference, G_win, e_win, F_F, n50, rf_sh, Cm_af."
        )

    def set_item_value(self, code: str, field: str, value: int | float | str | None) -> None:
        """Set value for (code, field). See `get_item_value` for supported fields."""
        code = str(code)
        if code not in self._owner:
            raise ValueError(f"Code '{code}' not found in any database.")
        db = self._owner[code]
        df = self._df_for(db)

        col = self._col(db, field)
        if col not in df.columns:
            raise KeyError(
                f"Column '{col}' not found in '{db}' for code '{code}'. "
                f"Available: {', '.join(map(str, df.columns))}"
            )

        df.at[code, col] = value