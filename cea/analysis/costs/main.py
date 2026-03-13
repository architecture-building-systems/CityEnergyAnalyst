"""
System costs calculation based on final-energy results.

Reads supply configuration and final-energy results to calculate CAPEX and OPEX
for each building's energy service systems.

Data sources (sole source of truth):
- configuration.json: per-building supply configs (component, scale, efficiency, carrier)
- final_energy_buildings.csv: annual summary (carrier MWh, service MWh, peak kW)
- B####.csv hourly files: per-service peak demand and booster annual energy
- outputs/data/potentials/solar/*_total_buildings.csv: installed solar area
"""

import json
import os
from math import log, ceil

import pandas as pd

import cea.config
from cea.inputlocator import InputLocator
from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Carrier name → feedstock CSV file name mapping
CARRIER_TO_FEEDSTOCK = {
    'NATURALGAS': 'NATURALGAS',
    'OIL': 'OIL',
    'COAL': 'COAL',
    'WOOD': 'WOOD',
    'GRID': 'GRID',
}

# Component code prefix → COMPONENTS table name
# IMPORTANT: longer prefixes (PVT, HEX) must appear before shorter overlapping ones (PV)
COMPONENT_PREFIX_TO_TABLE = {
    'BO': 'BOILERS',
    'HP': 'HEAT_PUMPS',
    'CH': 'VAPOR_COMPRESSION_CHILLERS',
    'CT': 'COOLING_TOWERS',
    'AC': 'ABSORPTION_CHILLERS',
    'PU': 'HYDRAULIC_PUMPS',
    'HEX': 'HEAT_EXCHANGERS',
    'PVT': 'PHOTOVOLTAIC_THERMAL_PANELS',  # must be before 'PV'
    'PV': 'PHOTOVOLTAIC_PANELS',
    'SC': 'SOLAR_COLLECTORS',
}


def _get_component_row(component_code, locator, capacity_W=None):
    """Return the component row for the given code, selecting the correct capacity-range segment."""
    for prefix, table_name in COMPONENT_PREFIX_TO_TABLE.items():
        if component_code.upper().startswith(prefix):
            path = locator.get_db4_components_conversion_conversion_technology_csv(table_name)
            df = pd.read_csv(path)
            rows = df[df['code'] == component_code]
            if rows.empty:
                return None, table_name
            if capacity_W is None or len(rows) == 1:
                return rows.iloc[0], table_name
            # Select the piecewise segment that covers this capacity
            matching = rows[(rows['cap_min'] <= capacity_W) & (rows['cap_max'] > capacity_W)]
            if not matching.empty:
                return matching.iloc[0], table_name
            # Above all segments: use the last (highest-capacity) row
            return rows.iloc[-1], table_name
    raise ValueError(f"Unknown component code prefix: {component_code}")


def _calc_cost_curve(quantity, row):
    """
    Apply cost curve: InvC = a + b*Q^c + (d + e*Q)*ln(Q)

    :param quantity: Raw quantity in the component's native unit (W for thermal/PV/PVT, m² for SC)
    :param row: Component database row with a,b,c,d,e,cap_min,cap_max,IR_%,LT_yr,O&M_%
    :return: (capex_total_USD, capex_a_USD, opex_fixed_a_USD)
    """
    if quantity <= 0:
        return 0.0, 0.0, 0.0

    cap_min = row.get('cap_min', 1)
    cap_max = row.get('cap_max', float('inf'))
    if quantity < cap_min:
        quantity = cap_min

    if quantity <= cap_max:
        Q = quantity
        n_units = 1
    else:
        n_units = int(ceil(quantity / cap_max))
        Q = quantity / n_units

    a, b, c, d, e = row['a'], row['b'], row['c'], row['d'], row['e']
    IR_pct = row['IR_%']
    LT_yr = row['LT_yr']
    OM_frac = row['O&M_%'] / 100.0

    InvC_unit = a + b * Q ** c + (d + e * Q) * log(Q)
    InvC = InvC_unit * n_units

    capex_a = calc_capex_annualized(InvC, IR_pct, LT_yr)
    opex_fixed_a = InvC * OM_frac

    return InvC, capex_a, opex_fixed_a


def _calc_component_cost(component_code, capacity_kW, locator):
    """
    Calculate CAPEX and O&M for a component at a given capacity in kW.
    Converts kW to W before applying the cost curve.

    :return: (capex_total_USD, capex_a_USD, opex_fixed_a_USD)
    """
    Q_W = capacity_kW * 1000.0
    comp_row, _ = _get_component_row(component_code, locator, capacity_W=Q_W)
    if comp_row is None:
        raise ValueError(f"Component {component_code} not found in database")

    return _calc_cost_curve(Q_W, comp_row)


def _mean_feedstock_price(carrier, locator):
    """
    Return mean annual variable buy price (USD/kWh) for a carrier.
    Feedstock files have 24 hourly rows; take the mean.
    """
    feedstock_name = CARRIER_TO_FEEDSTOCK.get(carrier)
    if not feedstock_name:
        return 0.0
    path = locator.get_db4_components_feedstocks_feedstocks_csv(feedstock_name)
    if not os.path.exists(path):
        return 0.0
    df = pd.read_csv(path)
    if 'Opex_var_buy_USD2015kWh' not in df.columns:
        return 0.0
    return float(df['Opex_var_buy_USD2015kWh'].mean())


def _per_service_peaks_and_booster(building_name, whatif_name, supply_cfg, locator):
    """
    Read hourly final-energy file for a building.

    Returns:
    - peaks: dict with per-service peak kW for hs/ww/cs/E
    - booster_data: dict with per-booster-service (hs_booster/ww_booster) →
                    {peak_kW, annual_kWh, carrier}
    - service_mwh: dict with per-service annual carrier MWh for hs/ww/cs/E
                   (each value covers only that service's carrier columns, avoiding
                   double-counting when multiple services share the same carrier)
    """
    path = locator.get_final_energy_building_file(building_name, whatif_name)
    if not os.path.exists(path):
        return (
            {'hs': 0.0, 'ww': 0.0, 'cs': 0.0, 'E': 0.0},
            {},
            {'hs': 0.0, 'ww': 0.0, 'cs': 0.0, 'E': 0.0},
        )

    df = pd.read_csv(path)

    peaks = {
        'hs': float(df['Qhs_sys_kWh'].max()) if 'Qhs_sys_kWh' in df.columns else 0.0,
        'ww': float(df['Qww_sys_kWh'].max()) if 'Qww_sys_kWh' in df.columns else 0.0,
        'cs': float(df['Qcs_sys_kWh'].max()) if 'Qcs_sys_kWh' in df.columns else 0.0,
        'E': float(df['E_sys_kWh'].max()) if 'E_sys_kWh' in df.columns else 0.0,
    }

    # Per-service annual carrier MWh — sum only columns belonging to that service.
    # This avoids double-counting when e.g. both hs and ww use NATURALGAS.
    demand_cols = {'Qhs_sys_kWh', 'Qww_sys_kWh', 'Qcs_sys_kWh', 'E_sys_kWh'}
    service_mwh = {'hs': 0.0, 'ww': 0.0, 'cs': 0.0, 'E': 0.0}
    for col in df.columns:
        if not col.endswith('_kWh') or col in demand_cols:
            continue
        if col.startswith('Qhs_sys_'):
            service_mwh['hs'] += float(df[col].sum()) / 1000.0
        elif col.startswith('Qww_sys_'):
            service_mwh['ww'] += float(df[col].sum()) / 1000.0
        elif col.startswith('Qcs_sys_'):
            service_mwh['cs'] += float(df[col].sum()) / 1000.0
        elif col.startswith('E_sys_'):
            service_mwh['E'] += float(df[col].sum()) / 1000.0

    booster_data = {}
    for booster_key, service_label in [('space_heating_booster', 'hs_booster'),
                                        ('hot_water_booster', 'ww_booster')]:
        booster_cfg = supply_cfg.get(booster_key)
        if not booster_cfg or not isinstance(booster_cfg, dict):
            continue
        if booster_cfg.get('scale') == 'NONE' or booster_cfg.get('scale') is None:
            continue
        carrier = booster_cfg.get('carrier')
        if not carrier:
            continue

        # Column name: Qhs_booster_{carrier}_kWh or Qww_booster_{carrier}_kWh
        prefix = 'Qhs' if 'heating' in booster_key else 'Qww'
        col = f'{prefix}_booster_{carrier}_kWh'
        if col in df.columns:
            peak_kW = float(df[col].max())
            annual_kWh = float(df[col].sum())
        else:
            peak_kW = 0.0
            annual_kWh = 0.0

        booster_data[service_label] = {
            'peak_kW': peak_kW,
            'annual_kWh': annual_kWh,
            'carrier': carrier,
            'component_code': booster_cfg.get('primary_component'),
            'efficiency': booster_cfg.get('efficiency', 1.0),
            'assembly_code': booster_cfg.get('assembly_code', ''),
        }

    return peaks, booster_data, service_mwh


def _process_building_service(building_name, service_label, supply_cfg_key, supply_cfg,
                               peak_kW, service_mwh, locator):
    """Compute costs for one building service (hs/ww/cs).

    :param service_mwh: Annual carrier MWh for this service only (not shared aggregate).
    """
    cfg = supply_cfg.get(supply_cfg_key)
    if not cfg or cfg.get('scale') == 'NONE':
        return None

    scale = cfg.get('scale', 'BUILDING')
    component_code = cfg.get('primary_component')
    efficiency = cfg.get('efficiency')
    carrier = cfg.get('carrier')
    assembly_code = cfg.get('assembly_code', '')

    if scale == 'DISTRICT':
        return {
            'name': building_name, 'service': service_label, 'scale': scale,
            'assembly_code': assembly_code, 'component_code': None,
            'carrier': carrier, 'peak_service_kW': peak_kW, 'capacity_kW': 0.0,
            'capex_total_USD': 0.0, 'capex_a_USD': 0.0,
            'opex_fixed_a_USD': 0.0, 'opex_var_a_USD': 0.0, 'TAC_USD': 0.0,
        }

    if not component_code or not efficiency or efficiency <= 0:
        return None

    capacity_kW = peak_kW / efficiency if peak_kW > 0 else 0.0

    try:
        capex_total, capex_a, opex_fixed_a = _calc_component_cost(
            component_code, capacity_kW, locator
        )
    except (ValueError, ZeroDivisionError) as e:
        print(f"    Warning: CAPEX calc failed for {building_name} {service_label} ({component_code}): {e}")
        capex_total, capex_a, opex_fixed_a = 0.0, 0.0, 0.0

    price = _mean_feedstock_price(carrier, locator) if carrier else 0.0
    opex_var_a = service_mwh * 1000.0 * price

    tac = capex_a + opex_fixed_a + opex_var_a
    return {
        'name': building_name, 'service': service_label, 'scale': scale,
        'assembly_code': assembly_code, 'component_code': component_code,
        'carrier': carrier, 'peak_service_kW': peak_kW, 'capacity_kW': capacity_kW,
        'capex_total_USD': capex_total, 'capex_a_USD': capex_a,
        'opex_fixed_a_USD': opex_fixed_a, 'opex_var_a_USD': opex_var_a, 'TAC_USD': tac,
    }


def _process_booster_services(building_name, booster_data, locator):
    """Compute costs for all booster services of a building."""
    rows = []
    for service_label, bd in booster_data.items():
        peak_kW = bd['peak_kW']
        annual_kWh = bd['annual_kWh']
        carrier = bd['carrier']
        component_code = bd['component_code']
        efficiency = bd['efficiency'] or 1.0
        assembly_code = bd['assembly_code']

        if not component_code or peak_kW <= 0:
            continue

        capacity_kW = peak_kW / efficiency

        try:
            capex_total, capex_a, opex_fixed_a = _calc_component_cost(
                component_code, capacity_kW, locator
            )
        except (ValueError, ZeroDivisionError) as e:
            print(f"    Warning: CAPEX calc failed for {building_name} {service_label} ({component_code}): {e}")
            capex_total, capex_a, opex_fixed_a = 0.0, 0.0, 0.0

        price = _mean_feedstock_price(carrier, locator)
        opex_var_a = annual_kWh * price  # kWh × USD/kWh = USD

        tac = capex_a + opex_fixed_a + opex_var_a
        rows.append({
            'name': building_name, 'service': service_label, 'scale': 'BUILDING',
            'assembly_code': assembly_code, 'component_code': component_code,
            'carrier': carrier, 'peak_service_kW': peak_kW, 'capacity_kW': capacity_kW,
            'capex_total_USD': capex_total, 'capex_a_USD': capex_a,
            'opex_fixed_a_USD': opex_fixed_a, 'opex_var_a_USD': opex_var_a, 'TAC_USD': tac,
        })
    return rows


def _process_electricity_service(building_name, supply_cfg, peak_kW, e_sys_mwh, locator):
    """Compute variable OPEX for electricity (grid connection — no CAPEX).

    :param e_sys_mwh: Annual MWh from E_sys_GRID_kWh only (plug loads, not cooling electricity).
    """
    cfg = supply_cfg.get('electricity')
    assembly_code = cfg.get('assembly_code', '') if cfg else ''
    price = _mean_feedstock_price('GRID', locator)
    opex_var_a = e_sys_mwh * 1000.0 * price
    return {
        'name': building_name, 'service': 'E', 'scale': 'BUILDING',
        'assembly_code': assembly_code, 'component_code': None,
        'carrier': 'GRID', 'peak_service_kW': peak_kW, 'capacity_kW': 0.0,
        'capex_total_USD': 0.0, 'capex_a_USD': 0.0,
        'opex_fixed_a_USD': 0.0, 'opex_var_a_USD': opex_var_a, 'TAC_USD': opex_var_a,
    }


def _process_plant_row(plant_row, plant_configs, whatif_name, network_name, locator):
    """Compute costs for a district plant from the summary row."""
    rows = []
    plant_name = plant_row['name']
    peak_kW = plant_row.get('peak_demand_kW', 0.0) or 0.0
    if peak_kW <= 0:
        return rows

    # Infer network type from case_description (set during final-energy from configuration.json)
    case_desc = plant_row.get('case_description', '') or ''
    if 'DH' in case_desc:
        network_type = 'DH'
    elif 'DC' in case_desc:
        network_type = 'DC'
    else:
        return rows

    # Load plant config from configuration.json (set during final-energy from district assembly)
    pc = plant_configs.get(network_type)
    if not pc:
        return rows

    component_code = pc.get('primary_component')
    efficiency = pc.get('efficiency')
    dominant_carrier = pc.get('carrier')
    assembly_code = pc.get('assembly_code', '')

    if not component_code or not efficiency or not dominant_carrier:
        return rows

    dominant_mwh = plant_row.get(f'{dominant_carrier}_MWh', 0.0) or 0.0
    capacity_kW = peak_kW / efficiency

    try:
        capex_total, capex_a, opex_fixed_a = _calc_component_cost(
            component_code, capacity_kW, locator
        )
    except (ValueError, ZeroDivisionError) as e:
        print(f"    Warning: CAPEX calc failed for plant {plant_name} ({component_code}): {e}")
        capex_total, capex_a, opex_fixed_a = 0.0, 0.0, 0.0

    price = _mean_feedstock_price(dominant_carrier, locator)
    opex_var_a = dominant_mwh * 1000.0 * price

    service_label = 'hs' if network_type == 'DH' else 'cs'
    tac = capex_a + opex_fixed_a + opex_var_a

    rows.append({
        'name': plant_name, 'service': service_label, 'scale': 'DISTRICT',
        'assembly_code': assembly_code, 'component_code': component_code,
        'carrier': dominant_carrier, 'peak_service_kW': peak_kW, 'capacity_kW': capacity_kW,
        'capex_total_USD': capex_total, 'capex_a_USD': capex_a,
        'opex_fixed_a_USD': opex_fixed_a, 'opex_var_a_USD': opex_var_a, 'TAC_USD': tac,
    })

    # Secondary and tertiary components: CAPEX + fixed O&M only (variable OPEX counted in primary)
    for comp_code in [pc.get('secondary_component'), pc.get('tertiary_component')]:
        if not comp_code:
            continue
        try:
            capex_total_s, capex_a_s, opex_fixed_a_s = _calc_component_cost(
                comp_code, capacity_kW, locator
            )
        except (ValueError, ZeroDivisionError) as e:
            print(f"    Warning: CAPEX calc failed for plant {plant_name} ({comp_code}): {e}")
            capex_total_s, capex_a_s, opex_fixed_a_s = 0.0, 0.0, 0.0
        tac_s = capex_a_s + opex_fixed_a_s
        rows.append({
            'name': plant_name, 'service': service_label, 'scale': 'DISTRICT',
            'assembly_code': assembly_code, 'component_code': comp_code,
            'carrier': None, 'peak_service_kW': peak_kW, 'capacity_kW': capacity_kW,
            'capex_total_USD': capex_total_s, 'capex_a_USD': capex_a_s,
            'opex_fixed_a_USD': opex_fixed_a_s, 'opex_var_a_USD': 0.0, 'TAC_USD': tac_s,
        })

    # Network pumping: CAPEX (PU1) + OPEX (GRID electricity)
    # Get peak pumping kW from the plant hourly file
    peak_pumping_kW = 0.0
    if network_name:
        plant_file = locator.get_final_energy_plant_file(
            network_name, network_type, plant_name, whatif_name
        )
        if os.path.exists(plant_file):
            try:
                plant_df = pd.read_csv(plant_file)
                if 'pumping_load_kWh' in plant_df.columns:
                    peak_pumping_kW = float(plant_df['pumping_load_kWh'].max())
            except Exception:
                pass

    if peak_pumping_kW > 0:
        try:
            capex_pu, capex_a_pu, opex_fixed_pu = _calc_component_cost('PU1', peak_pumping_kW, locator)
        except (ValueError, ZeroDivisionError) as e:
            print(f"    Warning: CAPEX calc failed for plant {plant_name} pump (PU1): {e}")
            capex_pu, capex_a_pu, opex_fixed_pu = 0.0, 0.0, 0.0

        # OPEX for pumping electricity (GRID) — only when primary carrier is not GRID,
        # since DC plants already bundle pumping into GRID_MWh with the chiller electricity.
        if dominant_carrier != 'GRID':
            grid_mwh = plant_row.get('GRID_MWh', 0.0) or 0.0
            grid_price = _mean_feedstock_price('GRID', locator)
            pumping_opex = grid_mwh * 1000.0 * grid_price
        else:
            pumping_opex = 0.0

        tac_pu = capex_a_pu + opex_fixed_pu + pumping_opex
        rows.append({
            'name': plant_name, 'service': f'{service_label}_pumping', 'scale': 'DISTRICT',
            'assembly_code': assembly_code, 'component_code': 'PU1',
            'carrier': 'GRID', 'peak_service_kW': peak_pumping_kW, 'capacity_kW': peak_pumping_kW,
            'capex_total_USD': capex_pu, 'capex_a_USD': capex_a_pu,
            'opex_fixed_a_USD': opex_fixed_pu, 'opex_var_a_USD': pumping_opex, 'TAC_USD': tac_pu,
        })

    # Network piping: CAPEX from THERMAL_GRID.csv unit costs × pipe lengths
    # No OPEX for pipes; annualised with infrastructure defaults (LT=40yr, IR=5%)
    if network_name:
        edges_file = locator.get_thermal_network_edge_list_file(network_type, network_name)
        if os.path.exists(edges_file):
            try:
                edges_df = pd.read_csv(edges_file)
                grid_path = locator.get_database_components_distribution_thermal_grid()
                grid_df = pd.read_csv(grid_path)
                unit_cost = {row['pipe_DN']: row['Inv_USD2015perm'] for _, row in grid_df.iterrows()}

                total_length_m = 0.0
                capex_pipes = 0.0
                for _, edge in edges_df.iterrows():
                    dn = edge['pipe_DN']
                    length_m = edge['length_m']
                    capex_pipes += unit_cost.get(dn, 0.0) * length_m
                    total_length_m += length_m

                if capex_pipes > 0:
                    capex_a_pipes = calc_capex_annualized(capex_pipes, 5.0, 40)
                    rows.append({
                        'name': plant_name, 'service': f'{service_label}_piping', 'scale': 'DISTRICT',
                        'assembly_code': assembly_code, 'component_code': 'PIPES',
                        'carrier': None, 'peak_service_kW': 0.0, 'capacity_kW': total_length_m,
                        'capex_total_USD': capex_pipes, 'capex_a_USD': capex_a_pipes,
                        'opex_fixed_a_USD': 0.0, 'opex_var_a_USD': 0.0, 'TAC_USD': capex_a_pipes,
                    })
            except Exception as e:
                print(f"    Warning: Piping cost calc failed for {plant_name}: {e}")

    return rows


def _calc_solar_costs_for_scenario(locator, active_tech_codes):
    """
    Calculate CAPEX and O&M for solar panels (PV, SC, PVT) installed on buildings.

    Scans potentials/solar/ folder for total_buildings files, restricted to the
    technology codes recorded in configuration.json['solar'].
    Solar has CAPEX and fixed O&M only (variable OPEX = 0, fuel is free).

    :param locator: InputLocator instance
    :param active_tech_codes: set of tech code strings from configuration.json['solar']
        e.g. {'PV_PV1', 'SC_ET'}.  Empty set → skip solar entirely.
    :return: list of component row dicts, one per building per technology
    """
    if not active_tech_codes:
        return []

    solar_folder = locator.get_potentials_solar_folder()
    if not os.path.exists(solar_folder):
        return []

    component_rows = []

    # Scan for PV, SC, PVT total_buildings files
    for fname in os.listdir(solar_folder):
        if not fname.endswith('_total_buildings.csv'):
            continue

        # Derive tech code from filename and skip if not in active set
        tech_code = fname[: fname.index('_total_buildings')]
        if tech_code not in active_tech_codes:
            continue

        fpath = os.path.join(solar_folder, fname)
        try:
            df = pd.read_csv(fpath)
        except Exception:
            continue

        if 'name' not in df.columns:
            continue

        if fname.startswith('PV_') and not fname.startswith('PVT_'):
            # PV_{panel_type}_total_buildings.csv
            panel_type = fname[3:fname.index('_total_buildings')]
            comp_rows = _solar_pv_costs(df, panel_type, 'PV', locator)
            component_rows.extend(comp_rows)

        elif fname.startswith('SC_'):
            # SC_{panel_type}_total_buildings.csv
            panel_type = fname[3:fname.index('_total_buildings')]
            comp_rows = _solar_sc_costs(df, panel_type, locator)
            component_rows.extend(comp_rows)

        elif fname.startswith('PVT_'):
            # PVT_{pv}_{sc}_total_buildings.csv  (e.g., PVT_PV1_FP or PVT_PV1_ET)
            suffix = fname[4:fname.index('_total_buildings')]
            parts = suffix.split('_', 1)
            pv_type = parts[0] if parts else 'PV1'
            sc_type = parts[1] if len(parts) > 1 else ''
            comp_rows = _solar_pvt_costs(df, pv_type, sc_type, locator)
            component_rows.extend(comp_rows)

    return component_rows


def _solar_pv_costs(df, panel_type, service_prefix, locator):
    """Calculate PV panel costs from total_buildings DataFrame."""
    rows = []
    if 'area_PV_m2' not in df.columns:
        return rows

    try:
        pv_db = pd.read_csv(
            locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS')
        )
        comp = pv_db[pv_db['code'] == panel_type]
        if comp.empty:
            # Fall back to first PV component
            comp = pv_db.head(1)
        comp = comp.iloc[0]
    except Exception:
        return rows

    # capacity_Wp and module_area_m2 allow converting area → peak power
    capacity_Wp = comp.get('capacity_Wp', 325.0)
    module_area_m2 = comp.get('module_area_m2', 1.76)
    wp_per_m2 = capacity_Wp / module_area_m2 if module_area_m2 > 0 else 185.0

    for _, brow in df.iterrows():
        building_name = brow['name']
        area_m2 = brow.get('area_PV_m2', 0.0) or 0.0
        if area_m2 <= 0:
            continue

        capacity_W = area_m2 * wp_per_m2
        try:
            capex_total, capex_a, opex_fixed_a = _calc_cost_curve(capacity_W, comp)
        except (ValueError, ZeroDivisionError):
            capex_total, capex_a, opex_fixed_a = 0.0, 0.0, 0.0

        tac = capex_a + opex_fixed_a
        rows.append({
            'name': building_name, 'service': f'PV_{panel_type}', 'scale': 'BUILDING',
            'assembly_code': '', 'component_code': comp['code'],
            'carrier': None, 'peak_service_kW': capacity_W / 1000.0,
            'capacity_kW': capacity_W / 1000.0,
            'capex_total_USD': capex_total, 'capex_a_USD': capex_a,
            'opex_fixed_a_USD': opex_fixed_a, 'opex_var_a_USD': 0.0, 'TAC_USD': tac,
        })
    return rows


def _solar_sc_costs(df, panel_type, locator):
    """Calculate solar collector costs from total_buildings DataFrame."""
    rows = []
    if 'area_SC_m2' not in df.columns:
        return rows

    try:
        sc_db = pd.read_csv(
            locator.get_db4_components_conversion_conversion_technology_csv('SOLAR_COLLECTORS')
        )
        # Match by type field (e.g., 'ET' or 'FP')
        comp = sc_db[sc_db['type'] == panel_type]
        if comp.empty:
            comp = sc_db.head(1)
        comp = comp.iloc[0]
    except Exception:
        return rows

    for _, brow in df.iterrows():
        building_name = brow['name']
        area_m2 = brow.get('area_SC_m2', 0.0) or 0.0
        if area_m2 <= 0:
            continue

        # SC cost curve uses m² directly (unit = 'm2')
        try:
            capex_total, capex_a, opex_fixed_a = _calc_cost_curve(area_m2, comp)
        except (ValueError, ZeroDivisionError):
            capex_total, capex_a, opex_fixed_a = 0.0, 0.0, 0.0

        tac = capex_a + opex_fixed_a
        rows.append({
            'name': building_name, 'service': f'SC_{panel_type}', 'scale': 'BUILDING',
            'assembly_code': '', 'component_code': comp['code'],
            'carrier': None, 'peak_service_kW': 0.0,
            'capacity_kW': area_m2,  # stored as m² for SC
            'capex_total_USD': capex_total, 'capex_a_USD': capex_a,
            'opex_fixed_a_USD': opex_fixed_a, 'opex_var_a_USD': 0.0, 'TAC_USD': tac,
        })
    return rows


def _solar_pvt_costs(df, pv_type, sc_type, locator):
    """Calculate PVT panel costs from total_buildings DataFrame."""
    rows = []
    if 'area_PVT_m2' not in df.columns:
        return rows

    try:
        pvt_db = pd.read_csv(
            locator.get_db4_components_conversion_conversion_technology_csv(
                'PHOTOVOLTAIC_THERMAL_PANELS'
            )
        )
        comp_rows = pvt_db[pvt_db['code'] == pv_type]
        if comp_rows.empty:
            comp_rows = pvt_db.head(1)
        comp = comp_rows.iloc[0]
    except Exception:
        return rows

    # Use PV component to get Wp/m² ratio for area → W conversion
    try:
        pv_db = pd.read_csv(
            locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS')
        )
        pv_comp = pv_db[pv_db['code'] == pv_type]
        if pv_comp.empty:
            pv_comp = pv_db.head(1)
        pv_comp = pv_comp.iloc[0]
        capacity_Wp = pv_comp.get('capacity_Wp', 325.0)
        module_area_m2 = pv_comp.get('module_area_m2', 1.76)
        wp_per_m2 = capacity_Wp / module_area_m2 if module_area_m2 > 0 else 185.0
    except Exception:
        wp_per_m2 = 185.0

    for _, brow in df.iterrows():
        building_name = brow['name']
        area_m2 = brow.get('area_PVT_m2', 0.0) or 0.0
        if area_m2 <= 0:
            continue

        capacity_W = area_m2 * wp_per_m2
        try:
            capex_total, capex_a, opex_fixed_a = _calc_cost_curve(capacity_W, comp)
        except (ValueError, ZeroDivisionError):
            capex_total, capex_a, opex_fixed_a = 0.0, 0.0, 0.0

        service_label = f'PVT_{pv_type}_{sc_type}' if sc_type else f'PVT_{pv_type}'
        tac = capex_a + opex_fixed_a
        rows.append({
            'name': building_name, 'service': service_label, 'scale': 'BUILDING',
            'assembly_code': '', 'component_code': comp['code'],
            'carrier': None, 'peak_service_kW': capacity_W / 1000.0,
            'capacity_kW': capacity_W / 1000.0,
            'capex_total_USD': capex_total, 'capex_a_USD': capex_a,
            'opex_fixed_a_USD': opex_fixed_a, 'opex_var_a_USD': 0.0, 'TAC_USD': tac,
        })
    return rows


def calculate_costs_for_whatif(whatif_name, locator):
    """
    Calculate CAPEX and OPEX for all buildings and plants in a what-if scenario.

    :param whatif_name: What-if scenario name
    :param locator: InputLocator instance
    :return: (buildings_df, components_df) DataFrames
    """
    config_file = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"configuration.json not found for what-if '{whatif_name}': {config_file}\n"
            "Please run 'final-energy' first."
        )
    with open(config_file) as f:
        config_data = json.load(f)
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

        peaks, booster_data, service_mwh = _per_service_peaks_and_booster(
            building_name, whatif_name, supply_cfg, locator
        )

        # Space heating
        r = _process_building_service(
            building_name, 'hs', 'space_heating', supply_cfg,
            peaks['hs'], service_mwh['hs'], locator
        )
        if r:
            component_rows.append(r)

        # Hot water
        r = _process_building_service(
            building_name, 'ww', 'hot_water', supply_cfg,
            peaks['ww'], service_mwh['ww'], locator
        )
        if r:
            component_rows.append(r)

        # Space cooling
        r = _process_building_service(
            building_name, 'cs', 'space_cooling', supply_cfg,
            peaks['cs'], service_mwh['cs'], locator
        )
        if r:
            component_rows.append(r)

        # Booster systems
        component_rows.extend(_process_booster_services(building_name, booster_data, locator))

        # Electricity (variable OPEX only — E_sys only, not cooling GRID)
        if peaks['E'] > 0 or service_mwh['E'] > 0:
            r = _process_electricity_service(
                building_name, supply_cfg, peaks['E'], service_mwh['E'], locator
            )
            if r:
                component_rows.append(r)

    # --- Plant rows ---
    if 'type' in summary_df.columns:
        plant_rows_df = summary_df[summary_df['type'] == 'plant']
        for _, row in plant_rows_df.iterrows():
            component_rows.extend(_process_plant_row(row, plant_configs, whatif_name, network_name, locator))

    # --- Solar costs (only for technologies configured in this what-if) ---
    active_tech_codes = {
        v
        for cfg in building_configs.values()
        for v in cfg.get('solar', {}).values()
        if v
    }
    solar_rows = _calc_solar_costs_for_scenario(locator, active_tech_codes)
    component_rows.extend(solar_rows)

    # Build components DataFrame
    if not component_rows:
        components_df = pd.DataFrame(columns=[
            'name', 'service', 'scale', 'assembly_code', 'component_code',
            'carrier', 'peak_service_kW', 'capacity_kW',
            'capex_total_USD', 'capex_a_USD', 'opex_fixed_a_USD', 'opex_var_a_USD', 'TAC_USD'
        ])
    else:
        components_df = pd.DataFrame(component_rows)

    # Aggregate to building-level summary
    if not components_df.empty:
        agg = components_df.groupby('name').agg(
            capex_total_USD=('capex_total_USD', 'sum'),
            capex_a_USD=('capex_a_USD', 'sum'),
            opex_fixed_a_USD=('opex_fixed_a_USD', 'sum'),
            opex_var_a_USD=('opex_var_a_USD', 'sum'),
            TAC_USD=('TAC_USD', 'sum'),
        ).reset_index()
    else:
        agg = pd.DataFrame(columns=['name', 'capex_total_USD', 'capex_a_USD',
                                     'opex_fixed_a_USD', 'opex_var_a_USD', 'TAC_USD'])

    meta_cols = [c for c in ['name', 'type', 'GFA_m2', 'x_coord', 'y_coord', 'scale']
                 if c in summary_df.columns]
    buildings_df = summary_df[meta_cols].merge(agg, on='name', how='left').fillna(0.0)
    buildings_df['whatif_name'] = whatif_name

    return buildings_df, components_df


def main(config: cea.config.Configuration):
    """
    Main entry point for system-costs script.

    :param config: Configuration instance
    """
    locator = InputLocator(config.scenario)

    whatif_names = config.what_ifs.what_if_name
    if not whatif_names:
        raise ValueError(
            "what-if-name is required. Please select at least one what-if scenario."
        )
    if isinstance(whatif_names, str):
        whatif_names = [whatif_names]

    print("=" * 80)
    print("SYSTEM COSTS CALCULATION")
    print("=" * 80)

    for whatif_name in whatif_names:
        print(f"\nProcessing what-if scenario: {whatif_name}")
        print("-" * 60)

        try:
            buildings_df, components_df = calculate_costs_for_whatif(whatif_name, locator)

            buildings_file = locator.get_costs_whatif_buildings_file(whatif_name)
            components_file = locator.get_costs_whatif_components_file(whatif_name)
            locator.ensure_parent_folder_exists(buildings_file)

            buildings_df.to_csv(buildings_file, index=False, float_format='%.2f')
            components_df.to_csv(components_file, index=False, float_format='%.2f')

            print(f"  Buildings processed: {len(buildings_df)}")
            print(f"  Component rows: {len(components_df)}")

            if not buildings_df.empty:
                total_capex_a = buildings_df['capex_a_USD'].sum()
                total_opex_var = buildings_df['opex_var_a_USD'].sum()
                total_tac = buildings_df['TAC_USD'].sum()
                print(f"  Total annualised CAPEX: {total_capex_a:,.0f} USD/yr")
                print(f"  Total variable OPEX:    {total_opex_var:,.0f} USD/yr")
                print(f"  Total TAC:              {total_tac:,.0f} USD/yr")

            print(f"  Saved: {buildings_file}")
            print(f"  Saved: {components_file}")

        except FileNotFoundError as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 80)
    print("SYSTEM COSTS CALCULATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main(cea.config.Configuration())
