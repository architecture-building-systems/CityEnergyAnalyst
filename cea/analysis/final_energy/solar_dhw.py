"""
Solar hot-water dispatch for the final-energy pipeline.

Implements the SC / PVT-primary branch of the DHW supply chain:

- :func:`load_solar_component_info` verifies the SC or PVT code exists
  in the component database and returns the fixed config dict the rest
  of the pipeline consumes (tank + parasitic parameters are module
  constants, not database columns — see below).

- :func:`validate_solar_dhw_building` verifies that a building with an
  SC/PVT-primary hot-water assembly has the required panels configured
  under ``solar-technology:buildings``. It raises early with a clear
  error before any solar time-series are computed.

- :func:`dispatch_solar_dhw` runs the hourly dispatch with a single
  hot-water tank: solar output serves the tank / demand first, then the
  secondary BO / HP covers the remainder. Returns the columns the
  caller should insert into the per-building final-energy DataFrame and
  the set of legacy offset columns that must be dropped to avoid
  double-counting.

Tank + dispatch parameters are kept as module constants here rather
than as columns on SOLAR_COLLECTORS.csv / PHOTOVOLTAIC_THERMAL_PANELS.csv:

    TANK_CAPACITY_L_PER_M2 = 50 L per m² of installed SC / PVT aperture
    TANK_LOSS_FRAC_HOUR    = 0.02 (standing loss per hour)
    PARASITIC_FRAC         = 0.02 of useful thermal output (pump electricity)

Other assumptions:
    tank_initial_state = cold (0 kWh) at hour 0
    surplus            = dumped (no inter-service credit)

To override these, edit this module. They are deliberately NOT a
database concern — they describe the dispatch model, not the panel.
"""
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Density (kg/L) and specific heat (kJ/kg·K) for water.
_WATER_DENSITY_KG_PER_L = 1.0
_WATER_CP_KJ_PER_KG_K = 4.186
# The tank temperature window the model assumes: cold inlet 15 °C,
# hot delivery 60 °C (45 K span). Capacity in kWh is derived below.
_TANK_DELTA_T_K = 45.0

# Dispatch parameters. These are module constants rather than database
# columns — they describe the SC/PVT → DHW dispatch model (tank sizing,
# standing loss, pump parasitic), not the solar panel itself. Editing
# this module is the intended override path.
PARASITIC_FRAC = 0.02
TANK_CAPACITY_L_PER_M2 = 50.0
TANK_LOSS_FRAC_HOUR = 0.02


def load_solar_component_info(
    component_code: str,
    locator: cea.inputlocator.InputLocator,
) -> Dict[str, Any]:
    """Verify an SC or PVT component code and return its config dict.

    Matches the return shape of ``load_component_info`` for other
    component families — just ``type``, ``carrier``, ``efficiency``.
    Dispatch parameters (tank capacity, standing loss, pump parasitic)
    are module constants in this file, not per-component database
    columns.

    :param component_code: Code like ``SC1`` or ``PVT1``.
    :param locator: Active :class:`InputLocator`.
    :return: Dict with ``type``, ``carrier``, ``efficiency``.
    :raises ValueError: If the code doesn't resolve to a row in the
        SOLAR_COLLECTORS or PHOTOVOLTAIC_THERMAL_PANELS sheet.
    """
    if component_code.startswith('PVT'):
        csv_name = 'PHOTOVOLTAIC_THERMAL_PANELS'
        component_type = 'PVT'
    elif component_code.startswith('SC'):
        csv_name = 'SOLAR_COLLECTORS'
        component_type = 'SC'
    else:
        raise ValueError(
            f"load_solar_component_info called with non-SC/PVT code "
            f"{component_code!r}"
        )

    component_file = locator.get_db4_components_conversion_conversion_technology_csv(csv_name)
    df = pd.read_csv(component_file)
    if (df['code'] == component_code).sum() == 0:
        raise ValueError(
            f"Component {component_code} not found in {csv_name} database"
        )

    return {
        'type': component_type,
        'carrier': 'SOLAR',
        'efficiency': 1.0,
    }


def aggregate_building_solar_thermal(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration,
) -> Tuple[np.ndarray, float]:
    """Return ``(hourly_thermal_kwh, total_aperture_m2)`` for one building.

    Reads the per-building SC/PVT potential result files and sums the
    thermal output and aperture area across every SC type (FP/ET) and
    PVT type (any ``*_Q_kWh`` column) that's currently assigned under
    ``solar-technology``. Returns an 8760-length numpy array for the
    thermal time series plus the total installed aperture in m².

    Imports inside the function avoid pulling the heavy solar-potential
    modules into this file at import time.
    """
    from cea.analysis.final_energy.calculation import (
        parse_solar_panel_configuration,
        read_solar_generation_file,
    )

    panel_config = parse_solar_panel_configuration(config)
    # Unique SC / PVT tech codes used by any facade.
    sc_pvt_codes = {
        code
        for code in panel_config.values()
        if code and (code.startswith('SC_') or code.startswith('PVT_'))
    }

    thermal_sum: Optional[np.ndarray] = None
    total_area_m2 = 0.0

    for tech_code in sc_pvt_codes:
        try:
            df = read_solar_generation_file(building_name, tech_code, locator)
        except ValueError:
            # Missing solar-potential file is handled by the
            # upstream validator; ignore here.
            continue

        # SC files expose `Q_SC_gen_kWh` (per-hour, all surfaces summed)
        # and `area_SC_m2` (a constant value repeated on every row).
        # PVT files expose `Q_PVT_gen_kWh` and `Area_PVT_m2` /
        # `area_PVT_m2` depending on database version.
        thermal_col = None
        area_col = None
        if tech_code.startswith('SC_'):
            thermal_col = 'Q_SC_gen_kWh'
            area_col = 'area_SC_m2'
        elif tech_code.startswith('PVT_'):
            thermal_col = 'Q_PVT_gen_kWh'
            for candidate in ('Area_PVT_m2', 'area_PVT_m2'):
                if candidate in df.columns:
                    area_col = candidate
                    break

        if thermal_col and thermal_col in df.columns:
            values = df[thermal_col].to_numpy(dtype=float)
            thermal_sum = (
                values if thermal_sum is None else thermal_sum + values
            )
        if area_col and area_col in df.columns:
            total_area_m2 += float(df[area_col].iloc[0])

    if thermal_sum is None:
        # No SC/PVT panel files found for this building — caller
        # already validated configuration, so this indicates missing
        # potential files and should surface as a clear error.
        raise ValueError(
            f"Building {building_name}: no SC or PVT potential result "
            f"files could be read. Run `cea solar-collector` and/or "
            f"`cea photovoltaic-thermal` first."
        )

    return thermal_sum, total_area_m2


def validate_solar_dhw_assembly(
    building_name: str,
    hot_water_cfg: Optional[Dict[str, Any]],
) -> None:
    """Raise if a hot-water assembly declares SC/PVT primary but has no backup.

    Solar thermal alone cannot cover 24/7 DHW demand, so the dispatch
    requires a non-empty secondary component that resolves to a BO or
    HP (boiler or heat pump). If that constraint is violated, fail fast
    with a message pointing at the offending assembly.
    """
    if not hot_water_cfg:
        return
    primary_type = hot_water_cfg.get('type')
    if primary_type not in ('SC', 'PVT'):
        return

    assembly_code = hot_water_cfg.get('assembly_code', '<unknown>')
    primary_component = hot_water_cfg.get('primary_component', '<unknown>')
    secondary_info = hot_water_cfg.get('secondary_info')
    secondary_component = hot_water_cfg.get('secondary_component')

    if not secondary_component or secondary_info is None:
        raise ValueError(
            f"Building {building_name}: hot-water assembly "
            f"{assembly_code!r} uses {primary_component} ({primary_type}) "
            f"as primary but defines no secondary component. SC/PVT "
            f"cannot cover full DHW demand without a dispatchable "
            f"backup. Add a BO or HP as the secondary component of "
            f"this assembly."
        )

    if not (
        secondary_component.startswith('BO')
        or secondary_component.startswith('HP')
    ):
        raise ValueError(
            f"Building {building_name}: hot-water assembly "
            f"{assembly_code!r} uses {primary_component} ({primary_type}) "
            f"as primary; the secondary component must be a BO or HP, "
            f"but got {secondary_component!r}."
        )


def validate_solar_dhw_building(
    building_name: str,
    hot_water_cfg: Optional[Dict[str, Any]],
    config: cea.config.Configuration,
) -> None:
    """Raise early if an SC/PVT-primary hot-water assembly can't run.

    Called at the top of :func:`calculate_building_final_energy` before
    any time-series are generated. Checks:

    1. ``hot_water`` supply has ``type ∈ {SC, PVT}`` — if not, returns.
    2. The building appears in ``solar-technology:buildings``.
    3. At least one SC or PVT technology is enabled on the building
       (config lists panel codes; the rule is "starts with SC_ or PVT_").
    """
    if not hot_water_cfg:
        return
    primary_type = hot_water_cfg.get('type')
    if primary_type not in ('SC', 'PVT'):
        return

    solar_buildings = getattr(config.solar_technology, 'buildings', None) or []
    if building_name not in solar_buildings:
        raise ValueError(
            f"Building {building_name}: hot-water supply uses "
            f"{primary_type} as primary, but the building is not in "
            f"`solar-technology:buildings`. Enable solar on the "
            f"building or change the hot-water supply assembly."
        )

    configured_codes = _get_building_solar_codes(building_name, config)
    if not any(
        code.startswith(('SC_', 'PVT_')) for code in configured_codes
    ):
        raise ValueError(
            f"Building {building_name}: hot-water supply wants SC/PVT "
            f"thermal, but only {sorted(configured_codes)!r} is "
            f"configured under `solar-technology`. Add an SC_* or "
            f"PVT_* technology or change the supply assembly."
        )


def _get_building_solar_codes(
    building_name: str,
    config: cea.config.Configuration,
) -> Iterable[str]:
    """Return the solar tech codes actually installed on any facade.

    `config.solar_technology` is a per-scenario (not per-building)
    configuration: every building in ``solar-technology:buildings``
    shares the same facade→tech_code mapping. We parse that mapping via
    the existing helper in ``calculation.py`` and return the non-None
    tech codes. The caller only uses the return value to check whether
    *any* SC_ or PVT_ code is present, so a flat list is enough.
    """
    from cea.analysis.final_energy.calculation import (
        parse_solar_panel_configuration,
    )
    panel_config = parse_solar_panel_configuration(config)
    return [code for code in panel_config.values() if code]


def _tank_capacity_kwh(area_m2: float, capacity_L_per_m2: float) -> float:
    """Convert tank volume (sized from solar aperture) to kWh of useful
    thermal storage, using the hard-coded 45 K Δ-T.
    """
    if area_m2 <= 0 or capacity_L_per_m2 <= 0:
        return 0.0
    volume_L = area_m2 * capacity_L_per_m2
    mass_kg = volume_L * _WATER_DENSITY_KG_PER_L
    energy_kj = mass_kg * _WATER_CP_KJ_PER_KG_K * _TANK_DELTA_T_K
    return energy_kj / 3600.0  # kJ → kWh


def dispatch_solar_dhw(
    dhw_demand_kwh: np.ndarray,
    solar_thermal_kwh: np.ndarray,
    total_sc_pvt_area_m2: float,
) -> Dict[str, np.ndarray]:
    """Run the hourly dispatch for SC/PVT primary + secondary backup.

    Tank capacity, standing loss, and pump parasitic come from the
    module constants ``TANK_CAPACITY_L_PER_M2``, ``TANK_LOSS_FRAC_HOUR``,
    ``PARASITIC_FRAC``.

    :param dhw_demand_kwh: ``Qww_sys_kWh`` hourly series.
    :param solar_thermal_kwh: Aggregated SC + PVT-thermal hourly series
        (summed across all configured facades for the building).
    :param total_sc_pvt_area_m2: Total aperture area (m²), used to size
        the tank via ``TANK_CAPACITY_L_PER_M2``.
    :return: Dict with numpy arrays
        ``served_by_solar``, ``served_by_backup``, ``parasitic_electricity``
        and scalar diagnostics ``surplus_dumped`` / ``tank_final_level``.
        Caller inserts the arrays into the per-building final-energy
        DataFrame and attributes them to the right carriers.
    """
    n = len(dhw_demand_kwh)
    if len(solar_thermal_kwh) != n:
        raise ValueError(
            f"dispatch_solar_dhw: length mismatch "
            f"(demand={n}, solar={len(solar_thermal_kwh)})"
        )

    tank_capacity_kwh = _tank_capacity_kwh(
        total_sc_pvt_area_m2,
        TANK_CAPACITY_L_PER_M2,
    )
    tank_loss_frac = TANK_LOSS_FRAC_HOUR
    parasitic_frac = PARASITIC_FRAC

    served_by_solar = np.zeros(n)
    served_by_backup = np.zeros(n)
    parasitic_electricity = np.zeros(n)
    tank_level = 0.0  # cold start
    surplus_dumped = 0.0

    for t in range(n):
        demand = max(0.0, float(dhw_demand_kwh[t]))
        gen = max(0.0, float(solar_thermal_kwh[t]))

        # 1. Draw from tank first.
        from_tank = min(tank_level, demand)
        tank_level -= from_tank
        after_tank = demand - from_tank

        # 2. Direct solar to demand.
        from_solar = min(gen, after_tank)
        remainder = after_tank - from_solar

        # 3. Surplus solar into tank (clip to capacity).
        surplus = gen - from_solar
        tank_level += surplus
        if tank_level > tank_capacity_kwh:
            surplus_dumped += tank_level - tank_capacity_kwh
            tank_level = tank_capacity_kwh

        # 4. Standing loss.
        tank_level *= (1.0 - tank_loss_frac)

        # 5. Accounting.
        served_by_solar[t] = from_tank + from_solar
        served_by_backup[t] = remainder
        parasitic_electricity[t] = served_by_solar[t] * parasitic_frac

    return {
        'served_by_solar_kwh': served_by_solar,
        'served_by_backup_kwh': served_by_backup,
        'parasitic_electricity_kwh': parasitic_electricity,
        'tank_capacity_kwh': tank_capacity_kwh,
        'tank_final_kwh': tank_level,
        'surplus_dumped_kwh': surplus_dumped,
    }


# Legacy-offset columns that the SC/PVT dispatch replaces. When the
# dispatch runs for a building, the caller drops these columns from the
# building's hourly final-energy DataFrame to prevent double-counting
# (the solar thermal output is now booked directly against DHW rather
# than credited against space heating).
SOLAR_DHW_SUPPRESSED_COLUMNS: Tuple[str, ...] = (
    'SC_Q_offset_kWh',
    'PVT_Q_offset_kWh',
    'SC_Q_offset_kgCO2e',
    'PVT_Q_offset_kgCO2e',
)


def drop_suppressed_offset_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove legacy thermal-offset columns that the dispatch replaces.

    Electrical offsets (``PV_E_offset``, ``PVT_E_offset``) are NOT
    touched — they live on an independent electricity-offset path.
    """
    to_drop = [c for c in SOLAR_DHW_SUPPRESSED_COLUMNS if c in df.columns]
    if to_drop:
        return df.drop(columns=to_drop)
    return df
