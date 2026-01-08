"""District material timeline (event-driven).

This module builds a district-level emissions timeline with *event semantics*:
- Operational emissions are applied as step functions per state-year simulation results.
- Embodied emissions are applied as discrete events driven by `district_timeline_log.yml`.

The changes are logged per archetype in the .yaml file. Therefore, the first task is to recreate the
individual building's changelog based on archetype changes.

For each building, there are four changes worth noticing along its timeline:
- envelope modifications (with change of layers);
- windows and supply system modifications (with change of codes);
- component's lifetime reached (for all envelope, windows and supply systems).
- building's demolition at the end of its lifetime.

Each change result in a demolition of an old component, and a production (+biognic) of a new component.
Specifically, the supply systems are assumed to have fixed lifetime (`SERVICE_LIFE_OF_TECHNICAL_SYSTEMS`)
and embodied emissions (`EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS`). 
There are in total 4 supplies: heating, cooling, hotwater and electrical. Each system is assumed to consume
1/4 of the total embodied emission intensity. 

Core workflow:
- Precompute an `ArchetypeTimeline` from the log (layer snapshots + authored delta events, and code snapshots
    for windows / supply systems).
- For each building, generate a `MaterialChangeEmissionTimeline` by iterating through the years in which
    something happens (authored modifications, code changes, or due replacements).
- Sum building timelines to create the district timeline.

The embodied timeline iteration is implemented by `MaterialChangeEmissionTimeline.build_embodied_from_log`,
which uses `_BuildingEventCursor` to select the next year to process.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

import geopandas as gpd
import numpy as np
import pandas as pd

from cea.analysis.lca.emission_timeline import (
    COMPONENT_TO_SRC_COMPONENT,
    TIMELINE_COMPONENTS,
    BaseYearlyEmissionTimeline,
    apply_feedstock_policies_inplace,
    get_component_quantities,
)
from cea.analysis.lca.hourly_operational_emission import _tech_name_mapping
from cea.config import Configuration
from cea.constants import (
    EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS,
    SERVICE_LIFE_OF_TECHNICAL_SYSTEMS,
)
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.district_level_states.timeline_years import (
    ensure_state_years_exist,
    get_building_construction_years,
    get_required_state_years,
    reconcile_states_to_cumulative_modifications,
)
from cea.demand.building_properties import BuildingProperties
from cea.inputlocator import InputLocator
from cea.utilities import epwreader

_MATERIAL_SRC_COMPONENTS: set[str] = {"wall", "roof", "base", "floor", "part"}
_ASSEMBLY_SRC_COMPONENTS: set[str] = {"win"}

# Layered envelope components supported by the district timeline log.
# Values are envelope DB table names used by `EnvelopeLookup`.
_LAYERED_COMPONENT_TO_DB: dict[str, str] = {
    "wall": "wall",
    "roof": "roof",
    "base": "floor",  # ground-contact constructions are stored in ENVELOPE_FLOOR
    "floor": "floor",
    "part": "wall",  # partitions reuse wall envelope definitions
}

# Source components modelled in this workflow.
# - Layered material components (walls / roofs / floors / base / partitions) are calculated from MATERIALS.csv.
# - Windows are calculated from envelope assembly databases (e.g., ENVELOPE_WINDOW.csv) via EnvelopeLookup.
_COMP_AREA_MAP: list[tuple[str, str, str]] = [
    (component, src_component, f"A{component}")
    for component, src_component in COMPONENT_TO_SRC_COMPONENT.items()
    if src_component in _MATERIAL_SRC_COMPONENTS
    or src_component in _ASSEMBLY_SRC_COMPONENTS
    or src_component == "technical_systems"
]

_CONSTRUCTION_TYPE_WIN_FIELD = "type_win"
_SUPPLY_TYPE_FIELDS: tuple[str, ...] = (
    "supply_type_hs",
    "supply_type_cs",
    "supply_type_dhw",
    "supply_type_el",
)
_TECH_SYSTEM_COMPONENT_BY_SUPPLY_FIELD: dict[str, str] = {
    "supply_type_hs": "technical_system_hs",
    "supply_type_cs": "technical_system_cs",
    "supply_type_dhw": "technical_system_dhw",
    "supply_type_el": "technical_system_el",
}


def _parse_code_change(value: Any) -> tuple[str, str] | None:
    """Return (old, new) if value is a 2-tuple, else None."""
    if isinstance(value, tuple) and len(value) == 2:
        old_val, new_val = value
        return str(old_val), str(new_val)
    return None


def _min_or_none(values: Mapping[Any, int] | None) -> int | None:
    if not values:
        return None
    return min(values.values())


@dataclass
class _BuildingEventCursor:
    """Per-building cursor that iterates through the next event year.

    This helper exists purely to simplify control flow in
    `MaterialChangeEmissionTimeline.build_embodied_from_log(...)`.

    Important distinction:
    - `ArchetypeTimeline` describes *district/archetype* facts (snapshots + authored deltas) and is reusable
      across buildings.
    - `_BuildingEventCursor` holds *per-building mutable iteration state* (indices + due-year clocks) while we
      assemble a single building's embodied timeline.

    Fields:
    - `modification_years`: sorted years where layer-based modifications exist for this building's `const_type`.
    - `code_change_years`: sorted years where construction-type code changes exist for this building's `const_type`.
    - `envelope_next_due`: mapping `src_component -> next_due_year` for layer-based envelope components.
    - `window_next_due`: next due year for window service-life replacement, or None.
    - `tech_next_due`: mapping `technical_system_* -> next_due_year` for technical quarters.
    - `end_active_year`: last year the building exists (typically `demolition_year - 1` if demolished).
    - `_mod_idx`: internal index into `modification_years`. If larger than `len(modification_years) - 1`, 
        no more modifications remain.
    - `_code_idx`: internal index into `code_change_years`. If larger than `len(code_change_years) - 1`, 
        no more code changes remain.

        Method overview:
    - `next_year()` selects the next year to process as the minimum over:
            (next modification year, next code-change year, earliest `envelope_next_due`, `window_next_due`, earliest `tech_next_due`).
        - `advance_envelope_mod_if(year)` / `advance_code_if(year)` *acknowledge* a processed year by advancing internal indices.
    - `due_envelope_components(year)` / `due_tech_components(year)` list components due exactly in that year.
    - `is_window_due(year)` checks whether window replacement is due.

    Example:
        ```
        schedule = _BuildingEventCursor(
            modification_years=[2005, 2010],
            code_change_years=[2005],
            envelope_next_due={"wall": 2030, "roof": 2040},
            window_next_due=2025,
            tech_next_due={"technical_system_hs": 2035},
            end_active_year=2050,
        )

        while (year := schedule.next_year()) is not None:
            if schedule.consume_mod_if(year):
                ...
            if schedule.consume_code_if(year):
                ...
            for src in schedule.due_envelope_components(year):
                ...
            if schedule.is_window_due(year):
                ...
            for sys in schedule.due_tech_components(year):
                ...
        ```
    """

    modification_years: list[int]
    code_change_years: list[int]
    envelope_next_due: dict[str, int]
    window_next_due: int | None
    tech_next_due: dict[str, int]
    end_active_year: int
    _mod_idx: int = 0
    _code_idx: int = 0

    def peek_mod_year(self) -> int | None:
        """Return the next pending layer-modification year without consuming it."""
        return (
            self.modification_years[self._mod_idx]
            if self._mod_idx < len(self.modification_years)
            else None
        )

    def peek_code_year(self) -> int | None:
        """Return the next pending construction-type code-change year without consuming it."""
        return (
            self.code_change_years[self._code_idx]
            if self._code_idx < len(self.code_change_years)
            else None
        )

    def next_year(self) -> int | None:
        """Return the next year to process across all pending event sources.

        Candidates are:
        - next pending modification year
        - next pending code-change year
        - earliest due year among `envelope_next_due`
        - `window_next_due`
        - earliest due year among `tech_next_due`

        Returns None if there are no candidates left or the earliest candidate exceeds `end_active_year`.
        """
        next_mod_year = self.peek_mod_year()
        next_code_year = self.peek_code_year()
        next_envelope_rep_year = _min_or_none(self.envelope_next_due)
        next_tech_year = _min_or_none(self.tech_next_due)
        candidates = [
            y
            for y in (
                next_mod_year,
                next_code_year,
                next_envelope_rep_year,
                self.window_next_due,
                next_tech_year,
            )
            if y is not None
        ]
        if not candidates:
            return None
        year = min(candidates)
        if year > int(self.end_active_year):
            return None
        return int(year)

    def advance_envelope_mod_if(self, year: int) -> bool:
        """Advance past the next pending envelope modification year if it matches `year`.

        Returns True if an item was consumed (internal index advanced), otherwise False.
        """
        if self.peek_mod_year() == int(year):
            self._mod_idx += 1
            return True
        return False

    def advance_code_if(self, year: int) -> bool:
        """Advance past the next pending code-change year if it matches `year`.

        Returns True if an item was consumed (internal index advanced), otherwise False.
        """
        if self.peek_code_year() == int(year):
            self._code_idx += 1
            return True
        return False

    def due_envelope_components(self, year: int) -> list[str]:
        """Return envelope `src_component` keys with a service-life replacement due in `year`."""
        y = int(year)
        return [src for src, due in self.envelope_next_due.items() if int(due) == y]

    def due_tech_components(self, year: int) -> list[str]:
        """Return technical quarter component names with a service-life replacement due in `year`."""
        y = int(year)
        return [sys for sys, due in self.tech_next_due.items() if int(due) == y]

    def is_window_due(self, year: int) -> bool:
        """Return True if windows are due for service-life replacement in `year`."""
        return self.window_next_due is not None and int(self.window_next_due) == int(
            year
        )


def _envelope_intensities_per_m2(
    env_lookup: EnvelopeLookup, *, code: str
) -> tuple[float, float, float]:
    """Return (production, demolition, biogenic) intensities in kgCO2e/m2 for an envelope code.

    Mirrors the logic in `cea.analysis.lca.emission_timeline`:
    - Prefer detailed `GHG_production_kgCO2m2` + `GHG_recycling_kgCO2m2` if present.
    - Otherwise fall back to `GHG_kgCO2m2` and assume zero demolition.
    """
    code_str = str(code)
    try:
        production_any = env_lookup.get_item_value(code_str, "GHG_production_kgCO2m2")
        demolition_any = env_lookup.get_item_value(code_str, "GHG_recycling_kgCO2m2")
    except KeyError:
        production_any = env_lookup.get_item_value(code_str, "GHG_kgCO2m2")
        demolition_any = 0.0

    biogenic_any = env_lookup.get_item_value(code_str, "GHG_biogenic_kgCO2m2")
    if production_any is None or demolition_any is None or biogenic_any is None:
        raise ValueError(
            f"Envelope database returned None for one of the required fields for item {code_str}."
        )
    return float(production_any), float(demolition_any), float(biogenic_any)


@dataclass(frozen=True)
class MaterialLayer:
    name: str
    thickness_m: float


def _empty_layers() -> list[MaterialLayer]:
    """Return a fixed 3-slot layer list representing "no material".

    CEA envelope databases are authored with three material/thickness columns
    (`material_name_1..3`, `thickness_1_m..3`). We keep the same topology in-memory
    to simplify type checks and diffing.
    """

    return [MaterialLayer(name="", thickness_m=0.0) for _ in range(3)]


def _coerce_3_layers(layers: list[MaterialLayer] | None) -> list[MaterialLayer]:
    """Normalise a layer list to exactly 3 slots.

    Rules:
    - Pads missing slots with ("", 0.0).
    - Negative thickness is clamped to 0.0.
    - Empty material names imply thickness 0.0.
    """

    src = list(layers) if layers else []
    out: list[MaterialLayer] = []
    for i in range(3):
        if i < len(src):
            name = str(src[i].name or "").strip()
            thickness = float(src[i].thickness_m)
            if thickness < 0.0:
                thickness = 0.0
            if not name:
                thickness = 0.0
            out.append(MaterialLayer(name=name, thickness_m=thickness))
        else:
            out.append(MaterialLayer(name="", thickness_m=0.0))
    return out


def _is_layer_active(layer: MaterialLayer) -> bool:
    """Return True if a layer contributes mass/emissions."""

    return bool(str(layer.name).strip()) and float(layer.thickness_m) > 0.0


def _active_layers(layers: list[MaterialLayer]) -> list[MaterialLayer]:
    return [layer for layer in layers if _is_layer_active(layer)]


@dataclass(frozen=True)
class ArchetypeTimeline:
    """Archetype snapshots + delta events per state year.

    Computed once for the district horizon and reused across all building timelines.

    Covers two distinct families of archetype information:
    1) **Layer-based envelope definitions** (walls/roofs/floors/base/partitions)
       - snapshots: `layers_at_year`
       - events: `layer_events_by_year`
    2) **Code-based construction types** (window + supply system codes)
       - snapshots: `construction_types_at_year`
       - events: `construction_type_events_by_year`

    Example:
        The five attributes on this class are nested dictionaries. The example below shows a "busy" year
        (a year that contains both layer changes and code changes for multiple archetypes).

        ```python
        year = 2005

        years_sorted = [2000, 2005]

        layers_at_year = {
            year: {
                "STANDARD1": {
                    "wall": [
                        MaterialLayer(name="Brick", thickness_m=0.25),
                        MaterialLayer(name="Insulation", thickness_m=0.10),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "roof": [
                        MaterialLayer(name="Concrete", thickness_m=0.20),
                        MaterialLayer(name="Insulation", thickness_m=0.12),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "base": [
                        MaterialLayer(name="Concrete", thickness_m=0.30),
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "floor": [
                        MaterialLayer(name="Concrete", thickness_m=0.25),
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "part": [
                        MaterialLayer(name="Gypsum", thickness_m=0.12),
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                },
            }
        }

        layer_events_by_year = {
            year: {
                "STANDARD1": {
                    "wall": [
                        ("remove", MaterialLayer(name="Brick", thickness_m=0.20)),
                        ("add", MaterialLayer(name="Brick", thickness_m=0.25)),  # replacement of the removed Brick layer
                        ("remove", MaterialLayer(name="", thickness_m=0.0)),
                        ("add", MaterialLayer(name="Insulation", thickness_m=0.10)),  # replacement of empty slot 2
                    ],
                    "roof": [
                        ("remove", MaterialLayer(name="Insulation", thickness_m=0.08)),
                        ("add", MaterialLayer(name="Insulation", thickness_m=0.12)),
                    ],
                },
                "STANDARD2": {
                    "part": [
                        ("remove", MaterialLayer(name="Brick", thickness_m=0.12)),
                        ("add", MaterialLayer(name="Brick", thickness_m=0.10)),
                    ]
                },
            }
        }

        construction_types_at_year = {
            year: {
                "STANDARD1": {
                    "type_win": "WIN_CODE_B",
                    "supply_type_hs": "HS_CODE_9",
                    "supply_type_cs": "CS_CODE_2",
                    "supply_type_dhw": "DHW_CODE_3",
                    "supply_type_el": "EL_CODE_4",
                },
                "STANDARD2": {
                    "type_win": "WIN_CODE_A",
                    "supply_type_hs": "HS_CODE_1",
                    "supply_type_cs": "CS_CODE_2",
                    "supply_type_dhw": "DHW_CODE_3",
                    "supply_type_el": "EL_CODE_4",
                },
            }
        }

        construction_type_events_by_year = {
            year: {
                "STANDARD1": {
                    "type_win": ("WIN_CODE_A", "WIN_CODE_B"), # old code, new code
                    "supply_type_hs": ("HS_CODE_1", "HS_CODE_9"), # old code, new code
                },
            }
        }
        ```

        Notes:
        - For "snapshot" dicts (`layers_at_year`, `construction_types_at_year`), the inner maps represent the
          *full cumulative state effective in that year*.
        - For "events" dicts (`layer_events_by_year`, `construction_type_events_by_year`), the inner maps represent
                    *only the deltas authored in that specific state year*.
                - For layer events, we model edits as **slot replacements**: any slot change yields a `remove` + `add` pair.
                    This applies even when transitioning from/to an "empty" layer slot (`name==""` and `thickness_m==0.0`).
                - For code events, values are stored as `(old_code, new_code)` tuples to represent a transition in that year;
                    the corresponding snapshot (`construction_types_at_year[year][const_type][field]`) stores only the
                    effective *current* code.
    """

    years_sorted: list[int]
    layers_at_year: dict[int, dict[str, dict[str, list[MaterialLayer]]]]
    layer_events_by_year: dict[int, dict[str, dict[str, list[tuple[str, MaterialLayer]]]]]
    construction_types_at_year: dict[int, dict[str, dict[str, str]]]
    construction_type_events_by_year: dict[int, dict[str, dict[str, tuple[str, str]]]]

    def layers_snapshot_at_or_before(self, year: int) -> dict[str, dict[str, list[MaterialLayer]]]:
        """Return the cumulative layer snapshot effective at (or before) a year.

        This snapshot contains **layer/material-based** envelope definitions only.
        For **code-based** construction types (windows + supply system codes), use
        `construction_types_snapshot_at_or_before`.

        Selection logic:
        - If a snapshot exists exactly at `year`, return it.
        - Otherwise return the latest snapshot with `snapshot_year <= year` (carry-forward).
        - If no earlier snapshot exists, return `{}`.

        Example:
            Suppose the district log defines state years `[2000, 2005]`.

            - `layers_snapshot_at_or_before(2000)` returns the baseline snapshot.
            - `layers_snapshot_at_or_before(2003)` returns the 2000 snapshot (carry-forward).
            - `layers_snapshot_at_or_before(2005)` returns the modified snapshot (after 2005 edits).
            - `layers_snapshot_at_or_before(1990)` returns `{}`.

            Shape of a snapshot:
            {
                "STANDARD1": {
                    "wall": [
                        MaterialLayer(name="Brick", thickness_m=0.20),
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "roof": [
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "base": [
                        MaterialLayer(name="Concrete", thickness_m=0.30),
                        MaterialLayer(name="", thickness_m=0.0),
                        MaterialLayer(name="", thickness_m=0.0),
                    ],
                    "floor": [...],
                    "part": [...],
                },
                "STANDARD2": {...},
            }

            To get the **full** archetype state (layers + codes) for a year, read both snapshots:

            ```python
            layers = timeline.layers_snapshot_at_or_before(2005)
            codes = timeline.construction_types_snapshot_at_or_before(2005)

            layers_std1 = layers.get("STANDARD1", {})
            codes_std1 = codes.get("STANDARD1", {})
            win_code = codes_std1.get("type_win")
            hs_code = codes_std1.get("supply_type_hs")
            ```
        """
        year_int = int(year)
        if year_int in self.layers_at_year:
            return dict(self.layers_at_year.get(year_int, {}) or {})
        prior_years = [y for y in self.years_sorted if y <= year_int]
        if not prior_years:
            return {}
        return dict(self.layers_at_year.get(prior_years[-1], {}) or {})

    def events_for_year(self, year: int) -> dict[str, dict[str, list[tuple[str, MaterialLayer]]]]:
        """Return layer delta events authored in the YAML log for a specific year.

        Returns only the changes authored *in that year*, not the full cumulative snapshot.

        Slot-based example:
            If in 2005 the log changes `STANDARD1.wall` slot 1 from `Brick 0.20m` to `Brick 0.25m`, then:

            {
                "STANDARD1": {
                    "wall": [
                        ("remove", MaterialLayer(name="Brick", thickness_m=0.20)),
                        ("add",    MaterialLayer(name="Brick", thickness_m=0.25)),
                    ]
                }
            }
        """
        return dict(self.layer_events_by_year.get(int(year), {}) or {})

    def construction_types_snapshot_at_or_before(self, year: int) -> dict[str, dict[str, str]]:
        """Return cumulative construction-type codes effective at (or before) a year.

        This is the code-based analogue of `layers_snapshot_at_or_before`.
        To retrieve both code-based and layer-based snapshots, call both accessors.

        Example:
            {
                "STANDARD1": {
                    "type_win": "WIN_CODE_A",
                    "supply_type_hs": "HS_CODE_1",
                    "supply_type_cs": "CS_CODE_2",
                    "supply_type_dhw": "DHW_CODE_3",
                    "supply_type_el": "EL_CODE_4",
                },
                ...
            }
        """
        year_int = int(year)
        if year_int in self.construction_types_at_year:
            return dict(self.construction_types_at_year.get(year_int, {}) or {})
        prior_years = [y for y in self.years_sorted if y <= year_int]
        if not prior_years:
            return {}
        return dict(self.construction_types_at_year.get(prior_years[-1], {}) or {})

    def construction_type_events_for_year(self, year: int) -> dict[str, dict[str, tuple[str, str]]]:
        """Return delta construction-type changes authored in a specific state year.

        Entries are stored as `(old_code, new_code)` tuples.

        Example:
            {
                "STANDARD1": {
                    "type_win": ("WIN_CODE_A", "WIN_CODE_B"),
                    "supply_type_hs": ("HS_CODE_1", "HS_CODE_9"),
                }
            }
        """
        return dict(self.construction_type_events_by_year.get(int(year), {}) or {})


def _prepare_archetype_timeline(
    *,
    years_sorted: list[int],
    base_year: int | None,
    log_data: Mapping[int, dict[str, Any]],
    archetype_layers: dict[str, dict[str, list[MaterialLayer]]],
    archetype_construction_types: dict[str, dict[str, str]],
) -> ArchetypeTimeline:
    """Prepare per-year archetype snapshots + delta events from the district YAML log.

        Notes:
        - Mutates `archetype_layers` / `archetype_construction_types` in-place as it applies cumulative modifications.
        - Returned snapshots (`layers_at_year`, `construction_types_at_year`) are copies and safe to reuse.
        - If `base_year` is provided and is earlier than the first state year, we insert a baseline snapshot at
            `base_year` using the main-scenario construction databases. This lets buildings constructed before the
            first simulated/logged state year still use the baseline constructions (and then carry them forward).
    """
    archetype_layer_events_by_year: dict[int, dict[str, dict[str, list[tuple[str, MaterialLayer]]]]] = {}
    archetype_layers_at_year: dict[int, dict[str, dict[str, list[MaterialLayer]]]] = {}
    archetype_construction_at_year: dict[int, dict[str, dict[str, str]]] = {}
    archetype_construction_events_by_year: dict[int, dict[str, dict[str, tuple[str, str]]]] = {}

    if not years_sorted:
        return ArchetypeTimeline(
            years_sorted=[],
            layers_at_year={},
            layer_events_by_year={},
            construction_types_at_year={},
            construction_type_events_by_year={},
        )

    effective_years = list(years_sorted)
    if base_year is not None and int(base_year) < int(min(years_sorted)):
        effective_years = sorted({int(base_year), *[int(y) for y in years_sorted]})

        base = int(base_year)
        archetype_layer_events_by_year[base] = {}
        archetype_layers_at_year[base] = {
            a: {c: layers[:] for c, layers in comps.items()}
            for a, comps in archetype_layers.items()
        }
        archetype_construction_events_by_year[base] = {}
        archetype_construction_at_year[base] = {a: dict(codes) for a, codes in archetype_construction_types.items()}

    for year in effective_years:
        entry = log_data.get(year, {}) or {}
        year_mods = entry.get("modifications", {}) or {}
        year_events: dict[str, dict[str, list[tuple[str, MaterialLayer]]]] = {}
        year_construction_events: dict[str, dict[str, tuple[str, str]]] = {}

        for archetype, components in year_mods.items():
            archetype = str(archetype)
            if archetype not in archetype_layers:
                continue
            for component, patch in (components or {}).items():
                component = str(component)
                if component == "construction_type":
                    patch_dict = dict(patch or {})
                    current = archetype_construction_types.setdefault(archetype, {})
                    for k, v in patch_dict.items():
                        if v is None:
                            continue
                        key = str(k)
                        new_val = str(v)
                        old_val = str(current.get(key, ""))
                        if new_val and new_val != old_val:
                            year_construction_events.setdefault(archetype, {})[key] = (old_val, new_val)
                            current[key] = new_val
                    continue

                if component == "supply_systems":
                    # Operational supply system configuration is handled by the state simulations.
                    continue
                if component not in _LAYERED_COMPONENT_TO_DB:
                    raise ValueError(
                        f"Unsupported modified component '{component}' in district timeline log. "
                        f"Supported components: {sorted(_LAYERED_COMPONENT_TO_DB.keys())}"
                    )
                old_layers = archetype_layers[archetype].get(component)
                new_layers = _apply_layer_patch(old_layers, patch or {})
                events = _diff_layers(old_layers, new_layers)
                if events:
                    year_events.setdefault(archetype, {})[component] = events
                archetype_layers[archetype][component] = new_layers

        archetype_layer_events_by_year[year] = year_events
        archetype_layers_at_year[year] = {
            a: {c: layers[:] for c, layers in comps.items()}
            for a, comps in archetype_layers.items()
        }
        archetype_construction_events_by_year[year] = year_construction_events
        archetype_construction_at_year[year] = {
            a: dict(codes) for a, codes in archetype_construction_types.items()
        }

    return ArchetypeTimeline(
        years_sorted=list(effective_years),
        layers_at_year=archetype_layers_at_year,
        layer_events_by_year=archetype_layer_events_by_year,
        construction_types_at_year=archetype_construction_at_year,
        construction_type_events_by_year=archetype_construction_events_by_year,
    )


class MaterialChangeEmissionTimeline(BaseYearlyEmissionTimeline):
    """Building-level *event* timeline driven by the district YAML log."""

    def __init__(
        self,
        *,
        name: str,
        locator: InputLocator,
    ):
        self.construction_year: int | None = None
        self.demolition_year: int | None = None
        self.window_code: str = ""
        self.supply_codes: dict[str, str] = {}
        self._notes_by_year: dict[str, list[str]] = {}
        super().__init__(name=name, locator=locator)

    def add_note(self, *, year: int, message: str) -> None:
        label = f"Y_{int(year)}"
        if label not in self.timeline.index:
            return
        msg = str(message).strip()
        if not msg:
            return
        self._notes_by_year.setdefault(label, [])
        if msg not in self._notes_by_year[label]:
            self._notes_by_year[label].append(msg)

    def notes_series(self) -> pd.Series:
        """Return a year-indexed Series of notes, aligned to the timeline index."""
        out = pd.Series(index=self.timeline.index, dtype=object)
        for label in self.timeline.index:
            msgs = self._notes_by_year.get(str(label), [])
            out.at[label] = " | ".join(msgs) if msgs else ""
        return out

    def set_existence(self, *, construction_year: int, demolition_year: int | None) -> None:
        self.construction_year = int(construction_year)
        self.demolition_year = int(demolition_year) if demolition_year is not None else None
        self.add_note(year=int(construction_year), message="Constructed")

    def exists_at(self, year: int) -> bool:
        if self.construction_year is None:
            return False
        if year < self.construction_year:
            return False
        if self.demolition_year is not None and year >= self.demolition_year:
            return False
        return True

    @staticmethod
    def layers_snapshot_at_or_before(
        layers_by_year: Mapping[int, dict[str, dict[str, list[MaterialLayer]]]],
        years_sorted: list[int],
        year: int,
    ) -> dict[str, dict[str, list[MaterialLayer]]]:
        if year in layers_by_year:
            return dict(layers_by_year.get(year, {}) or {})
        prior_years = [y for y in years_sorted if y <= year]
        if not prior_years:
            return {}
        return dict(layers_by_year.get(prior_years[-1], {}) or {})

    def fill_operational_step_function(
        self,
        *,
        state_years_sorted: list[int],
        end_year: int,
        operational_by_state_year: Mapping[int, pd.DataFrame | None],
        allow_missing_operational: bool,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
    ) -> None:
        """Fill `operation_*_kgCO2e` between available state years.

        Source of truth is the per-state-year operational-by-building output (from the `emissions` script).
                This method:
                - selects the latest known per-building *per-demand/per-feedstock* emissions for each state year
                - carries them forward until the next state year (step function on demand / technology)
                - builds a continuous per-year operational timeline for the building
                - applies any configured `feedstock_policies` (e.g., GRID decarbonisation) **after** the
                    continuous timeline is assembled

        Operational is set to 0 for years before construction, and for years >= demolition (if any).
        Args:
            years_sorted: Sorted list of state years available in the log 
                (some years are missing because of no construction change or no new building).
            end_year: Last year to fill in the timeline.
            operational_by_state_year: Mapping of state year -> district operational emissions DataFrame.
                Each dataframe constains yearly operational emission of all buildings for that state year.
                Each row is indexed by the name of a building, each column is in format of 
                `{demand_type}_{feedstock}_kgCO2e`.
            allow_missing_operational: If True, carry forward last known operational data when missing for a state year.
            feedstock_policies: Optional feedstock policies to apply after building the continuous timeline.
        """
        if self.construction_year is None:
            return
        construction_year = self.construction_year
        demolition_year = self.demolition_year

        active_years = [
            y
            for y in range(construction_year, end_year + 1)
            if demolition_year is None or y < demolition_year
        ]
        if not active_years:
            return

        idx_active = [f"Y_{y}" for y in active_years]
        operational_multi_years = pd.DataFrame(index=idx_active)

        last_known: pd.Series[float] | None = None
        for i, state_year in enumerate(state_years_sorted):
            if state_year > end_year:
                break
            df_op_buildings_yearly = operational_by_state_year.get(state_year)
            if df_op_buildings_yearly is not None and self.name in df_op_buildings_yearly.index:
                demand_types = list(_tech_name_mapping.keys())  # Qhs_sys, Qww_sys, Qcs_sys, E_sys
                feedstocks = self.get_available_feedstocks() # capitalized feedstock names + NONE

                op_cols_in_df: list[str] = []
                for demand in demand_types:
                    for fs in feedstocks:
                        c = f"{demand}_{fs}_kgCO2e"
                        if c in df_op_buildings_yearly.columns:
                            op_cols_in_df.append(c)
                # Keep PV offset/export emissions columns if present
                for c in df_op_buildings_yearly.columns:
                    if isinstance(c, str) and c.startswith("PV_") and c.endswith("_kgCO2e"):
                        op_cols_in_df.append(c)
                op_cols_in_df = list(dict.fromkeys(op_cols_in_df))  # deduplicate while preserving order

                op_state_year: pd.Series[float] = (
                    df_op_buildings_yearly.loc[[self.name], op_cols_in_df].iloc[0]
                    if op_cols_in_df
                    else pd.Series(dtype=float)
                )
                last_known = op_state_year
            else:
                if allow_missing_operational and last_known is not None:
                    op_state_year = last_known
                else:
                    op_state_year = pd.Series(dtype=float)

            next_state_year = (
                state_years_sorted[i + 1]
                if i + 1 < len(state_years_sorted)
                else (end_year + 1)
            )
            interval_years = [
                y
                for y in range(state_year, min(next_state_year, end_year + 1))
                if y >= construction_year and (demolition_year is None or y < demolition_year)
            ]
            if not interval_years:
                continue

            idx_interval = [f"Y_{y}" for y in interval_years]
            if op_state_year.empty:
                continue

            # Ensure we have columns available before assignment.
            for c in op_state_year.index:
                if c not in operational_multi_years.columns:
                    operational_multi_years[c] = np.nan

            values = op_state_year.astype(float).to_numpy(dtype=float)
            operational_multi_years.loc[idx_interval, op_state_year.index] = np.tile(values, (len(idx_interval), 1))

        # Years with no state before default to 0.0
        operational_multi_years = operational_multi_years.fillna(0.0).astype(float)

        if feedstock_policies:
            demand_types = list(_tech_name_mapping.keys())
            apply_feedstock_policies_inplace(
                operational_multi_years,
                feedstock_policies=feedstock_policies,
                available_feedstocks=self.get_available_feedstocks(),
                demand_types=demand_types,
            )

        # Aggregate per-demand totals back into the timeline.
        for demand in _tech_name_mapping.keys():
            col = f"operation_{demand}_kgCO2e"
            cols_demand = [
                c
                for c in operational_multi_years.columns
                if isinstance(c, str) and c.startswith(f"{demand}_") and c.endswith("_kgCO2e")
            ]
            values = (
                operational_multi_years[cols_demand].sum(axis=1).to_numpy(dtype=float)
                if cols_demand
                else 0.0
            )
            self.timeline.loc[idx_active, col] = values

    def build_embodied_from_log(
        self,
        *,
        const_type: str,
        area_dict: dict[str, float],
        materials: pd.DataFrame,
        years_sorted: list[int],
        start_year: int,
        end_year: int,
        archetype_timeline: ArchetypeTimeline,
        service_life_by_src_component: Mapping[str, int | None],
    ) -> None:
        """Populate embodied (production / demolition / biogenic) emissions for this building.

        This method interprets the district timeline log as the source of truth for envelope layer changes
        (per archetype / construction standard) and turns those changes into *building-level* emission events.
        The resulting events are written directly into `self.timeline`.

        Behaviour (high level):
        - **Initial construction**: at `construction_year` we add production (+ biogenic uptake) for the
            archetype's layer snapshot effective at/before construction.
        - **Modification events**: in any year where the log defines layer edits for this building's
            `const_type`, we apply deltas (add = production, remove = demolition) for the affected component.
        - **Service-life replacements (mandatory)**: for each envelope component with non-zero area, a full
            replacement is scheduled every `Service_Life` years, starting from construction.
            If a modification affects a component, the replacement "clock" for that component resets to
            `year + Service_Life`.
        - **Demolition**: if `demolition_year` lies within `[start_year, end_year]`, all components will be 
            demolished at the end of that year.

        Notes:
        - Service life values are taken from `service_life_by_src_component` and are required (missing or
            non-positive values raise).
        - The layer snapshots are sourced from `archetype_layers_at_year` and are assumed to already reflect
            the cumulative log edits up to that year.
        - Years outside the building's existence window (before construction, or from demolition onward) are
            not populated.

        Args:
            const_type: Construction standard / archetype key for this building (e.g., `STANDARD1`).
            area_dict: Building surface areas used to scale per-m2 material intensities.
            materials: Materials database (indexed by material name) providing emission factors and density.
            years_sorted: Sorted list of state years present in the district log.
            start_year: First year in the district timeline horizon.
            end_year: Last year in the district timeline horizon.
            archetype_timeline: Precomputed archetype snapshots + delta events (layers + construction types).
            service_life_by_src_component: Mapping `src_component -> Service_Life (years)`.
        """
        if self.construction_year is None:
            return
        construction_year = self.construction_year

        tech_system_keys, tech_quarter_prod, has_layer_snapshot_at_construction = (
            self._init_codes_and_initial_construction(
                const_type=const_type,
                area_dict=area_dict,
                materials=materials,
                construction_year=construction_year,
                archetype_timeline=archetype_timeline,
            )
        )
        if not has_layer_snapshot_at_construction:
            return

        # --- Mandatory service-life replacements ---------------------------------
        # Behaviour:
        # - Each envelope component has a service life (years) from the envelope DB.
        # - Starting from construction, a full replacement is scheduled every service_life years.
        # - Any modification event to that component resets its replacement clock (but does not force a full
        #   replacement in that year; only the logged delta is applied).
        end_active_year = self._compute_end_active_year(end_year)
        if end_active_year < construction_year:
            return

        (
            lifetimes,
            tech_lifetime,
            win_lifetime_default,
            tech_next_due,
            window_next_due,
            envelope_next_due,
        ) = self._prepare_replacement_clocks(
            const_type=const_type,
            area_dict=area_dict,
            service_life_by_src_component=service_life_by_src_component,
            construction_year=construction_year,
        )

        (
            modification_years,
            code_change_years,
            mod_by_year,
        ) = self._collect_events(
            years_sorted=years_sorted,
            const_type=const_type,
            archetype_timeline=archetype_timeline,
        )

        schedule = _BuildingEventCursor(
            modification_years=modification_years,
            code_change_years=code_change_years,
            envelope_next_due=envelope_next_due,
            window_next_due=window_next_due,
            tech_next_due=tech_next_due,
            end_active_year=end_active_year,
        )

        while (year := schedule.next_year()) is not None:
            self._apply_modifications_at_year(
                year=year,
                mod_by_year=mod_by_year,
                lifetimes=lifetimes,
                schedule=schedule,
                area_dict=area_dict,
                materials=materials,
            )

            self._apply_code_changes_at_year(
                year=year,
                const_type=const_type,
                archetype_timeline=archetype_timeline,
                area_dict=area_dict,
                tech_system_keys=tech_system_keys,
                tech_quarter_prod=tech_quarter_prod,
                tech_lifetime=tech_lifetime,
                win_lifetime_default=win_lifetime_default,
                schedule=schedule,
            )

            self._apply_due_replacements_at_year(
                year=year,
                const_type=const_type,
                archetype_timeline=archetype_timeline,
                area_dict=area_dict,
                materials=materials,
                lifetimes=lifetimes,
                win_lifetime_default=win_lifetime_default,
                schedule=schedule,
            )

        if self.demolition_year is not None and start_year <= self.demolition_year <= end_year:
            layers_snapshot = archetype_timeline.layers_snapshot_at_or_before(self.demolition_year)
            self.add_demolition(
                year=self.demolition_year,
                const_type=const_type,
                area_dict=area_dict,
                materials=materials,
                layers_snapshot=layers_snapshot,
                comp_area_map=_COMP_AREA_MAP,
            )
            self.add_note(year=int(self.demolition_year), message="Demolished")

    def _init_codes_and_initial_construction(
        self,
        *,
        const_type: str,
        area_dict: dict[str, float],
        materials: pd.DataFrame,
        construction_year: int,
        archetype_timeline: ArchetypeTimeline,
    ) -> tuple[dict[str, str], float, bool]:
        """Initialise code-based state and write initial embodied events.

        Reads the construction-type snapshot effective at the building's construction year and sets:
        - `self.window_code`
        - `self.supply_codes`

        Then applies initial embodied emissions:
        - Layered envelope components from the layer snapshot (production + biogenic uptake)
        - Technical systems as 4 independent quarters (production only) scaled by `Atechnical_systems`

        Returns:
            (tech_system_keys, tech_quarter_prod, has_layer_snapshot_at_construction)

        Notes:
                - `has_layer_snapshot_at_construction=False` indicates there is no layer snapshot at/before
                    construction. In that case, the embodied timeline is not produced (matching prior behaviour).
        - This method writes directly into `self.timeline`.
        """
        ct_snapshot = archetype_timeline.construction_types_snapshot_at_or_before(construction_year)
        ct_codes = ct_snapshot.get(str(const_type), {}) or {}
        win_code = str(ct_codes.get(_CONSTRUCTION_TYPE_WIN_FIELD, ""))
        if win_code:
            self.window_code = win_code
        self.supply_codes = {k: str(ct_codes.get(k, "")) for k in _SUPPLY_TYPE_FIELDS}

        layers_snapshot = archetype_timeline.layers_snapshot_at_or_before(construction_year)
        if str(const_type) not in layers_snapshot:
            self.add_note(
                year=int(construction_year),
                message="No envelope layer snapshot available for this construction type; skipping embodied emissions.",
            )
            return (
                dict(_TECH_SYSTEM_COMPONENT_BY_SUPPLY_FIELD),
                float(EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS) / 4.0, # total emission intensity distributed in four systems
                False,
            )
        self.add_initial_construction(
            year=construction_year,
            const_type=const_type,
            area_dict=area_dict,
            materials=materials,
            layers_snapshot=layers_snapshot,
            comp_area_map=_COMP_AREA_MAP,
        )

        tech_quarter_prod = float(EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS) / 4.0
        tech_system_keys = dict(_TECH_SYSTEM_COMPONENT_BY_SUPPLY_FIELD)
        area_tech = float(area_dict.get("Atechnical_systems", 0.0))
        if area_tech > 0:
            for sys_component in tech_system_keys.values():
                self.add_phase_component(
                    year=construction_year,
                    phase="production",
                    component=sys_component,
                    value_kgco2e=tech_quarter_prod * area_tech,
                )
        return tech_system_keys, tech_quarter_prod, True

    def _compute_end_active_year(self, end_year: int) -> int:
        """Return the last year in which the building is active.

        If `self.demolition_year` is set, the last active year is `demolition_year - 1`.
        Otherwise, it is `end_year`.
        """
        end_active_year = end_year
        if self.demolition_year is not None:
            end_active_year = min(end_active_year, self.demolition_year - 1)
        return int(end_active_year)

    def _prepare_replacement_clocks(
        self,
        *,
        const_type: str,
        area_dict: dict[str, float],
        service_life_by_src_component: Mapping[str, int | None],
        construction_year: int,
    ) -> tuple[dict[str, int], int, int, dict[str, int], int | None, dict[str, int]]:
        """Compute service-life replacement clocks for the building.

        This sets up the per-building 'due years' used by `_BuildingEventCursor`:
        - `envelope_next_due`: layered envelope components (wall/roof/base/floor/part)
        - `window_next_due`: windows (code-dependent service life)
        - `tech_next_due`: technical quarters (hs/cs/dhw/el), sharing a common service life

        Inputs:
        - `area_dict` is used to skip components with zero area.
        - `service_life_by_src_component` provides mandatory service lives for envelope + windows.

        Output:
        - Returns the lifetimes/clocks needed by the main per-year loop.
        - Raises `ValueError` if required service life values are missing or non-positive.

                Example shapes:
                - `lifetimes` (layered envelope only):

                    ```python
                    {
                            "wall": 30,
                            "roof": 40,
                            "base": 60,
                            "floor": 50,
                            "part": 30,
                    }
                    ```

                - `envelope_next_due` (when each layered envelope component is next replaced):

                    ```python
                    {
                            "wall": 2030,   # construction_year + lifetimes["wall"]
                            "roof": 2040,
                            "base": 2060,
                    }
                    ```

                - `tech_next_due` (one clock per technical quarter):

                    ```python
                    {
                            "technical_system_hs": 2035,
                            "technical_system_cs": 2035,
                            "technical_system_dhw": 2035,
                            "technical_system_el": 2035,
                    }
                    ```

                - `window_next_due`:
                    - `None` if the window lifetime cannot be determined
                    - otherwise an integer year, e.g. `2025`
        """
        areas_by_src_component: dict[str, float] = {}
        for _, comp_src, area_key in _COMP_AREA_MAP:
            areas_by_src_component[comp_src] = areas_by_src_component.get(comp_src, 0.0) + float(area_dict.get(area_key, 0.0))

        lifetimes: dict[str, int] = {}
        for src_component, total_area in areas_by_src_component.items():
            if total_area <= 0:
                continue
            if src_component in ("technical_systems", "win"):
                continue
            lifetime_any = service_life_by_src_component.get(src_component)
            if lifetime_any is None:
                raise ValueError(
                    f"Missing Service_Life for component '{src_component}' (const_type={const_type}). "
                    "Service life is mandatory for the district material timeline replacement scheduling."
                )
            lifetime = int(lifetime_any)
            if lifetime <= 0:
                raise ValueError(
                    f"Invalid Service_Life={lifetime} for component '{src_component}' (const_type={const_type})."
                )
            lifetimes[src_component] = lifetime

        tech_lifetime_any = service_life_by_src_component.get("technical_systems")
        tech_lifetime = int(tech_lifetime_any) if tech_lifetime_any is not None else int(SERVICE_LIFE_OF_TECHNICAL_SYSTEMS)
        if tech_lifetime <= 0:
            raise ValueError(
                f"Invalid Service_Life={tech_lifetime} for component 'technical_systems' (const_type={const_type})."
            )

        win_lifetime_default_any = service_life_by_src_component.get("win")
        if win_lifetime_default_any is None:
            raise ValueError(
                f"Missing Service_Life for component 'win' (const_type={const_type}). "
                "Service life is mandatory for window replacement scheduling."
            )
        win_lifetime_default = int(win_lifetime_default_any)
        if win_lifetime_default <= 0:
            raise ValueError(
                f"Invalid Service_Life={win_lifetime_default} for component 'win' (const_type={const_type})."
            )

        tech_next_due: dict[str, int] = {
            sys_comp: construction_year + tech_lifetime for sys_comp in _TECH_SYSTEM_COMPONENT_BY_SUPPLY_FIELD.values()
        }
        win_lt_any = self.envelope_lookup.get_item_value(str(self.window_code), "Service_Life")
        window_lifetime = int(win_lt_any) if win_lt_any is not None else win_lifetime_default
        window_next_due = construction_year + window_lifetime if window_lifetime > 0 else None
        envelope_next_due: dict[str, int] = {src: construction_year + lt for src, lt in lifetimes.items()}
        return lifetimes, tech_lifetime, win_lifetime_default, tech_next_due, window_next_due, envelope_next_due

    def _collect_events(
        self,
        *,
        years_sorted: list[int],
        const_type: str,
        archetype_timeline: ArchetypeTimeline,
    ) -> tuple[list[int], list[int], dict[int, dict[str, list[tuple[str, MaterialLayer]]]]]:
        """Collect authored modification and code-change years for this building.

        Filters the district state years down to those relevant for this building:
        - Modification years: layer deltas exist for this `const_type` and building exists.
        - Code-change years: construction-type patch exists for this `const_type` and building exists.

        Output:
        - `modification_years`: sorted list of years
        - `code_change_years`: sorted list of years
        - `mod_by_year`: mapping year -> src_component -> list[(action, layer)]

        Example shapes:
        - `modification_years` / `code_change_years`:

          ```python
          modification_years = [2005, 2010]
          code_change_years = [2005]
          ```

        - `mod_by_year`:

          ```python
          {
              2005: {
                  "wall": [
                      ("remove", MaterialLayer(name="Brick", thickness_m=0.20)),
                      ("add",    MaterialLayer(name="Brick", thickness_m=0.25)),
                  ],
                  "roof": [
                      ("add", MaterialLayer(name="Insulation", thickness_m=0.10)),
                  ],
              },
              2010: {
                  "floor": [
                      ("remove", MaterialLayer(name="Concrete", thickness_m=0.30)),
                      ("add",    MaterialLayer(name="Concrete", thickness_m=0.25)),
                  ],
              },
          }
          ```

        Notes:
        - The outer key is the *state year* where the log authored changes.
        - The second key is the *src_component* (e.g., `wall`, `roof`, `base`, `floor`, `part`).
        - The event list is slot-based: changing a slot yields a remove+add pair.
        """
        modification_years: list[int] = [
            y
            for y in years_sorted
            if self.exists_at(y)
            and const_type in (archetype_timeline.events_for_year(y) or {})
        ]
        code_change_years: list[int] = [
            y
            for y in years_sorted
            if self.exists_at(y)
            and const_type in (archetype_timeline.construction_type_events_for_year(y) or {})
        ]
        mod_by_year: dict[int, dict[str, list[tuple[str, MaterialLayer]]]] = {}
        for y in modification_years:
            year_events = archetype_timeline.events_for_year(y)
            mod_by_year[y] = dict((year_events.get(const_type, {}) or {}))
        return modification_years, code_change_years, mod_by_year

    def _apply_modifications_at_year(
        self,
        *,
        year: int,
        mod_by_year: Mapping[int, dict[str, list[tuple[str, MaterialLayer]]]],
        lifetimes: Mapping[str, int],
        schedule: _BuildingEventCursor,
        area_dict: Mapping[str, float],
        materials: pd.DataFrame,
    ) -> None:
        """Apply authored layer modifications for `year` (if any).

        Iteration semantics:
        - Only runs when `schedule.consume_mod_if(year)` is true.
        - Writes emission deltas (add = production + biogenic, remove = demolition).
        - Resets the service-life replacement clock for any modified component.

        Side effects:
        - Mutates `self.timeline` and `schedule.envelope_next_due`.
        """
        if schedule.advance_envelope_mod_if(year):
            year_mods = mod_by_year.get(year, {})
            for src_component, events in year_mods.items():
                if events:
                    removed = [f"-{layer.name} {layer.thickness_m:.3f}m" for action, layer in events if action == "remove"]
                    added = [f"+{layer.name} {layer.thickness_m:.3f}m" for action, layer in events if action == "add"]
                    parts = [p for p in (removed + added) if p]
                    detail = ", ".join(parts) if parts else ""
                    msg = f"Modified {src_component}" + (f": {detail}" if detail else "")
                    self.add_note(year=int(year), message=msg)
                self.add_modification_events(
                    year=year,
                    events=events,
                    src_component=src_component,
                    area_dict=dict(area_dict),
                    materials=materials,
                    comp_area_map=_COMP_AREA_MAP,
                )
                if src_component in lifetimes:
                    schedule.envelope_next_due[src_component] = year + int(lifetimes[src_component])

    def _apply_code_changes_at_year(
        self,
        *,
        year: int,
        const_type: str,
        archetype_timeline: ArchetypeTimeline,
        area_dict: Mapping[str, float],
        tech_system_keys: Mapping[str, str],
        tech_quarter_prod: float,
        tech_lifetime: int,
        win_lifetime_default: int,
        schedule: _BuildingEventCursor,
    ) -> None:
        """Apply code-based changes (windows + supply systems) for `year` (if any).

        Runs only when `schedule.consume_code_if(year)` is true.

        Window code changes:
        - A change in `type_win` triggers a full window replacement old -> new.
        - Writes demolition of old (using old-code demolition intensity) and production+biogenic of new.
        - Updates `self.window_code` and resets `schedule.window_next_due` using the new code's service life.

        Supply system code changes:
        - Each supply field change triggers production for the corresponding technical quarter.
        - Resets that quarter's due year to `year + tech_lifetime`.

        Side effects:
        - Mutates `self.timeline`, `self.window_code`, `self.supply_codes`, and the `schedule` clocks.
        """
        if not schedule.advance_code_if(year):
            return
        patch = (
            archetype_timeline.construction_type_events_for_year(int(year)).get(str(const_type), {})
            or {}
        )
        if _CONSTRUCTION_TYPE_WIN_FIELD in patch:
            change = _parse_code_change(patch.get(_CONSTRUCTION_TYPE_WIN_FIELD))
            if change is not None:
                old_code, new_code = change
                if new_code and new_code != old_code:
                    area_win = float(area_dict.get("Awin_ag", 0.0))
                    if area_win > 0:
                        prod_new, _, bio_new = _envelope_intensities_per_m2(self.envelope_lookup, code=new_code)
                        _, demo_old, _ = _envelope_intensities_per_m2(self.envelope_lookup, code=old_code)
                        self.add_phase_component(year=year, phase="demolition", component="win_ag", value_kgco2e=demo_old * area_win)
                        self.add_phase_component(year=year, phase="production", component="win_ag", value_kgco2e=prod_new * area_win)
                        self.add_phase_component(year=year, phase="biogenic", component="win_ag", value_kgco2e=(-bio_new) * area_win)
                    self.add_note(year=int(year), message=f"Window code changed: {old_code} -> {new_code}")
                    self.window_code = new_code
                    win_lt_any = self.envelope_lookup.get_item_value(str(self.window_code), "Service_Life")
                    win_lifetime_new = int(win_lt_any) if win_lt_any is not None else win_lifetime_default
                    schedule.window_next_due = int(year) + win_lifetime_new if win_lifetime_new > 0 else None

        area_tech = float(area_dict.get("Atechnical_systems", 0.0))
        for supply_field, sys_component in tech_system_keys.items():
            if supply_field not in patch:
                continue
            change = _parse_code_change(patch.get(supply_field))
            if change is None:
                continue
            old_code, new_code = change
            if new_code and new_code != old_code:
                if area_tech > 0:
                    self.add_phase_component(year=year, phase="production", component=sys_component, value_kgco2e=tech_quarter_prod * area_tech)
                label = supply_field.replace("supply_type_", "")
                self.add_note(year=int(year), message=f"Supply system changed ({label}): {old_code} -> {new_code}")
                self.supply_codes[supply_field] = new_code
                schedule.tech_next_due[sys_component] = int(year) + int(tech_lifetime)

    def _apply_due_replacements_at_year(
        self,
        *,
        year: int,
        const_type: str,
        archetype_timeline: ArchetypeTimeline,
        area_dict: Mapping[str, float],
        materials: pd.DataFrame,
        lifetimes: Mapping[str, int],
        win_lifetime_default: int,
        schedule: _BuildingEventCursor,
    ) -> None:
        """Apply any service-life replacements due in `year`.

        Ordering:
        - This is called after authored modifications and code-changes for the same year.
          That ensures same-year authored edits are applied first, and then (if still due) the
          scheduled full replacement is applied.

        Replacement rules:
        - Layered envelope components: full replacement using the layer snapshot at/before `year`.
        - Windows: full replacement using current `self.window_code` and code-dependent service life.

        Side effects:
        - Mutates `self.timeline` and updates the `schedule` due years.
        """
        due_components = schedule.due_envelope_components(year)
        if due_components:
            layers_snapshot = archetype_timeline.layers_snapshot_at_or_before(year)
            current_layers = layers_snapshot.get(const_type, {})
            for src_component in due_components:
                layers = current_layers.get(src_component, _empty_layers())
                layer_desc = ", ".join([f"{ly.name or '-'} {ly.thickness_m:.3f}m" for ly in layers])
                self.add_note(year=int(year), message=f"Service life reached: {src_component} (replace {layer_desc})")
                self.add_full_replacement(
                    year=year,
                    src_component=src_component,
                    area_dict=dict(area_dict),
                    materials=materials,
                    layers=layers,
                    comp_area_map=_COMP_AREA_MAP,
                )
                schedule.envelope_next_due[src_component] = year + int(lifetimes[src_component])

        if schedule.is_window_due(year):
            self.add_note(year=int(year), message="Service life reached: windows")
            self.add_full_replacement(
                year=year,
                src_component="win",
                area_dict=dict(area_dict),
                materials=materials,
                layers=[],
                comp_area_map=_COMP_AREA_MAP,
            )
            win_lt_any = self.envelope_lookup.get_item_value(str(self.window_code), "Service_Life")
            win_lifetime_new = int(win_lt_any) if win_lt_any is not None else win_lifetime_default
            if win_lifetime_new > 0:
                schedule.window_next_due = int(year) + win_lifetime_new

    def add_full_replacement(
        self,
        *,
        year: int,
        src_component: str,
        area_dict: dict[str, float],
        materials: pd.DataFrame,
        layers: list[MaterialLayer],
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        """Log a full replacement of the given component (demolish old + rebuild same).

        Biogenic carbon is treated as stored in materials (negative at production) and no end-of-life release
        is assumed (no positive biogenic term at demolition/removal), consistent with existing CEA net-emissions
        plotting assumptions.
        """
        for comp, comp_src, area_key in comp_area_map:
            if comp_src != src_component:
                continue
            area = float(area_dict.get(area_key, 0.0))
            if area <= 0:
                continue
            if comp_src == "technical_systems":
                prod = float(EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS)
                self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                continue

            if comp_src == "win":
                prod, demo, bio = _envelope_intensities_per_m2(self.envelope_lookup, code=self.window_code)
                self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
                continue

            active = _active_layers(layers)
            if active:
                for layer in active:
                    prod, demo, bio = _material_intensity_per_m2(materials, layer)
                    self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                    self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                    self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
                continue

            # Not resolvable to layered materials and not covered by an alternative model.
            continue
    def add_initial_construction(
        self,
        *,
        year: int,
        const_type: str,
        area_dict: dict[str, float],
        materials: pd.DataFrame,
        layers_snapshot: dict[str, dict[str, list[MaterialLayer]]],
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        """Add initial construction embodied emissions for this building.

        Writes production + biogenic (negative) terms at the given `year` using:
        - Layer snapshots for material-based components
        - Current `self.window_code` for window assemblies

        Technical systems are intentionally skipped here and handled separately as 4 quarters.
        """
        current_layers = layers_snapshot.get(const_type, {})
        for comp, src_component, area_key in comp_area_map:
            area = float(area_dict.get(area_key, 0.0))
            if area <= 0:
                continue
            if src_component == "technical_systems":
                # Technical systems are handled separately as 4 quarters in `build_embodied_from_log`.
                continue

            if src_component == "win":
                prod, _, bio = _envelope_intensities_per_m2(self.envelope_lookup, code=self.window_code)
                self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
                continue

            layers = current_layers.get(src_component, _empty_layers())
            events = _diff_layers(_empty_layers(), layers)
            if events:
                for _, layer in events:
                    prod, _, bio = _material_intensity_per_m2(materials, layer)
                    self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                    self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
                continue

            # Not resolvable to layered materials and not covered by an alternative model.
            continue

    def add_modification_events(
        self,
        *,
        year: int,
        events: list[tuple[str, MaterialLayer]],
        src_component: str,
        area_dict: dict[str, float],
        materials: pd.DataFrame,
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        """Apply a list of layer add/remove events for a single source component.

        Inputs:
        - `events` are produced by `_diff_layers` and are interpreted as:
          - "add"    -> production + biogenic
          - "remove" -> demolition

        Output:
        - Writes to `self.timeline` for the specified `year`.
        """
        for comp, comp_src, area_key in comp_area_map:
            if comp_src != src_component:
                continue
            area = float(area_dict.get(area_key, 0.0))
            if area <= 0:
                continue
            if comp_src == "technical_systems":
                continue
            for action, layer in events:
                prod, demo, bio = _material_intensity_per_m2(materials, layer)
                if action == "add":
                    self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                    self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
                else:
                    self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)

    def add_demolition(
        self,
        *,
        year: int,
        const_type: str,
        area_dict: dict[str, float],
        materials: pd.DataFrame,
        layers_snapshot: dict[str, dict[str, list[MaterialLayer]]],
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        """Add demolition embodied emissions for the given `year`.

        Writes demolition terms for:
        - Material-based components using layer snapshot at/before demolition
        - Windows using current `self.window_code`

        Technical systems are intentionally skipped (handled separately in the main loop).
        """
        current_layers = layers_snapshot.get(const_type, {})
        for comp, src_component, area_key in comp_area_map:
            area = float(area_dict.get(area_key, 0.0))
            if area <= 0:
                continue
            if src_component == "technical_systems":
                continue

            if src_component == "win":
                _, demo, _ = _envelope_intensities_per_m2(self.envelope_lookup, code=self.window_code)
                self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                continue

            layers = current_layers.get(src_component, _empty_layers())
            events = _diff_layers(_empty_layers(), layers)
            if events:
                for _, layer in events:
                    _, demo, _ = _material_intensity_per_m2(materials, layer)
                    self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                continue

            # Not resolvable to layered materials and not covered by an alternative model.
            continue


def _load_building_const_types(locator: InputLocator) -> dict[str, str]:
    """Return {building_name: const_type} from `zone.shp`.

    The `district_timeline_log.yml` stores modifications keyed by archetype / construction standard
    (e.g., `STANDARD1`). Buildings map to those standards via the `const_type` attribute.
    """
    zone = gpd.read_file(locator.get_zone_geometry())
    if "name" not in zone.columns:
        raise ValueError("Zone geometry is missing required 'name' column.")
    if "const_type" not in zone.columns:
        raise ValueError("Zone geometry is missing required 'const_type' column.")
    out: dict[str, str] = {}
    for _, row in zone.iterrows():
        name = str(row["name"])
        const_type = row["const_type"]
        if const_type is None or (isinstance(const_type, float) and np.isnan(const_type)):
            continue
        out[name] = str(const_type)
    return out


def _building_demolition_years(log_data: dict[int, dict[str, Any]]) -> dict[str, int]:
    """Return {building_name: demolition_year} from YAML building_events."""
    out: dict[str, int] = {}
    for year in sorted(int(y) for y in log_data.keys()):
        entry = log_data.get(year, {}) or {}
        events = entry.get("building_events", {}) or {}
        demolished = events.get("demolished_buildings", []) or []
        for b in demolished:
            name = str(b)
            out.setdefault(name, int(year))
    return out


def _apply_layer_patch(
    old_layers: list[MaterialLayer] | None,
    patch: dict[str, Any],
) -> list[MaterialLayer]:
    """Apply a YAML layer patch (material_name_i / thickness_i_m) to a layer list.

    Patch semantics:
    - Updates only the specified fields.
    - Unspecified slots are carried forward.
    - Slots are 1..3.
    - The returned list always contains exactly 3 slots; thickness may be 0.
    """
    base_layers = _coerce_3_layers(old_layers)
    slots: list[tuple[str, float]] = [(l.name, float(l.thickness_m)) for l in base_layers]

    for i in (1, 2, 3):
        m_key = f"material_name_{i}"
        t_key = f"thickness_{i}_m"
        name, thickness = slots[i - 1]
        if m_key in patch:
            raw = patch.get(m_key)
            # In CEA DB workflows, None/NaN typically means "do not change".
            if raw is not None and not (isinstance(raw, float) and np.isnan(raw)):
                name = str(raw).strip()
        if t_key in patch:
            raw = patch.get(t_key)
            if raw is not None and not (isinstance(raw, float) and np.isnan(raw)):
                thickness = float(raw)

        if thickness < 0.0:
            thickness = 0.0
        if not str(name).strip():
            name = ""
            thickness = 0.0
        slots[i - 1] = (name, float(thickness))

    return [MaterialLayer(name=n, thickness_m=t) for n, t in slots]


def _parse_density(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s == "-":
        return None
    # Handle ranges like '1200-2000'
    if "-" in s and all(p.strip().replace(".", "", 1).isdigit() for p in s.split("-")):
        lo, hi = s.split("-", 1)
        return 0.5 * (float(lo) + float(hi))
    try:
        return float(s)
    except Exception:
        return None


def _to_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float with defensive handling for pandas artefacts.

    Note:
        This function may call itself when `value` is a `pd.Series`. That is deliberate:
        it unwraps the first element (`value.iloc[0]`) and then re-applies the same
        conversion rules to the scalar (None/NaN/str/number). This is not unbounded
        recursion because the second call is typically on a non-Series value.
    """
    if value is None:
        return float(default)
    # pandas often yields NaN floats
    if isinstance(value, float) and np.isnan(value):
        return float(default)
    # guard against accidental Series
    if isinstance(value, pd.Series):
        if len(value) == 0:
            return float(default)
        # Intentional re-entry: unwrap the Series to a scalar and re-apply rules.
        return _to_float(value.iloc[0], default=default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _read_material_db(locator: InputLocator) -> pd.DataFrame:
    path = locator.get_database_components_materials()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Materials database not found: {path}")
    df = pd.read_csv(path)
    if "name" not in df.columns:
        raise ValueError("Materials database missing required 'name' column")
    return df.set_index("name", drop=False)


def _layers_from_envelope_row(row: pd.Series) -> list[MaterialLayer]:
    layers: list[MaterialLayer] = []
    for i in (1, 2, 3):
        material = row.get(f"material_name_{i}")
        thickness = row.get(f"thickness_{i}_m")

        name = ""
        if material is not None and not (isinstance(material, float) and np.isnan(material)):
            name = str(material).strip()

        t = 0.0
        if thickness is not None and not (isinstance(thickness, float) and np.isnan(thickness)):
            try:
                t = float(thickness)
            except Exception:
                t = 0.0
        if t < 0.0:
            t = 0.0
        if not name:
            t = 0.0

        layers.append(MaterialLayer(name=name, thickness_m=t))
    return layers


def _get_component_layers(
    env: EnvelopeLookup,
    *,
    db_name: str,
    code: str,
) -> list[MaterialLayer]:
    df = getattr(env.envelope, db_name)
    if df is None:
        return _empty_layers()
    if code not in df.index:
        raise ValueError(f"Envelope code '{code}' not found in DB '{db_name}'.")
    row = df.loc[code]
    required = {"material_name_1", "thickness_1_m"}
    if not required.issubset(set(df.columns)):
        raise ValueError(
            f"Envelope DB '{db_name}' is missing required layer columns {sorted(required)}."
        )
    return _layers_from_envelope_row(row)


def _material_intensity_per_m2(materials: pd.DataFrame, layer: MaterialLayer) -> tuple[float, float, float]:
    if layer.name not in materials.index:
        raise ValueError(f"Material '{layer.name}' not found in MATERIALS.csv")
    rec = materials.loc[layer.name]
    unit = str(rec.get("unit", "")).strip().lower()
    if unit != "kg":
        raise ValueError(
            f"Material '{layer.name}' has unit '{rec.get('unit')}', expected 'kg' for layered constructions."
        )

    density = _parse_density(rec.get("density"))
    if density is None or density <= 0:
        raise ValueError(f"Material '{layer.name}' has invalid density: {rec.get('density')}")

    mass_per_m2 = density * float(layer.thickness_m)

    prod = _to_float(rec.get("GHG_emission_production"), default=0.0) * mass_per_m2
    demo = _to_float(rec.get("GHG_emission_recycling"), default=0.0) * mass_per_m2
    bio = _to_float(rec.get("biogenic_carbon_in_product"), default=0.0) * mass_per_m2
    return prod, demo, bio


def _diff_layers(old_layers: list[MaterialLayer] | None, new_layers: list[MaterialLayer] | None) -> list[tuple[str, MaterialLayer]]:
    """Return event list of ('remove'|'add', layer) comparing per-position (1..3) definitions.

    We intentionally diff *by layer slot* to match how envelope definitions are authored:
    changing thickness or material in a slot implies replacement of that slot.

    Invariant:
        If a slot changes, emit exactly a `remove` + `add` pair (even if either side is an empty slot).
    """
    old3 = _coerce_3_layers(old_layers)
    new3 = _coerce_3_layers(new_layers)

    events: list[tuple[str, MaterialLayer]] = []
    for idx in range(3):
        old_layer = old3[idx]
        new_layer = new3[idx]
        if old_layer.name != new_layer.name or abs(old_layer.thickness_m - new_layer.thickness_m) > 1e-9:
            events.append(("remove", old_layer))
            events.append(("add", new_layer))

    return events




def _load_state_building_properties(locator: InputLocator, buildings: list[str]) -> BuildingProperties:
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    return BuildingProperties(locator, weather_data, buildings)


def _feedstock_policies_from_config(config: Configuration) -> Mapping[str, tuple[int, int, float]] | None:
    emissions_cfg = config.emissions
    ref_yr = getattr(emissions_cfg, "grid_decarbonise_reference_year", None)
    tar_yr = getattr(emissions_cfg, "grid_decarbonise_target_year", None)
    tar_ef = getattr(emissions_cfg, "grid_decarbonise_target_emission_factor", None)

    if ref_yr is not None and tar_yr is not None and tar_ef is not None:
        return {"GRID": (int(ref_yr), int(tar_yr), float(tar_ef))}
    if ref_yr is None and tar_yr is None and tar_ef is None:
        return None
    raise ValueError(
        "If one of grid_decarbonise_reference_year, grid_decarbonise_target_year, "
        "or grid_decarbonise_target_emission_factor is set, all must be set."
    )


def create_district_material_timeline(
    config: Configuration,
    *,
    allow_missing_operational: bool = False,
) -> pd.DataFrame:
    """Create a district-level *event* emissions timeline driven by the YAML log.

    Key idea (mirrors the standard district emissions timeline):
    1) Generate a *building-level* event timeline for each building using:
       - the building's `const_type` (archetype / construction standard) from `zone.shp`
       - the per-year `modifications` in `district_timeline_log.yml` (assumed authoritative)
       - building birth / demolition events in `building_events`
    2) Aggregate to district level by summing all building timelines.

    Operational emissions are still sourced from state simulations (stepwise by state year),
    but embodied changes are attributed from the log (not by diffing state folders).

    Output:
    - Index is 'Y_YYYY'.
    - Columns include per-component/per-phase embodied columns (matching emissions timelines),
      plus `production_kgCO2e`, `demolition_kgCO2e`, `biogenic_kgCO2e`, and per-demand operational columns.

    Files:
    - District aggregate (exposed): `district_timeline_states/district_material_timeline.csv`
    - Per-building timelines (for inspection): `district_timeline_states/district_material_timelines_buildings/*.csv`

    Naming convention:
    - This function only outputs emission columns; all columns end with `_kgCO2e`.

    Component coverage:
    - The output columns follow `cea.analysis.lca.emission_timeline.TIMELINE_COMPONENTS` for consistency.
    - Layered envelope components (roofs, walls (ag/bg/part), floors (base/floor)) use MATERIALS.csv.
    - Windows use envelope assembly DB intensities (e.g., ENVELOPE_WINDOW.csv) via EnvelopeLookup.
    - `technical_systems` uses CEA constants per GFA.
    """

    main_locator = InputLocator(config.scenario)

    years = get_required_state_years(config)
    log_data = ensure_state_years_exist(config, years, update_yaml=True)
    reconcile_states_to_cumulative_modifications(config, years, log_data=log_data)

    # Determine overall year range
    start_year = min(years)
    year_end_val = getattr(config.emissions, "year_end", None)
    end_year = int(year_end_val) if year_end_val is not None else max(years)

    idx = [f"Y_{y}" for y in range(start_year, end_year + 1)]
    base_cols: list[str] = []
    for phase in ("production", "biogenic", "demolition"):
        for comp in TIMELINE_COMPONENTS:
            base_cols.append(f"{phase}_{comp}_kgCO2e")

    # Technical systems are additionally exposed as 4 independent quarters.
    tech_components = (
        "technical_system_hs",
        "technical_system_cs",
        "technical_system_dhw",
        "technical_system_el",
    )
    for phase in ("production", "biogenic", "demolition"):
        for comp in tech_components:
            base_cols.append(f"{phase}_{comp}_kgCO2e")
    base_cols.extend(["production_kgCO2e", "demolition_kgCO2e", "biogenic_kgCO2e"])
    base_cols.extend([f"operation_{d}_kgCO2e" for d in _tech_name_mapping.keys()])

    def _empty_timeline() -> pd.DataFrame:
        df = pd.DataFrame(index=idx)
        df.index.name = "period"
        for c in base_cols:
            df[c] = 0.0
        return df

    out = _empty_timeline()

    years_sorted = sorted(years)
    feedstock_policies = _feedstock_policies_from_config(config)

    # Preflight: we require state outputs for this workflow.
    # - Radiation results are needed to compute surface areas via BuildingProperties.
    # - Operational-by-building results are needed for district operational step function.
    missing_radiation: dict[int, str] = {}
    missing_operational_years: list[int] = []

    for year in years_sorted:
        state_locator = InputLocator(main_locator.get_state_in_time_scenario_folder(year))
        buildings = list(state_locator.get_zone_building_names())
        if buildings:
            for b in buildings:
                rad_path = state_locator.get_radiation_building(b)
                if not os.path.exists(rad_path):
                    missing_radiation.setdefault(year, rad_path)
                    break
        op_path = state_locator.get_total_yearly_operational_building()
        if not os.path.exists(op_path):
            missing_operational_years.append(year)

    if missing_radiation:
        sample_lines = "\n".join(
            f"- {y}: missing {p}" for y, p in sorted(missing_radiation.items())
        )
        raise FileNotFoundError(
            "Some state years are missing solar-radiation outputs required for surface areas.\n"
            "Run the `state-simulations` script (includes Radiation) for all state years, then rerun this timeline.\n"
            "Missing examples:\n" + sample_lines
        )

    if missing_operational_years and not allow_missing_operational:
        years_str = ", ".join(map(str, sorted(set(missing_operational_years))))
        raise FileNotFoundError(
            "Missing operational-by-building results for some state years: "
            f"{years_str}.\n"
            "Run the `state-simulations` script (includes Emissions) to generate outputs for all state years, "
            "or call create_district_material_timeline(..., allow_missing_operational=True) for best-effort carry-forward."
        )

    # --- Inputs needed for per-building aggregation ---------------------------------
    building_construction_years = get_building_construction_years(main_locator)
    building_const_types = _load_building_const_types(main_locator)
    demolition_years = _building_demolition_years(log_data)

    # Cache areas per building (computed from BuildingProperties once the building exists in some state year).
    areas_by_building: dict[str, dict[str, float]] = {}

    # Cache per-state operational emissions by building (used for step function per building).
    operational_by_state_year: dict[int, pd.DataFrame] = {}

    for year in years_sorted:
        state_locator = InputLocator(main_locator.get_state_in_time_scenario_folder(year))
        buildings_in_state = list(state_locator.get_zone_building_names())
        if not buildings_in_state:
            continue

        # Operational-by-building results
        op_path = state_locator.get_total_yearly_operational_building()
        if os.path.exists(op_path):
            operational_by_state_year[year] = pd.read_csv(op_path, index_col="name")

        # Areas
        missing_area_buildings = [b for b in buildings_in_state if b not in areas_by_building]
        if missing_area_buildings:
            bp = _load_state_building_properties(state_locator, missing_area_buildings)
            for b in missing_area_buildings:
                areas_by_building[b] = get_component_quantities(bp, b)

    # --- Archetype layer evolution from YAML log ------------------------------------
    # Baseline archetype codes come from the (main) construction types database.
    archetype_df = pd.read_csv(main_locator.get_database_archetypes_construction_type(), index_col="const_type")
    env_lookup = EnvelopeLookup.from_locator(main_locator)
    materials = _read_material_db(main_locator)

    # Track current layers per archetype and component.
    # Notes:
    # - Only roofs, walls (ag/bg/part), and floors (base/floor) use layered material definitions.
    # - `base` layers are resolved from the envelope `floor` database table (ground-contact constructions).
    archetypes_needed = sorted({v for v in building_const_types.values()})
    archetype_layers: dict[str, dict[str, list[MaterialLayer]]] = {}
    archetype_service_life: dict[str, dict[str, int | None]] = {}
    archetype_construction_types: dict[str, dict[str, str]] = {}
    for archetype in archetypes_needed:
        if archetype not in archetype_df.index:
            raise ValueError(f"Archetype '{archetype}' not found in construction types database.")
        row = archetype_df.loc[archetype]
        layered_codes = {c: str(row.get(f"type_{c}")) for c in _LAYERED_COMPONENT_TO_DB}
        code_win = str(row.get("type_win"))
        archetype_construction_types[archetype] = {
            _CONSTRUCTION_TYPE_WIN_FIELD: code_win,
            **{k: str(row.get(k)) for k in _SUPPLY_TYPE_FIELDS},
        }
        archetype_layers[archetype] = {
            comp: _get_component_layers(
                env_lookup,
                db_name=_LAYERED_COMPONENT_TO_DB[comp],
                code=layered_codes[comp],
            )
            for comp in _LAYERED_COMPONENT_TO_DB
        }
        archetype_service_life[archetype] = {
            **{
                comp: cast(int | None, env_lookup.get_item_value(layered_codes[comp], "Service_Life"))
                for comp in _LAYERED_COMPONENT_TO_DB
            },
            "win": cast(int | None, env_lookup.get_item_value(code_win, "Service_Life")),
            "technical_systems": int(SERVICE_LIFE_OF_TECHNICAL_SYSTEMS),
        }

    # Ensure a baseline snapshot exists before the first state year if buildings are constructed earlier.
    in_range_construction_years = [
        int(y)
        for y in building_construction_years.values()
        if y is not None and start_year <= int(y) <= end_year
    ]
    baseline_year = min([start_year, *in_range_construction_years]) if in_range_construction_years else start_year

    archetype_timeline = _prepare_archetype_timeline(
        years_sorted=years_sorted,
        base_year=int(baseline_year),
        log_data=log_data,
        archetype_layers=archetype_layers,
        archetype_construction_types=archetype_construction_types,
    )

    # --- Build per-building timelines, then sum -------------------------------------
    building_timelines: dict[str, MaterialChangeEmissionTimeline] = {}
    all_buildings = sorted(set(building_const_types.keys()) | set(building_construction_years.keys()))

    for b in all_buildings:
        building_timeline = MaterialChangeEmissionTimeline(name=b, locator=main_locator)
        building_timeline.timeline = _empty_timeline()
        building_timelines[b] = building_timeline

        c_year = building_construction_years.get(b)
        if c_year is None:
            continue
        if c_year < start_year or c_year > end_year:
            continue
        construction_year = int(c_year)
        d_year = demolition_years.get(b)

        building_timeline.set_existence(construction_year=construction_year, demolition_year=d_year)

        # Operational emissions: only for years the building exists
        building_timeline.fill_operational_step_function(
            state_years_sorted=years_sorted,
            end_year=end_year,
            operational_by_state_year=operational_by_state_year,
            allow_missing_operational=allow_missing_operational,
            feedstock_policies=feedstock_policies,
        )

        const_type = building_const_types.get(b)
        if const_type is None:
            continue

        area_dict = areas_by_building.get(b)
        if area_dict is None:
            continue

        building_timeline.build_embodied_from_log(
            const_type=const_type,
            area_dict=area_dict,
            materials=materials,
            years_sorted=years_sorted,
            start_year=start_year,
            end_year=end_year,
            archetype_timeline=archetype_timeline,
            service_life_by_src_component=archetype_service_life[const_type],
        )

    # Persist per-building timelines under the district timeline folder.
    # This keeps the district-level output as the primary result while still exposing detailed per-building files.
    per_building_folder = os.path.join(
        main_locator.get_district_timeline_states_folder(),
        "district_material_timelines_buildings",
    )
    os.makedirs(per_building_folder, exist_ok=True)
    for b, building_timeline in building_timelines.items():
        # Only write timelines for buildings that actually exist in the timeline horizon.
        if building_timeline.construction_year is None:
            continue
        file_name = f"{b}_material_timeline.csv"
        save_b_path = os.path.join(per_building_folder, file_name)
        try:
            df_save = building_timeline.timeline.copy()
            df_save["Note"] = building_timeline.notes_series()
            df_save.to_csv(save_b_path, float_format="%.2f")
        except PermissionError as e:
            raise PermissionError(
                "Permission denied writing a per-building material timeline CSV. "
                "This often happens on Windows when the CSV is open in Excel or locked by OneDrive sync. "
                f"Close '{save_b_path}' and rerun."
            ) from e

    # Aggregate by summing all building timelines.
    for building_timeline in building_timelines.values():
        out = out.add(building_timeline.timeline, fill_value=0.0)

    # Convenience totals
    for label in out.index:
        out.at[label, "production_kgCO2e"] = float(out.filter(like="production_").loc[label].sum())
        out.at[label, "demolition_kgCO2e"] = float(out.filter(like="demolition_").loc[label].sum())
        out.at[label, "biogenic_kgCO2e"] = float(out.filter(like="biogenic_").loc[label].sum())

        # Maintain backwards-compatible `*_technical_systems_*` columns as sum of the 4 quarters.
        tech_cols = [
            "production_technical_system_hs_kgCO2e",
            "production_technical_system_cs_kgCO2e",
            "production_technical_system_dhw_kgCO2e",
            "production_technical_system_el_kgCO2e",
        ]
        out.at[label, "production_technical_systems_kgCO2e"] = float(
            out.loc[label, tech_cols].to_numpy(dtype=float).sum()
        )

    # Persist under district timeline folder to avoid mixing with lifetime-based timelines.
    save_path = os.path.join(main_locator.get_district_timeline_states_folder(), "district_material_timeline.csv")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        out.to_csv(save_path, float_format="%.2f")
    except PermissionError as e:
        raise PermissionError(
            "Permission denied writing the district material timeline output. "
            "This often happens on Windows when the CSV is open in Excel or locked by OneDrive sync. "
            f"Close '{save_path}' and rerun."
        ) from e

    return out


def main(config: Configuration) -> None:
    df = create_district_material_timeline(config)
    print(f"District material timeline saved with {len(df)} years.")


if __name__ == "__main__":
    main(Configuration())
