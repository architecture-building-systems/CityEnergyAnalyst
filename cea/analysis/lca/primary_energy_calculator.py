"""
Primary Energy Calculator

Calculates primary energy consumption using Primary Energy Factors (PEF).

Primary Energy = Final Energy × PEF

Supports PV offsetting using net metering approach.
"""

import pandas as pd
from cea.analysis.lca.pv_offsetting import calculate_net_energy


def calculate_primary_energy(locator, building, config):
    """
    Calculate annual primary energy for a building.

    Parameters
    ----------
    locator : InputLocator
        File path resolver for scenario
    building : str
        Building name (e.g., "B001")
    config : Configuration
        CEA configuration with primary-energy section containing:
        - include_pv : bool
        - pv_codes : str (comma-separated, e.g., "PV1,PV2")
        - pef_grid : float (default: 2.5)
        - pef_naturalgas : float (default: 1.1)
        - pef_coal : float (default: 1.1)
        - pef_oil : float (default: 1.1)
        - pef_wood : float (default: 1.0)

        Note: DH and DC are excluded - their primary energy is calculated
        separately in thermal network and district optimization features.

    Returns
    -------
    dict
        Dictionary with primary energy results:
        {
            'building': str,
            'FE_GRID_MJyr': float,
            'FE_NATURALGAS_MJyr': float,
            'FE_COAL_MJyr': float,
            'FE_OIL_MJyr': float,
            'FE_WOOD_MJyr': float,
            'PE_GRID_MJyr': float,
            'PE_NATURALGAS_MJyr': float,
            'PE_COAL_MJyr': float,
            'PE_OIL_MJyr': float,
            'PE_WOOD_MJyr': float,
            'NetGRID_{pv_code}_MJyr': float,      # Net grid after PV offset (per panel)
            'PE_NetGRID_{pv_code}_MJyr': float,   # Primary energy of net grid (per panel)
            'PV_{pv_code}_generation_MJyr': float, # PV generation (per panel)
            'GFA_m2': float                        # For normalisation
        }
    """
    # Parse PV codes from config
    include_pv = config.primary_energy.include_pv
    pv_codes_param = config.primary_energy.pv_codes

    # Handle both string (CLI) and list (GUI) input
    if isinstance(pv_codes_param, list):
        pv_codes = pv_codes_param if pv_codes_param else None
    elif isinstance(pv_codes_param, str):
        pv_codes = [code.strip() for code in pv_codes_param.split(',')] if pv_codes_param else None
    else:
        pv_codes = None

    # Get PEF values from config
    # Note: DH and DC excluded - calculated in district optimization
    pef = {
        'GRID': config.primary_energy.pef_grid,
        'NATURALGAS': config.primary_energy.pef_naturalgas,
        'COAL': config.primary_energy.pef_coal,
        'OIL': config.primary_energy.pef_oil,
        'WOOD': config.primary_energy.pef_wood,
    }

    # Calculate net energy using shared utility
    net_energy = calculate_net_energy(locator, building, include_pv, pv_codes)

    # Convert kWh to MJ (1 kWh = 3.6 MJ)
    kWh_to_MJ = 3.6

    # Extract final energy (FE) in MJ
    # Note: DH and DC excluded - their primary energy calculated in district optimization
    fe = {
        'GRID': net_energy['FE_GRID_kWh'] * kWh_to_MJ,
        'NATURALGAS': net_energy['FE_NATURALGAS_kWh'] * kWh_to_MJ,
        'COAL': net_energy['FE_COAL_kWh'] * kWh_to_MJ,
        'OIL': net_energy['FE_OIL_kWh'] * kWh_to_MJ,
        'WOOD': net_energy['FE_WOOD_kWh'] * kWh_to_MJ,
    }

    # Calculate primary energy (PE) in MJ
    pe = {
        carrier: fe[carrier] * pef[carrier]
        for carrier in fe.keys()
    }

    # Get GFA for normalisation
    demand_path = locator.get_demand_results_file(building)
    demand_df = pd.read_csv(demand_path)
    gfa_m2 = demand_df['GFA_m2'].iloc[0] if 'GFA_m2' in demand_df.columns else 0.0

    # Build base results
    results = {
        'building': building,
        'FE_GRID_MJyr': fe['GRID'],
        'FE_NATURALGAS_MJyr': fe['NATURALGAS'],
        'FE_COAL_MJyr': fe['COAL'],
        'FE_OIL_MJyr': fe['OIL'],
        'FE_WOOD_MJyr': fe['WOOD'],
        'PE_GRID_MJyr': pe['GRID'],
        'PE_NATURALGAS_MJyr': pe['NATURALGAS'],
        'PE_COAL_MJyr': pe['COAL'],
        'PE_OIL_MJyr': pe['OIL'],
        'PE_WOOD_MJyr': pe['WOOD'],
        'GFA_m2': gfa_m2
    }

    # Add per-panel NetGRID columns if PV is included
    pv_per_panel = net_energy.get('PV_per_panel', {})
    for pv_code, pv_generation_kWh in pv_per_panel.items():
        pv_generation_MJ = pv_generation_kWh * kWh_to_MJ
        net_grid_MJ = fe['GRID'] - pv_generation_MJ
        pe_net_grid_MJ = net_grid_MJ * pef['GRID']

        results[f'NetGRID_{pv_code}_MJyr'] = net_grid_MJ
        results[f'PE_NetGRID_{pv_code}_MJyr'] = pe_net_grid_MJ
        results[f'PV_{pv_code}_generation_MJyr'] = pv_generation_MJ

    return results


def calculate_normalized_metrics(building_results):
    """
    Add normalised metrics (per m²) to building results.

    Parameters
    ----------
    building_results : dict
        Results from calculate_primary_energy()

    Returns
    -------
    dict
        Same dict with added normalised columns:
        - FE_GRID_MJm2yr
        - PE_GRID_MJm2yr
        - NetGRID_{pv_code}_MJm2yr (per panel)
        - etc.
    """
    gfa_m2 = building_results['GFA_m2']

    if gfa_m2 == 0:
        # Avoid division by zero
        return building_results

    # Add normalised metrics
    normalized = building_results.copy()

    # Normalize base carriers
    for carrier in ['GRID', 'NATURALGAS', 'COAL', 'OIL', 'WOOD']:
        normalized[f'FE_{carrier}_MJm2yr'] = building_results[f'FE_{carrier}_MJyr'] / gfa_m2
        normalized[f'PE_{carrier}_MJm2yr'] = building_results[f'PE_{carrier}_MJyr'] / gfa_m2

    # Normalize per-panel NetGRID columns
    for key in building_results.keys():
        if key.startswith('NetGRID_') and key.endswith('_MJyr'):
            pv_code = key.replace('NetGRID_', '').replace('_MJyr', '')
            normalized[f'NetGRID_{pv_code}_MJm2yr'] = building_results[key] / gfa_m2
            normalized[f'PE_NetGRID_{pv_code}_MJm2yr'] = building_results[f'PE_NetGRID_{pv_code}_MJyr'] / gfa_m2
            normalized[f'PV_{pv_code}_generation_MJm2yr'] = building_results[f'PV_{pv_code}_generation_MJyr'] / gfa_m2

    return normalized
