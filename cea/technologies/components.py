"""
Data-driven component resolution.

CEA's downstream pipelines (final-energy, costs, heat-rejection) look up
a component by its ``code`` (``BO1``, ``HP1``, ``OEHR1``, ``ACH1``, …) and
need to know its *carrier* (NATURALGAS, GRID, SOLAR, …) and *efficiency*.
Historically both pieces were gated by hardcoded code-prefix tables: a
user who adds a new component CSV (``FUEL_CELLS.csv``, say) or a new
component code under an existing prefix would trip either an
"Unknown component code prefix" error or a branch-specific lookup that
didn't exist yet.

This module removes the gate. It:

1. Scans every ``*.csv`` file under
   ``{scenario}/inputs/technology/components/CONVERSION/`` (falling back
   to CEA's bundled DB) and builds a ``code → (table_name, row_dict)``
   index.
2. Classifies each component purely from its *columns* — a scheme that
   stays correct as long as users follow CEA's existing schema
   conventions.

Classification rules (column-driven, no prefix hardcoding):

+------------------------------------+----------------------------+-----------+
| Columns present                    | Interpretation             | Carrier   |
+====================================+============================+===========+
| ``fuel_code``                      | fuel-combustion device     | resolved  |
| (BOILERS, COGENERATION_PLANTS, …)  | (efficiency: prefer        | via       |
|                                    | ``therm_eff_design``, then | ENERGY_   |
|                                    | ``min_eff_rating``, then   | CARRIERS  |
|                                    | ``elec_eff_design``)       |           |
+------------------------------------+----------------------------+-----------+
| ``min_eff_rating_seasonal``        | electric heat pump         | GRID      |
+------------------------------------+----------------------------+-----------+
| ``min_eff_rating`` AND             | thermal-driven chiller     | None      |
| ``aux_power``                      | (absorption); main carrier | (set by   |
|                                    | is the upstream heat supply| assembly) |
+------------------------------------+----------------------------+-----------+
| ``min_eff_rating`` (no aux_power)  | vapour-compression chiller | GRID      |
+------------------------------------+----------------------------+-----------+
| ``aux_power`` (no min_eff_rating)  | cooling-tower-like aux.    | GRID      |
+------------------------------------+----------------------------+-----------+
| Filename in {SOLAR_COLLECTORS,     | delegate to ``solar_dhw``  | SOLAR     |
| PHOTOVOLTAIC_THERMAL_PANELS}       |                            |           |
+------------------------------------+----------------------------+-----------+
| none of the above                  | passive (heat exchanger)   | None      |
+------------------------------------+----------------------------+-----------+

Users who add a new component table (or new codes within an existing
table) get picked up automatically — no Python change is required as long
as the new table follows one of the column patterns above. If a user
invents a new column scheme, they can add their table name to the
filename-delegation path or extend this module's classification.
"""

from __future__ import annotations

import functools
import os
from typing import Dict, Optional, Tuple

import pandas as pd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



# Tables handled by the solar-specific helper in ``solar_dhw.py``. Matched
# by table filename, not by component-code prefix — so user-added codes
# inside these tables (e.g. ``SC3``) route through the same path.
_SOLAR_TABLES = {
    'SOLAR_COLLECTORS',
    'PHOTOVOLTAIC_THERMAL_PANELS',
}


@functools.lru_cache(maxsize=8)
def _scan_conversion_tables(scenario: str) -> Dict[str, Tuple[str, Dict]]:
    """Scan every ``COMPONENTS/CONVERSION/*.csv`` and index rows by ``code``.

    Returns a dict ``{code: (table_name, row_dict)}``. ``table_name`` is
    the CSV stem (e.g. ``"BOILERS"``). If the same code appears in
    multiple tables (shouldn't happen but is possible in an ill-formed
    DB), the first-scanned entry wins.

    Cached per-scenario via ``lru_cache`` keyed on the scenario path.
    """
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator(scenario=scenario)
    folder = locator.get_db4_components_conversion_folder()
    index: Dict[str, Tuple[str, Dict]] = {}
    if not folder or not os.path.isdir(folder):
        return index
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith('.csv'):
            continue
        path = os.path.join(folder, fname)
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if 'code' not in df.columns:
            continue
        table_name = os.path.splitext(fname)[0]
        for _, row in df.iterrows():
            code = str(row['code']).strip()
            if not code:
                continue
            # First table wins (cap_min/cap_max segments for the same
            # code appear as multiple rows; the first row is a fine
            # proxy for the component's category-level attributes like
            # fuel_code and efficiency).
            if code not in index:
                index[code] = (table_name, row.to_dict())
    return index


def get_component_table(component_code: str, locator) -> Optional[str]:
    """Return the CSV table name that owns this component code.

    E.g. ``'BO1' → 'BOILERS'``, ``'OEHR1' → 'COGENERATION_PLANTS'``.
    Returns ``None`` if the code isn't in any scanned table.
    """
    hit = _scan_conversion_tables(locator.scenario).get(component_code)
    return hit[0] if hit else None


def _pick_efficiency(row: Dict) -> Optional[float]:
    """Pick the most relevant efficiency value from a component row.

    Preference order:
    1. ``therm_eff_design`` (cogeneration: thermal output is primary for
       heat-supply sizing)
    2. ``min_eff_rating`` (standard efficiency/COP)
    3. ``min_eff_rating_seasonal`` (heat pumps use SCOP)
    4. ``elec_eff_design`` (cogeneration electrical, if no thermal)
    5. ``aux_power`` (cooling tower fan ratio)
    """
    for col in (
        'therm_eff_design',
        'min_eff_rating',
        'min_eff_rating_seasonal',
        'elec_eff_design',
        'aux_power',
    ):
        if col in row and pd.notna(row[col]):
            try:
                return float(row[col])
            except (TypeError, ValueError):
                pass
    return None


def load_component_info(component_code: str, locator) -> Dict:
    """Resolve a component's carrier and efficiency purely from the DB.

    Drop-in replacement for the hand-coded prefix table in
    ``cea.analysis.final_energy.calculation.load_component_info``. Uses
    only CSV columns to classify — no code-prefix hardcoding — so user-
    added components (and new tables) work without Python changes.

    :return: Dict with keys ``'carrier'`` (carrier name or ``None``) and
        ``'efficiency'`` (float or ``None``). Solar delegation may add a
        ``'type'`` key for the SC/PVT branches.
    :raises ValueError: If the code isn't in any conversion table, with
        an actionable message listing the tables that were scanned.
    """
    index = _scan_conversion_tables(locator.scenario)
    hit = index.get(component_code)
    if hit is None:
        raise ValueError(
            f"Component code {component_code!r} not found in any CSV "
            f"under COMPONENTS/CONVERSION/. Tables scanned: "
            f"{', '.join(sorted({t for t, _ in index.values()}))}. "
            f"Add a row for this code to the appropriate table, or check "
            f"for typos in the supply assembly referencing it."
        )
    table_name, row = hit

    # Solar tables have their own semantics (aperture-based sizing, no
    # efficiency column in the usual sense) — delegate.
    if table_name in _SOLAR_TABLES:
        from cea.analysis.final_energy.solar_dhw import load_solar_component_info
        return load_solar_component_info(component_code, locator)

    # Column-driven classification.
    cols = set(row.keys())

    # 1) Fuel-combustion device: has ``fuel_code``.
    fuel_code = row.get('fuel_code')
    if 'fuel_code' in cols and fuel_code is not None and pd.notna(fuel_code) and str(fuel_code).strip():
        from cea.technologies.energy_carriers import carrier_from_fuel_code
        return {
            'carrier': carrier_from_fuel_code(locator, str(fuel_code).strip()),
            'efficiency': _pick_efficiency(row),
        }

    # The electric-driven branches below (heat pump, electric chiller,
    # cooling-tower fan) book into the scenario's electricity carrier.
    # Resolve it once from ENERGY_CARRIERS.csv so a user who renamed
    # their electricity feedstock (e.g. 'GRID' → 'POWER') gets the
    # correct name here.
    from cea.technologies.energy_carriers import electricity_carrier

    # 2) Seasonal-COP heat pump.
    if 'min_eff_rating_seasonal' in cols and pd.notna(row.get('min_eff_rating_seasonal')):
        return {
            'carrier': electricity_carrier(locator),
            'efficiency': float(row['min_eff_rating_seasonal']),
        }

    # 3) Absorption chiller (thermal-driven): has both min_eff_rating
    #    AND aux_power. Carrier is set by the upstream heat supply, so
    #    leave it blank here.
    has_min_eff = 'min_eff_rating' in cols and pd.notna(row.get('min_eff_rating'))
    has_aux = 'aux_power' in cols and pd.notna(row.get('aux_power'))
    if has_min_eff and has_aux:
        return {
            'carrier': None,
            'efficiency': float(row['min_eff_rating']),
        }

    # 4) Electric chiller: min_eff_rating alone.
    if has_min_eff:
        return {
            'carrier': electricity_carrier(locator),
            'efficiency': float(row['min_eff_rating']),
        }

    # 5) Cooling-tower-like: aux_power alone.
    if has_aux:
        return {
            'carrier': electricity_carrier(locator),
            'efficiency': float(row['aux_power']),
        }

    # 6) Passive: no energy-conversion columns (HEX, storage, etc.).
    return {
        'carrier': None,
        'efficiency': None,
    }
