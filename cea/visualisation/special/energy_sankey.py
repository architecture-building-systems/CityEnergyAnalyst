"""
Energy Flow Sankey diagram.

    [Carrier]  →  [Plant Component]  →  [Network]  →  [Building Component]  →  [Service]

For district systems (DC/DH), the primary carrier is what the plant consumes (e.g. GRID for
a chiller). For building-scale systems, the carrier is what the building equipment consumes
(e.g. NATURALGAS for a gas boiler).

Layer visibility is controlled by x-to-plot:
  'component' → show plant-side equipment and building-side equipment nodes
  'scale'     → show DC/DH network node (district) or Building node (building-scale)

Data sources:
  - B####.csv          hourly building final energy files
  - {net}_{type}_{plant}.csv  hourly plant final energy files (if available)
  - configuration.json component/scale/carrier mapping
"""

import os
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import (
    COLOURS_TO_RGB,
    component_display,
    component_tech_colour,
)

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── Layer 0: energy carriers ──────────────────────────────────────────────────

# Carrier colours come from the canonical ``CARRIER_COLOURS`` palette so
# a given carrier renders the same way in the sankey, bar plots, and map
# layers. Only the darker shade is used here; the sankey doesn't gradient.
from cea.visualisation.format.plot_colours import (
    CARRIER_COLOURS as _CANONICAL_CARRIER_COLOURS,
    DEFAULT_CARRIER_COLOURS as _CANONICAL_DEFAULT,
)

_CARRIER_COLOURS = {
    code: COLOURS_TO_RGB[darker]
    for code, (_, darker) in _CANONICAL_CARRIER_COLOURS.items()
}

def _carrier_colour(code):
    return _CARRIER_COLOURS.get(code, COLOURS_TO_RGB[_CANONICAL_DEFAULT[1]])


# ── Layer 1: scale ────────────────────────────────────────────────────────────

_SCALE_COLOURS = {
    'Building':         COLOURS_TO_RGB['blue_light'],
    'DC Network':       COLOURS_TO_RGB['teal_light'],
    'DH Network':       COLOURS_TO_RGB['red_light'],
}

# ── Layer 2: components ───────────────────────────────────────────────────────


# ── Layer 3: services ─────────────────────────────────────────────────────────

# Layer 0 carriers render in alphabetical order; that way user-added
# carriers slot in without a code change.

_SERVICE_ORDER = [
    'Space Heating',
    'Domestic Hot Water',
    'Space Cooling',
    'Electricity',
    'Distribution',
    '(−) Offset Heat',
    '(−) Offset Electricity',
]

_SERVICE_COLOURS = {
    'Space Heating':        COLOURS_TO_RGB['red_light'],
    'Domestic Hot Water':   COLOURS_TO_RGB['orange_light'],
    'Space Cooling':        COLOURS_TO_RGB['blue_light'],
    'Electricity':          COLOURS_TO_RGB['green_light'],
    'Distribution':         COLOURS_TO_RGB['grey_light'],
    '(−) Offset Heat':      COLOURS_TO_RGB['yellow'],
    '(−) Offset Electricity': COLOURS_TO_RGB['yellow'],
}

# Maps config parameter choice → service display name
_SERVICE_DISPLAY = {
    'space_heating':      'Space Heating',
    'domestic_hot_water': 'Domestic Hot Water',
    'space_cooling':      'Space Cooling',
    'electricity':        'Electricity',
    'distribution':       'Distribution',
    'offset_heat':        '(−) Offset Heat',
    'offset_electricity': '(−) Offset Electricity',
}

# Maps configuration.json key → (service display name, B####.csv column prefix)
_CONFIG_KEY_MAP = {
    'space_heating': ('Space Heating',      'Qhs_sys'),
    'hot_water':     ('Domestic Hot Water', 'Qww_sys'),
    'space_cooling': ('Space Cooling',      'Qcs_sys'),
    'electricity':   ('Electricity',        'E_sys'),
}

# Maps booster config key → B####.csv column prefix for booster energy
_BOOSTER_COL_PREFIX = {
    'space_heating_booster': 'Qhs_booster',
    'hot_water_booster':     'Qww_booster',
}

_UNIT_DIVISORS = {'kWh': 1, 'MWh': 1_000, 'GWh': 1_000_000}

# Placeholder node labels for empty layers
_NO_DISTRICT = 'No District System'
_NO_BUILDING = 'No Building Conversion'
_PLACEHOLDER_COLOUR = COLOURS_TO_RGB.get('grey_lighter', 'rgb(210,210,210)')

# Fixed x positions for up to 5 layers (Plotly 0–1 range, exclusive of exact 0/1)
# Layout auto-collapses to 4 columns when no booster components exist.
_LAYER_X = {0: 0.01, 1: 0.25, 2: 0.50, 3: 0.75, 4: 0.99}


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_rgba(rgb_str, alpha=0.5):
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# Per-building solar-config surface key → column-name suffix in solar
# potential files (PV / SC / PVT). Same mapping used by `solar_dhw.py`.
_SOLAR_SURFACE_TO_FACADE_SUFFIX = {
    'roof':       'roofs_top',
    'wall_north': 'walls_north',
    'wall_south': 'walls_south',
    'wall_east':  'walls_east',
    'wall_west':  'walls_west',
}


def _solar_per_surface_radiation_kwh(building_name, tech_code, surface, locator):
    """Annual radiation (kWh) that landed on **just one configured surface**
    for a single PV / SC / PVT tech.

    The persisted ``*_radiation_kWh`` column in ``B####.csv`` is the
    per-panel-type aggregate across **every** surface simulated under that
    panel type — not just the surface(s) actually configured. Reading the
    aggregate as if it were the per-surface value inflates the source-side
    width of the Sankey arc (e.g. ``PV_PV4`` with 2964 MWh "in" vs 46 MWh
    generated, an absurd 1.5% efficiency).

    This helper opens the corresponding solar potential file directly and
    allocates the aggregate radiation in proportion to the surface's share
    of useful generation (E for PV, Q for SC, E+Q for PVT). For a panel
    type with uniform module efficiency η, per-surface_radiation =
    per-surface_useful / η = aggregate_radiation × per-surface_useful /
    aggregate_useful — a closed-form, no-η-lookup needed.

    Returns 0.0 when the surface key is unknown, the file is missing, or
    the file lacks the required columns.
    """
    suffix = _SOLAR_SURFACE_TO_FACADE_SUFFIX.get(surface)
    if suffix is None:
        return 0.0
    parts = tech_code.split('_')
    tech_type = parts[0]
    try:
        if tech_type == 'PV':
            panel_type = parts[1]
            path = locator.PV_results(building_name, panel_type)
            per_surface_col = f'PV_{suffix}_E_kWh'
            agg_useful_col = 'E_PV_gen_kWh'
        elif tech_type == 'SC':
            panel_type = '_'.join(parts[1:])  # 'FP' or 'ET'
            path = locator.SC_results(building_name, panel_type)
            per_surface_col = f'SC_{panel_type}_{suffix}_Q_kWh'
            agg_useful_col = 'Q_SC_gen_kWh'
        elif tech_type == 'PVT':
            # tech_code: PVT_<PV_panel_type>_<SC_panel_type>, e.g. PVT_PV1_ET
            pv_panel_type = parts[1]
            sc_panel_type = parts[2]
            path = locator.PVT_results(building_name, pv_panel_type, sc_panel_type)
        else:
            return 0.0
    except Exception:
        return 0.0

    if not os.path.exists(path):
        return 0.0
    try:
        df = pd.read_csv(path)
    except Exception:
        return 0.0
    if 'radiation_kWh' not in df.columns:
        return 0.0
    agg_radiation = float(df['radiation_kWh'].sum())
    if agg_radiation <= 0:
        return 0.0

    if tech_type == 'PVT':
        # PVT useful = E + Q across the same surface; allocate accordingly.
        per_e_col = f'PVT_{sc_panel_type}_{suffix}_E_kWh'
        per_q_col = f'PVT_{sc_panel_type}_{suffix}_Q_kWh'
        if per_e_col not in df.columns or per_q_col not in df.columns:
            return 0.0
        per_useful = float(df[per_e_col].sum()) + float(df[per_q_col].sum())
        agg_useful = (
            (float(df['E_PVT_gen_kWh'].sum()) if 'E_PVT_gen_kWh' in df.columns else 0.0)
            + (float(df['Q_PVT_gen_kWh'].sum()) if 'Q_PVT_gen_kWh' in df.columns else 0.0)
        )
    else:
        if per_surface_col not in df.columns or agg_useful_col not in df.columns:
            return 0.0
        per_useful = float(df[per_surface_col].sum())
        agg_useful = float(df[agg_useful_col].sum())

    if agg_useful <= 0:
        return 0.0
    return agg_radiation * per_useful / agg_useful


def _sc_gross_kwh_for_building(building_name, bconfig, locator):
    """Annual gross SC thermal output for one building, summed only over
    the ``(surface, panel_type)`` pairs actually configured under
    ``solar`` in the per-building config — *not* the per-panel-type
    aggregate ``Q_SC_gen_kWh`` columns, which would inflate the total by
    counting all roof+wall surfaces under both SC_FP and SC_ET when each
    surface is typically assigned to only one panel type.

    Delegates to :func:`aggregate_sc_thermal_per_surface` so the Sankey
    source-side width matches what the SC-DHW dispatch actually fed into
    the tank model. Returns 0.0 when no SC surface is configured or the
    SC potential files are missing — caller falls back to ``val`` and the
    SC node renders as a pass-through.
    """
    from cea.analysis.final_energy.solar_dhw import aggregate_sc_thermal_per_surface
    panel_config = (bconfig.get('solar') or {}) if isinstance(bconfig, dict) else {}
    if not panel_config:
        return 0.0
    thermal_sum, _ = aggregate_sc_thermal_per_surface(
        building_name, panel_config, locator
    )
    return float(thermal_sum.sum()) if thermal_sum is not None else 0.0


# ── plant data loader ─────────────────────────────────────────────────────────

def _load_plant_totals(locator, whatif_name, plant_configs, building_configs):
    """
    Load annual plant energy input totals from plant CSV files.

    Returns dict keyed by network_type ('DH' or 'DC'):
      {
        '_carrier_raw': 'GRID',
        'carrier': 'Grid Electricity',
        'component': 'Chiller (CH1)',
        'input_kWh': 5_000_000.0,
      }
    Returns an empty dict if no plant files exist.
    """
    # Collect network_name per network_type from building configs
    network_names = {}
    for bconfig in building_configs.values():
        for cfg_key in ('space_heating', 'hot_water', 'space_cooling'):
            cfg = bconfig.get(cfg_key)
            if not cfg or cfg.get('scale') != 'DISTRICT':
                continue
            nt = 'DH' if cfg_key in ('space_heating', 'hot_water') else 'DC'
            if nt not in network_names and cfg.get('network_name'):
                network_names[nt] = cfg['network_name']

    totals = {}

    for plant_name, plant_cfg in plant_configs.items():
        network_type = plant_cfg.get('network_type', '')
        carrier_raw = plant_cfg.get('carrier', 'GRID')
        component_code = plant_cfg.get('primary_component', '')
        tertiary_code = plant_cfg.get('tertiary_component')
        network_name = network_names.get(network_type, '')
        if not network_type or not network_name:
            continue

        # Plant files are named {plant_name}.csv
        plant_file = locator.get_final_energy_plant_file(
            network_name, network_type, plant_name, whatif_name
        )
        if not os.path.exists(plant_file):
            continue
        plant_files = [plant_file]

        primary_col = f'plant_primary_{network_type}_{carrier_raw}_kWh'

        total_input = 0.0
        total_tertiary = 0.0
        total_pumping = 0.0
        total_thermal = 0.0
        for fpath in plant_files:
            plant_df = pd.read_csv(fpath)
            if primary_col in plant_df.columns:
                total_input += plant_df[primary_col].sum()
            # Sum all tertiary columns for this network type
            for tc in [c for c in plant_df.columns if c.startswith(f'plant_tertiary_{network_type}_')]:
                total_tertiary += plant_df[tc].sum()
            for pc in [c for c in plant_df.columns if c.startswith('plant_pumping_') and c.endswith('_GRID_kWh')]:
                total_pumping += plant_df[pc].sum()
            if 'thermal_load_kWh' in plant_df.columns:
                total_thermal += plant_df['thermal_load_kWh'].sum()

        if total_input > 0 or total_tertiary > 0 or total_pumping > 0 or total_thermal > 0:
            if network_type in totals:
                totals[network_type]['input_kWh'] += total_input
                totals[network_type]['tertiary_kWh'] += total_tertiary
                totals[network_type]['pumping_kWh'] += total_pumping
                totals[network_type]['thermal_load_kWh'] += total_thermal
            else:
                totals[network_type] = {
                    '_carrier_raw': carrier_raw,
                    'carrier': carrier_raw,
                    'primary_component': component_display(component_code, locator) if component_code else '',
                    'tertiary_component': component_display(tertiary_code, locator) if tertiary_code else '',
                    'input_kWh': total_input,
                    'tertiary_kWh': total_tertiary,
                    'pumping_kWh': total_pumping,
                    'thermal_load_kWh': total_thermal,
                }

    return totals


# ── data loader ───────────────────────────────────────────────────────────────

def load_energy_flow_data(locator, whatif_name):
    """
    Aggregate energy flow across all buildings and plants into a flat DataFrame.

    Columns
    -------
    primary_carrier    display name of the primary energy carrier entering the system
    _carrier_raw       raw carrier code (for colour lookup)
    plant_component    plant-side equipment display name (DISTRICT only, else '')
    network            network type 'DC' or 'DH' (DISTRICT only, else '')
    building_component building-side equipment display name (HEX for district, equipment for building)
    scale              'District' or 'Building'
    service            end-use service display name
    value_kWh          building-side annual energy consumption
    plant_input_kWh    annual primary energy input to the plant (DISTRICT only; equals value_kWh
                       for building-scale rows)
    _has_plant_data    True if plant CSV files were found
    """
    config_data = locator.read_analysis_configuration(whatif_name)
    if config_data is None:
        expected = locator.get_analysis_configuration_file(whatif_name)
        raise FileNotFoundError(f"Configuration file not found: {expected}")

    building_configs = config_data.get('buildings', {})
    plant_configs = config_data.get('plants', {})

    plant_totals = _load_plant_totals(locator, whatif_name, plant_configs, building_configs)

    records = []

    # ── District pumping rows (one per network type) ───────────────────────
    for network_type, pt in plant_totals.items():
        pumping = pt.get('pumping_kWh', 0.0)
        if pumping > 0:
            records.append({
                'primary_carrier':    'Grid Electricity',
                '_carrier_raw':       'GRID',
                'plant_component':    f'Pump ({network_type})',
                'network':            network_type,
                'building_component': '',
                'scale':              'District',
                'service':            'Distribution',
                'value_kWh':          pumping,
                'plant_input_kWh':    pumping,
                '_has_plant_data':    True,
            })

    # ── District tertiary component rows (e.g. cooling tower fan electricity) ──
    for network_type, pt in plant_totals.items():
        tertiary_kWh = pt.get('tertiary_kWh', 0.0)
        tertiary_comp = pt.get('tertiary_component', '')
        if tertiary_kWh > 0 and tertiary_comp:
            records.append({
                'primary_carrier':    'Grid Electricity',
                '_carrier_raw':       'GRID',
                'plant_component':    tertiary_comp,
                'network':            network_type,
                'building_component': '',
                'scale':              'District',
                'service':            'Distribution',
                'value_kWh':          tertiary_kWh,
                'plant_input_kWh':    tertiary_kWh,
                '_has_plant_data':    True,
            })

    for building, bconfig in building_configs.items():
        bfile = locator.get_final_energy_building_file(building, whatif_name)
        if not os.path.exists(bfile):
            continue

        annual = pd.read_csv(bfile).sum(numeric_only=True)

        # Build booster lookup: {base_cfg_key: {carrier_raw: component_code}}
        # Booster carriers are processed separately; skip them in the base service loop.
        booster_carriers: dict[str, set] = {}
        for bst_key in ('space_heating_booster', 'hot_water_booster'):
            bst_cfg = bconfig.get(bst_key)
            if not isinstance(bst_cfg, dict) or bst_cfg.get('scale') != 'BUILDING':
                continue
            base_key = bst_key.replace('_booster', '')
            c_raw = bst_cfg.get('carrier', '')
            if base_key and c_raw:
                booster_carriers.setdefault(base_key, set()).add(c_raw)

        for cfg_key, (svc_display, col_prefix) in _CONFIG_KEY_MAP.items():
            svc_config = bconfig.get(cfg_key)

            # Electricity has no supply config entry — read columns directly at building scale.
            if not svc_config:
                if cfg_key != 'electricity':
                    continue
                for col in annual.index:
                    if not (col.startswith(f'{col_prefix}_') and col.endswith('_kWh')
                            and col != f'{col_prefix}_kWh'):
                        continue
                    val = annual[col]
                    if val <= 0:
                        continue
                    carrier_raw = col[len(col_prefix) + 1:-4]
                    records.append({
                        'primary_carrier':    carrier_raw,
                        '_carrier_raw':       carrier_raw,
                        'plant_component':    '',
                        'network':            '',
                        'building_component': '',
                        'scale':              'Building',
                        'service':            svc_display,
                        'value_kWh':          val,
                        'plant_input_kWh':    val,
                        '_has_plant_data':    False,
                    })
                continue

            scale = svc_config.get('scale', 'BUILDING')

            if scale == 'DISTRICT':
                network_type = 'DH' if cfg_key in ('space_heating', 'hot_water') else 'DC'
                col = f'{col_prefix}_{network_type}_kWh'
                val = annual.get(col, 0)
                if val <= 0:
                    continue

                pt = plant_totals.get(network_type)
                if pt:
                    carrier_raw = pt['_carrier_raw']
                    carrier = pt['carrier']
                    plant_comp = pt['primary_component']
                    plant_input = pt['input_kWh']
                    has_plant = True
                else:
                    # No plant files: infer carrier from the plant config if available,
                    # otherwise from the building's district assembly.
                    # DH/DC are network types, not city-scale energy carriers.
                    pc = plant_configs.get(network_type, {})
                    carrier_raw = pc.get('carrier') or svc_config.get('carrier', network_type)
                    if carrier_raw in ('DH', 'DC'):
                        # DH/DC are not primary carriers — default to electricity
                        from cea.technologies.energy_carriers import electricity_carrier
                        carrier_raw = electricity_carrier(locator)
                    carrier = carrier_raw
                    primary = pc.get('primary_component') or svc_config.get('primary_component', '')
                    plant_comp = component_display(primary, locator) if primary else ''
                    plant_input = val
                    has_plant = False

                # District connections have a heat exchanger at the building boundary.
                # The tertiary_component (e.g. CT1) belongs to the plant, not the building.
                building_comp = component_display('HEX', locator)

                records.append({
                    'primary_carrier':    carrier,
                    '_carrier_raw':       carrier_raw,
                    'plant_component':    plant_comp,
                    'network':            network_type,
                    'building_component': building_comp,
                    'scale':              'District',
                    'service':            svc_display,
                    'value_kWh':          val,
                    'plant_input_kWh':    plant_input,
                    '_has_plant_data':    has_plant,
                })

            else:
                primary_carrier_raw = svc_config.get('carrier', '')
                primary_component_code = svc_config.get('primary_component', '')
                booster_only_carriers = booster_carriers.get(cfg_key, set()) - {primary_carrier_raw}
                # Demand column: useful energy delivered to service
                demand_col = f'{col_prefix}_kWh'
                demand_total = annual.get(demand_col, 0)

                # Build carrier → (component_code, efficiency) map from the
                # saved supply config. Covers primary + real secondary +
                # tertiary (if ever serialised with its own info). Tertiary
                # CTs today have no separate ``Qxx_sys_*_kWh`` column
                # (their fan electricity is aggregated into the primary's
                # carrier column upstream in calculation.py), so the map
                # entry is harmless when no matching column exists.
                component_by_carrier: dict = {}
                if primary_component_code and primary_carrier_raw:
                    component_by_carrier[primary_carrier_raw] = (
                        primary_component_code,
                        float(svc_config.get('efficiency') or 1.0),
                    )
                for role in ('secondary', 'tertiary'):
                    role_code = svc_config.get(f'{role}_component')
                    role_info = svc_config.get(f'{role}_info') or {}
                    role_carrier = role_info.get('carrier')
                    if role_code and role_carrier:
                        # Primary wins if two roles share a carrier.
                        component_by_carrier.setdefault(role_carrier, (
                            role_code,
                            float(role_info.get('efficiency') or 1.0),
                        ))

                # Count distinct, non-booster, non-zero ``Qxx_sys_*`` carriers
                # to distinguish "primary covers all" (single-carrier, absorb
                # η into the primary component node) from "primary + real
                # secondary" (multi-carrier, localise each carrier's η at
                # its own component node so the service bar balances).
                service_carrier_cols = [
                    c for c in annual.index
                    if c.startswith(f'{col_prefix}_') and c.endswith('_kWh')
                    and c != f'{col_prefix}_kWh'
                    and not c.endswith('_dumped_kWh')
                    and annual[c] > 0
                    and c[len(col_prefix) + 1:-4] not in booster_only_carriers
                ]
                primary_covers_all = len(service_carrier_cols) <= 1

                for col in annual.index:
                    if not (col.startswith(f'{col_prefix}_') and col.endswith('_kWh')
                            and col != f'{col_prefix}_kWh'):
                        continue
                    # Skip diagnostic *_dumped_kWh columns (SC tank surplus) —
                    # not a delivered carrier, must not appear as a Sankey flow.
                    if col.endswith('_dumped_kWh'):
                        continue
                    val = annual[col]
                    if val <= 0:
                        continue

                    carrier_raw = col[len(col_prefix) + 1:-4]
                    if carrier_raw in booster_only_carriers:
                        continue  # handled by booster loop below

                    comp_info = component_by_carrier.get(carrier_raw)
                    if comp_info:
                        comp_code, eta = comp_info
                        comp = component_display(comp_code, locator)
                    else:
                        comp, eta = '', 1.0

                    # Source-side width (carrier input). For most carriers
                    # this equals ``val`` (e.g. fuel burned, grid kWh). For
                    # SOLAR SC-DHW, ``val`` is the *delivered* share — the
                    # real carrier input is the gross Q_SC_gen produced by
                    # the collectors before tank losses and pressure-relief
                    # dumping. Recompute it on the fly from the SC potential
                    # files on disk so the SC node narrows from gross-in to
                    # net-out, mirroring how BO1 / HP1 are rendered.
                    plant_input_val = val
                    if (comp and carrier_raw == 'SOLAR'
                            and cfg_key == 'hot_water'):
                        gross_kwh = _sc_gross_kwh_for_building(
                            building, bconfig, locator
                        )
                        if gross_kwh > val:
                            plant_input_val = gross_kwh

                    # value_kWh      = delivered-to-service (sink side width)
                    # plant_input_kWh = carrier input       (source side width)
                    if primary_covers_all and carrier_raw == primary_carrier_raw and comp:
                        # Single-carrier service: render sink side at demand
                        # so boiler (η<1) and HP (COP>1) efficiencies are
                        # absorbed into the node's width change rather than
                        # showing up as missing or extra heat.
                        output_kWh = demand_total
                    elif comp:
                        # Multi-carrier service: each carrier's delivered
                        # share is val × η, localising the loss at its own
                        # component node. Σ output_kWh across arcs ≈ demand.
                        output_kWh = val * eta
                    else:
                        # No component node on this arc (carrier not mapped
                        # to any configured component) — draw carrier = delivered.
                        output_kWh = val

                    records.append({
                        'primary_carrier':    carrier_raw,
                        '_carrier_raw':       carrier_raw,
                        'plant_component':    '',
                        'network':            '',
                        'building_component': comp,
                        'scale':              'Building',
                        'service':            svc_display,
                        'value_kWh':          output_kWh,
                        'plant_input_kWh':    plant_input_val,
                        '_has_plant_data':    False,
                        '_is_booster':        False,
                    })

        # ── Booster components (space_heating_booster / hot_water_booster) ──
        for bst_key in ('space_heating_booster', 'hot_water_booster'):
            bst_cfg = bconfig.get(bst_key)
            if not isinstance(bst_cfg, dict) or bst_cfg.get('scale') != 'BUILDING':
                continue
            base_key = bst_key.replace('_booster', '')
            svc_display, col_prefix = _CONFIG_KEY_MAP.get(base_key, ('', ''))
            if not svc_display:
                continue
            bst_carrier_raw = bst_cfg.get('carrier', '')
            bst_comp_code   = bst_cfg.get('primary_component', '')
            if not bst_carrier_raw:
                continue
            bst_col_prefix = _BOOSTER_COL_PREFIX.get(bst_key, '')
            if not bst_col_prefix:
                continue
            bst_carrier_col = f'{bst_col_prefix}_{bst_carrier_raw}_kWh'
            bst_demand_col = f'{bst_col_prefix}_kWh'
            carrier_val = annual.get(bst_carrier_col, 0)
            if carrier_val <= 0:
                continue
            # Read booster demand from CSV; both columns are in B####.csv
            demand_val = annual.get(bst_demand_col, carrier_val)
            records.append({
                'primary_carrier':    bst_carrier_raw,
                '_carrier_raw':       bst_carrier_raw,
                'plant_component':    '',
                'network':            '',
                'building_component': component_display(bst_comp_code, locator) if bst_comp_code else '',
                'scale':              'Building',
                'service':            svc_display,
                'value_kWh':          demand_val,
                'plant_input_kWh':    carrier_val,
                '_has_plant_data':    False,
                '_is_booster':        True,
            })

        # ── Solar panel generation ──────────────────────────────────────────
        # Solar flows never deduct from demand; they go to separate Offset nodes.
        # Config structure: {"surface": "tech_code"}, e.g. {"roof": "PV_PV3"}.
        #
        # plant_input_kWh = irradiation that landed on **this surface only**,
        # computed on-the-fly from the matching solar potential file (see
        # `_solar_per_surface_radiation_kwh`). Replaces the previous
        # "attribute the full per-panel-type aggregate to the first surface"
        # hack, which inflated the source-side width by 10–60× when the
        # potential simulation covered surfaces the user never configured.
        # value_kWh = useful output (electricity or heat).
        solar_config = bconfig.get('solar', {})
        for surface, tech_code in solar_config.items():
            if not tech_code:
                continue
            comp = component_display(tech_code, locator)
            parts = tech_code.split('_')
            tech_type = parts[0]  # 'PV', 'SC', or 'PVT'

            if tech_type == 'PV':
                val = annual.get(f'PV_{surface}_kWh', 0)
                if val <= 0:
                    continue
                radiation = _solar_per_surface_radiation_kwh(
                    building, tech_code, surface, locator
                ) or val
                records.append({
                    'primary_carrier':    'Solar',
                    '_carrier_raw':       'SOLAR',
                    'plant_component':    '',
                    'network':            '',
                    'building_component': comp,
                    'scale':              'Building',
                    'service':            '(−) Offset Electricity',
                    'value_kWh':          val,
                    'plant_input_kWh':    radiation,
                    '_has_plant_data':    False,
                })

            elif tech_type == 'SC':
                panel_type = '_'.join(parts[1:])  # 'FP' or 'ET'
                val = annual.get(f'SC_{panel_type}_{surface}_kWh', 0)
                if val <= 0:
                    continue
                radiation = _solar_per_surface_radiation_kwh(
                    building, tech_code, surface, locator
                ) or val
                records.append({
                    'primary_carrier':    'Solar',
                    '_carrier_raw':       'SOLAR',
                    'plant_component':    '',
                    'network':            '',
                    'building_component': comp,
                    'scale':              'Building',
                    'service':            '(−) Offset Heat',
                    'value_kWh':          val,
                    'plant_input_kWh':    radiation,
                    '_has_plant_data':    False,
                })

            elif tech_type == 'PVT':
                panel_type = parts[-1]  # last segment: 'FP' or 'ET'
                val_e = annual.get(f'PVT_{panel_type}_{surface}_E_kWh', 0)
                val_q = annual.get(f'PVT_{panel_type}_{surface}_Q_kWh', 0)
                # Per-surface radiation already accounts for both E and Q;
                # split it proportionally between the two outputs so each
                # arc carries its share of the irradiation source.
                radiation_total = _solar_per_surface_radiation_kwh(
                    building, tech_code, surface, locator
                ) or (val_e + val_q)
                total_out = val_e + val_q
                if val_e > 0:
                    rad_e = radiation_total * (val_e / total_out) if total_out > 0 else 0
                    records.append({
                        'primary_carrier':    'Solar',
                        '_carrier_raw':       'SOLAR',
                        'plant_component':    '',
                        'network':            '',
                        'building_component': comp,
                        'scale':              'Building',
                        'service':            '(−) Offset Electricity',
                        'value_kWh':          val_e,
                        'plant_input_kWh':    rad_e,
                        '_has_plant_data':    False,
                    })
                if val_q > 0:
                    rad_q = radiation_total * (val_q / total_out) if total_out > 0 else 0
                    records.append({
                        'primary_carrier':    'Solar',
                        '_carrier_raw':       'SOLAR',
                        'plant_component':    '',
                        'network':            '',
                        'building_component': comp,
                        'scale':              'Building',
                        'service':            '(−) Offset Heat',
                        'value_kWh':          val_q,
                        'plant_input_kWh':    rad_q,
                        '_has_plant_data':    False,
                    })

    # ── District thermal network losses (plant output − building receipts) ────
    for nt, pt in plant_totals.items():
        thermal_load = pt.get('thermal_load_kWh', 0.0)
        if thermal_load <= 0:
            continue
        receipts = sum(
            r['value_kWh'] for r in records
            if r.get('scale') == 'District'
            and r.get('network') == nt
            and r.get('service') != 'Distribution'
        )
        thermal_loss = thermal_load - receipts
        if thermal_loss > 0:
            records.append({
                'primary_carrier':    pt['carrier'],
                '_carrier_raw':       pt['_carrier_raw'],
                'plant_component':    pt.get('primary_component', ''),
                'network':            nt,
                'building_component': '',
                'scale':              'District',
                'service':            'Distribution',
                'value_kWh':          thermal_loss,
                'plant_input_kWh':    0.0,
                '_has_plant_data':    True,
            })

    # Ensure all records have _is_booster (default False)
    for r in records:
        r.setdefault('_is_booster', False)

    if not records:
        cols = ['primary_carrier', '_carrier_raw', 'plant_component', 'network',
                'building_component', 'scale', 'service', 'value_kWh',
                'plant_input_kWh', '_has_plant_data', '_is_booster']
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(records)

    group_cols = ['primary_carrier', '_carrier_raw', 'plant_component', 'network',
                  'building_component', 'scale', 'service', '_has_plant_data', '_is_booster']

    district = df[df['scale'] == 'District']
    building = df[df['scale'] == 'Building']

    parts = []
    if not district.empty:
        # value_kWh: sum across buildings
        # plant_input_kWh: when plant data exists the total is the same for every building row
        #   → take max to avoid double-counting; when no plant data it equals value_kWh → sum
        has_plant = district.groupby(group_cols)['_has_plant_data'].any()
        d_agg = district.groupby(group_cols, as_index=False).agg(
            value_kWh=('value_kWh', 'sum'),
            plant_input_kWh=('plant_input_kWh', 'sum'),
        )
        # Overwrite with max for rows that have real plant data (avoids double-counting)
        for i, row in d_agg.iterrows():
            key = tuple(row[c] for c in group_cols)
            if has_plant.get(key, False):
                grp = district.groupby(group_cols).get_group(key)
                d_agg.at[i, 'plant_input_kWh'] = grp['plant_input_kWh'].max()
        parts.append(d_agg)
    if not building.empty:
        b_agg = building.groupby(group_cols, as_index=False).agg(
            value_kWh=('value_kWh', 'sum'),
            plant_input_kWh=('plant_input_kWh', 'sum'),
        )
        parts.append(b_agg)

    return pd.concat(parts, ignore_index=True)


# ── core data builder ─────────────────────────────────────────────────────────

def build_sankey_data(df, service_filter, unit_divisor, use_solar_irradiation=True):
    """
    Build a 5-layer Sankey: City → District → Building → Distribution → End-use service.

    Column layout (auto-collapses when a layer has no data):
      l0 City        — energy carriers (Natural Gas, Oil, Grid Electricity, …)
      l1 District    — district plant equipment (BO1, Pump) + invisible pass-throughs
      l2 Building    — booster / standalone building equipment (BO2, standalone boilers)
      l3 Distribution— building-side district interface nodes (HEX)
      l4 Service     — end-use services (Space Heating, Domestic Hot Water, …)

    Typical flow paths:
      NatGas → BO1 [l1] → HEX [l3] → Space Heating [l4]
      Oil → [PT l1] → BO2 [l2] → HEX [l3] → Hot Water [l4]
      Electricity → Electricity [l4]  (no intermediate nodes)

    Parameters
    ----------
    df             Output of load_energy_flow_data().
    service_filter list[str]  Subset of _SERVICE_DISPLAY keys. Empty = all.
    unit_divisor   float
    normaliser     float      GFA in m² when normalising per m²; 1.0 otherwise.

    Returns
    -------
    dict  node_labels, node_colors, node_x, source, target, value, link_colors
    None  if no non-zero data.
    """
    if not service_filter:
        service_filter = list(_SERVICE_DISPLAY.keys())

    show_district = True
    show_building = True
    divisor = unit_divisor

    service_display_filter = [_SERVICE_DISPLAY[s] for s in service_filter if s in _SERVICE_DISPLAY]
    # Always include Distribution: it carries district pumping + thermal losses
    # which are intrinsic to district systems, not a user-selectable service.
    df = df[df['service'].isin(service_display_filter) | (df['service'] == 'Distribution')].copy()
    df = df[df['value_kWh'] > 0]
    if df.empty:
        return None

    district_df = df[df['scale'] == 'District']
    building_df = df[df['scale'] == 'Building']

    # ── Layer 0: City ──────────────────────────────────────────────────────
    carrier_set = set(df['primary_carrier'].unique())
    l0 = sorted(carrier_set)

    # ── Layer 1: district plant components ────────────────────────────────
    l1 = (
        sorted(set(district_df['plant_component'].unique()) - {''})
        if show_district and not district_df.empty else []
    )
    l1_set = set(l1)

    # ── Layer 2: building-scale components (boosters + standalone) ────────
    # Components that share a name with l1 (district plant) or l3 (HEX) need
    # a unique internal key so they get their own node. Prefix with '__bldg__';
    # the visual label is the original name (stripped in node_labels below).
    l3_raw = set(district_df['building_component'].unique()) - {''}

    l2_raw = set(building_df['building_component'].unique()) - {''}
    # Disambiguate: building components that collide with l1 or l3 get prefixed
    _l2_collisions = (l2_raw & l1_set) | (l2_raw & l3_raw)
    if _l2_collisions and not building_df.empty:
        building_df = building_df.copy()
        building_df.loc[building_df['building_component'].isin(_l2_collisions), 'building_component'] = (
            '__bldg__' + building_df.loc[building_df['building_component'].isin(_l2_collisions), 'building_component']
        )
        l2_raw = set(building_df['building_component'].unique()) - {''}
    l2 = sorted(l2_raw - l1_set - l3_raw) if show_building else []
    l2_set = set(l2)

    # ── Layer 3: district building-side components (HEX) ──────────────────
    # Building-boundary interface nodes for district systems (e.g. Heat Exchanger).
    l3 = sorted(l3_raw) if show_building else []
    l3_set = set(l3)

    # Transparent pass-through nodes at l1 for building-scale carriers.
    # arrangement='snap' uses DAG depth, not x hints, for intermediate nodes.
    # Without a pass-through, Oil→BO2 puts BO2 at depth 1 (District column).
    # With a pass-through at l1: Oil→PT[depth 1]→BO2[depth 2] = Building column.
    building_pt: dict[str, str] = {}
    if not building_df.empty:
        for carrier in building_df['primary_carrier'].unique():
            if not carrier:
                continue
            bcs = set(
                building_df[building_df['primary_carrier'] == carrier]['building_component'].unique()
            ) - {''}
            if bcs & l2_set:
                building_pt[carrier] = f'__bpt__{carrier}'
    l1_pt = sorted(building_pt.values())

    # Lookup: l3 HEX nodes per service — used to route booster components through HEX.
    # A booster in l2 routes: carrier → PT[l1] → BO2[l2] → HEX[l3] → service[l4].
    service_to_hex: dict[str, list[str]] = {}
    if not district_df.empty and l3_set:
        for svc, grp in district_df.groupby('service'):
            hexes = [bc for bc in grp['building_component'].unique() if bc in l3_set]
            if hexes:
                service_to_hex[svc] = hexes

    # ── Layer 4: End-use service ───────────────────────────────────────────
    svc_set = set(df['service'].unique())
    l4 = [s for s in _SERVICE_ORDER if s in svc_set] + sorted(svc_set - set(_SERVICE_ORDER))

    # ── Build node list ────────────────────────────────────────────────────
    layer_specs = [
        (l0,          0),
        (l1 + l1_pt,  1),
        (l2,          2),
        (l3,          3),
        (l4,          4),
    ]

    node_keys: list[str] = []
    node_labels: list[str] = []
    node_x_list: list[float] = []

    for nodes, layer in layer_specs:
        for n in nodes:
            node_keys.append(n)
            label = n
            if n.startswith('__bpt__'):
                label = ''
            elif n.startswith('__bldg__'):
                label = n[len('__bldg__'):]
            node_labels.append(label)
            node_x_list.append(_LAYER_X[layer])

    if not node_keys:
        return None

    idx = {key: i for i, key in enumerate(node_keys)}

    # ── Node colours ───────────────────────────────────────────────────────
    carrier_colour_map = {
        row['primary_carrier']: _carrier_colour(row['_carrier_raw'])
        for _, row in df.drop_duplicates('primary_carrier').iterrows()
    }

    def _node_colour(key, layer):
        if key.startswith('__bpt__'):
            carrier_name = key[len('__bpt__'):]
            return _to_rgba(carrier_colour_map.get(carrier_name, COLOURS_TO_RGB['grey']))
        if key.startswith('__bldg__'):
            return component_tech_colour(key[len('__bldg__'):])
        if layer == 0:
            return carrier_colour_map.get(key, COLOURS_TO_RGB['grey'])
        if layer in (1, 2, 3):
            return component_tech_colour(key)
        return _SERVICE_COLOURS.get(key, COLOURS_TO_RGB['grey'])

    node_colors = [_node_colour(k, lyr) for k, lyr in zip(node_keys, [
        layer for nodes, layer in layer_specs for _ in nodes
    ])]

    # ── Link builder ───────────────────────────────────────────────────────
    srcs, tgts, vals, link_colors = [], [], [], []

    def add_link(src_key, tgt_key, val, colour):
        if src_key not in idx or tgt_key not in idx or val <= 0:
            return
        srcs.append(idx[src_key])
        tgts.append(idx[tgt_key])
        vals.append(val / divisor)
        link_colors.append(_to_rgba(colour))

    # ── Helper: service colour for links targeting end-use nodes ─────────
    def _svc_colour(service):
        return _SERVICE_COLOURS.get(service, COLOURS_TO_RGB['grey'])

    # ── District flows ─────────────────────────────────────────────────────
    if not district_df.empty:
        # Carrier → plant component: one aggregated link per (carrier, plant)
        for (d_carrier, pc), grp in district_df.groupby(['primary_carrier', 'plant_component']):
            c_colour = carrier_colour_map.get(d_carrier, COLOURS_TO_RGB['grey'])
            plant_val = grp['plant_input_kWh'].max()
            if show_district and pc and pc in idx:
                add_link(d_carrier, pc, plant_val, c_colour)

        # Plant/carrier → building component → service
        # Aggregate across buildings first to avoid one link per building
        d_path_agg = (
            district_df
            .groupby(['primary_carrier', 'plant_component', 'building_component', 'service'],
                     as_index=False)
            .agg(value_kWh=('value_kWh', 'sum'))
        )
        for _, row in d_path_agg.iterrows():
            d_carrier = row['primary_carrier']
            pc        = row['plant_component']
            bc        = row['building_component']
            service   = row['service']
            d_val     = row['value_kWh']
            svc_col   = _svc_colour(service)
            c_colour  = carrier_colour_map.get(d_carrier, COLOURS_TO_RGB['grey'])
            # pc_colour = component_tech_colour(pc) if pc else c_colour

            prev = (
                pc if (show_district and pc and pc in idx)
                else d_carrier
            )
            if show_building and bc and bc in idx:
                add_link(prev, bc, d_val, svc_col)
                add_link(bc, service, d_val, svc_col)
            else:
                add_link(prev, service, d_val, svc_col)

    # ── Building-scale flows ───────────────────────────────────────────────
    # Aggregate across buildings first.
    # plant_input_kWh = carrier energy consumed (irradiation for solar, = value_kWh otherwise).
    # Using plant_input_kWh for the carrier→component link creates an unequal node width
    # that implicitly shows conversion efficiency (e.g. solar panel COP).
    # When use_solar_irradiation is False, treat carrier_kWh == value_kWh for Solar rows
    # so solar nodes appear with equal in/out widths (no efficiency visualisation).
    # Ensure _is_booster column exists (default False for records that don't set it)
    if '_is_booster' not in building_df.columns:
        building_df = building_df.copy()
        building_df['_is_booster'] = False
    else:
        building_df = building_df.copy()
        building_df['_is_booster'] = building_df['_is_booster'].fillna(False)

    b_path_agg = (
        building_df
        .groupby(['primary_carrier', 'building_component', 'service', '_is_booster'], as_index=False)
        .agg(value_kWh=('value_kWh', 'sum'), carrier_kWh=('plant_input_kWh', 'sum'))
    )
    if not use_solar_irradiation:
        is_solar = b_path_agg['primary_carrier'] == 'Solar'
        b_path_agg.loc[is_solar, 'carrier_kWh'] = b_path_agg.loc[is_solar, 'value_kWh']
    for _, row in b_path_agg.iterrows():
        carrier      = row['primary_carrier']
        bc           = row['building_component']
        service      = row['service']
        is_booster   = row['_is_booster']
        val          = row['value_kWh']       # useful output: component → service
        carrier_val  = row['carrier_kWh']     # carrier input: carrier → component
        c_colour     = carrier_colour_map.get(carrier, COLOURS_TO_RGB['grey'])
        svc_col      = _svc_colour(service)

        if show_building and bc and bc in idx:
            if bc in l2_set:
                # Building-scale component (l2): route via pass-through at l1 so snap
                # places BO2 at DAG depth 2 (Building column) not depth 1 (District).
                pt = building_pt.get(carrier)
                if pt and pt in idx:
                    add_link(carrier, pt, carrier_val, c_colour)
                    add_link(pt,      bc, carrier_val, c_colour)
                else:
                    add_link(carrier, bc, carrier_val, c_colour)
                # Booster routes through HEX (district interface).
                # Standalone and solar go directly to service.
                is_solar = carrier == 'Solar'
                if is_booster and not is_solar:
                    hex_nodes = service_to_hex.get(service, [])
                    if hex_nodes:
                        for hex_node in hex_nodes:
                            if hex_node in idx:
                                add_link(bc, hex_node, val, svc_col)
                                add_link(hex_node, service, val, svc_col)
                    else:
                        add_link(bc, service, val, svc_col)
                else:
                    add_link(bc, service, val, svc_col)
            else:
                # Component shared with District layer (e.g. standalone building uses same
                # code as district plant). Route through HEX if one exists for this service,
                # consistent with how district buildings are routed.
                add_link(carrier, bc, carrier_val, c_colour)
                hex_nodes = service_to_hex.get(service, [])
                if hex_nodes:
                    for hex_node in hex_nodes:
                        if hex_node in idx:
                            add_link(bc, hex_node, val, svc_col)
                            add_link(hex_node, service, val, svc_col)
                else:
                    add_link(bc, service, val, svc_col)
        else:
            add_link(carrier, service, carrier_val, svc_col)

    if not srcs:
        return None

    # Merge duplicate (source, target) links — same component routing to the same
    # node via multiple services creates separate bands in Plotly; consolidate them.
    link_map: dict[tuple, list] = {}
    for s, t, v, c in zip(srcs, tgts, vals, link_colors):
        key = (s, t)
        if key in link_map:
            link_map[key][0] += v
        else:
            link_map[key] = [v, c]
    srcs        = [k[0]    for k in link_map]
    tgts        = [k[1]    for k in link_map]
    vals        = [v[0]    for v in link_map.values()]
    link_colors = [v[1]    for v in link_map.values()]

    return {
        'node_labels': node_labels,
        'node_colors': node_colors,
        'node_x':      node_x_list,
        'source':      srcs,
        'target':      tgts,
        'value':       vals,
        'link_colors': link_colors,
    }


# ── figure builder ────────────────────────────────────────────────────────────

def create_sankey_fig(sankey_data, title, unit_label):
    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            label=sankey_data['node_labels'],
            color=sankey_data['node_colors'],
            x=sankey_data['node_x'],
            pad=24,
            thickness=20,
            line=dict(color='rgba(0,0,0,0)', width=0),
        ),
        link=dict(
            source=sankey_data['source'],
            target=sankey_data['target'],
            value=sankey_data['value'],
            color=sankey_data['link_colors'],
            hovertemplate=(
                '%{source.label} → %{target.label}<br>'
                f'Energy: %{{value:,.2f}} {unit_label}<br>'
                '<extra></extra>'
            ),
        ),
    ))
    # ── Column labels and divider lines ────────────────────────────────────
    # End-use services belong to the Building zone, so Building spans l2–l4.
    # City | District | Building (l2 + l3 + l4)
    building_label_x = (_LAYER_X[2] + _LAYER_X[4]) / 2
    column_labels = [
        ('City',     _LAYER_X[0]),
        ('District', _LAYER_X[1]),
        ('Building', building_label_x),
    ]
    visible_xs = set(
        x for lbl, x in zip(sankey_data['node_labels'], sankey_data['node_x'])
        if lbl != ''
    )
    annotations = []
    for lbl, x in column_labels:
        if lbl == 'Building':
            show = any(
                _LAYER_X[i] in visible_xs for i in (2, 3, 4)
            )
        else:
            show = x in visible_xs
        if show:
            annotations.append(dict(
                x=x, y=-0.08,
                xref='paper', yref='paper',
                text=f'<b>{lbl}</b>',
                showarrow=False,
                font=dict(size=12, color=COLOURS_TO_RGB['grey']),
            ))

    # Dashed vertical dividers between layer zones. Drawn between any two
    # *adjacent* visible zones — so a building-only scenario (no district)
    # still gets a single City | Building divider, not nothing.
    city_visible     = _LAYER_X[0] in visible_xs
    district_visible = _LAYER_X[1] in visible_xs
    building_visible = any(_LAYER_X[i] in visible_xs for i in (2, 3, 4))

    def _divider_shape(x_left, x_right):
        return dict(
            type='line',
            x0=(x_left + x_right) / 2,
            x1=(x_left + x_right) / 2,
            y0=0.02, y1=0.98,
            xref='paper', yref='paper',
            line=dict(color='rgba(150,150,150,0.5)', width=1, dash='6,3'),
        )

    shapes = []
    if city_visible and district_visible:
        shapes.append(_divider_shape(_LAYER_X[0], _LAYER_X[1]))
    if district_visible and building_visible:
        shapes.append(_divider_shape(_LAYER_X[1], _LAYER_X[2]))
    if city_visible and building_visible and not district_visible:
        # No district column — single divider sits between City and the
        # first Building column at the same x where the City|District
        # divider would have been, so the with/without-district layouts
        # share the same visual rhythm.
        shapes.append(_divider_shape(_LAYER_X[0], _LAYER_X[1]))

    fig.update_layout(
        title=dict(text=title, x=0, xanchor='left', yanchor='top', font=dict(size=20)),
        font_size=12,
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white'],
        margin=dict(l=20, r=20, t=80, b=60),
        annotations=annotations,
        shapes=shapes,
    )
    return fig


# ── main entry point ──────────────────────────────────────────────────────────

def main(config: cea.config.Configuration):
    locator = InputLocator(config.scenario)
    plot_config = config.plots_energy_sankey

    whatif_names = getattr(plot_config, 'what_if_name', [])
    if not whatif_names:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No what-if scenario selected</h3>'
            '<p>Please select a what-if scenario with final energy results.</p>'
            '</div>'
        )

    service_filter = plot_config.y_service_category_to_plot
    y_metric_unit = plot_config.y_metric_unit
    unit_divisor = _UNIT_DIVISORS.get(y_metric_unit, 1_000)
    unit_label = y_metric_unit
    custom_title = plot_config.plot_title
    use_solar_irradiation = getattr(plot_config, 'use_solar_irradiation', True)

    # ── First pass: build all sankey_data, collect totals for proportional height ──
    _BASE_HEIGHT = 600
    _MIN_HEIGHT = 150
    # slot: either ('ok', whatif_name, sankey_data) or ('err', html_str)
    slots = []

    for whatif_name in whatif_names:
        if locator.find_analysis_configuration_file(whatif_name) is None:
            expected_path = locator.get_analysis_configuration_file(whatif_name)
            slots.append(('err', (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
                f'background:#ffe0e0;margin:12px 0">'
                f'<h3>Final energy data not found for <em>{whatif_name}</em></h3>'
                f'<p>Run <strong>final-energy</strong> for this scenario first.</p>'
                f'<code>{expected_path}</code>'
                f'</div>'
            )))
            continue

        df = load_energy_flow_data(locator, whatif_name)
        sankey_data = build_sankey_data(df, service_filter, unit_divisor, use_solar_irradiation)
        if sankey_data is None:
            slots.append(('err', (
                f'<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
                f'background:#fff8e1;margin:12px 0">'
                f'<h3>No energy flow data for <em>{whatif_name}</em></h3>'
                f'<p>The selected service categories produced no non-zero values.</p>'
                f'</div>'
            )))
            continue

        slots.append(('ok', whatif_name, sankey_data))

    global_total = max(
        (sum(sd['value']) for kind, *rest in slots if kind == 'ok' for sd in [rest[1]]),
        default=1.0,
    )

    # ── Second pass: render with proportional heights, preserve order ─────────
    html_outputs = []
    plotly_included = False
    for slot in slots:
        if slot[0] == 'err':
            html_outputs.append(slot[1])
            continue
        _, whatif_name, sankey_data = slot
        scenario_total = sum(sankey_data['value'])
        height = max(_MIN_HEIGHT, int(_BASE_HEIGHT * scenario_total / global_total))
        scenario_name = os.path.basename(config.scenario)
        feature_label = custom_title or 'CEA-4 Energy Flow'
        subtitle_parts = [feature_label, scenario_name, whatif_name]
        subtitle = ' | '.join(subtitle_parts)
        title = f"<b>Energy Flow</b><br><sub>{subtitle}</sub>"
        fig = create_sankey_fig(sankey_data, title, unit_label)
        fig.update_layout(height=height, autosize=False)
        include_js = 'cdn' if not plotly_included else False
        plotly_included = True
        html_outputs.append(fig.to_html(full_html=False, include_plotlyjs=include_js,
                                        config={'responsive': True}))

    if not html_outputs:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No energy flow data to display</h3>'
            '</div>'
        )

    body = '\n'.join(html_outputs)
    return (
        '<!DOCTYPE html><html>'
        '<head><meta charset="utf-8"><style>html,body{height:100%;margin:0}</style></head>'
        f'<body>{body}</body></html>'
    )


if __name__ == '__main__':
    main(cea.config.Configuration())
