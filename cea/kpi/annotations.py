"""
Annotations: short notes a KPI card shows under its value, describing what
was measured (e.g. which PV panel type) rather than the value itself.

A KPI opts in with ``annotation: <name>`` in its yml entry. Providers are
registered here with ``@register("<name>")`` (the registry rejects unknown
names at load) and return a list of ``{"label": ..., "value": ...}`` rows.

They are computed per request, outside the value cache, so an annotation is
never staler than the files it describes. The files themselves (the PV panel
database, the what-if configuration -- which lists every building and can run
to megabytes) are read through `cea.kpi.file_cache`, so a request only pays
for parsing them after they change.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Mapping, Tuple

from cea.inputlocator import InputLocator
from cea.kpi.exceptions import KPIDefinitionError
from cea.kpi.file_cache import read_cached
from cea.kpi.pv_panels import describe_pv_panel, pv_panel_descriptions

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

Annotation = List[Dict[str, str]]
ProviderFn = Callable[[InputLocator, Mapping[str, Any]], Annotation]

_PROVIDERS: Dict[str, ProviderFn] = {}

# Orientation keys used by final-energy's per-building `solar` config, in display order,
# with the short name used when grouping walls ("Walls N/S").
_ORIENTATIONS = {
    "roof": "Roof",
    "wall_north": "N",
    "wall_south": "S",
    "wall_east": "E",
    "wall_west": "W",
}


def register(name: str) -> Callable[[ProviderFn], ProviderFn]:
    def decorator(fn: ProviderFn) -> ProviderFn:
        _PROVIDERS[name] = fn
        return fn

    return decorator


def known_providers() -> set[str]:
    return set(_PROVIDERS)


def annotate(name: str, locator: InputLocator, args: Mapping[str, Any]) -> Annotation:
    """Run provider ``name`` with the KPI's effective locator args."""
    fn = _PROVIDERS.get(name)
    if fn is None:
        raise KPIDefinitionError(f"unknown annotation '{name}'. Known: {sorted(_PROVIDERS)}")
    return fn(locator, args)


@register("pv_panel_type")
def _pv_panel_type(locator: InputLocator, args: Mapping[str, Any]) -> Annotation:
    """The PV panel type the KPI was computed for, with its database description."""
    code = args.get("panel_type")
    if not code:
        return []
    return [{"label": "Panel", "value": describe_pv_panel(code, pv_panel_descriptions(locator))}]


def _electric_pv_panel(technology: str | None) -> str | None:
    """PV panel code behind a final-energy facade technology: ``PV_PV1`` and ``PVT_PV1_FP`` both
    generate electricity with ``PV1``; solar collectors (``SC_FP``) generate none."""
    if not technology:
        return None
    parts = technology.split("_")
    if parts[0] in ("PV", "PVT") and len(parts) >= 2:
        return parts[1]
    return None


# Buildings in the what-if, and per orientation how many of them carry each panel code.
_InstalledPV = Tuple[int, Dict[str, Counter]]


def _installed_pv(configuration: Any) -> _InstalledPV:
    buildings = (configuration or {}).get("buildings") or {}
    by_orientation: Dict[str, Counter] = {key: Counter() for key in _ORIENTATIONS}
    for building in buildings.values():
        solar = (building or {}).get("solar") or {}
        for key in _ORIENTATIONS:
            panel = _electric_pv_panel(solar.get(key))
            if panel:
                by_orientation[key][panel] += 1
    return len(buildings), by_orientation


@register("installed_pv_by_orientation")
def _installed_pv_by_orientation(locator: InputLocator, args: Mapping[str, Any]) -> Annotation:
    """PV panel types installed on each orientation in the what-if, across all buildings.

    Orientations with the same installation are grouped into one row. A panel type that
    is not on every building shows how many carry it -- final-energy attaches the solar
    configuration only to the buildings selected for it, so partial coverage is the norm.
    """
    whatif_name = args.get("whatif_name", "")
    path = locator.find_analysis_configuration_file(whatif_name)
    if path is None:
        return []
    # Only the tally is kept, not the parsed configuration.
    total, by_orientation = read_cached(
        path,
        lambda _path: _installed_pv(locator.read_analysis_configuration(whatif_name)),
        kind="installed_pv_by_orientation",
    )
    if not any(by_orientation.values()):
        return []

    descriptions = pv_panel_descriptions(locator)
    rows: Dict[str, List[str]] = {}
    for key in _ORIENTATIONS:
        counts = by_orientation[key]
        if not counts:
            continue
        if len(counts) == 1 and next(iter(counts.values())) == total:
            value = describe_pv_panel(next(iter(counts)), descriptions)
        else:
            value = ", ".join(f"{describe_pv_panel(code, descriptions)} ({n} of {total} buildings)"
                              for code, n in sorted(counts.items()))
        rows.setdefault(value, []).append(key)
    return [{"label": _orientations_label(keys), "value": value} for value, keys in rows.items()]


def _orientations_label(keys: List[str]) -> str:
    """``["roof", "wall_north", ...]`` -> ``"Roof, walls"``; ``["wall_north", "wall_south"]`` ->
    ``"Walls N/S"``."""
    walls = [_ORIENTATIONS[k] for k in keys if k != "roof"]
    parts = ["Roof"] if "roof" in keys else []
    if walls:
        parts.append("walls" if len(walls) == 4 else "walls " + "/".join(walls))
    label = ", ".join(parts)
    return label[0].upper() + label[1:]
