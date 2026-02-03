"""
Final Energy Calculation - Core Logic

This module implements the core calculation logic for converting building demand
to final energy consumption by carrier.

Key approach (from IMPLEMENTATION_PLAN.md):
- Use constant efficiency from COMPONENTS database (not part-load curves)
- Assembly → Component → Feedstock workflow
- District systems read from thermal-network results
- Booster systems handled separately

"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import os
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe


# Constants
HOURS_IN_YEAR = 8760


def calculate_building_final_energy(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Calculate hourly final energy consumption by carrier for one building.

    Workflow:
    1. Read hourly demand from demand/{building}.csv
    2. Load supply system configuration (from supply.csv or config parameters)
    3. For each service (heating, cooling, DHW):
       - Get assembly code → load component → get feedstock
       - Apply constant efficiency: final_energy = demand / efficiency
    4. Handle district heating/cooling (read from thermal-network results)
    5. Handle booster systems (read from booster substation files)
    6. Return DataFrame with 8760 rows and carrier columns

    :param building_name: Name of the building (e.g., 'B1001')
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with columns: date, Qhs_sys_kWh, ..., scale, case, case_description
    """
    # Step 1: Read demand
    demand_file = locator.get_demand_results_file(building_name)
    if not os.path.exists(demand_file):
        raise FileNotFoundError(
            f"Demand file not found for building {building_name}: {demand_file}\n"
            f"Please run 'cea demand' first."
        )

    demand_df = pd.read_csv(demand_file)

    # Initialize output DataFrame with demand columns
    final_energy = pd.DataFrame({
        'date': demand_df['date'],
        'Qhs_sys_kWh': demand_df['Qhs_sys_kWh'],
        'Qww_sys_kWh': demand_df['Qww_sys_kWh'],
        'Qcs_sys_kWh': demand_df['Qcs_sys_kWh'],
        'E_sys_kWh': demand_df['E_sys_kWh'],
    })

    # Step 2: Load supply configuration
    supply_config = load_supply_configuration(building_name, locator, config)

    # Step 3: Calculate final energy for each service
    # Space heating
    if supply_config['space_heating'] and supply_config['space_heating']['scale'] == 'BUILDING':
        # Building-scale: use component efficiency
        carrier = supply_config['space_heating']['carrier']
        efficiency = supply_config['space_heating']['efficiency']
        final_energy[f'Qhs_sys_{carrier}_kWh'] = demand_df['Qhs_sys_kWh'] / efficiency
    elif supply_config['space_heating'] and supply_config['space_heating']['scale'] == 'DISTRICT':
        # District heating: read from thermal-network
        network_name = supply_config['space_heating']['network_name']
        dh_data = load_district_heating_data(building_name, network_name, locator)
        final_energy['Qhs_sys_DH_kWh'] = dh_data['DH_hs_kWh']
    else:
        # No heating system
        final_energy['Qhs_sys_NONE_kWh'] = 0.0

    # Hot water (DHW)
    if supply_config['hot_water'] and supply_config['hot_water']['scale'] == 'BUILDING':
        carrier = supply_config['hot_water']['carrier']
        efficiency = supply_config['hot_water']['efficiency']
        final_energy[f'Qww_sys_{carrier}_kWh'] = demand_df['Qww_sys_kWh'] / efficiency
    elif supply_config['hot_water'] and supply_config['hot_water']['scale'] == 'DISTRICT':
        network_name = supply_config['hot_water']['network_name']
        dh_data = load_district_heating_data(building_name, network_name, locator)
        final_energy['Qww_sys_DH_kWh'] = dh_data['DH_ww_kWh']
    else:
        final_energy['Qww_sys_NONE_kWh'] = 0.0

    # Space cooling
    if supply_config['space_cooling'] and supply_config['space_cooling']['scale'] == 'BUILDING':
        carrier = supply_config['space_cooling']['carrier']
        efficiency = supply_config['space_cooling']['efficiency']
        final_energy[f'Qcs_sys_{carrier}_kWh'] = demand_df['Qcs_sys_kWh'] / efficiency
    elif supply_config['space_cooling'] and supply_config['space_cooling']['scale'] == 'DISTRICT':
        network_name = supply_config['space_cooling']['network_name']
        dc_data = load_district_cooling_data(building_name, network_name, locator)
        final_energy['Qcs_sys_DC_kWh'] = dc_data['DC_cs_kWh']
    else:
        final_energy['Qcs_sys_NONE_kWh'] = 0.0

    # Electricity (always GRID)
    final_energy['E_sys_GRID_kWh'] = demand_df['E_sys_kWh']

    # Step 4: Handle booster systems (if applicable)
    # Only load booster data if booster is configured AND has a network_name
    if supply_config['space_heating_booster'] and supply_config['space_heating_booster']['network_name']:
        network_name = supply_config['space_heating_booster']['network_name']
        try:
            booster_data = load_booster_data(building_name, network_name, 'hs', locator)
            carrier = supply_config['space_heating_booster']['carrier']
            efficiency = supply_config['space_heating_booster']['efficiency']
            final_energy[f'Qhs_booster_{carrier}_kWh'] = booster_data['Qhs_booster_kWh'] / efficiency
        except FileNotFoundError:
            # Booster file not found - building may not be connected to network
            # This is OK, just skip booster calculation
            pass

    if supply_config['hot_water_booster'] and supply_config['hot_water_booster']['network_name']:
        network_name = supply_config['hot_water_booster']['network_name']
        try:
            booster_data = load_booster_data(building_name, network_name, 'dhw', locator)
            carrier = supply_config['hot_water_booster']['carrier']
            efficiency = supply_config['hot_water_booster']['efficiency']
            final_energy[f'Qww_booster_{carrier}_kWh'] = booster_data['Qww_booster_kWh'] / efficiency
        except FileNotFoundError:
            # Booster file not found - building may not be connected to network
            # This is OK, just skip booster calculation
            pass

    # Step 5: Add metadata columns
    final_energy['scale'] = 'BUILDING'
    case_num, case_desc = determine_case(supply_config)
    final_energy['case'] = case_num
    final_energy['case_description'] = case_desc

    return final_energy


def load_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> Dict:
    """
    Load supply system configuration for a building.

    Returns dict with structure:
    {
        'space_heating': {'scale': 'BUILDING'|'DISTRICT', 'carrier': 'NATURALGAS', 'efficiency': 0.85, ...},
        'hot_water': {...},
        'space_cooling': {...},
        'space_heating_booster': {...} or None,
        'hot_water_booster': {...} or None,
    }

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Supply configuration dict
    """
    if config.final_energy.overwrite_supply_settings:
        # What-if mode: use config parameters
        return load_whatif_supply_configuration(building_name, locator, config)
    else:
        # Production mode: use supply.csv
        return load_production_supply_configuration(building_name, locator, config)


def load_production_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> Dict:
    """
    Load supply configuration from supply.csv (production mode).

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Supply configuration dict
    """
    from cea.datamanagement.database.assemblies import Supply

    # Read supply.csv
    supply_df = pd.read_csv(locator.get_building_supply()).set_index('name')
    if building_name not in supply_df.index:
        raise ValueError(f"Building {building_name} not found in supply.csv")

    building_supply = supply_df.loc[building_name]

    # Load supply database
    supply_db = Supply.from_locator(locator)

    # Get network name from config (if specified)
    network_name = config.final_energy.network_name

    # Initialize supply config dict
    supply_config = {
        'space_heating': None,
        'hot_water': None,
        'space_cooling': None,
        'space_heating_booster': None,
        'hot_water_booster': None,
    }

    # Parse space heating
    if 'supply_type_hs' in building_supply and building_supply['supply_type_hs']:
        supply_config['space_heating'] = parse_supply_assembly(
            building_supply['supply_type_hs'],
            supply_db.heating,
            locator,
            'heating',
            network_name
        )

    # Parse hot water (DHW)
    if 'supply_type_dhw' in building_supply and building_supply['supply_type_dhw']:
        supply_config['hot_water'] = parse_supply_assembly(
            building_supply['supply_type_dhw'],
            supply_db.hot_water,
            locator,
            'hot_water',
            network_name
        )

    # Parse space cooling
    if 'supply_type_cs' in building_supply and building_supply['supply_type_cs']:
        supply_config['space_cooling'] = parse_supply_assembly(
            building_supply['supply_type_cs'],
            supply_db.cooling,
            locator,
            'cooling',
            network_name
        )

    # TODO: Handle booster systems - check if building is connected to district network
    # and if booster substation files exist

    return supply_config


def parse_supply_assembly(
    assembly_code: str,
    assembly_df: pd.DataFrame,
    locator: cea.inputlocator.InputLocator,
    service_type: str,  # 'heating', 'hot_water', or 'cooling'
    network_name: Optional[str] = None
) -> Dict:
    """
    Parse an assembly code and return its configuration.

    :param assembly_code: Assembly code (e.g., 'SUPPLY_HEATING_AS3')
    :param assembly_df: Supply assembly DataFrame (from Supply.from_locator())
    :param locator: InputLocator instance
    :param service_type: Type of service
    :param network_name: Network name (required for DISTRICT scale)
    :return: Dict with scale, carrier, efficiency, assembly_code, component_code, network_name
    """
    if assembly_code not in assembly_df.index:
        raise ValueError(f"Assembly {assembly_code} not found in database")

    assembly = assembly_df.loc[assembly_code]

    # Get scale
    scale = assembly['scale']

    if scale == 'NONE':
        return {
            'scale': 'NONE',
            'carrier': None,
            'efficiency': None,
            'assembly_code': assembly_code,
            'component_code': None,
            'network_name': None,
        }

    # Get primary component code
    component_code = assembly['primary_components']
    if pd.isna(component_code) or component_code == '-':
        raise ValueError(f"Assembly {assembly_code} has no primary component")

    # Load component information from COMPONENTS database
    component_info = load_component_info(component_code, locator)

    result = {
        'scale': scale,
        'carrier': component_info['carrier'],
        'efficiency': component_info['efficiency'],
        'assembly_code': assembly_code,
        'component_code': component_code,
        'network_name': network_name if scale == 'DISTRICT' else None,
    }

    return result


def load_component_info(
    component_code: str,
    locator: cea.inputlocator.InputLocator
) -> Dict:
    """
    Load component information from COMPONENTS database.

    :param component_code: Component code (e.g., 'BO1', 'HP1', 'CH1')
    :param locator: InputLocator instance
    :return: Dict with carrier and efficiency
    """
    # Determine component type from code prefix
    if component_code.startswith('BO'):
        # Boiler
        component_file = locator.get_db4_components_conversion_conversion_technology_csv('BOILERS')
        df = pd.read_csv(component_file)
        components = df[df['code'] == component_code]

        if components.empty:
            raise ValueError(f"Component {component_code} not found in BOILERS database")

        # Take first row (or average efficiency across capacity ranges)
        component = components.iloc[0]

        return {
            'carrier': map_fuel_code_to_carrier(component['fuel_code']),
            'efficiency': component['min_eff_rating']
        }

    elif component_code.startswith('HP'):
        # Heat pump
        component_file = locator.get_db4_components_conversion_conversion_technology_csv('HEAT_PUMPS')
        df = pd.read_csv(component_file)
        components = df[df['code'] == component_code]

        if components.empty:
            raise ValueError(f"Component {component_code} not found in HEAT_PUMPS database")

        # Take first row (or average COP across capacity ranges)
        component = components.iloc[0]

        return {
            'carrier': 'GRID',  # Heat pumps use electricity
            'efficiency': component['min_eff_rating_seasonal']
        }

    elif component_code.startswith('CH'):
        # Chiller
        component_file = locator.get_db4_components_conversion_conversion_technology_csv('VAPOR_COMPRESSION_CHILLERS')
        df = pd.read_csv(component_file)
        components = df[df['code'] == component_code]

        if components.empty:
            raise ValueError(f"Component {component_code} not found in CHILLERS database")

        # Take first row (or average COP across capacity ranges)
        component = components.iloc[0]

        return {
            'carrier': 'GRID',  # Chillers use electricity
            'efficiency': component['min_eff_rating']
        }

    else:
        raise ValueError(f"Unknown component type for code {component_code}")


def map_fuel_code_to_carrier(fuel_code: str) -> str:
    """
    Map database fuel codes to carrier names.

    :param fuel_code: Fuel code from database (e.g., 'Cgas', 'Coil', 'E230AC')
    :return: Carrier name (e.g., 'NATURALGAS', 'OIL', 'GRID')
    """
    fuel_mapping = {
        'Cgas': 'NATURALGAS',
        'Coil': 'OIL',
        'Ccoa': 'COAL',
        'Cwod': 'WOOD',
        'E230AC': 'GRID',
    }

    if fuel_code not in fuel_mapping:
        raise ValueError(f"Unknown fuel code: {fuel_code}")

    return fuel_mapping[fuel_code]


def load_whatif_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> Dict:
    """
    Load supply configuration from config parameters (what-if mode).

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Supply configuration dict
    """
    from cea.datamanagement.database.assemblies import Supply

    # Load supply database
    supply_db = Supply.from_locator(locator)

    # Get network name from config
    network_name = config.final_energy.network_name

    # Get supply type parameters from config
    # These are lists of assembly codes (can be multiple due to multi-select)
    supply_type_hs = config.final_energy.supply_type_hs if config.final_energy.supply_type_hs else []
    supply_type_dhw = config.final_energy.supply_type_dhw if config.final_energy.supply_type_dhw else []
    supply_type_cs = config.final_energy.supply_type_cs if config.final_energy.supply_type_cs else []

    # Booster parameters
    booster_hs = config.final_energy.hs_booster_type if config.final_energy.hs_booster_type else []
    booster_dhw = config.final_energy.dhw_booster_type if config.final_energy.dhw_booster_type else []

    # Initialize supply config dict
    supply_config = {
        'space_heating': None,
        'hot_water': None,
        'space_cooling': None,
        'space_heating_booster': None,
        'hot_water_booster': None,
    }

    # Helper function to strip scale labels from assembly codes
    def strip_scale_label(assembly_str: str) -> str:
        """Strip scale label from assembly code: 'SUPPLY_HEATING_AS3 (building)' -> 'SUPPLY_HEATING_AS3'"""
        if ' (' in assembly_str:
            return assembly_str.split(' (')[0]
        return assembly_str

    # Parse space heating (use first assembly if multiple selected)
    if supply_type_hs and len(supply_type_hs) > 0:
        assembly_code = strip_scale_label(supply_type_hs[0])  # Take first selection
        supply_config['space_heating'] = parse_supply_assembly(
            assembly_code,
            supply_db.heating,
            locator,
            'heating',
            network_name
        )

    # Parse hot water (DHW)
    if supply_type_dhw and len(supply_type_dhw) > 0:
        assembly_code = strip_scale_label(supply_type_dhw[0])
        supply_config['hot_water'] = parse_supply_assembly(
            assembly_code,
            supply_db.hot_water,
            locator,
            'hot_water',
            network_name
        )

    # Parse space cooling
    if supply_type_cs and len(supply_type_cs) > 0:
        assembly_code = strip_scale_label(supply_type_cs[0])
        supply_config['space_cooling'] = parse_supply_assembly(
            assembly_code,
            supply_db.cooling,
            locator,
            'cooling',
            network_name
        )

    # Parse booster systems
    if booster_hs and len(booster_hs) > 0:
        assembly_code = strip_scale_label(booster_hs[0])
        supply_config['space_heating_booster'] = parse_supply_assembly(
            assembly_code,
            supply_db.heating,
            locator,
            'heating',
            network_name
        )

    if booster_dhw and len(booster_dhw) > 0:
        assembly_code = strip_scale_label(booster_dhw[0])
        supply_config['hot_water_booster'] = parse_supply_assembly(
            assembly_code,
            supply_db.hot_water,
            locator,
            'hot_water',
            network_name
        )

    return supply_config


def load_district_heating_data(
    building_name: str,
    network_name: str,
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Load district heating consumption from thermal-network results.

    :param building_name: Name of the building
    :param network_name: Network layout name
    :param locator: InputLocator instance
    :return: DataFrame with columns: DH_hs_kWh, DH_ww_kWh
    """
    # Read substation file
    substation_file = locator.get_thermal_network_substation_results_file(
        building_name, 'DH', network_name
    )

    if not os.path.exists(substation_file):
        raise FileNotFoundError(
            f"District heating substation file not found for building {building_name}: {substation_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    substation_df = pd.read_csv(substation_file)

    # Convert from W to kWh (Watts are hourly averages, so W = Wh for hourly data)
    result = pd.DataFrame({
        'DH_hs_kWh': substation_df['Qhs_dh_W'] / 1000.0,
        'DH_ww_kWh': substation_df['Qww_dh_W'] / 1000.0,
    })

    return result


def load_district_cooling_data(
    building_name: str,
    network_name: str,
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Load district cooling consumption from thermal-network results.

    :param building_name: Name of the building
    :param network_name: Network layout name
    :param locator: InputLocator instance
    :return: DataFrame with columns: DC_cs_kWh, DC_cdata_kWh, DC_cre_kWh
    """
    # Read substation file
    substation_file = locator.get_thermal_network_substation_results_file(
        building_name, 'DC', network_name
    )

    if not os.path.exists(substation_file):
        raise FileNotFoundError(
            f"District cooling substation file not found for building {building_name}: {substation_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    substation_df = pd.read_csv(substation_file)

    # Convert from W to kWh
    result = pd.DataFrame({
        'DC_cs_kWh': substation_df['Qcs_dc_W'] / 1000.0,
        'DC_cdata_kWh': substation_df['Qcdata_dc_W'] / 1000.0,
        'DC_cre_kWh': substation_df['Qcre_dc_W'] / 1000.0,
    })

    return result


def load_booster_data(
    building_name: str,
    network_name: str,
    service: str,  # 'hs' or 'dhw'
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Load booster system demand from thermal-network booster results.

    :param building_name: Name of the building
    :param network_name: Network layout name
    :param service: 'hs' (space heating) or 'dhw' (hot water)
    :param locator: InputLocator instance
    :return: DataFrame with columns: Qhs_booster_kWh or Qww_booster_kWh
    """
    # Read substation file (booster data is in the same file as DH data)
    substation_file = locator.get_thermal_network_substation_results_file(
        building_name, 'DH', network_name
    )

    if not os.path.exists(substation_file):
        raise FileNotFoundError(
            f"District heating substation file not found for building {building_name}: {substation_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    substation_df = pd.read_csv(substation_file)

    # Extract booster columns and convert from W to kWh
    if service == 'hs':
        result = pd.DataFrame({
            'Qhs_booster_kWh': substation_df['Qhs_booster_W'] / 1000.0
        })
    elif service == 'dhw':
        result = pd.DataFrame({
            'Qww_booster_kWh': substation_df['Qww_booster_W'] / 1000.0
        })
    else:
        raise ValueError(f"Invalid service type: {service}. Must be 'hs' or 'dhw'")

    return result


def determine_case(supply_config: Dict) -> Tuple[float, str]:
    """
    Determine case number and description based on supply configuration.

    Case definitions (from IMPLEMENTATION_PLAN.md):
    1: Standalone (all services building-scale)
    2: DH + DC (both heating and cooling from district)
    3: DH only (district heating + standalone cooling)
    4: DC only (standalone heating + district cooling)
    4.01: DC + booster for space heating
    4.02: DC + booster for hot water
    4.03: DC + booster for both

    :param supply_config: Supply configuration dict
    :return: (case_number, case_description)
    """
    hs_district = supply_config['space_heating']['scale'] == 'DISTRICT'
    dhw_district = supply_config['hot_water']['scale'] == 'DISTRICT'
    cs_district = supply_config['space_cooling']['scale'] == 'DISTRICT'

    hs_booster = supply_config['space_heating_booster'] is not None
    dhw_booster = supply_config['hot_water_booster'] is not None

    # Determine case
    if hs_district and dhw_district and cs_district:
        return (2, "DH + DC (centralized heating + cooling)")
    elif hs_district and dhw_district and not cs_district:
        return (3, "DH only (centralized heating + standalone cooling)")
    elif not hs_district and not dhw_district and cs_district:
        if hs_booster and dhw_booster:
            return (4.03, "DC + booster for both space heating and hot water")
        elif hs_booster:
            return (4.01, "DC + booster for space heating")
        elif dhw_booster:
            return (4.02, "DC + booster for hot water")
        else:
            return (4, "DC only (standalone heating + centralized cooling)")
    else:
        return (1, "Standalone (all services)")


def calculate_plant_final_energy(
    network_name: str,
    network_type: str,
    plant_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Calculate hourly final energy consumption for one district plant.

    :param network_name: Network layout name (e.g., 'xxx')
    :param network_type: 'DH' (district heating) or 'DC' (district cooling)
    :param plant_name: Plant node name from shapefile (e.g., 'NODE_001')
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with 8760 rows and carrier columns
    """
    # TODO: Implement
    # 1. Read plant configuration from network files
    # 2. Read plant energy consumption
    # 3. Apply plant equipment efficiency
    # 4. Return DataFrame with plant carrier columns

    raise NotImplementedError("Plant final energy calculation not yet implemented")


def aggregate_buildings_summary(
    building_dfs: Dict[str, pd.DataFrame],
    plant_dfs: Dict[str, pd.DataFrame],
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Aggregate hourly data to annual summary (final_energy_buildings.csv).

    :param building_dfs: Dict of building_name -> final_energy DataFrame
    :param plant_dfs: Dict of plant_name -> final_energy DataFrame
    :param locator: InputLocator instance
    :return: Summary DataFrame with one row per building/plant
    """
    import geopandas as gpd

    # Read building metadata
    zone_gdf = gpd.read_file(locator.get_zone_geometry())
    zone_gdf = zone_gdf.set_index('name')

    # Read total demand for GFA
    total_demand_df = pd.read_csv(locator.get_total_demand()).set_index('name')

    summary_rows = []

    # Process buildings
    for building_name, df in building_dfs.items():
        # Get building metadata
        if building_name in zone_gdf.index:
            geom = zone_gdf.loc[building_name, 'geometry']
            x_coord = geom.centroid.x
            y_coord = geom.centroid.y
        else:
            x_coord = None
            y_coord = None

        GFA_m2 = total_demand_df.loc[building_name, 'GFA_m2'] if building_name in total_demand_df.index else None

        # Sum demand columns (kWh -> MWh)
        Qhs_sys_MWh = df['Qhs_sys_kWh'].sum() / 1000.0
        Qww_sys_MWh = df['Qww_sys_kWh'].sum() / 1000.0
        Qcs_sys_MWh = df['Qcs_sys_kWh'].sum() / 1000.0
        E_sys_MWh = df['E_sys_kWh'].sum() / 1000.0

        # Sum carrier columns by type
        carrier_totals = {}
        for col in df.columns:
            if col.endswith('_kWh') and col not in ['Qhs_sys_kWh', 'Qww_sys_kWh', 'Qcs_sys_kWh', 'E_sys_kWh']:
                # Extract carrier from column name
                # Format: Qhs_sys_NATURALGAS_kWh -> NATURALGAS
                parts = col.split('_')
                if len(parts) >= 3:
                    carrier = parts[2]  # Get carrier part
                    if carrier not in carrier_totals:
                        carrier_totals[carrier] = 0.0
                    carrier_totals[carrier] += df[col].sum() / 1000.0  # kWh -> MWh

        # Calculate total final energy
        TOTAL_MWh = sum(carrier_totals.values())

        # Calculate peak demand
        total_demand_kW = df['Qhs_sys_kWh'] + df['Qww_sys_kWh'] + df['Qcs_sys_kWh'] + df['E_sys_kWh']
        peak_idx = total_demand_kW.idxmax()
        peak_demand_kW = total_demand_kW.iloc[peak_idx] if len(total_demand_kW) > 0 else 0.0
        peak_datetime = df.loc[peak_idx, 'date'] if len(total_demand_kW) > 0 else None

        # Get case info
        scale = df['scale'].iloc[0] if 'scale' in df.columns else 'BUILDING'
        case = df['case'].iloc[0] if 'case' in df.columns else None
        case_description = df['case_description'].iloc[0] if 'case_description' in df.columns else None

        # Build row
        row = {
            'name': building_name,
            'type': 'building',
            'GFA_m2': GFA_m2,
            'x_coord': x_coord,
            'y_coord': y_coord,
            'scale': scale,
            'case': case,
            'case_description': case_description,
            'Qhs_sys_MWh': Qhs_sys_MWh,
            'Qww_sys_MWh': Qww_sys_MWh,
            'Qcs_sys_MWh': Qcs_sys_MWh,
            'E_sys_MWh': E_sys_MWh,
        }

        # Add carrier columns
        for carrier in ['NATURALGAS', 'OIL', 'COAL', 'WOOD', 'GRID', 'DH', 'DC', 'SOLAR']:
            row[f'{carrier}_MWh'] = carrier_totals.get(carrier, 0.0)

        row['TOTAL_MWh'] = TOTAL_MWh
        row['peak_demand_kW'] = peak_demand_kW
        row['peak_datetime'] = peak_datetime

        summary_rows.append(row)

    # Process plants (TODO when plant calculation is implemented)
    for plant_name, df in plant_dfs.items():
        # Similar logic for plants
        pass

    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_rows)

    return summary_df


def create_final_energy_breakdown(
    building_dfs: Dict[str, pd.DataFrame],
    plant_dfs: Dict[str, pd.DataFrame],
    building_configs: Dict[str, Dict],
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Create detailed carrier breakdown by service (final_energy.csv).

    :param building_dfs: Dict of building_name -> final_energy DataFrame
    :param plant_dfs: Dict of plant_name -> final_energy DataFrame
    :param building_configs: Dict of building_name -> supply_configuration
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Breakdown DataFrame with multiple rows per building/plant
    """
    breakdown_rows = []

    # Service mapping
    service_map = {
        'space_heating': {
            'demand_col': 'Qhs_sys_kWh',
            'prefix': 'Qhs_sys',
        },
        'hot_water': {
            'demand_col': 'Qww_sys_kWh',
            'prefix': 'Qww_sys',
        },
        'space_cooling': {
            'demand_col': 'Qcs_sys_kWh',
            'prefix': 'Qcs_sys',
        },
        'electricity': {
            'demand_col': 'E_sys_kWh',
            'prefix': 'E_sys',
        },
    }

    # Process buildings
    for building_name, df in building_dfs.items():
        supply_config = building_configs.get(building_name, {})

        # Process each service
        for service_key, service_info in service_map.items():
            service_config = supply_config.get(service_key)

            if not service_config or service_config['scale'] == 'NONE':
                continue

            demand_col = service_info['demand_col']
            prefix = service_info['prefix']

            # Find carrier column
            carrier = service_config['carrier']
            carrier_col = f'{prefix}_{carrier}_kWh'

            if carrier_col not in df.columns:
                continue

            # Calculate annual totals (kWh -> MWh)
            annual_demand_MWh = df[demand_col].sum() / 1000.0
            annual_final_energy_MWh = df[carrier_col].sum() / 1000.0

            # Calculate peaks
            peak_demand_idx = df[demand_col].idxmax()
            peak_demand_kW = df.loc[peak_demand_idx, demand_col] if len(df) > 0 else 0.0
            peak_final_energy_kW = df.loc[peak_demand_idx, carrier_col] if len(df) > 0 else 0.0
            peak_datetime = df.loc[peak_demand_idx, 'date'] if len(df) > 0 else None

            # Determine component type from component code
            component_code = service_config.get('component_code')
            if component_code:
                if component_code.startswith('BO'):
                    component_type = 'Boiler'
                elif component_code.startswith('HP'):
                    component_type = 'HeatPump'
                elif component_code.startswith('CH'):
                    component_type = 'VapourCompressionChiller'
                else:
                    component_type = 'Unknown'
            else:
                component_type = None

            # Build row
            row = {
                'name': building_name,
                'type': 'building',
                'scale': service_config['scale'],
                'service': service_key,
                'demand_column': demand_col,
                'carrier': carrier,
                'assembly_code': service_config.get('assembly_code'),
                'component_code': component_code,
                'component_type': component_type,
                'efficiency': service_config.get('efficiency'),
                'annual_demand_MWh': annual_demand_MWh,
                'annual_final_energy_MWh': annual_final_energy_MWh,
                'peak_demand_kW': peak_demand_kW,
                'peak_final_energy_kW': peak_final_energy_kW,
                'peak_datetime': peak_datetime,
            }

            breakdown_rows.append(row)

        # Process booster systems if present
        if supply_config.get('space_heating_booster'):
            booster_config = supply_config['space_heating_booster']
            carrier = booster_config['carrier']
            booster_col = f'Qhs_booster_{carrier}_kWh'

            if booster_col in df.columns:
                annual_final_energy_MWh = df[booster_col].sum() / 1000.0
                if annual_final_energy_MWh > 0:
                    row = {
                        'name': building_name,
                        'type': 'building',
                        'scale': 'BUILDING',
                        'service': 'space_heating_booster',
                        'demand_column': 'Qhs_booster_kWh',
                        'carrier': carrier,
                        'assembly_code': booster_config.get('assembly_code'),
                        'component_code': booster_config.get('component_code'),
                        'component_type': 'Boiler',  # Boosters are typically boilers
                        'efficiency': booster_config.get('efficiency'),
                        'annual_demand_MWh': None,  # Booster demand is derived
                        'annual_final_energy_MWh': annual_final_energy_MWh,
                        'peak_demand_kW': None,
                        'peak_final_energy_kW': None,
                        'peak_datetime': None,
                    }
                    breakdown_rows.append(row)

        if supply_config.get('hot_water_booster'):
            booster_config = supply_config['hot_water_booster']
            carrier = booster_config['carrier']
            booster_col = f'Qww_booster_{carrier}_kWh'

            if booster_col in df.columns:
                annual_final_energy_MWh = df[booster_col].sum() / 1000.0
                if annual_final_energy_MWh > 0:
                    row = {
                        'name': building_name,
                        'type': 'building',
                        'scale': 'BUILDING',
                        'service': 'hot_water_booster',
                        'demand_column': 'Qww_booster_kWh',
                        'carrier': carrier,
                        'assembly_code': booster_config.get('assembly_code'),
                        'component_code': booster_config.get('component_code'),
                        'component_type': 'Boiler',
                        'efficiency': booster_config.get('efficiency'),
                        'annual_demand_MWh': None,
                        'annual_final_energy_MWh': annual_final_energy_MWh,
                        'peak_demand_kW': None,
                        'peak_final_energy_kW': None,
                        'peak_datetime': None,
                    }
                    breakdown_rows.append(row)

    # Process plants (TODO when plant calculation is implemented)
    for plant_name, df in plant_dfs.items():
        # Similar logic for plants
        pass

    # Create breakdown DataFrame
    breakdown_df = pd.DataFrame(breakdown_rows)

    return breakdown_df
