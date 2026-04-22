"""
Booster plumbing and validation for DH networks.

Boosters lift the trunk temperature to the service setpoint for individual
buildings in a low-temperature DH network — e.g. a heat-pump booster taking
35 °C supply to 60 °C for DHW. Two user-facing parameters live in the
``[thermal-network]`` section:

- ``hs-booster-type-building``   — assembly used for space-heating booster
- ``dhw-booster-type-building``  — assembly used for domestic-hot-water booster

At run-time of Thermal Network Part 2a (single-phase) or Part 2b (multi-phase),
those two *global* values get fanned out to every DH-connected building that
has the corresponding demand and written into ``connectivity.yml`` as a
``networks.DH.boosters.<building>.<service>`` tree. Advanced users can then
hand-edit ``connectivity.yml`` for per-building overrides — subsequent Part 2
runs only overwrite per-building entries when the global value is non-blank;
a blank global leaves existing per-building entries untouched.

Final-Energy reads boosters per-building from ``connectivity.yml`` rather
than re-reading the global config — so the workflow is:

  1. User runs Part 2 with the booster dropdowns set.
  2. Part 2 persists per-building booster entries to ``connectivity.yml``
     (and uses them in its flow/sizing — the physics is handled in
     Part 2's main flow engine; this module only handles plumbing).
  3. User runs Final-Energy; the per-building entries are consumed from
     ``connectivity.yml``.

This module provides:

- :func:`write_boosters_to_connectivity` — call once per network from Part 2.
- :func:`read_boosters_for_building` — called by Final-Energy per building.
- :func:`validate_booster_configuration` — heavy write-time check: every
  building with non-zero booster demand must have a booster assembly set.
- :func:`validate_booster_temperature_compatibility` — heavy write-time
  check: the booster's design supply temperature must cover the required
  setpoint at every building.
- :func:`validate_booster_assembly_exists` — light read-time check used by
  Final-Energy: the assembly code from ``connectivity.yml`` must still
  resolve in the assembly database.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

import pandas as pd


__author__ = "Zhongming Shi, Martin Mosteiro"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Keys under ``networks.DH.boosters.<building>``. Match the two service
# names already used elsewhere in ``connectivity.yml``
# (``per_building_services``), so readers can iterate without mapping.
_SERVICE_KEYS = ('space_heating', 'domestic_hot_water')


# ── plumbing: fan out + read back ─────────────────────────────────────────────

def write_boosters_to_connectivity(locator, network_name, config) -> None:
    """Fan out the two global booster assemblies from ``config`` to every
    DH-connected building in ``connectivity.yml`` and write the file back.

    Behaviour per service:

    - Global value set (non-blank):  write this assembly for every
      DH-connected building that carries the matching service. Any
      existing per-building entry for the service is **replaced**.
    - Global value blank:             leave existing per-building entries
      for that service alone. This is the "I've hand-edited the yml and
      don't want Part 2 to touch it" workflow.

    No-op when ``connectivity.yml`` has no DH network. Safe to call from
    both Part 2a and Part 2b.
    """
    hs_global = (getattr(config.thermal_network, 'hs_booster_type_building', '') or '').strip()
    dhw_global = (getattr(config.thermal_network, 'dhw_booster_type_building', '') or '').strip()
    if not (hs_global or dhw_global):
        # Neither set → nothing to fan out. Don't rewrite the yml.
        return

    data = locator.read_network_connectivity(network_name)
    if data is None:
        return
    dh = (data.get('networks') or {}).get('DH')
    if not dh:
        return

    per_building_services = dh.get('per_building_services') or {}
    if not per_building_services:
        return

    boosters = dict(dh.get('boosters') or {})
    for building, services in per_building_services.items():
        existing = dict(boosters.get(building) or {})
        if hs_global and 'space_heating' in services:
            existing['space_heating'] = hs_global
        if dhw_global and 'domestic_hot_water' in services:
            existing['domestic_hot_water'] = dhw_global
        # Fill in missing service slots with None so downstream readers
        # can treat ``None`` uniformly instead of missing-key lookups.
        for key in _SERVICE_KEYS:
            existing.setdefault(key, None)
        boosters[building] = existing

    dh['boosters'] = boosters
    locator.write_network_connectivity(network_name, data)


def read_boosters_for_building(locator, network_name: str, building: str) -> Dict[str, Optional[str]]:
    """Return the booster assemblies for one building.

    :return: ``{'space_heating_booster': <assembly or None>,
                'hot_water_booster':     <assembly or None>}``
        Keys use the ``*_booster`` suffix (matching the service-config
        keys in Final-Energy's ``supply_config`` dict). Missing /
        hand-deleted entries surface as ``None``.
    """
    empty = {'space_heating_booster': None, 'hot_water_booster': None}
    if not network_name:
        return empty
    data = locator.read_network_connectivity(network_name)
    if data is None:
        return empty
    boosters = (
        ((data.get('networks') or {}).get('DH') or {}).get('boosters') or {}
    ).get(building) or {}
    return {
        'space_heating_booster': _norm(boosters.get('space_heating')),
        'hot_water_booster':     _norm(boosters.get('domestic_hot_water')),
    }


def _norm(value) -> Optional[str]:
    """Treat empty-string / 'None' / None uniformly as ``None``."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.upper() in ('NONE', 'NULL'):
        return None
    return s


# ── validators ────────────────────────────────────────────────────────────────

def validate_booster_assembly_exists(assembly_code: str, locator) -> None:
    """Light existence check: the assembly resolves in the scenario DB.

    Called by Final-Energy at read-time, after ``connectivity.yml`` has
    already been written and validated by Part 2. Catches the rare case
    where a user deleted the referenced assembly from their database
    between running Part 2 and running Final-Energy, or hand-edited the
    yml to point at a non-existent assembly.

    :raises ValueError: if the assembly is not resolvable.
    """
    from cea.analysis.final_energy.supply_validation import load_assembly_components
    load_assembly_components(assembly_code, locator)  # raises on missing


def validate_booster_configuration(dh_network, network_name, locator, config) -> None:
    """Booster-coverage check: every building with non-zero booster demand
    has a booster assembly set.

    Reads the substation CSVs Part 2 writes for each DH-connected
    building and checks whether ``Qhs_booster_W`` / ``Qww_booster_W`` is
    non-zero. For each such building, verifies that a booster assembly
    is available — either:

    1. via a per-building entry in ``dh_network['boosters'][<bldg>]``
       (the authoritative per-building source written by Part 2 and
       potentially hand-edited); or
    2. via the global config dropdown
       (``config.thermal_network.*_booster_type_building``), which acts
       as a fallback when the per-building tree is absent (e.g. Part 2
       was run before this feature shipped and the yml hasn't been
       rewritten yet).

    Raises with an actionable message listing every building that is
    missing a booster. Usable from both Part 2 (write-time) and
    Final-Energy (read-time).
    """
    hs_global = getattr(config.thermal_network, 'hs_booster_type_building', None)
    dhw_global = getattr(config.thermal_network, 'dhw_booster_type_building', None)

    per_building_boosters = dh_network.get('boosters') or {}

    hs_needs_booster = []
    dhw_needs_booster = []

    per_building_services = dh_network.get('per_building_services', {})

    for building, services in per_building_services.items():
        substation_file = locator.get_thermal_network_substation_results_file(
            building, 'DH', network_name
        )
        if not os.path.exists(substation_file):
            continue
        try:
            substation_df = pd.read_csv(substation_file)
        except Exception:
            continue

        per_bldg = per_building_boosters.get(building) or {}
        hs_set = _norm(per_bldg.get('space_heating')) or (hs_global or None)
        dhw_set = _norm(per_bldg.get('domestic_hot_water')) or (dhw_global or None)

        if 'space_heating' in services and 'Qhs_booster_W' in substation_df.columns:
            if substation_df['Qhs_booster_W'].sum() > 0 and not hs_set:
                hs_needs_booster.append(building)

        if 'domestic_hot_water' in services and 'Qww_booster_W' in substation_df.columns:
            if substation_df['Qww_booster_W'].sum() > 0 and not dhw_set:
                dhw_needs_booster.append(building)

    messages = []
    if hs_needs_booster:
        listing = "\n".join(f"  - {b}" for b in sorted(hs_needs_booster))
        messages.append(
            "The following buildings have space heating booster demand from the "
            "low-temperature district heating network, but no booster assembly is configured:\n"
            f"{listing}\n\n"
            "Please select a booster assembly in 'hs-booster-type-building' "
            "(Thermal Network settings)."
        )
    if dhw_needs_booster:
        listing = "\n".join(f"  - {b}" for b in sorted(dhw_needs_booster))
        messages.append(
            "The following buildings have domestic hot water booster demand from the "
            "low-temperature district heating network, but no booster assembly is configured:\n"
            f"{listing}\n\n"
            "Please select a booster assembly in 'dhw-booster-type-building' "
            "(Thermal Network settings)."
        )
    if messages:
        raise ValueError("\n\n".join(messages))


def validate_booster_temperature_compatibility(dh_network, network_name, locator, config) -> None:
    """Booster-temperature-coverage check per building.

    For each DH-connected building, resolves the effective booster
    assembly (per-building entry in ``dh_network['boosters']`` if
    present, else falling back to the global config dropdown), looks up
    its primary component's design supply temperature, and compares to
    ``T_target_hs_C`` / ``T_target_dhw_C`` in the substation CSVs. Fails
    with a consolidated message when any booster cannot meet the
    required setpoint, grouped by (assembly-component pair,
    temperature).

    :raises ValueError: consolidated error message.
    """
    from cea.analysis.final_energy.supply_validation import (
        load_assembly_components,
        get_component_design_supply_temperature,
    )

    hs_global = _norm(getattr(config.thermal_network, 'hs_booster_type_building', None))
    dhw_global = _norm(getattr(config.thermal_network, 'dhw_booster_type_building', None))
    per_building_boosters = dh_network.get('boosters') or {}
    per_building_services = dh_network.get('per_building_services', {})

    # Cache (primary_code, design_temp) per assembly so we don't re-read
    # the same file for every building that shares the same booster.
    assembly_info: Dict[str, tuple] = {}

    def _resolve(assembly_code: Optional[str]):
        if not assembly_code:
            return (None, None)
        if assembly_code in assembly_info:
            return assembly_info[assembly_code]
        components = load_assembly_components(assembly_code, locator)
        primary = components.get('primary_components')
        design_temp = (
            get_component_design_supply_temperature(primary, locator)
            if primary else None
        )
        info = (primary, design_temp)
        assembly_info[assembly_code] = info
        return info

    # Grouped by (assembly, primary_code, design_temp, t_required_C) → [buildings]
    hs_groups: Dict[tuple, list] = {}
    dhw_groups: Dict[tuple, list] = {}

    for building in per_building_services:
        substation_file = locator.get_thermal_network_substation_results_file(
            building, 'DH', network_name
        )
        if not os.path.exists(substation_file):
            continue
        try:
            sub_df = pd.read_csv(substation_file)
        except Exception:
            continue

        per_bldg = per_building_boosters.get(building) or {}
        hs_code = _norm(per_bldg.get('space_heating')) or hs_global
        dhw_code = _norm(per_bldg.get('domestic_hot_water')) or dhw_global
        hs_primary, hs_temp = _resolve(hs_code)
        dhw_primary, dhw_temp = _resolve(dhw_code)

        # Missing-column back-compat check only fires when SOME building
        # has a booster configured that requires the column.
        needs_check = (hs_temp is not None) or (dhw_temp is not None)
        if needs_check:
            missing_cols = []
            if hs_temp is not None and 'T_target_hs_C' not in sub_df.columns:
                if sub_df.get('Qhs_booster_W') is not None and sub_df['Qhs_booster_W'].sum() > 0:
                    missing_cols.append('T_target_hs_C')
            if dhw_temp is not None and 'T_target_dhw_C' not in sub_df.columns:
                if sub_df.get('Qww_booster_W') is not None and sub_df['Qww_booster_W'].sum() > 0:
                    missing_cols.append('T_target_dhw_C')
            if missing_cols:
                raise ValueError(
                    f"Substation file for building '{building}' is missing columns: "
                    f"{', '.join(missing_cols)}.\n\n"
                    "This is likely because the thermal network was simulated with an older "
                    "version of CEA.\n\n"
                    "Please re-run Thermal Network Part 2 to regenerate the substation files.\n"
                    "If the error persists, re-run Thermal Network Part 1 as well."
                )

        if hs_temp is not None and 'T_target_hs_C' in sub_df.columns:
            t_required = round(sub_df['T_target_hs_C'].max())
            if t_required > 0 and hs_temp < t_required - 0.5:
                key = (hs_code, hs_primary, hs_temp, t_required)
                hs_groups.setdefault(key, []).append(building)

        if dhw_temp is not None and 'T_target_dhw_C' in sub_df.columns:
            t_required = round(sub_df['T_target_dhw_C'].max())
            if t_required > 0 and dhw_temp < t_required - 0.5:
                key = (dhw_code, dhw_primary, dhw_temp, t_required)
                dhw_groups.setdefault(key, []).append(building)

    def _format(groups, service_label):
        if not groups:
            return None
        lines = []
        for (code, primary, supply_t, t_req), buildings in sorted(
            groups.items(), key=lambda kv: (kv[0][0] or '', kv[0][3])
        ):
            names = ", ".join(sorted(buildings))
            lines.append(
                f"  - Assembly {code} (component {primary or '?'}) supplies "
                f"{supply_t:.0f} °C but {len(buildings)} building(s) need "
                f"{t_req:.0f} °C: {names}"
            )
        return (
            f"{service_label} booster temperature mismatch:\n"
            + "\n".join(lines)
            + "\n\nPlease select a booster assembly whose primary component "
              "can supply a higher temperature for these buildings."
        )

    messages = [m for m in (_format(hs_groups, "Space heating"),
                            _format(dhw_groups, "Domestic hot water")) if m]
    if messages:
        raise ValueError("\n\n".join(messages))
