"""
Shared utility for calculating net energy with PV offsetting.

Used by both:
- primary_energy module (Life Cycle Analysis)
- operational_emission module (Life Cycle Analysis)

Net metering approach: NetGRID = GRID_demand - PV_total
"""

import pandas as pd
from cea.demand import demand_writers


def calculate_net_energy(locator, building, include_pv=False, pv_codes=None):
    """
    Calculate final energy consumption with optional PV offsetting.

    This function implements net metering for grid electricity:
    - Reads building demand (final energy by carrier)
    - Optionally reads PV generation from selected panels
    - Calculates net grid electricity: NetGRID = GRID_demand - PV_total

    Parameters
    ----------
    locator : InputLocator
        File path resolver for scenario
    building : str
        Building name (e.g., "B001")
    include_pv : bool
        Whether to include PV offsetting (default: False)
    pv_codes : list[str] or None
        List of PV panel codes to include (e.g., ["PV1", "PV2"])
        If None and include_pv=True, includes all available panels

    Returns
    -------
    dict
        Dictionary with energy data:
        {
            'FE_GRID_kWh': float,           # Original grid demand (annual)
            'FE_NATURALGAS_kWh': float,     # Natural gas (annual)
            'FE_DH_kWh': float,             # District heating (annual)
            'FE_DC_kWh': float,             # District cooling (annual)
            'FE_COAL_kWh': float,           # Coal (annual)
            'FE_OIL_kWh': float,            # Oil (annual)
            'FE_WOOD_kWh': float,           # Wood (annual)
            'NetGRID_kWh': float,           # Net grid after PV offset (annual)
            'PV_generation_kWh': float,     # Total PV generation (annual)
            'PV_codes': list[str],          # List of included PV codes
            'hourly_data': pd.DataFrame     # Hourly timeseries (optional future use)
        }

    Notes
    -----
    - NetGRID can be negative (building as net exporter)
    - All non-GRID carriers pass through unchanged
    - Uses demand_energycarrier columns from building demand file
    """
    # Read building demand
    demand_path = locator.get_demand_results_file(building)
    demand_df = pd.read_csv(demand_path)

    # Extract final energy by carrier (kWh = Wh / 1000)
    # Use demand_energycarrier columns from demand output
    carriers = {
        'GRID': demand_df['GRID_kWh'].sum() if 'GRID_kWh' in demand_df.columns else 0.0,
        'NATURALGAS': demand_df['NG_hs_kWh'].sum() if 'NG_hs_kWh' in demand_df.columns else 0.0,
        'DH': demand_df['DH_hs_kWh'].sum() if 'DH_hs_kWh' in demand_df.columns else 0.0,
        'DC': demand_df['DC_cs_kWh'].sum() if 'DC_cs_kWh' in demand_df.columns else 0.0,
        'COAL': demand_df['COAL_hs_kWh'].sum() if 'COAL_hs_kWh' in demand_df.columns else 0.0,
        'OIL': demand_df['OIL_hs_kWh'].sum() if 'OIL_hs_kWh' in demand_df.columns else 0.0,
        'WOOD': demand_df['WOOD_hs_kWh'].sum() if 'WOOD_hs_kWh' in demand_df.columns else 0.0,
    }

    # Initialize PV offsetting
    pv_generation_total = 0.0
    included_pv_codes = []

    if include_pv:
        # Get available PV panels
        available_panels = _get_available_pv_panels(locator, building)

        # Determine which panels to include
        if pv_codes is None:
            # Include all available panels
            panels_to_include = available_panels
        else:
            # Include only requested panels that exist
            panels_to_include = [code for code in pv_codes if code in available_panels]

        # Sum PV generation from selected panels
        for pv_code in panels_to_include:
            pv_path = locator.PV_results(building, pv_code)
            try:
                pv_df = pd.read_csv(pv_path)
                # PV generation column: E_PV_gen_kWh
                if 'E_PV_gen_kWh' in pv_df.columns:
                    pv_generation = pv_df['E_PV_gen_kWh'].sum()
                    pv_generation_total += pv_generation
                    included_pv_codes.append(pv_code)
            except FileNotFoundError:
                # Panel file doesn't exist, skip
                continue

    # Calculate net grid electricity
    net_grid = carriers['GRID'] - pv_generation_total

    # Return results
    return {
        'FE_GRID_kWh': carriers['GRID'],
        'FE_NATURALGAS_kWh': carriers['NATURALGAS'],
        'FE_DH_kWh': carriers['DH'],
        'FE_DC_kWh': carriers['DC'],
        'FE_COAL_kWh': carriers['COAL'],
        'FE_OIL_kWh': carriers['OIL'],
        'FE_WOOD_kWh': carriers['WOOD'],
        'NetGRID_kWh': net_grid,
        'PV_generation_kWh': pv_generation_total,
        'PV_codes': included_pv_codes,
        'hourly_data': demand_df  # For potential future hourly analysis
    }


def _get_available_pv_panels(locator, building):
    """
    Get list of available PV panel codes for a building.

    Parameters
    ----------
    locator : InputLocator
        File path resolver
    building : str
        Building name

    Returns
    -------
    list[str]
        List of PV codes (e.g., ["PV1", "PV2"])
    """
    import os

<<<<<<< Updated upstream
    pv_folder = locator.solar_potential_folder_PV()
=======
    pv_folder = os.path.join(locator.get_potentials_solar_folder(), building)
>>>>>>> Stashed changes

    if not os.path.exists(pv_folder):
        return []

<<<<<<< Updated upstream
    # Find all PV result files for this building
    # Format: {building}_{panel_type}.csv (e.g., B1000_PV1.csv)
    pv_codes = []
    for filename in os.listdir(pv_folder):
        if filename.startswith(building + '_') and filename.endswith('.csv'):
            # Extract panel type from filename: B1000_PV1.csv -> PV1
            pv_code = filename.replace(building + '_', '').replace('.csv', '')
=======
    # Find all PV result files
    pv_codes = []
    for filename in os.listdir(pv_folder):
        if filename.startswith(building + '_') and filename.endswith('_PV.csv'):
            # Extract PV code from filename: B001_PV1_PV.csv -> PV1
            pv_code = filename.replace(building + '_', '').replace('_PV.csv', '')
>>>>>>> Stashed changes
            pv_codes.append(pv_code)

    return sorted(pv_codes)
