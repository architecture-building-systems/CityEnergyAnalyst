"""
Load Duration Curve by Component.

One plot per selected supply component, showing annual hourly final energy loads
sorted from peak to minimum (load duration curve).

- District-scale components (Chiller, Pump): aggregate across all plant CSV files.
- Building-scale components (Gas Boiler, HEX, etc.): one curve per selected
  building, or aggregated if no buildings selected.
- Multiple what-if scenarios shown as separate lines on the same chart.
"""

import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── component display helpers ─────────────────────────────────────────────────

_COMPONENT_PREFIX_DISPLAY = [
    ('PVT', 'PVT Panel'),
    ('PV',  'PV Panel'),
    ('SC',  'Solar Collector'),
    ('BO',  'Boiler'),
    ('HP',  'Heat Pump'),
    ('CH',  'Chiller'),
    ('CT',  'Cooling Tower'),
    ('PU',  'Pump'),
    ('HEX', 'Heat Exchanger'),
]

_COMPONENT_EXACT_DISPLAY = {
    'PIPES': 'Piping',
    'GRID':  'City Grid',
}


def _component_display(code):
    code = str(code).strip()
    if code in _COMPONENT_EXACT_DISPLAY:
        return _COMPONENT_EXACT_DISPLAY[code]
    for prefix, label in _COMPONENT_PREFIX_DISPLAY:
        if code.startswith(prefix):
            return f'{label} ({code})'
    return code


# ── colours ───────────────────────────────────────────────────────────────────

_TECH_COLOURS = {
    'Boiler':          COLOURS_TO_RGB['red'],
    'Heat Pump':       COLOURS_TO_RGB['orange'],
    'Chiller':         COLOURS_TO_RGB['blue'],
    'Cooling Tower':   COLOURS_TO_RGB['blue'],
    'Pump':            COLOURS_TO_RGB['orange'],
    'Heat Exchanger':  COLOURS_TO_RGB['orange'],
    'City Grid':       COLOURS_TO_RGB['purple'],
    'PV Panel':        COLOURS_TO_RGB['yellow'],
    'Solar Collector': COLOURS_TO_RGB['yellow'],
    'PVT Panel':       COLOURS_TO_RGB['yellow'],
}

# Whatif line colours for multi-scenario comparison
_WHATIF_COLOURS = [
    COLOURS_TO_RGB['blue'],
    COLOURS_TO_RGB['red'],
    COLOURS_TO_RGB['green'],
    COLOURS_TO_RGB['orange'],
    COLOURS_TO_RGB['purple'],
]

_UNIT_DIVISORS = {'kW': 1, 'MW': 1_000}

# Maps configuration.json service key -> B####.csv column prefix
_CONFIG_KEY_COL_PREFIX = {
    'space_heating': 'Qhs_sys',
    'hot_water':     'Qww_sys',
    'space_cooling': 'Qcs_sys',
    'electricity':   'E_sys',
}


def _tech_colour(display_label):
    for base, colour in _TECH_COLOURS.items():
        if display_label.startswith(base):
            return colour
    return COLOURS_TO_RGB['grey']


def _to_rgba(rgb_str, alpha=0.2):
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# ── core data loading ─────────────────────────────────────────────────────────

def _load_config(locator, whatif_name):
    """Load configuration.json for a what-if scenario."""
    config_file = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    with open(config_file) as f:
        return json.load(f)


def _get_network_names_from_buildings(building_configs):
    """Extract network_name per network_type from building configs."""
    network_names = {}
    for bconfig in building_configs.values():
        for cfg_key in ('space_heating', 'hot_water', 'space_cooling'):
            cfg = bconfig.get(cfg_key)
            if not cfg or cfg.get('scale') != 'DISTRICT':
                continue
            nt = 'DH' if cfg_key in ('space_heating', 'hot_water') else 'DC'
            if nt not in network_names and cfg.get('network_name'):
                network_names[nt] = cfg['network_name']
    return network_names


def load_component_hourly(component_display, whatif_name, scales, selected_buildings, locator):
    """
    Load hourly arrays for a given component display name from a what-if scenario.

    Parameters
    ----------
    component_display : str
        Human-readable component label, e.g. 'Chiller (CH1)' or 'Pump'.
    whatif_name : str
        What-if scenario folder name.
    scales : list[str]
        List of scales to search: 'district', 'building', or both.
    selected_buildings : list[str]
        Buildings to include for building-scale components. Empty = aggregate all.
    locator : InputLocator

    Returns
    -------
    dict mapping label -> np.array of 8760 hourly values in kWh/h (= kW).
    For district: {'District': array(8760)}
    For building, no selection: {'All Buildings': array(8760)} (summed)
    For building, with selection: {'B001': array(8760), ...}
    Returns empty dict if no data found.
    """
    config_data = _load_config(locator, whatif_name)
    building_configs = config_data.get('buildings', {})
    plant_configs = config_data.get('plants', {})
    folder = locator.get_final_energy_folder(whatif_name)
    result = {}

    # ── District-scale ─────────────────────────────────────────────────────
    if 'district' in scales:
        network_names = _get_network_names_from_buildings(building_configs)

        if component_display == 'Pump':
            # Pump: sum plant_pumping_GRID_kWh across all plant files
            hourly = np.zeros(8760)
            found = False
            for network_type, network_name in network_names.items():
                prefix = f'{network_name}_{network_type}_'
                plant_files = [
                    os.path.join(folder, f) for f in os.listdir(folder)
                    if f.startswith(prefix) and f.endswith('.csv')
                ]
                for fpath in plant_files:
                    df = pd.read_csv(fpath)
                    if 'plant_pumping_GRID_kWh' in df.columns:
                        vals = df['plant_pumping_GRID_kWh'].values
                        if len(vals) == 8760:
                            hourly += vals
                            found = True
            if found:
                result['District'] = hourly

        else:
            # Non-pump district component: match primary_component of plants
            for plant_name, plant_cfg in plant_configs.items():
                component_code = plant_cfg.get('primary_component', '')
                if not component_code:
                    continue
                if _component_display(component_code) != component_display:
                    continue

                network_type = plant_cfg.get('network_type', '')
                carrier_raw = plant_cfg.get('carrier', 'GRID')
                network_name = network_names.get(network_type, '')
                if not network_type or not network_name:
                    continue

                carrier_col = (
                    f'plant_cooling_{carrier_raw}_kWh'
                    if network_type == 'DC'
                    else f'plant_heating_{carrier_raw}_kWh'
                )

                prefix = f'{network_name}_{network_type}_'
                plant_files = [
                    os.path.join(folder, f) for f in os.listdir(folder)
                    if f.startswith(prefix) and f.endswith('.csv')
                ]
                hourly = np.zeros(8760)
                found = False
                for fpath in plant_files:
                    df = pd.read_csv(fpath)
                    if carrier_col in df.columns:
                        vals = df[carrier_col].values
                        if len(vals) == 8760:
                            hourly += vals
                            found = True
                if found:
                    key = f'District ({network_type})'
                    if key in result:
                        result[key] += hourly
                    else:
                        result[key] = hourly

    # ── Building-scale ─────────────────────────────────────────────────────
    if 'building' in scales:
        # Find (building, service_key, carrier) pairs for this component
        matches = []
        for building, bconfig in building_configs.items():
            if selected_buildings and building not in selected_buildings:
                continue
            for svc_key, col_prefix in _CONFIG_KEY_COL_PREFIX.items():
                svc_cfg = bconfig.get(svc_key)
                if not svc_cfg or not isinstance(svc_cfg, dict):
                    continue
                if svc_cfg.get('scale') != 'BUILDING':
                    continue
                component_code = svc_cfg.get('primary_component', '')
                if not component_code:
                    continue
                if _component_display(component_code) != component_display:
                    continue
                carrier = svc_cfg.get('carrier', '')
                matches.append((building, col_prefix, carrier))

        if matches:
            building_series = {}
            for building, col_prefix, carrier in matches:
                bfile = locator.get_final_energy_building_file(building, whatif_name)
                if not os.path.exists(bfile):
                    continue
                df = pd.read_csv(bfile)
                col = f'{col_prefix}_{carrier}_kWh' if carrier else None
                # Try exact carrier column, fall back to any matching column
                hourly = None
                if col and col in df.columns and len(df[col]) == 8760:
                    hourly = df[col].values.astype(float)
                else:
                    for c in df.columns:
                        if c.startswith(f'{col_prefix}_') and c.endswith('_kWh') and len(df[c]) == 8760:
                            if hourly is None:
                                hourly = df[c].values.astype(float)
                            else:
                                hourly += df[c].values.astype(float)
                if hourly is None:
                    continue
                if building in building_series:
                    building_series[building] += hourly
                else:
                    building_series[building] = hourly

            if building_series:
                if not selected_buildings:
                    # Aggregate into a single curve
                    total = np.zeros(8760)
                    for arr in building_series.values():
                        total += arr
                    result['All Buildings'] = total
                else:
                    result.update(building_series)

    return result


# ── figure builder ────────────────────────────────────────────────────────────

def build_ldc_fig(component_display, data_by_whatif, unit, unit_divisor):
    """
    Build a load duration curve figure for one component.

    Parameters
    ----------
    component_display : str
        Human-readable component label used as the plot title.
    data_by_whatif : dict
        {whatif_name: {label: np.array(8760)}}
    unit : str
        Display unit string, e.g. 'kW' or 'MW'.
    unit_divisor : float
        Divisor applied to hourly kWh values.

    Returns
    -------
    go.Figure
    """
    fig = go.Figure()

    for wi_idx, (whatif_name, series_dict) in enumerate(data_by_whatif.items()):
        colour = _WHATIF_COLOURS[wi_idx % len(_WHATIF_COLOURS)]
        for label, hourly in series_dict.items():
            sorted_vals = np.sort(hourly)[::-1] / unit_divisor
            x = np.linspace(0, 100, len(sorted_vals))
            if len(data_by_whatif) > 1 or len(series_dict) > 1:
                name = f"{whatif_name} \u2014 {label}"
            else:
                name = whatif_name
            fig.add_trace(go.Scatter(
                x=x,
                y=sorted_vals,
                mode='lines',
                name=name,
                fill='tozeroy',
                fillcolor=_to_rgba(colour),
                line=dict(color=colour, width=2),
                hovertemplate=(
                    f'Duration: %{{x:.1f}}%<br>Load: %{{y:,.1f}} {unit}'
                    f'<extra>{name}</extra>'
                ),
            ))

    fig.update_layout(
        title_text=f'Load Duration Curve \u2014 {component_display}',
        title_font_size=16,
        xaxis_title='Duration Normalised [%]',
        yaxis_title=f'Load [{unit}]',
        font_size=12,
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white'],
        margin=dict(l=60, r=20, t=60, b=60),
        legend=dict(orientation='v', x=1.02, xanchor='left'),
    )
    return fig


# ── main entry point ──────────────────────────────────────────────────────────

def main(config: cea.config.Configuration):
    locator = InputLocator(config.scenario)
    plot_config = config.plots_ldc_component

    what_if_names = plot_config.what_if_name
    scales = plot_config.scale
    components = plot_config.components
    selected_buildings = plot_config.buildings
    unit = plot_config.y_metric_unit
    unit_divisor = _UNIT_DIVISORS.get(unit, 1)

    if not what_if_names:
        print('No what-if scenario selected.')
        return None
    if not components:
        print('No components selected.')
        return None

    html_outputs = []

    for component_display in components:
        data_by_whatif = {}
        for whatif_name in what_if_names:
            try:
                series = load_component_hourly(
                    component_display, whatif_name, scales, selected_buildings, locator
                )
            except FileNotFoundError as exc:
                print(f'Skipping {whatif_name}: {exc}')
                continue
            if series:
                data_by_whatif[whatif_name] = series

        if not data_by_whatif:
            print(f'No data found for component: {component_display}')
            continue

        fig = build_ldc_fig(component_display, data_by_whatif, unit, unit_divisor)
        # include_plotlyjs only on first figure to avoid loading CDN multiple times
        include_js = 'cdn' if not html_outputs else False
        html_outputs.append(fig.to_html(full_html=False, include_plotlyjs=include_js))

    if not html_outputs:
        return None

    # Wrap all figure fragments in a single full HTML document
    body = '\n'.join(html_outputs)
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f'<body>{body}</body></html>'
    )


if __name__ == '__main__':
    main(cea.config.Configuration())
