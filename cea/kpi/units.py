"""
Display units a KPI value can be converted to.

A KPI is defined (and cached) in one base unit — the yml's ``unit``. When
that unit belongs to a family below, the canvas KPI picker offers the
family's other units as a "Unit" dropdown, and the value endpoint converts
the cached base value on the way out. KPIs outside every family (``%``,
``USD``, ``m²``…) offer no choice.

Factors are relative to the family's first unit.
"""

from __future__ import annotations

from typing import List

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Parameter name the canvas uses for the chosen display unit. Reserved:
# no KPI may declare a `source.parameters` entry with this name.
UNIT_PARAMETER = "unit"

UNIT_FAMILIES = (
    {"kWh/yr": 1.0, "MWh/yr": 1e-3, "GWh/yr": 1e-6},
    {"kW": 1.0, "MW": 1e-3},
)


def unit_choices(unit: str) -> List[str]:
    """Units ``unit`` can be shown in, itself included; empty when there is no choice."""
    for family in UNIT_FAMILIES:
        if unit in family:
            return list(family)
    return []


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert ``value`` between two units of the same family. Raises ``ValueError``
    for units that are not interchangeable."""
    if from_unit == to_unit:
        return value
    for family in UNIT_FAMILIES:
        if from_unit in family and to_unit in family:
            return value * family[to_unit] / family[from_unit]
    raise ValueError(f"cannot convert '{from_unit}' to '{to_unit}'")
