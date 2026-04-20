"""
Heat rejection calculation based on final-energy results.

Reads supply configuration and final-energy results to calculate heat rejection
to the environment for each building's energy service systems.

Data sources (sole source of truth):
- configuration.json: per-building supply configs (component, scale, efficiency, carrier)
- final_energy_buildings.csv: annual summary and metadata
- B####.csv hourly files: per-service carrier flows
- Plant hourly files: thermal load and carrier flows for district plants
"""

import os

import pandas as pd

from cea.technologies.cooling_tower import calc_CT_const

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

FUEL_CARRIERS = {'NATURALGAS', 'OIL', 'COAL', 'WOOD'}


def _get_ct_aux_power(tertiary_component, locator):
    """
    Look up the auxiliary power ratio for a cooling tower component from the database.

    :param tertiary_component: CT component code (e.g. 'CT1'), or None
    :param locator: InputLocator
    :return: aux_power ratio (float) or None if component not found
    """
    if not tertiary_component:
        return None
    path = locator.get_db4_components_conversion_conversion_technology_csv('COOLING_TOWERS')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    rows = df[df['code'] == tertiary_component]
    if rows.empty:
        return None
    return float(rows.iloc[0]['aux_power'])


def _calc_building_heat_rejection(building_name, whatif_name, supply_cfg, locator):
    """
    Calculate hourly heat rejection for a single building.

    Reads the building's hourly final-energy file and applies technology-based
    heat rejection formulae for each carrier column:
    - Fuel carriers (hs/ww): losses = fuel_kWh - demand_kWh
    - Grid cooling (cs): condenser heat → cooling tower rejection
    - Fuel boosters: losses = col_kWh × (1 − efficiency)
    - Grid/DH/DC: zero heat rejection at building level

    :param building_name: Building identifier (e.g. 'B1001')
    :param whatif_name: What-if scenario name
    :param supply_cfg: Supply configuration dict for this building from configuration.json
    :param locator: InputLocator
    :return: (hr_series, component_rows, date_series) where hr_series is hourly kWh Series,
             component_rows is a list of dicts for heat_rejection_components.csv,
             date_series is the date column from the source file
    """
    path = locator.get_final_energy_building_file(building_name, whatif_name)
    if not os.path.exists(path):
        return pd.Series(dtype=float), [], pd.Series(dtype=str)

    df = pd.read_csv(path)

    demand_cols = {'Qhs_sys_kWh', 'Qww_sys_kWh', 'Qcs_sys_kWh', 'E_sys_kWh'}
    hs_demand = df['Qhs_sys_kWh'] if 'Qhs_sys_kWh' in df.columns else pd.Series(0.0, index=df.index)
    ww_demand = df['Qww_sys_kWh'] if 'Qww_sys_kWh' in df.columns else pd.Series(0.0, index=df.index)
    cs_demand = df['Qcs_sys_kWh'] if 'Qcs_sys_kWh' in df.columns else pd.Series(0.0, index=df.index)

    # Per-service rejection accumulators
    hs_hr = pd.Series(0.0, index=df.index)
    ww_hr = pd.Series(0.0, index=df.index)
    cs_hr = pd.Series(0.0, index=df.index)
    hs_booster_hr = pd.Series(0.0, index=df.index)
    ww_booster_hr = pd.Series(0.0, index=df.index)

    cs_cfg = supply_cfg.get('space_cooling') or {}
    ct_aux_power = _get_ct_aux_power(cs_cfg.get('tertiary_component'), locator)

    hs_booster_cfg = supply_cfg.get('space_heating_booster') or {}
    ww_booster_cfg = supply_cfg.get('hot_water_booster') or {}

    for col in df.columns:
        if not col.endswith('_kWh') or col in demand_cols:
            continue

        if col.startswith('Qhs_sys_'):
            carrier = col[len('Qhs_sys_'):-len('_kWh')]
            if carrier in FUEL_CARRIERS:
                # Boiler losses: fuel - demand (both in kWh)
                hs_hr = hs_hr + (df[col] - hs_demand).clip(lower=0)

        elif col.startswith('Qww_sys_'):
            carrier = col[len('Qww_sys_'):-len('_kWh')]
            if carrier in FUEL_CARRIERS:
                ww_hr = ww_hr + (df[col] - ww_demand).clip(lower=0)

        elif col.startswith('Qcs_sys_'):
            carrier = col[len('Qcs_sys_'):-len('_kWh')]
            if carrier == 'GRID':
                # Chiller condenser heat = cooling demand + electricity input
                q_cond = cs_demand + df[col]
                if ct_aux_power is not None:
                    # Cooling tower: q_anth = q_cond × (1 + aux_power)
                    _, q_anth = calc_CT_const(q_cond, ct_aux_power)
                else:
                    # No cooling tower: condenser heat directly to atmosphere
                    q_anth = q_cond
                cs_hr = cs_hr + q_anth.clip(lower=0)
            # DH/DC carriers: zero at building level (attributed to plant)

        elif col.startswith('Qhs_booster_'):
            carrier = col[len('Qhs_booster_'):-len('_kWh')]
            if carrier in FUEL_CARRIERS:
                eff = hs_booster_cfg.get('efficiency', 1.0) or 1.0
                # Booster losses: col_kWh × (1 − η)
                hs_booster_hr = hs_booster_hr + (df[col] * (1.0 - eff)).clip(lower=0)
            # GRID booster: electric, no exhaust heat

        elif col.startswith('Qww_booster_'):
            carrier = col[len('Qww_booster_'):-len('_kWh')]
            if carrier in FUEL_CARRIERS:
                eff = ww_booster_cfg.get('efficiency', 1.0) or 1.0
                ww_booster_hr = ww_booster_hr + (df[col] * (1.0 - eff)).clip(lower=0)

    hr_series = hs_hr + ww_hr + cs_hr + hs_booster_hr + ww_booster_hr

    # Build component rows per service
    hs_cfg = supply_cfg.get('space_heating') or {}
    ww_cfg = supply_cfg.get('hot_water') or {}

    component_rows = []
    for service, svc_hr, cfg in [
        ('hs', hs_hr, hs_cfg),
        ('ww', ww_hr, ww_cfg),
        ('cs', cs_hr, cs_cfg),
        ('hs_booster', hs_booster_hr, hs_booster_cfg),
        ('ww_booster', ww_booster_hr, ww_booster_cfg),
    ]:
        if svc_hr.sum() <= 0:
            continue
        component_rows.append({
            'name': building_name,
            'service': service,
            'scale': cfg.get('scale', 'BUILDING'),
            'assembly_code': cfg.get('assembly_code', ''),
            'component_code': cfg.get('primary_component', ''),
            'carrier': cfg.get('carrier', ''),
            'peak_heat_rejection_kW': float(svc_hr.max()),
            'heat_rejection_annual_MWh': float(svc_hr.sum()) / 1000.0,
        })

    date_series = df['date'] if 'date' in df.columns else pd.Series(dtype=str)
    return hr_series, component_rows, date_series


def _calc_plant_heat_rejection(plant_row, plant_configs, whatif_name, network_name, locator):
    """
    Calculate hourly heat rejection for a district plant.

    For DH plants (boiler): losses = fuel_kWh - thermal_load_kWh
    For DC plants (chiller+CT): q_cond = thermal_load + grid_electricity → cooling tower

    :param plant_row: Row from final_energy_buildings.csv for this plant (pandas Series)
    :param plant_configs: Dict of plant configs from configuration.json (keyed by plant name or network type)
    :param whatif_name: What-if scenario name
    :param network_name: District network name from metadata
    :param locator: InputLocator
    :return: (hr_series, component_rows, date_series)
    """
    plant_name = plant_row['name']
    case_desc = plant_row.get('case_description', '') or ''

    if 'DH' in case_desc:
        network_type = 'DH'
    elif 'DC' in case_desc:
        network_type = 'DC'
    else:
        return pd.Series(dtype=float), [], pd.Series(dtype=str)

    # Plant configs may be keyed by plant name (e.g. 'NODE16') or by network type ('DH'/'DC')
    pc = plant_configs.get(plant_name) or plant_configs.get(network_type)
    if not pc:
        return pd.Series(dtype=float), [], pd.Series(dtype=str)

    if not network_name:
        return pd.Series(dtype=float), [], pd.Series(dtype=str)

    plant_file = locator.get_final_energy_plant_file(network_name, network_type, plant_name, whatif_name)
    if not os.path.exists(plant_file):
        return pd.Series(dtype=float), [], pd.Series(dtype=str)

    plant_df = pd.read_csv(plant_file)

    carrier = pc.get('carrier', '')
    assembly_code = pc.get('assembly_code', '')
    component_code = pc.get('primary_component', '')

    thermal_load = (
        plant_df['thermal_load_kWh']
        if 'thermal_load_kWh' in plant_df.columns
        else pd.Series(0.0, index=plant_df.index)
    )

    hr_series = pd.Series(0.0, index=plant_df.index)

    if network_type == 'DH':
        if carrier in FUEL_CARRIERS:
            fuel_col = f'plant_primary_{network_type}_{carrier}_kWh'
            if fuel_col in plant_df.columns:
                hr_series = (plant_df[fuel_col] - thermal_load).clip(lower=0)
        # GRID carrier (HP): hr = 0

    elif network_type == 'DC':
        # Read primary (chiller) electricity
        primary_col = f'plant_primary_{network_type}_{carrier}_kWh'
        if primary_col in plant_df.columns:
            q_cond = thermal_load + plant_df[primary_col]
            # Add tertiary (CT fan) electricity if stored separately
            tertiary_cols = [c for c in plant_df.columns if c.startswith(f'plant_tertiary_{network_type}_')]
            for tc in tertiary_cols:
                q_cond = q_cond + plant_df[tc]
            ct_code = pc.get('tertiary_component')
            ct_aux_power = _get_ct_aux_power(ct_code, locator)
            if ct_aux_power is not None:
                _, q_anth = calc_CT_const(q_cond, ct_aux_power)
            else:
                q_anth = q_cond
            hr_series = q_anth.clip(lower=0)

    service_label = 'hs' if network_type == 'DH' else 'cs'
    component_rows = []
    if hr_series.sum() > 0:
        component_rows.append({
            'name': plant_name,
            'service': service_label,
            'scale': 'DISTRICT',
            'assembly_code': assembly_code,
            'component_code': component_code,
            'carrier': carrier,
            'peak_heat_rejection_kW': float(hr_series.max()),
            'heat_rejection_annual_MWh': float(hr_series.sum()) / 1000.0,
        })

    date_series = plant_df['date'] if 'date' in plant_df.columns else pd.Series(dtype=str)
    return hr_series, component_rows, date_series


def calculate_heat_rejection_for_whatif(whatif_name, locator):
    """
    Calculate heat rejection for all buildings and plants in a what-if scenario.

    :param whatif_name: What-if scenario name
    :param locator: InputLocator
    :return: (buildings_df, components_df) DataFrames
    """
    config_data = locator.read_analysis_configuration(whatif_name)
    if config_data is None:
        expected = locator.get_analysis_configuration_file(whatif_name)
        raise FileNotFoundError(
            f"configuration file not found for what-if '{whatif_name}': {expected}\n"
            "Please run 'final-energy' first."
        )
    building_configs = config_data.get('buildings', {})
    plant_configs = config_data.get('plants', {})
    network_name = config_data.get('metadata', {}).get('network_name')

    summary_file = locator.get_final_energy_buildings_file(whatif_name)
    if not os.path.exists(summary_file):
        raise FileNotFoundError(
            f"final_energy_buildings.csv not found for what-if '{whatif_name}': {summary_file}\n"
            "Please run 'final-energy' first."
        )
    summary_df = pd.read_csv(summary_file)

    component_rows = []

    # --- Building rows ---
    building_rows_df = summary_df[summary_df['type'] == 'building']
    for _, row in building_rows_df.iterrows():
        building_name = row['name']
        supply_cfg = building_configs.get(building_name, {})

        hr_series, comp_rows, date_series = _calc_building_heat_rejection(
            building_name, whatif_name, supply_cfg, locator
        )
        component_rows.extend(comp_rows)

        if not hr_series.empty:
            out_data = {'date': date_series.values, 'heat_rejection_kW': hr_series.values.clip(min=0)}
            out_df = pd.DataFrame(out_data)
            out_file = locator.get_heat_rejection_whatif_building_file(building_name, whatif_name)
            locator.ensure_parent_folder_exists(out_file)
            out_df.to_csv(out_file, index=False, float_format='%.4f')

    # --- Plant rows ---
    if 'type' in summary_df.columns:
        plant_rows_df = summary_df[summary_df['type'] == 'plant']
        for _, row in plant_rows_df.iterrows():
            plant_name = row['name']
            hr_series, comp_rows, date_series = _calc_plant_heat_rejection(
                row, plant_configs, whatif_name, network_name, locator
            )
            component_rows.extend(comp_rows)

            if not hr_series.empty:
                out_data = {'date': date_series.values, 'heat_rejection_kW': hr_series.values.clip(min=0)}
                out_df = pd.DataFrame(out_data)
                out_file = locator.get_heat_rejection_whatif_building_file(plant_name, whatif_name)
                locator.ensure_parent_folder_exists(out_file)
                out_df.to_csv(out_file, index=False, float_format='%.4f')

    # Build components DataFrame
    if not component_rows:
        components_df = pd.DataFrame(columns=[
            'name', 'service', 'scale', 'assembly_code', 'component_code',
            'carrier', 'peak_heat_rejection_kW', 'heat_rejection_annual_MWh',
        ])
    else:
        components_df = pd.DataFrame(component_rows)

    # Aggregate to building-level summary
    if not components_df.empty:
        agg = components_df.groupby('name').agg(
            heat_rejection_annual_MWh=('heat_rejection_annual_MWh', 'sum'),
            peak_heat_rejection_kW=('peak_heat_rejection_kW', 'max'),
        ).reset_index()
    else:
        agg = pd.DataFrame(columns=['name', 'heat_rejection_annual_MWh', 'peak_heat_rejection_kW'])

    meta_cols = [c for c in ['name', 'type', 'GFA_m2', 'x_coord', 'y_coord', 'scale', 'case', 'case_description']
                 if c in summary_df.columns]
    buildings_df = summary_df[meta_cols].merge(agg, on='name', how='left').fillna(0.0)
    buildings_df['whatif_name'] = whatif_name

    return buildings_df, components_df
