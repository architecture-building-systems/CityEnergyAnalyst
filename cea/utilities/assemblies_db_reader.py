from __future__ import annotations
from typing import TYPE_CHECKING, Callable
import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class EnvelopeDBReader:
    """
    One-stop lookup for envelope + related DBs via (code, field).
    """

    # Which DBs we load and their locator getters (adjust method names if needed)
    _DB_LOADERS = {
        "wall": "get_database_assemblies_envelope_wall",
        "roof": "get_database_assemblies_envelope_roof",
        "floor": "get_database_assemblies_envelope_floor",
        "window": "get_database_assemblies_envelope_window",
        "tightness": "get_database_assemblies_envelope_tightness",
        "shading": "get_database_assemblies_envelope_shading",
        "mass": "get_database_assemblies_envelope_mass",
    }

    # Suffix used in per-component column names
    _SUFFIX = {"wall": "wall", "roof": "roof", "floor": "floor", "window": "win"}

    # Field routing + column name mapping
    # - str means a fixed column name in that DB
    # - callable(db_name) -> str for envelope fields that vary by DB
    _FIELD_SPEC: dict[str, dict[str, str | Callable[[str], str]]] = {
        # Envelope common fields
        "U": {
            db: (lambda d: f"U_{EnvelopeDBReader._SUFFIX[d]}")
            for db in ("wall", "roof", "floor", "window")
        },
        "GHG_kgCO2m2": {
            db: (lambda d: f"GHG_{EnvelopeDBReader._SUFFIX[d]}_kgCO2m2")
            for db in ("wall", "roof", "floor", "window")
        },
        "GHG_biogenic_kgCO2m2": {
            db: (lambda d: f"GHG_biogenic_{EnvelopeDBReader._SUFFIX[d]}_kgCO2m2")
            for db in ("wall", "roof", "floor", "window")
        },
        "Service_Life": {
            db: (lambda d: f"Service_Life_{EnvelopeDBReader._SUFFIX[d]}")
            for db in ("wall", "roof", "floor", "window")
        },
        # Envelope shared metadata
        "description": {db: "description" for db in _DB_LOADERS.keys()},
        "Reference": {db: "Reference" for db in _DB_LOADERS.keys()},
        # Window-only extras
        "G_win": {"window": "G_win"},
        "e_win": {"window": "e_win"},
        "F_F": {"window": "F_F"},
        # Other DBs
        "n50": {"tightness": "n50"}, # air tightness
        "rf_sh": {"shading": "rf_sh"}, # shading
        "Cm_af": {"mass": "Cm_af"}, # mass
    }

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

    def __init__(self, locator: InputLocator):
        self.locator = locator
        self._db: dict[str, pd.DataFrame] = {}

        # Load available DBs
        for name, getter in self._DB_LOADERS.items():
            if not hasattr(locator, getter):
                # If a DB isn’t used in your project, you may skip it
                continue
            path = getattr(locator, getter)()
            self._db[name] = pd.read_csv(path)

            if "code" not in self._db[name].columns:
                raise ValueError(f"DB '{name}' must contain a 'code' column.")

        if not self._db:
            raise ValueError("No databases loaded. Check locator method names/paths.")

        # Build code -> (db_name, row_index) map and reject duplicates
        self._code_map: dict[str, tuple[str, int]] = {}
        duplicates: dict[str, list[str]] = {}

        for db_name, df in self._db.items():
            for i, code in enumerate(df["code"].astype(str).tolist()):
                if code in self._code_map:
                    duplicates.setdefault(code, [self._code_map[code][0]]).append(
                        db_name
                    )
                else:
                    self._code_map[code] = (db_name, i)

        if duplicates:
            details = "; ".join(f"{c}: {sorted(dbs)}" for c, dbs in duplicates.items())
            raise ValueError(
                f"Duplicate codes across DBs are not allowed. Conflicts -> {details}"
            )

    # -------------------- Public API --------------------

    def get_item_value(self, code: str, field: str) -> int | float | str | None:
        """Get a value from the database.
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


        :param code: The code of the item to retrieve.
        :type code: str
        :param field: The field to retrieve from the item.
        :type field: str
        :raises ValueError: If the code is not found.
        :raises KeyError: If the field is not found anywhere.
        :raises ValueError: field unsupported for the DB where the code lives. 
            For example, asking 'G_win' for a wall code.
        :raises KeyError: If the column is not found in the DB.
        :return: The value from the database.
        :rtype: int | float | str | None
        """
        code = str(code)
        if code not in self._code_map:
            raise ValueError(f"Code '{code}' not found in any database.")

        db_name, row_idx = self._code_map[code]
        df = self._db[db_name]

        if field not in self._FIELD_SPEC:
            available = ", ".join(sorted(self._FIELD_SPEC.keys()))
            raise KeyError(
                f"Unsupported field '{field}'. Supported fields: {available}"
            )

        # Is this field valid for the DB that owns this code?
        spec = self._FIELD_SPEC[field]
        if db_name not in spec:
            # Example: asking 'G_win' for a wall code
            allowed = ", ".join(sorted(spec.keys()))
            raise ValueError(
                f"Field '{field}' is only available in DB(s): {allowed}. "
                f"Code '{code}' belongs to DB '{db_name}'."
            )

        # Resolve the actual column name
        col = spec[db_name]
        if callable(col):
            col = col(db_name)

        if col not in df.columns:
            raise KeyError(
                f"Column '{col}' not found in '{db_name}' DB for code '{code}'. "
                f"Available columns include: {', '.join(df.columns)}"
            )

        val = df.iloc[row_idx][col]

        if pd.isna(val):
            return None
        if field in self._INT_FIELDS:
            return int(val)
        if field in self._FLOAT_FIELDS:
            try:
                return float(val)
            except Exception:
                pass  # fall through for non-numeric text stored in a numeric column
        return val
