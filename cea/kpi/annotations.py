"""
Annotations: short notes a KPI card shows under its value, describing what
was measured (e.g. which PV panel type) rather than the value itself.

A KPI opts in with ``annotation: <name>`` in its yml entry. Providers are
registered here with ``@register("<name>")`` (the registry rejects unknown
names at load) and return a list of ``{"label": ..., "value": ...}`` rows.

They are computed per request, outside the value cache: each reads one small
file (a database CSV or the what-if configuration), and a stale annotation
next to a fresh value would be worse than the read.
"""

from __future__ import annotations

import os
from collections import Counter
from typing import Any, Callable, Dict, List, Mapping

import pandas as pd

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


def pv_panel_descriptions(locator: InputLocator) -> Dict[str, str]:
    """``{code: description}`` from the scenario's PV panel database; empty when missing."""
    path = locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
    if not os.path.isfile(path):
        return {}
    panels = pd.read_csv(path, usecols=["code", "description"]).drop_duplicates("code")
    return dict(zip(panels["code"], panels["description"]))


def describe_pv_panel(code: str, descriptions: Mapping[str, str]) -> str:
    description = descriptions.get(code)
    return f"{code} · {description}" if description else f"{code} (not in database)"


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


@register("installed_pv_by_orientation")
def _installed_pv_by_orientation(locator: InputLocator, args: Mapping[str, Any]) -> Annotation:
    """PV panel types installed on each orientation in the what-if, across all buildings.

    Orientations with the same installation are grouped into one row. When buildings differ,
    each panel type shows how many buildings carry it.
    """
    configuration = locator.read_analysis_configuration(args.get("whatif_name", "")) or {}
    buildings = configuration.get("buildings") or {}

    by_orientation: Dict[str, Counter] = {key: Counter() for key in _ORIENTATIONS}
    for building in buildings.values():
        solar = (building or {}).get("solar") or {}
        for key in _ORIENTATIONS:
            panel = _electric_pv_panel(solar.get(key))
            if panel:
                by_orientation[key][panel] += 1
    if not any(by_orientation.values()):
        return []

    descriptions = pv_panel_descriptions(locator)
    rows: Dict[str, List[str]] = {}
    for key in _ORIENTATIONS:
        counts = by_orientation[key]
        if not counts:
            continue
        if len(counts) == 1:
            value = describe_pv_panel(next(iter(counts)), descriptions)
        else:
            value = ", ".join(f"{describe_pv_panel(code, descriptions)} ({n} building{'' if n == 1 else 's'})"
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
