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

import json
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

_CARRIER_COLOURS = {
    'NATURALGAS':  COLOURS_TO_RGB['orange'],
    'GRID':        COLOURS_TO_RGB['green'],
    'GRID_DIRECT': COLOURS_TO_RGB['green_light'],
    'DH':          COLOURS_TO_RGB['red'],
    'DC':          COLOURS_TO_RGB['blue'],
    'WOOD':        COLOURS_TO_RGB['brown'],
    'OIL':         COLOURS_TO_RGB['brown_light'],
    'COAL':        COLOURS_TO_RGB['grey'],
    'SOLAR':       COLOURS_TO_RGB['yellow'],
}

_CARRIER_DISPLAY = {
    'NATURALGAS':  'Natural Gas',
    'GRID':        'Electricity Grid',
    'GRID_DIRECT': 'Building Electricity',
    'DH':          'District Heating',
    'DC':          'District Cooling',
    'WOOD':        'Wood',
    'OIL':         'Oil',
    'COAL':        'Coal',
    'SOLAR':       'Solar',
}


def _carrier_display(code):
    return _CARRIER_DISPLAY.get(code, code)


def _carrier_colour(code):
    if code.startswith('PV_') or code.startswith('SC_') or code.startswith('PVT_'):
        return COLOURS_TO_RGB['yellow']
    return _CARRIER_COLOURS.get(code, COLOURS_TO_RGB['grey'])


# ── Layer 1: scale ────────────────────────────────────────────────────────────

_SCALE_COLOURS = {
    'Building':         COLOURS_TO_RGB['blue_light'],
    'DC Network':       COLOURS_TO_RGB['teal_light'],
    'DH Network':       COLOURS_TO_RGB['red_light'],
}

# ── Layer 2: components ───────────────────────────────────────────────────────


# ── Layer 3: services ─────────────────────────────────────────────────────────

_CARRIER_ORDER = [
    'Electricity Grid',
    'Building Electricity',
    'Natural Gas',
    'Wood',
    'Oil',
    'Coal',
    'Solar',
    'District Heating',
    'District Cooling',
]

_SERVICE_ORDER = [
    'Space Heating',
    'Domestic Hot Water',
    'Space Cooling',
    'Electricity',
    'Distribution',
]

_SERVICE_COLOURS = {
    'Space Heating':      COLOURS_TO_RGB['red_light'],
    'Domestic Hot Water': COLOURS_TO_RGB['orange_light'],
    'Space Cooling':      COLOURS_TO_RGB['blue_light'],
    'Electricity':        COLOURS_TO_RGB['green_light'],
    'Distribution':       COLOURS_TO_RGB['grey_light'],
}

# Maps config parameter choice → service display name
_SERVICE_DISPLAY = {
    'space_heating':      'Space Heating',
    'domestic_hot_water': 'Domestic Hot Water',
    'space_cooling':      'Space Cooling',
    'electricity':        'Electricity',
    'distribution':       'Distribution',
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


# ── plant data loader ─────────────────────────────────────────────────────────

def _load_plant_totals(locator, whatif_name, plant_configs, building_configs):
    """
    Load annual plant energy input totals from plant CSV files.

    Returns dict keyed by network_type ('DH' or 'DC'):
      {
        '_carrier_raw': 'GRID',
        'carrier': 'Electricity Grid',
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
    folder = locator.get_final_energy_folder(whatif_name)

    for plant_name, plant_cfg in plant_configs.items():
        network_type = plant_cfg.get('network_type', '')
        carrier_raw = plant_cfg.get('carrier', 'GRID')
        component_code = plant_cfg.get('primary_component', '')
        network_name = network_names.get(network_type, '')
        if not network_type or not network_name:
            continue

        # Scan for all plant files: {network_name}_{network_type}_{plant_name}.csv
        prefix = f'{network_name}_{network_type}_'
        plant_files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.startswith(prefix) and f.endswith('.csv')
        ]
        if not plant_files:
            continue

        carrier_col = (
            f'plant_cooling_{carrier_raw}_kWh'
            if network_type == 'DC'
            else f'plant_heating_{carrier_raw}_kWh'
        )

        total_input = 0.0
        total_pumping = 0.0
        total_thermal = 0.0
        for fpath in plant_files:
            plant_df = pd.read_csv(fpath)
            if carrier_col in plant_df.columns:
                total_input += plant_df[carrier_col].sum()
            if 'plant_pumping_GRID_kWh' in plant_df.columns:
                total_pumping += plant_df['plant_pumping_GRID_kWh'].sum()
            if 'thermal_load_kWh' in plant_df.columns:
                total_thermal += plant_df['thermal_load_kWh'].sum()

        if total_input > 0 or total_pumping > 0 or total_thermal > 0:
            if network_type in totals:
                totals[network_type]['input_kWh'] += total_input
                totals[network_type]['pumping_kWh'] += total_pumping
                totals[network_type]['thermal_load_kWh'] += total_thermal
            else:
                totals[network_type] = {
                    '_carrier_raw': carrier_raw,
                    'carrier': _carrier_display(carrier_raw),
                    'component': component_display(component_code) if component_code else '',
                    'input_kWh': total_input,
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
    config_file = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file) as f:
        config_data = json.load(f)

    building_configs = config_data.get('buildings', {})
    plant_configs = config_data.get('plants', {})

    plant_totals = _load_plant_totals(locator, whatif_name, plant_configs, building_configs)

    records = []

    # ── District pumping rows (one per network type) ───────────────────────
    for network_type, pt in plant_totals.items():
        pumping = pt.get('pumping_kWh', 0.0)
        if pumping > 0:
            records.append({
                'primary_carrier':    'Electricity Grid',
                '_carrier_raw':       'GRID',
                'plant_component':    'Pump',
                'network':            network_type,
                'building_component': '',
                'scale':              'District',
                'service':            'Distribution',
                'value_kWh':          pumping,
                'plant_input_kWh':    pumping,
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
            # Use GRID_DIRECT raw code so these flows get a separate 'Building Electricity'
            # carrier node, keeping 'Electricity Grid' only for equipment-mediated flows
            # (e.g. heat pumps, chillers) and preventing direct use from swamping them.
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
                    # Map GRID direct use to GRID_DIRECT so it gets its own carrier node
                    display_raw = 'GRID_DIRECT' if carrier_raw == 'GRID' else carrier_raw
                    records.append({
                        'primary_carrier':    _carrier_display(display_raw),
                        '_carrier_raw':       display_raw,
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
                    plant_comp = pt['component']
                    plant_input = pt['input_kWh']
                    has_plant = True
                else:
                    # No plant files: fall back to network carrier as entry point
                    carrier_raw = network_type  # 'DC' or 'DH'
                    carrier = _carrier_display(carrier_raw)
                    plant_comp = component_display(svc_config.get('primary_component', ''))
                    plant_input = val
                    has_plant = False

                # District connections always have a heat exchanger at the building boundary.
                # Fall back to 'HEX' if no explicit building-side component is configured.
                building_comp = (
                    svc_config.get('tertiary_component')
                    or svc_config.get('secondary_component')
                    or svc_config.get('building_component')
                    or 'HEX'
                )
                building_comp = component_display(building_comp)

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
                component_code = svc_config.get('primary_component', '')
                skip_carriers = booster_carriers.get(cfg_key, set())

                for col in annual.index:
                    if not (col.startswith(f'{col_prefix}_') and col.endswith('_kWh')
                            and col != f'{col_prefix}_kWh'):
                        continue
                    val = annual[col]
                    if val <= 0:
                        continue

                    carrier_raw = col[len(col_prefix) + 1:-4]
                    if carrier_raw in skip_carriers:
                        continue  # handled by booster loop below

                    comp = component_display(component_code) if carrier_raw == primary_carrier_raw else ''

                    records.append({
                        'primary_carrier':    _carrier_display(carrier_raw),
                        '_carrier_raw':       carrier_raw,
                        'plant_component':    '',
                        'network':            '',
                        'building_component': comp,
                        'scale':              'Building',
                        'service':            svc_display,
                        'value_kWh':          val,
                        'plant_input_kWh':    val,
                        '_has_plant_data':    False,
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
            bst_col = f'{bst_col_prefix}_{bst_carrier_raw}_kWh'
            val = annual.get(bst_col, 0)
            if val <= 0:
                continue
            records.append({
                'primary_carrier':    _carrier_display(bst_carrier_raw),
                '_carrier_raw':       bst_carrier_raw,
                'plant_component':    '',
                'network':            '',
                'building_component': component_display(bst_comp_code) if bst_comp_code else '',
                'scale':              'Building',
                'service':            svc_display,
                'value_kWh':          val,
                'plant_input_kWh':    val,
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
                'plant_component':    pt.get('component', ''),
                'network':            nt,
                'building_component': '',
                'scale':              'District',
                'service':            'Distribution',
                'value_kWh':          thermal_loss,
                'plant_input_kWh':    0.0,
                '_has_plant_data':    True,
            })

    if not records:
        cols = ['primary_carrier', '_carrier_raw', 'plant_component', 'network',
                'building_component', 'scale', 'service', 'value_kWh',
                'plant_input_kWh', '_has_plant_data']
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(records)

    group_cols = ['primary_carrier', '_carrier_raw', 'plant_component', 'network',
                  'building_component', 'scale', 'service', '_has_plant_data']

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

def build_sankey_data(df, service_filter, x_to_plot, unit_divisor, normaliser=1.0):
    """
    Build a 5-layer Sankey: City → District → Building → Distribution → End-use service.

    Column layout (auto-collapses to 4 when no booster components exist):
      l0 City        — energy carriers (Natural Gas, Oil, Electricity Grid, …)
      l1 District    — district plant equipment (BO1, Pump) + invisible pass-throughs
      l2 Building    — booster / standalone building equipment (BO2, standalone boilers)
      l3 Distribution— building-side district interface nodes (HEX)
      l4 Service     — end-use services (Space Heating, Domestic Hot Water, …)

    Typical flow paths:
      NatGas → BO1 [l1] → HEX [l3] → Space Heating [l4]
      Oil → [PT l1] → BO2 [l2] → HEX [l3] → Hot Water [l4]
      Electricity → Electricity [l4]  (no intermediate nodes)

    When no booster exists, arrangement='snap' places HEX at topological depth 2
    (Building column), so the layout collapses to 4 columns naturally.

    x_to_plot controls whether real component nodes are shown at each layer:
      'district' → show district plant equipment (Chiller, DH Boiler, …)
      'building' → show building equipment (Heat Exchanger, standalone Boiler, …)

    Parameters
    ----------
    df             Output of load_energy_flow_data().
    service_filter list[str]  Subset of _SERVICE_DISPLAY keys. Empty = all.
    x_to_plot      list[str]  Subset of ['district', 'building'].
    unit_divisor   float
    normaliser     float      GFA in m² when normalising per m²; 1.0 otherwise.

    Returns
    -------
    dict  node_labels, node_colors, node_x, node_y, source, target, value, link_colors
    None  if no non-zero data.
    """
    if not service_filter:
        service_filter = list(_SERVICE_DISPLAY.keys())

    show_district = 'district' in x_to_plot
    show_building = 'building' in x_to_plot
    divisor = unit_divisor * normaliser

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
    l0 = [c for c in _CARRIER_ORDER if c in carrier_set] + sorted(carrier_set - set(_CARRIER_ORDER))

    # ── Layer 1: district plant components ────────────────────────────────
    l1 = (
        sorted(set(district_df['plant_component'].unique()) - {''})
        if show_district and not district_df.empty else []
    )
    l1_set = set(l1)

    # ── Layer 2: building-scale components (boosters + standalone) ────────
    # Only includes building_df components (not district). Excludes l1 (district
    # plant codes reused as-is) and l3 (district building-side codes like HEX).
    l3_raw = set(district_df['building_component'].unique()) - {''}

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
            node_labels.append('' if n.startswith('__bpt__') else n)
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
            c_colour  = carrier_colour_map.get(d_carrier, COLOURS_TO_RGB['grey'])
            pc_colour = component_tech_colour(pc) if pc else c_colour
            bc_colour = component_tech_colour(bc) if bc else pc_colour

            prev, prev_colour = (
                (pc, pc_colour) if (show_district and pc and pc in idx)
                else (d_carrier, c_colour)
            )
            if show_building and bc and bc in idx:
                add_link(prev, bc, d_val, prev_colour)
                add_link(bc, service, d_val, bc_colour)
            else:
                add_link(prev, service, d_val, prev_colour)

    # ── Building-scale flows ───────────────────────────────────────────────
    # Aggregate across buildings first
    b_path_agg = (
        building_df
        .groupby(['primary_carrier', 'building_component', 'service'], as_index=False)
        .agg(value_kWh=('value_kWh', 'sum'))
    )
    for _, row in b_path_agg.iterrows():
        carrier   = row['primary_carrier']
        bc        = row['building_component']
        service   = row['service']
        val       = row['value_kWh']
        c_colour  = carrier_colour_map.get(carrier, COLOURS_TO_RGB['grey'])
        bc_colour = component_tech_colour(bc) if bc else c_colour

        if show_building and bc and bc in idx:
            if bc in l2_set:
                # Building-scale component (l2): route via pass-through at l1 so snap
                # places BO2 at DAG depth 2 (Building column) not depth 1 (District).
                pt = building_pt.get(carrier)
                if pt and pt in idx:
                    add_link(carrier, pt, val, c_colour)
                    add_link(pt,      bc, val, c_colour)
                else:
                    add_link(carrier, bc, val, c_colour)
                # Booster: if this service has an HEX in l3, route through it.
                # Otherwise (standalone), link directly to service.
                hex_nodes = service_to_hex.get(service, [])
                if hex_nodes:
                    for hex_node in hex_nodes:
                        if hex_node in idx:
                            add_link(bc, hex_node, val, bc_colour)
                            add_link(hex_node, service, val, component_tech_colour(hex_node))
                else:
                    add_link(bc, service, val, bc_colour)
            else:
                # Component shared with District layer (e.g. standalone building uses same
                # code as district plant). Route directly to service — standalone buildings
                # have no district HEX. The district flow already routes district buildings
                # through HEX correctly.
                add_link(carrier, bc, val, c_colour)
                add_link(bc, service, val, bc_colour)
        else:
            add_link(carrier, service, val, c_colour)

    if not srcs:
        return None

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
    # ── Column labels at the bottom ────────────────────────────────────────
    # l2 (booster/standalone) and l3 (HEX/distribution) are both building-side
    # components, so they share one "Building" label centred between them.
    building_x = (_LAYER_X[2] + _LAYER_X[3]) / 2
    column_labels = [
        ('City',            _LAYER_X[0]),
        ('District',        _LAYER_X[1]),
        ('Building',        building_x),
        ('End-use Service', _LAYER_X[4]),
    ]
    visible_xs = set(
        x for lbl, x in zip(sankey_data['node_labels'], sankey_data['node_x'])
        if lbl != ''
    )
    # Building label is visible when either l2 or l3 has nodes
    building_visible = _LAYER_X[2] in visible_xs or _LAYER_X[3] in visible_xs
    annotations = []
    for lbl, x in column_labels:
        show = building_visible if lbl == 'Building' else x in visible_xs
        if show:
            annotations.append(dict(
                x=x, y=-0.08,
                xref='paper', yref='paper',
                text=f'<b>{lbl}</b>',
                showarrow=False,
                font=dict(size=12, color=COLOURS_TO_RGB['grey']),
            ))

    fig.update_layout(
        title_text=title,
        title_font_size=16,
        font_size=12,
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white'],
        margin=dict(l=20, r=20, t=60, b=60),
        annotations=annotations,
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

    whatif_name = whatif_names[0]
    config_path = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_path):
        return (
            f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
            f'background:#ffe0e0;">'
            f'<h3>Final energy data not found</h3>'
            f'<p>Run <strong>final-energy</strong> for scenario <em>{whatif_name}</em> first.</p>'
            f'<code>{config_path}</code>'
            f'</div>'
        )

    df = load_energy_flow_data(locator, whatif_name)

    service_filter = plot_config.y_service_category_to_plot
    x_to_plot = plot_config.x_to_plot
    y_metric_unit = plot_config.y_metric_unit
    unit_divisor = _UNIT_DIVISORS.get(y_metric_unit, 1_000)

    normaliser = 1.0
    if plot_config.y_normalised_by == 'gross_floor_area':
        fe_path = locator.get_final_energy_buildings_file(whatif_name)
        if os.path.exists(fe_path):
            fe_df = pd.read_csv(fe_path)
            gfa = fe_df['GFA_m2'].sum() if 'GFA_m2' in fe_df.columns else 1.0
            normaliser = gfa if gfa > 0 else 1.0
        unit_label = f'{y_metric_unit}/m² GFA'
    else:
        unit_label = y_metric_unit

    sankey_data = build_sankey_data(df, service_filter, x_to_plot, unit_divisor, normaliser)
    if sankey_data is None:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No energy flow data to display</h3>'
            '<p>The selected service categories produced no non-zero values.</p>'
            '</div>'
        )

    title = plot_config.plot_title or f'Energy Flow — {whatif_name}'
    fig = create_sankey_fig(sankey_data, title, unit_label)

    fig.update_layout(autosize=True)
    html = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'responsive': True})
    return html.replace('<head>', '<head><style>html,body{height:100%;margin:0}</style>', 1)


if __name__ == '__main__':
    main(cea.config.Configuration())
