"""
Shared utility for calculating net energy with PV offsetting.

Used by both:
- primary_energy module (Life Cycle Analysis)
- operational_emission module (Life Cycle Analysis)

Net metering approach: NetGRID = GRID_demand - PV_total
"""

import pandas as pd


__author__ = "Yiqiao Wang, Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Yiqiao Wang", "Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

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
            'FE_COAL_kWh': float,           # Coal (annual)
            'FE_OIL_kWh': float,            # Oil (annual)
            'FE_WOOD_kWh': float,           # Wood (annual)
            'PV_by_type': dict,             # {pv_code: generation_kWh} by panel type
            'hourly_data': pd.DataFrame     # Hourly timeseries (optional future use)
        }

    Notes
    -----
    - DH (District Heating) and DC (District Cooling) are excluded from primary energy
      calculations as their distribution losses and generation primary energy are
      calculated separately in thermal network and district optimization features.

    Notes
    -----
    - All non-GRID carriers pass through unchanged
    - Uses demand_energycarrier columns from building demand file
    - PV data returned per-panel for flexibility in downstream calculations
    """
    # Read building demand
    demand_path = locator.get_demand_results_file(building)
    demand_df = pd.read_csv(demand_path)

    # Extract final energy by carrier (kWh = Wh / 1000)
    # Use demand_energycarrier columns from demand output
    # Note: DH and DC excluded - their primary energy calculated in district optimization
    carriers = {
        'GRID': demand_df['GRID_kWh'].sum() if 'GRID_kWh' in demand_df.columns else 0.0,
        'NATURALGAS': demand_df['NG_hs_kWh'].sum() if 'NG_hs_kWh' in demand_df.columns else 0.0,
        'COAL': demand_df['COAL_hs_kWh'].sum() if 'COAL_hs_kWh' in demand_df.columns else 0.0,
        'OIL': demand_df['OIL_hs_kWh'].sum() if 'OIL_hs_kWh' in demand_df.columns else 0.0,
        'WOOD': demand_df['WOOD_hs_kWh'].sum() if 'WOOD_hs_kWh' in demand_df.columns else 0.0,
    }

    # Initialize PV offsetting
    pv_by_type = {}  # Store PV generation by panel type

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

        # Get PV generation for each panel separately
        for pv_code in panels_to_include:
            pv_path = locator.PV_results(building, pv_code)
            try:
                pv_df = pd.read_csv(pv_path)
                # PV generation column: E_PV_gen_kWh
                if 'E_PV_gen_kWh' in pv_df.columns:
                    pv_generation = pv_df['E_PV_gen_kWh'].sum()
                    pv_by_type[pv_code] = pv_generation
            except FileNotFoundError:
                # Panel file doesn't exist, skip
                continue

    # Return results with per-panel data
    return {
        'FE_GRID_kWh': carriers['GRID'],
        'FE_NATURALGAS_kWh': carriers['NATURALGAS'],
        'FE_COAL_kWh': carriers['COAL'],
        'FE_OIL_kWh': carriers['OIL'],
        'FE_WOOD_kWh': carriers['WOOD'],
        'PV_by_type': pv_by_type,  # Dict: {pv_code: generation_kWh}
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

    pv_folder = locator.solar_potential_folder_PV()

    if not os.path.exists(pv_folder):
        return []

    # Find all PV result files for this building
    # Format: {building}_{panel_type}.csv (e.g., B1000_PV1.csv)
    pv_codes = []
    for filename in os.listdir(pv_folder):
        if filename.startswith(building + '_') and filename.endswith('.csv'):
            # Extract panel type from filename: B1000_PV1.csv -> PV1
            pv_code = filename.replace(building + '_', '').replace('.csv', '')
            pv_codes.append(pv_code)

    return sorted(pv_codes)
