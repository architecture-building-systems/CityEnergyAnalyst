"""
Solar panel cost calculation for baseline costs.

Calculates capital and operational costs for solar panels (PV, PVT, SC)
based on user-selected technologies per building facade.
"""
import os
import pandas as pd
import numpy as np
from math import log

from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def parse_solar_tech_code(tech_code):
    """
    Parse solar technology code into components.

    Args:
        tech_code: Technology code string (e.g., 'PV_PV1', 'PVT_PV1_FP', 'SC_FP')

    Returns:
        tuple: (technology_type, panel_code_for_files, panel_code_for_database)

    Examples:
        'PV_PV1' -> ('PV', 'PV1', 'PV1')
        'PVT_PV1_FP' -> ('PVT', 'PV1_FP', 'PVT1')
        'SC_FP' -> ('SC', 'FP', 'SC1')
        'SC_ET' -> ('SC', 'ET', 'SC2')
        'No solar technology installed' -> (None, None, None)
    """
    if not tech_code or tech_code == 'No solar technology installed':
        return None, None, None

    parts = tech_code.split('_')

    if parts[0] == 'PV':
        # PV_PV1 -> files: PV1, database: PV1
        return 'PV', parts[1], parts[1]
    elif parts[0] == 'PVT':
        # PVT_PV1_FP -> files: PV1_FP, database: PVT1
        # Note: CEA files use PV panel type + SC type, but database just uses PVT1
        file_code = f"{parts[1]}_{parts[2]}"
        db_code = 'PVT1'  # Currently only PVT1 in database
        return 'PVT', file_code, db_code
    elif parts[0] == 'SC':
        # SC_FP -> files: FP, database: SC1
        # SC_ET -> files: ET, database: SC2
        file_code = parts[1]
        db_code = 'SC1' if parts[1] == 'FP' else 'SC2'
        return 'SC', file_code, db_code
    else:
        raise ValueError(f"Unknown solar technology format: {tech_code}")


def get_solar_panel_database_params(locator, technology_type, panel_code_for_database):
    """
    Read solar panel cost and technical parameters from COMPONENTS/CONVERSION database.

    Args:
        locator: InputLocator instance
        technology_type: 'PV', 'PVT', or 'SC'
        panel_code_for_database: Database code (e.g., 'PV1', 'PVT1', 'SC1')

    Returns:
        dict: Parameters including capacity_Wp, module_area_m2, a, b, c, d, e, LT_yr, O&M_%, IR_%, code

    Raises:
        ValueError: If technology not found in database
    """
    if technology_type == 'PV':
        db_path = locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS')
    elif technology_type == 'PVT':
        db_path = locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_THERMAL_PANELS')
    elif technology_type == 'SC':
        db_path = locator.get_db4_components_conversion_conversion_technology_csv('SOLAR_COLLECTORS')
    else:
        raise ValueError(f"Unknown technology type: {technology_type}")

    df = pd.read_csv(db_path)

    # Filter to selected panel
    panel_data = df[df['code'] == panel_code_for_database]

    if panel_data.empty:
        available = df['code'].unique().tolist()
        raise ValueError(
            f"Solar panel '{panel_code_for_database}' not found in {technology_type} database. "
            f"Available codes: {', '.join(available)}"
        )

    # Extract parameters
    params = {
        'a': panel_data['a'].values[0],
        'b': panel_data['b'].values[0],
        'c': panel_data['c'].values[0],
        'd': panel_data['d'].values[0],
        'e': panel_data['e'].values[0],
        'LT_yr': panel_data['LT_yr'].values[0],
        'O&M_%': panel_data['O&M_%'].values[0],
        'IR_%': panel_data['IR_%'].values[0],
        'code': panel_code_for_database,
        'technology_type': technology_type
    }

    # Only PV has capacity_Wp and module_area_m2 columns
    # PVT and SC are thermal systems - we'll use area directly
    if technology_type == 'PV':
        params['capacity_Wp'] = panel_data['capacity_Wp'].values[0]
        params['module_area_m2'] = panel_data['module_area_m2'].values[0]
    else:
        params['capacity_Wp'] = None
        params['module_area_m2'] = None

    return params


def read_solar_area_data(locator, technology_type, panel_code_for_files, buildings):
    """
    Read installed area data from *_total_buildings.csv file.

    Args:
        locator: InputLocator instance
        technology_type: 'PV', 'PVT', or 'SC'
        panel_code_for_files: File code (e.g., 'PV1', 'PV1_FP', 'FP')
        buildings: List of building names to filter

    Returns:
        DataFrame with columns: name, roofs_top_m2, walls_north_m2, walls_south_m2, walls_east_m2, walls_west_m2
        Returns None if file doesn't exist
    """
    solar_folder = locator.get_potentials_solar_folder()

    # Construct filename and column prefix based on technology type
    if technology_type == 'PV':
        filename = f"PV_{panel_code_for_files}_total_buildings.csv"
        prefix = 'PV'  # Column prefix is just 'PV'
    elif technology_type == 'PVT':
        # panel_code_for_files is like 'PV1_FP', extract SC type (FP or ET)
        sc_type = panel_code_for_files.split('_')[-1]  # Get 'FP' from 'PV1_FP'
        filename = f"PVT_{panel_code_for_files}_total_buildings.csv"
        prefix = f'PVT_{sc_type}'  # Column prefix is 'PVT_FP'
    elif technology_type == 'SC':
        filename = f"SC_{panel_code_for_files}_total_buildings.csv"
        prefix = f'SC_{panel_code_for_files}'  # Column prefix is 'SC_FP' or 'SC_ET'
    else:
        raise ValueError(f"Unknown technology type: {technology_type}")

    filepath = os.path.join(solar_folder, filename)

    if not os.path.exists(filepath):
        print(f"  Warning: Solar results file not found: {filename}")
        return None

    df = pd.read_csv(filepath)

    # Filter to requested buildings
    df = df[df['name'].isin(buildings)]

    if df.empty:
        print(f"  Warning: No buildings found in {filename}")
        return None

    # Extract area columns and rename to standard names
    area_columns = {
        'name': 'name',
        f'{prefix}_roofs_top_m2': 'roofs_top_m2',
        f'{prefix}_walls_north_m2': 'walls_north_m2',
        f'{prefix}_walls_south_m2': 'walls_south_m2',
        f'{prefix}_walls_east_m2': 'walls_east_m2',
        f'{prefix}_walls_west_m2': 'walls_west_m2'
    }

    # Check which columns exist
    existing_cols = {k: v for k, v in area_columns.items() if k in df.columns}

    if len(existing_cols) <= 1:  # Only 'name' column
        print(f"  Warning: No area columns found in {filename}")
        return None

    # Select and rename columns
    df_areas = df[list(existing_cols.keys())].copy()
    df_areas.rename(columns=existing_cols, inplace=True)

    return df_areas


def calculate_solar_panel_costs(area_m2, panel_params):
    """
    Calculate solar panel costs using abcde cost formula from optimization-new.

    Formula: CAPEX = a + b×area_m2^c + (d + e×area_m2)×log(area_m2)

    Uses installed area directly in the cost formula, as the database cost parameters
    are calibrated for area-based calculations.

    Args:
        area_m2: Installed area in square metres
        panel_params: Dict with technology_type, a, b, c, d, e, LT_yr, O&M_%, IR_%

    Returns:
        dict: area_m2, capex_total_USD, capex_a_USD, opex_fixed_a_USD, opex_var_a_USD
    """
    if area_m2 <= 0:
        return {
            'area_m2': 0.0,
            'capex_total_USD': 0.0,
            'capex_a_USD': 0.0,
            'opex_fixed_a_USD': 0.0,
            'opex_var_a_USD': 0.0
        }

    # Calculate CAPEX using abcde formula with area directly
    a = panel_params['a']
    b = panel_params['b']
    c = panel_params['c']
    d = panel_params['d']
    e = panel_params['e']

    capex_total_USD = (
        a +
        b * (area_m2 ** c) +
        (d + e * area_m2) * log(area_m2)
    )

    # Calculate annualised costs
    IR_percent = panel_params['IR_%']
    LT_yr = panel_params['LT_yr']
    OM_percent = panel_params['O&M_%']

    capex_a_USD = calc_capex_annualized(capex_total_USD, IR_percent, LT_yr)
    opex_fixed_a_USD = capex_total_USD * (OM_percent / 100)
    opex_var_a_USD = 0.0  # Solar has no variable costs (for now - future: sell to grid)

    return {
        'area_m2': area_m2,
        'capex_total_USD': capex_total_USD,
        'capex_a_USD': capex_a_USD,
        'opex_fixed_a_USD': opex_fixed_a_USD,
        'opex_var_a_USD': opex_var_a_USD
    }


def calculate_building_solar_costs(config, locator, buildings):
    """
    Calculate solar panel costs for all buildings based on user configuration.

    Args:
        config: Configuration object
        locator: InputLocator instance
        buildings: List of building names

    Returns:
        tuple: (solar_details, solar_summary)
            - solar_details: DataFrame for costs_components.csv (one row per building per facade)
            - solar_summary: DataFrame for costs_buildings.csv (aggregated by building)
    """
    print("  Checking solar panel configuration...")

    # Map facade configuration parameters to column suffixes
    facade_mapping = {
        'panels_on_roof': 'roofs_top',
        'panels_on_wall_north': 'walls_north',
        'panels_on_wall_south': 'walls_south',
        'panels_on_wall_east': 'walls_east',
        'panels_on_wall_west': 'walls_west'
    }

    detail_rows = []

    # Process each facade
    for config_param, facade_suffix in facade_mapping.items():
        # Get selected technology from config
        try:
            tech_code = getattr(config.system_costs, config_param)
        except AttributeError:
            print(f"  Warning: Configuration parameter '{config_param}' not found. Skipping.")
            continue

        if not tech_code or tech_code == 'No solar technology installed':
            continue

        print(f"  Processing {config_param}: {tech_code}")

        # Parse technology code
        try:
            technology_type, panel_code_for_files, panel_code_for_database = parse_solar_tech_code(tech_code)
        except ValueError as e:
            print(f"    Error: {e}")
            continue

        if technology_type is None:
            continue

        # Get database parameters
        try:
            panel_params = get_solar_panel_database_params(locator, technology_type, panel_code_for_database)
        except ValueError as e:
            print(f"    Error: {e}")
            continue

        # Read area data
        area_data = read_solar_area_data(locator, technology_type, panel_code_for_files, buildings)

        if area_data is None:
            continue

        # Calculate costs for each building
        area_column = f"{facade_suffix}_m2"

        if area_column not in area_data.columns:
            print(f"    Warning: Column '{area_column}' not found in area data. Skipping.")
            continue

        buildings_processed = 0
        for _, row in area_data.iterrows():
            building_name = row['name']
            area_m2 = row.get(area_column, 0.0)

            if area_m2 <= 0:
                continue

            # Calculate costs
            costs = calculate_solar_panel_costs(area_m2, panel_params)

            if costs['area_m2'] <= 0:
                continue

            # Create detail row
            detail_rows.append({
                'name': building_name,
                'network_type': '',
                'service': 'SOLAR',
                'code': tech_code,
                'capacity_kW': costs['area_m2'],  # Store area in the capacity column
                'placement': facade_suffix.replace('_m2', ''),  # e.g., 'roofs_top'
                'capex_total_USD': costs['capex_total_USD'],
                'capex_a_USD': costs['capex_a_USD'],
                'opex_fixed_a_USD': costs['opex_fixed_a_USD'],
                'opex_var_a_USD': costs['opex_var_a_USD'],
                'scale': 'BUILDING'
            })
            buildings_processed += 1

        print(f"    Calculated costs for {buildings_processed} buildings")

    # Create details DataFrame
    if detail_rows:
        solar_details = pd.DataFrame(detail_rows)
    else:
        solar_details = pd.DataFrame()
        print("  No solar panels configured or no valid data found")

    # Create summary DataFrame (aggregate by building)
    if not solar_details.empty:
        solar_summary = solar_details.groupby('name').agg({
            'capex_total_USD': 'sum',
            'capex_a_USD': 'sum',
            'opex_fixed_a_USD': 'sum',
            'opex_var_a_USD': 'sum'
        }).reset_index()
    else:
        solar_summary = pd.DataFrame()

    return solar_details, solar_summary


def merge_solar_costs_to_buildings(final_results, solar_summary):
    """
    Add or update solar costs in building rows of costs_buildings.csv.

    Args:
        final_results: DataFrame with building-level costs (summary format)
        solar_summary: DataFrame with aggregated solar costs per building

    Returns:
        DataFrame: Updated final_results with solar costs added
    """
    if solar_summary.empty:
        return final_results

    # Make a copy to avoid modifying original
    result = final_results.copy()

    # Map solar_summary column names to final_results column names
    # solar_summary uses: capex_total_USD, capex_a_USD, opex_fixed_a_USD, opex_var_a_USD
    # final_results uses: Capex_total_USD, Capex_a_USD, Opex_fixed_a_USD, Opex_var_a_USD (capitalized)

    for _, solar_row in solar_summary.iterrows():
        building_name = solar_row['name']

        # Find existing building row (buildings don't have _DC or _DH suffix)
        mask = (result['name'] == building_name)

        if mask.any():
            # Update existing row - add solar costs to existing costs
            # Note: final_results uses capitalized column names
            result.loc[mask, 'Capex_total_USD'] += solar_row['capex_total_USD']
            result.loc[mask, 'Capex_a_USD'] += solar_row['capex_a_USD']
            result.loc[mask, 'Opex_fixed_a_USD'] += solar_row['opex_fixed_a_USD']
            result.loc[mask, 'Opex_var_a_USD'] += solar_row['opex_var_a_USD']
            result.loc[mask, 'Opex_a_USD'] += (solar_row['opex_fixed_a_USD'] + solar_row['opex_var_a_USD'])
            result.loc[mask, 'TAC_USD'] += (solar_row['capex_a_USD'] + solar_row['opex_fixed_a_USD'] + solar_row['opex_var_a_USD'])

            # Add to building scale costs (solar is building-level)
            result.loc[mask, 'Capex_total_building_scale_USD'] += solar_row['capex_total_USD']
            result.loc[mask, 'Capex_a_building_scale_USD'] += solar_row['capex_a_USD']
            result.loc[mask, 'Opex_a_building_scale_USD'] += (solar_row['opex_fixed_a_USD'] + solar_row['opex_var_a_USD'])
        else:
            # Create new row for building with only solar costs
            # Match the format of final_results (from format_simplified.py)
            new_row = {
                'name': building_name,
                'GFA_m2': 0.0,  # We don't have GFA info here
                'Capex_total_USD': solar_row['capex_total_USD'],
                'Capex_a_USD': solar_row['capex_a_USD'],
                'Opex_fixed_a_USD': solar_row['opex_fixed_a_USD'],
                'Opex_var_a_USD': solar_row['opex_var_a_USD'],
                'Opex_a_USD': solar_row['opex_fixed_a_USD'] + solar_row['opex_var_a_USD'],
                'TAC_USD': solar_row['capex_a_USD'] + solar_row['opex_fixed_a_USD'] + solar_row['opex_var_a_USD'],
                'Capex_total_building_scale_USD': solar_row['capex_total_USD'],
                'Capex_total_district_scale_USD': 0.0,
                'Capex_a_building_scale_USD': solar_row['capex_a_USD'],
                'Capex_a_district_scale_USD': 0.0,
                'Opex_a_building_scale_USD': solar_row['opex_fixed_a_USD'] + solar_row['opex_var_a_USD'],
                'Opex_a_district_scale_USD': 0.0,
            }
            result = pd.concat([result, pd.DataFrame([new_row])], ignore_index=True)

    return result
