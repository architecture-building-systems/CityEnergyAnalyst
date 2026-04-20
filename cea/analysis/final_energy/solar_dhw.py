"""
Solar hot-water dispatch for the final-energy pipeline.

**Scope**: supports ONLY SC (solar collector — flat-plate SC1/FP or evacuated-
tube SC2/ET) as the DHW primary, with a BO or HP as the secondary (booster).
PVT is explicitly NOT supported as a DHW primary; its ~35 °C operating
temperature is below the DHW setpoint and would require a stratified tank
model to credit meaningfully. PVT thermal output continues to be credited
against space heating via the legacy ``PVT_Q_offset_kgCO2e`` mechanism in
``cea/analysis/lca/emission_time_dependent.py``.

Public API
----------

- :func:`load_solar_component_info` — resolves an SC code against the
  SOLAR_COLLECTORS database. Raises for PVT codes and unknown codes.

- :func:`validate_solar_dhw_assembly` — enforces that an SC primary has a
  BO/HP secondary (solar alone cannot cover 24/7 DHW) and rejects PVT
  primaries with a clear error.

- :func:`validate_solar_dhw_building` — ensures the building has SC_*
  configured under ``solar-technology`` before dispatch runs.

- :func:`aggregate_building_sc_thermal` — sums hourly ``Q_SC_gen_kWh`` and
  SC aperture across every SC_* (FP/ET) technology configured for the
  building. Ignores PVT.

- :func:`compute_dhw_cold_inlet_hourly` — computes the hourly cold-mains
  inlet series from the scenario weather file using the same CEA helper
  (:func:`cea.demand.hotwater_loads.calc_water_temperature`) as the demand
  pipeline. Climate-aware: low in winter, higher in summer; warmer
  year-round in tropical scenarios.

- :func:`dispatch_solar_dhw` — runs the hourly dispatch with a
  temperature-tracking fully-mixed tank.

Tank model
----------

Single-node fully-mixed tank. **State variable: `tank_temp_C`.** One hour loop:

1. **Solar charges the tank**: `tank_temp += Q_SC_gen × 3600 / (mass × cp)`.
   Cap at :data:`T_MAX_C`. Overflow is dumped (real-system pressure relief).
2. **Demand is served** from the tank, with a thermostatic mixing valve when
   the tank is above setpoint (draws less mass, dilutes with cold bypass).
   The booster (secondary BO/HP) tops up the deficit between tank temp and
   the DHW setpoint for the drawn mass.
3. **Standing loss**: tank cools toward ambient via Newton-style decay:
   ``tank_temp = T_AMBIENT + (tank_temp - T_AMBIENT) × (1 - TANK_LOSS_FRAC_HOUR)``.

Temperatures from CEA's shared constants / helpers (not duplicated here):

- DHW setpoint :data:`cea.demand.constants.TWW_SETPOINT` — 60 °C, sanitary.
- Hourly cold-mains inlet from :func:`cea.demand.hotwater_loads.calc_water_temperature`
  at 1 m depth, driven by the scenario weather file.

Tank / dispatch constants in this module:

- :data:`T_AMBIENT_C` = 20 °C   — room where the tank sits (#TODO: configurable)
- :data:`T_MAX_C` = 105 °C     — pressure-relief cap; heat above is dumped
- :data:`TANK_CAPACITY_L_PER_M2` = 50 L/m² of SC aperture
- :data:`TANK_LOSS_FRAC_HOUR` = 0.02 standing-loss fraction toward ambient
- :data:`PARASITIC_FRAC` = 0.02 pump kWh per kWh delivered solar

Known simplifications (#TODOs in the code):

- Initial tank temp = cold-inlet at hour 0 (brief warm-up transient in January).
- Heat above :data:`T_MAX_C` is dumped — no credit to SH or any other service.
- Pump parasitic ∝ delivered solar (should be gross ``Q_SC_gen`` in reality).
- :data:`T_AMBIENT_C` hardcoded.
- CEA's ``Q_SC_gen_kWh`` is computed at a fixed collector inlet (setpoint).
  When the tank is above setpoint, real Q would be lower. We inherit CEA's
  simplification — modest over-credit on hot-tank summer hours.
"""
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea.demand.constants import TWW_SETPOINT
from cea.demand.hotwater_loads import calc_water_temperature


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Water density (kg/L) and specific heat (kJ/kg·K).
_WATER_DENSITY_KG_PER_L = 1.0
_WATER_CP_KJ_PER_KG_K = 4.186

# Dispatch parameters. These describe the SC → DHW dispatch model (tank
# sizing, standing loss, pump parasitic), not the solar panel itself.
# Editing this module is the intended override path.
TANK_CAPACITY_L_PER_M2 = 50.0  # L of tank water per m² of SC aperture
TANK_LOSS_FRAC_HOUR = 0.02      # standing loss: fraction of (T_tank - T_AMBIENT)/hour
PARASITIC_FRAC = 0.02           # pump kWh per kWh of delivered solar heat
T_AMBIENT_C = 20.0              # TODO: make configurable (tank-room temperature)
T_MAX_C = 105.0                 # tank pressure-relief cap; heat above is dumped


def load_solar_component_info(
    component_code: str,
    locator: cea.inputlocator.InputLocator,
) -> Dict[str, Any]:
    """Verify an SC component code and return its config dict.

    Only SC (flat-plate SC1/FP or evacuated-tube SC2/ET) is supported as a
    DHW primary. PVT is explicitly rejected — see module docstring.

    :param component_code: Code like ``SC1`` or ``SC2``.
    :param locator: Active :class:`InputLocator`.
    :return: Dict with ``type``, ``carrier``, ``efficiency``.
    :raises ValueError: If the code is a PVT code, starts with something
        other than ``SC``, or doesn't resolve to a row in
        ``SOLAR_COLLECTORS.csv``.
    """
    if component_code.startswith('PVT'):
        raise ValueError(
            f"PVT component {component_code!r} cannot be used as a DHW "
            "primary. PVT's low operating temperature (~35 °C) is below "
            "the DHW setpoint and would require a stratified tank model. "
            "Use an SC (flat-plate SC1 or evacuated-tube SC2) primary "
            "instead."
        )
    if not component_code.startswith('SC'):
        raise ValueError(
            f"load_solar_component_info called with non-SC code "
            f"{component_code!r}"
        )

    component_file = locator.get_db4_components_conversion_conversion_technology_csv(
        'SOLAR_COLLECTORS'
    )
    df = pd.read_csv(component_file)
    if (df['code'] == component_code).sum() == 0:
        raise ValueError(
            f"Component {component_code} not found in SOLAR_COLLECTORS database"
        )

    return {
        'type': 'SC',
        'carrier': 'SOLAR',
        'efficiency': 1.0,
    }


def aggregate_building_sc_thermal(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration,
) -> Tuple[np.ndarray, float]:
    """Return ``(hourly_thermal_kwh, sc_aperture_m2)`` for one building.

    Reads per-building SC potential result files and sums hourly
    ``Q_SC_gen_kWh`` and ``area_SC_m2`` across every SC_* technology
    (typically SC_FP and/or SC_ET) currently assigned under
    ``solar-technology``. PVT is deliberately ignored — its output
    contributes to space-heating offsets via the existing legacy path,
    not to DHW.

    Imports inside the function avoid pulling the heavy solar-potential
    modules into this module at import time.
    """
    from cea.analysis.final_energy.calculation import (
        parse_solar_panel_configuration,
        read_solar_generation_file,
    )

    panel_config = parse_solar_panel_configuration(config)
    sc_codes = {
        code for code in panel_config.values()
        if code and code.startswith('SC_')
    }

    thermal_sum: Optional[np.ndarray] = None
    total_area_m2 = 0.0

    for tech_code in sc_codes:
        try:
            df = read_solar_generation_file(building_name, tech_code, locator)
        except ValueError:
            # Missing solar-potential file is caught by the upstream
            # validator; skip silently here.
            continue

        # SC output shape: Q_SC_gen_kWh hourly, area_SC_m2 constant column.
        if 'Q_SC_gen_kWh' in df.columns:
            values = df['Q_SC_gen_kWh'].to_numpy(dtype=float)
            thermal_sum = values if thermal_sum is None else thermal_sum + values
        if 'area_SC_m2' in df.columns:
            total_area_m2 += float(df['area_SC_m2'].iloc[0])

    if thermal_sum is None:
        raise ValueError(
            f"No SC potential result files could be read for building "
            f"{building_name}.\n"
            "Run `cea solar-collector` with the appropriate SC technology "
            "configured first."
        )

    return thermal_sum, total_area_m2


def compute_dhw_cold_inlet_hourly(
    locator: cea.inputlocator.InputLocator,
) -> np.ndarray:
    """Hourly DHW cold-mains inlet temperature for the scenario.

    Uses the same helper as CEA's demand pipeline so that SC-DHW dispatch
    sees the same cold-inlet assumption that the demand model used when
    computing ``Qww_sys_kWh``. Returns an 8760-length numpy array of °C,
    climate-aware: lower in winter, higher in summer, warmer year-round in
    tropical climates.
    """
    from cea.utilities.epwreader import epw_reader

    weather_df = epw_reader(locator.get_weather_file())
    return calc_water_temperature(weather_df['drybulb_C'].to_numpy(dtype=float), depth_m=1)


def validate_solar_dhw_assembly(
    building_name: str,
    hot_water_cfg: Optional[Dict[str, Any]],
) -> None:
    """Raise if an SC-primary hot-water assembly is misconfigured.

    - PVT primary → hard error (SC-only policy).
    - SC primary with no BO/HP secondary → hard error (solar alone can't
      cover 24/7 DHW).
    """
    if not hot_water_cfg:
        return
    primary_type = hot_water_cfg.get('type')
    assembly_code = hot_water_cfg.get('assembly_code', '<unknown>')
    primary_component = hot_water_cfg.get('primary_component', '<unknown>')

    if primary_type == 'PVT':
        raise ValueError(
            "PVT is not supported as a DHW primary — its ~35 °C operating "
            "temperature is below the DHW setpoint and would require a "
            f"stratified tank model for building {building_name}.\n"
            f"Hot-water assembly {assembly_code!r} uses "
            f"{primary_component} as primary. Use an SC (SC1/FP or SC2/ET) "
            "primary instead. PVT thermal is still credited against space "
            "heating via the legacy offset mechanism when PVT is "
            "configured under solar-technology."
        )
    if primary_type != 'SC':
        return

    secondary_info = hot_water_cfg.get('secondary_info')
    secondary_component = hot_water_cfg.get('secondary_component')

    if not secondary_component or secondary_info is None:
        raise ValueError(
            "SC-primary hot-water assembly has no secondary component "
            f"for building {building_name}.\n"
            f"Assembly {assembly_code!r} uses {primary_component} (SC) as "
            "primary but defines no backup. SC alone cannot cover full "
            "DHW demand. Add a BO (boiler) or HP (heat pump) as the "
            "secondary component of this assembly."
        )

    if not (
        secondary_component.startswith('BO')
        or secondary_component.startswith('HP')
    ):
        raise ValueError(
            "SC-primary hot-water assembly has an invalid secondary "
            f"component for building {building_name}.\n"
            f"Assembly {assembly_code!r} uses {primary_component} (SC) as "
            "primary. The secondary component must be a BO (boiler) or "
            f"HP (heat pump), but got {secondary_component!r}."
        )


def validate_solar_dhw_building(
    building_name: str,
    hot_water_cfg: Optional[Dict[str, Any]],
    config: cea.config.Configuration,
    locator: Optional[cea.inputlocator.InputLocator] = None,
) -> None:
    """Raise early if an SC-primary hot-water assembly can't run.

    Called at the top of :func:`calculate_building_final_energy` before
    any time-series are generated. Checks:

    1. ``hot_water`` supply has ``type == 'SC'`` — if not, returns.
    2. The building appears in ``solar-technology:buildings``.
    3. At least one ``SC_*`` technology is configured on the building.

    If the locator is provided and no SC technology is configured, the
    error message names the specific ``panels-on-*`` parameter to set
    and lists the SC variants (SC_FP / SC_ET) that already have
    pre-computed potential results on disk for this building.
    """
    if not hot_water_cfg:
        return
    if hot_water_cfg.get('type') != 'SC':
        return

    solar_buildings = getattr(config.solar_technology, 'buildings', None) or []
    if building_name not in solar_buildings:
        raise ValueError(
            "SC-primary hot-water assembly requires solar to be enabled "
            f"on the building, but it is missing from "
            f"`solar-technology:buildings` for building {building_name}.\n"
            "Enable solar on the building or change the hot-water supply "
            "assembly."
        )

    configured_codes = _get_building_solar_codes(building_name, config)
    if not any(code.startswith('SC_') for code in configured_codes):
        available_on_disk = (
            _find_available_sc_codes(building_name, locator)
            if locator is not None else []
        )

        lines = [
            "SC-primary hot-water assembly requires an SC_* panel type "
            "under `solar-technology`, but none is configured "
            f"for building {building_name}.",
            "",
            "Set one of the panels-on-* parameters to an SC code:",
            "  solar-technology:panels-on-roof       = SC_FP   (flat plate — typical DHW choice)",
            "  solar-technology:panels-on-roof       = SC_ET   (evacuated tube — higher temp)",
            "  solar-technology:panels-on-wall-south = SC_FP   (or any wall facet)",
        ]
        if configured_codes:
            lines.append(
                f"\nCurrently configured solar technologies: {sorted(configured_codes)!r}"
            )
        if available_on_disk:
            lines.append(
                "\nSC potential results already computed for this building: "
                f"{sorted(available_on_disk)!r}. You just need to tell "
                "`final-energy` which variant the SC-primary DHW assembly should use."
            )
        else:
            lines.append(
                "\nNo SC potential results were found on disk for this building. "
                "Run `cea solar-collector` with the chosen SC panel type before "
                "running `cea final-energy`."
            )
        lines.append(
            "\nAlternatively, change the hot-water supply assembly to one that "
            "doesn't use SC as primary."
        )

        raise ValueError("\n".join(lines))


def _find_available_sc_codes(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
) -> Iterable[str]:
    """Return the SC_* tech codes for which a per-building potential result
    file already exists on disk. Used to give the user specific guidance
    when their config is missing a panels-on-* setting."""
    import os as _os
    found = []
    for panel_type, code in (('FP', 'SC_FP'), ('ET', 'SC_ET')):
        if _os.path.exists(locator.SC_results(building_name, panel_type)):
            found.append(code)
    return found


def _get_building_solar_codes(
    building_name: str,
    config: cea.config.Configuration,
) -> Iterable[str]:
    """Return the solar tech codes installed on any facade for this scenario.

    ``config.solar_technology`` is per-scenario, not per-building: every
    building in ``solar-technology:buildings`` shares the same
    facade→tech_code mapping. The returned list is used only to check
    whether at least one ``SC_*`` code is present.
    """
    from cea.analysis.final_energy.calculation import (
        parse_solar_panel_configuration,
    )
    panel_config = parse_solar_panel_configuration(config)
    return [code for code in panel_config.values() if code]


def _tank_mass_kg(aperture_m2: float) -> float:
    """Water mass in a DHW tank sized from SC aperture."""
    if aperture_m2 <= 0:
        return 0.0
    return aperture_m2 * TANK_CAPACITY_L_PER_M2 * _WATER_DENSITY_KG_PER_L


def dispatch_solar_dhw(
    dhw_demand_kwh: np.ndarray,
    solar_thermal_kwh: np.ndarray,
    sc_aperture_m2: float,
    T_cold_hourly_C: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Temperature-tracking hourly dispatch for SC primary + BO/HP backup.

    The tank is modelled as a single-node fully-mixed water mass. State
    variable is ``tank_temp_C``. See module docstring for the full
    dispatch loop description.

    :param dhw_demand_kwh: ``Qww_sys_kWh`` hourly series (kWh/h above cold
        inlet, i.e. CEA's standard DHW demand definition).
    :param solar_thermal_kwh: Aggregated ``Q_SC_gen_kWh`` hourly series
        across all SC technologies for this building.
    :param sc_aperture_m2: Total SC aperture area (m²); sizes the tank via
        :data:`TANK_CAPACITY_L_PER_M2`.
    :param T_cold_hourly_C: Hourly cold-mains inlet temperature (°C), same
        length as the demand / solar series. Typically from
        :func:`compute_dhw_cold_inlet_hourly`.
    :return: Dict with numpy arrays ``served_by_solar_kwh``,
        ``served_by_backup_kwh``, ``parasitic_electricity_kwh`` and
        scalar diagnostics ``tank_mass_kg``, ``tank_final_temp_C``,
        ``surplus_dumped_kwh``.
    """
    n = len(dhw_demand_kwh)
    if len(solar_thermal_kwh) != n:
        raise ValueError(
            f"dispatch_solar_dhw: length mismatch "
            f"(demand={n}, solar={len(solar_thermal_kwh)})"
        )
    if len(T_cold_hourly_C) != n:
        raise ValueError(
            f"dispatch_solar_dhw: cold-inlet length {len(T_cold_hourly_C)} "
            f"doesn't match demand length {n}"
        )

    tank_mass = _tank_mass_kg(sc_aperture_m2)
    # kJ of energy change per kelvin of tank temperature, divided later
    # by 3600 to convert kJ ↔ kWh on the fly.
    tank_capacity_kj_per_k = tank_mass * _WATER_CP_KJ_PER_KG_K

    served_by_solar = np.zeros(n)
    served_by_backup = np.zeros(n)
    parasitic_electricity = np.zeros(n)
    surplus_dumped = 0.0

    # Initial state. TODO: initialise at a steady-state estimate so the
    # January warm-up transient doesn't bias short runs. For annual or
    # multi-year runs the first few days are absorbed.
    tank_temp = float(T_cold_hourly_C[0]) if tank_capacity_kj_per_k > 0 else 0.0

    for t in range(n):
        demand = max(0.0, float(dhw_demand_kwh[t]))
        gen = max(0.0, float(solar_thermal_kwh[t]))
        T_cold = float(T_cold_hourly_C[t])

        # Step 1: solar heat raises tank temperature (cap at T_MAX).
        if tank_capacity_kj_per_k > 0 and gen > 0.0:
            delta_T = gen * 3600.0 / tank_capacity_kj_per_k
            tank_temp += delta_T
            if tank_temp > T_MAX_C:
                # Surplus dumped — pressure-relief / anti-stagnation.
                # TODO: consider crediting against SH instead of dumping.
                surplus_kwh = (tank_temp - T_MAX_C) * tank_capacity_kj_per_k / 3600.0
                surplus_dumped += surplus_kwh
                tank_temp = T_MAX_C

        # Step 2: serve demand from tank with thermostatic mixing valve.
        tank_contribution_kwh = 0.0
        m_tank_drawn = 0.0
        if demand > 0.0 and tank_mass > 0 and tank_temp > T_cold:
            dhw_setpoint = float(TWW_SETPOINT)
            available_delta = max(0.0, dhw_setpoint - T_cold)
            if tank_temp >= dhw_setpoint:
                # Mixing valve: hot from tank, cold bypass to hit setpoint.
                # Draw less mass from the tank than the full reference mass.
                m_tank_drawn = demand * 3600.0 / (
                    _WATER_CP_KJ_PER_KG_K * (tank_temp - T_cold)
                )
                tank_contribution_kwh = demand
            else:
                # Tank below setpoint: draw the full reference mass, tank
                # provides preheat from T_cold to tank_temp, booster tops
                # up from tank_temp to setpoint.
                m_tank_drawn = (
                    demand * 3600.0
                    / (_WATER_CP_KJ_PER_KG_K * available_delta)
                    if available_delta > 0 else 0.0
                )
                tank_contribution_kwh = (
                    m_tank_drawn * _WATER_CP_KJ_PER_KG_K * (tank_temp - T_cold)
                    / 3600.0
                )

            # Draw can't exceed tank mass in a single hour — pin it.
            if m_tank_drawn > tank_mass:
                m_tank_drawn = tank_mass
                tank_contribution_kwh = min(
                    tank_contribution_kwh,
                    m_tank_drawn * _WATER_CP_KJ_PER_KG_K
                    * (tank_temp - T_cold) / 3600.0,
                )

            # Update tank: drawn mass at tank_temp replaced by cold inlet.
            f = m_tank_drawn / tank_mass if tank_mass > 0 else 0.0
            tank_temp = (1.0 - f) * tank_temp + f * T_cold

        booster_kwh = demand - tank_contribution_kwh

        # Step 3: Newton-style standing loss toward ambient, one-way.
        # Real insulated DHW tanks lose heat to a warmer room; we ignore
        # the reverse (colder tank absorbing heat from a warmer room)
        # because real tanks are well-insulated and the effect is small,
        # and because crediting "free" room heat as DHW service would
        # be a modeling artifact that effectively draws from the
        # building's space-heating balance without being tracked.
        if tank_temp > T_AMBIENT_C:
            tank_temp = T_AMBIENT_C + (tank_temp - T_AMBIENT_C) * (
                1.0 - TANK_LOSS_FRAC_HOUR
            )

        # Step 4: record this hour.
        served_by_solar[t] = tank_contribution_kwh
        served_by_backup[t] = booster_kwh
        # TODO: base parasitic on gross Q_SC_gen (pump runs whenever the
        # collector is hot), not on the share delivered to demand.
        parasitic_electricity[t] = tank_contribution_kwh * PARASITIC_FRAC

    return {
        'served_by_solar_kwh': served_by_solar,
        'served_by_backup_kwh': served_by_backup,
        'parasitic_electricity_kwh': parasitic_electricity,
        'tank_mass_kg': tank_mass,
        'tank_final_temp_C': tank_temp,
        'surplus_dumped_kwh': surplus_dumped,
    }


# Legacy-offset columns the SC-DHW dispatch replaces. Only SC_ columns are
# dropped — PVT_*_Q_kWh columns are preserved so PVT thermal continues to
# be credited against space heating via the legacy ``PVT_Q_offset_kgCO2e``
# mechanism in the emissions pipeline.
SOLAR_DHW_SUPPRESSED_COLUMNS: Tuple[str, ...] = (
    'SC_Q_offset_kWh',
    'SC_Q_offset_kgCO2e',
)


def drop_suppressed_offset_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove legacy SC thermal-offset columns that the dispatch replaces.

    PVT thermal offsets, PV electrical offsets and PVT electrical offsets
    are NOT touched — they live on independent offset paths unaffected by
    SC-DHW dispatch.
    """
    to_drop = [c for c in SOLAR_DHW_SUPPRESSED_COLUMNS if c in df.columns]
    if to_drop:
        return df.drop(columns=to_drop)
    return df
