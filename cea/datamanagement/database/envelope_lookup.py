from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd

from cea.datamanagement.database.assemblies import Envelope

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class EnvelopeLookup:
    """DB-agnostic (code, field) lookup on top of Envelope dataclass."""

    _SUFFIX = {"wall": "wall", "roof": "roof", "floor": "floor", "window": "win"}
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
        self._dfs: dict[str, pd.DataFrame] = {
            name: df
            for name, df in {
                "wall": envelope.wall,
                "roof": envelope.roof,
                "floor": envelope.floor,
                "window": envelope.window,
                "tightness": envelope.tightness,
                "shading": envelope.shading,
                "mass": envelope.mass,
            }.items()
            if df is not None
        }
        if not self._dfs:
            raise ValueError("No envelope databases loaded.")

        # Build code owner map; reject duplicates across ALL DBs and within a DB
        self._owner: dict[str, str] = {}
        dups: dict[str, list[str]] = {}
        for db_name, df in self._dfs.items():
            if df.index.duplicated().any():
                dup_in = sorted(set(df.index[df.index.duplicated()].astype(str)))
                raise ValueError(f"Duplicate codes within DB '{db_name}': {dup_in}")
            for code in df.index.astype(str):
                if code in self._owner:
                    dups.setdefault(code, [self._owner[code]]).append(db_name)
                else:
                    self._owner[code] = db_name
        if dups:
            details = "; ".join(f"{c}: {sorted(dbset)}" for c, dbset in dups.items())
            raise ValueError(f"Duplicate codes across DBs are not allowed: {details}")

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
        df = self._dfs[db]

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
                return int(float(val))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Cannot convert value '{val}' to integer for field '{field}' "
                    f"in database '{db}' for code '{code}'. Original error: {e}"
                )
        if field in self._FLOAT_FIELDS:
            try:
                return float(val)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Cannot convert value '{val}' to float for field '{field}' "
                    f"in database '{db}' for code '{code}'. Please check the envelope "
                    f"database file for malformed numeric values. Original error: {e}"
                )
        return val

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
