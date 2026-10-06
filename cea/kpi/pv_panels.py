"""
PV panel labels from the scenario's component database, shared by the KPI
parameter dropdowns (`option_generators`) and card annotations (`annotations`).

The database is user-editable and the labels are cosmetic, so nothing here
raises on a missing, malformed or partly filled file: a panel that cannot be
described is shown by its code alone.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Mapping, Optional

import pandas as pd

from cea.inputlocator import InputLocator
from cea.kpi.file_cache import read_cached

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi", "Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

logger = logging.getLogger(__name__)


def pv_panel_descriptions(locator: InputLocator) -> Mapping[str, Optional[str]]:
    """``{code: description}`` from the scenario's PV panel database (``None`` for a
    panel listed without a description); empty when the database is missing or
    unreadable."""
    path = locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
    if not os.path.isfile(path):
        return {}
    try:
        return read_cached(path, _load_descriptions, kind="pv_panel_descriptions")
    except OSError:
        logger.warning("Could not read the PV panel database %s", path, exc_info=True)
        return {}


def _load_descriptions(path: str) -> Dict[str, Optional[str]]:
    try:
        # A callable `usecols` tolerates a database without a `description` column.
        panels = pd.read_csv(path, usecols=lambda column: column in ("code", "description"), dtype=str)
    except ValueError:
        # Parser and decoding errors. Returned (and so cached) as "nothing known"
        # rather than raised, so a broken file is not re-parsed on every request.
        logger.warning("Could not parse the PV panel database %s", path, exc_info=True)
        return {}
    if "code" not in panels.columns:
        return {}
    if "description" not in panels.columns:
        panels["description"] = None

    descriptions: Dict[str, Optional[str]] = {}
    # The database has one row per capacity range; the first row of a code wins.
    for code, description in zip(panels["code"], panels["description"]):
        if not isinstance(code, str) or code in descriptions:
            continue
        text = description.strip() if isinstance(description, str) else ""
        descriptions[code] = text or None
    return descriptions


def describe_pv_panel(code: str, descriptions: Mapping[str, Optional[str]]) -> str:
    """``PV1 · typical csi 2024 (BIPV)``; the bare code when there is no description
    to show; ``PV9 (not in database)`` when the database lists other panels but not
    this one."""
    if not descriptions:
        return code
    if code not in descriptions:
        return f"{code} (not in database)"
    description = descriptions[code]
    return f"{code} · {description}" if description else code
