"""Per-component LCA inputs for conversion technologies: service life and embodied carbon.

Both are read from the component's own row in `COMPONENTS/CONVERSION/*.csv`, and both report
where the number came from rather than returning a bare figure. Replacement count drives
embodied emissions directly -- a component with half the service life is replaced twice as
often over the same study period -- so the provenance matters as much as the value.

Service life, in order of preference:

1. `LT_yr` from the component's own row in `COMPONENTS/CONVERSION/*.csv`. Every row in the
   shipped databases has one, so this is the normal path.
2. A Green Mark reference value for the component family, when the database omits `LT_yr`.
3. A deliberately short default, when the family has no reference value either.

Green Mark reference
--------------------
Values in `GM_SERVICE_LIFE_YR` are taken from *Green Mark Version 7 Cn Technical Guide*
(BCA/SGBC, R1, 2 Sep 2026), Table 15 "Recommended Service life (RSL) for different MEPs",
p.65, mapped onto CEA's conversion-component families. Green Mark is used here only as a
published reference for missing data; CEA is not a Green Mark assessment tool.

Where CEA's own `LT_yr` and the Green Mark value disagree, CEA's value wins -- it is data
about the specific component, not a category default. The two differ most for:

===========================  =======  =======
family                       CEA      GM
===========================  =======  =======
UNITARY_AIR_CONDITIONERS     25       10
PHOTOVOLTAIC_PANELS          25       15
VAPOR_COMPRESSION_CHILLERS   25       20 water-cooled / 15 air-cooled
HYDRAULIC_PUMPS              25       20
BOILERS                      20       20 (agree)
===========================  =======  =======
"""
from __future__ import annotations

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE LTD"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from typing import TYPE_CHECKING, Any, NamedTuple

import pandas as pd

from cea.technologies.components import get_component_table

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

# Green Mark Table 15 values, mapped to CEA conversion-component families. The comment on
# each line is the Green Mark category the value is taken from, so the mapping can be checked
# against the source rather than trusted.
GM_SERVICE_LIFE_YR: dict[str, int] = {
    "ABSORPTION_CHILLERS": 20,           # water cooled chilled water system
    "BOILERS": 20,                       # heat source, e.g. boilers, calorifiers
    "COGENERATION_PLANTS": 20,           # heat source (no separate GM category)
    "COOLING_TOWERS": 20,                # part of the water cooled chilled water system
    "HEAT_EXCHANGERS": 20,               # space heating and air treatment
    "HEAT_PUMPS": 20,                    # space heating and air treatment
    "HYDRAULIC_PUMPS": 20,               # pumps
    "PHOTOVOLTAIC_PANELS": 15,           # solar PV system
    "PHOTOVOLTAIC_THERMAL_PANELS": 15,   # solar PV system
    "POWER_TRANSFORMERS": 30,            # electrical installations
    "SOLAR_COLLECTORS": 15,              # solar PV system (closest category)
    "THERMAL_ENERGY_STORAGES": 20,       # space heating and air treatment
    "UNITARY_AIR_CONDITIONERS": 10,      # unitary aircon system
    "VAPOR_COMPRESSION_CHILLERS": 15,    # air cooled chilled water system -- see note below
}
# VAPOR_COMPRESSION_CHILLERS: Green Mark distinguishes water cooled (20) from air cooled (15);
# CEA's family does not, so the shorter is used. A shorter life means more replacements and a
# higher emission estimate, which is the safer direction for a value that is a guess.

# Families with no Green Mark counterpart (FUEL_CELLS, BORE_HOLES) fall through to this.
GM_FALLBACK_SERVICE_LIFE_YR = 15
# Chosen to over- rather than under-estimate: fewer years means more replacement cycles and a
# larger embodied figure. It is a poor fit for long-lived civil works such as BORE_HOLES
# (CEA's own value is 50), which is a reason to supply `LT_yr` rather than rely on this.


class ServiceLife(NamedTuple):
    """A service life in years, and which of the three sources supplied it."""

    years: int
    source: str  # "database" | "green_mark_reference" | "fallback"

    @property
    def is_assumed(self) -> bool:
        """True when the value did not come from the component's own data."""
        return self.source != "database"


def resolve_service_life(family: str, lt_yr: float | int | None) -> ServiceLife:
    """Return the service life to use for a component, and where it came from.

    :param family: conversion-component family, e.g. ``"BOILERS"`` (the CSV stem).
    :param lt_yr: the component row's own ``LT_yr``, or None when absent or unparseable.
    """
    years = _positive_number(lt_yr)
    if years is not None:
        return ServiceLife(int(years), "database")

    reference = GM_SERVICE_LIFE_YR.get(str(family).upper())
    if reference is not None:
        return ServiceLife(reference, "green_mark_reference")

    return ServiceLife(GM_FALLBACK_SERVICE_LIFE_YR, "fallback")


def _positive_number(value: Any) -> float | None:
    """A usable positive number, or None for anything absent, unparseable, NaN or <= 0.

    Zero is treated as absent rather than as a value: neither a zero service life nor a zero
    embodied factor carries information, and both would otherwise propagate silently.
    """
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number <= 0:  # NaN or non-positive
        return None
    return number


def service_life_for_component(component_code: str, locator: InputLocator) -> ServiceLife:
    """Resolve a conversion component's service life from its code.

    Finds the owning table the same way `system-costs` does (`get_component_table` scans
    `COMPONENTS/CONVERSION/`), reads that row's `LT_yr`, then applies the preference order in
    this module's docstring. A code that is in no table gets the fallback -- an unknown
    component is exactly the case where a guess must be visible rather than fatal.
    """
    family, row = _component_row(component_code, locator)
    if family is None:
        return ServiceLife(GM_FALLBACK_SERVICE_LIFE_YR, "fallback")
    return resolve_service_life(family, None if row is None else row.get("LT_yr"))


# --- embodied carbon --------------------------------------------------------------------

# The capacity-based factor each CONVERSION table may carry. Optional: only
# PHOTOVOLTAIC_PANELS ships data today (under its own older column name), so most components
# still fall back to the blanket per-GFA intensity in `cea.constants`.
EMBODIED_FACTOR_COLUMN = "GHG_embodied_kgCO2e_per_unit"

# PHOTOVOLTAIC_PANELS predates the shared column and states its factor per m2 of module,
# while its capacity `unit` is W. Read it only when the caller asks in m2.
_PV_LEGACY_FACTOR_COLUMN = "module_embodied_kgco2m2"


class EmbodiedFactor(NamedTuple):
    """A capacity-based embodied-carbon factor, and the unit its capacity is measured in.

    `kgCO2e_per_unit` multiplies a capacity expressed in `unit` -- W, VA, m2, m3 or kWh
    depending on the technology, exactly as the cost curve does. Callers must pass a capacity
    in that unit rather than assuming watts.
    """

    kgCO2e_per_unit: float
    unit: str
    family: str


def embodied_factor_for_component(
    component_code: str, locator: InputLocator
) -> EmbodiedFactor | None:
    """The component's embodied-carbon factor, or None when its table carries no value.

    None is the common case and is not an error: it means the caller should fall back to the
    blanket per-GFA intensity. Returning None rather than a substituted number keeps the two
    bases distinct -- a per-GFA figure is not a capacity factor and must not masquerade as one.
    """
    family, row = _component_row(component_code, locator)
    if family is None or row is None:
        return None

    factor = _positive_number(row.get(EMBODIED_FACTOR_COLUMN))
    if factor is None:
        factor = _positive_number(row.get(_PV_LEGACY_FACTOR_COLUMN))
        if factor is None:
            return None
        # The legacy column is per m2 of module regardless of the table's capacity unit.
        return EmbodiedFactor(factor, "m2", family)

    unit = str(row.get("unit", "")).strip()
    if not unit:
        return None
    return EmbodiedFactor(factor, unit, family)


def _component_row(
    component_code: str, locator: InputLocator
) -> tuple[str | None, pd.Series | None]:
    """The conversion table that owns this code, and the code's row in it.

    `(None, None)` when no table claims the code; `(family, None)` when the table exists but
    the row or file does not, so a caller can still fall back per family. Multiple rows per
    code are capacity-range segments of one product, and the data read through here (service
    life, embodied factor) is a property of the product, so the first segment answers it.
    """
    family = get_component_table(component_code, locator)
    if family is None:
        return None, None

    path = locator.get_db4_components_conversion_conversion_technology_csv(family)
    try:
        frame = pd.read_csv(path)
    except (FileNotFoundError, OSError):
        return family, None

    rows = frame[frame["code"] == component_code] if "code" in frame.columns else frame
    return family, None if rows.empty else rows.iloc[0]
