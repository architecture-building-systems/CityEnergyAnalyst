"""
Read / write the per-scenario KPI cache record.

The file lives at ``<scenario>/outputs/kpis/kpi_status.json`` (path
owned by :meth:`InputLocator.get_kpi_status_file`) and carries one
record per KPI:

.. code-block:: json

    {
      "schema_version": 1,
      "kpis": {
        "demand.eui_kwh_m2": {
          "value": 78.4,
          "unit": "kWh/m\u00b2/yr",
          "computed_at": "2026-05-05T18:42:00+00:00",
          "scenario_inputs_hash": "...",
          "upstream_outputs_hash": "...",
          "kpi_definition_hash": "...",
          "sources_read": ["..."]
        }
      }
    }

Writes are atomic via temp-file + ``os.replace`` so a crashed
process can never leave the JSON half-written. Reads return ``{}``
on a missing or malformed file — a corrupted cache is recoverable
by recomputing, never a hard failure.

Mirrors :mod:`cea.datamanagement.district_pathways.pathway_status`'s
shape so the two status records read consistently in tests / debug.
"""

from __future__ import annotations

import json
import os
from typing import Any

from cea.inputlocator import InputLocator

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

SCHEMA_VERSION = 1


def read_status(scenario: str) -> dict[str, Any]:
    """Return the full status record for a scenario, or an empty
    dict if the file doesn't exist or can't be parsed."""
    path = InputLocator(scenario).get_kpi_status_file()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle) or {}
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        # A corrupted cache is recoverable — caller will recompute.
        return {}


def read_kpi(scenario: str, kpi_id: str) -> dict[str, Any] | None:
    """Return the single KPI record, or ``None`` if absent."""
    record = read_status(scenario).get("kpis", {}).get(kpi_id)
    return record if isinstance(record, dict) else None


def write_kpi(scenario: str, kpi_id: str, payload: dict[str, Any]) -> None:
    """Insert or replace one KPI record. Other entries in the file
    are preserved. Atomic via temp-file + ``os.replace``."""
    path = InputLocator(scenario).get_kpi_status_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    current = read_status(scenario)
    current.setdefault("schema_version", SCHEMA_VERSION)
    current.setdefault("kpis", {})[kpi_id] = payload
    _atomic_write_json(path, current)


def clear_kpi(
    scenario: str,
    *,
    kpi_id: str | None = None,
    feature: str | None = None,
) -> None:
    """Remove cache entries.

    * ``kpi_id`` set → drop that one entry.
    * ``feature`` set → drop every entry whose id starts with
      ``"<feature>."``.
    * Both unset → drop every entry (full reset).
    """
    path = InputLocator(scenario).get_kpi_status_file()
    if not os.path.isfile(path):
        return
    current = read_status(scenario)
    kpis = current.get("kpis", {})
    if kpi_id is not None:
        kpis.pop(kpi_id, None)
    elif feature is not None:
        prefix = f"{feature}."
        for key in [k for k in kpis if k.startswith(prefix)]:
            kpis.pop(key)
    else:
        kpis.clear()
    current["kpis"] = kpis
    _atomic_write_json(path, current)


def _atomic_write_json(path: str, payload: dict[str, Any]) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    os.replace(tmp, path)
