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
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import (
    COLOURS_TO_RGB,
    component_display as _component_display,
    component_tech_colour as _tech_colour,
)

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── colours ───────────────────────────────────────────────────────────────────

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

_BOOSTER_KEY_COL_PREFIX = {
    'space_heating_booster': 'Qhs_booster',
    'hot_water_booster':     'Qww_booster',
}


def _to_rgba(rgb_str, alpha=0.2):

    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# ── core data loading ─────────────────────────────────────────────────────────

def _load_config(locator, whatif_name):
    """Load the analysis configuration for a what-if scenario."""
    data = locator.read_analysis_configuration(whatif_name)
    if data is None:
        expected = locator.get_analysis_configuration_file(whatif_name)
        raise FileNotFoundError(f"Configuration file not found: {expected}")
    return data


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
    result = {}

    # ── District-scale ─────────────────────────────────────────────────────
    if 'district' in scales:
        network_names = _get_network_names_from_buildings(building_configs)

        if component_display == 'Pump':
            # Pump: sum plant_pumping_{NT}_GRID_kWh across all plant files
            hourly = np.zeros(8760)
            found = False
            for plant_name, plant_cfg in plant_configs.items():
                network_type = plant_cfg.get('network_type', '')
                network_name = network_names.get(network_type, '')
                if not network_type or not network_name:
                    continue
                plant_file = locator.get_final_energy_plant_file(
                    network_name, network_type, plant_name, whatif_name
                )
                if not os.path.exists(plant_file):
                    continue
                df = pd.read_csv(plant_file)
                for pc in [c for c in df.columns if c.startswith('plant_pumping_') and c.endswith('_GRID_kWh')]:
                    vals = df[pc].values
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
                if _component_display(component_code, locator) != component_display:
                    continue

                network_type = plant_cfg.get('network_type', '')
                carrier_raw = plant_cfg.get('carrier', 'GRID')
                network_name = network_names.get(network_type, '')
                if not network_type or not network_name:
                    continue

                carrier_col = f'plant_primary_{network_type}_{carrier_raw}_kWh'

                plant_file = locator.get_final_energy_plant_file(
                    network_name, network_type, plant_name, whatif_name
                )
                plant_files = [plant_file] if os.path.exists(plant_file) else []
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
                if _component_display(component_code, locator) != component_display:
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
                    total = np.zeros(8760)
                    for arr in building_series.values():
                        total += arr
                    result['All Buildings'] = total
                else:
                    result.update(building_series)

        # ── Booster components ────────────────────────────────────────────
        booster_matches = []
        for building, bconfig in building_configs.items():
            if selected_buildings and building not in selected_buildings:
                continue
            for bst_key, col_prefix in _BOOSTER_KEY_COL_PREFIX.items():
                bst_cfg = bconfig.get(bst_key)
                if not bst_cfg or not isinstance(bst_cfg, dict):
                    continue
                if bst_cfg.get('scale') != 'BUILDING':
                    continue
                component_code = bst_cfg.get('primary_component', '')
                if not component_code:
                    continue
                if _component_display(component_code, locator) != component_display:
                    continue
                carrier = bst_cfg.get('carrier', '')
                booster_matches.append((building, col_prefix, carrier))

        if booster_matches:
            booster_series = {}
            for building, col_prefix, carrier in booster_matches:
                bfile = locator.get_final_energy_building_file(building, whatif_name)
                if not os.path.exists(bfile):
                    continue
                df = pd.read_csv(bfile)
                col = f'{col_prefix}_{carrier}_kWh' if carrier else None
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
                label = f'{building} (booster)'
                if label in booster_series:
                    booster_series[label] += hourly
                else:
                    booster_series[label] = hourly

            if booster_series:
                if not selected_buildings:
                    total = np.zeros(8760)
                    for arr in booster_series.values():
                        total += arr
                    result['All Buildings (booster)'] = total
                else:
                    result.update(booster_series)

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

    multi_scenario = len(data_by_whatif) > 1
    for wi_idx, (whatif_name, series_dict) in enumerate(data_by_whatif.items()):
        for label, hourly in series_dict.items():
            sorted_vals = np.sort(hourly)[::-1] / unit_divisor
            x = np.linspace(0, 100, len(sorted_vals))
            if multi_scenario or len(series_dict) > 1:
                name = f"{whatif_name} \u2014 {label}"
            else:
                name = whatif_name
            if multi_scenario:
                colour = _WHATIF_COLOURS[wi_idx % len(_WHATIF_COLOURS)]
            else:
                colour = _tech_colour(component_display)
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
        title=dict(
            text=f'<b>Load Duration Curve \u2014 {component_display}</b>',
            x=0, xanchor='left', yanchor='top', font=dict(size=20),
        ),
        xaxis_title='Duration Normalised [%]',
        yaxis_title=f'Load [{unit}]',
        font_size=12,
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white'],
        margin=dict(l=60, r=20, t=60, b=120),
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.25,
            yanchor='top',
        ),
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
        # Auto-select all available components when none specified
        components = plot_config.parameters['components']._choices
        if not components:
            print('No components available for the selected what-if scenarios and scale.')
            return None
        print(f"No components specified — using all available: {components}")

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
        # Add subtitle with scenario and what-if names
        scenario_name = os.path.basename(config.scenario)
        whatif_label = ', '.join(what_if_names)
        subtitle = ' | '.join(['CEA-4 Load Duration Curve', scenario_name, whatif_label])
        fig.update_layout(title_text=f'<b>Load Duration Curve \u2014 {component_display}</b><br><sub>{subtitle}</sub>')
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
