"""
Data-driven access to the scenario's ``ENERGY_CARRIERS.csv``.

CEA's downstream pipelines (final-energy, costs, heat-rejection, emissions,
visualisations) classify energy flows by *carrier name* — ``NATURALGAS``,
``GRID``, ``WOOD``, etc. Historically those mappings lived in several
hardcoded dicts/sets across the codebase (``map_fuel_code_to_carrier``,
``CARRIER_TO_FEEDSTOCK``, ``FUEL_CARRIERS``), which meant any fuel code not
in the hardcoded set — including users' own carriers — produced a hard
crash or silently wrong results.

This module gives those pipelines a single, database-driven lookup:

- :func:`carrier_from_fuel_code` — resolve a component ``fuel_code``
  (``Cgas``, ``Cwbm``, …) to the carrier name (``NATURALGAS``,
  ``WETBIOMASS``, …) via the ``feedstock_file`` column.
- :func:`combustible_carriers` — set of carriers whose ``type`` column is
  ``combustible`` (drives heat-rejection combustion-loss accounting).
- :func:`available_carriers` — set of every carrier name defined in the
  scenario's database.

A user who adds a row to ``ENERGY_CARRIERS.csv`` (with its matching
``FEEDSTOCKS_LIBRARY/{name}.csv``) gets picked up automatically — no
Python change needed.
"""

from __future__ import annotations

import functools
from typing import Set

import pandas as pd

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def _load_cached(scenario: str) -> pd.DataFrame:
    """Cached read of the scenario's ``ENERGY_CARRIERS.csv``.

    Scenarios keyed by path string so the cache doesn't retain InputLocator
    instances (which are lightweight but can pickle-fail in workers).
    """
    return _load_cached_by_path(scenario)


@functools.lru_cache(maxsize=8)
def _load_cached_by_path(scenario: str) -> pd.DataFrame:
    # Late import — importing InputLocator at module load creates a
    # circular path through ``cea.config`` in some entry points.
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator(scenario=scenario)
    path = locator.get_database_components_feedstocks_energy_carriers()
    df = pd.read_csv(path)
    df['feedstock_file'] = (
        df['feedstock_file'].fillna('-').astype(str).str.strip().str.upper()
    )
    df['type'] = df['type'].fillna('').astype(str).str.strip().str.lower()
    df['code'] = df['code'].astype(str).str.strip()
    return df


def _df(locator) -> pd.DataFrame:
    return _load_cached(locator.scenario)


def carrier_from_fuel_code(locator, fuel_code: str) -> str:
    """Resolve a component's ``fuel_code`` to its carrier name.

    :raises ValueError: If the code is not in ``ENERGY_CARRIERS.csv`` or
        its ``feedstock_file`` column is empty (``-``). The error names
        the CSV so users can fix it directly.
    """
    df = _df(locator)
    row = df[df['code'] == fuel_code]
    if row.empty:
        raise ValueError(
            f"Unknown fuel code: {fuel_code!r}. No row with this code in "
            "ENERGY_CARRIERS.csv. Add a row for it, or fix the typo in the "
            "component that references it."
        )
    feedstock_file = row.iloc[0]['feedstock_file']
    if feedstock_file == '-' or not feedstock_file:
        raise ValueError(
            f"Fuel code {fuel_code!r} has no ``feedstock_file`` set in "
            "ENERGY_CARRIERS.csv. Set the column to the carrier name "
            "(e.g. 'NATURALGAS', 'WETBIOMASS') matching a file in "
            "FEEDSTOCKS_LIBRARY/."
        )
    return feedstock_file


def combustible_carriers(locator) -> Set[str]:
    """Carriers whose components release heat via combustion.

    Used by heat-rejection to compute combustion losses = fuel_in − heat_out.
    Derived from ``ENERGY_CARRIERS.csv``: every row with ``type ==
    'combustible'`` contributes its ``feedstock_file`` name.
    """
    df = _df(locator)
    combustibles = df.loc[df['type'] == 'combustible', 'feedstock_file']
    return {c for c in combustibles if c and c != '-'}


def available_carriers(locator) -> Set[str]:
    """Every carrier name defined in the scenario's database.

    Equivalent to the distinct set of ``feedstock_file`` values, excluding
    the ``-`` placeholder used for thermal-only rows.
    """
    df = _df(locator)
    return {c for c in df['feedstock_file'] if c and c != '-'}
