"""
Option generators for KPI parameter dropdowns.

Each KPI yml's ``source.parameters`` block names a generator (e.g.
``solar_panel_types``) that the canvas's KPI picker step-2 form
calls to populate a dropdown's choices. Generators take an
:class:`InputLocator` (so they can scan the active scenario's
output folders) and return a list of ``{value, label}`` dicts.

Generators are registered via the ``register`` decorator below;
:func:`run_generator` is the dispatch entry point used by the
``/api/kpis/<id>/parameters`` endpoint.

Adding a new generator:

1. Decorate a function with ``@register("<name>")``.
2. Reference the name from a yml ``parameters:`` block's
   ``options_generator`` field.
3. The endpoint resolves it on the next request.
"""

from __future__ import annotations

import glob
import os
from typing import Callable, Dict, List

from cea.inputlocator import InputLocator
from cea.kpi.exceptions import KPIDefinitionError

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Each generator returns ``[{"value": ..., "label": ...}, ...]``.
# Value is what the resolver receives as ``locator_args[<key>]``;
# label is what the dropdown renders.
ChoiceList = List[Dict[str, str]]
GeneratorFn = Callable[[InputLocator], ChoiceList]

_GENERATORS: Dict[str, GeneratorFn] = {}


def register(name: str) -> Callable[[GeneratorFn], GeneratorFn]:
    """Decorator: bind a generator function to a name reachable
    from yml ``options_generator`` fields."""

    def decorator(fn: GeneratorFn) -> GeneratorFn:
        _GENERATORS[name] = fn
        return fn

    return decorator


def run_generator(name: str, locator: InputLocator) -> ChoiceList:
    """Dispatch entry point. Raises :class:`KPIDefinitionError` for
    unregistered names so a typo in a yml fails loudly."""
    fn = _GENERATORS.get(name)
    if fn is None:
        raise KPIDefinitionError(
            f"unknown options_generator '{name}'. "
            f"Known: {sorted(_GENERATORS)}"
        )
    return fn(locator)


# ── Generators ──────────────────────────────────────────────────────


@register("solar_panel_types")
def _pv_panel_types(locator: InputLocator) -> ChoiceList:
    """Scan ``outputs/data/potentials/solar`` for `PV_<code>_total_buildings.csv`
    files and return the discovered panel codes. Mirrors the same
    on-disk scan the renewable-energy-potentials map layer uses for
    its panel-type dropdown so the two surfaces stay in sync."""
    folder = locator.get_potentials_solar_folder()
    if not os.path.isdir(folder):
        return []
    codes = set()
    for path in glob.glob(os.path.join(folder, "PV_*_total_buildings.csv")):
        stem = os.path.basename(path)[len("PV_"):-len("_total_buildings.csv")]
        if not stem or stem.startswith("PVT"):
            continue
        codes.add(stem)
    return [{"value": c, "label": c} for c in sorted(codes)]


@register("whatif_names")
def _whatif_names(locator: InputLocator) -> ChoiceList:
    """List analyses found under ``outputs/data/analysis/``. Always
    seeds the empty-string baseline first so users see a sensible
    default even when no what-if folders exist yet."""
    out: ChoiceList = [{"value": "", "label": "(baseline)"}]
    folder = locator.get_analysis_parent_folder()
    if not os.path.isdir(folder):
        return out
    for entry in sorted(os.listdir(folder)):
        full = os.path.join(folder, entry)
        if entry.startswith(".") or not os.path.isdir(full):
            continue
        out.append({"value": entry, "label": entry})
    return out


@register("network_types")
def _network_types(_: InputLocator) -> ChoiceList:
    """Static list — DH / DC. CEA's thermal-network model only
    ships these two; new types would be added here when they
    land."""
    return [
        {"value": "DH", "label": "District Heating"},
        {"value": "DC", "label": "District Cooling"},
    ]


@register("network_names")
def _network_names(locator: InputLocator) -> ChoiceList:
    """Scan the thermal-network folder for named-network sub-
    folders. The empty-string default (``""``) covers the most
    common single-network case where CEA omits the named subfolder
    entirely."""
    out: ChoiceList = [{"value": "", "label": "(default)"}]
    folder = locator.get_thermal_network_folder()
    if not os.path.isdir(folder):
        return out
    for entry in sorted(os.listdir(folder)):
        full = os.path.join(folder, entry)
        if entry.startswith(".") or not os.path.isdir(full):
            continue
        # Skip the sub-folders the network tool creates per type
        # (DH / DC) — those aren't network NAMES, they're types.
        if entry in {"DH", "DC"}:
            continue
        out.append({"value": entry, "label": entry})
    return out


@register("district_energy_system_ids")
def _district_energy_system_ids(locator: InputLocator) -> ChoiceList:
    """List published Pareto-front DES ids (e.g. ``DHS_000``,
    ``DCS_001``) — falls back to ``current_DES`` (the locator's
    default) when no optimisation results are on disk yet."""
    try:
        ids = locator.get_new_optimization_des_solution_folders()
    except (FileNotFoundError, StopIteration):
        ids = []
    if not ids:
        return [{"value": "current_DES", "label": "current_DES"}]
    return [{"value": i, "label": i} for i in sorted(ids)]
